from client_service import app
from fastapi.testclient import TestClient
import os

import json
from tests.tests_integration.utils import mock_template_response_with_cookies
from tests.tests_integration.ClientService.client_service_utils import (mock_redirect_response_with_cookies, mock_service_url,
                                                                  mock_service_exception_handling)

os.environ["DEBUG"] = "True"
client = TestClient(app)

def test_services_success(mock_template_response_with_cookies, mock_service_url, mock_service_exception_handling):
    response = client.get("/services", cookies={"auth_token": "mocktoken", "username": "testuser"})

    response_data = json.loads(response.text)
    assert response_data["status_code"] == 200
    assert "services.html" in response_data["template_name"]
    assert len(response_data["detail"]["services"]) == 1
    assert response_data["detail"]["services"][0]["name"] == "test_service"
    assert response_data["error"] == ''


def test_services_token_invalid(mock_service_url, mock_service_exception_handling, mock_template_response_with_cookies, mock_redirect_response_with_cookies):
    response = client.get("/services", cookies={"auth_token": "invalid", "username": "testuser"})
    response_data = json.loads(response.text)
    assert response.status_code == 303
    assert response_data["url"] == "/login"


def test_services_failure(mock_service_url, mock_template_response_with_cookies, mock_redirect_response_with_cookies):
    response = client.get("/services", cookies={"auth_token": "mocktoken", "username": "testuser"})
    response_data = json.loads(response.text)
    assert response.status_code == 303
    assert response.cookies["error_message"].startswith("Request Failure Exception An error occurred")
    assert response_data["url"] == "/error"
