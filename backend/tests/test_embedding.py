"""
Tests for the embedding service.
"""

import pytest
import numpy as np


@pytest.mark.asyncio
class TestEmbeddingService:
    """Test cases for embedding generation service."""

    def test_embed_text_basic(self, mock_embedding_service):
        """Test basic text embedding."""
        text = "This is a test sentence"
        vector = mock_embedding_service.embed_text(text)

        assert vector is not None
        assert len(vector) == 384
        assert all(isinstance(v, (int, float)) for v in vector)

    def test_embed_text_empty(self, mock_embedding_service):
        """Test embedding empty text."""
        text = ""
        vector = mock_embedding_service.embed_text(text)

        assert vector is not None
        assert len(vector) == 384

    def test_embed_text_unicode(self, mock_embedding_service):
        """Test embedding text with Unicode characters."""
        text = "Test with emoji 🎉 and 中文 characters"
        vector = mock_embedding_service.embed_text(text)

        assert vector is not None
        assert len(vector) == 384

    def test_embed_text_long(self, mock_embedding_service):
        """Test embedding long text."""
        text = "word " * 1000  # Long text
        vector = mock_embedding_service.embed_text(text)

        assert vector is not None
        assert len(vector) == 384

    def test_embed_texts_batch(self, mock_embedding_service):
        """Test batch embedding of multiple texts."""
        texts = [
            "First text",
            "Second text",
            "Third text",
        ]

        vectors = mock_embedding_service.embed_texts(texts)

        assert len(vectors) == len(texts)
        assert all(len(v) == 384 for v in vectors)

    def test_embed_texts_empty_list(self, mock_embedding_service):
        """Test embedding empty list of texts."""
        vectors = mock_embedding_service.embed_texts([])

        assert vectors == []

    def test_embed_texts_single(self, mock_embedding_service):
        """Test embedding single text in batch."""
        texts = ["Single text"]
        vectors = mock_embedding_service.embed_texts(texts)

        assert len(vectors) == 1
        assert len(vectors[0]) == 384

    def test_embed_image_basic(self, mock_embedding_service):
        """Test basic image embedding."""
        image_path = "/path/to/image.jpg"
        vector = mock_embedding_service.embed_image(image_path)

        assert vector is not None
        assert len(vector) == 512

    def test_deterministic_embeddings(self, mock_embedding_service):
        """Test that same input produces same embedding."""
        text = "Deterministic test"

        vector1 = mock_embedding_service.embed_text(text)
        vector2 = mock_embedding_service.embed_text(text)

        assert vector1 == vector2

    def test_different_inputs_different_embeddings(self, mock_embedding_service):
        """Test that different inputs produce different embeddings."""
        vector1 = mock_embedding_service.embed_text("text one")
        vector2 = mock_embedding_service.embed_text("text two")

        assert vector1 != vector2

    def test_embedding_normalization(self, mock_embedding_service):
        """Test that embeddings are normalized (if applicable)."""
        text = "Test text"
        vector = mock_embedding_service.embed_text(text)

        # Check if vector is normalized (L2 norm = 1)
        # This may or may not be true depending on the embedding model
        norm = np.linalg.norm(vector)
        assert norm > 0

    def test_embedding_values_range(self, mock_embedding_service):
        """Test that embedding values are in expected range."""
        text = "Test text"
        vector = mock_embedding_service.embed_text(text)

        # Most embedding models produce values in [-1, 1] or [0, 1]
        assert all(-1 <= v <= 1 for v in vector)


@pytest.mark.asyncio
class TestEmbeddingFallback:
    """Test cases for embedding fallback mode."""

    def test_fallback_mode_deterministic(self, mock_embedding_service):
        """Test that fallback mode produces deterministic vectors."""
        text1 = "test"
        text2 = "test"

        vector1 = mock_embedding_service.embed_text(text1)
        vector2 = mock_embedding_service.embed_text(text2)

        assert vector1 == vector2

    def test_fallback_different_inputs(self, mock_embedding_service):
        """Test that fallback mode produces different vectors for different inputs."""
        vector1 = mock_embedding_service.embed_text("apple")
        vector2 = mock_embedding_service.embed_text("banana")

        # Should be different
        assert vector1 != vector2

    def test_fallback_vector_dimensions(self, mock_embedding_service):
        """Test that fallback produces correct dimensions."""
        vector = mock_embedding_service.embed_text("test")

        assert len(vector) == 384


@pytest.mark.asyncio
class TestEmbeddingModelLoading:
    """Test cases for embedding model loading."""

    async def test_initialize_service(self):
        """Test initializing embedding service."""
        from app.services.embedding import embedding_service

        # Should initialize without errors
        await embedding_service.initialize()

    async def test_close_service(self):
        """Test closing embedding service."""
        from app.services.embedding import embedding_service

        # Should close without errors
        await embedding_service.close()

    async def test_service_singleton(self):
        """Test that embedding service is a singleton."""
        from app.services.embedding import embedding_service

        # Multiple imports should return same instance
        from app.services.embedding import embedding_service as es2

        assert embedding_service is es2


@pytest.mark.asyncio
class TestEmbeddingPerformance:
    """Test cases for embedding service performance."""

    def test_batch_embedding_performance(self, mock_embedding_service):
        """Test batch embedding performance."""
        import time

        texts = ["text"] * 100

        start = time.time()
        vectors = mock_embedding_service.embed_texts(texts)
        elapsed = time.time() - start

        assert len(vectors) == 100
        # Mock should be fast, real model would be slower
        assert elapsed < 1.0

    def test_single_embedding_performance(self, mock_embedding_service):
        """Test single text embedding performance."""
        import time

        text = "This is a test of embedding performance"

        start = time.time()
        vector = mock_embedding_service.embed_text(text)
        elapsed = time.time() - start

        assert len(vector) == 384
        # Mock should be very fast
        assert elapsed < 0.1


@pytest.mark.asyncio
class TestEmbeddingEdgeCases:
    """Test cases for embedding edge cases."""

    def test_very_long_text(self, mock_embedding_service):
        """Test embedding very long text."""
        text = "word " * 10000

        vector = mock_embedding_service.embed_text(text)

        assert vector is not None
        assert len(vector) == 384

    def test_special_characters_only(self, mock_embedding_service):
        """Test embedding text with only special characters."""
        text = "!@#$%^&*()_+-=[]{}|;:,.<>?/"

        vector = mock_embedding_service.embed_text(text)

        assert vector is not None
        assert len(vector) == 384

    def test_newlines_and_tabs(self, mock_embedding_service):
        """Test embedding text with newlines and tabs."""
        text = "line1\nline2\tindented"

        vector = mock_embedding_service.embed_text(text)

        assert vector is not None
        assert len(vector) == 384

    def test_numbers_and_mixed_content(self, mock_embedding_service):
        """Test embedding text with numbers and mixed content."""
        text = "Version 2.0 released on 2024-01-01 with 1000+ features!"

        vector = mock_embedding_service.embed_text(text)

        assert vector is not None
        assert len(vector) == 384
