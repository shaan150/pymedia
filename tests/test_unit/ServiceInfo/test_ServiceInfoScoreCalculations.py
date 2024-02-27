import unittest
from unittest import IsolatedAsyncioTestCase

from classes.ServiceInfo import ServiceInfo
from classes.enum.ServiceType import ServiceType



# Use IsolatedAsyncioTestCase for testing async functions
class TestServiceInfoScoreCalculations(IsolatedAsyncioTestCase):

    async def test_calc_score(self):
        service_info = ServiceInfo(
            name="test-service",
            service_type=ServiceType.DATABASE_SERVICE.name,
            url="http://example.com",
            cpu_usage=60,
            memory_usage=1024,
            memory_free=4096,
            total_memory=5120,
            cpu_free=40
        )

        calculated_score = await service_info.calc_score()

        expected_score = ( (60 * 0.65) + ((1024/4096) * 100 * 0.35)) / 100
        self.assertEqual(calculated_score, expected_score)  # Allow for floating-point precision

    async def test_calc_available_score(self):
        service_info = ServiceInfo(
            name="test-service",
            service_type=ServiceType.DATABASE_SERVICE.name,
            url="http://example.com",
            cpu_usage=60,
            memory_usage=1024,
            memory_free=4096,
            total_memory=5120,
            cpu_free=40
        )

        calculated_score = await service_info.calc_available_score()

        # Ensure the calculation matches your expectation
        expected_score = ((40 * 0.65) + ((4096/5120) * 100 * 0.35)) / 100
        self.assertEqual(calculated_score, expected_score)