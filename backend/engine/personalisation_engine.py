"""
PersonalisationEngine — Session-Based Interest Vectors
=======================================================
Maintains a lightweight interest profile per session.
Each category dimension accumulates a weight based on interaction type:
  VIEW         → +1.0
  ADD_TO_CART  → +3.0

session:{session_id}:profile → Redis hash  {category: cumulative_weight}
TTL: 5 minutes (resets when session goes idle)
"""
import logging

logger = logging.getLogger(__name__)

CATEGORY_DIMS = ['Electronics', 'Apparel', 'Home', 'Sports', 'Beauty', 'Toys']
EVENT_WEIGHTS = {
    'VIEW':        1.0,
    'ADD_TO_CART': 3.0,
    'PURCHASE':    5.0,
}
PROFILE_TTL = 300  # 5 minutes


async def update_session(redis, session_id: str, product_id: str, event_type: str):
    """
    Called on every ingestion event.
    Updates the session's category interest vector.
    """
    try:
        prod = await redis.hgetall(f"product:{product_id}")
        if not prod:
            return

        category = prod.get("category", "Electronics")
        weight = EVENT_WEIGHTS.get(event_type, 1.0)

        profile_key = f"session:{session_id}:profile"
        await redis.hincrbyfloat(profile_key, category, weight)
        await redis.expire(profile_key, PROFILE_TTL)

    except Exception as e:
        logger.warning(f"[PersonalisationEngine] update_session error: {e}")


async def get_session_profile(redis, session_id: str) -> dict:
    """Returns {category: weight} dict for the given session."""
    try:
        profile_key = f"session:{session_id}:profile"
        raw = await redis.hgetall(profile_key)
        return {k: float(v) for k, v in raw.items()} if raw else {}
    except Exception as e:
        logger.warning(f"[PersonalisationEngine] get_session_profile error: {e}")
        return {}


async def rerank_by_session(redis, session_id: str, product_ids: list) -> list:
    """
    Re-ranks a list of product IDs according to the session's interest profile.
    Products matching the session's top categories float to the top.
    """
    try:
        profile = await get_session_profile(redis, session_id)
        if not profile:
            return product_ids

        scored = []
        for pid in product_ids:
            prod = await redis.hgetall(f"product:{pid}")
            category = prod.get("category", "") if prod else ""
            boost = profile.get(category, 0.0)
            scored.append((pid, boost))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in scored]

    except Exception as e:
        logger.warning(f"[PersonalisationEngine] rerank_by_session error: {e}")
        return product_ids
