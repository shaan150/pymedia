from tempfile import TemporaryDirectory

import pytest

from file_service import app, service
from fastapi.testclient import TestClient
import os

os.environ["DEBUG"] = "True"
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_test_directories():
    with TemporaryDirectory() as tmp_music, TemporaryDirectory() as tmp_image:
        original_music_dir = service.music_dir
        original_image_dir = service.image_dir
        service.music_dir = tmp_music
        service.image_dir = tmp_image
        yield
        service.music_dir = original_music_dir
        service.image_dir = original_image_dir


def create_test_files(song_id: str):
    mp3_file_path = os.path.join(service.music_dir, f"{song_id}.mp3")
    image_file_path = os.path.join(service.image_dir, f"{song_id}.jpg")
    # Create temporary files to simulate existing song and image files
    with open(mp3_file_path, 'wb') as f:
        f.write(b"Fake MP3 data")
    with open(image_file_path, 'wb') as f:
        f.write(b"Fake image data")


def test_delete_existing_song_files(setup_test_directories):
    song_id = "test_song"
    create_test_files(song_id)
    response = client.delete(f"/delete/song?song_id={song_id}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Files deleted successfully"}
    assert not os.path.exists(os.path.join(service.music_dir, f"{song_id}.mp3"))
    assert not os.path.exists(os.path.join(service.image_dir, f"{song_id}.jpg"))

def test_delete_nonexistent_song_files(setup_test_directories):
    song_id = "nonexistent_song"
    response = client.delete(f"/delete/song?song_id={song_id}")
    assert response.status_code == 404

def test_delete_song_invalid_id(setup_test_directories):
    response = client.delete("/delete/song?song_id=")
    assert response.status_code == 400
    assert "Invalid Request" in response.json()["detail"]