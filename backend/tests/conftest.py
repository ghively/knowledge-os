"""
Shared pytest fixtures for Knowledge OS backend tests.
"""

import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from qdrant_client import models as qdrant_models
from qdrant_client.http.models import PayloadSchema

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client with realistic collection and point operations."""
    mock_client = MagicMock()

    # Storage for mock data
    mock_storage = {
        "collections": {
            "objects": {},
            "blocks": {},
            "relations": {},
            "files": {},
            "images": {},
            "code": {},
            "agent_memories": {},
            "chat_logs": {},
        },
        "points": {},
    }

    # Mock collection operations
    def mock_create_collection(collection_name, vectors_config, **kwargs):
        mock_storage["collections"][collection_name] = {}

    def mock_get_collection(collection_name):
        if collection_name in mock_storage["collections"]:
            return MagicMock(result=MagicMock(status="green"))
        raise Exception("Collection not found")

    def mock_delete_collection(collection_name):
        if collection_name in mock_storage["collections"]:
            del mock_storage["collections"][collection_name]

    def mock_create_payload_index(collection_name, payload_schema_path, **kwargs):
        return None

    # Mock point operations
    def mock_upsert(collection_name, points):
        if collection_name not in mock_storage["collections"]:
            return
        for point in points:
            if isinstance(point, qdrant_models.PointStruct):
                mock_storage["points"][point.id] = point
            elif isinstance(point, dict):
                mock_storage["points"][point["id"]] = point

    def mock_search(collection_name, query_vector, limit=10, **kwargs):
        points = list(mock_storage["points"].values())
        # Return first N points as mock results
        results = []
        for i, point in enumerate(points[:limit]):
            if isinstance(point, qdrant_models.PointStruct):
                results.append(
                    qdrant_models.ScoredPoint(
                        id=point.id,
                        score=0.9 - (i * 0.1),
                        payload=point.payload,
                        vector=point.vector,
                    )
                )
        return results

    def mock_recommend(collection_name, positive, limit=10, **kwargs):
        return mock_search(collection_name, [], limit)

    def mock_delete(collection_name, points_selector, **kwargs):
        if hasattr(points_selector, "points"):
            for point_id in points_selector.points:
                mock_storage["points"].pop(point_id, None)
        elif hasattr(points_selector, "ids"):
            for point_id in points_selector.ids:
                mock_storage["points"].pop(point_id, None)

    def mock_retrieve(collection_name, ids, **kwargs):
        results = []
        for point_id in ids:
            if point_id in mock_storage["points"]:
                point = mock_storage["points"][point_id]
                if isinstance(point, qdrant_models.PointStruct):
                    results.append(
                        qdrant_models.Record(
                            id=point.id,
                            payload=point.payload,
                            vector=point.vector,
                        )
                    )
        return results

    def mock_count(collection_name, **kwargs):
        count = len(
            [
                p
                for p in mock_storage["points"].values()
                if isinstance(p, qdrant_models.PointStruct)
            ]
        )
        return MagicMock(count=count)

    def mock_scroll(collection_name, limit=10, **kwargs):
        points = list(mock_storage["points"].values())[:limit]
        records = []
        for point in points:
            if isinstance(point, qdrant_models.PointStruct):
                records.append(
                    qdrant_models.Record(
                        id=point.id, payload=point.payload, vector=point.vector
                    )
                )
        return records, None

    # Assign mock methods
    mock_client.create_collection = mock_create_collection
    mock_client.get_collection = mock_get_collection
    mock_client.delete_collection = mock_delete_collection
    mock_client.create_payload_index = mock_create_payload_index
    mock_client.upsert = mock_upsert
    mock_client.search = mock_search
    mock_client.recommend = mock_recommend
    mock_client.delete = mock_delete
    mock_client.retrieve = mock_retrieve
    mock_client.count = mock_count
    mock_client.scroll = mock_scroll

    # Store reference for test access
    mock_client._storage = mock_storage

    return mock_client


@pytest.fixture
def mock_async_qdrant_client():
    """Mock async Qdrant client."""
    mock_client = AsyncMock()

    # Storage for mock data
    mock_storage = {
        "collections": {
            "objects": {},
            "blocks": {},
            "relations": {},
            "files": {},
            "images": {},
            "code": {},
            "agent_memories": {},
            "chat_logs": {},
        },
        "points": {},
    }

    # Mock point operations
    async def mock_upsert(collection_name, points):
        for point in points:
            if isinstance(point, qdrant_models.PointStruct):
                mock_storage["points"][point.id] = point
            elif isinstance(point, dict):
                mock_storage["points"][point["id"]] = point

    async def mock_search(collection_name, query_vector, limit=10, **kwargs):
        points = list(mock_storage["points"].values())
        results = []
        for i, point in enumerate(points[:limit]):
            if isinstance(point, qdrant_models.PointStruct):
                results.append(
                    qdrant_models.ScoredPoint(
                        id=point.id,
                        score=0.9 - (i * 0.1),
                        payload=point.payload,
                        vector=point.vector,
                    )
                )
        return results

    async def mock_recommend(collection_name, positive, limit=10, **kwargs):
        return await mock_search(collection_name, [], limit)

    async def mock_delete(collection_name, points_selector, **kwargs):
        if hasattr(points_selector, "points"):
            for point_id in points_selector.points:
                mock_storage["points"].pop(point_id, None)
        elif hasattr(points_selector, "ids"):
            for point_id in points_selector.ids:
                mock_storage["points"].pop(point_id, None)

    async def mock_retrieve(collection_name, ids, **kwargs):
        results = []
        for point_id in ids:
            if point_id in mock_storage["points"]:
                point = mock_storage["points"][point_id]
                if isinstance(point, qdrant_models.PointStruct):
                    results.append(
                        qdrant_models.Record(
                            id=point.id,
                            payload=point.payload,
                            vector=point.vector,
                        )
                    )
        return results

    async def mock_count(collection_name, **kwargs):
        count = len(
            [
                p
                for p in mock_storage["points"].values()
                if isinstance(p, qdrant_models.PointStruct)
            ]
        )
        return MagicMock(count=count)

    mock_client.upsert = mock_upsert
    mock_client.search = mock_search
    mock_client.recommend = mock_recommend
    mock_client.delete = mock_delete
    mock_client.retrieve = mock_retrieve
    mock_client.count = mock_count
    mock_client._storage = mock_storage

    return mock_client


@pytest.fixture
def mock_sqlite_manager():
    """Mock SQLite database manager."""
    mock_manager = MagicMock()

    # Mock storage
    storage = {
        "settings": {},
        "watched_folders": [],
        "file_sync_status": {},
        "backup_log": [],
        "agent_sessions": {},
    }

    def mock_execute(query, params=None):
        return MagicMock(lastrowid=1, rowcount=1)

    def mock_executemany(query, params):
        return MagicMock(rowcount=len(params) if params else 0)

    def mock_fetchone(query, params=None):
        return None

    def mock_fetchall(query, params=None):
        return []

    def mock_upsert_setting(key, value):
        storage["settings"][key] = value

    def mock_get_setting(key, default=None):
        return storage["settings"].get(key, default)

    mock_manager.execute = mock_execute
    mock_manager.executemany = mock_executemany
    mock_manager.fetchone = mock_fetchone
    mock_manager.fetchall = mock_fetchall
    mock_manager.upsert_setting = mock_upsert_setting
    mock_manager.get_setting = mock_get_setting
    mock_manager._storage = storage

    return mock_manager


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service with deterministic vectors."""
    mock_service = MagicMock()

    def mock_embed_text(text):
        # Deterministic 384-dim vector based on text hash
        import hashlib

        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(hash_val + i) % 1000 / 1000 for i in range(384)]

    def mock_embed_texts(texts):
        return [mock_embed_text(text) for text in texts]

    def mock_embed_image(image_path):
        # Deterministic 512-dim vector
        import hashlib

        hash_val = int(hashlib.md5(image_path.encode()).hexdigest(), 16)
        return [(hash_val + i) % 1000 / 1000 for i in range(512)]

    mock_service.embed_text = mock_embed_text
    mock_service.embed_texts = mock_embed_texts
    mock_service.embed_image = mock_embed_image

    return mock_service


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager."""
    mock_manager = MagicMock()

    mock_connections = {}

    async def mock_connect(websocket, client_id, channel="system"):
        mock_connections[client_id] = websocket

    async def mock_disconnect(client_id):
        mock_connections.pop(client_id, None)

    async def mock_broadcast(message, channel="system"):
        pass  # Mock broadcast

    async def mock_handle_message(websocket, client_id):
        pass  # Mock message handling

    mock_manager.connect = mock_connect
    mock_manager.disconnect = mock_disconnect
    mock_manager.broadcast = mock_broadcast
    mock_manager.handle_message = mock_handle_message
    mock_manager._connections = mock_connections

    return mock_manager


@pytest.fixture
def mock_openclaw_service():
    """Mock OpenClaw service."""
    mock_service = MagicMock()

    async def mock_send_message(agent_name, content, session_id=None):
        return {
            "response": "Mock response",
            "session_id": session_id or "test-session",
            "timestamp": "2024-01-01T00:00:00Z",
        }

    async def mock_assign_task(agent_name, task_id, context):
        return {"status": "assigned", "agent": agent_name, "task_id": task_id}

    async def mock_get_agent_status(agent_name):
        return {
            "name": agent_name,
            "status": "idle",
            "current_task": None,
            "last_seen": "2024-01-01T00:00:00Z",
        }

    mock_service.send_message = mock_send_message
    mock_service.assign_task = mock_assign_task
    mock_service.get_agent_status = mock_get_agent_status

    return mock_service


@pytest.fixture
async def test_client(mock_qdrant_client, mock_embedding_service):
    """Create test HTTP client with mocked dependencies."""
    from app.main import app
    from app.database import qdrant_client

    # Patch the qdrant_client singleton
    with patch.object(qdrant_client, "get_client", return_value=mock_qdrant_client), \
         patch.object(qdrant_client, "get_async_client", return_value=mock_async_qdrant_client()), \
         patch("app.services.embedding.embedding_service", mock_embedding_service):

        # Create transport
        transport = ASGITransport(app=app)

        # Create async client
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.fixture
def sample_object_data():
    """Sample object data for testing."""
    return {
        "id": "test-object-1",
        "payload": {
            "title": "Test Object",
            "content": "Test content",
            "object_type": "note",
            "tags": ["test", "sample"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
        "vector": [0.1] * 384,
    }


@pytest.fixture
def sample_block_data():
    """Sample block data for testing."""
    return {
        "id": "test-block-1",
        "payload": {
            "object_id": "test-object-1",
            "content": "Test block content",
            "block_type": "text",
            "order": 0,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
        "vector": [0.1] * 384,
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "id": "test-task-1",
        "payload": {
            "title": "Test Task",
            "description": "Test task description",
            "status": "todo",
            "priority": "medium",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
        "vector": [0.1] * 384,
    }


@pytest.fixture
def sample_relation_data():
    """Sample relation data for testing."""
    return {
        "id": "test-relation-1",
        "payload": {
            "source_type": "object",
            "source_id": "test-object-1",
            "target_type": "object",
            "target_id": "test-object-2",
            "relation_type": "references",
            "created_at": "2024-01-01T00:00:00Z",
        },
        "vector": [0.1] * 384,
    }
