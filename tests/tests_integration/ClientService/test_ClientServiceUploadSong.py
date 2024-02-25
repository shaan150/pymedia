from io import BytesIO

from client_service import app
from fastapi.testclient import TestClient
import os
import json

from tests.tests_integration.ClientService.client_service_utils import (mock_service_url, mock_service_exception_handling,
                                                                    mock_redirect_response_with_cookies)
from tests.tests_integration.utils import mock_template_response_with_cookies
os.environ["DEBUG"] = "True"
client = TestClient(app)


def test_upload_song_success(mock_service_url, mock_template_response_with_cookies,
                             mock_service_exception_handling, mock_redirect_response_with_cookies):
    # Create mock files
    image_file = BytesIO(b"fake image data")
    image_file.name = "test_image.png"
    mp3_file = BytesIO(b"fake mp3 data")
    mp3_file.name = "test_song.mp3"

    cookies = {"auth_token": "mocktoken", "username": "testuser"}

    # Prepare form data
    data = {
        "song_name": (None, "test_song"),  # Use tuple format to include form fields in files parameter
        "artist": (None, "test_artist"),
        "image": (image_file.name, image_file, "image/png"),
        "mp3_file": (mp3_file.name, mp3_file, "audio/mpeg"),
    }

    response = client.post("/upload/song", files=data, cookies=cookies)
    response_data = json.loads(response.text)
    assert response_data["status_code"] == 303
    assert response_data["url"] == "/home"

def test_upload_song_with_invalid_format(mock_service_url, mock_template_response_with_cookies, mock_service_exception_handling, mock_redirect_response_with_cookies):
    # Create mock files
    image_file = BytesIO(b"fake image data")
    image_file.name = "test_image.png"
    mp4_file = BytesIO(b"fake mp4 data")
    mp4_file.name = "test_song.mp4"

    cookies = {"auth_token": "mocktoken", "username": "testuser"}

    # Prepare form data
    data = {
        "song_name": (None, "test_song"),  # Use tuple format to include form fields in files parameter
        "artist": (None, "test_artist"),
        "image": (image_file.name, image_file, "image/png"),
        "mp3_file": (mp4_file.name, mp4_file, "audio/mp4"),
    }

    response = client.post("/upload/song", files=data, cookies=cookies)
    response_data = json.loads(response.text)
    assert response_data["status_code"] == 200
    assert response_data["template_name"] == "upload.html"
    assert response_data["error"] == "Invalid Audio File Type"

def test_upload_song_failure(mock_service_url, mock_template_response_with_cookies, mock_service_exception_handling):
    cookies = {"auth_token": "mocktoken", "username": "testuser"}
    response = client.post("/upload/song", cookies=cookies)
    assert response.status_code == 422