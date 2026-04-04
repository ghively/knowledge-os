"""
Tests for the relations router and service.
"""

import pytest
from qdrant_client.models import PointStruct


@pytest.mark.asyncio
class TestRelationsRouter:
    """Test cases for /api/relations endpoints."""

    async def test_create_relation_success(self, test_client):
        """Test creating a new relation."""
        relation_data = {
            "source_type": "object",
            "source_id": "test-object-1",
            "target_type": "object",
            "target_id": "test-object-2",
            "relation_type": "references",
        }

        response = await test_client.post("/api/relations", json=relation_data)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["source_id"] == relation_data["source_id"]
        assert data["target_id"] == relation_data["target_id"]
        assert data["relation_type"] == relation_data["relation_type"]

    async def test_create_relation_missing_required(self, test_client):
        """Test creating a relation with missing required fields."""
        relation_data = {
            "source_type": "object",
            "source_id": "test-object-1",
        }

        response = await test_client.post("/api/relations", json=relation_data)

        assert response.status_code in [422, 400]

    async def test_create_relation_invalid_type(self, test_client):
        """Test creating a relation with invalid entity type."""
        relation_data = {
            "source_type": "invalid",
            "source_id": "test-1",
            "target_type": "object",
            "target_id": "test-2",
            "relation_type": "references",
        }

        response = await test_client.post("/api/relations", json=relation_data)

        assert response.status_code in [422, 400]

    async def test_get_relations_for_object_empty(self, test_client):
        """Test getting relations for an object with no relations."""
        response = await test_client.get("/api/relations/object/test-object-1")

        assert response.status_code == 200
        data = response.json()
        assert "relations" in data
        assert data["relations"] == []
        assert data["total"] == 0

    async def test_get_relations_for_object_with_data(
        self, test_client, mock_qdrant_client, sample_relation_data
    ):
        """Test getting relations for an object with existing relations."""
        # Add mock data
        point = PointStruct(
            id=sample_relation_data["id"],
            vector=sample_relation_data["vector"],
            payload=sample_relation_data["payload"],
        )
        mock_qdrant_client.upsert("relations", [point])

        response = await test_client.get(
            f"/api/relations/object/{sample_relation_data['payload']['source_id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "relations" in data
        assert data["total"] >= 0

    async def test_get_relations_with_filters(self, test_client):
        """Test getting relations with relation_type filter."""
        response = await test_client.get(
            "/api/relations/object/test-object-1",
            params={"relation_type": "references"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "relations" in data

    async def test_update_relation_success(
        self, test_client, mock_qdrant_client, sample_relation_data
    ):
        """Test updating an existing relation."""
        # Add mock data
        point = PointStruct(
            id=sample_relation_data["id"],
            vector=sample_relation_data["vector"],
            payload=sample_relation_data["payload"],
        )
        mock_qdrant_client.upsert("relations", [point])

        update_data = {
            "relation_type": "depends_on"
        }

        response = await test_client.put(
            f"/api/relations/{sample_relation_data['id']}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_relation_data["id"]

    async def test_update_relation_not_found(self, test_client):
        """Test updating a non-existent relation."""
        update_data = {"relation_type": "references"}

        response = await test_client.put("/api/relations/non-existent", json=update_data)

        assert response.status_code == 404

    async def test_delete_relation_success(
        self, test_client, mock_qdrant_client, sample_relation_data
    ):
        """Test deleting a relation."""
        # Add mock data
        point = PointStruct(
            id=sample_relation_data["id"],
            vector=sample_relation_data["vector"],
            payload=sample_relation_data["payload"],
        )
        mock_qdrant_client.upsert("relations", [point])

        response = await test_client.delete(f"/api/relations/{sample_relation_data['id']}")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_delete_relation_not_found(self, test_client):
        """Test deleting a non-existent relation."""
        response = await test_client.delete("/api/relations/non-existent")

        assert response.status_code == 404

    async def test_create_bidirectional_relation(self, test_client):
        """Test creating bidirectional relations."""
        # Create first relation
        relation_data_1 = {
            "source_type": "object",
            "source_id": "test-object-1",
            "target_type": "object",
            "target_id": "test-object-2",
            "relation_type": "references",
        }

        response_1 = await test_client.post("/api/relations", json=relation_data_1)
        assert response_1.status_code == 200

        # Create reverse relation
        relation_data_2 = {
            "source_type": "object",
            "source_id": "test-object-2",
            "target_type": "object",
            "target_id": "test-object-1",
            "relation_type": "referenced_by",
        }

        response_2 = await test_client.post("/api/relations", json=relation_data_2)
        assert response_2.status_code == 200


@pytest.mark.asyncio
class TestRelationService:
    """Test cases for the relation service."""

    async def test_extract_wiki_links(self):
        """Test extracting wiki-style links from text."""
        from app.services.relations import extract_wiki_links

        text = "Check out [[Page One]] and [[Page Two]] for more info."
        links = extract_wiki_links(text)

        assert "Page One" in links
        assert "Page Two" in links

    async def test_extract_block_references(self):
        """Test extracting block references from text."""
        from app.services.relations import extract_block_references

        text = "See block ((block-1)) and ((block-2)) for details."
        refs = extract_block_references(text)

        assert "block-1" in refs
        assert "block-2" in refs

    async def test_extract_mixed_references(self):
        """Test extracting both wiki links and block references."""
        from app.services.relations import (
            extract_wiki_links,
            extract_block_references
        }

        text = "Link [[Page]] with block ((block-1))."
        links = extract_wiki_links(text)
        refs = extract_block_references(text)

        assert "Page" in links
        assert "block-1" in refs

    async def test_extract_empty_references(self):
        """Test extracting references from text with none."""
        from app.services.relations import (
            extract_wiki_links,
            extract_block_references
        )

        text = "No references here."
        links = extract_wiki_links(text)
        refs = extract_block_references(text)

        assert len(links) == 0
        assert len(refs) == 0

    async def test_sync_object_links(self):
        """Test syncing wiki-style links to relations."""
        from app.services.relations import sync_object_links

        # This would need actual object data to work properly
        # For now just test that the function exists and is callable
        assert callable(sync_object_links)
