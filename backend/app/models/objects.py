"""Object Models"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class ObjectType(str, Enum):
    """Object types"""
    PAGE = "page"
    TASK = "task"
    PERSON = "person"
    BOOK = "book"
    MEETING = "meeting"
    AGENT = "agent"
    FILE = "file"
    FOLDER = "folder"
    IMAGE = "image"
    CODE = "code"
    NOTE = "note"


class TaskStatus(str, Enum):
    """Task statuses"""
    TODO = "todo"
    IN_PROGRESS = "in-progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"


class Priority(str, Enum):
    """Priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class LayoutType(str, Enum):
    """Layout types"""
    DEFAULT = "default"
    PROFILE = "profile"
    CARD = "card"
    ENCYCLOPEDIA = "encyclopedia"


class ObjectProperties(BaseModel):
    """Object properties (type-specific)"""
    # Common
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None  # user or agent name
    
    # Task-specific
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None  # agent name
    completed_at: Optional[datetime] = None
    context_included: List[str] = Field(default_factory=list)  # Object UUIDs
    current_action: Optional[str] = None  # "researching", "writing", etc.
    
    # Person-specific
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    
    # Book-specific
    author: Optional[str] = None
    rating: Optional[int] = None
    started_date: Optional[datetime] = None
    finished_date: Optional[datetime] = None
    
    # File/Folder-specific
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    checksum: Optional[str] = None
    is_watched: Optional[bool] = None
    last_modified: Optional[datetime] = None
    
    # Agent-specific
    agent_name: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    agent_status: Optional[str] = None  # active, idle, busy, offline
    last_seen: Optional[datetime] = None
    
    # Image-specific
    description: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    
    class Config:
        extra = "allow"  # Allow additional properties


class Object(BaseModel):
    """Object model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ObjectType
    title: str
    icon: Optional[str] = None
    content: str = ""  # Combined content for embedding
    properties: ObjectProperties = Field(default_factory=ObjectProperties)
    layout: LayoutType = LayoutType.DEFAULT
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc-123",
                "type": "task",
                "title": "Research vector databases",
                "icon": "✅",
                "content": "Research vector databases for our project",
                "properties": {
                    "status": "in-progress",
                    "priority": "urgent",
                    "assigned_to": "researcher",
                    "tags": ["research", "databases"]
                },
                "layout": "default"
            }
        }


class ObjectCreate(BaseModel):
    """Object creation request"""
    type: ObjectType
    title: str
    icon: Optional[str] = None
    content: Optional[str] = None
    properties: Optional[ObjectProperties] = None
    layout: Optional[LayoutType] = LayoutType.DEFAULT


class ObjectUpdate(BaseModel):
    """Object update request"""
    title: Optional[str] = None
    icon: Optional[str] = None
    content: Optional[str] = None
    properties: Optional[ObjectProperties] = None
    layout: Optional[LayoutType] = None


class ObjectResponse(Object):
    """Object response with vector score (for search results)"""
    score: Optional[float] = None


class ObjectListResponse(BaseModel):
    """List of objects"""
    objects: List[ObjectResponse]
    total: int


import uuid
