"""Context Builder Service - Builds rich context for task assignments"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.database.qdrant_client import qdrant_manager
from app.services.embedding import embedding_service


class ContextBuilderService:
    """Builds rich context for agent task assignments"""
    
    def __init__(self):
        self.max_context_tokens = 4000
        self.chunk_size = 1000
    
    async def build_task_context(self, task_id: str, object_id: str,
                                  parent_object_id: Optional[str] = None,
                                  additional_object_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Build full context for a task assignment"""
        
        client = qdrant_manager.get_client()
        context = {
            "task_id": task_id,
            "qdrant_pointers": {}
        }
        
        # 1. Get the task object itself
        task_object = self._get_object(object_id)
        if task_object:
            context["task_title"] = task_object.get("title", "Untitled")
            context["task_content"] = task_object.get("content", "")
            context["priority"] = task_object.get("properties", {}).get("priority", "medium")
            context["qdrant_pointers"]["task_object_id"] = object_id
        
        # 2. Get parent object context
        if parent_object_id:
            parent = self._get_object(parent_object_id)
            if parent:
                context["parent_object"] = {
                    "id": parent_object_id,
                    "title": parent.get("title"),
                    "type": parent.get("type"),
                    "content_preview": parent.get("content", "")[:500]
                }
                context["qdrant_pointers"]["parent_object_id"] = parent_object_id
        
        # 3. Find linked objects (via [[...]] in content)
        linked_objects = await self._find_linked_objects(object_id)
        context["linked_objects"] = linked_objects
        
        # 4. Find related files via semantic search
        related_files = await self._find_related_files(context.get("task_content", ""))
        context["related_files"] = related_files
        
        # 5. Find agent's relevant memories
        assigned_to = task_object.get("properties", {}).get("assigned_to") if task_object else None
        if assigned_to:
            memories = await self._find_relevant_memories(assigned_to, context.get("task_content", ""))
            context["relevant_memories"] = memories
        
        # 6. Get recent chat context
        recent_chat = await self._get_recent_chat(object_id)
        context["recent_chat"] = recent_chat
        
        # 7. Include additional user-specified objects
        if additional_object_ids:
            additional = []
            for obj_id in additional_object_ids:
                obj = self._get_object(obj_id)
                if obj:
                    additional.append({
                        "id": obj_id,
                        "title": obj.get("title"),
                        "type": obj.get("type"),
                        "content_preview": obj.get("content", "")[:300]
                    })
            context["additional_objects"] = additional
        
        return context
    
    def _get_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        """Get object by ID from Qdrant"""
        try:
            client = qdrant_manager.get_client()
            result = client.retrieve(
                collection_name="objects",
                ids=[object_id],
                with_payload=True,
                with_vectors=False
            )
            if result:
                return result[0].payload
            return None
        except Exception as e:
            print(f"Error getting object {object_id}: {e}")
            return None
    
    async def _find_linked_objects(self, object_id: str) -> List[Dict[str, Any]]:
        """Find objects linked to this object via relations"""
        try:
            client = qdrant_manager.get_client()
            
            # Search for relations where this object is the source
            results = client.scroll(
                collection_name="relations",
                scroll_filter={
                    "must": [{"key": "source_id", "match": {"value": object_id}}]
                },
                limit=20,
                with_payload=True
            )[0]
            
            linked = []
            for result in results:
                target_id = result.payload.get("target_id")
                if target_id:
                    obj = self._get_object(target_id)
                    if obj:
                        linked.append({
                            "id": target_id,
                            "title": obj.get("title"),
                            "type": obj.get("type"),
                            "relation_type": result.payload.get("relation_type"),
                            "content_preview": obj.get("content", "")[:200]
                        })
            
            return linked
        except Exception as e:
            print(f"Error finding linked objects: {e}")
            return []
    
    async def _find_related_files(self, query_text: str) -> List[Dict[str, Any]]:
        """Find files semantically related to the task"""
        try:
            if not query_text:
                return []
            
            # Generate embedding for query
            embedding = await embedding_service.embed_text(query_text)
            
            client = qdrant_manager.get_client()
            results = client.search(
                collection_name="files",
                query_vector=embedding.tolist(),
                limit=5,
                with_payload=True
            )
            
            files = []
            for result in results:
                payload = result.payload
                files.append({
                    "id": payload.get("id"),
                    "filename": payload.get("filename"),
                    "path": payload.get("path"),
                    "content_preview": payload.get("content_preview", "")[:200],
                    "score": result.score
                })
            
            return files
        except Exception as e:
            print(f"Error finding related files: {e}")
            return []
    
    async def _find_relevant_memories(self, agent_name: str, query_text: str) -> List[Dict[str, Any]]:
        """Find agent's memories relevant to this task"""
        try:
            if not query_text:
                return []
            
            # Generate embedding for query
            embedding = await embedding_service.embed_text(query_text)
            
            client = qdrant_manager.get_client()
            results = client.search(
                collection_name="agent_memories",
                query_vector=embedding.tolist(),
                query_filter={
                    "must": [{"key": "agent_name", "match": {"value": agent_name}}]
                },
                limit=5,
                with_payload=True
            )
            
            memories = []
            for result in results:
                payload = result.payload
                memories.append({
                    "id": payload.get("id"),
                    "content": payload.get("content"),
                    "memory_type": payload.get("memory_type"),
                    "importance": payload.get("importance"),
                    "timestamp": payload.get("timestamp"),
                    "score": result.score
                })
            
            return memories
        except Exception as e:
            print(f"Error finding memories: {e}")
            return []
    
    async def _get_recent_chat(self, object_id: str) -> List[Dict[str, Any]]:
        """Get recent chat messages related to this object"""
        try:
            client = qdrant_manager.get_client()
            
            # Search for chat logs mentioning this object
            results = client.scroll(
                collection_name="chat_logs",
                scroll_filter={
                    "must": [{"key": "related_object", "match": {"value": object_id}}]
                },
                limit=10,
                with_payload=True
            )[0]
            
            chats = []
            for result in results:
                payload = result.payload
                chats.append({
                    "session_id": payload.get("session_id"),
                    "agent_name": payload.get("agent_name"),
                    "message_type": payload.get("message_type"),
                    "content": payload.get("content"),
                    "timestamp": payload.get("timestamp")
                })
            
            return sorted(chats, key=lambda x: x.get("timestamp", ""), reverse=True)
        except Exception as e:
            print(f"Error getting recent chat: {e}")
            return []


# Global instance
context_builder = ContextBuilderService()
