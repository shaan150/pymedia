import os
from unittest.mock import patch, AsyncMock

import pytest
from fastapi import Response
from fastapi.testclient import TestClient

from client_service import app

os.environ["DEBUG"] = "True"
client = TestClient(app)

# Corrected mock_service_url fixture to not be async and use the correct path
@pytest.fixture
def mock_service_url():
    with patch('classes.services.ClientService.ClientService.get_service_url', new_callable=AsyncMock) as mock_get_service_url:
        mock_get_service_url.return_value = "http://mockauthservice"
        yield
@pytest.fixture
def mock_service_exception_handling():
    with patch('classes.services.ClientService.ClientService.service_exception_handling',
               new_callable=AsyncMock) as mock_get_service_exception_handling:
        mock_get_service_exception_handling.return_value = ({"token": "mocktoken"}, 200)
        yield

@pytest.fixture
def mock_service_exception_handling_failure():
    with patch('classes.services.ClientService.ClientService.service_exception_handling',
               new_callable=AsyncMock) as mock_get_service_exception_handling:
        mock_get_service_exception_handling.return_value = ({"Invalid credentials"}, 401)
        yield


@pytest.fixture
def mock_template_response_success():
    # Mock the TemplateResponse to return a standard Response with a simple body
    with patch('fastapi.templating.Jinja2Templates.TemplateResponse') as mock_template:
        def template_response_mock(*args, **kwargs):
            # You can adjust the content to be more relevant to your test
            content = "Mocked template response"
            return Response(content=content, media_type="text/html", status_code=303)
        mock_template.side_effect = template_response_mock
        yield

@pytest.fixture
def mock_template_response_failure():
    # Mock the TemplateResponse to return a standard Response with a simple body
    with patch('fastapi.templating.Jinja2Templates.TemplateResponse') as mock_template:
        def template_response_mock(*args, **kwargs):
            # You can adjust the content to be more relevant to your test
            content = "Invalid details"
            return Response(content=content, media_type="text/html", status_code=200)
        mock_template.side_effect = template_response_mock
        yield
def test_login_success(mock_service_url, mock_service_exception_handling, mock_template_response_success):
    response = client.post("/login", data={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 303  # Redirect to /home

def test_login_failure( mock_service_url, mock_template_response_failure, mock_service_exception_handling_failure):
    response = client.post("/login", data={"username": "wronguser", "password": "wrongpassword"})
    assert response.status_code == 200  # Render login page again with error
    assert "Invalid details" in response.text

def test_login_invalid_request(mock_service_url):
    response = client.post("/login", data={})
    assert response.status_code == 422