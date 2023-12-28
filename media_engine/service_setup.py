import asyncio
import httpx
import socket
import psutil
from fastapi import HTTPException

def get_local_ip():
    try:
        # The following line creates a UDP socket and connects to an external address,
        # but does not send any data. This is used to determine the local network interface.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Connect to a public DNS server
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception as e:
        return "Unable to get local IP"


async def get_service_data(service_name, service_type, service_url):
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_usage = memory_info.rss / (1024 ** 2)  # Convert to MB for Resident Set Size
    cpu_usage = process.cpu_percent(interval=1)
    # Retrieve the current CPU and memory usage
    total_cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_free = memory.available / (1024 ** 2)  # Convert to MB
    cpu_free = 100 - total_cpu_usage # Calculate the free CPU percentage

    # Replace 'users' with your method of tracking current users
    users = []  # Example: list of current users

    return {
        "name": service_name,
        "type": service_type,
        "url": service_url,
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "memory_free": memory_free,
        "cpu_free": cpu_free,
        "users": users
    }


async def update_main_service(main_service_url):
    while True:
        try:
            service_data = await get_service_data()
            await handle_rest_request(main_service_url, "update_service", "POST", service_data)

        except Exception as e:
            print(f"An error occurred while updating main service: {str(e)}")

        await asyncio.sleep(300)  # Wait for 5 minutes (300 seconds) before next update


async def single_update(url, data, endpoint, params=None):
    retry_interval = 5  # seconds
    attempt_duration = 30  # seconds
    start_time = asyncio.get_event_loop().time()

    while asyncio.get_event_loop().time() - start_time < attempt_duration:
        try:
            async with httpx.AsyncClient() as client:
                return await client.post(f"{url}/{endpoint}", json=data, params=params)
        except httpx.RequestError as e:
            return {"error": str(e)}
        finally:
            await asyncio.sleep(retry_interval)  # Wait before retrying

    return {"error": "Failed to update the service within the allotted time."}


async def get_from_service(url, endpoint, params=None):
    retry_interval = 5  # seconds
    attempt_duration = 30  # seconds
    start_time = asyncio.get_event_loop().time()

    while asyncio.get_event_loop().time() - start_time < attempt_duration:
        try:
            async with httpx.AsyncClient() as client:
                return await client.get(f"{url}/{endpoint}", params=params)
        except httpx.RequestError as e:
            return {"error": str(e)}
        finally:
            await asyncio.sleep(retry_interval)  # Wait before retrying

    return {"error": "Failed to retrieve data from service within the allotted time."}


async def handle_rest_request(url, endpoint, method, data=None, params=None):
    retry_interval = 5  # seconds
    attempt_duration = 30  # seconds
    start_time = asyncio.get_event_loop().time()

    while asyncio.get_event_loop().time() - start_time < attempt_duration:
        try:
            async with httpx.AsyncClient() as client:
                if method == "POST":
                    return await client.post(f"{url}/{endpoint}", json=data, params=params)
                elif method == "GET":
                    return await client.get(f"{url}/{endpoint}", params=params)
                else:
                    raise HTTPException(status_code=400, detail="Invalid Request")
        except httpx.RequestError as e:
            return {"error": str(e)}
        finally:
            await asyncio.sleep(retry_interval)

    return {"error": "Failed to retrieve data from service within the allotted time."}