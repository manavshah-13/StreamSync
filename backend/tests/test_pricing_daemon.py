import pytest
import fakeredis.aioredis
from unittest.mock import AsyncMock, MagicMock, patch
from db.redis_client import fake_server
import sys, os

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schema import Product
from workers.pricing_daemon import run_pricing_sweep

@pytest.mark.asyncio
async def test_pricing_daemon_sweep_mocked():
    """
    Test dynamic pricing daemon sweep orchestration with mocked database:
    1. Mock the async_session_maker to yield a mock DB session.
    2. Setup mock product.
    3. Setup FakeRedis and mock stream events.
    4. Execute run_pricing_sweep and verify that the products are evaluated.
    """
    # 1. Setup mock product
    mock_product = Product(
        id="daemon-test-sku",
        name="Daemon Test Headset",
        category="Electronics",
        base_price=200.0,
        current_price=200.0,
        rating=4.5,
        review_count=100,
        demand_velocity=10,
        brand="Sony",
        description="Test headset",
        specs={"stock_count": 8, "is_trending": True}  # Stock < 10 (1.3x), Trending (1.05x)
    )

    # 2. Setup mock DB execute result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_product]

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    mock_db.add = MagicMock()

    # Mock async context manager for session maker
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__.return_value = mock_db

    # 3. Setup FakeRedis and seed mock events
    client = fakeredis.aioredis.FakeRedis(server=fake_server, decode_responses=True)
    await client.delete("stream:user_events")

    # Add 2 events to get a velocity of 2
    await client.xadd("stream:user_events", {"user_id": "u1", "session_id": "s1", "event_type": "view", "sku": "daemon-test-sku"})
    await client.xadd("stream:user_events", {"user_id": "u2", "session_id": "s2", "event_type": "view", "sku": "daemon-test-sku"})

    # 4. Patch async_session_maker and execute the pricing daemon sweep
    with patch("workers.pricing_daemon.async_session_maker", mock_session_maker):
        await run_pricing_sweep(redis_client=client)

    # Assertions
    # Verify product current_price was updated (calculated: 200 * (1.02 * 1.3 * 1.05) = 278.46, clamped to 250.0 by shock absorption)
    assert mock_product.current_price == 250.0

    # Verify that db.add was called to log the PricingHistory entry
    assert mock_db.add.called
    added_obj = mock_db.add.call_args[0][0]
    from models.schema import PricingHistory
    assert isinstance(added_obj, PricingHistory)
    assert added_obj.product_id == "daemon-test-sku"
    assert added_obj.old_price == 200.0
    assert added_obj.new_price == 250.0
    assert "increased" in added_obj.change_reason

    # Verify transaction commit was triggered
    assert mock_db.commit.called

    await client.delete("stream:user_events")
    await client.aclose()
