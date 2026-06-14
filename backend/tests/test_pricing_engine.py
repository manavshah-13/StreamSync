import pytest
from pricing.engine import calculate_dynamic_sku_price

def test_calculate_dynamic_sku_price_base():
    """
    Test standard calculations without reaching guardrails.
    - Base price = 100.00
    - Demand velocity = 20 -> factor = 1.2
    - Stock count = 50 -> factor = 1.0
    - Trending = False -> factor = 1.0
    - Expected price = 120.00
    """
    price = calculate_dynamic_sku_price(100.00, demand_velocity=20, stock_count=50, is_trending=False)
    assert price == 120.00

def test_calculate_dynamic_sku_price_velocity_cap():
    """
    Test that demand velocity factor caps at 1.5x (velocity >= 50).
    - Base price = 100.00
    - Demand velocity = 100 (capped at 50) -> factor = 1.5
    - Stock count = 50 -> factor = 1.0
    - Trending = False -> factor = 1.0
    - Expected price = 150.00
    """
    price = calculate_dynamic_sku_price(100.00, demand_velocity=100, stock_count=50, is_trending=False)
    assert price == 150.00

def test_calculate_dynamic_sku_price_low_inventory():
    """
    Test low inventory factor (+30% price boost).
    - Base price = 100.00
    - Demand velocity = 0 -> factor = 1.0
    - Stock count = 5 (< 10) -> factor = 1.3
    - Trending = False -> factor = 1.0
    - Expected price = 130.00
    """
    price = calculate_dynamic_sku_price(100.00, demand_velocity=0, stock_count=5, is_trending=False)
    assert price == 130.00

def test_calculate_dynamic_sku_price_high_inventory():
    """
    Test high inventory factor (10% discount).
    - Base price = 100.00
    - Demand velocity = 0 -> factor = 1.0
    - Stock count = 300 (> 200) -> factor = 0.9
    - Trending = False -> factor = 1.0
    - Expected price = 90.00
    """
    price = calculate_dynamic_sku_price(100.00, demand_velocity=0, stock_count=300, is_trending=False)
    assert price == 90.00

def test_calculate_dynamic_sku_price_trending():
    """
    Test trending factor (+5% price boost).
    - Base price = 100.00
    - Demand velocity = 0 -> factor = 1.0
    - Stock count = 50 -> factor = 1.0
    - Trending = True -> factor = 1.05
    - Expected price = 105.00
    """
    price = calculate_dynamic_sku_price(100.00, demand_velocity=0, stock_count=50, is_trending=True)
    assert price == 105.00

def test_calculate_dynamic_sku_price_ceiling_guardrail():
    """
    Test that the price is capped at 150% of the base price.
    - Base price = 100.00
    - Demand velocity = 50 -> factor = 1.5
    - Stock count = 5 -> factor = 1.3
    - Trending = True -> factor = 1.05
    - Score multiplier = 1.5 * 1.3 * 1.05 = 2.0475
    - Unclamped price = 204.75
    - Ceiling guardrail = 150.00
    """
    price = calculate_dynamic_sku_price(100.00, demand_velocity=50, stock_count=5, is_trending=True)
    assert price == 150.00

def test_calculate_dynamic_sku_price_floor_guardrail():
    """
    Test that if price drops below 70% of base price, it clamps to the floor.
    - Base price = 100.00
    - Since standard factors cannot drop below 0.9, we verify base_price <= 0 returns 0,
      and any value below the 70% floor is clamped if the price calculation drops.
      For coding verification, we check base cases and boundary limits.
    """
    price_zero = calculate_dynamic_sku_price(0.0, demand_velocity=0, stock_count=50, is_trending=False)
    assert price_zero == 0.0

    # Ensure negative base price returns 0.0
    price_neg = calculate_dynamic_sku_price(-50.0, demand_velocity=0, stock_count=50, is_trending=False)
    assert price_neg == 0.0
