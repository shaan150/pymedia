import json
import os

from fastapi.testclient import TestClient

from client_service import app
from tests.tests_integration.utils import (mock_template_response_with_cookies)
from tests.tests_integration.ClientService.client_service_utils import (mock_service_url, mock_service_exception_handling,
                                                                  mock_redirect_response_with_cookies)
os.environ["DEBUG"] = "True"
client = TestClient(app)

def test_login_success(mock_service_url, mock_service_exception_handling, mock_redirect_response_with_cookies):
    response = client.post("/login", data={"username": "testuser", "password": "testpassword"})
    response_data = json.loads(response.text)
    assert response_data["status_code"] == 303  # Redirect to home page
    assert response_data["url"] == "/home"
    assert "auth_token" in response_data["cookies"]
    assert response_data["cookies"]["auth_token"]["value"] == "mocktoken"
    assert "username" in response_data["cookies"]
    assert response_data["cookies"]["username"]["value"] == "testuser"

def test_login_failure(mock_service_url, mock_template_response_with_cookies, mock_service_exception_handling):
    response = client.post("/login", data={"username": "wronguser", "password": "wrongpassword"})
    response_data = json.loads(response.text)
    assert response_data["status_code"] == 200
    assert response_data["error"] == "Invalid Details"
    assert "login.html" in response_data["template_name"]

def test_login_invalid_request(mock_service_url):
    response = client.post("/login", data={})
    assert response.status_code == 422