import unittest
from unittest.mock import patch, AsyncMock

from fastapi import HTTPException
from httpx import HTTPStatusError

from classes.services.BaseService import BaseService, ServiceType


class test_BaseServiceExceptionHandling(unittest.IsolatedAsyncioTestCase):
    @patch('utils.service_utils.handle_rest_request', new_callable=AsyncMock)
    async def test_service_exception_handling_http_exception(self, mock_handle_rest_request):
        mock_handle_rest_request.side_effect = HTTPStatusError(message="Error", request=None, response=None)
        service = BaseService(service_type=ServiceType.MAIN_SERVICE)

        with self.assertRaises(HTTPException):
            await service.service_exception_handling("http://example.com", "endpoint", "GET")