import os
from contextlib import asynccontextmanager
from tempfile import NamedTemporaryFile
from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient

from file_service import app

os.environ["DEBUG"] = "True"
client = TestClient(app)

@asynccontextmanager
async def async_mock_open(*args, **kwargs):
    mock_file = AsyncMock()
    yield mock_file

@pytest.fixture
def mock_file_storage_operations():
    with patch('aiofiles.open', new_callable=lambda: async_mock_open) as mock_file:
        yield mock_file

@pytest.fixture
def temp_mp3_file():
    with NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(b"Fake MP3 data")
        tmp.seek(0)
    yield tmp.name
    os.unlink(tmp.name)

@pytest.fixture
def temp_image_file():
    with NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(b"Fake image data")
        tmp.seek(0)
    yield tmp.name
    os.unlink(tmp.name)



def test_upload_file_success(temp_mp3_file, temp_image_file, mock_file_storage_operations):
    with open(temp_mp3_file, "rb") as mp3_file, open(temp_image_file, "rb") as image_file:
        response = client.put(
            "/upload/song?song_id=test_song",
            files={
                "mp3_file": ("test_song.mp3", mp3_file, "audio/mpeg"),
                "image_file": ("test_image.jpg", image_file, "image/jpeg")
            }
        )
    assert response.status_code == 200

def test_upload_file_failure(temp_mp3_file, temp_image_file, mock_file_storage_operations):
    response = client.put(
        "/upload/song?song_id=test_song",
        files={
            "mp3_file": ("test_song.mp3", "mp3_file", "audio/mpeg"),
        }
    )
    assert response.status_code == 422