"""
Tests for the search router.
"""

import pytest


@pytest.mark.asyncio
class TestSearchRouter:
    """Test cases for /api/search endpoints."""

    async def test_search_empty_query(self, test_client):
        """Test search with empty query."""
        response = await test_client.get("/api/search", params={"query": ""})

        # Should either return empty results or handle gracefully
        assert response.status_code in [200, 400]

    async def test_search_with_query(self, test_client):
        """Test semantic search with a query."""
        response = await test_client.get(
            "/api/search",
            params={"query": "test query", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    async def test_search_with_type_filter(self, test_client):
        """Test search with entity type filter."""
        response = await test_client.get(
            "/api/search",
            params={"query": "test", "type": "object"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    async def test_search_with_limit(self, test_client):
        """Test search with custom limit."""
        response = await test_client.get(
            "/api/search",
            params={"query": "test", "limit": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # If results exist, should respect limit
        if data["results"]:
            assert len(data["results"]) <= 5

    async def test_search_with_threshold(self, test_client):
        """Test search with similarity threshold."""
        response = await test_client.get(
            "/api/search",
            params={"query": "test", "threshold": 0.7}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # All results should have score >= threshold
        for result in data["results"]:
            if "score" in result:
                assert result["score"] >= 0.7

    async def test_find_similar_empty_id(self, test_client):
        """Test finding similar content with empty object ID."""
        response = await test_client.get("/api/search/similar/")

        assert response.status_code == 404  # Empty ID should not be found

    async def test_find_similar_success(self, test_client, mock_qdrant_client, sample_object_data):
        """Test finding similar content to an object."""
        from qdrant_client.models import PointStruct

        # Add mock data
        point = PointStruct(
            id=sample_object_data["id"],
            vector=sample_object_data["vector"],
            payload=sample_object_data["payload"],
        )
        mock_qdrant_client.upsert("objects", [point])

        response = await test_client.get(
            f"/api/search/similar/{sample_object_data['id']}",
            params={"limit": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    async def test_find_similar_not_found(self, test_client):
        """Test finding similar content for non-existent object."""
        response = await test_client.get("/api/search/similar/non-existent-id")

        assert response.status_code == 404

    async def test_find_similar_with_type(self, test_client):
        """Test finding similar content with type filter."""
        response = await test_client.get(
            "/api/search/similar/test-id",
            params={"type": "object"}
        )

        # Should return 404 for non-existent ID or 200 for valid
        assert response.status_code in [200, 404]

    async def test_search_special_characters(self, test_client):
        """Test search with special characters in query."""
        response = await test_client.get(
            "/api/search",
            params={"query": "test & special @ chars"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    async def test_search_unicode(self, test_client):
        """Test search with Unicode characters."""
        response = await test_client.get(
            "/api/search",
            params={"query": "test emoji 🎉 and 中文"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    async def test_search_large_limit(self, test_client):
        """Test search with very large limit."""
        response = await test_client.get(
            "/api/search",
            params={"query": "test", "limit": 1000}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    async def test_search_invalid_threshold(self, test_client):
        """Test search with invalid threshold value."""
        response = await test_client.get(
            "/api/search",
            params={"query": "test", "threshold": 2.0}
        )

        # Should handle invalid threshold gracefully
        assert response.status_code in [200, 400, 422]

    async def test_search_no_results(self, test_client):
        """Test search that returns no results."""
        response = await test_client.get(
            "/api/search",
            params={"query": "xyznonexistentcontent", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["total"] == 0


@pytest.mark.asyncio
class TestSearchService:
    """Test cases for search functionality."""

    async def test_embedding_generation_for_search(self, mock_embedding_service):
        """Test that embeddings are generated for search queries."""
        query = "test search query"
        vector = mock_embedding_service.embed_text(query)

        assert vector is not None
        assert len(vector) == 384
        assert all(isinstance(v, float) for v in vector)

    async def test_deterministic_embeddings(self, mock_embedding_service):
        """Test that the same query produces the same embedding."""
        query = "deterministic test"
        vector1 = mock_embedding_service.embed_text(query)
        vector2 = mock_embedding_service.embed_text(query)

        assert vector1 == vector2

    async def test_different_queries_different_embeddings(self, mock_embedding_service):
        """Test that different queries produce different embeddings."""
        vector1 = mock_embedding_service.embed_text("query one")
        vector2 = mock_embedding_service.embed_text("query two")

        assert vector1 != vector2
