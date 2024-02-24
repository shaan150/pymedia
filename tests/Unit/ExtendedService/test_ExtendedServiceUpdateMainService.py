import asyncio
import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, AsyncMock

from classes.enum.ServiceType import ServiceType
from classes.services.ExtendedService import ExtendedService


class TestUpdateMainService(IsolatedAsyncioTestCase):
    @patch('builtins.open', unittest.mock.mock_open(
        read_data='{"main_service_url": "http://example.com"}'))
    @patch('classes.services.ExtendedService.ExtendedService.service_exception_handling', new_callable=AsyncMock)
    async def test_update_main_service(self, mock_service_exception_handling):
        service = ExtendedService(ServiceType.CLIENT_SERVICE)

        # Start the update_main_service task
        update_task = asyncio.create_task(service.update_main_service())

        try:
            # Wait for 10 seconds or until the task completes, whichever comes first
            await asyncio.wait_for(update_task, timeout=1)
        except asyncio.TimeoutError:
            # If a timeout occurs, it means the task didn't finish within 10 seconds
            pass

        # Cancel the task to ensure it doesn't continue running after the test
        update_task.cancel()
        try:
            # Wait for the task cancellation to complete
            await update_task
        except asyncio.CancelledError:
            # Task was cancelled, ignore the error
            pass

        # Assertions
        mock_service_exception_handling.assert_called()