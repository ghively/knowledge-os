"""Block Models"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class BlockType(str, Enum):
    """Block types"""
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    TODO = "todo"
    BULLET = "bullet"
    NUMBERED = "numbered"
    QUOTE = "quote"
    CODE = "code"
    DIVIDER = "divider"
    IMAGE = "image"
    EMBED = "embed"
    CALLOUT = "callout"


class BlockProperties(BaseModel):
    """Block properties"""
    checked: Optional[bool] = None  # For todos
    language: Optional[str] = None  # For code blocks
    collapsed: Optional[bool] = False
    
    # Task assignment within block
    assigned_to: Optional[str] = None  # Agent name
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    
    # Image/embed
    src: Optional[str] = None
    alt: Optional[str] = None
    caption: Optional[str] = None
    
    class Config:
        extra = "allow"


class Block(BaseModel):
    """Block model"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    object_id: str
    content: str
    type: BlockType = BlockType.PARAGRAPH
    level: int = 0  # Heading level or indentation
    properties: BlockProperties = Field(default_factory=BlockProperties)
    order: int = 0  # Position in object
    parent_id: Optional[str] = None  # For nested blocks
    
    # Backlinks/references
    references: List[str] = Field(default_factory=list)  # Block IDs this references
    referenced_by: List[str] = Field(default_factory=list)  # Block IDs referencing this
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "block-123",
                "object_id": "abc-123",
                "content": "Research vector databases",
                "type": "todo",
                "level": 1,
                "properties": {
                    "checked": False,
                    "assigned_to": "researcher"
                },
                "order": 0
            }
        }


class BlockCreate(BaseModel):
    """Block creation request"""
    content: str
    type: Optional[BlockType] = BlockType.PARAGRAPH
    level: Optional[int] = 0
    properties: Optional[BlockProperties] = None
    parent_id: Optional[str] = None


class BlockUpdate(BaseModel):
    """Block update request"""
    content: Optional[str] = None
    type: Optional[BlockType] = None
    level: Optional[int] = None
    properties: Optional[BlockProperties] = None
    order: Optional[int] = None


class BlockMoveRequest(BaseModel):
    """Block move request"""
    block_id: str
    new_order: int
    new_parent_id: Optional[str] = None


class BlockListResponse(BaseModel):
    """List of blocks"""
    blocks: List[Block]
    total: int


class BlockBatchUpdate(BaseModel):
    """Batch update blocks"""
    blocks: List[Block]
