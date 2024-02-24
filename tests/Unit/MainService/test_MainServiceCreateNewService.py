import unittest
from unittest.mock import MagicMock, patch
from classes.services.MainService import MainService

class TestCreateNewInstance(unittest.TestCase):

    @patch('classes.services.MainService.start_service')
    @patch('classes.services.MainService.handle_rest_request')
    @patch('classes.services.MainService.logger')
    @patch('classes.services.MainService.asyncio.gather')
    @patch('classes.services.MainService.ServiceType')
    async def test_create_new_instance(self, mock_service_type, mock_gather, mock_logger, mock_handle_rest_request, mock_start_service):
        # Mock necessary objects
        mock_service_type.return_value = MagicMock()
        mock_gather.return_value = [0.8, 0.6]  # Mock scores for services
        mock_logger.info = MagicMock()
        mock_logger.error = MagicMock()
        mock_start_service.return_value = MagicMock()
        mock_handle_rest_request.return_value = MagicMock()

        # Create an instance of YourClass
        instance = MainService()

        # Call the method with different scenarios
        await instance.create_new_instance(mock_service_type, existing_services=True)
        await instance.create_new_instance(mock_service_type, existing_services=False)

        # Assert that the expected methods were called
        mock_logger.info.assert_called()
        mock_logger.error.assert_not_called()  # Assuming no errors occurred in this test case
        mock_start_service.assert_called_once()
        mock_handle_rest_request.assert_called_once()

    # check for

if __name__ == '__main__':
    unittest.main()