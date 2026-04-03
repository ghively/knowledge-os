"""Objects Router - CRUD operations for objects"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.database.qdrant_client import qdrant_manager
from app.models.objects import Object, ObjectCreate, ObjectUpdate, ObjectListResponse
from app.services.websocket_manager import websocket_manager, WebSocketEvents
from app.services.embedding import embedding_service

router = APIRouter()


@router.get("", response_model=ObjectListResponse)
async def list_objects(
    type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all objects with optional filtering"""
    client = qdrant_manager.get_client()
    
    # Build filter
    query_filter = None
    if type:
        query_filter = {
            "must": [{"key": "type", "match": {"value": type}}]
        }
    
    # Scroll through collection
    results, next_offset = client.scroll(
        collection_name="objects",
        scroll_filter=query_filter,
        limit=limit,
        offset=offset,
        with_payload=True,
        with_vectors=False
    )
    
    objects = []
    for result in results:
        payload = result.payload
        payload["id"] = result.id
        objects.append(payload)
    
    return ObjectListResponse(
        objects=objects,
        total=len(objects)  # Note: Qdrant doesn't give total count easily
    )


@router.get("/{object_id}")
async def get_object(object_id: str):
    """Get a single object by ID"""
    client = qdrant_manager.get_client()
    
    result = client.retrieve(
        collection_name="objects",
        ids=[object_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Object not found")
    
    payload = result[0].payload
    payload["id"] = result[0].id
    return payload


@router.post("")
async def create_object(obj: ObjectCreate):
    """Create a new object"""
    client = qdrant_manager.get_client()
    
    # Generate ID
    object_id = str(__import__('uuid').uuid4())
    
    # Build content for embedding
    content = obj.content or obj.title
    
    # Generate embedding
    embedding = await embedding_service.embed_text(content)
    
    # Set timestamps
    now = datetime.now().isoformat()
    properties = obj.properties or {}
    properties.created_at = now
    properties.updated_at = now
    
    # Build payload
    payload = {
        "id": object_id,
        "type": obj.type,
        "title": obj.title,
        "icon": obj.icon,
        "content": content,
        "properties": properties.dict() if properties else {},
        "layout": obj.layout or "default"
    }
    
    # Insert into Qdrant
    client.upsert(
        collection_name="objects",
        points=[{
            "id": object_id,
            "vector": embedding.tolist(),
            "payload": payload
        }]
    )
    
    # Broadcast event
    await websocket_manager.broadcast(
        WebSocketEvents.object_created(object_id, obj.type, obj.title)
    )
    
    return payload


@router.put("/{object_id}")
async def update_object(object_id: str, update: ObjectUpdate):
    """Update an object"""
    client = qdrant_manager.get_client()
    
    # Get existing object
    existing = client.retrieve(
        collection_name="objects",
        ids=[object_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Object not found")
    
    payload = existing[0].payload
    changes = []
    
    # Update fields
    if update.title is not None:
        payload["title"] = update.title
        changes.append("title")
    
    if update.icon is not None:
        payload["icon"] = update.icon
        changes.append("icon")
    
    if update.content is not None:
        payload["content"] = update.content
        changes.append("content")
    
    if update.properties is not None:
        payload["properties"] = update.properties.dict()
        changes.append("properties")
    
    if update.layout is not None:
        payload["layout"] = update.layout
        changes.append("layout")
    
    # Update timestamp
    payload["properties"]["updated_at"] = datetime.now().isoformat()
    
    # Regenerate embedding if content changed
    if "content" in changes or "title" in changes:
        embedding = await embedding_service.embed_text(
            payload["content"] or payload["title"]
        )
        
        client.upsert(
            collection_name="objects",
            points=[{
                "id": object_id,
                "vector": embedding.tolist(),
                "payload": payload
            }]
        )
    else:
        # Just update payload
        client.set_payload(
            collection_name="objects",
            payload=payload,
            points=[object_id]
        )
    
    # Broadcast event
    await websocket_manager.broadcast(
        WebSocketEvents.object_updated(object_id, changes)
    )
    
    payload["id"] = object_id
    return payload


@router.delete("/{object_id}")
async def delete_object(object_id: str):
    """Delete an object"""
    client = qdrant_manager.get_client()
    
    # Check if exists
    existing = client.retrieve(
        collection_name="objects",
        ids=[object_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Object not found")
    
    # Delete
    client.delete(
        collection_name="objects",
        points_selector=[object_id]
    )
    
    # Broadcast event
    await websocket_manager.broadcast(
        WebSocketEvents.object_deleted(object_id)
    )
    
    return {"message": "Object deleted", "id": object_id}


@router.get("/{object_id}/relations")
async def get_object_relations(object_id: str):
    """Get all relations for an object"""
    client = qdrant_manager.get_client()
    
    # Get outgoing relations
    outgoing = client.scroll(
        collection_name="relations",
        scroll_filter={
            "must": [{"key": "source_id", "match": {"value": object_id}}]
        },
        limit=100,
        with_payload=True
    )[0]
    
    # Get incoming relations
    incoming = client.scroll(
        collection_name="relations",
        scroll_filter={
            "must": [{"key": "target_id", "match": {"value": object_id}}]
        },
        limit=100,
        with_payload=True
    )[0]
    
    return {
        "outgoing": [r.payload for r in outgoing],
        "incoming": [r.payload for r in incoming]
    }
