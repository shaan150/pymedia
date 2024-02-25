from auth_service import app
from fastapi.testclient import TestClient
import os
import json
from tests.tests_integration.AuthService.auth_service_utils import (mock_service_url, mock_service_exception_handling)

os.environ["DEBUG"] = "True"
client = TestClient(app)

def test_auth_service_create_user_success(mock_service_url, mock_service_exception_handling):
    response = client.post("/create_user", json={"username": "testuser2", "password": "testpassword", "email": "testemail"})
    response_data = json.loads(response.text)
    assert response.status_code == 200
    assert response_data["detail"] == "User testuser2 created"

def test_auth_service_create_user_already_exists(mock_service_url, mock_service_exception_handling):
    response = client.post("/create_user", json={"username": "testuser3", "password": "testpassword", "email": "testemail"})
    response_data = json.loads(response.text)
    assert response.status_code == 409
    assert response_data["detail"] == "User already exists"

    response = client.post("/create_user", json={"username": "testuser", "password": "testpassword", "email": "testemail"})
    response_data = json.loads(response.text)
    assert response.status_code == 409
    assert response_data["detail"] == "User testuser already exists"


def test_auth_service_create_user_failure(mock_service_url, mock_service_exception_handling):
    response = client.post("/create_user", json={})
    response_data = json.loads(response.text)
    assert response.status_code == 400
    assert response_data["detail"] == "Invalid Request"

    response = client.post("/create_user", json={"username": "testuser4", "password": "testpassword", "email": "testemail"})
    response_data = json.loads(response.text)
    assert response.status_code == 500
    assert response_data["detail"] == "Internal Server Error"