import asyncio
import json
import random
import socket
import sys
from datetime import datetime

import httpx
import psutil
from fastapi import HTTPException, Request

from classes.enum.ServiceType import ServiceType
from classes.exception.FailedServiceCreationException import FailedServiceCreationException
from classes.exception.InvalidRequestMethodException import InvalidRequestMethodException
from classes.exception.MissingPropertyException import MissingPropertyException
from classes.exception.RequestFailedExceptionException import RequestFailedException

last_exception = None


def get_local_ip():
    """
    Returns the local IP address of the device.

    :return: The local IP address of the device.
    :rtype: str
    :raises Exception: If unable to get local IP address.
    """
    try:
        return socket.gethostname()
    except Exception as e:
        return "Unable to get local IP"


async def get_service_data(service_name, service_type, service_url):
    """
    Retrieves the service data including CPU and memory usage, free CPU and memory, and current users.

    :param service_name: Name of the service.
    :param service_type: Type of the service.
    :param service_url: URL of the service.
    :return: A dictionary containing the service data including CPU and memory usage, free CPU and memory, and current users.

    Example:
        service_data = await get_service_data("Service1", "Web", "http://localhost:8080")
        print(service_data)
        {
            "name": "Service1",
            "type": "Web",
            "url": "http://localhost:8080",
            "cpu_usage": 32.5,
            "memory_usage": 256.3,
            "memory_free": 1024.7,
            "total_memory": 1280.0,
            "cpu_free": 67.5,
            "users": []
        }
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

    # Replace 'users' with your method of tracking current users
    users = []  # Example: list of current users

    return {
        "name": service_name,
        "type": service_type,
        "url": service_url,
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "memory_free": memory_free,
        "total_memory": total_memory,
        "cpu_free": cpu_free,
        "users": users
    }


async def handle_rest_request(url, endpoint, method, data=None, params=None, files=None, stream=False):
    """
    :param url: The base URL for the REST API.
    :param endpoint: The endpoint of the REST API.
    :param method: The HTTP method to be used for the request. It can be one of "POST", "GET", "PUT", or "DELETE".
    :param data: The JSON payload for the request. It is optional and only required for "POST" and "PUT" methods.
    :param params: The query parameters for the request. It is optional.
    :param files: The files to be uploaded with the request. It is optional and only required for "POST" and "PUT" methods.
    :param stream: A boolean flag indicating whether to stream the response or not. Defaults to False.
    :return: If stream is True, returns the streaming response.
             Otherwise, returns a tuple containing the JSON response and the HTTP status code.

    """
    retry_interval = 3  # seconds
    attempt_duration = 15 # seconds
    start_time = asyncio.get_event_loop().time()

    async with httpx.AsyncClient(verify=False) as client:
        while asyncio.get_event_loop().time() - start_time < attempt_duration:
            try:
                request_url = f"http://{url}/{endpoint}"
                response = None
                if method == "POST":
                    response = await client.post(request_url, json=data, params=params, files=files)
                elif method == "GET":
                    response = await client.get(request_url, params=params)
                elif method == "PUT":
                    response = await client.put(request_url, json=data, params=params, files=files)
                elif method == "DELETE":
                    response = await client.delete(request_url, params=params)
                else:
                    raise InvalidRequestMethodException()

                if response.is_error:
                    # If response status code is not 500 or 503, raise an exception to stop retrying
                    if response.status_code not in (500, 503):
                        detail = response.json().get('detail', 'Error without detail') if not stream else 'Error without detail'
                        raise HTTPException(status_code=response.status_code, detail=detail)
                else:
                    # For streaming responses, return the response directly
                    if stream:
                        return response
                    # Successful JSON response
                    return response.json(), response.status_code

            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_exception = f"An error occurred: {e}"
                # Log error or handle it as needed here
            except HTTPException as e:
                # Stop retrying and handle or propagate the exception
                raise e from None
            except Exception as e:
                last_exception = f"An error occurred: {e}"
                # Log error or handle it as needed here

            # Sleep before the next retry
            await asyncio.sleep(retry_interval)

        # This raises a custom exception if the request consistently fails
        raise RequestFailedException(last_exception if 'last_exception' in locals() else "Request failed after retries")


async def start_service(main_service_url, service_type: ServiceType, secret_key=None):
    """
    Start a service by running the service creator script with the necessary arguments.

    :param main_service_url: The URL of the main service.
    :type main_service_url: str
    :param service_type: The type of the service to start.
    :type service_type: ServiceType
    :param secret_key: The secret key for the service (optional).
    :type secret_key: str
    :return: None
    :raises ValueError: If main_service_url or service_type is None.
    :raises FailedServiceCreationException: If there is an error starting the service.
    """
    if main_service_url is None or service_type is None:
        raise ValueError("Main service URL and service type are required")

    # Construct the command to run the service creator script with the necessary arguments
    cmd = [
        sys.executable, 'service_creator.py',
        '--auto', 'true',
        '--main_service_url', main_service_url,
        '--service_type', service_type.name
    ]

    if secret_key is not None:
        cmd.extend(['--secret_key', secret_key])

    try:
        # Start the subprocess
        await asyncio.create_subprocess_exec(*cmd)
    except Exception as e:
        raise FailedServiceCreationException(
            f"Failed to start new instance of {service_type.value} with error: {str(e)}")

    # Wait for the subprocess to finish if necessary
    # await process.wait()
    print(f"New instance of {service_type.value} started successfully.")


def get_property(property: str, file_path: str):
    """
    Get the value of a specified property from a JSON file.

    :param property: The name of the property to retrieve.
    :param file_path: The path to the JSON file.
    :return: The value of the specified property.
    :raises ValueError: If either `property` or `file_path` is None.
    :raises MissingPropertyException: If the specified property is not found in the JSON file or is found with no value.
    :raises Exception: If an error occurs while reading or parsing the JSON file.
    """
    if property is None or file_path is None:
        raise ValueError("Invalid Property or File Path")
    # Read and parse the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)
    try:
        value = data[property]
        if value is None:
            raise MissingPropertyException(f"{property} found with no value in {file_path}")

        return value
    except KeyError:
        breakpoint()
        raise MissingPropertyException(f"{property} not found in {file_path}")
    except Exception as e:
        raise e


def generate_service_name(service_type):
    """
    Generate a service name based on the service type, device name, random number, and timestamp.

    :param service_type: The type of the service.
    :return: The generated service name.
    """
    device_name = socket.gethostname()

    random_name = random.randrange(1, 50)

    time = datetime.now()

    return f"{service_type.name}_{device_name}_{random_name}_{time}"


def get_main_service_url():
    """
    Returns the main service URL from a JSON file.

    :return: The main service URL.
    :rtype: str
    :raise Exception: If the main service URL is not found in the JSON file.
    """
    try:
        return get_property('main_service_url', 'service_properties.json')
    except Exception:
        raise
