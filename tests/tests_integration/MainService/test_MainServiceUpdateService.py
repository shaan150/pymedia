import os

from fastapi.testclient import TestClient
from main_service import app
import pytest
from unittest.mock import patch, AsyncMock

os.environ["DEBUG"] = "True"
client = TestClient(app)

@pytest.fixture
def mock_update_or_add_service():
    with patch("main_service.service.update_or_add_service", new_callable=AsyncMock) as mock:
        yield mock

def test_update_service_success(mock_update_or_add_service):
    service_data = {
        "name": "Example Service",
        "type": "ExampleType",
        "url": "http://example.com",
        "cpu_usage": 10,
        "memory_usage": 2048,
        "memory_free": 1024,
        "cpu_free": 5,
        "total_memory": 4096
    }
    response = client.post("/update_or_add_service", json=service_data)
    assert response.status_code == 200
    assert response.json() == {"detail": "Service Example Service Updated"}

def test_update_service_invalid_request():
    # Example with missing 'name' field
    service_data = {
        "type": "ExampleType",
        "url": "http://example.com"
    }
    response = client.post("/update_or_add_service", json=service_data)
    assert response.status_code == 400
    assert "Insufficient service data" in response.json()["detail"]