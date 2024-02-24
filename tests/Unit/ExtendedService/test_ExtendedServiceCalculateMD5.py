import asyncio
import hashlib
import io
import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, AsyncMock

from classes.enum.ServiceType import ServiceType
from classes.services.ExtendedService import ExtendedService
class TestCalculateMD5(IsolatedAsyncioTestCase):

    @patch('builtins.open', unittest.mock.mock_open(
        read_data='{"main_service_url": "http://example.com"}'))
    @patch('aiofiles.open', new_callable=MagicMock)
    async def test_calculate_md5_error(self, mock_aiofiles_open):
        # Simulate an exception raised from aiofiles.open
        mock_aiofiles_open.side_effect = Exception('Simulated file error')

        your_instance = ExtendedService(ServiceType.DATABASE_SERVICE)

        with self.assertRaises(Exception) as context:  # Check for raised exception
            await your_instance.calculate_md5('mock_filepath')

        self.assertEqual(str(context.exception), 'Simulated file error')  # Check exception message
