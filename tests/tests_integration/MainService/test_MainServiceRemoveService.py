import os
from unittest.mock import patch, AsyncMock
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from main_service import app  # Adjust the import path as necessary

os.environ["DEBUG"] = "True"
client = TestClient(app)

@pytest.fixture
def mock_del_service_failure():
    with patch("main_service.service.del_service", new_callable=AsyncMock) as mock:
        mock.side_effect = HTTPException(status_code=404, detail="Service not found")
        yield mock

def test_remove_service_no_url():
    response = client.delete("/remove_service/")
    assert response.status_code == 404

def test_remove_service_failure(mock_del_service_failure):
    service_url = "http://nonexistent.com/service"
    response = client.delete(f"/remove_service/{service_url}")
    assert response.status_code == 404
    assert "Not Found" in response.json()["detail"]