import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch
import sys, os

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db.database import get_db
from models.schema import Product

@pytest.mark.asyncio
async def test_personalized_recommendations_personalization():
    """
    Test GET /api/v1/recommendations/personalized:
    - Mocks compute_active_session_vector to return a non-zero vector.
    - Mocks rank_products_by_similarity to return a product ID.
    - Asserts that personalized recommendations (vector_similarity) are returned.
    """
    mock_product = Product(
        id="personalized-sku",
        name="Personalized Shoes",
        category="Footwear",
        base_price=80.0,
        current_price=80.0,
        description="Premium running shoes"
    )
    
    # Mock DB queries
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = [mock_product]
    mock_db.query.return_value = mock_query
    
    def override_get_db():
        yield mock_db
        
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock compute_active_session_vector and rank_products_by_similarity
    with patch("app.api.v1.endpoints.recommendations.compute_active_session_vector") as mock_compute, \
         patch("app.api.v1.endpoints.recommendations.rank_products_by_similarity") as mock_rank:
         
        # Return a populated session vector
        mock_compute.return_value = [0.5] * 384
        # Return the recommended product ID
        mock_rank.return_value = ["personalized-sku"]
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.get("/api/v1/recommendations/personalized?session_id=session_123")
            assert res.status_code == 200
            data = res.json()
            assert data["recommender"] == "vector_similarity"
            assert len(data["products"]) == 1
            assert data["products"][0]["id"] == "personalized-sku"
            assert data["products"][0]["name"] == "Personalized Shoes"

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_personalized_recommendations_cold_start_fallback():
    """
    Test GET /api/v1/recommendations/personalized (cold-start fallback):
    - Mocks compute_active_session_vector to return an unpopulated/zero vector.
    - Mocks Redis category affinity to return nothing (empty).
    - Asserts that cold-start users are served global trending items.
    """
    mock_trending_product = Product(
        id="trending-sku",
        name="Trending Gadget",
        category="Electronics",
        base_price=200.0,
        current_price=200.0,
        demand_velocity=95,
        description="A hot trending device"
    )
    
    mock_db = MagicMock()
    mock_query = MagicMock()
    
    # For global trending fallback, it queries:
    # 1. db.query(Product).order_by(Product.demand_velocity.desc()).limit(5).all() -> [mock_trending_product]
    # 2. db.query(Product).filter(Product.id.in_(...)).all() -> [mock_trending_product]
    def mock_all():
        return [mock_trending_product]
        
    mock_query.order_by.return_value.limit.return_value.all.side_effect = mock_all
    mock_query.filter.return_value.all.side_effect = mock_all
    mock_db.query.return_value = mock_query
    
    def override_get_db():
        yield mock_db
        
    app.dependency_overrides[get_db] = override_get_db
    
    with patch("app.api.v1.endpoints.recommendations.compute_active_session_vector") as mock_compute, \
         patch("core.redis.redis_service.get_client") as mock_redis_client:
         
        mock_compute.return_value = [0.0] * 384
        
        # Mock Redis client to raise exception or return empty list for affinity
        mock_client = MagicMock()
        
        # Mocking an async method zrevrange
        async def mock_zrevrange(*args, **kwargs):
            return []
            
        mock_client.zrevrange = mock_zrevrange
        mock_redis_client.return_value = mock_client
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.get("/api/v1/recommendations/personalized?user_id=new_user_123")
            assert res.status_code == 200
            data = res.json()
            assert data["recommender"] == "global_trending"
            assert len(data["products"]) == 1
            assert data["products"][0]["id"] == "trending-sku"
            assert data["products"][0]["name"] == "Trending Gadget"

    app.dependency_overrides.clear()
