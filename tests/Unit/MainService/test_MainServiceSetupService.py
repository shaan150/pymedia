import unittest
from unittest.mock import patch, AsyncMock

from classes.exception.FailedServiceCreationException import FailedServiceCreationException
from classes.exception.NoAvailableServicesException import NoAvailableServicesException
from classes.services.MainService import MainService
from classes.services.MainService import ServiceType


@patch('classes.services.MainService.start_service', new_callable=AsyncMock)
class TestSetupService(unittest.IsolatedAsyncioTestCase):

    @patch('classes.services.MainService.MainService.wait_for_service', new_callable=AsyncMock)
    async def test_setup_service_success(self, mock_wait_for_service, mock_start_service):
        service = MainService()
        service.services = {}  # Assuming services is a dict; adjust as necessary

        mock_wait_for_service.return_value = True  # Simulate successful wait for service

        await service.setup_service(ServiceType.DATABASE_SERVICE)

        mock_start_service.assert_awaited_once_with(service.service_url, ServiceType.DATABASE_SERVICE)
        mock_wait_for_service.assert_awaited_once()

    async def test_setup_service_failure(self, mock_start_service):
        mock_start_service.side_effect = Exception("Service start failed")  # Simulate failure

        service = MainService()

        with self.assertRaises(FailedServiceCreationException):
            await service.setup_service(ServiceType.DATABASE_SERVICE)

        mock_start_service.assert_awaited_once()

    @patch('classes.services.MainService.MainService.wait_for_service', new_callable=AsyncMock)
    async def test_no_available_services(self, mock_wait_for_service, mock_start_service):
        mock_wait_for_service.return_value = None  # Simulate no service available after wait

        service = MainService()

        with self.assertRaises(NoAvailableServicesException):
            await service.setup_service(ServiceType.DATABASE_SERVICE)

        mock_start_service.assert_awaited_once()
        mock_wait_for_service.assert_awaited_once()