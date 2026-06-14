import sys
import os
from unittest.mock import MagicMock, patch

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np

from app.ml.indexer import build_product_text_blob, generate_catalog_embeddings

def test_build_product_text_blob():
    # Test typical input
    blob = build_product_text_blob("Running Shoes", "Apparel", "Comfortable for jogging.")
    assert blob == "running shoes apparel comfortable for jogging."
    
    # Test None and empty values
    blob_null = build_product_text_blob(None, "", None)
    assert blob_null == ""
    
    # Test excessive and weird whitespace
    blob_spacing = build_product_text_blob("  New  Laptop\n", "\tElectronics  ", "\rSleek design.   ")
    assert blob_spacing == "new laptop electronics sleek design."

@pytest.mark.asyncio
async def test_generate_catalog_embeddings():
    # Mock database session query
    mock_db = MagicMock()
    
    # Mock product instances
    p1 = MagicMock()
    p1.id = "prod-100"
    p1.name = "Smart Watch"
    p1.category = "Electronics"
    p1.description = "Feature rich smartwatch."
    
    p2 = MagicMock()
    p2.id = "prod-200"
    p2.name = "Yoga Mat"
    p2.category = "Sports"
    p2.description = None
    
    p3 = MagicMock()
    p3.id = None # Should be skipped
    p3.name = "Invalid Product"
    p3.category = "N/A"
    p3.description = "Missing ID"
    
    mock_db.query.return_value.all.return_value = [p1, p2, p3]
    
    # Mock ProductEmbedder to avoid loading real model
    mock_embedder_instance = MagicMock()
    mock_embedder_instance.get_embedding.side_effect = lambda x: [0.5] * 384
    
    with patch("app.ml.indexer.ProductEmbedder", return_value=mock_embedder_instance):
        results = await generate_catalog_embeddings(mock_db)
        
        # Verify database was queried
        mock_db.query.assert_called_once()
        
        # Verify response structure and size (invalid product should be skipped)
        assert isinstance(results, list)
        assert len(results) == 2
        
        # Verify mapping of product IDs to their corresponding vector arrays
        assert "prod-100" in results[0]
        assert results[0]["prod-100"] == [0.5] * 384
        
        assert "prod-200" in results[1]
        assert results[1]["prod-200"] == [0.5] * 384
