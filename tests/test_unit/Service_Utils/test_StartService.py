from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, AsyncMock
from classes.enum.ServiceType import ServiceType
from classes.exception.FailedServiceCreationException import FailedServiceCreationException
from utils.service_utils import start_service  # Adjust the import path to your module


class TestStartService(IsolatedAsyncioTestCase):
    @patch('utils.service_utils.asyncio.create_subprocess_exec', new_callable=AsyncMock)
    async def test_start_service_success(self, mock_subprocess):
        # Setup the mock to simulate a successful subprocess execution
        mock_subprocess.return_value = AsyncMock()

        # Assume these are correctly set in your context
        main_service_url = "http://main-service.com"
        service_type = ServiceType.FILE_SERVICE  # or any valid ServiceType enum

        await start_service(main_service_url, service_type)

        # Verify the subprocess was called with the expected command
        mock_subprocess.assert_called_once()

    @patch('utils.service_utils.asyncio.create_subprocess_exec')
    async def test_start_service_value_error(self, mock_subprocess):
        # Test the function with invalid parameters to trigger a ValueError
        with self.assertRaises(ValueError):
            await start_service(None, None)

    @patch('utils.service_utils.asyncio.create_subprocess_exec')
    async def test_start_service_failed_service_creation_exception(self, mock_subprocess):
        # Setup the mock to raise an exception, simulating a failure in subprocess execution
        mock_subprocess.side_effect = Exception("Subprocess failed")

        main_service_url = "http://main-service.com"
        service_type = ServiceType.MAIN_SERVICE  # Adjust as needed

        # Verify that the custom exception is raised when the subprocess fails
        with self.assertRaises(FailedServiceCreationException) as context:
            await start_service(main_service_url, service_type)

        self.assertIn("Failed to start new instance", str(context.exception))