from database_service import app
from fastapi.testclient import TestClient
import os


from tests.tests_integration.DatabaseService.database_service_utils import (mock_get_user, mock_get_user_failure,
                                                                      mock_get_user_exception)

os.environ["DEBUG"] = "True"
client = TestClient(app)


def test_database_service_get_user_success(mock_get_user):
    response = client.get("/users/user", params={"username": "testuser"})
    assert response.status_code == 200

def test_database_service_get_user_failure(mock_get_user_failure):
    response = client.get("/users/user", params={"username": "testuser"})
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_database_service_get_user_exception(mock_get_user_exception):
    response = client.get("/users/user", params={"username": "testuser"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}