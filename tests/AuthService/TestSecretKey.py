import asyncio
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from classes.services.AuthService import AuthService


class TestSecretKey(unittest.IsolatedAsyncioTestCase):
    """
    TestSecretKey
    =============

    This class is used to test the `get_secret_key` method in the `AuthService` class. It contains two test methods: `test_get_secret_key_success` and `test_get_secret_key_with_exception
    *`.

    Test Methods:
    -------------
    - `test_get_secret_key_success(mock_service_exception_handling, mock_json_load)`:
        This method tests the success scenario of the `get_secret_key` method. It mocks the necessary dependencies and verifies the correctness of the method's behavior.
        Parameters:
            - `mock_service_exception_handling`: Patched version of the `service_exception_handling` method.
            - `mock_json_load`: Patched version of the `json.load` method.

    - `test_get_secret_key_with_exception(mock_logger_error, mock_service_exception_handling)`:
        This method tests the scenario where an exception is raised during the execution of the `get_secret_key` method. It mocks the necessary dependencies and checks the error handling
    * and recovery.
        Parameters:
            - `mock_logger_error`: Patched version of the `logging.Logger.error` method.
            - `mock_service_exception_handling`: Patched version of the `service_exception_handling` method.
    """
    @patch('builtins.open', unittest.mock.mock_open(read_data='{"main_service_url": "http://example.com"}'))
    @patch('json.load', return_value={'main_service_url': 'http://example.com'})
    @patch('classes.services.AuthService.AuthService.service_exception_handling', new_callable=AsyncMock)
    async def test_get_secret_key_success(self, mock_service_exception_handling, mock_json_load):
        # Mocking the service_exception_handling method to return the mocked secret key
        mock_secret_key = [{"secret_key": "mocked_secret_key"}]
        mock_service_exception_handling.return_value = mock_secret_key

        # Calling the method under test
        secret_key = await AuthService().get_secret_key()

        # Assertions
        mock_service_exception_handling.assert_awaited_once_with("http://example.com", "secret_key", "GET")
        self.assertEqual(secret_key, "mocked_secret_key")
    @patch('builtins.open', unittest.mock.mock_open(read_data='{"main_service_url": "http://example.com"}'))
    @patch('classes.services.AuthService.AuthService.service_exception_handling', new_callable=AsyncMock)
    @patch('logging.Logger.error')  # Patching the logging.Logger.error directly
    async def test_get_secret_key_with_exception(self, mock_logger_error, mock_service_exception_handling):
        # Configure the mock to raise an exception on the first call
        # Then return a successful response on the second call
        mock_service_exception_handling.side_effect = [Exception("Mock exception"), [{"secret_key": "mocked_secret_key"}]]

        # Instantiate AuthService and attempt to get the secret key
        service = AuthService()
        secret_key = await service.get_secret_key()

        # Assertions
        # Check that the logger.error was called with the expected message
        mock_logger_error.assert_called_with(f"An error occurred while getting secret key: Mock exception")

        # Check that the secret key is as expected after recovery from the exception
        self.assertEqual(secret_key, "mocked_secret_key")

        # Verify that service_exception_handling was called twice
        # First for the exception, then for the successful retrieval
        self.assertEqual(mock_service_exception_handling.call_count, 2)
