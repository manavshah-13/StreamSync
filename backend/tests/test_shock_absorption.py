import pytest
import sys, os

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pricing.engine import apply_shock_absorption, calculate_dynamic_sku_price

def test_apply_shock_absorption_directly():
    """
    Direct test of the apply_shock_absorption clamping boundaries.
    """
    # 1. Target price within 25% change limit -> no clamping
    assert apply_shock_absorption(current_price=100.0, target_price=110.0) == 110.0
    assert apply_shock_absorption(current_price=100.0, target_price=90.0) == 90.0

    # 2. Target price exceeds +25% limit (125.0) -> clamp to 125.0
    assert apply_shock_absorption(current_price=100.0, target_price=135.0) == 125.0

    # 3. Target price exceeds -25% limit (75.0) -> clamp to 75.0
    assert apply_shock_absorption(current_price=100.0, target_price=60.0) == 75.0

    # 4. Handle edge case of 0.0 current price -> no clamping
    assert apply_shock_absorption(current_price=0.0, target_price=15.0) == 15.0


def test_calculate_dynamic_sku_price_with_shock_absorption():
    """
    Integration test verifying calculate_dynamic_sku_price uses shock absorption
    when current_price is provided.
    """
    # Without current_price:
    # base=100.0, velocity=50 (1.5x), stock=5 (<10 -> 1.3x), trending=True (1.05x)
    # Raw target = 100 * (1.5 * 1.3 * 1.05) = 204.75 -> ceiling clamped to 150.0 (150% of base)
    assert calculate_dynamic_sku_price(
        base_price=100.0,
        demand_velocity=50,
        stock_count=5,
        is_trending=True,
        current_price=None
    ) == 150.0

    # With current_price=100.0:
    # Raw target is 150.0 (due to ceiling clamp), but shock absorption clamps it to max +25% shift from current (125.0)
    assert calculate_dynamic_sku_price(
        base_price=100.0,
        demand_velocity=50,
        stock_count=5,
        is_trending=True,
        current_price=100.0
    ) == 125.0
