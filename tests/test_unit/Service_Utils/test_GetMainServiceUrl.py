import unittest
from unittest.mock import patch
from utils.service_utils import get_main_service_url, MissingPropertyException  # Adjust import path

class TestGetMainServiceUrl(unittest.TestCase):
    @patch('utils.service_utils.get_property', side_effect=MissingPropertyException("main_service_url not found"))
    def test_get_main_service_url_exception(self, mock_get_property):
        with self.assertRaises(MissingPropertyException):
            get_main_service_url()

    @patch('utils.service_utils.get_property', return_value="http://main-service-url.com")
    def test_get_main_service_url_success(self, mock_get_property):
        url = get_main_service_url()
        self.assertEqual(url, "http://main-service-url.com")