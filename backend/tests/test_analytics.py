import pytest
from httpx import AsyncClient, ASGITransport
import sys, os
from unittest.mock import AsyncMock, MagicMock

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from core.redis import get_redis

@pytest.mark.asyncio
async def test_analytics_overview_route():
    # Mock Redis dependency
    mock_redis_client = MagicMock()
    
    # Mock xlen and llen calls to be async
    async def mock_xlen(*args, **kwargs):
        return 50
    async def mock_llen(*args, **kwargs):
        return 12
        
    mock_redis_client.xlen = mock_xlen
    mock_redis_client.llen = mock_llen

    def override_redis():
        yield mock_redis_client

    app.dependency_overrides[get_redis] = override_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/analytics/overview")
        assert res.status_code == 200
        data = res.json()
        assert "p99Latency" in data
        assert "activeSkus" in data
        assert "repricingRate" in data
        assert "activeSessions" in data
        assert "cacheHitRate" in data
        assert "streamLag" in data
        assert "current_tick" in data
        
        tick = data["current_tick"]
        assert "time" in tick
        assert "variableFactor" in tick
        assert "velocity" in tick
        assert isinstance(tick["variableFactor"], float)
        assert isinstance(tick["velocity"], int)

    app.dependency_overrides.clear()
