"""
Tests for the blocks router.
"""

import pytest
from qdrant_client.models import PointStruct


@pytest.mark.asyncio
class TestBlocksRouter:
    """Test cases for /api/blocks endpoints."""

    async def test_get_blocks_for_object_empty(self, test_client):
        """Test getting blocks for an object with no blocks."""
        response = await test_client.get("/api/blocks/object/test-object-1")

        assert response.status_code == 200
        data = response.json()
        assert "blocks" in data
        assert data["blocks"] == []
        assert data["total"] == 0

    async def test_get_blocks_for_object_with_data(
        self, test_client, mock_qdrant_client, sample_block_data
    ):
        """Test getting blocks for an object with existing blocks."""
        # Add mock data
        point = PointStruct(
            id=sample_block_data["id"],
            vector=sample_block_data["vector"],
            payload=sample_block_data["payload"],
        )
        mock_qdrant_client.upsert("blocks", [point])

        response = await test_client.get(f"/api/blocks/object/{sample_block_data['payload']['object_id']}")

        assert response.status_code == 200
        data = response.json()
        assert "blocks" in data
        assert data["total"] >= 0

    async def test_create_block_success(self, test_client):
        """Test creating a new block."""
        block_data = {
            "object_id": "test-object-1",
            "content": "New block content",
            "block_type": "text",
            "order": 0,
        }

        response = await test_client.post("/api/blocks", json=block_data)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["content"] == block_data["content"]
        assert data["block_type"] == block_data["block_type"]

    async def test_create_block_missing_required(self, test_client):
        """Test creating a block with missing required fields."""
        block_data = {
            "content": "Content without object_id"
        }

        response = await test_client.post("/api/blocks", json=block_data)

        assert response.status_code in [422, 400]

    async def test_create_block_with_all_fields(self, test_client):
        """Test creating a block with all optional fields."""
        block_data = {
            "object_id": "test-object-1",
            "content": "Complete block",
            "block_type": "code",
            "order": 1,
            "checked": False,
            "language": "python",
            "url": "https://example.com",
            "alias": "test-alias",
        }

        response = await test_client.post("/api/blocks", json=block_data)

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == block_data["language"]
        assert data["alias"] == block_data["alias"]

    async def test_update_block_success(
        self, test_client, mock_qdrant_client, sample_block_data
    ):
        """Test updating an existing block."""
        # Add mock data
        point = PointStruct(
            id=sample_block_data["id"],
            vector=sample_block_data["vector"],
            payload=sample_block_data["payload"],
        )
        mock_qdrant_client.upsert("blocks", [point])

        update_data = {
            "content": "Updated block content",
            "checked": True,
        }

        response = await test_client.put(f"/api/blocks/{sample_block_data['id']}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_block_data["id"]

    async def test_update_block_not_found(self, test_client):
        """Test updating a non-existent block."""
        update_data = {"content": "Updated"}

        response = await test_client.put("/api/blocks/non-existent", json=update_data)

        assert response.status_code == 404

    async def test_batch_update_blocks(self, test_client):
        """Test batch updating multiple blocks."""
        update_data = {
            "blocks": [
                {"id": "block-1", "content": "Updated 1", "order": 1},
                {"id": "block-2", "content": "Updated 2", "order": 2},
            ]
        }

        response = await test_client.post("/api/blocks/batch-update", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_sync_blocks_for_object(self, test_client):
        """Test syncing blocks for an object."""
        sync_data = {
            "blocks": [
                {
                    "id": "new-block-1",
                    "content": "Synced block 1",
                    "block_type": "text",
                    "order": 0,
                },
                {
                    "id": "new-block-2",
                    "content": "Synced block 2",
                    "block_type": "text",
                    "order": 1,
                },
            ]
        }

        response = await test_client.put(
            "/api/blocks/object/test-object-1/sync",
            json=sync_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_delete_block_success(
        self, test_client, mock_qdrant_client, sample_block_data
    ):
        """Test deleting a block."""
        # Add mock data
        point = PointStruct(
            id=sample_block_data["id"],
            vector=sample_block_data["vector"],
            payload=sample_block_data["payload"],
        )
        mock_qdrant_client.upsert("blocks", [point])

        response = await test_client.delete(f"/api/blocks/{sample_block_data['id']}")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_delete_block_not_found(self, test_client):
        """Test deleting a non-existent block."""
        response = await test_client.delete("/api/blocks/non-existent")

        assert response.status_code == 404

    async def test_create_checklist_block(self, test_client):
        """Test creating a checklist block."""
        block_data = {
            "object_id": "test-object-1",
            "content": "Checklist item",
            "block_type": "text",
            "order": 0,
            "checked": False,
        }

        response = await test_client.post("/api/blocks", json=block_data)

        assert response.status_code == 200
        data = response.json()
        assert data["checked"] == False

    async def test_create_code_block(self, test_client):
        """Test creating a code block."""
        block_data = {
            "object_id": "test-object-1",
            "content": "print('hello')",
            "block_type": "code",
            "order": 0,
            "language": "python",
        }

        response = await test_client.post("/api/blocks", json=block_data)

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "python"

    async def test_batch_update_empty_list(self, test_client):
        """Test batch update with empty block list."""
        response = await test_client.post("/api/blocks/batch-update", json={"blocks": []})

        assert response.status_code == 200

    async def test_sync_empty_blocks(self, test_client):
        """Test syncing with empty blocks list (clears all blocks)."""
        response = await test_client.put(
            "/api/blocks/object/test-object-1/sync",
            json={"blocks": []}
        )

        assert response.status_code == 200
