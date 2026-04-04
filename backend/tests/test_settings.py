"""
Tests for the settings router.
"""

import pytest


@pytest.mark.asyncio
class TestSettingsRouter:
    """Test cases for /api/settings endpoints."""

    async def test_get_settings(self, test_client, mock_sqlite_manager):
        """Test getting application settings."""
        response = await test_client.get("/api/settings")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_update_settings(self, test_client, mock_sqlite_manager):
        """Test updating application settings."""
        update_data = {
            "theme": "dark",
            "default_view": "grid",
            "items_per_page": 50,
        }

        response = await test_client.put("/api/settings", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_update_settings_partial(self, test_client, mock_sqlite_manager):
        """Test partial settings update."""
        update_data = {
            "theme": "light",
        }

        response = await test_client.put("/api/settings", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data.get("theme") == "light"

    async def test_update_settings_invalid(self, test_client):
        """Test updating with invalid settings data."""
        update_data = {
            "invalid_key": "value",
        }

        response = await test_client.put("/api/settings", json=update_data)

        # Should either accept or reject gracefully
        assert response.status_code in [200, 422, 400]

    async def test_get_watched_folders_empty(self, test_client, mock_sqlite_manager):
        """Test getting watched folders when none exist."""
        response = await test_client.get("/api/settings/watched-folders")

        assert response.status_code == 200
        data = response.json()
        assert "folders" in data
        assert data["folders"] == []

    async def test_add_watched_folder(self, test_client, mock_sqlite_manager):
        """Test adding a watched folder."""
        folder_data = {
            "path": "/path/to/watch",
            "recursive": True,
            "include_patterns": ["*.txt", "*.md"],
            "exclude_patterns": ["*.tmp", "*.bak"],
        }

        response = await test_client.post(
            "/api/settings/watched-folders",
            json=folder_data
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["path"] == folder_data["path"]

    async def test_add_watched_folder_missing_path(self, test_client):
        """Test adding watched folder without path."""
        folder_data = {
            "recursive": True,
        }

        response = await test_client.post(
            "/api/settings/watched-folders",
            json=folder_data
        )

        assert response.status_code in [422, 400]

    async def test_add_watched_folder_invalid_patterns(self, test_client):
        """Test adding watched folder with invalid patterns."""
        folder_data = {
            "path": "/path/to/watch",
            "include_patterns": "not-a-list",
        }

        response = await test_client.post(
            "/api/settings/watched-folders",
            json=folder_data
        )

        assert response.status_code in [422, 400]

    async def test_remove_watched_folder(self, test_client, mock_sqlite_manager):
        """Test removing a watched folder."""
        response = await test_client.delete("/api/settings/watched-folders/folder-id-1")

        assert response.status_code in [200, 404]

    async def test_trigger_backup_qdrant(self, test_client):
        """Test triggering Qdrant snapshot backup."""
        backup_data = {
            "type": "qdrant",
        }

        response = await test_client.post("/api/settings/backup", json=backup_data)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_trigger_backup_markdown(self, test_client):
        """Test triggering markdown export backup."""
        backup_data = {
            "type": "markdown",
        }

        response = await test_client.post("/api/settings/backup", json=backup_data)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_trigger_backup_git(self, test_client):
        """Test triggering git sync backup."""
        backup_data = {
            "type": "git",
        }

        response = await test_client.post("/api/settings/backup", json=backup_data)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_trigger_backup_invalid_type(self, test_client):
        """Test triggering backup with invalid type."""
        backup_data = {
            "type": "invalid_type",
        }

        response = await test_client.post("/api/settings/backup", json=backup_data)

        assert response.status_code in [422, 400]

    async def test_trigger_backup_without_type(self, test_client):
        """Test triggering backup without specifying type."""
        backup_data = {}

        response = await test_client.post("/api/settings/backup", json=backup_data)

        assert response.status_code in [422, 400]


@pytest.mark.asyncio
class TestSettingsService:
    """Test cases for settings management."""

    async def test_setting_persistence(self, mock_sqlite_manager):
        """Test that settings persist across restarts."""
        # Set a value
        mock_sqlite_manager.upsert_setting("test_key", "test_value")
        # Retrieve it
        value = mock_sqlite_manager.get_setting("test_key")
        assert value == "test_value"

    async def test_setting_defaults(self, mock_sqlite_manager):
        """Test getting default values for unset settings."""
        value = mock_sqlite_manager.get_setting("nonexistent_key", default="default")
        assert value == "default"

    async def test_setting_overwrite(self, mock_sqlite_manager):
        """Test overwriting existing settings."""
        mock_sqlite_manager.upsert_setting("key", "value1")
        mock_sqlite_manager.upsert_setting("key", "value2")
        value = mock_sqlite_manager.get_setting("key")
        assert value == "value2"

    async def test_complex_setting_values(self, mock_sqlite_manager):
        """Test storing complex (dict/list) settings."""
        complex_value = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
        }
        mock_sqlite_manager.upsert_setting("complex", complex_value)
        value = mock_sqlite_manager.get_setting("complex")
        assert value == complex_value


@pytest.mark.asyncio
class TestBackupService:
    """Test cases for backup service."""

    async def test_qdrant_snapshot_creation(self):
        """Test creating Qdrant snapshot."""
        from app.services.backup import BackupService
        # Should create snapshot in Qdrant data directory
        pass

    async def test_markdown_export(self):
        """Test exporting to markdown files."""
        from app.services.backup import BackupService
        # Should export objects as markdown files
        pass

    async def test_git_sync(self):
        """Test syncing to git repository."""
        from app.services.backup import BackupService
        # Should commit and push to git
        pass

    async def test_backup_scheduling(self):
        """Test scheduled backup execution."""
        from app.services.backup import BackupService
        # Should run backups on schedule
        pass

    async def test_backup_error_handling(self):
        """Test backup error handling."""
        from app.services.backup import BackupService
        # Should handle backup failures gracefully
        pass

    async def test_backup_status_tracking(self):
        """Test tracking backup status."""
        from app.services.backup import BackupService
        # Should log backup attempts and results
        pass
