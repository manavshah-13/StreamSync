import sys
import os
import threading
from unittest.mock import MagicMock, patch

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np

def test_product_embedder_singleton_and_thread_safety():
    # Mock the SentenceTransformer to avoid internet dependency and speed up tests
    mock_model = MagicMock()
    mock_model.encode.side_effect = lambda x: np.random.randn(384)

    with patch('app.ml.embedder.SentenceTransformer', return_value=mock_model) as mock_st:
        from app.ml.embedder import ProductEmbedder

        # Reset singleton instance to ensure clean test state
        ProductEmbedder._instance = None

        # Instantiate the embedder twice
        embedder1 = ProductEmbedder()
        embedder2 = ProductEmbedder()

        # Check singleton identity
        assert embedder1 is embedder2

        # Verify that SentenceTransformer was only instantiated once with the correct model
        mock_st.assert_called_once_with("all-MiniLM-L6-v2")

        # Get embedding and verify dimensions/type
        emb = embedder1.get_embedding("StreamSync ML Layer")
        assert isinstance(emb, list)
        assert len(emb) == 384
        assert all(isinstance(x, float) for x in emb)

        # Test thread-safety with concurrent calls
        results = []
        errors = []

        def worker(text):
            try:
                res = embedder1.get_embedding(text)
                results.append(res)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(20):
            t = threading.Thread(target=worker, args=(f"sample text query {i}",))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Ensure no thread encountered any errors and all retrieved the embedding
        assert len(errors) == 0, f"Errors occurred in threads: {errors}"
        assert len(results) == 20
        for res in results:
            assert len(res) == 384
            assert all(isinstance(x, float) for x in res)
