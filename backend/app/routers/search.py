"""Search Router - Semantic search across all content"""
from fastapi import APIRouter, Query
from typing import List, Optional

from app.database.qdrant_client import qdrant_manager
from app.services.embedding import embedding_service

router = APIRouter()


@router.get("")
async def search(
    q: str = Query(..., description="Search query"),
    collection: Optional[str] = Query(None, description="Specific collection to search"),
    limit: int = Query(10, ge=1, le=100)
):
    """Semantic search across all content"""
    if not q:
        return {"results": [], "query": q}
    
    # Generate embedding for query
    embedding = await embedding_service.embed_text(q)
    
    client = qdrant_manager.get_client()
    all_results = []
    
    # Determine which collections to search
    collections = [collection] if collection else ["objects", "files", "blocks", "agent_memories"]
    
    for coll in collections:
        try:
            results = client.search(
                collection_name=coll,
                query_vector=embedding.tolist(),
                limit=limit,
                with_payload=True
            )
            
            for result in results:
                payload = result.payload
                payload["id"] = result.id
                payload["collection"] = coll
                payload["score"] = result.score
                all_results.append(payload)
                
        except Exception as e:
            print(f"Error searching {coll}: {e}")
    
    # Sort by score
    all_results.sort(key=lambda r: r.get("score", 0), reverse=True)
    
    return {
        "query": q,
        "results": all_results[:limit],
        "total": len(all_results)
    }


@router.get("/similar/{object_id}")
async def find_similar(
    object_id: str,
    collection: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=20)
):
    """Find objects similar to a given object"""
    client = qdrant_manager.get_client()
    
    # Determine collection
    search_collection = collection or "objects"
    
    # Get the source object
    result = client.retrieve(
        collection_name=search_collection,
        ids=[object_id],
        with_payload=True,
        with_vectors=True
    )
    
    if not result:
        return {"error": "Object not found", "results": []}
    
    source_vector = result[0].vector
    
    # Search for similar
    similar = client.search(
        collection_name=search_collection,
        query_vector=source_vector,
        limit=limit + 1,  # +1 to exclude self
        with_payload=True
    )
    
    # Filter out the source object
    results = []
    for item in similar:
        if item.id != object_id:
            payload = item.payload
            payload["id"] = item.id
            payload["score"] = item.score
            results.append(payload)
    
    return {
        "source_id": object_id,
        "results": results[:limit]
    }
