import redis.asyncio as aioredis
from typing import Optional, List
from core.redis import redis_service

# Event-to-score mappings for category affinity tracking
AFFINITY_SCORES = {
    "view": 1,
    "click": 1,
    "cart_add": 3,
    "wishlist": 2,
    "checkout": 4,
    "purchase": 5
}

async def update_user_affinity(
    user_id: str,
    event_type: str,
    category_id: str,
    redis_client: Optional[aioredis.Redis] = None
) -> float:
    """
    Increments a user's affinity score for a given product category in a Redis Sorted Set (ZSET).
    Affinity score weighting: view=1, cart_add=3, purchase=5.
    Optimized with pipeline to keep read/write round-trips low.
    """
    client = redis_client if redis_client else redis_service.get_client()
    key = f"user:affinity:{user_id}"

    # Extract score or default to 1 (e.g. view)
    score = AFFINITY_SCORES.get(event_type.lower(), 1)

    async with client.pipeline(transaction=True) as pipe:
        pipe.zincrby(key, score, category_id)
        # Keep profiles active for 30 days of inactivity
        pipe.expire(key, 30 * 24 * 60 * 60)
        results = await pipe.execute()

    return float(results[0])

async def record_session_interaction(
    session_id: str,
    sku: str,
    redis_client: Optional[aioredis.Redis] = None
) -> None:
    """
    Updates the rolling sequence of the last 5 unique product SKUs a user interacted with.
    Optimizes using a pipeline to combine LREM (remove previous), LPUSH (insert front), 
    and LTRIM (keep up to 5 elements) into a single network round-trip.
    """
    client = redis_client if redis_client else redis_service.get_client()
    key = f"session:history:{session_id}"

    async with client.pipeline(transaction=True) as pipe:
        # Remove any existing instance of the SKU to guarantee uniqueness
        pipe.lrem(key, 0, sku)
        # Push the new interaction to the head of the list
        pipe.lpush(key, sku)
        # Trim list to keep only the 5 most recent unique SKUs
        pipe.ltrim(key, 0, 4)
        # Session TTL set to 2 hours of inactivity
        pipe.expire(key, 2 * 60 * 60)
        await pipe.execute()

async def get_active_session_history(
    session_id: str,
    redis_client: Optional[aioredis.Redis] = None
) -> List[str]:
    """
    Fetches the rolling sequence of the last 5 unique product SKUs the user interacted with.
    """
    client = redis_client if redis_client else redis_service.get_client()
    key = f"session:history:{session_id}"
    return await client.lrange(key, 0, 4)
