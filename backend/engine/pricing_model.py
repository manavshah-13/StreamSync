import random
from engine.guardrails import apply_guardrails

# In a real environment, this would be:
# import xgboost as xgb
# model = xgb.Booster()
# model.load_model('models/pricing_v1.pkl')

def calculate_new_price(base_price: float, current_price: float, velocity: int) -> float:
    """
    Simulates an XGBoost prediction using demand velocity.
    - Velocity > 75: High Demand (Increase price)
    - Velocity < 30: Low Demand (Decrease price)
    - Otherwise minor noise adjustments
    """
    if velocity > 75:
        # Increase price by 2% to 8%
        spike = random.uniform(0.02, 0.08)
        proposed = current_price * (1 + spike)
    elif velocity < 30:
        # Decrease price by 1% to 5%
        drop = random.uniform(0.01, 0.05)
        proposed = current_price * (1 - drop)
    else:
        # Maintenance mode - minor fluctuations
        noise = random.uniform(-0.01, 0.01)
        proposed = current_price * (1 + noise)
        
    # Pipe proposed price through organizational guardrails
    final_price = apply_guardrails(base_price, proposed)
    return final_price
