import sys
import os
from unittest.mock import MagicMock, patch

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from app.services.recommendation_service import compute_active_session_vector
from app.core import lifecycle

@pytest.mark.asyncio
async def test_compute_active_session_vector_cache_hit():
    # Mock Redis session history
    mock_skus = [b"prod-1", b"prod-2"]
    mock_db = MagicMock()

    # Pre-populate startup cache
    vec1 = [0.1] * 384
    vec2 = [0.2] * 384
    lifecycle.PRODUCT_EMBEDDING_CACHE["prod-1"] = vec1
    lifecycle.PRODUCT_EMBEDDING_CACHE["prod-2"] = vec2

    with patch("app.services.recommendation_service.get_active_session_history", return_value=mock_skus):
        result = await compute_active_session_vector("session-xyz", mock_db)

        # Expected blend math:
        # composite = 1.0 * vec1 + 0.8 * vec2
        #           = [0.1]*384 + [0.16]*384 = [0.26]*384
        # Normalized:
        # norm = sqrt(384 * 0.26^2) = 0.26 * sqrt(384)
        # result = [0.26] / (0.26 * sqrt(384)) = [1 / sqrt(384)] * 384
        expected_val = 1.0 / np.sqrt(384)
        
        assert len(result) == 384
        assert np.allclose(result, [expected_val] * 384)

@pytest.mark.asyncio
async def test_compute_active_session_vector_db_fallback():
    # Mock Redis history with a SKU not in cache
    mock_skus = ["prod-db"]
    mock_db = MagicMock()
    
    # Ensure not in cache
    if "prod-db" in lifecycle.PRODUCT_EMBEDDING_CACHE:
        del lifecycle.PRODUCT_EMBEDDING_CACHE["prod-db"]

    # Mock product returned by database
    mock_product = MagicMock()
    mock_product.id = "prod-db"
    mock_product.name = "Database Product"
    mock_product.category = "Test"
    mock_product.description = "Fetched from DB"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_product

    # Mock ProductEmbedder to avoid loading SentenceTransformer
    mock_embedder = MagicMock()
    mock_embedder.get_embedding.return_value = [0.5] * 384

    with patch("app.services.recommendation_service.get_active_session_history", return_value=mock_skus), \
         patch("app.services.recommendation_service.ProductEmbedder", return_value=mock_embedder):
         
        result = await compute_active_session_vector("session-xyz", mock_db)

        # Verify DB query
        mock_db.query.assert_called_once()
        
        # Verify it was added to the cache
        assert "prod-db" in lifecycle.PRODUCT_EMBEDDING_CACHE
        assert lifecycle.PRODUCT_EMBEDDING_CACHE["prod-db"] == [0.5] * 384
        
        # Normalized [0.5]*384 should be [1/sqrt(384)]*384
        expected_val = 1.0 / np.sqrt(384)
        assert np.allclose(result, [expected_val] * 384)

@pytest.mark.asyncio
async def test_compute_active_session_vector_empty_fallback():
    # Empty history
    mock_db = MagicMock()
    with patch("app.services.recommendation_service.get_active_session_history", return_value=[]):
        result = await compute_active_session_vector("session-empty", mock_db)
        assert result == [0.0] * 384

    # Redis error
    with patch("app.services.recommendation_service.get_active_session_history", side_effect=Exception("Redis connection error")):
        result = await compute_active_session_vector("session-error", mock_db)
        assert result == [0.0] * 384
