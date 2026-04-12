"""
Upgraded Pricing Model — Demand-Elasticity with Confidence Score
================================================================
Replaces the pure-random noise model with a demand-elasticity approach:
  - High velocity (>75): price increases proportional to demand intensity
  - Low velocity (<30):  price softens to stimulate demand
  - Mid-range:           micro-adjustments with gentle regression-to-mean

Also returns a confidence_score (0.0–1.0) indicating how certain the
model is in its recommendation.
"""
import math
import random
from engine.guardrails import apply_guardrails


def calculate_new_price(
    base_price: float,
    current_price: float,
    velocity: int,
    click_rate: int = 0,
) -> float:
    """
    Demand-elasticity pricing model.

    Parameters
    ----------
    base_price    : original product base price
    current_price : current live price
    velocity      : demand velocity 0–100
    click_rate    : raw click count in rolling window (from velocity_raw)
    """
    # Normalised velocity 0.0–1.0
    v = velocity / 100.0

    # ── Elasticity factor  ─────────────────────────────────────────────────────
    # High-demand → inelastic (can charge more); low-demand → elastic (must discount)
    elasticity = 1.0 - (0.4 * v)          # range [0.60, 1.00]

    # ── Click-rate amplifier (bonus pressure when many real clicks) ────────────
    click_amplifier = min(1.0 + click_rate * 0.002, 1.15)  # caps at +15%

    if velocity > 75:
        # Demand spike: raise price proportional to intensity above threshold
        intensity = (velocity - 75) / 25.0                 # 0.0–1.0
        spike_pct = 0.02 + intensity * 0.06                 # 2%–8%
        proposed  = current_price * (1 + spike_pct * click_amplifier)

    elif velocity < 30:
        # Demand slump: pull price down, but use elasticity to moderate
        slump_pct = 0.01 + (30 - velocity) / 30.0 * 0.04  # 1%–5%
        proposed  = current_price * (1 - slump_pct * elasticity)

    else:
        # Equilibrium: gentle regression toward base price + tiny noise
        mean_reversion = (base_price - current_price) * 0.03
        noise          = random.uniform(-0.005, 0.005) * current_price
        proposed       = current_price + mean_reversion + noise

    # Guardrails ensure price stays within org-defined bounds
    return apply_guardrails(base_price, proposed)


def calculate_confidence(velocity: int, click_rate: int = 0) -> float:
    """
    Returns a confidence score 0.0–1.0 for the pricing decision.
    Higher velocity + higher click rate = higher confidence.
    """
    v_conf  = velocity / 100.0
    c_conf  = min(click_rate / 50.0, 1.0)
    return round(0.6 * v_conf + 0.4 * c_conf, 3)
