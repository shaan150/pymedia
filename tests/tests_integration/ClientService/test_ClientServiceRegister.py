import os

from client_service import app
from fastapi.testclient import TestClient
from tests.tests_integration.ClientService.client_service_utils import (mock_redirect_response_with_cookies, mock_service_url,
                                                                  mock_service_exception_handling)
from tests.tests_integration.utils import mock_template_response_with_cookies

import json

os.environ["DEBUG"] = "True"
client = TestClient(app)

def test_register_success(mock_redirect_response_with_cookies, mock_service_url, mock_service_exception_handling):
    response = client.post("/register", data={"username": "testuser", "password": "testpassword", "email": "testemail"})
    response_data = json.loads(response.text)
    assert response_data["status_code"] == 303  # Redirect to login page
    assert response_data["url"] == "/login"

def test_register_failure(mock_service_url, mock_service_exception_handling, mock_template_response_with_cookies):
    response = client.post("/register", data={"username": "testuser2", "password": "testpassword", "email": "testemail"})
    response_data = json.loads(response.text)
    assert response_data["status_code"] == 200
    assert response_data["error"] == "User already exists"
    assert "register.html" in response_data["template_name"]

def test_register_invalid_request(mock_service_url):
    response = client.post("/register", data={})
    assert response.status_code == 422