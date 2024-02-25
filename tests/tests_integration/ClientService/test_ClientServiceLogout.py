import json
import os

from client_service import app
from fastapi.testclient import TestClient
from tests.tests_integration.ClientService.client_service_utils import mock_redirect_response_with_cookies
os.environ["DEBUG"] = "True"
client = TestClient(app)

def test_logout_success(mock_redirect_response_with_cookies):
    response = client.get("/logout")
    response_data = json.loads(response.text)

    assert response_data["status_code"] == 303  # Redirect to login page
    assert response_data["url"] == "/login"
    assert "auth_token" not in response_data["cookies"]
    assert "username" not in response_data["cookies"]