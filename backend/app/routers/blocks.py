"""Blocks Router - CRUD operations for blocks"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime

from app.database.qdrant_client import qdrant_manager
from app.models.blocks import Block, BlockCreate, BlockUpdate, BlockBatchUpdate
from app.services.websocket_manager import websocket_manager, WebSocketEvents
from app.services.embedding import embedding_service

router = APIRouter()


@router.get("/object/{object_id}")
async def get_object_blocks(object_id: str):
    """Get all blocks for an object"""
    client = qdrant_manager.get_client()
    
    results = client.scroll(
        collection_name="blocks",
        scroll_filter={
            "must": [{"key": "object_id", "match": {"value": object_id}}]
        },
        limit=1000,
        with_payload=True
    )[0]
    
    blocks = []
    for result in results:
        payload = result.payload
        payload["id"] = result.id
        blocks.append(payload)
    
    # Sort by order
    blocks.sort(key=lambda b: b.get("order", 0))
    
    return {"blocks": blocks}


@router.post("")
async def create_block(block: BlockCreate, object_id: str):
    """Create a new block"""
    client = qdrant_manager.get_client()
    
    # Generate ID
    block_id = str(__import__('uuid').uuid4())
    
    # Get current max order for this object
    existing = client.scroll(
        collection_name="blocks",
        scroll_filter={
            "must": [{"key": "object_id", "match": {"value": object_id}}]
        },
        limit=1000,
        with_payload=True
    )[0]
    
    max_order = max([r.payload.get("order", 0) for r in existing] + [-1])
    
    # Generate embedding
    embedding = await embedding_service.embed_text(block.content)
    
    # Build payload
    payload = {
        "id": block_id,
        "object_id": object_id,
        "content": block.content,
        "type": block.type or "paragraph",
        "level": block.level or 0,
        "properties": block.properties.dict() if block.properties else {},
        "order": max_order + 1,
        "parent_id": block.parent_id,
        "references": [],
        "referenced_by": []
    }
    
    # Insert into Qdrant
    client.upsert(
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
    
    return payload


@router.put("/{block_id}")
async def update_block(block_id: str, update: BlockUpdate):
    """Update a block"""
    client = qdrant_manager.get_client()
    
    # Get existing
    existing = client.retrieve(
        collection_name="blocks",
        ids=[block_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Block not found")
    
    payload = existing[0].payload
    
    # Update fields
    if update.content is not None:
        payload["content"] = update.content
    
    if update.type is not None:
        payload["type"] = update.type
    
    if update.level is not None:
        payload["level"] = update.level
    
    if update.properties is not None:
        payload["properties"] = update.properties.dict()
    
    if update.order is not None:
        payload["order"] = update.order
    
    # Regenerate embedding if content changed
    if update.content is not None:
        embedding = await embedding_service.embed_text(update.content)
        
        client.upsert(
            collection_name="blocks",
            points=[{
                "id": block_id,
                "vector": embedding.tolist(),
                "payload": payload
            }]
        )
    else:
        client.set_payload(
            collection_name="blocks",
            payload=payload,
            points=[block_id]
        )
    
    # Broadcast event
    await websocket_manager.broadcast(
        WebSocketEvents.block_updated(block_id, update.content)
    )
    
    payload["id"] = block_id
    return payload


@router.post("/batch-update")
async def batch_update_blocks(update: BlockBatchUpdate):
    """Update multiple blocks at once (for reordering)"""
    client = qdrant_manager.get_client()
    
    for block in update.blocks:
        client.set_payload(
            collection_name="blocks",
            payload={
                "order": block.order,
                "parent_id": block.parent_id
            },
            points=[block.id]
        )
    
    return {"message": "Blocks updated", "count": len(update.blocks)}


@router.delete("/{block_id}")
async def delete_block(block_id: str):
    """Delete a block"""
    client = qdrant_manager.get_client()
    
    # Get block info for broadcast
    existing = client.retrieve(
        collection_name="blocks",
        ids=[block_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Block not found")
    
    object_id = existing[0].payload.get("object_id")
    
    # Delete
    client.delete(
        collection_name="blocks",
        points_selector=[block_id]
    )
    
    # Broadcast event
    await websocket_manager.broadcast(
        WebSocketEvents.block_updated(block_id)
    )
    
    return {"message": "Block deleted", "id": block_id, "object_id": object_id}
