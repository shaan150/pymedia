from client_service import app
from fastapi.testclient import TestClient
import os

import json

from tests.tests_integration.ClientService.client_service_utils import (mock_service_url, mock_service_exception_handling,
                                                                  mock_redirect_response_with_cookies,
                                                                  mock_service_url_no_url)
from tests.tests_integration.utils import mock_template_response_with_cookies

os.environ["DEBUG"] = "True"
client = TestClient(app)

def test_home_page_success(mock_service_url, mock_template_response_with_cookies, mock_service_exception_handling):
    response = client.get("/home", cookies={"auth_token": "mocktoken", "username": "testuser"})
    response_data = json.loads(response.text)

    assert response_data["status_code"] == 200
    assert "home.html" in response_data["template_name"]

def test_home_page_token_invalid(mock_service_url, mock_service_exception_handling, mock_template_response_with_cookies, mock_redirect_response_with_cookies):
    response = client.get("/home", cookies={"auth_token": "invalid", "username": "testuser"})
    response_data = json.loads(response.text)
    assert response.status_code == 303
    assert response_data["url"] == "/login"

def test_home_page_no_token(mock_service_url, mock_service_exception_handling, mock_template_response_with_cookies, mock_redirect_response_with_cookies):
    response = client.get("/home")
    response_data = json.loads(response.text)
    assert response.status_code == 303
    assert response_data["url"] == "/login"