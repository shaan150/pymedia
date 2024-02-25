import asyncio
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.logger import logger
from httpx import HTTPStatusError

from classes.enum.ServiceType import ServiceType
from classes.exception.RequestFailedExceptionException import RequestFailedException
from utils.service_utils import generate_service_name, get_local_ip, get_property, handle_rest_request


class BaseService:
    """

    The `BaseService` class represents a base service that can be extended to create specific service implementations. It provides functionality for starting and stopping the service, handling
    * service exceptions, and managing background tasks.

    Attributes:
        - `service_type`: The type of the service.
        - `properties_file`: The path to the properties file for the service.
        - `service_name`: The generated name for the service.
        - `service_port`: The port on which the service is running.
        - `service_url`: The URL of the service.
        - `services_lock`: A lock object for synchronizing access to the service.
        - `tasks`: A list of background tasks.
        - `secret_key`: The secret key used for authentication.
        - `algorithm`: The algorithm used for authentication.

    Methods:
        - `__init__(self, service_type: ServiceType)`: Initializes a new instance of the `BaseService` class.
        - `lifespan(self, app: FastAPI)`: An async context manager that handles the lifespan of the service.
        - `start_background_tasks(self)`: Starts the background tasks of the service.
        - `stop(self)`: Handles any cleanup necessary before service shutdown.
        - `service_exception_handling(self, service_url, endpoint, method, params=None, data=None, files=None, stream=False)`: Handles service exceptions and returns the response.

    """
    def __init__(self, service_type: ServiceType, debug: Optional[bool] = False):
        self.service_type = service_type
        self.properties_file = "service_properties.json"
        self.service_name = generate_service_name(service_type)
        self.service_port = None
        self.service_url = None
        self.services_lock = asyncio.Lock()
        self.tasks = []
        self.secret_key = None
        self.algorithm = "HS256"
        # enable swagger
        self.app = FastAPI(
            title=self.service_name,
            description="Service API",
            version="0.1",
            openapi_url="/openapi.json",
            docs_url="/docs",
            redoc_url=None,
            lifespan=self.lifespan
        )
        self.debug = debug

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """
        Execute the lifespan of the application.

        :param app: Instance of FastAPI application.
        :type app: FastAPI
        :return: Context manager for executing the lifespan.
        :rtype: async generator
        """
        await self.start_background_tasks()
        yield
        await self.stop()

    async def start_background_tasks(self):
        """
        Starts the background tasks.

        :return: None
        """
        if not os.getenv("DEBUG", "True") == "True":
            try:
                self.service_port = get_property(f"{self.service_type.value}", self.properties_file)
                self.service_url = f"{get_local_ip()}:{self.service_port}"
                logger.info("Starting Service On URL " + self.service_url)
            except Exception as e:
                logger.error(f"Error occurred while starting service: {str(e)}, exiting...")
                # pause so the error message is printed before exiting by asking for input
                input("Press enter to exit")
                exit(1)
        else:
            self.service_port = 8000
            self.service_url = f"{get_local_ip()}:{self.service_port}"
            logger.info("Starting Service On URL " + self.service_url)


    async def stop(self):
        """
        Stop method stops all running tasks and clears the list of tasks.

        :return: None
        """
        BackgroundTasks().tasks.clear()

        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def service_exception_handling(self, service_url, endpoint, method, params=None, data=None, files=None,
                                         stream=False):
        """
        :param service_url: The URL of the service to make the request to.
        :param endpoint: The endpoint of the service to make the request to.
        :param method: The HTTP method to use for the request.
        :param params: Optional. The query parameters to include in the request.
        :param data: Optional. The body of the request.
        :param files: Optional. Any files to include in the request.
        :param stream: Optional. Whether to enable streaming of the response.
        :return: The response from the service.

        """
        try:
            response = await handle_rest_request(service_url, endpoint, method, params=params, data=data, files=files,
                                                 stream=stream)
        except HTTPException:
            raise
        except HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.json()['detail'])
        except ValueError as e:
            raise HTTPException(status_code=503, detail=f"No Service Available with error {e}")
        except RequestFailedException as e:
            raise HTTPException(status_code=500, detail=f"Request Failure Exception {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Service Error With Detail {e}")

        return response