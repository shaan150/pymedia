import asyncio
import hashlib
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import UploadFile  # Assuming UploadFile is from FastAPI

from classes.services.ClientService import ClientService, ServiceType, logger



class TestClientService(unittest.IsolatedAsyncioTestCase):

    # Corrected test method with properly ordered mock arguments

    @patch('os.path.isdir', return_value=True)  # 4th mock parameter, thus 'mock_isdir'
    @patch('builtins.open', unittest.mock.mock_open(
        read_data='{"main_service_url": "http://example.com"}'))  # 3rd mock parameter, thus 'mock_open'
    @patch("fastapi.UploadFile.seek", new_callable=AsyncMock)  # 2nd mock parameter, thus 'mock_seek'
    @patch("fastapi.UploadFile.read", new_callable=AsyncMock,
           side_effect=[b"test data", b"", b""])  # 1st mock parameter, thus 'mock_read'
    async def test_calculate_md5(self, mock_read, mock_seek, mock_open):
        # Now, the method signature correctly reflects all mock objects in reverse order.
        client_service = ClientService()

        # Since UploadFile is a complex object, we'll use AsyncMock directly to simulate it.
        mock_upload_file = AsyncMock()
        mock_upload_file.read = mock_read
        mock_upload_file.seek = mock_seek

        # Call the method under test
        result = await client_service.calculate_md5(mock_upload_file)

        # Assertions
        expected_md5 = hashlib.md5(b"test data").hexdigest()
        self.assertEqual(result, expected_md5)
        mock_upload_file.seek.assert_awaited_with(0)
    @patch('os.path.isdir', return_value=True)  # 4th mock parameter, thus 'mock_isdir'
    @patch('builtins.open', unittest.mock.mock_open(
        read_data='{"main_service_url": "http://example.com"}'))  # 3rd mock parameter, thus 'mock_open'
    @patch("fastapi.UploadFile.seek", new_callable=AsyncMock)  # 2nd mock parameter, thus 'mock_seek'
    @patch("fastapi.UploadFile.read", new_callable=AsyncMock,
           side_effect=[b"test data", b"", b""])  # 1st mock parameter, thus 'mock_read'
    @patch("classes.services.ClientService.ClientService.get_optimal_service_instance")
    @patch("classes.services.ClientService.logger")
    async def test_is_optimal_service_success(self, mock_logger, mock_get_optimal_service_instance, mock_read,
                                              mock_seek, mock_open):
        # Mock the get_optimal_service_instance to return a simulated successful response
        mock_get_optimal_service_instance.return_value = [{"url": "http://optimal-service-url"}]
        service = ClientService()
        # Call the method under test
        result = await service.is_optimal_service()

        # Verify the result
        self.assertEqual(result, "http://optimal-service-url")

    @patch('os.path.isdir', return_value=True)  # 4th mock parameter, thus 'mock_isdir'
    @patch('builtins.open', unittest.mock.mock_open(
        read_data='{"main_service_url": "http://example.com"}'))  # 3rd mock parameter, thus 'mock_open'
    @patch("fastapi.UploadFile.seek", new_callable=AsyncMock)  # 2nd mock parameter, thus 'mock_seek'
    @patch("fastapi.UploadFile.read", new_callable=AsyncMock,
           side_effect=[b"test data", b"", b""])  # 1st mock parameter, thus 'mock_read'
    @patch("classes.services.ClientService.ClientService.get_optimal_service_instance")
    @patch("classes.services.ClientService.logger")
    async def test_is_optimal_service_exception(self, mock_logger, mock_get_optimal_service_instance, mock_read,
                                              mock_seek, mock_open):
        # Simulate an exception being raised by get_optimal_service_instance
        mock_get_optimal_service_instance.side_effect = Exception("Test exception")
        service = ClientService()
        # Call the method under test
        result = await service.is_optimal_service()

        # Verify the logger was called with the correct error message
        mock_logger.error.assert_called_with("Failed to update Service URL: Test exception")

        # Assuming self.service_url is defined and has a fallback value
        self.assertEqual(result, service.service_url)
