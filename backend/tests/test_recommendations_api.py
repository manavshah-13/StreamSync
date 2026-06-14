import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from main import app
from db.database import get_db
from models.schema import Product

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()

def test_personalized_recommendations_vector_similarity():
    # 1. Mock session vector to be populated
    mock_vector = [0.1] * 384
    mock_ranked_ids = ["prod-sim-1", "prod-sim-2"]
    
    mock_prod_1 = Product(id="prod-sim-1", name="Product Sim 1", base_price=10.0, current_price=9.0, image="img1.jpg", description="Desc 1")
    mock_prod_2 = Product(id="prod-sim-2", name="Product Sim 2", base_price=20.0, current_price=18.0, image="img2.jpg", description="Desc 2")

    mock_db_session = MagicMock()
    mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_prod_1, mock_prod_2]
    app.dependency_overrides[get_db] = lambda: mock_db_session

    with patch("app.api.v1.endpoints.recommendations.compute_active_session_vector", return_value=mock_vector), \
         patch("app.api.v1.endpoints.recommendations.rank_products_by_similarity", return_value=mock_ranked_ids):

         response = client.get("/api/v1/recommendations/personalized?session_id=session-123")
         
         assert response.status_code == 200
         data = response.json()
         assert data["recommender"] == "vector_similarity"
         assert len(data["products"]) == 2
         assert data["products"][0]["id"] == "prod-sim-1"
         assert data["products"][0]["name"] == "Product Sim 1"
         assert data["products"][0]["current_price"] == 9.0

def test_personalized_recommendations_category_affinity():
    # Mock session vector to be zero (cold-start)
    mock_vector = [0.0] * 384
    
    mock_prod = Product(id="prod-aff-1", name="Product Affinity 1", base_price=15.0, current_price=15.0, image="img_aff.jpg", description="Affinity Desc")

    # Mock Redis client using AsyncMock for async methods
    mock_redis = MagicMock()
    mock_redis.zrevrange = AsyncMock(return_value=[b"Sports"])
    
    mock_db_session = MagicMock()
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_prod]
    mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_prod]
    app.dependency_overrides[get_db] = lambda: mock_db_session

    with patch("app.api.v1.endpoints.recommendations.compute_active_session_vector", return_value=mock_vector), \
         patch("app.api.v1.endpoints.recommendations.redis_service.get_client", return_value=mock_redis):

         response = client.get("/api/v1/recommendations/personalized?session_id=session-empty&user_id=user-123")
         
         assert response.status_code == 200
         data = response.json()
         assert data["recommender"] == "category_affinity"
         assert len(data["products"]) == 1
         assert data["products"][0]["id"] == "prod-aff-1"
         assert data["products"][0]["name"] == "Product Affinity 1"

def test_personalized_recommendations_global_trending():
    # Mock session vector to be zero, no user ID
    mock_vector = [0.0] * 384
    
    mock_prod = Product(id="prod-trend-1", name="Trending Product 1", base_price=5.0, current_price=5.0, image="img_trend.jpg", description="Trending Desc")

    mock_db_session = MagicMock()
    mock_db_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_prod]
    mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_prod]
    app.dependency_overrides[get_db] = lambda: mock_db_session

    with patch("app.api.v1.endpoints.recommendations.compute_active_session_vector", return_value=mock_vector):

         response = client.get("/api/v1/recommendations/personalized")
         
         assert response.status_code == 200
         data = response.json()
         assert data["recommender"] == "global_trending"
         assert len(data["products"]) == 1
         assert data["products"][0]["id"] == "prod-trend-1"
         assert data["products"][0]["name"] == "Trending Product 1"
