import pytest
from models.schema import Product
from sqlalchemy import select

@pytest.mark.asyncio
async def test_conftest_fixtures(async_db_session, mock_redis):
    # 1. Test mock Redis client operations
    await mock_redis.set("test_key", "test_value")
    val = await mock_redis.get("test_key")
    assert val == "test_value"
    
    # 2. Test DB transactional session operations
    p = Product(
        id="fixture-test-sku",
        name="Fixture Test Product",
        category="Test",
        base_price=9.99,
        current_price=9.99
    )
    async_db_session.add(p)
    await async_db_session.commit()
    
    # Query database to assert insertion succeeded
    result = await async_db_session.execute(select(Product).where(Product.id == "fixture-test-sku"))
    fetched = result.scalars().first()
    assert fetched is not None
    assert fetched.name == "Fixture Test Product"
