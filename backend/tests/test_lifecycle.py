import sys
import os
from unittest.mock import MagicMock, patch

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio
from app.core import lifecycle

@pytest.mark.asyncio
async def test_build_and_cache_catalog_embeddings_success():
    mock_db = MagicMock()
    mock_embeddings = [{"prod-1": [0.1] * 384}, {"prod-2": [0.2] * 384}]
    
    with patch("app.core.lifecycle.SessionLocal", return_value=mock_db), \
         patch("app.core.lifecycle.generate_catalog_embeddings", return_value=mock_embeddings) as mock_gen:
         
        # Reset cache
        lifecycle.PRODUCT_EMBEDDING_CACHE.clear()
        
        await lifecycle.build_and_cache_catalog_embeddings()
        
        # Verify mock interactions
        mock_gen.assert_called_once_with(mock_db)
        mock_db.close.assert_called_once()
        
        # Verify cache has correct contents loaded
        assert len(lifecycle.PRODUCT_EMBEDDING_CACHE) == 2
        assert lifecycle.PRODUCT_EMBEDDING_CACHE["prod-1"] == [0.1] * 384
        assert lifecycle.PRODUCT_EMBEDDING_CACHE["prod-2"] == [0.2] * 384

@pytest.mark.asyncio
async def test_build_and_cache_catalog_embeddings_failure_handling():
    mock_db = MagicMock()
    
    with patch("app.core.lifecycle.SessionLocal", return_value=mock_db), \
         patch("app.core.lifecycle.generate_catalog_embeddings", side_effect=Exception("Model download error")):
         
        lifecycle.PRODUCT_EMBEDDING_CACHE.clear()
        
        # Executing this should not crash the process; it should capture and handle the exception gracefully
        await lifecycle.build_and_cache_catalog_embeddings()
        
        # Verify cache is empty and cleanup was executed
        assert len(lifecycle.PRODUCT_EMBEDDING_CACHE) == 0
        mock_db.close.assert_called_once()

def test_register_startup_sync():
    mock_app = MagicMock()
    with patch("asyncio.create_task") as mock_create_task:
        lifecycle.register_startup_sync(mock_app)
        mock_create_task.assert_called_once()
