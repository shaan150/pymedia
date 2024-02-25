import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

import pytest

from classes.services.MainService import MainService, ServiceType
from classes.ServiceInfo import ServiceInfo

class TestMainServiceSelectOptimalService(unittest.IsolatedAsyncioTestCase):
    async def test_select_optimal_service_new_instance(self):
        service_type = ServiceType.FILE_SERVICE
        mock_self = MagicMock()
        mock_self.services_lock = AsyncMock()
        mock_self.services = {}
        mock_self.create_new_instance = AsyncMock(return_value="http://test-service-url")

        result = await MainService.select_optimal_service(mock_self, service_type)

        mock_self.create_new_instance.assert_called_once_with(service_type, False)
        self.assertEqual(result, "http://test-service-url")

    @pytest.mark.asyncio
    async def test_select_optimal_service_existing_instance(self):
        service_type = ServiceType.FILE_SERVICE
        mock_self = MainService()
        mock_self.services_lock = asyncio.Lock()
        mock_self.services = {
            "service1": ServiceInfo("service1", service_type=ServiceType.FILE_SERVICE.name, url="http://service1-url",
                                    cpu_usage=0, memory_usage=0, memory_free=100, total_memory=100, cpu_free=100),
            "service2": ServiceInfo("service2", service_type=ServiceType.FILE_SERVICE.name, url="http://service2-url",
                                    cpu_usage=1, memory_usage=0, memory_free=100, total_memory=100, cpu_free=100)
        }

        # Mock calc_score to return specific scores
        for service in mock_self.services.values():
            service.calc_score = AsyncMock(return_value=0.05)

        mock_self.create_new_instance = AsyncMock()

        result = await MainService.select_optimal_service(mock_self, service_type)

        # Assert that create_new_instance was not called
        mock_self.create_new_instance.assert_not_called()

        # Assert that the service with the lowest score was returned
        self.assertEqual(result, mock_self.services["service1"])

    # Add more test cases for edge cases, exceptions, etc.


if __name__ == '__main__':
    unittest.main()
