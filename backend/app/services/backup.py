"""Backup Service - Handles all backup operations"""
import os
import json
import shutil
import subprocess
from datetime import datetime
from typing import Optional

from app.config import settings
from app.database.qdrant_client import qdrant_manager


class BackupService:
    """Service for handling backups"""
    
    def __init__(self):
        self.backup_path = settings.backup_path
        self.running = False
    
    async def start(self):
        """Start the backup service"""
        self.running = True
        os.makedirs(self.backup_path, exist_ok=True)
        print(f"✅ Backup service started (path: {self.backup_path})")
    
    async def stop(self):
        """Stop the backup service"""
        self.running = False
        print("🛑 Backup service stopped")
    
    async def run_backup(self, backup_type: str):
        """Run a backup of the specified type"""
        if backup_type == "snapshot":
            await self._create_qdrant_snapshot()
        elif backup_type == "markdown":
            await self._export_markdown()
        elif backup_type == "git":
            await self._git_sync()
    
    async def _create_qdrant_snapshot(self):
        """Create a Qdrant snapshot"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_dir = os.path.join(self.backup_path, "snapshots")
            os.makedirs(snapshot_dir, exist_ok=True)
            
            # Create snapshot via Qdrant API
            import httpx
            qdrant_host = settings.qdrant_host
            qdrant_port = settings.qdrant_port
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://{qdrant_host}:{qdrant_port}/snapshots"
                )
                
                if response.status_code == 200:
                    print(f"✅ Qdrant snapshot created: {timestamp}")
                else:
                    print(f"⚠️ Qdrant snapshot failed: {response.text}")
                    
        except Exception as e:
            print(f"❌ Error creating Qdrant snapshot: {e}")
    
    async def _export_markdown(self):
        """Export all objects to markdown files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_dir = os.path.join(self.backup_path, "markdown", timestamp)
            os.makedirs(export_dir, exist_ok=True)
            
            # Get all objects from Qdrant
            client = qdrant_manager.get_client()
            
            collections = ["objects", "blocks"]
            for collection in collections:
                collection_dir = os.path.join(export_dir, collection)
                os.makedirs(collection_dir, exist_ok=True)
                
                results, _ = client.scroll(
                    collection_name=collection,
                    limit=10000,
                    with_payload=True,
                    with_vectors=False
                )
                
                for result in results:
                    payload = result.payload
                    title = payload.get("title", "untitled")
                    content = payload.get("content", "")
                    
                    # Create markdown file
                    filename = f"{result.id}.md"
                    filepath = os.path.join(collection_dir, filename)
                    
                    with open(filepath, "w") as f:
                        f.write(f"# {title}\n\n")
                        f.write(content or "")
            
            print(f"✅ Markdown export completed: {export_dir}")
            
        except Exception as e:
            print(f"❌ Error exporting markdown: {e}")
    
    async def _git_sync(self):
        """Sync to Git repository"""
        try:
            git_repo = settings.git_repo_url
            if not git_repo:
                print("⚠️ No Git repository configured")
                return
            
            git_dir = os.path.join(self.backup_path, "git")
            os.makedirs(git_dir, exist_ok=True)
            
            # Check if repo exists
            if not os.path.exists(os.path.join(git_dir, ".git")):
                # Clone repo
                subprocess.run(
                    ["git", "clone", git_repo, "."],
                    cwd=git_dir,
                    check=True
                )
            
            # Pull latest
            subprocess.run(
                ["git", "pull"],
                cwd=git_dir,
                check=True
            )
            
            # Export markdown to git directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_subdir = os.path.join(git_dir, "exports", timestamp)
            
            # Copy markdown export
            await self._export_markdown_to_dir(export_subdir)
            
            # Commit and push
            subprocess.run(
                ["git", "add", "."],
                cwd=git_dir,
                check=True
            )
            subprocess.run(
                ["git", "commit", "-m", f"Auto-export {timestamp}"],
                cwd=git_dir,
                check=False  # May fail if no changes
            )
            subprocess.run(
                ["git", "push"],
                cwd=git_dir,
                check=True
            )
            
            print(f"✅ Git sync completed")
            
        except Exception as e:
            print(f"❌ Error syncing to Git: {e}")
    
    async def _export_markdown_to_dir(self, export_dir: str):
        """Export markdown to a specific directory"""
        os.makedirs(export_dir, exist_ok=True)
        
        client = qdrant_manager.get_client()
        
        collections = ["objects", "blocks"]
        for collection in collections:
            collection_dir = os.path.join(export_dir, collection)
            os.makedirs(collection_dir, exist_ok=True)
            
            results, _ = client.scroll(
                collection_name=collection,
                limit=10000,
                with_payload=True,
                with_vectors=False
            )
            
            for result in results:
                payload = result.payload
                title = payload.get("title", "untitled")
                content = payload.get("content", "")
                
                filename = f"{result.id}.md"
                filepath = os.path.join(collection_dir, filename)
                
                with open(filepath, "w") as f:
                    f.write(f"# {title}\n\n")
                    f.write(content or "")


# Global backup service instance
backup_service = BackupService()
