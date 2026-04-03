"""Object Models"""
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class ObjectProperties(BaseModel):
    """Object properties"""
    tags: List[str] = Field(default_factory=list)
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    current_action: Optional[str] = None
    notes: Optional[str] = None
    parent_id: Optional[str] = None
    linked_objects: List[str] = Field(default_factory=list)


class Object(BaseModel):
    """Object model"""
    id: str
    type: str
    title: str
    icon: Optional[str] = None
    content: Optional[str] = None
    properties: ObjectProperties = Field(default_factory=ObjectProperties)
    layout: Optional[str] = "default"


class ObjectCreate(BaseModel):
    """Object creation model"""
    type: str
    title: str
    icon: Optional[str] = None
    content: Optional[str] = None
    properties: Optional[ObjectProperties] = None
    layout: Optional[str] = "default"


class ObjectUpdate(BaseModel):
    """Object update model"""
    title: Optional[str] = None
    icon: Optional[str] = None
    content: Optional[str] = None
    properties: Optional[ObjectProperties] = None
    layout: Optional[str] = None


class ObjectListResponse(BaseModel):
    """Object list response"""
    objects: List[Dict[str, Any]]
    total: int
