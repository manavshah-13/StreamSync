import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.workers.fairness_worker import run_fairness_scan
from models.schema import PricingHistory

@pytest.mark.asyncio
async def test_run_fairness_scan_no_history():
    # Test when there are no pricing history records
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_db.execute.return_value = mock_result
    mock_result.scalars.return_value.all.return_value = []
    
    result = await run_fairness_scan(mock_db)
    assert result["status"] == "success"
    assert result["scanned_products"] == 0
    assert result["anomalies_detected"] == 0

@pytest.mark.asyncio
async def test_run_fairness_scan_with_history_compliant():
    # Test when there are history rows but they don't indicate surge demand/velocity
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_db.execute.return_value = mock_result
    
    row1 = PricingHistory(
        product_id="prod-1",
        old_price=100.0,
        new_price=101.0,
        change_reason="Small random fluctuation"
    )
    
    mock_result.scalars.return_value.all.return_value = [row1]
    
    result = await run_fairness_scan(mock_db)
    assert result["status"] == "success"
    assert result["scanned_products"] == 1
    assert result["anomalies_detected"] == 0

@pytest.mark.asyncio
async def test_run_fairness_scan_with_history_biased():
    # Test when there is a history row indicating high demand/surge
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_db.execute.return_value = mock_result
    
    row1 = PricingHistory(
        product_id="prod-bias",
        old_price=100.0,
        new_price=150.0,
        change_reason="High demand pricing update"
    )
    
    mock_result.scalars.return_value.all.return_value = [row1]
    
    # We patch FairnessLog instantiation and verify it gets added to the session
    with patch("models.schema.FairnessLog") as mock_fairness_log:
        result = await run_fairness_scan(mock_db)
        
        assert result["status"] == "success"
        assert result["scanned_products"] == 1
        assert result["anomalies_detected"] == 1
        
        # Verify it added a FairnessLog to db session and committed
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
