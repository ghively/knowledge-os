"""SQLite Database Manager"""
import os
import logging
from typing import Optional
import aiosqlite

from app.config import settings

logger = logging.getLogger(__name__)


class SQLiteManager:
    """Manages SQLite database connection"""
    
    def __init__(self):
        self.db_path: str = settings.database_url.replace("sqlite:///", "")
        self.connection: Optional[aiosqlite.Connection] = None
    
    async def initialize(self):
        """Initialize SQLite database"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Open connection with proper settings
        self.connection = await aiosqlite.connect(
            self.db_path,
            check_same_thread=False  # Allow use across threads
        )
        
        # Enable foreign keys
        await self.connection.execute("PRAGMA foreign_keys = ON")
        
        # Create tables
        await self._create_tables()
        
        logger.info(f"SQLite initialized: {self.db_path}")
    
    async def _create_tables(self):
        """Create database tables"""
        # Settings table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Watched folders table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS watched_folders (
                id TEXT PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                recursive INTEGER DEFAULT 1,
                file_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.connection.commit()
    
    async def execute(self, query: str, parameters: tuple = ()):
        """Execute a query"""
        if not self.connection:
            raise RuntimeError("Database not initialized")
        
        async with self.connection.execute(query, parameters) as cursor:
            await self.connection.commit()
            return cursor
    
    async def fetchone(self, query: str, parameters: tuple = ()):
        """Fetch a single row"""
        if not self.connection:
            raise RuntimeError("Database not initialized")
        
        async with self.connection.execute(query, parameters) as cursor:
            return await cursor.fetchone()
    
    async def fetchall(self, query: str, parameters: tuple = ()):
        """Fetch all rows"""
        if not self.connection:
            raise RuntimeError("Database not initialized")
        
        async with self.connection.execute(query, parameters) as cursor:
            return await cursor.fetchall()
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            logger.info("SQLite connection closed")


# Global instance
sqlite_manager = SQLiteManager()
