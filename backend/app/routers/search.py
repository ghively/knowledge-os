"""Search Router - Semantic and exact search"""
import logging

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.database.qdrant_client import qdrant_manager
from app.services.embedding import embedding_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def search(
    q: str,
    type: str = Query("semantic", regex="^(semantic|exact)$"),
    collection: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """Search across all content"""
    client = qdrant_manager.get_async_client()
    
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    results = []
    
    # Determine which collections to search
    collections = [collection] if collection else ["objects", "blocks", "files", "chat_logs"]
    
    for coll in collections:
        try:
            if type == "semantic":
                # Generate embedding for query
                query_embedding = await embedding_service.embed_text(q)
                
                # Search using async client
                search_results = await client.search(
                    collection_name=coll,
                    query_vector=query_embedding.tolist(),
                    limit=limit,
                    with_payload=True,
                    with_vectors=False
                )
                
                for result in search_results:
                    payload = result.payload
                    payload["id"] = result.id
                    payload["score"] = result.score
                    payload["collection"] = coll
                    results.append(payload)
                    
            else:
                # Exact match search
                scroll_results = await client.scroll(
                    collection_name=coll,
                    scroll_filter={
                        "must": [
                            {"key": "content", "match": {"text": q}}
                        ]
                    },
                    limit=limit,
                    with_payload=True,
                    with_vectors=False
                )
                
                for result in scroll_results[0]:
                    payload = result.payload
                    payload["id"] = result.id
                    payload["score"] = 1.0  # Exact match
                    payload["collection"] = coll
                    results.append(payload)
                    
        except Exception as e:
            logger.warning(f"Error searching collection {coll}: {e}")
            continue
    
    # Sort by score (descending)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return {"results": results[:limit]}


@router.get("/similar/{object_id}")
async def find_similar(
    object_id: str,
    collection: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50)
):
    """Find similar objects"""
    client = qdrant_manager.get_async_client()
    
    # Get source object
    source_collection = collection or "objects"
    
    source = await client.retrieve(
        collection_name=source_collection,
        ids=[object_id],
        with_payload=True,
        with_vectors=True
    )
    
    if not source:
        raise HTTPException(status_code=404, detail="Object not found")
    
    source_vector = source[0].vector
    
    # Search for similar vectors
    results = await client.search(
        collection_name=source_collection,
        query_vector=source_vector,
        limit=limit + 1,  # +1 to exclude self
        with_payload=True,
        with_vectors=False
    )
    
    # Filter out the source object
    similar = []
    for result in results:
        if result.id != object_id:
            payload = result.payload
            payload["id"] = result.id
            payload["score"] = result.score
            similar.append(payload)
    
    return {"results": similar[:limit]}
