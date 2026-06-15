import sys
import os
from unittest.mock import MagicMock, patch

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.compliance.fairness import FairnessAuditor, analyze_pricing_parity

def test_analyze_pricing_parity_uniform():
    segment_prices = {
        "Age 18-25": 100.0,
        "Age 45+": 100.0,
        "Premium Members": 100.0
    }
    result = analyze_pricing_parity("prod-1", segment_prices)
    assert result["fairness_score"] == 1.0
    assert result["variance_score"] == 0.0
    assert result["bias_detected"] is False

def test_analyze_pricing_parity_low_variance():
    # 5% price difference (105 vs 100) -> 5% spread ratio
    segment_prices = {
        "Age 18-25": 100.0,
        "Age 45+": 105.0
    }
    result = analyze_pricing_parity("prod-1", segment_prices, threshold=0.15)
    assert result["fairness_score"] == 0.95
    assert result["bias_detected"] is False

def test_analyze_pricing_parity_high_variance():
    # 20% price difference (120 vs 100) -> 20% spread ratio
    segment_prices = {
        "Age 18-25": 100.0,
        "Age 45+": 120.0
    }
    result = analyze_pricing_parity("prod-1", segment_prices, threshold=0.15)
    assert result["fairness_score"] == 0.8
    assert result["bias_detected"] is True

def test_audit_and_log():
    segment_prices = {
        "Age 18-25": 100.0,
        "Age 45+": 120.0
    }
    mock_db = MagicMock()
    auditor = FairnessAuditor(threshold=0.15)
    
    # We mock the schema model imports to avoid DB issues
    with patch("models.schema.FairnessLog") as mock_fairness_log_cls:
        result = auditor.audit_and_log(mock_db, "prod-123", segment_prices)
        
        # Verify result content
        assert result["bias_detected"] is True
        
        # Verify db interaction
        mock_fairness_log_cls.assert_called_once()
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
