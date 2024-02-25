import os

from fastapi.testclient import TestClient

from classes.ServiceInfo import ServiceInfo
from main_service import app
import pytest
from unittest.mock import patch, AsyncMock


os.environ["DEBUG"] = "True"
client = TestClient(app)

@pytest.fixture
def mock_service_info():
    service_info_mock = AsyncMock(spec=ServiceInfo)
    service_info_mock.name = "Test Service"
    service_info_mock.calc_score.return_value = 100
    service_info_mock.calc_available_score.return_value = 95
    service_info_mock.to_dict.return_value = {"name": "Test Service", "other_details": {}}

    services_mock = {"http://example.com": service_info_mock}

    with patch("main_service.service.services", services_mock):
        yield services_mock


@pytest.fixture
def mock_service_info_exception():
    with patch("main_service.service.services", new_callable=AsyncMock) as services_mock:
        async def raise_exception(*args, **kwargs):
            raise Exception("Test Exception")

        service_info_mock = AsyncMock(spec=ServiceInfo)
        service_info_mock.calc_score.side_effect = raise_exception
        service_info_mock.calc_available_score.side_effect = raise_exception

        services_mock.return_value = {"http://example.com": service_info_mock}
        yield services_mock
def test_debug_endpoint(mock_service_info):
    response = client.get("/debug")
    assert response.status_code == 200
    response_data = response.json()

    # Validate the structure of the response
    assert "services" in response_data
    assert "services_with_scores" in response_data
    assert "services_with_availability" in response_data

    # Validate the content of the response based on mocked data
    assert response_data["services"]["http://example.com"]["name"] == "Test Service"
    assert response_data["services_with_scores"]["http://example.com"] == 100
    assert response_data["services_with_availability"]["http://example.com"] == 95

def test_debug_endpoint_service_exception(mock_service_info_exception):
    response = client.get("/debug")
    assert response.status_code == 500
    assert "Error fetching service data" in response.json()["detail"]