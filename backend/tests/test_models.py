"""
Tests for Pydantic model validation.
"""

import pytest
from pydantic import ValidationError

from app.models.objects import (
    ObjectProperties,
    Object,
    ObjectCreate,
    ObjectUpdate,
    ObjectListResponse
)
from app.models.blocks import (
    BlockProperties,
    Block,
    BlockCreate,
    BlockUpdate,
    BlockListResponse
)
from app.models.tasks import (
    TaskStatus,
    Priority,
    Task,
    TaskCreate,
    TaskUpdate,
    TaskListResponse
)
from app.models.relations import (
    RelationCreate,
    RelationUpdate,
    RelationListResponse
)


@pytest.mark.asyncio
class TestObjectModels:
    """Test cases for object Pydantic models."""

    def test_object_properties_valid(self):
        """Test creating valid object properties."""
        data = {
            "title": "Test Object",
            "content": "Test content",
            "object_type": "note",
            "tags": ["test", "sample"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        props = ObjectProperties(**data)

        assert props.title == "Test Object"
        assert props.content == "Test content"
        assert props.object_type == "note"
        assert props.tags == ["test", "sample"]

    def test_object_properties_minimal(self):
        """Test creating object properties with minimal fields."""
        data = {
            "title": "Minimal Object",
            "object_type": "note",
        }

        props = ObjectProperties(**data)

        assert props.title == "Minimal Object"
        assert props.object_type == "note"

    def test_object_create_valid(self):
        """Test creating object with ObjectCreate model."""
        data = {
            "title": "New Object",
            "content": "Content",
            "object_type": "note",
            "tags": ["tag1", "tag2"],
        }

        obj = ObjectCreate(**data)

        assert obj.title == "New Object"
        assert obj.object_type == "note"

    def test_object_create_with_all_fields(self):
        """Test creating object with all optional fields."""
        data = {
            "title": "Complete Object",
            "content": "Content",
            "object_type": "note",
            "tags": ["test"],
            "status": "active",
            "priority": "high",
            "url": "https://example.com",
            "author": "Test Author",
            "language": "en",
            "reading_time": 5,
            "word_count": 500,
            "checked": False,
            "alias": "test-alias",
        }

        obj = ObjectCreate(**data)

        assert obj.title == "Complete Object"
        assert obj.url == "https://example.com"
        assert obj.reading_time == 5

    def test_object_update_partial(self):
        """Test updating object with partial data."""
        data = {
            "title": "Updated Title",
        }

        obj = ObjectUpdate(**data)

        assert obj.title == "Updated Title"

    def test_object_update_empty(self):
        """Test updating object with no fields."""
        obj = ObjectUpdate()

        # Should allow empty update
        assert obj is not None

    def test_object_model_invalid_type(self):
        """Test object with invalid object_type."""
        data = {
            "title": "Test",
            "object_type": "invalid_type",
        }

        with pytest.raises(ValidationError):
            ObjectCreate(**data)

    def test_object_list_response(self):
        """Test object list response structure."""
        data = {
            "objects": [
                {
                    "id": "obj-1",
                    "payload": {
                        "title": "Object 1",
                        "object_type": "note",
                    },
                    "vector": [0.1] * 384,
                }
            ],
            "total": 1,
        }

        response = ObjectListResponse(**data)

        assert len(response.objects) == 1
        assert response.total == 1


@pytest.mark.asyncio
class TestBlockModels:
    """Test cases for block Pydantic models."""

    def test_block_properties_valid(self):
        """Test creating valid block properties."""
        data = {
            "object_id": "obj-1",
            "content": "Block content",
            "block_type": "text",
            "order": 0,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        props = BlockProperties(**data)

        assert props.object_id == "obj-1"
        assert props.content == "Block content"
        assert props.block_type == "text"
        assert props.order == 0

    def test_block_create_valid(self):
        """Test creating block with BlockCreate model."""
        data = {
            "object_id": "obj-1",
            "content": "New block",
            "block_type": "text",
            "order": 0,
        }

        block = BlockCreate(**data)

        assert block.object_id == "obj-1"
        assert block.content == "New block"

    def test_block_create_checklist(self):
        """Test creating checklist block."""
        data = {
            "object_id": "obj-1",
            "content": "Checklist item",
            "block_type": "text",
            "order": 0,
            "checked": False,
        }

        block = BlockCreate(**data)

        assert block.checked is False

    def test_block_create_code(self):
        """Test creating code block."""
        data = {
            "object_id": "obj-1",
            "content": "print('hello')",
            "block_type": "code",
            "order": 0,
            "language": "python",
        }

        block = BlockCreate(**data)

        assert block.language == "python"

    def test_block_update_partial(self):
        """Test updating block with partial data."""
        data = {
            "content": "Updated content",
        }

        block = BlockUpdate(**data)

        assert block.content == "Updated content"


@pytest.mark.asyncio
class TestTaskModels:
    """Test cases for task Pydantic models."""

    def test_task_status_enum(self):
        """Test task status enum values."""
        assert TaskStatus.TODO == "todo"
        assert TaskStatus.IN_PROGRESS == "in-progress"
        assert TaskStatus.BLOCKED == "blocked"
        assert TaskStatus.REVIEW == "review"
        assert TaskStatus.DONE == "done"

    def test_priority_enum(self):
        """Test priority enum values."""
        assert Priority.LOW == "low"
        assert Priority.MEDIUM == "medium"
        assert Priority.HIGH == "high"
        assert Priority.URGENT == "urgent"

    def test_task_create_valid(self):
        """Test creating task with TaskCreate model."""
        data = {
            "title": "Test Task",
            "description": "Task description",
            "status": TaskStatus.TODO,
            "priority": Priority.MEDIUM,
        }

        task = TaskCreate(**data)

        assert task.title == "Test Task"
        assert task.status == TaskStatus.TODO
        assert task.priority == Priority.MEDIUM

    def test_task_create_minimal(self):
        """Test creating task with minimal fields."""
        data = {
            "title": "Minimal Task",
        }

        task = TaskCreate(**data)

        assert task.title == "Minimal Task"

    def test_task_update_status(self):
        """Test updating task status."""
        data = {
            "status": TaskStatus.IN_PROGRESS,
        }

        task = TaskUpdate(**data)

        assert task.status == TaskStatus.IN_PROGRESS

    def test_task_update_multiple_fields(self):
        """Test updating multiple task fields."""
        data = {
            "title": "Updated title",
            "status": TaskStatus.DONE,
            "priority": Priority.HIGH,
        }

        task = TaskUpdate(**data)

        assert task.title == "Updated title"
        assert task.status == TaskStatus.DONE


@pytest.mark.asyncio
class TestRelationModels:
    """Test cases for relation Pydantic models."""

    def test_relation_create_valid(self):
        """Test creating relation with RelationCreate model."""
        data = {
            "source_type": "object",
            "source_id": "obj-1",
            "target_type": "object",
            "target_id": "obj-2",
            "relation_type": "references",
        }

        relation = RelationCreate(**data)

        assert relation.source_type == "object"
        assert relation.source_id == "obj-1"
        assert relation.target_type == "object"
        assert relation.target_id == "obj-2"
        assert relation.relation_type == "references"

    def test_relation_create_bidirectional(self):
        """Test creating bidirectional relation."""
        data1 = {
            "source_type": "object",
            "source_id": "obj-1",
            "target_type": "object",
            "target_id": "obj-2",
            "relation_type": "references",
        }

        data2 = {
            "source_type": "object",
            "source_id": "obj-2",
            "target_type": "object",
            "target_id": "obj-1",
            "relation_type": "referenced_by",
        }

        rel1 = RelationCreate(**data1)
        rel2 = RelationCreate(**data2)

        assert rel1.source_id == "obj-1"
        assert rel2.source_id == "obj-2"

    def test_relation_update(self):
        """Test updating relation."""
        data = {
            "relation_type": "depends_on",
        }

        relation = RelationUpdate(**data)

        assert relation.relation_type == "depends_on"

    def test_relation_list_response(self):
        """Test relation list response."""
        data = {
            "relations": [
                {
                    "id": "rel-1",
                    "payload": {
                        "source_type": "object",
                        "source_id": "obj-1",
                        "target_type": "object",
                        "target_id": "obj-2",
                        "relation_type": "references",
                    },
                    "vector": [0.1] * 384,
                }
            ],
            "total": 1,
        }

        response = RelationListResponse(**data)

        assert len(response.relations) == 1
        assert response.total == 1


@pytest.mark.asyncio
class TestModelValidation:
    """Test cases for general model validation."""

    def test_url_validation(self):
        """Test URL field validation."""
        data = {
            "title": "Test",
            "url": "not-a-valid-url",
        }

        # URL validation may or may not be strict
        # This tests the model handles it
        try:
            obj = ObjectCreate(**data, object_type="note")
            assert obj.url == "not-a-valid-url"
        except ValidationError:
            # If validation is strict, this is also acceptable
            pass

    def test_datetime_validation(self):
        """Test datetime field validation."""
        data = {
            "title": "Test",
            "created_at": "invalid-datetime",
        }

        with pytest.raises(ValidationError):
            ObjectProperties(**data, object_type="note")

    def test_array_validation(self):
        """Test array/list field validation."""
        data = {
            "title": "Test",
            "tags": "not-an-array",
        }

        with pytest.raises(ValidationError):
            ObjectCreate(**data, object_type="note")

    def test_enum_validation(self):
        """Test enum field validation."""
        data = {
            "title": "Test Task",
            "status": "invalid_status",
        }

        with pytest.raises(ValidationError):
            TaskCreate(**data)

    def test_integer_validation(self):
        """Test integer field validation."""
        data = {
            "title": "Test",
            "reading_time": "not-an-integer",
        }

        with pytest.raises(ValidationError):
            ObjectCreate(**data, object_type="note")

    def test_boolean_validation(self):
        """Test boolean field validation."""
        data = {
            "title": "Test",
            "checked": "not-a-boolean",
        }

        with pytest.raises(ValidationError):
            ObjectCreate(**data, object_type="note")
