from unittest.mock import patch, AsyncMock

import pytest

from classes.pydantic.UserAccount import UserAccount


@pytest.fixture
def mock_get_user():
    with patch("database_service.get_user",  new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = ("testuser", "testpassword", "testemail")
        yield mock_get_user

@pytest.fixture
def mock_get_user_failure():
    with patch("database_service.get_user", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = None
        yield

@pytest.fixture
def mock_get_user_exception():
    with patch("database_service.get_user", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.side_effect = Exception("Internal Server Error")
        yield