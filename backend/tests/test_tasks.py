"""
Tests for the tasks router.
"""

import pytest
from qdrant_client.models import PointStruct


@pytest.mark.asyncio
class TestTasksRouter:
    """Test cases for /api/tasks endpoints."""

    async def test_list_tasks_empty(self, test_client):
        """Test listing tasks when none exist."""
        response = await test_client.get("/api/tasks")

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert data["tasks"] == []
        assert data["total"] == 0

    async def test_list_tasks_with_data(self, test_client, mock_qdrant_client, sample_task_data):
        """Test listing tasks with existing data."""
        # Add mock data
        point = PointStruct(
            id=sample_task_data["id"],
            vector=sample_task_data["vector"],
            payload=sample_task_data["payload"],
        )
        mock_qdrant_client.upsert("objects", [point])

        response = await test_client.get("/api/tasks")

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "counts" in data

    async def test_list_tasks_with_status_filter(self, test_client):
        """Test listing tasks filtered by status."""
        response = await test_client.get(
            "/api/tasks",
            params={"status": "todo"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

    async def test_list_tasks_with_priority_filter(self, test_client):
        """Test listing tasks filtered by priority."""
        response = await test_client.get(
            "/api/tasks",
            params={"priority": "high"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

    async def test_list_tasks_with_agent_filter(self, test_client):
        """Test listing tasks filtered by assigned agent."""
        response = await test_client.get(
            "/api/tasks",
            params={"assigned_agent": "test-agent"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

    async def test_get_task_success(self, test_client, mock_qdrant_client, sample_task_data):
        """Test getting a specific task by ID."""
        # Add mock data
        point = PointStruct(
            id=sample_task_data["id"],
            vector=sample_task_data["vector"],
            payload=sample_task_data["payload"],
        )
        mock_qdrant_client.upsert("objects", [point])

        response = await test_client.get(f"/api/tasks/{sample_task_data['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_task_data["id"]
        assert data["title"] == sample_task_data["payload"]["title"]

    async def test_get_task_not_found(self, test_client):
        """Test getting a non-existent task."""
        response = await test_client.get("/api/tasks/non-existent-id")

        assert response.status_code == 404

    async def test_assign_task_success(self, test_client, mock_openclaw_service):
        """Test assigning a task to an agent."""
        assign_data = {
            "agent_name": "test-agent",
            "context": {"notes": "Test context"}
        }

        response = await test_client.post(
            "/api/tasks/test-task-1/assign",
            json=assign_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "agent" in data
        assert data["agent"] == "test-agent"

    async def test_assign_task_missing_agent(self, test_client):
        """Test assigning a task without specifying an agent."""
        assign_data = {
            "context": {"notes": "Test context"}
        }

        response = await test_client.post(
            "/api/tasks/test-task-1/assign",
            json=assign_data
        )

        assert response.status_code in [422, 400]

    async def test_update_task_status(self, test_client):
        """Test updating task status."""
        status_data = {
            "status": "in-progress",
            "notes": "Started working on it"
        }

        response = await test_client.post(
            "/api/tasks/test-task-1/status",
            json=status_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    async def test_update_task_status_invalid(self, test_client):
        """Test updating task status with invalid status."""
        status_data = {
            "status": "invalid_status"
        }

        response = await test_client.post(
            "/api/tasks/test-task-1/status",
            json=status_data
        )

        assert response.status_code in [422, 400]

    async def test_update_task_status_all_statuses(self, test_client):
        """Test updating task status with all valid statuses."""
        valid_statuses = ["todo", "in-progress", "blocked", "review", "done"]

        for status in valid_statuses:
            response = await test_client.post(
                "/api/tasks/test-task-1/status",
                json={"status": status}
            )
            assert response.status_code in [200, 404]  # 404 if task doesn't exist

    async def test_get_task_context(self, test_client):
        """Test getting context for a task."""
        response = await test_client.get("/api/tasks/test-task-1/context")

        assert response.status_code == 200
        data = response.json()
        assert "context" in data
        assert "entities" in data["context"]

    async def test_get_task_context_not_found(self, test_client):
        """Test getting context for non-existent task."""
        response = await test_client.get("/api/tasks/non-existent/context")

        # Should return empty context or 404
        assert response.status_code in [200, 404]

    async def test_create_task(self, test_client):
        """Test creating a new task via objects endpoint."""
        # Tasks are objects with object_type="task"
        task_data = {
            "title": "New Test Task",
            "description": "Task description",
            "object_type": "task",
            "status": "todo",
            "priority": "medium",
        }

        response = await test_client.post("/api/objects", json=task_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["object_type"] == "task"

    async def test_task_priorities(self, test_client):
        """Test all valid task priorities."""
        valid_priorities = ["low", "medium", "high", "urgent"]

        for priority in valid_priorities:
            response = await test_client.post("/api/objects", json={
                "title": f"Task with {priority} priority",
                "object_type": "task",
                "priority": priority,
            })
            assert response.status_code == 200


@pytest.mark.asyncio
class TestTaskContextBuilder:
    """Test cases for task context building service."""

    async def test_build_empty_context(self):
        """Test building context for a task with no related entities."""
        from app.services.context_builder import build_task_context

        # This would need actual task data
        # For now just test that the function exists
        assert callable(build_task_context)

    async def test_context_includes_pointers(self):
        """Test that context includes entity pointers."""
        # Context builder should create pointers to related entities
        pass

    async def test_context_includes_relations(self):
        """Test that context includes related entities."""
        # Context builder should fetch related entities
        pass


@pytest.mark.asyncio
class TestTaskCounts:
    """Test cases for task count aggregation."""

    async def test_counts_by_status(self, test_client):
        """Test getting task counts grouped by status."""
        response = await test_client.get("/api/tasks")

        assert response.status_code == 200
        data = response.json()
        assert "counts" in data
        assert "by_status" in data["counts"]

    async def test_counts_by_priority(self, test_client):
        """Test getting task counts grouped by priority."""
        response = await test_client.get("/api/tasks")

        assert response.status_code == 200
        data = response.json()
        assert "counts" in data
        assert "by_priority" in data["counts"]
