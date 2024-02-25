from auth_service import app
from fastapi.testclient import TestClient
import os
import json
from tests.tests_integration.AuthService.auth_service_utils import (mock_service_url, mock_service_exception_handling,
                                                              mock_decode_token, mock_decode_token_invalid,
                                                              mock_decode_token_internal_error)

os.environ["DEBUG"] = "True"
client = TestClient(app)

def test_auth_service_validate_token_success(mock_service_url, mock_service_exception_handling, mock_decode_token):
    response = client.get("/validate_token",params = {"token": "mocktoken"})
    response_data = json.loads(response.text)
    assert response.status_code == 200
    assert response_data["detail"] == "Token is valid"


def test_auth_service_validate_token_invalid(mock_service_url, mock_service_exception_handling,
                                             mock_decode_token_invalid):
    response = client.get("/validate_token",params = {"token": "invalid"})
    response_data = json.loads(response.text)
    assert response.status_code == 401
    assert response_data["detail"] == "Invalid Token"

def test_auth_service_validate_token_failure(mock_service_url, mock_service_exception_handling,
                                             mock_decode_token_internal_error):
    response = client.get("/validate_token",params = {"token": "mocktoken"})
    response_data = json.loads(response.text)
    assert response.status_code == 500
    assert response_data["detail"] == "Internal Server Error"

def test_auth_service_validate_token_invalid_request(mock_service_url, mock_service_exception_handling, mock_decode_token):
    response = client.get("/validate_token")
    response_data = json.loads(response.text)
    assert response.status_code == 422