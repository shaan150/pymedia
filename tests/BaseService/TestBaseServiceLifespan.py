import unittest
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException, FastAPI
from httpx import HTTPStatusError

from classes.services.BaseService import BaseService, ServiceType


class TestBaseServiceLifespan(unittest.IsolatedAsyncioTestCase):
    """
    Unit test class for testing the lifespan of BaseService.

    Methods:
    - test_lifespan: Test the lifespan of BaseService.

    Attributes:
    - mock_stop: Mock object for BaseService stop method.
    - mock_start_background_tasks: Mock object for BaseService start_background_tasks method.
    - service: BaseService instance for testing.
    """
    @patch.object(BaseService, 'start_background_tasks', new_callable=AsyncMock)
    @patch.object(BaseService, 'stop', new_callable=AsyncMock)
    async def test_lifespan(self, mock_stop, mock_start_background_tasks):
        service = BaseService(service_type=ServiceType.MAIN_SERVICE)
        async with service.app.router.lifespan_context(FastAPI()):
            pass

        mock_start_background_tasks.assert_awaited_once()
        mock_stop.assert_awaited_once()
