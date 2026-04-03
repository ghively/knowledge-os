"""Application Configuration"""
import os
from typing import List


class Settings:
    """Application settings"""
    
    # Qdrant settings
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    
    # SQLite settings
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///app/data/knowledge_os.db")
    
    # OpenClaw settings
    openclaw_url: str = os.getenv("OPENCLAW_URL", "http://localhost:18789")
    openclaw_token: str = os.getenv("OPENCLAW_TOKEN", "")
    
    # Backup settings
    backup_path: str = os.getenv("BACKUP_PATH", "/app/backups")
    
    # CORS settings
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins from environment"""
        origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
        return [origin.strip() for origin in origins.split(",")]
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # File watching
    watched_folders_path: str = os.getenv("WATCHED_FOLDERS_PATH", "/app/data/watched_folders.json")
    
    # Git settings
    git_repo_url: str = os.getenv("GIT_REPO_URL", "")


# Global settings instance
settings = Settings()
