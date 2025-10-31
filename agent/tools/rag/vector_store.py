"""
Vector Store Manager using ChromaDB

Handles storage and retrieval of document embeddings.
Provides hierarchical retrieval for SEC filings and simple retrieval for news.
"""

import os
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from .embeddings import get_embedding_service
from .chunking import Chunk


class VectorStoreManager:
    """
    Manages ChromaDB collections for different document types.
    Provides unified interface for storing and querying embeddings.
    """

    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize vector store manager.

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        self.embedding_service = get_embedding_service()

        # Initialize collections
        self.sec_collection = self._get_or_create_collection("sec_filings")
        self.news_collection = self._get_or_create_collection("news_articles")

    def _get_or_create_collection(self, name: str):
        """
        Get existing collection or create new one.

        Args:
            name: Collection name

        Returns:
            ChromaDB collection object
        """
        try:
            return self.client.get_collection(name=name)
        except:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )

    def add_chunks(self, chunks: List[Chunk], collection_name: str = "sec_filings"):
        """
        Add chunks to vector store with embeddings.

        Args:
            chunks: List of Chunk objects to add
            collection_name: Name of collection to add to
        """
        if not chunks:
            return

        collection = self.sec_collection if collection_name == "sec_filings" else self.news_collection

        # Extract texts for batch embedding
        texts = [chunk.text for chunk in chunks]

        # Generate embeddings in batch
        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embedding_service.embed_batch(texts)

        # Prepare data for ChromaDB
        ids = [chunk.chunk_id for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        # Add parent_id to metadata if it exists
        for i, chunk in enumerate(chunks):
            if chunk.parent_id:
                metadatas[i]['parent_id'] = chunk.parent_id

        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        print(f"Added {len(chunks)} chunks to {collection_name}")

    def query_sec_filing_hierarchical(self,
                                     query: str,
                                     ticker: str,
                                     filing_type: Optional[str] = None,
                                     n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Hierarchical retrieval for SEC filings.
        First retrieves parent chunks, then retrieves relevant child chunks.

        Args:
            query: Query string
            ticker: Stock ticker to filter by
            filing_type: Optional filing type filter ("10-K", "10-Q")
            n_results: Total number of results to return

        Returns:
            List of result dictionaries with text, metadata, and score
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)

        # Build where filter
        where_filter = {"ticker": ticker, "chunk_type": "parent"}
        if filing_type:
            where_filter["filing_type"] = filing_type

        # Step 1: Query parent chunks
        try:
            parent_results = self.sec_collection.query(
                query_embeddings=[query_embedding],
                where=where_filter,
                n_results=min(5, n_results)  # Get top 5 parents
            )
        except Exception as e:
            print(f"Error querying parent chunks: {e}")
            return []

        if not parent_results['ids'] or not parent_results['ids'][0]:
            # No results found, return empty
            return []

        # Step 2: For each parent, retrieve relevant child chunks
        all_results = []

        # Add parent chunks to results
        for i in range(len(parent_results['ids'][0])):
            all_results.append({
                'id': parent_results['ids'][0][i],
                'text': parent_results['documents'][0][i],
                'metadata': parent_results['metadatas'][0][i],
                'distance': parent_results['distances'][0][i],
                'chunk_type': 'parent'
            })

        # Get child chunks for each parent
        children_per_parent = max(2, (n_results - len(all_results)) // len(parent_results['ids'][0]))

        for parent_id in parent_results['ids'][0]:
            try:
                child_results = self.sec_collection.query(
                    query_embeddings=[query_embedding],
                    where={"parent_id": parent_id},
                    n_results=children_per_parent
                )

                if child_results['ids'] and child_results['ids'][0]:
                    for i in range(len(child_results['ids'][0])):
                        all_results.append({
                            'id': child_results['ids'][0][i],
                            'text': child_results['documents'][0][i],
                            'metadata': child_results['metadatas'][0][i],
                            'distance': child_results['distances'][0][i],
                            'chunk_type': 'child',
                            'parent_id': parent_id
                        })
            except Exception as e:
                print(f"Error querying child chunks for parent {parent_id}: {e}")
                continue

        # Sort all results by relevance (distance)
        all_results.sort(key=lambda x: x['distance'])

        # Return top N results
        return all_results[:n_results]

    def query_news(self,
                   query: str,
                   ticker: Optional[str] = None,
                   date_from: Optional[str] = None,
                   n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Simple semantic search for news articles.

        Args:
            query: Query string
            ticker: Optional ticker filter
            date_from: Optional date filter (YYYY-MM-DD)
            n_results: Number of results to return

        Returns:
            List of result dictionaries with text, metadata, and score
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)

        # Build where filter
        where_filter = {}
        if ticker:
            where_filter["ticker"] = ticker

        try:
            results = self.news_collection.query(
                query_embeddings=[query_embedding],
                where=where_filter if where_filter else None,
                n_results=n_results
            )
        except Exception as e:
            print(f"Error querying news: {e}")
            return []

        if not results['ids'] or not results['ids'][0]:
            return []

        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })

        return formatted_results

    def query_multi_source(self,
                          query: str,
                          ticker: str,
                          sources: List[str] = ["sec_filings", "news"],
                          n_results: int = 15) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query multiple document sources for comprehensive analysis.

        Args:
            query: Query string
            ticker: Stock ticker
            sources: List of sources to query
            n_results: Total results to return per source

        Returns:
            Dictionary mapping source names to result lists
        """
        results = {}

        if "sec_filings" in sources:
            results["sec_filings"] = self.query_sec_filing_hierarchical(
                query, ticker, n_results=n_results
            )

        if "news" in sources:
            results["news"] = self.query_news(
                query, ticker, n_results=n_results
            )

        return results

    def check_filing_indexed(self, ticker: str, filing_type: str, year: int) -> bool:
        """
        Check if a filing is already indexed in vector store.

        Args:
            ticker: Stock ticker
            filing_type: Filing type (10-K, 10-Q, etc.)
            year: Filing year

        Returns:
            True if filing is indexed, False otherwise
        """
        try:
            results = self.sec_collection.get(
                where={
                    "ticker": ticker,
                    "filing_type": filing_type,
                    "filing_year": year
                },
                limit=1
            )
            return len(results['ids']) > 0
        except:
            return False

    def delete_filing(self, ticker: str, filing_type: str, year: int):
        """
        Delete a filing from the vector store.

        Args:
            ticker: Stock ticker
            filing_type: Filing type
            year: Filing year
        """
        try:
            self.sec_collection.delete(
                where={
                    "ticker": ticker,
                    "filing_type": filing_type,
                    "filing_year": year
                }
            )
            print(f"Deleted {ticker} {filing_type} {year} from vector store")
        except Exception as e:
            print(f"Error deleting filing: {e}")

    def get_collection_stats(self) -> Dict[str, int]:
        """
        Get statistics about stored documents.

        Returns:
            Dictionary with collection counts
        """
        return {
            "sec_filings": self.sec_collection.count(),
            "news_articles": self.news_collection.count()
        }


# Global singleton instance
_vector_store_instance = None


def get_vector_store() -> VectorStoreManager:
    """
    Get or create the global vector store instance.
    Uses singleton pattern to maintain single ChromaDB connection.

    Returns:
        VectorStoreManager instance
    """
    global _vector_store_instance

    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreManager()

    return _vector_store_instance


if __name__ == "__main__":
    # Test vector store
    from dotenv import load_dotenv
    load_dotenv()

    store = VectorStoreManager()

    # Get stats
    stats = store.get_collection_stats()
    print(f"Vector store stats: {stats}")
