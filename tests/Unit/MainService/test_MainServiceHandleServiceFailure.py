import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from classes.ServiceInfo import ServiceInfo
from classes.enum.ServiceType import ServiceType
from classes.exception.FailedServiceCreationException import FailedServiceCreationException
from classes.exception.NoAvailableServicesException import NoAvailableServicesException
from classes.services.MainService import MainService as ms

class TestMainServiceHandleServiceFailure(unittest.IsolatedAsyncioTestCase):
    async def test_service_replacement_success(self):
        """
        Test the case where a replacement service is successfully found and the failed service is deleted.
        """
        service = ServiceInfo(name="TestService", service_type=ServiceType.FILE_SERVICE, url="http://testurl.com")
        with patch('logging.Logger') as mock_logger, \
                patch('classes.services.MainService.MainService.get_optimal_service_instance', new_callable=AsyncMock) as mock_get_optimal_service, \
                patch('classes.services.MainService.MainService.del_service', new_callable=AsyncMock) as mock_del_service:
            mock_get_optimal_service.return_value = ServiceInfo(name="ReplacementService", service_type=ServiceType.FILE_SERVICE,
                                                                url="http://replacementurl.com")

            await ms().handle_service_failure(service)

            mock_get_optimal_service.assert_awaited_once_with(service.type)
            mock_del_service.assert_awaited_once_with(service.url)

    async def test_no_replacement_found(self):
        """
        Test the case where no replacement service is found, expecting NoAvailableServicesException.
        """
        service = ServiceInfo(name="TestService", service_type=ServiceType.FILE_SERVICE, url="http://testurl.com")
        with patch('logging.Logger') as mock_logger, \
                patch('classes.services.MainService.MainService.get_optimal_service_instance', new_callable=AsyncMock) as mock_get_optimal_service, \
                self.assertRaises(NoAvailableServicesException):
            mock_get_optimal_service.return_value = None

            await ms().handle_service_failure(service)

            mock_get_optimal_service.assert_awaited_once_with(service.type)
            mock_logger.error.assert_called_with("No replacement available for service TestService of type TestType.")

    async def test_failed_service_creation_exception(self):
        """
        Test the case where there is an issue starting a new instance of the service, expecting FailedServiceCreationException.
        """
        service = ServiceInfo(name="TestService", service_type=ServiceType.FILE_SERVICE, url="http://testurl.com")
        with patch('logging.Logger') as mock_logger, \
                patch('classes.services.MainService.MainService.get_optimal_service_instance', new_callable=AsyncMock) as mock_get_optimal_service, \
                self.assertRaises(FailedServiceCreationException):
            mock_get_optimal_service.side_effect = FailedServiceCreationException("Test failure")

            await ms().handle_service_failure(service)

            mock_get_optimal_service.assert_awaited_once_with(service.type)
            mock_logger.error.assert_called_with("Failed to start a new instance of TestType: Test failure")

    async def test_unexpected_exception(self):
        """
        Test the case where an unexpected exception is raised, expecting FailedServiceCreationException.
        """
        service = ServiceInfo(name="TestService", service_type=ServiceType.FILE_SERVICE, url="http://testurl.com")
        with patch('logging.Logger') as mock_logger, \
                patch('classes.services.MainService.MainService.get_optimal_service_instance', new_callable=AsyncMock) as mock_get_optimal_service, \
                self.assertRaises(FailedServiceCreationException):
            mock_get_optimal_service.side_effect = Exception("Unexpected error")

            await ms().handle_service_failure(service)

            mock_get_optimal_service.assert_awaited_once_with(service.type)
            mock_logger.error.assert_called_with(
                "Unexpected error handling failure of service TestService: Unexpected error")


if __name__ == "__main__":
    unittest.main()