from unittest.mock import patch, AsyncMock

import pytest

from database_service import app
from fastapi.testclient import TestClient
import os
import json

os.environ["DEBUG"] = "True"
client = TestClient(app)


@pytest.fixture
def mock_validate_user():
    with patch("database_service.get_user_by_password", new_callable=AsyncMock) as mock_validate_user:
        mock_validate_user.return_value = {"username": "testuser", "email": "testemail"}
        yield


@pytest.fixture
def mock_validate_user_failure():
    with patch("database_service.get_user_by_password", new_callable=AsyncMock) as mock_validate_user:
        mock_validate_user.return_value = None
        yield


@pytest.fixture
def mock_validate_user_exception():
    with patch("database_service.get_user_by_password", new_callable=AsyncMock) as mock_validate_user:
        mock_validate_user.side_effect = Exception("Internal Server Error")
        yield


def test_database_service_validate_user_success(mock_validate_user):
    response = client.post("/users/user/validate", json={"username": "testuser", "password": "testpassword"})
    response_data = json.loads(response.text)
    assert response.status_code == 200
    assert response_data["detail"] == "User Validated"


def test_database_service_validate_user_failure(mock_validate_user_failure):
    response = client.post("/users/user/validate", json={"username": "testuser", "password": "testpassword"})
    response_data = json.loads(response.text)
    assert response.status_code == 401
    assert response_data["detail"] == "Not Valid Password"


def test_database_service_validate_user_exception(mock_validate_user_exception):
    response = client.post("/users/user/validate", json={"username": "testuser", "password": "testpassword"})
    response_data = json.loads(response.text)
    assert response.status_code == 500
    assert response_data["detail"] == "Internal Server Error"