def generate_price_change_reason(old_price: float, new_price: float, velocity: int, stock_count: int) -> str:
    """
    Generates a premium, human-readable business explanation for a price change.
    Evaluates the factors of demand velocity and inventory levels that contributed to the price delta.
    """
    if old_price <= 0:
        return "Initial price established."

    diff = new_price - old_price
    if abs(diff) < 0.005:
        return "Price remained stable."

    pct = (diff / old_price) * 100.0
    pct_str = f"{abs(pct):.1f}%"

    if diff > 0:
        # Price increased
        if stock_count < 10:
            return f"Price increased by {pct_str} due to a high demand velocity of {velocity} views and low inventory levels ({stock_count} items left)."
        elif velocity > 30:
            return f"Price increased by {pct_str} due to strong market demand velocity of {velocity} views within the tracking window."
        else:
            return f"Price adjusted up by {pct_str} reflecting standard dynamic scaling parameters."
    else:
        # Price decreased
        if stock_count > 200:
            return f"Price adjusted down by {pct_str} to stimulate sales due to high inventory levels ({stock_count} items in stock)."
        elif velocity < 5:
            return f"Price adjusted down by {pct_str} to stimulate sales due to low demand velocity within the last tracking window."
        else:
            return f"Price adjusted down by {pct_str} reflecting standard dynamic scaling parameters."
