from typing import Optional

def apply_shock_absorption(current_price: float, target_price: float, max_delta_pct: float = 0.25) -> float:
    """
    Stabilizes target_price based on current_price and allowable max_delta_pct.
    Clamps the target_price if it deviates more than max_delta_pct up or down from current_price.
    """
    if current_price <= 0:
        return target_price

    max_increase = current_price * (1.0 + max_delta_pct)
    max_decrease = current_price * (1.0 - max_delta_pct)

    if target_price > max_increase:
        target_price = max_increase
    elif target_price < max_decrease:
        target_price = max_decrease

    return round(target_price, 2)

def calculate_dynamic_sku_price(
    base_price: float,
    demand_velocity: int,
    stock_count: int,
    is_trending: bool,
    current_price: Optional[float] = None
) -> float:
    """
    Executes the dynamic pricing engine formula:
        Price Score = Demand Velocity Factor * Inventory Factor * Trend Factor
        Target Price = Base Price * Price Score

    Guardrails enforce that the price never drops below 70% (floor) 
    or exceeds 150% (ceiling) of the original base price.
    
    If current_price is provided, applies shock absorption to clamp price shifts
    within 25% of the current price.

    Returns the target price rounded to 2 decimal places.
    """
    if base_price <= 0:
        return 0.0

    # 1. Demand Velocity Factor (caps structural growth at 1.5x for demand_velocity >= 50)
    demand_velocity_factor = 1.0 + (min(demand_velocity, 50) / 100.0)

    # 2. Inventory Factor
    if stock_count < 10:
        inventory_factor = 1.3
    elif stock_count > 200:
        inventory_factor = 0.9
    else:
        inventory_factor = 1.0

    # 3. Trend Factor
    trend_factor = 1.05 if is_trending else 1.0

    # Calculate final price multiplier
    price_score = demand_velocity_factor * inventory_factor * trend_factor

    # Compute target price before business guardrails
    target_price = base_price * price_score

    # Apply strict business guardrails (floor = 70% of base, ceiling = 150% of base)
    floor = base_price * 0.7
    ceiling = base_price * 1.5

    if target_price < floor:
        target_price = floor
    elif target_price > ceiling:
        target_price = ceiling

    # If current_price is provided, apply shock absorption price smoothing
    if current_price is not None:
        target_price = apply_shock_absorption(current_price, target_price)

    return round(target_price, 2)
