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
    """

    The `ExtendedService` class extends the `BaseService` class and provides additional functionality for updating the main service, fetching service data, getting the optimal service URL
    *, and calculating the MD5 hash of a file.

    ## Attributes:
    - `main_service_url`: The URL of the main service.
    - `last_updated_main_service`: The timestamp of the last update to the main service.

    ## Methods:

    ### `__init__(self, service_type)`
    Constructor method that initializes the `ExtendedService` object.

    ### `start_background_tasks(self)`
    Starts background tasks. This method calls the `start_background_tasks` method of the superclass to start any inherited background tasks, and then creates a new task to update the main
    * service by calling the `update_main_service` method. The new task is added to the `tasks` list.

    ### `stop(self)`
    Stops the service. This method calls the `stop` method of the superclass to stop any running tasks, and then attempts to remove the service from the main service using the `service_exception
    *_handling` method with the parameters `self.main_service_url`, "remove_service/{self.service_url}", and "DELETE". If an HTTPException with a status code of 404 is raised, it is ignored
    *. If any other exception is raised, an error log is generated. Finally, the process is killed using `os.kill` with the `SIGINT` signal.

    ### `fetch_service_data(self)`
    Fetches service data. This method retrieves information about the service and the system it is running on, such as the service name, type, URL, CPU usage, memory usage, memory free,
    * total memory, and CPU free. The information is returned as a dictionary.

    ### `update_main_service(self)`
    Updates the main service. This method repeatedly fetches service data using the `fetch_service_data` method, sends the data to the main service using the `service_exception_handling
    *` method with the parameters `self.main_service_url`, "update_or_add_service", "POST", and `data=service_data`, and updates the `last_updated_main_service` attribute with the current
    * time. If an error occurs during the update process, an error log is generated. The method waits for 100 seconds before performing the next update.

    ### `get_service_url(self, service_type: ServiceType)`
    Gets the URL of the optimal service instance for the given service type. This method repeatedly calls the `get_optimal_service_instance` method with the `service_type` parameter to get
    * the URL of the optimal service instance. If a URL is returned, it is immediately returned. If an exception is raised, an error log is generated. The method waits for 5 seconds before
    * retrying.

    ### `calculate_md5(self, filepath: str)`
    Calculates the MD5 hash of the file specified by the given filepath. This method opens the file in binary mode using `aiofiles.open`, reads the contents in chunks of 4096 bytes, and
    * repeatedly updates the `hash_md5` object with the read content. The MD5 hash of the file is returned as a hexadecimal string.

    ### `get_optimal_service_instance(self, service_type: ServiceType)`
    Gets the optimal service instance for the given service type. This method calls the `service_exception_handling` method with the parameters `self.main_service_url`, "get_service", "
    *GET", and `params={"service_type": service_type.value}` to retrieve the optimal service instance from the main service. If the main service URL is not provided or an exception is raised
    * during the retrieval process, an error log is generated.

    """
    def __init__(self, service_type, debug=False):
        super().__init__(service_type, debug)
        if self.debug or debug:
            self.main_service_url = "http://localhost:8000"
        else:
            self.main_service_url = get_main_service_url()
        self.last_updated_main_service = None
        if self.main_service_url is None:
            logger.error("Main service URL not found. Exiting...")
            # pause so the error message is printed before exiting by asking for input
            input("Press enter to exit")
            exit(1)

    async def start_background_tasks(self):
        """
        Start background tasks.

        :return: None
        """
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

    async def fetch_service_data(self):
        """
        Fetches service data.

        :return: A dictionary containing the following information:
                 - "name": The name of the service.
                 - "type": The type of the service.
                 - "url": The URL of the service.
                 - "cpu_usage": The CPU usage of the service in percentage.
                 - "memory_usage": The memory usage of the service in MB.
                 - "memory_free": The free memory available in MB.
                 - "total_memory": The total memory of the system in MB.
                 - "cpu_free": The free CPU percentage.

        :rtype: dict
        """
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
        """Updates the main service.

        This method retrieves the service data using the `fetch_service_data` method, and then sends it to the main service using the `service_exception_handling` method with the parameters
        * `self.main_service_url`, "update_or_add_service", "POST", and `data=service_data`.

        After successfully updating the main service, the `last_updated_main_service` attribute is updated with the current time using the `time()` function. A log message is also generated
        * to indicate that the service has been updated on the main service.

        If an error occurs during the update process, an error log is generated with the details of the error.

        This method waits for 100 seconds using the `asyncio.sleep` function before performing the next update.

        :return: None
        """
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
        """
        Get the URL of the optimal service instance for the given service type.

        :param service_type: The service type to get the URL for.
        :type service_type: ServiceType
        :return: The URL of the optimal service instance, or None if no instance is available.
        :rtype: str or None
        """
        while True:
            try:
                new_url, _ = await self.get_optimal_service_instance(service_type)
                if new_url is not None:
                    return new_url["url"]
            except Exception as e:
                logger.error(f"Failed to update Service URL: {e}")
            await asyncio.sleep(5)

    async def calculate_md5(self, filepath: str) -> str:
        """
        Calculate the MD5 hash of the file specified by the given filepath.

        :param filepath: The path to the file.
        :return: The MD5 hash of the file.
        """
        try:
            hash_md5 = hashlib.md5()
            async with aiofiles.open(filepath, "rb") as file:
                while content := await file.read(4096):
                    hash_md5.update(content)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"An error occurred while calculating MD5: {str(e)}")
            raise

    async def get_optimal_service_instance(self, service_type: ServiceType):
        """
        Retrieve the optimal service instance for a given service type.

        :param service_type: The type of service being requested.
        :type service_type: ServiceType
        :raises InvalidServiceException: If no main service URL is provided.
        :return: The optimal service instance.
        :rtype: Awaitable[ServiceInstance]
        """
        breakpoint()
        if self.main_service_url is None:
            raise InvalidServiceException("No Main Service URL Provided")
        try:
            return await self.service_exception_handling(self.main_service_url, "get_service", "GET", params={
            "service_type": service_type.value})
        except Exception as e:
            logger.error(f"An error occurred while getting optimal service instance: {str(e)}")
            raise


