"""File Watcher Service - Monitors folders and indexes files"""
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, Any, Optional
import asyncio

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileDeletedEvent

from app.config import settings
from app.database.sqlite import sqlite_manager
from app.services.websocket_manager import websocket_manager, WebSocketEvents


class FileEventHandler(FileSystemEventHandler):
    """Handles file system events"""
    
    def __init__(self, watcher_service):
        self.watcher = watcher_service
    
    def on_created(self, event):
        if not event.is_directory:
            asyncio.create_task(self.watcher.handle_file_created(event.src_path))
    
    def on_modified(self, event):
        if not event.is_directory:
            asyncio.create_task(self.watcher.handle_file_modified(event.src_path))
    
    def on_deleted(self, event):
        if not event.is_directory:
            asyncio.create_task(self.watcher.handle_file_deleted(event.src_path))


class FileWatcherService:
    """Service for watching file system changes"""
    
    def __init__(self):
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[FileEventHandler] = None
        self.watched_paths: Set[str] = set()
        self.is_running = False
    
    async def start(self):
        """Start file watcher"""
        if self.is_running:
            return
        
        print("📁 Starting file watcher...")
        
        # Get watched folders from database
        folders = await sqlite_manager.get_watched_folders()
        
        if not folders:
            print("⚠️ No folders configured for watching")
            return
        
        self.observer = Observer()
        self.event_handler = FileEventHandler(self)
        
        for folder in folders:
            path = folder["path"]
            if os.path.exists(path):
                self.observer.schedule(
                    self.event_handler,
                    path,
                    recursive=folder.get("recursive", True)
                )
                self.watched_paths.add(path)
                print(f"  👁️  Watching: {path}")
        
        self.observer.start()
        self.is_running = True
        
        # Initial scan
        await self._initial_scan(folders)
        
        print(f"✅ File watcher started ({len(self.watched_paths)} folders)")
    
    async def stop(self):
        """Stop file watcher"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.is_running = False
        print("📁 File watcher stopped")
    
    async def _initial_scan(self, folders: list):
        """Initial scan of watched folders"""
        print("🔍 Running initial scan...")
        
        for folder in folders:
            path = folder["path"]
            if not os.path.exists(path):
                continue
            
            include_patterns = folder.get("include_patterns", ["*"])
            exclude_patterns = folder.get("exclude_patterns", [])
            
            for root, dirs, files in os.walk(path):
                # Filter directories
                dirs[:] = [d for d in dirs if not self._should_exclude_dir(d, exclude_patterns)]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    if self._should_include_file(file, include_patterns, exclude_patterns):
                        await self._check_and_index_file(file_path)
        
        print("✅ Initial scan complete")
    
    def _should_exclude_dir(self, dirname: str, exclude_patterns: list) -> bool:
        """Check if directory should be excluded"""
        for pattern in exclude_patterns:
            if pattern in dirname:
                return True
        return False
    
    def _should_include_file(self, filename: str, include_patterns: list, exclude_patterns: list) -> bool:
        """Check if file should be included"""
        # Check exclude patterns first
        for pattern in exclude_patterns:
            if pattern in filename:
                return False
        
        # Check include patterns
        for pattern in include_patterns:
            if pattern == "*" or filename.endswith(pattern.replace("*", "")):
                return True
        
        return False
    
    async def _check_and_index_file(self, file_path: str):
        """Check if file needs indexing and queue it"""
        try:
            # Get file stats
            stat = os.stat(file_path)
            
            # Check size
            size_mb = stat.st_size / (1024 * 1024)
            if size_mb > settings.max_file_size_mb:
                print(f"  ⚠️  Skipping large file: {file_path} ({size_mb:.1f} MB)")
                return
            
            # Calculate checksum
            checksum = await self._calculate_checksum(file_path)
            
            # Check if already indexed
            existing = await sqlite_manager.get_file_sync_status(file_path)
            
            if existing and existing["checksum"] == checksum:
                return  # No change
            
            # Queue for indexing
            await sqlite_manager.update_file_sync_status(
                file_path=file_path,
                checksum=checksum,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                index_status="pending"
            )
            
            # Broadcast indexing started
            await websocket_manager.broadcast(
                WebSocketEvents.file_indexed(None, file_path, None)
            )
            
        except Exception as e:
            print(f"Error checking file {file_path}: {e}")
    
    async def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    async def handle_file_created(self, file_path: str):
        """Handle file created event"""
        print(f"📄 File created: {file_path}")
        await self._check_and_index_file(file_path)
    
    async def handle_file_modified(self, file_path: str):
        """Handle file modified event"""
        print(f"📄 File modified: {file_path}")
        await self._check_and_index_file(file_path)
    
    async def handle_file_deleted(self, file_path: str):
        """Handle file deleted event"""
        print(f"🗑️  File deleted: {file_path}")
        
        # Update status
        await sqlite_manager.update_file_sync_status(
            file_path=file_path,
            index_status="deleted"
        )
        
        # Broadcast
        await websocket_manager.broadcast(
            WebSocketEvents.file_indexed(None, file_path, None)
        )
    
    async def add_folder(self, path: str, recursive: bool = True,
                         include_patterns: list = None,
                         exclude_patterns: list = None) -> bool:
        """Add a folder to watch"""
        if not os.path.exists(path):
            return False
        
        folder_id = str(__import__('uuid').uuid4())
        
        success = await sqlite_manager.add_watched_folder(
            folder_id=folder_id,
            path=path,
            recursive=recursive,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )
        
        if success and self.is_running:
            # Add to observer
            self.observer.schedule(
                self.event_handler,
                path,
                recursive=recursive
            )
            self.watched_paths.add(path)
            
            # Initial scan
            await self._initial_scan([{
                "path": path,
                "recursive": recursive,
                "include_patterns": include_patterns or ["*"],
                "exclude_patterns": exclude_patterns or []
            }])
        
        return success
    
    async def remove_folder(self, folder_id: str) -> bool:
        """Remove a folder from watching"""
        return await sqlite_manager.remove_watched_folder(folder_id)


# Global instance
file_watcher_service = FileWatcherService()
