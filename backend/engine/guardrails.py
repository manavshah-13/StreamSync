def apply_guardrails(base_price: float, proposed_price: float) -> float:
    """
    Ensures the proposed dynamic price does not drop below a 15% margin
    or exceed a 50% ceiling compared to the underlying base_price.
    """
    min_price = base_price * 0.85
    max_price = base_price * 1.50
    
    if proposed_price < min_price:
        return round(min_price, 2)
    elif proposed_price > max_price:
        return round(max_price, 2)
        
    return round(proposed_price, 2)
