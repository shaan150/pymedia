import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from classes.services.MainService import MainService


class TestMainServiceCheckServices(unittest.TestCase):

    async def perform_service_check(self, service):
        # Mock the perform_service_check method
        pass

    async def test_check_services(self):
        # Mock the necessary objects and functions
        service1 = MagicMock()
        service1.name = "Service1"
        service1.last_update = datetime.now()

        service2 = MagicMock()
        service2.name = "Service2"
        service2.last_update = datetime.now()

        mock_self = MagicMock()
        mock_self.services = {1: service1, 2: service2}
        mock_self.services_lock = MagicMock()

        # Set the time difference to be greater than 60 seconds for service1
        service1.last_update = datetime.now() - timedelta(seconds=61)

        with patch('asyncio.sleep') as mock_sleep, patch('asyncio.gather') as mock_gather:
            # Call the method under test
            await MainService().check_services(mock_self)

            # Assertions
            mock_gather.assert_called_once()  # Ensure asyncio.gather is called
            mock_sleep.assert_called_once_with(100)  # Ensure asyncio.sleep is called with the correct argument


if __name__ == '__main__':
    unittest.main()
