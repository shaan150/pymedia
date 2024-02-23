from fastapi.testclient import TestClient
from auth_service import app  # Import your FastAPI app
from unittest.mock import AsyncMock, patch
import pytest


client = TestClient(app)  # Create a TestClient instance for your app

@pytest.mark.asyncio
@patch("DatabaseConnector.create_user")
@patch("utils.hash_password")
async def test_create_user(mock_hash_password, mock_create_user):
    # Mock the hash_password function
    mock_hash_password.return_value = AsyncMock(return_value="hashed_password")

    # Mock the create_user function and specify the return value
    mock_create_user.return_value = AsyncMock(return_value=True)

    # Define the data to be sent in the request
    data = {
        "username": "johndoe2",
        "password": "12345",
        "email": "johndoe2@email.com"
    }

    # Make a POST request to the create_user endpoint
    response = client.post("/create_user", json=data)

    # Assertions to validate the response
    assert response.status_code == 200
    assert response.json() == {"detail": "User johndoe2 created"}

    # Validate with missing data that the endpoint returns a 400
    data = {
        "username": "johndoe2"
    }

    response = client.post("/create_user", json=data)

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Request"}
