import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import sys
from pathlib import Path

# Add the source directory to the path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'source'))

from vector_store.vector_store import VectorStore


class TestVectorStore(unittest.TestCase):
    """Test suite for the VectorStore class."""

    def setUp(self):
        """Set up test fixtures."""
        self.pinecone_api_key = "test-api-key"
        self.index_name = "test-index"

    @patch('vector_store.vector_store.Pinecone')
    @patch('vector_store.vector_store.HuggingFaceEmbeddings')
    def test_initialization(self, mock_embeddings, mock_pinecone):
        """Test VectorStore initialization."""
        # Mock the embeddings model
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query.return_value = [0.1] * 384
        mock_embeddings.return_value = mock_embeddings_instance

        # Mock Pinecone
        mock_pc = Mock()
        mock_pc.list_indexes.return_value.names.return_value = []
        mock_pinecone.return_value = mock_pc

        vs = VectorStore(self.pinecone_api_key, self.index_name)

        # Verify embeddings model was initialized
        mock_embeddings.assert_called_once()
        # Verify Pinecone was initialized
        mock_pinecone.assert_called_once_with(api_key=self.pinecone_api_key)

    @patch('vector_store.vector_store.Pinecone')
    @patch('vector_store.vector_store.HuggingFaceEmbeddings')
    def test_index_creation(self, mock_embeddings, mock_pinecone):
        """Test that a new index is created if it doesn't exist."""
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query.return_value = [0.1] * 384
        mock_embeddings.return_value = mock_embeddings_instance

        mock_pc = Mock()
        mock_pc.list_indexes.return_value.names.return_value = []
        mock_pc.Index.return_value = Mock()
        mock_pinecone.return_value = mock_pc

        vs = VectorStore(self.pinecone_api_key, self.index_name)

        # Verify create_index was called
        mock_pc.create_index.assert_called_once()

    @patch('vector_store.vector_store.Pinecone')
    @patch('vector_store.vector_store.HuggingFaceEmbeddings')
    def test_load_and_parse_xml_file_not_found(self, mock_embeddings, mock_pinecone):
        """Test XML parsing with a non-existent file."""
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query.return_value = [0.1] * 384
        mock_embeddings.return_value = mock_embeddings_instance

        mock_pc = Mock()
        mock_pc.list_indexes.return_value.names.return_value = ["test-index"]
        mock_pc.Index.return_value = Mock()
        mock_pinecone.return_value = mock_pc

        vs = VectorStore(self.pinecone_api_key, self.index_name)
        result = vs._load_and_parse_xml("/nonexistent/path/file.xml")

        # Should return empty list for missing file
        self.assertEqual(result, [])

    @patch('vector_store.vector_store.Pinecone')
    @patch('vector_store.vector_store.HuggingFaceEmbeddings')
    def test_load_and_parse_xml_valid_file(self, mock_embeddings, mock_pinecone):
        """Test XML parsing with a valid XML file."""
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query.return_value = [0.1] * 384
        mock_embeddings.return_value = mock_embeddings_instance

        mock_pc = Mock()
        mock_pc.list_indexes.return_value.names.return_value = ["test-index"]
        mock_pc.Index.return_value = Mock()
        mock_pinecone.return_value = mock_pc

        # Create a temporary XML file
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <context id="ctx1">
                <period>
                    <instant>2024-01-01</instant>
                </period>
            </context>
            <Revenue contextRef="ctx1">1000000</Revenue>
        </root>
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
            f.write(xml_content)
            temp_file = f.name

        try:
            vs = VectorStore(self.pinecone_api_key, self.index_name)
            docs = vs._load_and_parse_xml(temp_file)

            # Verify documents were parsed
            self.assertGreater(len(docs), 0)
            self.assertIn('text', docs[0])
            self.assertIn('metadata', docs[0])
            self.assertEqual(docs[0]['metadata']['period'], '2024-01-01')
        finally:
            os.unlink(temp_file)

    @patch('vector_store.vector_store.Pinecone')
    @patch('vector_store.vector_store.HuggingFaceEmbeddings')
    def test_embed_and_upsert(self, mock_embeddings, mock_pinecone):
        """Test embedding and upserting documents."""
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query.return_value = [0.1] * 384
        mock_embeddings_instance.embed_documents.return_value = [[0.1] * 384, [0.2] * 384]
        mock_embeddings.return_value = mock_embeddings_instance

        mock_index = Mock()
        mock_pc = Mock()
        mock_pc.list_indexes.return_value.names.return_value = ["test-index"]
        mock_pc.Index.return_value = mock_index
        mock_pinecone.return_value = mock_pc

        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <context id="ctx1">
                <period>
                    <instant>2024-01-01</instant>
                </period>
            </context>
            <Revenue contextRef="ctx1">1000000</Revenue>
            <NetIncome contextRef="ctx1">500000</NetIncome>
        </root>
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
            f.write(xml_content)
            temp_file = f.name

        try:
            vs = VectorStore(self.pinecone_api_key, self.index_name)
            vs.embed_and_upsert(temp_file, "doc_123", batch_size=10, max_workers=2)

            # Verify upsert was called
            mock_index.upsert.assert_called()
        finally:
            os.unlink(temp_file)

    @patch('vector_store.vector_store.Pinecone')
    @patch('vector_store.vector_store.HuggingFaceEmbeddings')
    def test_query(self, mock_embeddings, mock_pinecone):
        """Test querying the Pinecone index."""
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query.return_value = [0.1] * 384
        mock_embeddings.return_value = mock_embeddings_instance

        mock_index = Mock()
        mock_index.query.return_value = {
            'matches': [
                {
                    'id': 'doc_123_0',
                    'score': 0.95,
                    'metadata': {'text': 'Revenue is 1000000', 'period': '2024-01-01'}
                }
            ]
        }
        mock_pc = Mock()
        mock_pc.list_indexes.return_value.names.return_value = ["test-index"]
        mock_pc.Index.return_value = mock_index
        mock_pinecone.return_value = mock_pc

        vs = VectorStore(self.pinecone_api_key, self.index_name)
        results = vs.query("What is the revenue?", "doc_123", top_k=5)

        # Verify query was called with correct parameters
        mock_index.query.assert_called_once()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['score'], 0.95)


if __name__ == '__main__':
    unittest.main()