"""Files Router - File management and indexing"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime

from app.database.qdrant_client import qdrant_manager
from app.database.sqlite import sqlite_manager
from app.services.websocket_manager import websocket_manager, WebSocketEvents

router = APIRouter()


@router.get("")
async def list_files():
    """List all indexed files"""
    client = qdrant_manager.get_client()
    
    results, _ = client.scroll(
        collection_name="files",
        limit=1000,
        with_payload=True,
        with_vectors=False
    )
    
    files = []
    for result in results:
        payload = result.payload
        payload["id"] = result.id
        files.append(payload)
    
    return {"files": files}


@router.get("/{file_id}")
async def get_file(file_id: str):
    """Get file details"""
    client = qdrant_manager.get_client()
    
    results = client.retrieve(
        collection_name="files",
        ids=[file_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="File not found")
    
    payload = results[0].payload
    payload["id"] = results[0].id
    
    return payload


@router.post("/{file_id}/reindex")
async def reindex_file(file_id: str, background_tasks: BackgroundTasks):
    """Reindex a file"""
    client = qdrant_manager.get_client()
    
    # Get existing file
    results = client.retrieve(
        collection_name="files",
        ids=[file_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_data = results[0].payload
    file_path = file_data.get("path")
    
    # Trigger reindex in background
    background_tasks.add_task(_reindex_file_task, file_id, file_path)
    
    return {"message": "Reindexing started", "file_id": file_id}


async def _reindex_file_task(file_id: str, file_path: str):
    """Background task to reindex a file"""
    try:
        from app.services.file_watcher import file_watcher_service
        await file_watcher_service.process_file(file_path)
        
        # Broadcast event
        await websocket_manager.broadcast(
            WebSocketEvents.file_reindexed(file_id, file_path)
        )
    except Exception as e:
        print(f"Error reindexing file {file_id}: {e}")


@router.post("/notify")
async def file_notification(data: dict):
    """Receive file change notifications from file watcher"""
    event_type = data.get("event_type")
    path = data.get("path")
    folder_id = data.get("folder_id")
    
    if not event_type or not path:
        raise HTTPException(status_code=400, detail="event_type and path are required")
    
    # Process based on event type
    if event_type in ["created", "modified"]:
        # Index the file
        from app.services.file_watcher import file_watcher_service
        await file_watcher_service.process_file(path)
    elif event_type == "deleted":
        # Remove from index
        await _remove_file_from_index(path)
    elif event_type == "moved":
        # Update path in index
        dest_path = data.get("dest_path")
        if dest_path:
            await _update_file_path(path, dest_path)
    
    return {"status": "ok"}


async def _remove_file_from_index(file_path: str):
    """Remove a file from the index"""
    client = qdrant_manager.get_client()
    
    # Find file by path
    results, _ = client.scroll(
        collection_name="files",
        scroll_filter={
            "must": [{"key": "path", "match": {"value": file_path}}]
        },
        limit=1,
        with_payload=False,
        with_vectors=False
    )
    
    if results:
        client.delete(
            collection_name="files",
            points_selector=[results[0].id]
        )


async def _update_file_path(old_path: str, new_path: str):
    """Update file path in index"""
    client = qdrant_manager.get_client()
    
    # Find file by old path
    results, _ = client.scroll(
        collection_name="files",
        scroll_filter={
            "must": [{"key": "path", "match": {"value": old_path}}]
        },
        limit=1,
        with_payload=True,
        with_vectors=False
    )
    
    if results:
        file_id = results[0].id
        payload = results[0].payload
        payload["path"] = new_path
        
        client.set_payload(
            collection_name="files",
            payload=payload,
            points=[file_id]
        )
