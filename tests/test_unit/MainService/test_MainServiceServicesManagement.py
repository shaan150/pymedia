import unittest

import pytest

from classes.ServiceInfo import ServiceInfo
from classes.enum.ServiceType import ServiceType
from classes.services.MainService import MainService


class TestMainServiceServicesManagement:
    @pytest.mark.asyncio
    async def test_update_service_valid(self, monkeypatch):
        service_instance = MainService()
        service_info = ServiceInfo(name="TestService", service_type=ServiceType.FILE_SERVICE.name, url="http://example.com")

        # Assuming an update scenario where the service already exists
        monkeypatch.setattr(service_instance, 'services', {'http://example.com': service_info})

        await service_instance.update_or_add_service(service_info)
        # Your assertion here, e.g., service updated correctly

    @pytest.mark.asyncio
    async def test_add_service_invalid_type(self):
        service_instance = MainService()
        invalid_service = "Not a ServiceInfo object"  # Invalid type

        with pytest.raises(TypeError):
            await service_instance.update_or_add_service(invalid_service)

    @pytest.mark.asyncio
    async def test_del_service_existing(self, monkeypatch):
        service_instance = MainService()
        url_to_delete = 'http://example.com'
        monkeypatch.setattr(service_instance, 'services', {'http://example.com': ServiceInfo(name="some_service", service_type="some_type", url='http://example.com')})

        await service_instance.del_service(url_to_delete)
        # Your assertion here, e.g., service is removed from `service_instance.services`

    @pytest.mark.asyncio
    async def test_del_service_not_found(self, monkeypatch):
        service_instance = MainService()
        monkeypatch.setattr(service_instance, 'services', {})

        with pytest.raises(ValueError):
            await service_instance.del_service('http://nonexistent.com')