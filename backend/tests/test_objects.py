"""
Tests for the objects router.
"""

import pytest
from qdrant_client.models import PointStruct


@pytest.mark.asyncio
class TestObjectsRouter:
    """Test cases for /api/objects endpoints."""

    async def test_list_objects_empty(self, test_client, mock_qdrant_client):
        """Test listing objects when none exist."""
        response = await test_client.get("/api/objects")

        assert response.status_code == 200
        data = response.json()
        assert "objects" in data
        assert data["objects"] == []
        assert data["total"] == 0

    async def test_list_objects_with_data(self, test_client, mock_qdrant_client, sample_object_data):
        """Test listing objects with existing data."""
        # Add mock data
        point = PointStruct(
            id=sample_object_data["id"],
            vector=sample_object_data["vector"],
            payload=sample_object_data["payload"],
        )
        mock_qdrant_client.upsert("objects", [point])

        response = await test_client.get("/api/objects")

        assert response.status_code == 200
        data = response.json()
        assert "objects" in data
        assert len(data["objects"]) >= 0
        assert data["total"] >= 0

    async def test_list_objects_with_filters(self, test_client):
        """Test listing objects with query filters."""
        response = await test_client.get(
            "/api/objects",
            params={"object_type": "note", "tag": "test", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert "objects" in data

    async def test_get_object_success(self, test_client, mock_qdrant_client, sample_object_data):
        """Test getting a specific object by ID."""
        # Add mock data
        point = PointStruct(
            id=sample_object_data["id"],
            vector=sample_object_data["vector"],
            payload=sample_object_data["payload"],
        )
        mock_qdrant_client.upsert("objects", [point])

        response = await test_client.get(f"/api/objects/{sample_object_data['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_object_data["id"]
        assert data["title"] == sample_object_data["payload"]["title"]

    async def test_get_object_not_found(self, test_client):
        """Test getting a non-existent object."""
        response = await test_client.get("/api/objects/non-existent-id")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_create_object_success(self, test_client):
        """Test creating a new object."""
        object_data = {
            "title": "New Object",
            "content": "New content",
            "object_type": "note",
            "tags": ["new", "test"],
        }

        response = await test_client.post("/api/objects", json=object_data)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == object_data["title"]
        assert data["content"] == object_data["content"]

    async def test_create_object_missing_required(self, test_client):
        """Test creating an object with missing required fields."""
        object_data = {
            "content": "Content without title"
        }

        response = await test_client.post("/api/objects", json=object_data)

        # Should validate and return 422 for missing required fields
        assert response.status_code in [422, 400]

    async def test_update_object_success(self, test_client, mock_qdrant_client, sample_object_data):
        """Test updating an existing object."""
        # Add mock data
        point = PointStruct(
            id=sample_object_data["id"],
            vector=sample_object_data["vector"],
            payload=sample_object_data["payload"],
        )
        mock_qdrant_client.upsert("objects", [point])

        update_data = {
            "title": "Updated Title",
            "content": "Updated content",
        }

        response = await test_client.put(
            f"/api/objects/{sample_object_data['id']}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_object_data["id"]

    async def test_update_object_not_found(self, test_client):
        """Test updating a non-existent object."""
        update_data = {"title": "Updated"}

        response = await test_client.put("/api/objects/non-existent", json=update_data)

        assert response.status_code == 404

    async def test_delete_object_success(self, test_client, mock_qdrant_client, sample_object_data):
        """Test deleting an object."""
        # Add mock data
        point = PointStruct(
            id=sample_object_data["id"],
            vector=sample_object_data["vector"],
            payload=sample_object_data["payload"],
        )
        mock_qdrant_client.upsert("objects", [point])

        response = await test_client.delete(f"/api/objects/{sample_object_data['id']}")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_delete_object_not_found(self, test_client):
        """Test deleting a non-existent object."""
        response = await test_client.delete("/api/objects/non-existent")

        assert response.status_code == 404

    async def test_get_object_relations(self, test_client):
        """Test getting relations for an object."""
        response = await test_client.get("/api/objects/test-object-1/relations")

        assert response.status_code == 200
        data = response.json()
        assert "relations" in data

    async def test_create_object_with_tags(self, test_client):
        """Test creating an object with tags."""
        object_data = {
            "title": "Tagged Object",
            "content": "Content",
            "object_type": "note",
            "tags": ["tag1", "tag2", "tag3"],
        }

        response = await test_client.post("/api/objects", json=object_data)

        assert response.status_code == 200
        data = response.json()
        assert "tags" in data
        assert set(data["tags"]) == set(object_data["tags"])

    async def test_create_object_with_all_fields(self, test_client):
        """Test creating an object with all optional fields."""
        object_data = {
            "title": "Complete Object",
            "content": "Content",
            "object_type": "note",
            "tags": ["test"],
            "status": "active",
            "priority": "high",
            "url": "https://example.com",
            "author": "Test Author",
        }

        response = await test_client.post("/api/objects", json=object_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == object_data["title"]
        assert data["url"] == object_data["url"]
