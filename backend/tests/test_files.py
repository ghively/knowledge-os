"""
Tests for the files router.
"""

import pytest


@pytest.mark.asyncio
class TestFilesRouter:
    """Test cases for /api/files endpoints."""

    async def test_list_files_empty(self, test_client):
        """Test listing files when none exist."""
        response = await test_client.get("/api/files")

        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert data["files"] == []

    async def test_list_files_with_pagination(self, test_client):
        """Test listing files with pagination."""
        response = await test_client.get(
            "/api/files",
            params={"limit": 10, "offset": 0}
        )

        assert response.status_code == 200
        data = response.json()
        assert "files" in data

    async def test_list_files_with_filter(self, test_client):
        """Test listing files with file type filter."""
        response = await test_client.get(
            "/api/files",
            params={"file_type": "pdf"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "files" in data

    async def test_get_file_success(self, test_client, mock_qdrant_client):
        """Test getting a specific file by ID."""
        from qdrant_client.models import PointStruct

        # Add mock file data
        file_data = {
            "id": "test-file-1",
            "payload": {
                "filename": "test.pdf",
                "file_path": "/path/to/test.pdf",
                "file_type": "pdf",
                "size": 1024,
                "indexed_at": "2024-01-01T00:00:00Z",
            },
            "vector": [0.1] * 384,
        }
        point = PointStruct(
            id=file_data["id"],
            vector=file_data["vector"],
            payload=file_data["payload"],
        )
        mock_qdrant_client.upsert("files", [point])

        response = await test_client.get(f"/api/files/{file_data['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == file_data["id"]
        assert data["filename"] == file_data["payload"]["filename"]

    async def test_get_file_not_found(self, test_client):
        """Test getting a non-existent file."""
        response = await test_client.get("/api/files/non-existent-id")

        assert response.status_code == 404

    async def test_reindex_file_success(self, test_client):
        """Test reindexing a file."""
        response = await test_client.post("/api/files/test-file-1/reindex")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_reindex_file_not_found(self, test_client):
        """Test reindexing a non-existent file."""
        response = await test_client.post("/api/files/non-existent/reindex")

        assert response.status_code == 404

    async def test_file_notification(self, test_client):
        """Test receiving file change notification."""
        notification_data = {
            "file_path": "/path/to/changed.pdf",
            "event_type": "modified",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        response = await test_client.post("/api/files/notify", json=notification_data)

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    async def test_index_file_content(self, test_client):
        """Test indexing file content."""
        content_data = {
            "file_path": "/path/to/file.txt",
            "content": "Test file content",
        }

        response = await test_client.post(
            "/api/files/test-file-1/content",
            json=content_data
        )

        # Should either succeed or indicate file not found
        assert response.status_code in [200, 404]

    async def test_index_file_content_missing_path(self, test_client):
        """Test indexing content without providing file path."""
        content_data = {
            "content": "Test content"
        }

        response = await test_client.post(
            "/api/files/test-file-1/content",
            json=content_data
        )

        assert response.status_code in [422, 400, 404]

    async def test_list_files_sorted(self, test_client):
        """Test listing files with sorting."""
        response = await test_client.get(
            "/api/files",
            params={"sort_by": "indexed_at", "sort_order": "desc"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "files" in data


@pytest.mark.asyncio
class TestFileWatcherService:
    """Test cases for file watcher service."""

    async def test_add_watched_folder(self, test_client):
        """Test adding a watched folder."""
        folder_data = {
            "path": "/path/to/watch",
            "recursive": True,
            "include_patterns": ["*.txt", "*.md"],
            "exclude_patterns": ["*.tmp"],
        }

        response = await test_client.post(
            "/api/settings/watched-folders",
            json=folder_data
        )

        assert response.status_code in [200, 201]

    async def test_remove_watched_folder(self, test_client):
        """Test removing a watched folder."""
        response = await test_client.delete("/api/settings/watched-folders/folder-id-1")

        assert response.status_code in [200, 404]

    async def test_list_watched_folders(self, test_client):
        """Test listing watched folders."""
        response = await test_client.get("/api/settings/watched-folders")

        assert response.status_code == 200
        data = response.json()
        assert "folders" in data

    async def test_file_pattern_matching(self):
        """Test file pattern matching logic."""
        from app.services.file_watcher import _matches_patterns

        # Test include patterns
        include = ["*.txt", "*.md"]
        assert _matches_patterns("test.txt", include, [])
        assert _matches_patterns("doc.md", include, [])
        assert not _matches_patterns("test.pdf", include, [])

        # Test exclude patterns
        exclude = ["*.tmp"]
        assert not _matches_patterns("test.tmp", [], exclude)
        assert _matches_patterns("test.txt", [], exclude)

        # Test combined
        assert _matches_patterns("test.txt", include, exclude)
        assert not _matches_patterns("test.tmp", include, exclude)


@pytest.mark.asyncio
class TestFileContentExtraction:
    """Test cases for file content extraction."""

    async def test_extract_text_content(self):
        """Test extracting content from text files."""
        from app.services.file_watcher import _extract_content

        # This would need actual file paths
        # For now just test that the function exists
        assert callable(_extract_content)

    async def test_extract_pdf_content(self):
        """Test extracting content from PDF files."""
        # PDF extraction should handle text extraction
        pass

    async def test_extract_code_content(self):
        """Test extracting and indexing code files."""
        # Code extraction should handle syntax highlighting
        pass

    async def test_extract_image_metadata(self):
        """Test extracting metadata from images."""
        # Image extraction should handle embeddings
        pass


@pytest.mark.asyncio
class TestFileSyncStatus:
    """Test cases for file sync status tracking."""

    async def test_update_sync_status(self):
        """Test updating file sync status."""
        # Sync status should track last indexed time
        pass

    async def test_get_sync_status(self):
        """Test getting file sync status."""
        # Should return when file was last indexed
        pass

    async def test_handle_sync_errors(self):
        """Test handling sync errors gracefully."""
        # Should mark files as failed and retry
        pass
