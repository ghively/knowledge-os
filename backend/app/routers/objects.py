"""Objects Router - CRUD operations for objects"""
import uuid
import logging

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.database.qdrant_client import qdrant_manager
from app.models.objects import Object, ObjectCreate, ObjectUpdate, ObjectListResponse
from app.services.websocket_manager import websocket_manager, WebSocketEvents
from app.services.embedding import embedding_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=ObjectListResponse)
async def list_objects(
    type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all objects with optional filtering"""
    client = qdrant_manager.get_async_client()
    
    # Build filter
    query_filter = None
    if type:
        query_filter = {
            "must": [{"key": "type", "match": {"value": type}}]
        }
    
    # Scroll through collection using async client
    results = await client.scroll(
        collection_name="objects",
        scroll_filter=query_filter,
        limit=limit,
        offset=offset,
        with_payload=True,
        with_vectors=False
    )
    
    objects = []
    for result in results[0]:  # results is a tuple (points, next_offset)
        payload = result.payload
        payload["id"] = result.id
        objects.append(payload)
    
    return ObjectListResponse(
        objects=objects,
        total=len(objects)
    )


@router.get("/{object_id}")
async def get_object(object_id: str):
    """Get a single object by ID"""
    client = qdrant_manager.get_async_client()
    
    results = await client.retrieve(
        collection_name="objects",
        ids=[object_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="Object not found")
    
    payload = results[0].payload
    payload["id"] = results[0].id
    
    return payload


@router.post("")
async def create_object(obj: ObjectCreate):
    """Create a new object"""
    client = qdrant_manager.get_async_client()
    
    # Generate ID
    object_id = str(uuid.uuid4())
    
    # Generate embedding from content or title
    content = obj.content or obj.title
    embedding = await embedding_service.embed_text(content)
    
    # Build payload
    properties = obj.properties.model_dump() if obj.properties else {}
    properties["created_at"] = datetime.now().isoformat()
    properties["updated_at"] = datetime.now().isoformat()
    
    payload = {
        "id": object_id,
        "type": obj.type,
        "title": obj.title,
        "icon": obj.icon,
        "content": content,
        "properties": properties,
        "layout": obj.layout or "default"
    }
    
    # Insert into Qdrant using async client
    await client.upsert(
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
    
    logger.info(f"Created object: {object_id} ({obj.type})")
    
    return payload


@router.put("/{object_id}")
async def update_object(object_id: str, update: ObjectUpdate):
    """Update an object"""
    client = qdrant_manager.get_async_client()
    
    # Get existing object
    existing = await client.retrieve(
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
        payload["properties"] = update.properties.model_dump()
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
        
        await client.upsert(
            collection_name="objects",
            points=[{
                "id": object_id,
                "vector": embedding.tolist(),
                "payload": payload
            }]
        )
    else:
        # Just update payload without regenerating embedding
        await client.set_payload(
            collection_name="objects",
            payload=payload,
            points=[object_id]
        )
    
    # Broadcast event
    await websocket_manager.broadcast(
        WebSocketEvents.object_updated(object_id, changes)
    )
    
    logger.info(f"Updated object: {object_id}")
    
    return payload


@router.delete("/{object_id}")
async def delete_object(object_id: str):
    """Delete an object"""
    client = qdrant_manager.get_async_client()
    
    # Check if object exists
    existing = await client.retrieve(
        collection_name="objects",
        ids=[object_id],
        with_payload=False,
        with_vectors=False
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Object not found")
    
    # Delete from Qdrant
    await client.delete(
        collection_name="objects",
        points_selector=[object_id]
    )
    
    # Broadcast event
    await websocket_manager.broadcast(
        WebSocketEvents.object_deleted(object_id)
    )
    
    logger.info(f"Deleted object: {object_id}")
    
    return {"message": "Object deleted"}


@router.get("/{object_id}/relations")
async def get_object_relations(object_id: str):
    """Get relations for an object"""
    client = qdrant_manager.get_async_client()
    
    # Query relations collection
    results = await client.scroll(
        collection_name="relations",
        scroll_filter={
            "must": [{"key": "source_id", "match": {"value": object_id}}]
        },
        limit=100,
        with_payload=True,
        with_vectors=False
    )
    
    relations = []
    for result in results[0]:
        payload = result.payload
        payload["id"] = result.id
        relations.append(payload)
    
    return {"relations": relations}
