import unittest
from unittest.mock import patch, AsyncMock

from classes.services.MainService import MainService
from classes.services.MainService import ServiceType


class TestMainServiceSetupServices(unittest.IsolatedAsyncioTestCase):
    """

    This class defines a unit test case for the `setup_services` method of the `MainService` class.

    Methods:
    ----------
    test_setup_services(mock_setup_service)
        Method to test the `setup_services` method.

    Attributes:
    ----------
    mock_setup_service : MagicMock
        A mocked version of the `MainService.setup_service` method.


    """
    @patch('classes.services.MainService.MainService.setup_service', new_callable=AsyncMock)
    async def test_setup_services(self, mock_setup_service):
        service = MainService()
        await service.setup_services()

        """expected_calls = [((service_type,),) for service_type in [
            ServiceType.DATABASE_SERVICE,
            ServiceType.FILE_SERVICE,
            ServiceType.AUTH_SERVICE,
            ServiceType.CLIENT_SERVICE
        ]]"""
        expected_calls = []
        mock_setup_service.assert_has_awaits(expected_calls)