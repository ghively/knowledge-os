"""Context Builder Service - Builds context packages for agent tasks."""
import logging
from typing import Dict, List, Optional

from app.database.qdrant_client import qdrant_manager
from app.database.sqlite import sqlite_manager
from app.services.embedding import embedding_service

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds context for task assignment."""

    async def build_task_context(
        self,
        task_id: str,
        additional_objects: Optional[List[str]] = None,
    ) -> Dict:
        client = qdrant_manager.get_async_client()
        settings = await sqlite_manager.get_setting("max_context_tokens", 4000)
        context = {
            "task_id": task_id,
            "task_title": None,
            "task_content": None,
            "priority": None,
            "task": None,
            "parent_object": None,
            "linked_objects": [],
            "related_files": [],
            "relevant_memories": [],
            "recent_chat": [],
            "additional_context_objects": [],
            "qdrant_pointers": {},
            "max_context_tokens": settings,
        }

        task_result = await client.retrieve(
            collection_name="objects",
            ids=[task_id],
            with_payload=True,
            with_vectors=False,
        )
        if not task_result:
            return context

        task_payload = dict(task_result[0].payload or {})
        task_payload["id"] = str(task_result[0].id)
        context["task"] = task_payload
        context["task_title"] = task_payload.get("title")
        context["task_content"] = task_payload.get("content")
        context["priority"] = task_payload.get("properties", {}).get("priority")
        context["qdrant_pointers"]["task_object_id"] = task_id

        properties = task_payload.get("properties", {})
        parent_id = properties.get("parent_id")
        linked_ids = list(dict.fromkeys(properties.get("linked_objects", []) + (additional_objects or [])))

        if parent_id:
            parent = await self._get_pointer("objects", parent_id)
            if parent:
                context["parent_object"] = parent
                context["qdrant_pointers"]["parent_object_id"] = parent_id

        for object_id in linked_ids:
            linked = await self._get_pointer("objects", object_id)
            if linked:
                if object_id in (additional_objects or []):
                    context["additional_context_objects"].append(linked)
                else:
                    context["linked_objects"].append(linked)
        context["qdrant_pointers"]["linked_object_ids"] = [item["id"] for item in context["linked_objects"]]
        context["qdrant_pointers"]["additional_context_object_ids"] = [
            item["id"] for item in context["additional_context_objects"]
        ]

        query_text = task_payload.get("content") or task_payload.get("title", "")
        if query_text:
            query_embedding = await embedding_service.embed_text(query_text)
            file_results = await client.search(
                collection_name="files",
                query_vector=query_embedding.tolist(),
                limit=5,
                with_payload=True,
                with_vectors=False,
            )
            for point in file_results:
                payload = dict(point.payload or {})
                payload["id"] = str(point.id)
                payload["score"] = point.score
                context["related_files"].append(payload)
        context["qdrant_pointers"]["related_file_ids"] = [item["id"] for item in context["related_files"]]

        assigned_to = properties.get("assigned_to")
        if assigned_to:
            memories = await client.scroll(
                collection_name="agent_memories",
                scroll_filter={"must": [{"key": "agent_name", "match": {"value": assigned_to}}]},
                limit=10,
                with_payload=True,
                with_vectors=False,
            )
            for point in memories[0]:
                payload = dict(point.payload or {})
                payload["id"] = str(point.id)
                context["relevant_memories"].append(payload)

            chat = await client.scroll(
                collection_name="chat_logs",
                scroll_filter={"must": [{"key": "agent_name", "match": {"value": assigned_to}}]},
                limit=10,
                with_payload=True,
                with_vectors=False,
            )
            recent = []
            for point in chat[0]:
                payload = dict(point.payload or {})
                payload["id"] = str(point.id)
                recent.append(payload)
            context["recent_chat"] = sorted(recent, key=lambda item: item.get("timestamp", ""))[-10:]
            context["qdrant_pointers"]["agent_memory_ids"] = [item["id"] for item in context["relevant_memories"]]
            context["qdrant_pointers"]["recent_chat_ids"] = [item["id"] for item in context["recent_chat"]]

        return context

    async def _get_pointer(self, collection: str, object_id: str):
        client = qdrant_manager.get_async_client()
        result = await client.retrieve(
            collection_name=collection,
            ids=[object_id],
            with_payload=True,
            with_vectors=False,
        )
        if not result:
            return None
        payload = dict(result[0].payload or {})
        payload["id"] = str(result[0].id)
        return payload


context_builder = ContextBuilder()
