import pytest
import sys, os

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pricing.explainer import generate_price_change_reason

def test_generate_price_change_reason():
    """
    Unit tests for the generate_price_change_reason logic.
    """
    # 1. Initial price established
    assert generate_price_change_reason(0.0, 100.0, 10, 50) == "Initial price established."

    # 2. Stable price
    assert generate_price_change_reason(100.0, 100.0, 10, 50) == "Price remained stable."

    # 3. Price increased and low stock (< 10)
    # increase of 50.0% (100 -> 150)
    reason = generate_price_change_reason(old_price=100.0, new_price=150.0, velocity=45, stock_count=8)
    assert "increased by 50.0%" in reason
    assert "high demand velocity of 45 views" in reason
    assert "low inventory levels (8 items left)" in reason

    # 4. Price increased with normal stock but high velocity (> 30)
    # increase of 25.0% (100 -> 125)
    reason_high_vel = generate_price_change_reason(old_price=100.0, new_price=125.0, velocity=35, stock_count=50)
    assert "increased by 25.0%" in reason_high_vel
    assert "strong market demand velocity of 35 views" in reason_high_vel

    # 5. Price adjusted down with low velocity (< 5)
    # decrease of 10.0% (100 -> 90)
    reason_low_vel = generate_price_change_reason(old_price=100.0, new_price=90.0, velocity=3, stock_count=50)
    assert "adjusted down by 10.0%" in reason_low_vel
    assert "stimulate sales due to low demand velocity within the last tracking window" in reason_low_vel

    # 6. Price adjusted down with high inventory (> 200)
    # decrease of 10.0% (100 -> 90)
    reason_high_stock = generate_price_change_reason(old_price=100.0, new_price=90.0, velocity=15, stock_count=250)
    assert "adjusted down by 10.0%" in reason_high_stock
    assert "stimulate sales due to high inventory levels (250 items in stock)" in reason_high_stock
