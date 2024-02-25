from unittest.mock import MagicMock

import pytest
from fastapi.exceptions import HTTPException

from classes.ServiceInfo import ServiceInfo
from classes.services.MainService import MainService


class TestMainServiceVerifyIP:
    class TestVerifyIP:
        @pytest.mark.asyncio
        async def test_verify_ip_allowed(self, monkeypatch):
            # Assuming you have a way to mock request.client.host to return a mock IP
            request = self.MockRequest('192.168.1.1')  # Adjust MockRequest to your mocking strategy

            service_instance = MainService()
            monkeypatch.setattr(service_instance, 'services', {
                'some_service': ServiceInfo(name="some_service", service_type="some_type", url="192.168.1.1:1256")})

            try:
                await service_instance.verify_ip(request)
            except HTTPException:
                pytest.fail("Unexpected HTTPException raised")

        @pytest.mark.asyncio
        async def test_verify_ip_forbidden(self, monkeypatch):
            request = self.MockRequest('10.10.10.10')  # Non-allowed IP

            service_instance = MainService()
            monkeypatch.setattr(service_instance, 'services', {'some_service': ServiceInfo(name="some_service", service_type="some_type", url="0.0.0.0:0000")})

            with pytest.raises(HTTPException) as exc_info:
                await service_instance.verify_ip(request)
            assert exc_info.value.status_code == 403

        def MockRequest(self, ip_address):
            request = MagicMock()
            request.client.host = ip_address
            return request