import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from classes.exception.FailedServiceCreationException import FailedServiceCreationException
from classes.services.MainService import MainService
from classes.enum.ServiceType import ServiceType
from classes.ServiceInfo import ServiceInfo  # Adjust the import path if necessary
from classes.exception.NoAvailableServicesException import NoAvailableServicesException
from classes.exception.InvalidServiceException import InvalidServiceException

@pytest.fixture
def service_instance():
    return MainService()

@pytest.fixture
def service_type_file():
    return ServiceType.FILE_SERVICE

@pytest.fixture
def service_type_db():
    return ServiceType.DATABASE_SERVICE

@pytest.fixture
def service_type_invalid():
    return "invalid_service_type"

@pytest.mark.asyncio
async def test_get_service_file_service_available(service_instance, service_type_file):
    with patch('classes.services.MainService.MainService.create_new_instance', new_callable=MagicMock) as mock_create_new_instance:
        # Mocking the create_new_instance method to return a dummy service
        mock_service = MagicMock()
        mock_service.type = service_type_file.name
        service_instance.services = {"service1": mock_service}

        result = await service_instance.get_service(service_type_file)
        assert result == mock_service

@pytest.mark.asyncio
async def test_get_service_no_available_services(service_instance, service_type_file):
    with patch('classes.services.MainService.MainService.get_optimal_service_instance', new_callable=AsyncMock) as mock_get_optimal_service_instance:
        # Mocking the get_optimal_service_instance method to return None asynchronously
        mock_get_optimal_service_instance.return_value = None

        with pytest.raises(FailedServiceCreationException):
            await service_instance.get_service(service_type_file)
@pytest.mark.asyncio
async def test_get_service_invalid_service_type(service_instance, service_type_invalid):
    with pytest.raises(TypeError):
        await service_instance.get_service(service_type_invalid)

@pytest.mark.asyncio
async def test_get_service_none_service_type(service_instance):
    with pytest.raises(InvalidServiceException):
        await service_instance.get_service(None)