import unittest
from unittest.mock import patch
from datetime import datetime

from classes.enum.ServiceType import ServiceType
from classes.ServiceInfo import ServiceInfo


class TestServiceInfoConstructor(unittest.TestCase):

    def test_constructor_with_valid_data(self):
        service_info = ServiceInfo(
            name="test-service",
            service_type=ServiceType.DATABASE_SERVICE,
            url="http://example.com",
            cpu_usage=45,
            memory_usage=2048,
            memory_free=3072,
            total_memory=5120,
            cpu_free=55
        )

        self.assertEqual(service_info.name, "test-service")
        self.assertEqual(service_info.type, ServiceType.DATABASE_SERVICE)
        self.assertEqual(service_info.url, "http://example.com")
        self.assertEqual(service_info.cpu_used, 45)
        self.assertEqual(service_info.memory_used, 2048)
        self.assertEqual(service_info.memory_free, 3072)
        self.assertEqual(service_info.total_memory, 5120)
        self.assertEqual(service_info.cpu_free, 55)

    @patch('datetime.datetime')
    def test_constructor_timestamp(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 12, 25, 10, 30, 0)  # Set a fixed time

        service_info = ServiceInfo(
            name="test-service",
            service_type=ServiceType.DATABASE_SERVICE,
            url="http://example.com",
            cpu_usage=45,
            memory_usage=2048,
            memory_free=3072,
            total_memory=5120,
            cpu_free=55
        )

        self.assertEqual(datetime.now(), service_info.last_update)