import os
import socket
from unittest import IsolatedAsyncioTestCase, mock
from unittest.mock import patch, MagicMock

from classes.services.BaseService import BaseService, ServiceType


class TestBaseServiceStartBackgroundTasks(IsolatedAsyncioTestCase):
    os.environ["DEBUG"] = "False"
    """

    TestBaseServiceStartBackgroundTasks

    This class is responsible for testing the functionality of the `start_background_tasks` method in the `BaseService` class.

    The `start_background_tasks` method starts the background tasks associated with the service. It sets up a socket connection and retrieves the local IP address and port number from a
    * mock file. It then sets the `service_url` attribute of the `BaseService` instance to the constructed URL using the obtained IP address and port number.

    Attributes:
        - None

    Methods:
        - `test_start_background_tasks`: Test method that mocks the necessary dependencies and verifies the correct behavior of the `start_background_tasks` method.

    Example usage:
        ```python
        test = TestBaseServiceStartBackgroundTasks()
        test.test_start_background_tasks()
        ```

    """
    @patch('builtins.open', mock.mock_open(read_data='{"main_service": "8080"}'))
    @patch('socket.socket')
    async def test_start_background_tasks(self, mock_socket):
        os.environ["DEBUG"] = "False"
        mock_socket_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance

        # Setup mock IP address
        mock_local_ip = socket.gethostbyname(socket.gethostname())

        # Directly mock __getitem__ on the return value of getsockname() to return the mock IP
        mock_socket_instance.getsockname.return_value.__getitem__.side_effect = lambda x: mock_local_ip if x == 0 else None

        service = BaseService(service_type=ServiceType.MAIN_SERVICE)
        await service.start_background_tasks()

        expected_url = f"{mock_local_ip}:8080"
        self.assertEqual(service.service_url, expected_url)