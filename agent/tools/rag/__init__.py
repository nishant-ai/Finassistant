"""
RAG (Retrieval-Augmented Generation) Tools

Provides vector store-based semantic search across financial documents.
"""

from .embeddings import EmbeddingService
from .vector_store import VectorStoreManager
from .chunking import DocumentChunker, SECFilingChunker, NewsArticleChunker
from .rag_tools import (
    semantic_search_sec_filing,
    semantic_search_news,
    multi_document_analysis
)

__all__ = [
    'EmbeddingService',
    'VectorStoreManager',
    'DocumentChunker',
    'SECFilingChunker',
    'NewsArticleChunker',
    'semantic_search_sec_filing',
    'semantic_search_news',
    'multi_document_analysis'
]
