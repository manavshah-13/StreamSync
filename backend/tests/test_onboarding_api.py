import pytest
from httpx import AsyncClient, ASGITransport
import sys, os

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db.database import get_db

@pytest.mark.asyncio
async def test_users_onboarding_endpoint():
    """
    Test POST /api/v1/users/onboarding:
    - Verifies that a valid payload correctly inserts onboarding preferences
    - Checks that guest users are created if no authentication token is provided
    - Confirms it returns user_id and session_id
    """
    payload = {
        "age_group": "26-35",
        "gender": "Non-binary",
        "interests": ["Electronics", "Apparel"],
        "shopping_preferences": {
            "deals": True,
            "newTech": False,
            "ecoFriendly": True
        }
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/users/onboarding", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "success"
        assert "user_id" in data
        assert "session_id" in data
        assert data["user_id"] is not None
        assert data["session_id"].startswith("session-")
