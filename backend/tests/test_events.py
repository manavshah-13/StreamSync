import pytest
from httpx import AsyncClient, ASGITransport
import sys, os

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

@pytest.mark.asyncio
async def test_ingest_event():
    """
    Test event ingestion endpoint (POST /api/v1/events).
    Sends a mock tracking event payload and verifies it returns 201 Created
    and a valid Redis Stream ID (timestamped sequence format).
    """
    payload = {
        "user_id": "user-test-uuid-456",
        "session_id": "sess-test-abc",
        "event_type": "click",
        "sku": "prod-5",
        "metadata": {"referrer": "pytest_unit_tests", "position": 2}
    }

    # Use ASGITransport to hit the application gateway in-process
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/events", json=payload)

    # Assert 201 Created status code
    assert response.status_code == 201

    # Extract JSON response payload
    data = response.json()
    assert data["status"] == "queued"
    assert "event_id" in data

    # Verify that the response object contains a valid timestamped Redis Stream ID sequence (e.g. "1718335028123-0")
    event_id = data["event_id"]
    assert "-" in event_id, f"Event ID '{event_id}' is not in standard Redis Stream ID format"
    
    parts = event_id.split("-")
    assert len(parts) == 2, f"Event ID '{event_id}' has invalid segment count"
    assert parts[0].isdigit(), "Timestamp portion of Redis Stream ID must be numeric"
    assert parts[1].isdigit(), "Sequence portion of Redis Stream ID must be numeric"
