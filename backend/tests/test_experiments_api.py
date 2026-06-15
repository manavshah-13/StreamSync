import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock
import sys, os

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db.database import get_db
from models.schema import Experiment, ExperimentResult

@pytest.mark.asyncio
async def test_track_experiment_event_not_found():
    # Test tracking when the experiment doesn't exist
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    def override_get_db():
        yield mock_db
        
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "experiment_id": "non_existent_exp",
            "variant_group": "B",
            "event_type": "conversion",
            "revenue": 99.99
        }
        res = await ac.post("/api/v1/experiments/track", json=payload)
        assert res.status_code == 404
        
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_track_experiment_event_success_insert():
    # Test tracking a conversion event when no result exists yet (insert path)
    mock_exp = Experiment(id=1, name="test_exp", is_active=True)
    mock_db = MagicMock()
    
    # First query is looking up Experiment by name (returns mock_exp)
    # Second query is checking if ExperimentResult exists (returns None)
    # Let's mock query to return a mock query object where first() yields mock_exp or None
    mock_query = MagicMock()
    
    def mock_first():
        if mock_query.filter.call_args[0][0].left.name == "name":
            return mock_exp
        return None
        
    mock_query.filter.return_value.first.side_effect = mock_first
    mock_db.query.return_value = mock_query
    
    def override_get_db():
        yield mock_db
        
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "experiment_id": "test_exp",
            "variant_group": "B",
            "event_type": "conversion",
            "revenue": 150.0
        }
        res = await ac.post("/api/v1/experiments/track", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "success"
        
        # Verify db.add was called to insert the new ExperimentResult
        assert mock_db.add.called
        added_res = mock_db.add.call_args[0][0]
        assert isinstance(added_res, ExperimentResult)
        assert added_res.experiment_id == 1
        assert added_res.variant_group == "B"
        assert added_res.conversions == 1
        assert added_res.total_revenue == 150.0
        
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_track_experiment_event_success_update():
    # Test tracking a conversion event when a result row already exists (update/atomic path)
    mock_exp = Experiment(id=1, name="test_exp", is_active=True)
    mock_result = ExperimentResult(id=10, experiment_id=1, variant_group="B", conversions=5, total_revenue=500.0)
    mock_db = MagicMock()
    
    mock_query = MagicMock()
    
    def mock_first():
        # First query for Experiment name
        if mock_query.filter.call_args[0][0].left.name == "name":
            return mock_exp
        # Second query for ExperimentResult
        return mock_result
        
    mock_query.filter.return_value.first.side_effect = mock_first
    mock_db.query.return_value = mock_query
    
    def override_get_db():
        yield mock_db
        
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "experiment_id": "test_exp",
            "variant_group": "B",
            "event_type": "conversion",
            "revenue": 50.0
        }
        res = await ac.post("/api/v1/experiments/track", json=payload)
        assert res.status_code == 200
        
        # Verify db.execute was called to execute the atomic update statement
        assert mock_db.execute.called
        
    app.dependency_overrides.clear()
