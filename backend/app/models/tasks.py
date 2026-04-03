"""Task Models"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.objects import TaskStatus, Priority


class TaskContext(BaseModel):
    """Context included with a task assignment"""
    # The task itself
    task_id: str
    task_title: str
    task_content: str
    
    # Parent object
    parent_object: Optional[Dict[str, Any]] = None
    
    # Linked objects (via [[...]] or relations)
    linked_objects: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Related files (semantic search results)
    related_files: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Agent memories
    relevant_memories: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Recent chat context
    recent_chat: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Pointers to Qdrant (for agent to query more)
    qdrant_pointers: Dict[str, str] = Field(default_factory=dict)


class TaskAssignment(BaseModel):
    """Task assignment request"""
    task_id: str
    agent_name: str
    priority: Priority
    include_context: bool = True
    additional_context: Optional[List[str]] = None  # Additional object IDs to include


class TaskStatusUpdate(BaseModel):
    """Task status update from agent"""
    task_id: str
    agent_name: str
    status: TaskStatus
    current_action: Optional[str] = None  # "researching", "writing", etc.
    notes: Optional[str] = None


class TaskProgressUpdate(BaseModel):
    """Task progress update from agent"""
    task_id: str
    agent_name: str
    update: str
    timestamp: datetime = Field(default_factory=datetime.now)


class TaskComplete(BaseModel):
    """Task completion from agent"""
    task_id: str
    agent_name: str
    notes: Optional[str] = None
    artifacts_created: List[str] = Field(default_factory=list)  # Object IDs


class TaskFilter(BaseModel):
    """Filter for tasks"""
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    assigned_to: Optional[str] = None
    due_before: Optional[datetime] = None
    tags: Optional[List[str]] = None


class TaskListResponse(BaseModel):
    """List of tasks"""
    tasks: List[Dict[str, Any]]
    total: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
