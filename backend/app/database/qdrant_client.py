"""Qdrant Database Manager"""
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PayloadSchemaType,
    CreateCollection, OptimizersConfig
)
from typing import List, Optional, Dict, Any
import uuid
import asyncio

from app.config import settings


# Collection configurations
COLLECTIONS = {
    "objects": {
        "vector_size": 384,
        "distance": Distance.COSINE,
        "on_disk_payload": False,
    },
    "blocks": {
        "vector_size": 384,
        "distance": Distance.COSINE,
        "on_disk_payload": False,
    },
    "relations": {
        "vector_size": 384,  # Small vectors for relation context
        "distance": Distance.COSINE,
        "on_disk_payload": False,
    },
    "files": {
        "vector_size": 384,
        "distance": Distance.COSINE,
        "on_disk_payload": True,  # Files can be large
    },
    "images": {
        "vector_size": 512,  # CLIP dimension
        "distance": Distance.COSINE,
        "on_disk_payload": True,
    },
    "code": {
        "vector_size": 384,
        "distance": Distance.COSINE,
        "on_disk_payload": True,
    },
    "agent_memories": {
        "vector_size": 384,
        "distance": Distance.COSINE,
        "on_disk_payload": False,
    },
    "chat_logs": {
        "vector_size": 384,
        "distance": Distance.COSINE,
        "on_disk_payload": False,
    },
}


class QdrantManager:
    """Manages Qdrant connection and collections"""
    
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.async_client: Optional[AsyncQdrantClient] = None
    
    async def initialize(self):
        """Initialize Qdrant connection and collections"""
        # Sync client for most operations
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key,
            prefer_grpc=True
        )
        
        # Async client for async operations
        self.async_client = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key,
            prefer_grpc=True
        )
        
        # Create collections if they don't exist
        for collection_name, config in COLLECTIONS.items():
            await self._ensure_collection(collection_name, config)
        
        print(f"✅ Qdrant initialized with {len(COLLECTIONS)} collections")
    
    async def _ensure_collection(self, name: str, config: Dict[str, Any]):
        """Ensure a collection exists"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == name for c in collections)
            
            if not exists:
                print(f"📦 Creating collection: {name}")
                
                # Create collection
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=config["vector_size"],
                        distance=config["distance"]
                    ),
                    optimizers_config=OptimizersConfig(
                        indexing_threshold=100
                    ),
                    on_disk_payload=config.get("on_disk_payload", False)
                )
                
                # Create payload indexes for common fields
                if name in ["objects", "blocks"]:
                    try:
                        self.client.create_payload_index(
                            collection_name=name,
                            field_name="type",
                            field_schema=PayloadSchemaType.KEYWORD
                        )
                        self.client.create_payload_index(
                            collection_name=name,
                            field_name="properties.tags",
                            field_schema=PayloadSchemaType.KEYWORD
                        )
                    except Exception as e:
                        print(f"Warning: Could not create index: {e}")
                
                print(f"✅ Created collection: {name}")
            
        except Exception as e:
            print(f"❌ Error ensuring collection {name}: {e}")
            raise
    
    async def close(self):
        """Close connections"""
        if self.client:
            self.client.close()
        if self.async_client:
            await self.async_client.close()
    
    # Convenience methods
    def get_client(self) -> QdrantClient:
        """Get sync client"""
        return self.client
    
    def get_async_client(self) -> AsyncQdrantClient:
        """Get async client"""
        return self.async_client


# Global instance
qdrant_manager = QdrantManager()
