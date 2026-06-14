import pytest
import asyncio
import fakeredis.aioredis
from db.redis_client import fake_server
import sys, os

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.analytics_worker import run_worker

@pytest.mark.asyncio
async def test_analytics_worker_event_processing():
    """
    Integration/Unit test for the background analytics worker:
    1. Seed a mock product and product category.
    2. Write a mock event tracking payload into the stream.
    3. Run the worker loop in the background.
    4. Assert that the event was processed, ZSET affinity scores updated, 
       and session list history recorded correctly.
    """
    client = fakeredis.aioredis.FakeRedis(server=fake_server, decode_responses=True)

    stream_name = "stream:user_events"
    user_id = "test-worker-user"
    session_id = "test-worker-session"

    # Reset keys from previous tests
    await client.delete(stream_name)
    await client.delete(f"user:affinity:{user_id}")
    await client.delete(f"session:history:{session_id}")

    # 1. Seed a mock product's category
    await client.hset("product:prod-toy-1", mapping={"category": "Toys"})

    # 2. Add an event to 'stream:user_events'
    event_payload = {
        "user_id": user_id,
        "session_id": session_id,
        "event_type": "purchase",  # Weighting: 5
        "sku": "prod-toy-1"
    }
    await client.xadd(stream_name, event_payload)

    # 3. Start the worker loop in a background asyncio task
    worker_task = asyncio.create_task(run_worker(redis_client=client))

    # 4. Wait a short period (1.5 seconds) for processing to complete
    await asyncio.sleep(1.5)

    # 5. Gracefully cancel the background task
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass

    # 6. Verify that the user affinity score for 'Toys' was set to 5.0
    affinity_score = await client.zscore(f"user:affinity:{user_id}", "Toys")
    assert affinity_score == 5.0, f"Expected user affinity score of 5.0 for category 'Toys', got {affinity_score}"

    # 7. Verify that the session history was updated with the product SKU
    history = await client.lrange(f"session:history:{session_id}", 0, -1)
    assert history == ["prod-toy-1"], f"Expected session history to contain ['prod-toy-1'], got {history}"

    # 8. Clean up test keys
    await client.delete(stream_name)
    await client.delete("product:prod-toy-1")
    await client.delete(f"user:affinity:{user_id}")
    await client.delete(f"session:history:{session_id}")
    await client.aclose()
