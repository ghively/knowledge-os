"""Blocks Router - CRUD operations for blocks"""
import uuid
import logging

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.database.qdrant_client import qdrant_manager
from app.models.blocks import Block, BlockCreate, BlockUpdate, BlockListResponse
from app.services.websocket_manager import websocket_manager, WebSocketEvents
from app.services.embedding import embedding_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/object/{object_id}")
async def get_blocks_for_object(
    object_id: str,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all blocks for an object"""
    client = qdrant_manager.get_async_client()
    
    results = await client.scroll(
        collection_name="blocks",
        scroll_filter={
            "must": [{"key": "object_id", "match": {"value": object_id}}]
        },
        limit=limit,
        with_payload=True,
        with_vectors=False
    )
    
    blocks = []
    for result in results[0]:
        payload = result.payload
        payload["id"] = result.id
        blocks.append(payload)
    
    # Sort by order
    blocks.sort(key=lambda x: x.get("order", 0))
    
    return BlockListResponse(blocks=blocks)


@router.post("")
async def create_block(data: dict):
    """Create a new block"""
    client = qdrant_manager.get_async_client()
    
    object_id = data.get("object_id")
    content = data.get("content", "")
    block_type = data.get("type", "paragraph")
    level = data.get("level", 0)
    properties = data.get("properties", {})
    parent_id = data.get("parent_id")
    
    if not object_id:
        raise HTTPException(status_code=400, detail="object_id is required")
    
    # Generate ID
    block_id = str(uuid.uuid4())
    
    # Generate embedding
    embedding = await embedding_service.embed_text(content)
    
    # Get next order for this object
    existing_blocks = await client.scroll(
        collection_name="blocks",
        scroll_filter={
            "must": [{"key": "object_id", "match": {"value": object_id}}]
        },
        limit=1000,
        with_payload=False,
        with_vectors=False
    )
    next_order = len(existing_blocks[0])
    
    # Build payload
    payload = {
        "id": block_id,
        "object_id": object_id,
        "type": block_type,
        "content": content,
        "level": level,
        "order": next_order,
        "properties": properties,
        "parent_id": parent_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Insert into Qdrant
    await client.upsert(
        collection_name="blocks",
        points=[{
            "id": block_id,
            "vector": embedding.tolist(),
            "payload": payload
        }]
    )
    
    # Broadcast event
    await websocket_manager.broadcast(
        WebSocketEvents.block_created(block_id, object_id)
    )
    
    logger.info(f"Created block: {block_id} for object: {object_id}")
    
    return payload


@router.put("/{block_id}")
async def update_block(block_id: str, data: dict):
    """Update a block"""
    client = qdrant_manager.get_async_client()
    
    # Get existing block
    existing = await client.retrieve(
        collection_name="blocks",
        ids=[block_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Block not found")
    
    payload = existing[0].payload
    content_changed = False
    
    # Update fields
    if "content" in data:
        payload["content"] = data["content"]
        content_changed = True
    
    if "type" in data:
        payload["type"] = data["type"]
    
    if "level" in data:
        payload["level"] = data["level"]
    
    if "properties" in data:
        payload["properties"] = data["properties"]
    
    if "order" in data:
        payload["order"] = data["order"]
    
    if "parent_id" in data:
        payload["parent_id"] = data["parent_id"]
    
    payload["updated_at"] = datetime.now().isoformat()
    
    # Regenerate embedding if content changed
    if content_changed:
        embedding = await embedding_service.embed_text(payload["content"])
        await client.upsert(
            collection_name="blocks",
            points=[{
                "id": block_id,
                "vector": embedding.tolist(),
                "payload": payload
            }]
        )
    else:
        await client.set_payload(
            collection_name="blocks",
            payload=payload,
            points=[block_id]
        )
    
    # Broadcast event
    await websocket_manager.broadcast(
        WebSocketEvents.block_updated(block_id)
    )
    
    logger.info(f"Updated block: {block_id}")
    
    return payload


@router.post("/batch-update")
async def batch_update_blocks(data: dict):
    """Batch update blocks (for reordering)"""
    client = qdrant_manager.get_async_client()
    
    blocks = data.get("blocks", [])
    
    for block_data in blocks:
        block_id = block_data.get("id")
        if not block_id:
            continue
        
        # Get existing block
        existing = await client.retrieve(
            collection_name="blocks",
            ids=[block_id],
            with_payload=True,
            with_vectors=False
        )
        
        if not existing:
            continue
        
        payload = existing[0].payload
        
        if "order" in block_data:
            payload["order"] = block_data["order"]
        
        if "parent_id" in block_data:
            payload["parent_id"] = block_data["parent_id"]
        
        payload["updated_at"] = datetime.now().isoformat()
        
        await client.set_payload(
            collection_name="blocks",
            payload=payload,
            points=[block_id]
        )
    
    logger.info(f"Batch updated {len(blocks)} blocks")
    
    return {"message": f"Updated {len(blocks)} blocks"}


@router.delete("/{block_id}")
async def delete_block(block_id: str):
    """Delete a block"""
    client = qdrant_manager.get_async_client()
    
    # Check if block exists
    existing = await client.retrieve(
        collection_name="blocks",
        ids=[block_id],
        with_payload=False,
        with_vectors=False
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Block not found")
    
    # Delete from Qdrant
    await client.delete(
        collection_name="blocks",
        points_selector=[block_id]
    )
    
    # Broadcast event
    await websocket_manager.broadcast(
        WebSocketEvents.block_deleted(block_id)
    )
    
    logger.info(f"Deleted block: {block_id}")
    
    return {"message": "Block deleted"}
