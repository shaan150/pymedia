from unittest.mock import patch, AsyncMock

import pytest
from fastapi import HTTPException
from jwt import PyJWTError

from classes.ServiceInfo import ServiceInfo
from classes.enum.ServiceType import ServiceType

from tests.tests_integration.utils import MockRedirectResponse, mock_service_url_side_effect


def mock_service_exception_handling_side_effect(service_url, operation, method, data=None, params=None, files=None):
    if operation == "users/user/salt" and method == "GET":
        if params == {"username": "testuser"}:
            return {"salt": "mocksalt"}, 200
        elif params == {"username": "testuser5"}:
            return {"salt": "mocksalt"}, 200

        if params == {"username": "testuser2"}:
            raise HTTPException(status_code=404, detail="User not found")

        if params == {"username": None}:
            raise HTTPException(status_code=422, detail="Invalid Request")

        raise HTTPException(status_code=500, detail="Internal Server Error")

    if operation == "users/user/validate" and method == "POST":
        if data["username"] == "testuser":
            return {"detail": "User validated"}, 200
        else:
            raise HTTPException(status_code=401, detail="Invalid Details")

    if operation == "users/user" and method == "GET":
        if params == {"username": "testuser"}:
            return {"username": "testuser"}, 200
        elif params == {"username": "testuser5"}:
            return {"username": "testuser5"}, 200
        else:
            raise HTTPException(status_code=404, detail="User not found")

    if operation == "users/user/create" and method == "POST":
        if data["username"] == "testuser2" and data["email"] == "testemail":
            return {"detail": "User created"}, 200
        elif data["username"] == "testuser3":
            raise HTTPException(status_code=409, detail="User already exists")
        else:
            raise HTTPException(status_code=500, detail="Internal Server Error")


@pytest.fixture
def mock_service_url():
    with patch('classes.services.AuthService.AuthService.get_service_url', new_callable=AsyncMock) as mock_get_service_url:
        mock_get_service_url.side_effect = mock_service_url_side_effect
        yield

@pytest.fixture
def mock_service_url_no_url():
    with patch('classes.services.AuthService.AuthService.get_service_url', new_callable=AsyncMock) as mock_get_service_url:
        mock_get_service_url.side_effect = None
        yield


@pytest.fixture
def mock_service_exception_handling():
    with patch('classes.services.AuthService.AuthService.service_exception_handling',
               new_callable=AsyncMock) as mock_get_service_exception_handling:
        mock_get_service_exception_handling.side_effect = mock_service_exception_handling_side_effect
        yield

@pytest.fixture
def mock_generate_token():
    with patch('classes.services.AuthService.AuthService.generate_token',
               new_callable=AsyncMock) as mock_generate_token:
        mock_generate_token.return_value = "mocktoken"
        yield

@pytest.fixture
def mock_generate_token_invalid():
    with patch('classes.services.AuthService.AuthService.generate_token',
               new_callable=AsyncMock) as mock_generate_token:
        mock_generate_token.side_effect = Exception("Internal Server Error")
        yield

@pytest.fixture
def mock_decode_token():
    with patch('classes.services.AuthService.AuthService.decode_token',
               new_callable=AsyncMock) as mock_decode_token:
        mock_decode_token.return_value = True
        yield

@pytest.fixture
def mock_decode_token_invalid():
    with patch('classes.services.AuthService.AuthService.decode_token',
               new_callable=AsyncMock) as mock_decode_token:
        mock_decode_token.side_effect = PyJWTError("Invalid Token")
        yield

@pytest.fixture
def mock_decode_token_internal_error():
    with patch('classes.services.AuthService.AuthService.decode_token',
               new_callable=AsyncMock) as mock_decode_token:
        mock_decode_token.side_effect = Exception("Internal Server Error")
        yield