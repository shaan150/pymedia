import asyncio

from fastapi.logger import logger

from classes.enum.ServiceType import ServiceType
from classes.services.ExtendedService import ExtendedService


class StandardExtendedService(ExtendedService):
    def __init__(self, service_type):
        super().__init__(service_type)