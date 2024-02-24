import unittest
from unittest import mock
from unittest.mock import patch, AsyncMock, MagicMock

from classes.services.MainService import MainService


class TestMainServiceStartBackgroundTasks(unittest.IsolatedAsyncioTestCase):
    """
    TestMainServiceStartBackgroundTasks

    This class defines unit tests for the start_background_tasks() method of the TestMainServiceStartBackgroundTasks class.

    Methods:
    - test_start_background_tasks: Tests the start_background_tasks() method.

    """
    @patch('builtins.open', mock.mock_open(read_data='{"main_service": "8080"}'))
    @patch('socket.socket')
    @patch('classes.services.MainService.MainService.setup_services', new_callable=AsyncMock)
    @patch('classes.services.MainService.MainService.check_services', new_callable=AsyncMock)
    async def test_start_background_tasks(self, mock_socket, mock_check_services, mock_setup_services):
        mock_socket_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance

        # Setup mock IP address
        mock_local_ip = '192.168.1.100'

        # Directly mock __getitem__ on the return value of getsockname() to return the mock IP
        mock_socket_instance.getsockname.return_value.__getitem__.side_effect = lambda x: mock_local_ip if x == 0 else None

        service = MainService()
        await service.start_background_tasks()

        mock_setup_services.assert_called_once()
        mock_check_services.assert_called_once()
        self.assertEqual(len(service.tasks), 2)  # Assuming 2 tasks are created