import os
import unittest
from unittest.mock import patch, mock_open
from utils.service_utils import get_property, MissingPropertyException


class TestGetProperty(unittest.TestCase):
    @patch('json.load', return_value={'valid_property': None})
    @patch('builtins.open', new_callable=mock_open, read_data='{"valid_property": null}')
    def test_property_found_with_no_value(self, mock_file, mock_json_load):
        with self.assertRaises(MissingPropertyException) as cm:
            get_property("valid_property", "valid_path.json")
        self.assertEqual(str(cm.exception), "valid_property found with no value in valid_path.json")

    def test_invalid_arguments_raise_value_error(self):
        with self.assertRaises(ValueError):
            get_property(None, "valid_path.json")
        with self.assertRaises(ValueError):
            get_property("valid_property", None)

    @patch('json.load', return_value={'valid_property': 'value'})
    @patch('builtins.open', new_callable=mock_open, read_data='{"valid_property": "value"}')
    def test_get_property_success(self, mock_file, mock_json_load):
        value = get_property("valid_property", "valid_path.json")
        self.assertEqual(value, "value")
