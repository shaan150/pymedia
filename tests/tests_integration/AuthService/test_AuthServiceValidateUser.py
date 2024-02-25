from auth_service import app
from fastapi.testclient import TestClient
import os
import json


from tests.tests_integration.AuthService.auth_service_utils import (mock_service_url, mock_service_exception_handling,
                                                              mock_generate_token, mock_generate_token_invalid)

os.environ["DEBUG"] = "True"
client = TestClient(app)


def test_auth_service_validate_user_success(mock_service_url, mock_service_exception_handling, mock_generate_token):
    response = client.post("/validate_user", json={"username": "testuser", "password": "testpassword"})
    response_data = json.loads(response.text)
    assert response.status_code == 200
    assert response_data["token"] == "mocktoken"

def test_auth_service_validate_user_invalid(mock_service_url, mock_service_exception_handling, mock_generate_token):
    response = client.post("/validate_user", json={"username": "testuser5", "password": "invalid"})
    response_data = json.loads(response.text)
    assert response.status_code == 401
    assert response_data["detail"] == "Invalid Details"

def test_auth_service_validate_user_failure(mock_service_url, mock_service_exception_handling, mock_generate_token):
    response = client.post("/validate_user", json={})
    response_data = json.loads(response.text)
    assert response.status_code == 422
    assert response_data["detail"] == "Invalid Request"

def test_auth_service_validate_user_internal_error(mock_service_url, mock_service_exception_handling, mock_generate_token):
    response = client.post("/validate_user", json={"username": "testuser3", "password": "testpassword"})
    response_data = json.loads(response.text)
    assert response.status_code == 500
    assert response_data["detail"] == "Internal Server Error"

def test_auth_service_validate_user_invalid_token_generation(mock_service_url, mock_service_exception_handling, mock_generate_token_invalid):
    response = client.post("/validate_user", json={"username": "testuser", "password": "testpassword"})
    response_data = json.loads(response.text)
    assert response.status_code == 500
    assert response_data["detail"] == "Internal Server Error"