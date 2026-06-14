import pytest
import fakeredis.aioredis
from db.redis_client import fake_server
import sys, os

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.session_profiles import (
    update_user_affinity,
    record_session_interaction,
    get_active_session_history
)

@pytest.mark.asyncio
async def test_session_profiles_aggregator():
    """
    Test session profile analytics calculations:
    1. Verify category affinity increments dynamically per event weighting.
    2. Verify rolling SKU history contains only the last 5 unique product SKUs.
    """
    client = fakeredis.aioredis.FakeRedis(server=fake_server, decode_responses=True)

    # 1. Verify User Category Affinity (ZSET scores)
    user_id = "test-user-999"
    affinity_key = f"user:affinity:{user_id}"

    # Clean previous runs
    await client.delete(affinity_key)

    # Send a view (+1) to 'electronics'
    score_electronics = await update_user_affinity(user_id, "view", "electronics", redis_client=client)
    assert score_electronics == 1.0

    # Send a cart_add (+3) to 'electronics' (running sum: 4.0)
    score_electronics = await update_user_affinity(user_id, "cart_add", "electronics", redis_client=client)
    assert score_electronics == 4.0

    # Send a purchase (+5) to 'sports'
    score_sports = await update_user_affinity(user_id, "purchase", "sports", redis_client=client)
    assert score_sports == 5.0

    # Confirm directly via ZSCORE
    assert await client.zscore(affinity_key, "electronics") == 4.0
    assert await client.zscore(affinity_key, "sports") == 5.0

    # 2. Verify Session SKU History (unique rolling 5 item limit)
    session_id = "test-session-888"
    history_key = f"session:history:{session_id}"

    # Clean previous runs
    await client.delete(history_key)

    # Interact with a sequence of products
    await record_session_interaction(session_id, "prod-100", redis_client=client)
    await record_session_interaction(session_id, "prod-200", redis_client=client)
    await record_session_interaction(session_id, "prod-300", redis_client=client)
    # Re-interact with prod-100 (should move prod-100 to the front and keep it unique)
    await record_session_interaction(session_id, "prod-100", redis_client=client)
    await record_session_interaction(session_id, "prod-400", redis_client=client)
    await record_session_interaction(session_id, "prod-500", redis_client=client)
    # 6th unique product (should push the oldest unique SKU "prod-200" out of the rolling window)
    await record_session_interaction(session_id, "prod-600", redis_client=client)

    history = await get_active_session_history(session_id, redis_client=client)

    # Expected order (newest to oldest, capped at 5):
    # 1. prod-600 (newest)
    # 2. prod-500
    # 3. prod-400
    # 4. prod-100 (re-interacted, moved to front of history prior to 400/500/600)
    # 5. prod-300
    # (prod-200 is dropped because it became the oldest unique entry)
    assert history == ["prod-600", "prod-500", "prod-400", "prod-100", "prod-300"]

    # Clean up
    await client.delete(affinity_key)
    await client.delete(history_key)
    await client.aclose()
