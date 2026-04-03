"""File Watcher Service - Watches folders for changes"""
import os
import uuid
import logging
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileDeletedEvent, FileMovedEvent

from app.config import settings
from app.database.qdrant_client import qdrant_manager
from app.services.embedding import embedding_service
from app.services.websocket_manager import websocket_manager, WebSocketEvents

logger = logging.getLogger(__name__)


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return ""


class FileChangeHandler(FileSystemEventHandler):
    """Handles file system events"""
    
    def __init__(self, watcher):
        self.watcher = watcher
        self.loop = None
    
    def on_created(self, event):
        if not event.is_directory and self._should_process(event.src_path):
            logger.info(f"File created: {event.src_path}")
            if self.watcher.loop:
                asyncio.run_coroutine_threadsafe(
                    self.watcher.handle_file_created(event.src_path),
                    self.watcher.loop
                )
    
    def on_modified(self, event):
        if not event.is_directory and self._should_process(event.src_path):
            logger.info(f"File modified: {event.src_path}")
            if self.watcher.loop:
                asyncio.run_coroutine_threadsafe(
                    self.watcher.handle_file_modified(event.src_path),
                    self.watcher.loop
                )
    
    def on_deleted(self, event):
        if not event.is_directory and self._should_process(event.src_path):
            logger.info(f"File deleted: {event.src_path}")
            if self.watcher.loop:
                asyncio.run_coroutine_threadsafe(
                    self.watcher.handle_file_deleted(event.src_path),
                    self.watcher.loop
                )
    
    def _should_process(self, path: str) -> bool:
        """Check if file should be processed"""
        # Skip hidden files and common directories
        filename = os.path.basename(path)
        if filename.startswith("."):
            return False
        if "__pycache__" in path or "node_modules" in path:
            return False
        
        # Check extension
        valid_extensions = ['.md', '.txt', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.pdf']
        if not any(path.endswith(ext) for ext in valid_extensions):
            return False
        
        return True


class FileWatcherService:
    """Service for watching file system changes"""
    
    def __init__(self):
        self.observers: Dict[str, Observer] = {}
        self.handlers: Dict[str, FileChangeHandler] = {}
        self.folders: Dict[str, dict] = {}
        self.loop = None
    
    async def start(self):
        """Start the file watcher service"""
        self.loop = asyncio.get_running_loop()
        logger.info("File watcher service started")
    
    async def stop(self):
        """Stop the file watcher service"""
        for folder_id in list(self.observers.keys()):
            await self.remove_folder(folder_id)
        logger.info("File watcher service stopped")
    
    async def add_folder(self, folder: dict):
        """Add a folder to watch"""
        folder_id = folder["id"]
        path = folder["path"]
        recursive = folder.get("recursive", True)
        
        if folder_id in self.observers:
            logger.warning(f"Folder already being watched: {path}")
            return
        
        if not os.path.exists(path):
            logger.error(f"Folder does not exist: {path}")
            return
        
        handler = FileChangeHandler(self)
        handler.loop = self.loop
        
        observer = Observer()
        observer.schedule(handler, path, recursive=recursive)
        observer.start()
        
        self.observers[folder_id] = observer
        self.handlers[folder_id] = handler
        self.folders[folder_id] = folder
        
        logger.info(f"Started watching: {path} (recursive={recursive})")
    
    async def remove_folder(self, folder_id: str):
        """Remove a watched folder"""
        if folder_id not in self.observers:
            return
        
        observer = self.observers.pop(folder_id)
        handler = self.handlers.pop(folder_id)
        
        observer.stop()
        observer.join()
        
        self.folders.pop(folder_id, None)
        
        logger.info(f"Stopped watching folder: {folder_id}")
    
    async def handle_file_created(self, path: str):
        """Handle file creation"""
        await self.process_file(path)
    
    async def handle_file_modified(self, path: str):
        """Handle file modification"""
        await self.process_file(path)
    
    async def handle_file_deleted(self, path: str):
        """Handle file deletion"""
        await self._remove_file_from_index(path)
    
    async def process_file(self, file_path: str):
        """Process a file for indexing"""
        try:
            if not os.path.exists(file_path):
                return
            
            # Read file content
            content = ""
            content_type = "text/plain"
            
            if file_path.endswith(".pdf"):
                content = await self._extract_pdf_content(file_path)
                content_type = "application/pdf"
            elif file_path.endswith(".py"):
                content = await self._extract_code_content(file_path)
                content_type = "text/x-python"
            else:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception as e:
                    logger.warning(f"Could not read file {file_path}: {e}")
                    return
            
            # Compute SHA-256 hash
            file_hash = compute_file_hash(file_path)
            
            # Generate embedding
            embedding = await embedding_service.embed_text(content[:10000])  # Limit content
            
            # Store in Qdrant
            client = qdrant_manager.get_async_client()
            file_id = str(uuid.uuid4())
            
            await client.upsert(
                collection_name="files",
                points=[{
                    "id": file_id,
                    "vector": embedding.tolist(),
                    "payload": {
                        "id": file_id,
                        "path": file_path,
                        "name": os.path.basename(file_path),
                        "content_type": content_type,
                        "content_preview": content[:1000] if content else "",
                        "hash": file_hash,
                        "indexed_at": datetime.utcnow().isoformat(),
                        "indexed": True
                    }
                }]
            )
            
            # Broadcast event
            await websocket_manager.broadcast(
                WebSocketEvents.file_indexed(file_id, file_path)
            )
            
            logger.info(f"Indexed file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    async def _remove_file_from_index(self, file_path: str):
        """Remove a file from the index"""
        try:
            client = qdrant_manager.get_async_client()
            
            results = await client.scroll(
                collection_name="files",
                scroll_filter={
                    "must": [{"key": "path", "match": {"value": file_path}}]
                },
                limit=1,
                with_payload=False,
                with_vectors=False
            )
            
            if results[0]:
                await client.delete(
                    collection_name="files",
                    points_selector=[results[0][0].id]
                )
                
                logger.info(f"Removed file from index: {file_path}")
        except Exception as e:
            logger.error(f"Error removing file from index: {e}")
    
    async def _extract_pdf_content(self, file_path: str) -> str:
        """Extract text from PDF"""
        try:
            import PyPDF2
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
        except Exception as e:
            logger.error(f"Error extracting PDF content: {e}")
            return ""
    
    async def _extract_code_content(self, file_path: str) -> str:
        """Extract and process code file content"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading code file: {e}")
            return ""


# Global file watcher service instance
file_watcher_service = FileWatcherService()
