import fakeredis
import fakeredis.aioredis

# Shared server instance so all FakeRedis clients in this process share data
fake_server = fakeredis.FakeServer()

async def get_redis():
    """Dependency for FastAPI route injection"""
    client = fakeredis.aioredis.FakeRedis(server=fake_server, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()

def get_redis_async():
    """Async connection for background workers"""
    return fakeredis.aioredis.FakeRedis(server=fake_server, decode_responses=True)

def get_redis_sync():
    """Synchronous connection for background workers & middleware"""
    return fakeredis.FakeRedis(server=fake_server, decode_responses=True)
