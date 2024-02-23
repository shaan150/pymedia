import asyncio
import unittest

from classes.services.BaseService import BaseService, ServiceType


class TestBaseServiceInitialization(unittest.TestCase):
    """
    Test class for initializing the BaseService.
    """
    def test_initialization(self):
        service_type = ServiceType.MAIN_SERVICE  # Replace YOUR_SERVICE_TYPE with actual value
        service = BaseService(service_type=service_type)

        self.assertEqual(service.service_type, service_type)
        self.assertEqual(service.properties_file, "service_properties.json")
        self.assertIsNotNone(service.app)
        self.assertIsInstance(service.services_lock, asyncio.Lock)
        self.assertEqual(service.algorithm, "HS256")