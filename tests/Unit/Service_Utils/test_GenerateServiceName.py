import unittest
from utils.service_utils import generate_service_name  # Adjust import path
from classes.enum.ServiceType import ServiceType  # Adjust import path if needed

class TestGenerateServiceName(unittest.TestCase):
    def test_generate_service_name_format(self):
        service_name = generate_service_name(ServiceType.MAIN_SERVICE)  # Example usage
        self.assertTrue(isinstance(service_name, str))
        self.assertTrue(service_name.startswith(ServiceType.MAIN_SERVICE.name))