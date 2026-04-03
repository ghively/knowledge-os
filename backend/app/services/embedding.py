"""Embedding Service - Text and image embeddings"""
import logging
import asyncio
from typing import List, Optional
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings"""
    
    def __init__(self):
        self.text_model = None
        self.image_model = None
        self.loop = None
    
    async def initialize(self):
        """Initialize the embedding service - load models"""
        logger.info("Loading embedding models...")
        
        # Models are loaded lazily on first use
        # This avoids blocking startup
        
        logger.info("Embedding service initialized")
    
    async def close(self):
        """Close the embedding service"""
        logger.info("Embedding service closed")
    
    def _load_text_model(self):
        """Load text embedding model"""
        if self.text_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded text embedding model")
            except Exception as e:
                logger.error(f"Error loading text model: {e}")
                raise
    
    async def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        if not text:
            # Return zero vector for empty text
            return np.zeros(384)
        
        self._load_text_model()
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self.text_model.encode(text, convert_to_numpy=True)
        )
        
        return embedding
    
    async def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        self._load_text_model()
        
        # Run in thread pool
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.text_model.encode(texts, convert_to_numpy=True)
        )
        
        return embeddings
    
    def _load_image_model(self):
        """Load image embedding model"""
        if self.image_model is None:
            try:
                from transformers import CLIPProcessor, CLIPModel
                self.image_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                self.image_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                logger.info("Loaded image embedding model")
            except Exception as e:
                logger.error(f"Error loading image model: {e}")
                raise
    
    async def embed_image(self, image_path: str) -> np.ndarray:
        """Generate embedding for image"""
        self._load_image_model()
        
        from PIL import Image
        
        # Load image
        image = Image.open(image_path)
        
        # Process
        inputs = self.image_processor(images=image, return_tensors="pt")
        
        # Run in thread pool
        loop = asyncio.get_running_loop()
        outputs = await loop.run_in_executor(
            None,
            lambda: self.image_model.get_image_features(**inputs)
        )
        
        # Convert to numpy
        embedding = outputs.detach().numpy().flatten()
        
        return embedding


# Global embedding service instance
embedding_service = EmbeddingService()
