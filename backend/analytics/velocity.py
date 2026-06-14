import time
from typing import Optional
import redis.asyncio as aioredis
from core.redis import redis_service

class DemandVelocityAnalyzer:
    """
    DemandVelocityAnalyzer handles connection and range filtering queries 
    over the user event stream to calculate demand velocity (traffic/event rate).
    """
    def __init__(self, redis_client: Optional[aioredis.Redis] = None) -> None:
        self._redis = redis_client

    async def get_sku_velocity(self, sku: str, window_seconds: int = 30) -> int:
        """
        Calculates a product's interaction volume (velocity) within a sliding window.
        Queries the stream:user_events Redis stream using xrange with time boundaries.
        """
        # Determine which client to use: provided mock/test client or standard connection pool
        client = self._redis if self._redis else redis_service.get_client()

        # Convert current time and compute historical lower bound boundary in milliseconds
        current_time_ms = int(time.time() * 1000)
        lower_bound_ms = current_time_ms - (window_seconds * 1000)

        stream_name = "stream:user_events"

        try:
            # Query the stream with the lower bound boundary to target only the specified time block
            events = await client.xrange(
                name=stream_name,
                min=str(lower_bound_ms),
                max="+"
            )
        except Exception as e:
            # Handle cases where the stream does not exist yet (returns 0 velocity)
            print(f"[Velocity] Warning: Failed to query stream {stream_name} (might not exist yet): {e}")
            return 0

        # Filter the stream results to count matching interaction events for the target SKU
        count = 0
        for _, event_data in events:
            if event_data.get("sku") == sku:
                count += 1

        return count

async def get_sku_velocity(sku: str, window_seconds: int = 30) -> int:
    """
    Helper helper function to fetch SKU velocity using the default Redis client connection pool.
    """
    analyzer = DemandVelocityAnalyzer()
    return await analyzer.get_sku_velocity(sku=sku, window_seconds=window_seconds)
