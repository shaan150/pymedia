import asyncio
import hashlib
import os
import signal
from datetime import time

import aiofiles
import psutil
from fastapi import HTTPException
from fastapi.logger import logger

from classes.enum.ServiceType import ServiceType
from classes.exception.InvalidServiceException import InvalidServiceException
from classes.services.BaseService import BaseService
from utils.service_utils import (
    get_main_service_url
)


class ExtendedService(BaseService):
    def __init__(self, service_type):
        super().__init__(service_type)

        self.main_service_url = get_main_service_url()
        self.last_updated_main_service = None
        if self.main_service_url is None:
            logger.error("Main service URL not found. Exiting...")
            # pause so the error message is printed before exiting by asking for input
            input("Press enter to exit")
            exit(1)

    async def start_background_tasks(self):
        await super().start_background_tasks()
        self.tasks.append(asyncio.create_task(self.update_main_service()))

    async def fetch_service_data(self):
        """Fetch service data, might vary based on implementation."""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage = memory_info.rss / (1024 ** 2)  # Convert to MB for Resident Set Size
        cpu_usage = process.cpu_percent(interval=1)
        # Retrieve the current CPU and memory usage
        total_cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_free = memory.available / (1024 ** 2)  # Convert to MB
        # get the total memory in MB
        total_memory = memory.total / (1024 ** 2)
        cpu_free = 100 - total_cpu_usage  # Calculate the free CPU percentage

        return {
            "name": self.service_name,
            "type": self.service_type.name,
            "url": self.service_url,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "memory_free": memory_free,
            "total_memory": total_memory,
            "cpu_free": cpu_free
        }

    async def update_main_service(self):
        while True:
            try:
                service_data = await self.fetch_service_data()
                await self.service_exception_handling(self.main_service_url, "update_or_add_service", "POST", data=service_data)
                self.last_updated_main_service = time()
                logger.info(f"Service {self.service_name} updated on main service")

            except Exception as e:
                logger.error(f"An error occurred while updating main service: {str(e)}")

            await asyncio.sleep(100)  # Wait for 5 minutes (300 seconds) before next update

    async def get_service_url(self, service_type: ServiceType):
        while True:
            try:
                new_url, _ = await self.get_optimal_service_instance(service_type)
                if new_url is not None:
                    return new_url["url"]
            except Exception as e:
                logger.error(f"Failed to update Service URL: {e}")
            await asyncio.sleep(5)

    async def calculate_md5(self, filepath: str) -> str:
        hash_md5 = hashlib.md5()
        async with aiofiles.open(filepath, "rb") as file:
            while content := await file.read(4096):
                hash_md5.update(content)
        return hash_md5.hexdigest()

    async def start_background_tasks(self):
        await super().start_background_tasks()
        self.tasks.append(asyncio.create_task(self.update_main_service()))

    async def stop(self):
        await super().stop()

        try:
            await self.service_exception_handling(self.main_service_url, f"remove_service/{self.service_url}",
                                                  "DELETE")
        except HTTPException as e:
            if e.status_code != 404:
                logger.error(f"An error occurred while removing service from main service: {str(e)}")
        except Exception as e:
            logger.error(f"An error occurred while removing service from main service: {str(e)}")

        os.kill(os.getpid(), signal.SIGINT)

    async def get_optimal_service_instance(self, service_type: ServiceType):
        if self.main_service_url is None:
            raise InvalidServiceException("No Main Service URL Provided")

        return await self.service_exception_handling(self.main_service_url, "get_service", "GET", params={
            "service_type": service_type.value})


