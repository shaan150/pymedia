from fastapi.testclient import TestClient
from main import app  # Import your FastAPI app
from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.asyncio
async def test_create_user():
    # Call your asynchronous create_user function
    result = await create_user("johndoe2", "12345", "generated_salt", "johndoe2@email.com")
    assert result == True

@pytest.mark.asyncio
async def test_validate_user():
    # Call your asynchronous validate_user function
    user = await auth_user("johndoe1", "12345")
    assert user is not None