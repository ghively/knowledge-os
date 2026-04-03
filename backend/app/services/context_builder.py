"""Context Builder Service - Builds context for agent tasks"""
import logging
from typing import Dict, List, Optional

from app.database.qdrant_client import qdrant_manager
from app.services.embedding import embedding_service

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds context for agent tasks"""
    
    async def build_task_context(
        self,
        task_id: str,
        additional_objects: Optional[List[str]] = None
    ) -> Dict:
        """Build context for a task"""
        client = qdrant_manager.get_async_client()
        
        context = {
            "task_id": task_id,
            "parent_object": None,
            "linked_objects": [],
            "related_files": [],
            "agent_memories": [],
            "recent_chat": []
        }
        
        # Get task object
        task_result = await client.retrieve(
            collection_name="objects",
            ids=[task_id],
            with_payload=True,
            with_vectors=False
        )
        
        if not task_result:
            return context
        
        task = task_result[0].payload
        
        # Get parent object if exists
        parent_id = task.get("properties", {}).get("parent_id")
        if parent_id:
            parent_result = await client.retrieve(
                collection_name="objects",
                ids=[parent_id],
                with_payload=True,
                with_vectors=False
            )
            if parent_result:
                context["parent_object"] = {
                    "id": parent_id,
                    "title": parent_result[0].payload.get("title"),
                    "content": parent_result[0].payload.get("content", "")[:500]
                }
        
        # Get linked objects
        linked_ids = task.get("properties", {}).get("linked_objects", [])
        for obj_id in linked_ids:
            obj_result = await client.retrieve(
                collection_name="objects",
                ids=[obj_id],
                with_payload=True,
                with_vectors=False
            )
            if obj_result:
                context["linked_objects"].append({
                    "id": obj_id,
                    "title": obj_result[0].payload.get("title"),
                    "type": obj_result[0].payload.get("type")
                })
        
        # Get additional objects if provided
        if additional_objects:
            for obj_id in additional_objects:
                obj_result = await client.retrieve(
                    collection_name="objects",
                    ids=[obj_id],
                    with_payload=True,
                    with_vectors=False
                )
                if obj_result:
                    context["linked_objects"].append({
                        "id": obj_id,
                        "title": obj_result[0].payload.get("title"),
                        "type": obj_result[0].payload.get("type")
                    })
        
        # Get related files using semantic search
        task_content = task.get("content", "") or task.get("title", "")
        if task_content:
            query_embedding = await embedding_service.embed_text(task_content)
            
            file_results = await client.search(
                collection_name="files",
                query_vector=query_embedding.tolist(),
                limit=5,
                with_payload=True,
                with_vectors=False
            )
            
            for result in file_results:
                context["related_files"].append({
                    "id": result.id,
                    "name": result.payload.get("name"),
                    "path": result.payload.get("path"),
                    "score": result.score
                })
        
        # Get agent memories
        assigned_to = task.get("properties", {}).get("assigned_to")
        if assigned_to:
            memory_results = await client.scroll(
                collection_name="agent_memories",
                scroll_filter={
                    "must": [{"key": "agent_name", "match": {"value": assigned_to}}]
                },
                limit=10,
                with_payload=True,
                with_vectors=False
            )
            
            for result in memory_results[0]:
                context["agent_memories"].append({
                    "id": result.id,
                    "content": result.payload.get("content", "")[:200],
                    "timestamp": result.payload.get("timestamp")
                })
        
        return context


# Global context builder instance
context_builder = ContextBuilder()
