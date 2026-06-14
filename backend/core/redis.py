import os
from dotenv import load_dotenv
import redis.asyncio as aioredis
import fakeredis.aioredis
from db.redis_client import fake_server
from typing import AsyncGenerator

# Load environment variables
load_dotenv()

class RedisService:
    def __init__(self) -> None:
        # Read REDIS_URL from the environment, with local fallback
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        self.pool: aioredis.ConnectionPool | None = None

    async def init_pool(self) -> None:
        """
        Initialize the async Redis connection pool.
        Expose this startup event handler to be mounted by the FastAPI app context.
        """
        if not self.pool:
            self.pool = aioredis.ConnectionPool.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=50  # Optimized max connections
            )
            print(f"[REDIS] Connection pool initialized at {self.redis_url}")

    async def close_pool(self) -> None:
        """
        Dismantle the async Redis connection pool.
        Expose this shutdown event handler to be cleaned up by the FastAPI app context.
        """
        if self.pool:
            await self.pool.disconnect()
            self.pool = None
            print("[REDIS] Connection pool shut down successfully.")

    def get_client(self) -> aioredis.Redis:
        """
        Retrieve an active Redis client. If the pool is not initialized,
        falls back to a mock FakeRedis instance for local/test environments.
        """
        if not self.pool:
            # Fallback to FakeRedis for backward compatibility in local dev/testing
            return fakeredis.aioredis.FakeRedis(server=fake_server, decode_responses=True)
        return aioredis.Redis(connection_pool=self.pool)

# Singleton service instance
redis_service = RedisService()

# Dependency function for FastAPI routes
async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    async with redis_service.get_client() as client:
        yield client
