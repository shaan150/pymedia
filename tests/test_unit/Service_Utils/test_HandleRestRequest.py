import unittest
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from utils.service_utils import handle_rest_request, httpx


class TestHandleRestRequest(unittest.IsolatedAsyncioTestCase):
    # Mocking the httpx.AsyncClient for testing purposes
    @patch('utils.service_utils.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_handle_rest_request(self, mock_client):
        # Mocking the response object
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_error = False
        mock_response.json.return_value = {'key': 'value'}

        # Setting up the mock client to return the mock response
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value.put.return_value = mock_response
        mock_client.return_value.__aenter__.return_value.delete.return_value = mock_response

        # Testing the POST method
        response = await handle_rest_request("example.com", "endpoint", "POST", data={'key': 'value'})
        assert response == ({'key': 'value'}, 200)

        # Testing the GET method
        response = await handle_rest_request("example.com", "endpoint", "GET")
        assert response == ({'key': 'value'}, 200)

        # Testing the PUT method
        response = await handle_rest_request("example.com", "endpoint", "PUT", data={'key': 'value'})
        assert response == ({'key': 'value'}, 200)

        # Testing the DELETE method
        response = await handle_rest_request("example.com", "endpoint", "DELETE")
        assert response == ({'key': 'value'}, 200)

        # Testing the case where response status code is not 500 or 503
        mock_response.status_code = 404
        mock_response.json.return_value = {'detail': 'Not Found'}
        mock_response.is_error = True

        with pytest.raises(HTTPException) as exc_info:
            await handle_rest_request("example.com", "endpoint", "GET")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == 'Not Found'