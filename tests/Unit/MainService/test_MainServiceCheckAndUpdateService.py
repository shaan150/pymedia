import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from httpx import HTTPStatusError

from classes.ServiceInfo import ServiceInfo
from classes.enum.ServiceType import ServiceType
from classes.services.BaseService import BaseService
from classes.services.MainService import MainService
from fastapi import HTTPException



class test_MainServiceCheckAndUpdateService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.instance = MainService() # Adjust based on actual constructor
        self.service = ServiceInfo(name="TestService", url="http://example.com", service_type=ServiceType.FILE_SERVICE)  # Adjust based on actual constructor

    @patch("classes.services.MainService.logger")
    @patch("classes.services.MainService.MainService.service_exception_handling")
    async def test_service_online(self, mock_service_exception_handling, mock_logger):
        # Mock service_exception_handling to simulate service being online
        mock_response = AsyncMock(status_code=200)
        mock_service_exception_handling.return_value = mock_response

        # Perform the test
        result = await self.instance.check_and_update_service(self.service)

        # Assertions
        self.assertTrue(result)
        mock_logger.info.assert_called_with(f"Service {self.service.name} online.")
        self.assertIsInstance(self.service.last_update, datetime)  # Assuming last_update should be a

    @patch("classes.services.MainService.logger")
    @patch("classes.services.MainService.MainService.service_exception_handling")
    async def test_service_offline_http_status_error(self, mock_service_exception_handling, mock_logger):
        # Mock service_exception_handling to raise HTTPStatusError
        mock_service_exception_handling.side_effect = HTTPStatusError("Error message", response=AsyncMock(status_code=404, text="Not found"), request=AsyncMock(url="http://example.com"))

        # Perform the test
        result = await self.instance.check_and_update_service(self.service)

        # Assertions
        self.assertFalse(result)
        mock_logger.error.assert_called_with(f"Service {self.service.name} returned status code 404. With Error: Not found")

    @patch("classes.services.MainService.logger")
    @patch("classes.services.MainService.MainService.service_exception_handling")
    async def test_service_offline_generic_exception(self, mock_service_exception_handling, mock_logger):
        # Mock service_exception_handling to raise a generic exception
        mock_service_exception_handling.side_effect = Exception("Generic error")

        # Perform the test
        result = await self.instance.check_and_update_service(self.service)

        # check that an error was logged
        mock_logger.error.assert_called_with(f"Failed to check and update service {self.service.name}: Generic error")