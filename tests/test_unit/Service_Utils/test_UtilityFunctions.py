import unittest
from unittest.mock import patch
from utils.service_utils import get_local_ip  # Adjust import path

class TestUtilityFunctions(unittest.TestCase):
    @patch('socket.socket')
    def test_get_local_ip(self, mock_socket):
        mock_socket.return_value.__enter__.return_value.getsockname.return_value = ['192.168.1.1']

        ip = get_local_ip()
        self.assertEqual(ip, '192.168.1.1')