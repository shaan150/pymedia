import os
import unittest
import unittest.mock as mock
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock
from classes.services.ExtendedService import ExtendedService, ServiceType, InvalidServiceException

class TestExtendedServiceGetOptimalServiceInstance(IsolatedAsyncioTestCase):
    @mock.patch('classes.services.ExtendedService.ExtendedService.service_exception_handling', new_callable=AsyncMock)
    async def test_get_optimal_service_instance_success(self, mock_request):
        os.environ["DEBUG"] = "True"
        # Setup
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {'instance_data': '...'}  # Example response
        mock_request.return_value = mock_response

        your_instance = ExtendedService(ServiceType.FILE_SERVICE)  # Provide a valid URL

        # Call the method
        result = await your_instance.get_optimal_service_instance(ServiceType.DATABASE_SERVICE)

        # Assertions
        mock_request.assert_called_once_with(
            'http://localhost:8000',
            'get_service',
            'GET',
            params={'service_type': ServiceType.DATABASE_SERVICE.value}
        )

    @mock.patch('builtins.open', unittest.mock.mock_open(
        read_data='{"main_service_url": "http://example.com"}'))
    @mock.patch('classes.services.ExtendedService.ExtendedService.service_exception_handling', new_callable=AsyncMock)
    async def test_get_optimal_service_instance_no_url(self, mock_request):
        your_instance = ExtendedService(ServiceType.FILE_SERVICE)
        # raise InvalidServiceException from service_exception_handling
        mock_request.side_effect = InvalidServiceException("No Main Service URL Provided")

        with self.assertRaises(InvalidServiceException) as context:
            await your_instance.get_optimal_service_instance(ServiceType.DATABASE_SERVICE)

        self.assertIn("No Main Service URL Provided", str(context.exception))

    @mock.patch('builtins.open', unittest.mock.mock_open(
        read_data='{"main_service_url": "http://example.com"}'))
    @mock.patch('classes.services.ExtendedService.ExtendedService.service_exception_handling', new_callable=AsyncMock)
    async def test_get_optimal_service_instance_error(self, mock_request):
        mock_request.side_effect = Exception('Simulated error')

        your_instance = ExtendedService(ServiceType.FILE_SERVICE)

        with self.assertRaises(Exception) as context:
            await your_instance.get_optimal_service_instance(ServiceType.DATABASE_SERVICE)

        self.assertIn("Simulated error", str(context.exception))
