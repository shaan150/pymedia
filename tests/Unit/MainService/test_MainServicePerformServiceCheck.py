import unittest
from unittest.mock import MagicMock, patch

from classes.services.MainService import MainService


class TestMainServicePerformServiceCheck(unittest.TestCase):
    @patch('classes.services.MainService.MainService.check_and_update_service')
    @patch('classes.services.MainService.MainService.handle_service_failure')
    @patch('classes.services.MainService.MainService.get_optimal_service_instance')
    async def test_perform_service_check_conn_success(self, mock_get_optimal, mock_handle_failure, mock_check_update):
        my_service = MainService()
        service = MagicMock()
        mock_check_update.return_value = True
        mock_get_optimal.return_value = None

        await my_service.perform_service_check(service)

        mock_check_update.assert_called_once_with(service)
        mock_get_optimal.assert_called_once_with(service.type)
        mock_handle_failure.assert_not_called()

    @patch('classes.services.MainService.MainService.check_and_update_service')
    @patch('classes.services.MainService.MainService.handle_service_failure')
    @patch('classes.services.MainService.MainService.get_optimal_service_instance')
    async def test_perform_service_check_conn_failure(self, mock_get_optimal, mock_handle_failure, mock_check_update):
        my_service = MainService()
        service = MagicMock()
        mock_check_update.return_value = False

        await my_service.perform_service_check(service)

        mock_check_update.assert_called_once_with(service)
        mock_handle_failure.assert_called_once_with(service)
        mock_get_optimal.assert_not_called()


if __name__ == '__main__':
    unittest.main()
