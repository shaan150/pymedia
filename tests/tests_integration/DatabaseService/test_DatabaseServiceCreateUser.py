from unittest.mock import patch, AsyncMock

import pytest

from database_service import app
from fastapi.testclient import TestClient
import os
import json

from tests.tests_integration.DatabaseService.database_service_utils import mock_get_user, mock_get_user_failure

os.environ["DEBUG"] = "True"
client = TestClient(app)

@pytest.fixture
def mock_create_user():
    with patch("database_service.create_user",  new_callable=AsyncMock) as mock_create_user:
        mock_create_user.return_value = "User created"
        yield

@pytest.fixture
def mock_create_user_failure():
    with patch("database_service.create_user",  new_callable=AsyncMock) as mock_create_user:
        mock_create_user.return_value = None
        yield

@pytest.fixture
def mock_create_user_exception():
    with patch("database_service.create_user",  new_callable=AsyncMock) as mock_create_user:
        mock_create_user.side_effect = Exception("Internal Server Error")
        yield


def test_database_service_create_user_success(mock_create_user, mock_get_user_failure):
    response = client.post("/users/user/create", json={"username": "testuser2", "password": "testpassword", "email": "testemail"})
    response_data = json.loads(response.text)
    assert response.status_code == 200
    assert response_data["detail"] == "User created successfully"

def test_database_service_create_user_already_exists(mock_create_user, mock_get_user):
    response = client.post("/users/user/create", json={"username": "testuser", "password": "testpassword", "email": "testemail"})
    response_data = json.loads(response.text)
    assert response.status_code == 409
    assert response_data["detail"] == "User already exists"


def test_database_service_create_user_failure(mock_create_user_failure, mock_get_user_failure):
    response = client.post("/users/user/create", json={},)
    assert response.status_code == 422

    response = client.post("/users/user/create", json={"username": "testuser4", "password": "testpassword", "email": "testemail"})
    response_data = json.loads(response.text)
    assert response.status_code == 400
    assert response_data["detail"] == "Could not create user"


def test_database_service_create_user_exception(mock_create_user_exception, mock_get_user_failure):
    response = client.post("/users/user/create", json={"username": "testuser4", "password": "testpassword", "email": "testemail"})
    response_data = json.loads(response.text)
    assert response.status_code == 500
    assert response_data["detail"] == "Internal Server Error"
