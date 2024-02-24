import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock

from classes.enum.ServiceType import ServiceType


class TestFetchServiceData(IsolatedAsyncioTestCase):
    @patch('builtins.open', unittest.mock.mock_open(
        read_data='{"main_service_url": "http://example.com"}'))
    @patch('psutil.Process')
    async def test_fetch_service_data(self, mocked_process):
        mocked_process.return_value.memory_info.return_value.rss = 1024 ** 3  # 1 GB
        mocked_process.return_value.cpu_percent.return_value = 50
        # Mock other psutil functions as needed
        from classes.services.ExtendedService import ExtendedService
        service = ExtendedService(ServiceType.CLIENT_SERVICE)
        data = await service.fetch_service_data()
        self.assertEqual(data['memory_usage'], 1024)  # Assuming RSS is converted to MB
        self.assertEqual(data['cpu_usage'], 50)