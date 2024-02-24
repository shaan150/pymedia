from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from classes.enum.ServiceType import ServiceType

class TestExtendedServiceInitialization(IsolatedAsyncioTestCase):
    @patch('classes.services.ExtendedService.get_main_service_url', return_value='http://example.com')
    @patch('builtins.input', return_value='')  # Mock input to simulate pressing enter
    def test_initialization(self, mocked_input, mocked_get_url):
        from classes.services.ExtendedService import ExtendedService
        service = ExtendedService(ServiceType.CLIENT_SERVICE)
        self.assertEqual(service.main_service_url, 'http://example.com')