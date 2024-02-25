import unittest

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from classes.services.MainService import MainService
from classes.enum.ServiceType import ServiceType
from classes.ServiceInfo import ServiceInfo  # Adjust the import path if necessary
from classes.exception.NoAvailableServicesException import NoAvailableServicesException
from classes.exception.InvalidServiceException import InvalidServiceException


class TestYourClass(unittest.TestCase):

    @patch('classes.services.MainService.MainService.select_optimal_service')
    async def test_get_optimal_service_instance_success(self, mock_select_optimal_service):
        # Mock the select_optimal_service method to return a mock service instance
        mock_service_instance = MagicMock()
        mock_select_optimal_service.return_value = mock_service_instance

        # Create an instance of YourClass
        instance = MainService()

        # Call the get_optimal_service_instance method with valid service type
        result = await instance.get_optimal_service_instance(ServiceType.FILE_SERVICE)

        # Assert that the method returns the mock service instance
        self.assertEqual(result, mock_service_instance)

    @patch('classes.services.MainService.MainService.select_optimal_service')
    async def test_get_optimal_service_instance_no_service_found(self, mock_select_optimal_service):
        # Mock the select_optimal_service method to return None
        mock_select_optimal_service.return_value = None

        # Create an instance of YourClass
        instance = MainService()

        # Call the get_optimal_service_instance method with valid service type
        result = await instance.get_optimal_service_instance(ServiceType.FILE_SERVICE)

        # Assert that the method returns None
        self.assertIsNone(result)

    async def test_get_optimal_service_instance_invalid_service_type(self):
        # Create an instance of YourClass
        instance = MainService()


        # Call the get_optimal_service_instance method with None service type
        with self.assertRaises(InvalidServiceException):
            await instance.get_optimal_service_instance(None)

if __name__ == '__main__':
    unittest.main()