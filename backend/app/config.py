"""Configuration for Knowledge OS Backend"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    app_name: str = "Knowledge OS"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None
    
    # SQLite
    sqlite_path: str = "./data/knowledge_os.db"
    
    # OpenClaw Gateway
    openclaw_gateway_url: str = "http://localhost:18789"
    openclaw_gateway_token: Optional[str] = None
    openclaw_enabled: bool = True
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"  # 384 dims
    clip_model: str = "openai/clip-vit-base-patch32"  # 512 dims
    
    # File Watcher
    watched_folders: List[str] = []
    max_file_size_mb: int = 50
    exclude_patterns: List[str] = [
        ".git", "node_modules", "__pycache__", ".venv", "venv",
        ".pytest_cache", "*.tmp", "*.log", ".DS_Store", "Thumbs.db",
        ".idea", ".vscode", "dist", "build", ".next"
    ]
    include_patterns: List[str] = [
        "*.md", "*.txt", "*.pdf", "*.docx", "*.doc",
        "*.py", "*.js", "*.ts", "*.jsx", "*.tsx",
        "*.html", "*.css", "*.scss", "*.json", "*.yaml", "*.yml",
        "*.rs", "*.go", "*.java", "*.cpp", "*.c", "*.h",
        "*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp", "*.svg"
    ]
    
    # Backup
    backup_enabled: bool = True
    snapshot_interval_hours: int = 24
    markdown_export_enabled: bool = True
    markdown_export_path: str = "./backups/markdown"
    markdown_export_interval_hours: int = 168  # Weekly
    git_backup_enabled: bool = False
    git_repo_path: str = "./backups/git"
    git_remote_url: Optional[str] = None
    
    # Context Builder
    max_context_tokens: int = 4000  # Leave room for response
    context_chunk_size: int = 1000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

# Ensure data directories exist
os.makedirs("./data", exist_ok=True)
os.makedirs("./backups/markdown", exist_ok=True)
os.makedirs("./backups/git", exist_ok=True)
