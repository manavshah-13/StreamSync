import asyncio
import pytest
import pytest_asyncio
import fakeredis.aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from models.schema import Base

@pytest.fixture(scope="session")
def event_loop():
    """
    Creates an instance of the default event loop for the test session.
    Ensures async tests run cleanly in a single-session event loop.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def async_db_session():
    """
    Spins up a clean, transactional database session using an in-memory SQLite database.
    Automatically rolls back all transactions after each unit test completes
    to guarantee test isolation.
    """
    # Create an in-memory SQLite engine for the test session
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Connect and yield session within transaction
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        
        async_session = AsyncSession(
            bind=connection,
            expire_on_commit=False
        )
        
        yield async_session
        
        await transaction.rollback()
        
    await test_engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def mock_redis():
    """
    Provides a localized, mocked Redis client using fakeredis.
    Stubs out asyncio Redis operations (like streams and lists) for fast,
    deterministic parallel unit testing.
    """
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.aclose()
