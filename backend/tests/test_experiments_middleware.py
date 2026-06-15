import sys
import os
from unittest.mock import MagicMock, patch

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.experiments.middleware import get_experiment_variant
from models.schema import Experiment

@pytest.mark.asyncio
async def test_get_experiment_variant_no_headers():
    # If no headers are provided, it should return 'A'
    result = await get_experiment_variant(x_session_id=None, x_user_id=None, db=MagicMock())
    assert result == "A"

@pytest.mark.asyncio
async def test_get_experiment_variant_no_active_experiment():
    # If headers are provided but no active experiment is found, return 'A'
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    result = await get_experiment_variant(x_session_id="session_123", x_user_id=None, db=mock_db)
    assert result == "A"

@pytest.mark.asyncio
async def test_get_experiment_variant_with_active_experiment():
    # If headers are provided and active experiment is found, calculate A/B using router logic
    mock_db = MagicMock()
    mock_exp = Experiment(name="test_experiment", is_active=True)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_exp
    
    # We patch assign_experiment_variant to return a specific value and verify it is returned
    with patch("app.experiments.middleware.assign_experiment_variant") as mock_assign:
        mock_assign.return_value = "B"
        result = await get_experiment_variant(x_session_id=None, x_user_id="user_123", db=mock_db)
        
        assert result == "B"
        mock_assign.assert_called_once_with("user_123", "test_experiment")

@pytest.mark.asyncio
async def test_get_experiment_variant_db_error_graceful_fallback():
    # If DB queries fail, default gracefully to 'A'
    mock_db = MagicMock()
    mock_db.query.side_effect = Exception("DB connection timeout")
    
    result = await get_experiment_variant(x_session_id="session_123", x_user_id="user_123", db=mock_db)
    assert result == "A"
