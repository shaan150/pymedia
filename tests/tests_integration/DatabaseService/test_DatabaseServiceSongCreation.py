from unittest.mock import AsyncMock, patch

import pytest

from database_service import app
from fastapi.testclient import TestClient
import os

os.environ["DEBUG"] = "True"
client = TestClient(app)


@pytest.fixture
def mock_get_song():
    with patch("database_service.get_songs", new_callable=AsyncMock) as mock_get_song:
        mock_get_song.return_value = "Song found"
        yield


@pytest.fixture
def mock_get_song_failure():
    with patch("database_service.get_songs", new_callable=AsyncMock) as mock_get_song:
        mock_get_song.return_value = None
        yield


@pytest.fixture
def mock_get_song_exception():
    with patch("database_service.get_songs", new_callable=AsyncMock) as mock_get_song:
        mock_get_song.side_effect = Exception("Internal Server Error")
        yield


@pytest.fixture
def mock_create_song():
    with patch("database_service.create_song", new_callable=AsyncMock) as mock_create_song:
        mock_create_song.return_value = "song id"
        yield


@pytest.fixture
def mock_create_song_failure():
    with patch("database_service.create_song", new_callable=AsyncMock) as mock_create_song:
        mock_create_song.return_value = None
        yield


@pytest.fixture
def mock_create_song_exception():
    with patch("database_service.create_song", new_callable=AsyncMock) as mock_create_song:
        mock_create_song.side_effect = Exception("Internal Server Error")
        yield


def test_database_service_create_song_success(mock_create_song, mock_get_song_failure):
    response = client.post("/songs/song/create", json={"song_id": "song_id", "song_name": "testtitle",
                                                       "artist": "testartist", "usernames": ["testuser"]})
    assert response.status_code == 200
    assert response.json() == {"detail": "Song created successfully", "song_id": "song id"}


def test_database_service_create_song_already_exists(mock_create_song, mock_get_song):
    response = client.post("/songs/song/create", json={"song_id": "song_id", "song_name": "testtitle",
                                                       "artist": "testartist", "usernames": ["testuser"]})
    assert response.status_code == 409
    assert response.json() == {"detail": "Song already exists"}


def test_database_service_create_song_failure(mock_create_song_failure, mock_get_song_failure):
    response = client.post("/songs/song/create", json={})
    assert response.status_code == 422


def test_database_service_create_song_exception(mock_create_song_exception, mock_get_song_failure):
    response = client.post("/songs/song/create", json={"song_id": "song_id", "song_name": "testtitle",
                                                       "artist": "testartist", "usernames": ["testuser"]})
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}