"""SQLite Database Manager"""
import aiosqlite
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.config import settings


class SQLiteManager:
    """Manages SQLite connection for non-vector data"""
    
    def __init__(self):
        self.db_path = settings.sqlite_path
        self.connection: Optional[aiosqlite.Connection] = None
    
    async def initialize(self):
        """Initialize SQLite database"""
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row
        
        await self._create_tables()
        print("✅ SQLite initialized")
    
    async def _create_tables(self):
        """Create database tables"""
        
        # Watched folders
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS watched_folders (
                id TEXT PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                recursive BOOLEAN DEFAULT 1,
                include_patterns TEXT DEFAULT '["*"]',
                exclude_patterns TEXT DEFAULT '[".git", "node_modules"]',
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # File sync status
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS file_sync_status (
                file_path TEXT PRIMARY KEY,
                checksum TEXT,
                last_modified TIMESTAMP,
                index_status TEXT DEFAULT 'pending',
                error_message TEXT,
                object_id TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Backup log
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS backup_log (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        # Settings
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Agent sessions
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS agent_sessions (
                id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                task_id TEXT,
                status TEXT DEFAULT 'active',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                summary TEXT,
                messages_count INTEGER DEFAULT 0
            )
        """)
        
        await self.connection.commit()
    
    async def close(self):
        """Close connection"""
        if self.connection:
            await self.connection.close()
    
    # Settings operations
    async def get_setting(self, key: str) -> Optional[Any]:
        """Get a setting value"""
        async with self.connection.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row["value"])
            return None
    
    async def set_setting(self, key: str, value: Any):
        """Set a setting value"""
        await self.connection.execute(
            """INSERT OR REPLACE INTO settings (key, value, updated_at)
               VALUES (?, ?, ?)""",
            (key, json.dumps(value), datetime.now().isoformat())
        )
        await self.connection.commit()
    
    # Watched folders operations
    async def get_watched_folders(self) -> List[Dict[str, Any]]:
        """Get all watched folders"""
        async with self.connection.execute(
            "SELECT * FROM watched_folders WHERE enabled = 1"
        ) as cursor:
            rows = await cursor.fetchall()
            return [{
                "id": row["id"],
                "path": row["path"],
                "recursive": bool(row["recursive"]),
                "include_patterns": json.loads(row["include_patterns"]),
                "exclude_patterns": json.loads(row["exclude_patterns"]),
                "enabled": bool(row["enabled"]),
                "created_at": row["created_at"]
            } for row in rows]
    
    async def add_watched_folder(self, folder_id: str, path: str, 
                                  recursive: bool = True,
                                  include_patterns: List[str] = None,
                                  exclude_patterns: List[str] = None) -> bool:
        """Add a watched folder"""
        try:
            await self.connection.execute(
                """INSERT INTO watched_folders 
                   (id, path, recursive, include_patterns, exclude_patterns)
                   VALUES (?, ?, ?, ?, ?)""",
                (folder_id, path, recursive,
                 json.dumps(include_patterns or ["*"]),
                 json.dumps(exclude_patterns or [".git", "node_modules"]))
            )
            await self.connection.commit()
            return True
        except Exception as e:
            print(f"Error adding watched folder: {e}")
            return False
    
    async def remove_watched_folder(self, folder_id: str) -> bool:
        """Remove a watched folder"""
        try:
            await self.connection.execute(
                "DELETE FROM watched_folders WHERE id = ?",
                (folder_id,)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            print(f"Error removing watched folder: {e}")
            return False
    
    # File sync status operations
    async def get_file_sync_status(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file sync status"""
        async with self.connection.execute(
            "SELECT * FROM file_sync_status WHERE file_path = ?",
            (file_path,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    async def update_file_sync_status(self, file_path: str, 
                                       checksum: str = None,
                                       last_modified: datetime = None,
                                       index_status: str = None,
                                       error_message: str = None,
                                       object_id: str = None):
        """Update file sync status"""
        await self.connection.execute(
            """INSERT OR REPLACE INTO file_sync_status 
               (file_path, checksum, last_modified, index_status, error_message, object_id, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (file_path, checksum, 
             last_modified.isoformat() if last_modified else None,
             index_status, error_message, object_id,
             datetime.now().isoformat())
        )
        await self.connection.commit()
    
    # Backup log operations
    async def log_backup_start(self, backup_id: str, backup_type: str) -> bool:
        """Log backup start"""
        try:
            await self.connection.execute(
                """INSERT INTO backup_log (id, type, status, started_at)
                   VALUES (?, ?, 'started', ?)""",
                (backup_id, backup_type, datetime.now().isoformat())
            )
            await self.connection.commit()
            return True
        except Exception as e:
            print(f"Error logging backup start: {e}")
            return False
    
    async def log_backup_complete(self, backup_id: str, status: str, details: Dict = None):
        """Log backup completion"""
        await self.connection.execute(
            """UPDATE backup_log 
               SET status = ?, completed_at = ?, details = ?
               WHERE id = ?""",
            (status, datetime.now().isoformat(), 
             json.dumps(details) if details else None, backup_id)
        )
        await self.connection.commit()


# Global instance
sqlite_manager = SQLiteManager()
