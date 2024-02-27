import socket
import unittest
from unittest.mock import patch
from utils.service_utils import get_local_ip  # Adjust import path

class TestUtilityFunctions(unittest.TestCase):
    def test_get_local_ip(self):

        ip = get_local_ip()
        self.assertEqual(ip, socket.gethostbyname(socket.gethostname()))