from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    """
    Validates that the health check endpoint returns 200 and matches the expected schema.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "service": "SURAKSHA AI Backend",
        "status": "Running"
    }

def test_api_routes_initialization():
    """
    Validates that endpoints return standard HTTP 200 and correct status payload.
    """
    # Test chat route initialization
    response = client.post("/api/chat/query?session_id=sess_01&message=test")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "Project Initialized"
    assert "data" in json_data
