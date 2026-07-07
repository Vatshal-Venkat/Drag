import os
import unittest
from unittest.mock import patch, MagicMock

# Set environment variable before importing to avoid config exceptions
os.environ["GROQ_API_KEY"] = "gsk_test"
os.environ["GEMINI_API_KEY"] = "AIzaSy_test"

from app.services.embeddings import embed_texts, embed_query
from app.services.retriever import retrieve_context, retrieve
from app.vectorstore.store_manager import get_store_for_document

class TestRetrievalBugs(unittest.TestCase):

    @patch("app.services.embeddings._get_client")
    def test_embeddings_propagate_exception(self, mock_get_client):
        # Configure client to raise exception
        mock_get_client.side_effect = RuntimeError("Mock API Key Error")
        
        # Verify that embed_texts raises RuntimeError
        with self.assertRaises(RuntimeError):
            embed_texts(["hello"])
            
        # Verify that embed_query raises RuntimeError
        with self.assertRaises(RuntimeError):
            embed_query("hello")

    @patch("app.services.retriever.get_store_for_document")
    @patch("app.services.retriever.get_bm25_for_store")
    @patch("app.services.retriever.embed_query")
    def test_retrieve_context_no_nan_when_no_keyword_match(self, mock_embed_query, mock_get_bm25, mock_get_store):
        # Setup mock FAISS store search result
        mock_store = MagicMock()
        mock_store.search.return_value = [
            {"id": 0, "text": "This is sample text about dogs.", "source": "test.txt", "page": 1, "confidence": 0.8}
        ]
        mock_get_store.return_value = mock_store
        
        # Setup mock BM25 with query tokens that don't match (BM25 scores will be all 0.0)
        import numpy as np
        mock_bm25 = MagicMock()
        mock_bm25.get_scores.return_value = np.array([0.0]) # all zero scores!
        mock_get_bm25.return_value = mock_bm25
        
        mock_embed_query.return_value = [0.1] * 768
        
        # Run retrieval - it should run successfully and return hybrid score without NaN errors
        results = retrieve_context(query="cats", top_k=1, document_id="test.txt")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 0)
        # Verify final_score is calculated and is a valid float (not NaN)
        import math
        final_score = results[0]["final_score"]
        self.assertTrue(not math.isnan(final_score))
        self.assertEqual(final_score, round(0.8 * 0.8 + 0.2 * 0.0, 4)) # semantic_weight = 0.8, bm25_weight = 0.2, confidence = 0.8, bm25_score = 0.0

if __name__ == "__main__":
    unittest.main()
