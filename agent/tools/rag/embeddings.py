"""
Embedding Service for RAG

Uses Google's text-embedding-004 model (free with Gemini API).
Provides caching and batch processing capabilities.
"""

import os
from typing import List, Union
from functools import lru_cache
import hashlib
import json
from google import genai
from google.genai import types


class EmbeddingService:
    """
    Handles text embeddings using Google's embedding models.
    Provides caching to reduce API calls and costs.
    """

    def __init__(self, model_name: str = "text-embedding-004"):
        """
        Initialize embedding service.

        Args:
            model_name: Google embedding model to use
        """
        self.model_name = model_name
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self._embedding_dim = 768  # text-embedding-004 dimension

    @property
    def embedding_dimension(self) -> int:
        """Return the dimension of embeddings produced by this model."""
        return self._embedding_dim

    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text string.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        try:
            result = self.client.models.embed_content(
                model=self.model_name,
                content=text
            )
            return result.embeddings[0].values

        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self._embedding_dim

    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Embed multiple texts in batches for efficiency.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to embed per API call

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                result = self.client.models.embed_content(
                    model=self.model_name,
                    content=batch
                )
                batch_embeddings = [emb.values for emb in result.embeddings]
                embeddings.extend(batch_embeddings)

            except Exception as e:
                print(f"Error embedding batch {i // batch_size}: {e}")
                # Add zero vectors for failed batch
                embeddings.extend([[0.0] * self._embedding_dim] * len(batch))

        return embeddings

    @lru_cache(maxsize=1000)
    def embed_text_cached(self, text: str) -> tuple:
        """
        Cached version of embed_text for frequently used queries.
        Returns tuple for hashability (LRU cache requirement).

        Args:
            text: Text to embed

        Returns:
            Tuple of floats representing the embedding vector
        """
        embedding = self.embed_text(text)
        return tuple(embedding)

    def get_text_hash(self, text: str) -> str:
        """
        Generate a unique hash for text content.
        Useful for cache keys and deduplication.

        Args:
            text: Text to hash

        Returns:
            MD5 hash of the text
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()


# Global singleton instance
_embedding_service_instance = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create the global embedding service instance.
    Uses singleton pattern to avoid multiple API client initializations.

    Returns:
        EmbeddingService instance
    """
    global _embedding_service_instance

    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()

    return _embedding_service_instance


if __name__ == "__main__":
    # Test the embedding service
    from dotenv import load_dotenv
    load_dotenv()

    service = EmbeddingService()

    # Test single embedding
    text = "Apple Inc. reported strong quarterly earnings with revenue growth of 15%."
    embedding = service.embed_text(text)

    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")

    # Test batch embedding
    texts = [
        "Revenue increased by 20% year-over-year",
        "The company faces regulatory challenges in Europe",
        "New product launches are expected next quarter"
    ]
    batch_embeddings = service.embed_batch(texts)

    print(f"\nBatch embeddings: {len(batch_embeddings)} vectors")
    print(f"All vectors have dimension {len(batch_embeddings[0])}")
