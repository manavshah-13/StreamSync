import pytest
import time
import fakeredis.aioredis
from db.redis_client import fake_server
import sys, os

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.velocity import DemandVelocityAnalyzer

@pytest.mark.asyncio
async def test_demand_velocity_calculation():
    """
    Verify that DemandVelocityAnalyzer correctly filters stream events 
    based on the specified sliding window duration (seconds) and target SKU.
    """
    # Create an isolated FakeRedis client sharing the memory space
    client = fakeredis.aioredis.FakeRedis(server=fake_server, decode_responses=True)
    analyzer = DemandVelocityAnalyzer(redis_client=client)

    stream_name = "stream:user_events"

    # Reset any existing test stream data
    await client.delete(stream_name)

    # Calculate exact millisecond timestamps
    now_ms = int(time.time() * 1000)
    out_of_window_ms = now_ms - 45000  # 45 seconds ago (out of 30s window)
    in_window_ms = now_ms - 15000      # 15 seconds ago (inside 30s window)

    # 1. Add historical events outside the sliding window
    await client.xadd(stream_name, {"sku": "SKU-A", "user_id": "user1"}, id=f"{out_of_window_ms}-0")
    await client.xadd(stream_name, {"sku": "SKU-A", "user_id": "user2"}, id=f"{out_of_window_ms}-1")

    # 2. Add current events inside the sliding window
    await client.xadd(stream_name, {"sku": "SKU-A", "user_id": "user3"}, id=f"{in_window_ms}-0")
    await client.xadd(stream_name, {"sku": "SKU-A", "user_id": "user4"}, id=f"{in_window_ms}-1")
    await client.xadd(stream_name, {"sku": "SKU-B", "user_id": "user5"}, id=f"{in_window_ms}-2") # Diff SKU

    # 3. Assert counts for SKU-A (should be 2: only those in the last 30s window)
    velocity_a = await analyzer.get_sku_velocity(sku="SKU-A", window_seconds=30)
    assert velocity_a == 2, f"Expected 2 matches for SKU-A in window, got {velocity_a}"

    # 4. Assert counts for SKU-B (should be 1: only 1 event inside window)
    velocity_b = await analyzer.get_sku_velocity(sku="SKU-B", window_seconds=30)
    assert velocity_b == 1, f"Expected 1 match for SKU-B in window, got {velocity_b}"

    # 5. Clean up stream data
    await client.delete(stream_name)
    await client.aclose()
