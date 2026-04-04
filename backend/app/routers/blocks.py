"""Blocks Router - CRUD operations for blocks."""
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.database.qdrant_client import qdrant_manager
from app.models.blocks import BlockCreate, BlockListResponse, BlockUpdate
from app.services.embedding import embedding_service
from app.services.relations import relation_service
from app.services.websocket_manager import WebSocketEvents, websocket_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/object/{object_id}", response_model=BlockListResponse)
async def get_blocks_for_object(object_id: str, limit: int = Query(1000, ge=1, le=5000)):
    """Get all blocks for an object."""
    client = qdrant_manager.get_async_client()
    results = await client.scroll(
        collection_name="blocks",
        scroll_filter={"must": [{"key": "object_id", "match": {"value": object_id}}]},
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    blocks = []
    for point in results[0]:
        payload = dict(point.payload or {})
        payload["id"] = str(point.id)
        blocks.append(payload)

    blocks.sort(key=lambda item: (item.get("order", 0), item.get("created_at", "")))
    return BlockListResponse(blocks=blocks)


@router.post("")
async def create_block(block: BlockCreate):
    """Create a new block."""
    client = qdrant_manager.get_async_client()
    block_id = block.id or str(uuid.uuid4())
    embedding = await embedding_service.embed_text(block.content)

    existing_blocks = await get_blocks_for_object(block.object_id)
    payload = {
        "id": block_id,
        "object_id": block.object_id,
        "type": block.type,
        "content": block.content,
        "level": block.level,
        "order": block.order if block.order is not None else len(existing_blocks.blocks),
        "properties": (block.properties.model_dump(exclude_none=True) if block.properties else {}),
        "parent_id": block.parent_id,
        "references": [],
        "referenced_by": [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    await client.upsert(
        collection_name="blocks",
        points=[{"id": block_id, "vector": embedding.tolist(), "payload": payload}],
    )
    await relation_service.sync_block_references(block_id, block.object_id, block.content)
    await websocket_manager.broadcast(WebSocketEvents.block_created(block_id, block.object_id))
    return payload


@router.put("/{block_id}")
async def update_block(block_id: str, update: BlockUpdate):
    """Update a block."""
    client = qdrant_manager.get_async_client()
    existing = await client.retrieve(
        collection_name="blocks",
        ids=[block_id],
        with_payload=True,
        with_vectors=False,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Block not found")

    payload = dict(existing[0].payload or {})
    content_changed = False
    if update.content is not None:
        payload["content"] = update.content
        content_changed = True
    if update.type is not None:
        payload["type"] = update.type
    if update.level is not None:
        payload["level"] = update.level
    if update.properties is not None:
        payload["properties"] = update.properties.model_dump(exclude_none=True)
    if update.order is not None:
        payload["order"] = update.order
    if "parent_id" in update.model_fields_set:
        payload["parent_id"] = update.parent_id
    payload["updated_at"] = datetime.utcnow().isoformat()

    if content_changed:
        embedding = await embedding_service.embed_text(payload["content"])
        await client.upsert(
            collection_name="blocks",
            points=[{"id": block_id, "vector": embedding.tolist(), "payload": payload}],
        )
        await relation_service.sync_block_references(block_id, payload["object_id"], payload["content"])
    else:
        await client.set_payload(collection_name="blocks", payload=payload, points=[block_id])

    await websocket_manager.broadcast(WebSocketEvents.block_updated(block_id, payload["object_id"]))
    return payload


@router.post("/batch-update")
async def batch_update_blocks(data: dict):
    """Batch update block order and nesting."""
    client = qdrant_manager.get_async_client()
    updated = 0

    for block_data in data.get("blocks", []):
        block_id = block_data.get("id")
        if not block_id:
            continue
        existing = await client.retrieve(
            collection_name="blocks",
            ids=[block_id],
            with_payload=True,
            with_vectors=False,
        )
        if not existing:
            continue
        payload = dict(existing[0].payload or {})
        if "order" in block_data:
            payload["order"] = block_data["order"]
        if "parent_id" in block_data:
            payload["parent_id"] = block_data["parent_id"]
        if "level" in block_data:
            payload["level"] = block_data["level"]
        payload["updated_at"] = datetime.utcnow().isoformat()
        await client.set_payload(collection_name="blocks", payload=payload, points=[block_id])
        updated += 1

    return {"message": f"Updated {updated} blocks", "count": updated}


@router.delete("/{block_id}")
async def delete_block(block_id: str):
    """Delete a block."""
    client = qdrant_manager.get_async_client()
    existing = await client.retrieve(
        collection_name="blocks",
        ids=[block_id],
        with_payload=True,
        with_vectors=False,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Block not found")

    payload = dict(existing[0].payload or {})
    await relation_service.remove_block_references(block_id)
    await client.delete(collection_name="blocks", points_selector=[block_id])
    await websocket_manager.broadcast(WebSocketEvents.block_deleted(block_id, payload.get("object_id")))
    return {"message": "Block deleted", "id": block_id}
