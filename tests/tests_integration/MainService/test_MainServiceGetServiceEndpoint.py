from unittest.mock import patch, AsyncMock

import pytest

from classes.enum.ServiceType import ServiceType
from main_service import app
from fastapi.testclient import TestClient
import os
import json

os.environ["DEBUG"] = "True"
client = TestClient(app)

@pytest.fixture
def mock_get_service_success():
    with patch("main_service.MainService.get_service", new_callable=AsyncMock) as mock_get_service:
        mock_get_service.return_value = {"service_name": "ExampleService", "service_url": "http://example.com"}
        yield

@pytest.fixture
def mock_get_service_not_found():
    with patch("main_service.MainService.get_service", new_callable=AsyncMock) as mock_get_service:
        mock_get_service.return_value = None
        yield

@pytest.fixture
def mock_get_service_exception():
    with patch("main_service.MainService.get_service", new_callable=AsyncMock) as mock_get_service:
        mock_get_service.side_effect = Exception("Internal Server Error")
        yield

def test_get_service_success(mock_get_service_success):
    response = client.get("/get_service?service_type="+ServiceType.AUTH_SERVICE.value)
    assert response.status_code == 200
    assert response.json() == {"service_name": "ExampleService", "service_url": "http://example.com"}

def test_get_service_no_type_provided():
    response = client.get("/get_service")  # No service_type query parameter
    assert response.status_code == 422

def test_get_service_not_found(mock_get_service_not_found):
    response = client.get("/get_service?service_type="+ServiceType.AUTH_SERVICE.value)
    assert response.status_code == 404
    assert "No ServiceType.AUTH_SERVICE service found" in response.json()["detail"]

def test_get_service_exception(mock_get_service_exception):
    response = client.get("/get_service?service_type="+ServiceType.AUTH_SERVICE.value)
    assert response.status_code == 500
    assert "Internal Server Error" in response.json()["detail"]