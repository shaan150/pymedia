from unittest.mock import patch, AsyncMock

import pytest
from fastapi import HTTPException
from classes.ServiceInfo import ServiceInfo
from classes.enum.ServiceType import ServiceType

from tests.tests_integration.utils import MockRedirectResponse, mock_service_url_side_effect


def mock_service_exception_handling_side_effect(service_url, operation, method, data=None, params=None, files=None):
    # Example logic to return different values based on parameters

    if operation == "validate_user" and method == "POST":
        if data == {"username": "testuser", "password": "testpassword"}:
            return {"token": "mocktoken"}, 200
        else:
            return {"detail": "Invalid Details"}, 401

    if operation == "validate_token" and method == "GET":
        if params == {"token": "mocktoken", "username": "testuser"}:
            return {"detail": "Token is valid"}, 200
        else:
            raise HTTPException(status_code=401, detail="Invalid Token")

    if operation == "songs" and method == "GET":
        raise HTTPException(status_code=404, detail="No songs found")

    if operation == "create_user" and method == "POST":
        if data == {"username": "testuser", "password": "testpassword", "email": "testemail"}:
            return {"detail": "User created"}, 200
        elif data == {"username": "testuser2", "password": "testpassword", "email": "testemail"}:
            raise HTTPException(status_code=409, detail="User already exists")
        else:
            raise Exception("Internal Server Error")

    if operation == "songs/song/create" and method == "POST":
        return {"detail": "Song created"}, 200

    if operation == "upload/song" and method == "POST":
        return {"detail": "song uploaded"}, 200

    if operation == "get_services" and method == "GET":

        return {"services": [ServiceInfo("test_service", service_type=ServiceType.FILE_SERVICE.name,
                                         url="test.com").to_dict()]}, 200






@pytest.fixture
def mock_service_url():
    with patch('classes.services.ClientService.ClientService.get_service_url', new_callable=AsyncMock) as mock_get_service_url:
        mock_get_service_url.side_effect = mock_service_url_side_effect
        yield

@pytest.fixture
def mock_service_url_no_url():
    with patch('classes.services.ClientService.ClientService.get_service_url', new_callable=AsyncMock) as mock_get_service_url:
        mock_get_service_url.side_effect = None
        yield


@pytest.fixture
def mock_service_exception_handling():
    with patch('classes.services.ClientService.ClientService.service_exception_handling',
               new_callable=AsyncMock) as mock_get_service_exception_handling:
        mock_get_service_exception_handling.side_effect = mock_service_exception_handling_side_effect
        yield


@pytest.fixture
def mock_redirect_response_with_cookies():
    with patch('client_service.RedirectResponse') as mock_redirect_response:
        # Mock for RedirectResponse
        def redirect_response_mock(url, status_code=303, *args, **kwargs):
            response = MockRedirectResponse(url, status_code)
            for key, value in kwargs.get('cookies', {}).items():
                response.set_cookie(key, value['value'], value.get('httponly', True))
            return response

        mock_redirect_response.side_effect = redirect_response_mock

        yield