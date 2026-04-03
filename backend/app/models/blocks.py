"""Block Models"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class BlockProperties(BaseModel):
    """Block properties"""
    checked: Optional[bool] = None
    language: Optional[str] = None
    url: Optional[str] = None


class Block(BaseModel):
    """Block model"""
    id: str
    object_id: str
    type: str
    content: str
    level: int = 0
    order: int = 0
    properties: BlockProperties = Field(default_factory=BlockProperties)
    parent_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BlockCreate(BaseModel):
    """Block creation model"""
    object_id: str
    type: str = "paragraph"
    content: str = ""
    level: int = 0
    properties: Optional[BlockProperties] = None
    parent_id: Optional[str] = None


class BlockUpdate(BaseModel):
    """Block update model"""
    content: Optional[str] = None
    type: Optional[str] = None
    level: Optional[int] = None
    properties: Optional[BlockProperties] = None
    order: Optional[int] = None
    parent_id: Optional[str] = None


class BlockListResponse(BaseModel):
    """Block list response"""
    blocks: List[Dict[str, Any]]
