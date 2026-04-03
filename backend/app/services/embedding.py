"""Embedding Service - Generate embeddings for text and images"""
import numpy as np
from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.config import settings


class EmbeddingService:
    """Service for generating embeddings"""
    
    def __init__(self):
        self.text_model = None
        self.clip_model = None
        self.clip_processor = None
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def initialize(self):
        """Initialize embedding models"""
        print("📥 Loading embedding models...")
        
        # Load sentence transformer model (for text)
        try:
            from sentence_transformers import SentenceTransformer
            self.text_model = SentenceTransformer(settings.embedding_model)
            print(f"✅ Loaded text model: {settings.embedding_model}")
        except Exception as e:
            print(f"⚠️ Could not load text model: {e}")
        
        # Load CLIP model (for images) - lazy load on first use
        print("📥 CLIP model will be loaded on first image embedding")
    
    async def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        if not self.text_model:
            raise RuntimeError("Text model not loaded")
        
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(384)
        
        # Run in thread pool to not block
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            self.executor,
            self.text_model.encode,
            text
        )
        
        return embedding
    
    async def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts"""
        if not self.text_model:
            raise RuntimeError("Text model not loaded")
        
        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        
        if not valid_texts:
            return [np.zeros(384) for _ in texts]
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            self.executor,
            self.text_model.encode,
            valid_texts
        )
        
        return embeddings
    
    async def embed_image(self, image_path: str) -> Optional[np.ndarray]:
        """Generate embedding for image using CLIP"""
        try:
            # Lazy load CLIP
            if self.clip_model is None:
                from transformers import CLIPProcessor, CLIPModel
                from PIL import Image
                
                print("📥 Loading CLIP model...")
                self.clip_model = CLIPModel.from_pretrained(settings.clip_model)
                self.clip_processor = CLIPProcessor.from_pretrained(settings.clip_model)
                print("✅ Loaded CLIP model")
            
            from PIL import Image
            
            # Load image
            image = Image.open(image_path).convert("RGB")
            
            # Process
            inputs = self.clip_processor(images=image, return_tensors="pt")
            
            # Generate embedding in thread pool
            loop = asyncio.get_event_loop()
            
            def _embed():
                import torch
                with torch.no_grad():
                    image_features = self.clip_model.get_image_features(**inputs)
                # Normalize
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                return image_features.numpy().flatten()
            
            embedding = await loop.run_in_executor(self.executor, _embed)
            return embedding
            
        except Exception as e:
            print(f"Error embedding image {image_path}: {e}")
            return None
    
    async def embed_image_batch(self, image_paths: List[str]) -> List[Optional[np.ndarray]]:
        """Generate embeddings for multiple images"""
        embeddings = []
        for path in image_paths:
            emb = await self.embed_image(path)
            embeddings.append(emb)
        return embeddings
    
    def get_text_dimension(self) -> int:
        """Get text embedding dimension"""
        if self.text_model:
            return self.text_model.get_sentence_embedding_dimension()
        return 384  # Default for all-MiniLM-L6-v2
    
    def get_image_dimension(self) -> int:
        """Get image embedding dimension"""
        return 512  # CLIP dimension


# Global instance
embedding_service = EmbeddingService()
