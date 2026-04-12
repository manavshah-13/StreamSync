"""
RecommendationEngine — Item-Item Collaborative Filtering
=========================================================
Builds a co-click matrix in Redis sorted sets.
When session_id clicks prod-A, all products that session previously
clicked get their co-click score incremented with prod-A.

recs:{product_id}  → sorted set  {rec_product_id: co_click_score}
session:{sid}:clicks → set of product IDs viewed this session (TTL 30 min)
"""
import random
import logging

logger = logging.getLogger(__name__)

MAX_RECS_STORED = 20       # Top-N co-clicked products to remember per SKU
SESSION_TTL     = 1800     # 30 minutes
ATTRIBUTE_BOOST = 1.5      # Score boost for same-category recs


async def record_click(redis, product_id: str, session_id: str):
    """
    Called by stream_consumer on every VIEW / ADD_TO_CART event.
    Updates co-click counts between this product and all other products
    the session has already interacted with this session.
    """
    try:
        session_key = f"session:{session_id}:clicks"
        prev_clicks = await redis.smembers(session_key)

        # For each product the session previously clicked, bump co-click score
        for other_id in prev_clicks:
            if other_id != product_id:
                await redis.zincrby(f"co_clicks:{product_id}", 1, other_id)
                await redis.zincrby(f"co_clicks:{other_id}", 1, product_id)

        # Register this click in session history
        await redis.sadd(session_key, product_id)
        await redis.expire(session_key, SESSION_TTL)

        # Rebuild the fast-lookup recs sorted set for this product
        top = await redis.zrevrange(f"co_clicks:{product_id}", 0, MAX_RECS_STORED - 1, withscores=True)
        if top:
            mapping = {item: score for item, score in top}
            await redis.zadd(f"recs:{product_id}", mapping)
            await redis.expire(f"recs:{product_id}", SESSION_TTL * 4)

    except Exception as e:
        logger.warning(f"[RecommendationEngine] record_click error: {e}")


async def get_recommendations(redis, product_id: str, session_id: str = None, limit: int = 4) -> list:
    """
    Returns a list of recommended product IDs for product_id.
    Uses co-click sorted set, falls back to random sampling on cold-start.
    """
    try:
        recs = await redis.zrevrange(f"recs:{product_id}", 0, limit - 1)
        recs = list(recs)

        if len(recs) < limit:
            # Cold-start: fill remaining slots with random products
            all_products = await redis.smembers("products:all")
            excluded = set(recs) | {product_id}
            candidates = [p for p in all_products if p not in excluded]
            random.shuffle(candidates)
            recs += candidates[:limit - len(recs)]

        return recs[:limit]
    except Exception as e:
        logger.warning(f"[RecommendationEngine] get_recommendations error: {e}")
        return []
