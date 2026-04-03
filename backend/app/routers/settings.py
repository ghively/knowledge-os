"""Settings Router - Application settings and configuration"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime
import os
import json

from app.database.sqlite import sqlite_manager
from app.config import settings as app_settings
from app.services.websocket_manager import websocket_manager

router = APIRouter()

# Settings file path
SETTINGS_FILE = os.getenv("SETTINGS_PATH", "/app/data/settings.json")
WATCHED_FOLDERS_FILE = os.getenv("WATCHED_FOLDERS_PATH", "/app/data/watched_folders.json")


def _load_settings():
    """Load settings from file"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {
        "openclaw_url": app_settings.openclaw_url,
        "openclaw_token": "",
        "backup_snapshots": True,
        "backup_markdown": True,
        "backup_git": False,
        "git_repo_url": "",
        "auto_index": True
    }


def _save_settings(settings: dict):
    """Save settings to file"""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


@router.get("")
async def get_settings():
    """Get application settings"""
    return _load_settings()


@router.put("")
async def update_settings(data: dict):
    """Update application settings"""
    current = _load_settings()
    current.update(data)
    _save_settings(current)
    return current


@router.get("/watched-folders")
async def get_watched_folders():
    """Get list of watched folders"""
    if os.path.exists(WATCHED_FOLDERS_FILE):
        with open(WATCHED_FOLDERS_FILE, "r") as f:
            data = json.load(f)
            return {"folders": data.get("folders", [])}
    return {"folders": []}


@router.post("/watched-folders")
async def add_watched_folder(data: dict):
    """Add a new watched folder"""
    path = data.get("path")
    recursive = data.get("recursive", True)
    include_patterns = data.get("include_patterns")
    exclude_patterns = data.get("exclude_patterns")
    
    if not path:
        raise HTTPException(status_code=400, detail="path is required")
    
    # Load existing folders
    folders = []
    if os.path.exists(WATCHED_FOLDERS_FILE):
        with open(WATCHED_FOLDERS_FILE, "r") as f:
            data = json.load(f)
            folders = data.get("folders", [])
    
    # Generate ID
    import uuid
    folder_id = str(uuid.uuid4())
    
    # Add new folder
    new_folder = {
        "id": folder_id,
        "path": path,
        "recursive": recursive,
        "file_count": 0
    }
    
    if include_patterns:
        new_folder["include_patterns"] = include_patterns
    if exclude_patterns:
        new_folder["exclude_patterns"] = exclude_patterns
    
    folders.append(new_folder)
    
    # Save
    os.makedirs(os.path.dirname(WATCHED_FOLDERS_FILE), exist_ok=True)
    with open(WATCHED_FOLDERS_FILE, "w") as f:
        json.dump({"folders": folders}, f, indent=2)
    
    # Notify file watcher
    from app.services.file_watcher import file_watcher_service
    await file_watcher_service.add_folder(new_folder)
    
    return new_folder


@router.delete("/watched-folders/{folder_id}")
async def remove_watched_folder(folder_id: str):
    """Remove a watched folder"""
    if not os.path.exists(WATCHED_FOLDERS_FILE):
        raise HTTPException(status_code=404, detail="No watched folders found")
    
    with open(WATCHED_FOLDERS_FILE, "r") as f:
        data = json.load(f)
        folders = data.get("folders", [])
    
    # Find and remove folder
    folder = next((f for f in folders if f["id"] == folder_id), None)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    folders = [f for f in folders if f["id"] != folder_id]
    
    # Save
    with open(WATCHED_FOLDERS_FILE, "w") as f:
        json.dump({"folders": folders}, f, indent=2)
    
    # Notify file watcher
    from app.services.file_watcher import file_watcher_service
    await file_watcher_service.remove_folder(folder_id)
    
    return {"message": "Folder removed"}


@router.post("/backup")
async def trigger_backup(data: dict, background_tasks: BackgroundTasks):
    """Trigger a backup"""
    backup_type = data.get("type")
    
    if backup_type not in ["snapshot", "markdown", "git"]:
        raise HTTPException(status_code=400, detail="Invalid backup type")
    
    # Trigger backup in background
    from app.services.backup import backup_service
    background_tasks.add_task(backup_service.run_backup, backup_type)
    
    return {"message": f"{backup_type} backup started"}
