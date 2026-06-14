import pytest
from httpx import AsyncClient, ASGITransport
import sys, os
from unittest.mock import MagicMock

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db.database import get_db
from models.schema import Product

@pytest.mark.asyncio
async def test_get_product_detail_api():
    """
    Test GET /api/v1/products/{id} and GET /api/products/{id}:
    - Verifies response payload keys.
    - Asserts correctness of original_price, current_price, and price_change_percentage.
    """
    mock_product = Product(
        id="api-test-sku",
        name="API Test Laptop",
        category="Computers",
        base_price=1000.0,
        current_price=1100.0,  # 10.0% increase
        rating=4.8,
        review_count=50,
        brand="Apple",
        specs={"stock_count": 100}
    )

    # Mock DB query
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_product
    mock_db = MagicMock()
    mock_db.query.return_value = mock_query

    def override_get_db():
        try:
            yield mock_db
        finally:
            pass

    # Apply FastAPI dependency override
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test standard route
        res = await ac.get("/api/products/api-test-sku")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "api-test-sku"
        assert data["original_price"] == 1000.0
        assert data["current_price"] == 1100.0
        assert data["price_change_percentage"] == 10.0

        # Test v1 prefixed route
        res_v1 = await ac.get("/api/v1/products/api-test-sku")
        assert res_v1.status_code == 200
        data_v1 = res_v1.json()
        assert data_v1["id"] == "api-test-sku"
        assert data_v1["original_price"] == 1000.0
        assert data_v1["current_price"] == 1100.0
        assert data_v1["price_change_percentage"] == 10.0

    # Clear dependency overrides
    app.dependency_overrides.clear()
