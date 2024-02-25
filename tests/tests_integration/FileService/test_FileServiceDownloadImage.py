import os
from tempfile import TemporaryDirectory

import pytest
from fastapi.testclient import TestClient

from file_service import app, service

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_test_directories():
    with TemporaryDirectory() as tmp_image:
        original_image_dir = service.image_dir
        service.image_dir = tmp_image
        yield
        service.image_dir = original_image_dir

def create_test_image_file(image_id: str):
    image_file_path = os.path.join(service.image_dir, f"{image_id}.jpg")
    # Create a temporary image file
    with open(image_file_path, 'wb') as f:
        f.write(b"Fake image data")
    return image_file_path

def test_download_image_success(setup_test_directories):
    image_id = "test_image"
    image_file_path = create_test_image_file(image_id)
    response = client.get(f"/download/image?id={image_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    # Additional checks can be added here to validate the response content

def test_download_image_not_found(setup_test_directories):
    image_id = "nonexistent_image"
    response = client.get(f"/download/image?id={image_id}")
    assert response.status_code == 404

def test_download_image_invalid_id():
    response = client.get("/download/image?id=")
    assert response.status_code == 400