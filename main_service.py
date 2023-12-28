from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
import os
import time
import asyncio
import socket
from classes.UserNotificationInfo import UserNotificationInfo
import classes.ServiceInfo as ServiceInfo
import httpx

app = FastAPI()

services = []

users_to_be_notified = []

users_to_be_notified_lock = asyncio.Lock()

services_lock = asyncio.Lock()

max_retries = 3
retry_delay = 30


async def check_services():
    global services
    while True:
        async with services_lock:
            if services:
                for service in services:
                    time_diff = time.time() - service.last_update
                    if time_diff > 5 * 60:  # 5 minutes in seconds
                        conn_success = await check_and_update_service(service)
                        if not conn_success:
                            await handle_service_failure(service)
        await asyncio.sleep(300)  # Wait for 5 minutes before next check


async def check_and_update_service(service):
    start_time = time.time()
    while time.time() - start_time < 30:  # 30 seconds timeout
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{service.url}/")
                if response.status_code == 200:
                    print("Service Online")
                    service.last_update = time.time()
                    return True
        except httpx.RequestError as e:
            print(f"Error checking service {service.name}: {e}")
        await asyncio.sleep(5)  # Wait for 5 seconds before retrying
    return False


async def handle_service_failure(service):
    print(f"Service {service.name} offline. Attempting to find a replacement...")
    optimal_service = await get_optimal_service_instance(service.type)

    if not optimal_service:

        print(f"No optimal replacement found. Starting a new local instance of {service.type}...")
        try:
            # Replace this with the actual command to start the service
            process = await asyncio.create_subprocess_exec('start_service_command', service.type)
            await process.wait()
            print(f"New instance of {service.type} started successfully.")

        except Exception as e:
            print(f"Failed to start a new instance of {service.type}: {e}")

        finally:
            # Add all users on the failed service to the list of users to be notified
            async with users_to_be_notified_lock:
                for user in service.users:
                    users_to_be_notified.append(UserNotificationInfo(user.username, user.token))
            await del_service(service.url)


@app.on_event("startup")
async def on_startup():
    # Starting background tasks
    await asyncio.create_task(check_services())


@app.get("/")
async def root():
    return {"detail": "Main Server Active"}


@app.get("/get_service")
async def get_service(service_type: str):
    if service_type is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    # get all services with type auth_service
    try:
        optimal_service = await get_optimal_service_instance(service_type)
        if optimal_service:
            return {"url": optimal_service.url}
        else:
            raise HTTPException(status_code=500, detail="No available services found after waiting 30 seconds")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error Handling Endpoint {str(e)}")


@app.post("/add_service")
async def add_service(request: Request):
    data = await request.json()

    if data is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    # Extract service data from the request
    name = data.get("name")
    url = data.get("url")
    service_type = data.get("type")
    cpu_usage = data.get("cpu_usage", 0)
    memory_usage = data.get("memory_usage", 0)
    memory_free = data.get("memory_free", 0)
    cpu_free = data.get("cpu_free", 0)
    users = data.get("users", [])

    if not name or not url or not service_type:
        raise HTTPException(status_code=400, detail="Insufficient service data")

    service_info = ServiceInfo.ServiceInfo(name, service_type, url, cpu_usage, memory_usage, memory_free, cpu_free,
                                           users)

    try:
        await update_or_add_service(service_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"detail": f"Service {service_info} Added"}


@app.post("/update_service")
async def update_service(request: Request):
    data = await request.json()

    if data is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    # Extract service data from the request
    name = data.get("name")
    service_type = data.get("type")
    url = data.get("url")
    cpu_usage = data.get("cpu_usage", 0)
    memory_usage = data.get("memory_usage", 0)
    memory_free = data.get("memory_free", 0)
    cpu_free = data.get("cpu_free", 0)
    users = data.get("users", [])

    if url is None:
        raise HTTPException(status_code=400, detail="Insufficient service data")

    service_info = ServiceInfo.ServiceInfo(name, service_type, url, cpu_usage, memory_usage, memory_free, cpu_free,
                                           users)

    try:
        await update_or_add_service(service_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"detail": f"Service {service_info.name} Updated"}


@app.post("/remove_service")
async def remove_service(request: Request):
    data = await request.json()

    if data is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    url = data.get("url")

    if url is None:
        raise HTTPException(status_code=400, detail="No Service Provided")

    try:
        await del_service(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"detail": f"Service {url} Removed"}


@app.post("/handle_user_redirect")
async def handle_user_redirect(request: Request):
    data = await check_user(request)

    if data is None:
        raise HTTPException(status_code=500, detail="System Error: Request Data Removed During Processing")

    data = await request.json()

    service_type = data.get("service_type")

    if service_type is None:
        raise HTTPException(status_code=500, detail="System Error: Service Type Removed During Processing")

    optimal_service = await get_optimal_service_instance(service_type)

    if optimal_service is None:
        raise HTTPException(status_code=500, detail="No available services found after waiting 30 seconds")

    return {"redirect_url": optimal_service.url}


@app.post("/check_user/")
async def check_user(request: Request):
    data = await request.json()

    if data is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    username = data.get("username")
    token = data.get("token")
    service_type = data.get("service_type")

    if username is None or service_type is None or token is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    async with users_to_be_notified_lock:
        for user in users_to_be_notified:
            if user.username == username and user.token == token:
                users_to_be_notified.remove(user)
                return {"detail": "User Validated"}
            else:
                raise HTTPException(status_code=400, detail="No User Found")


async def update_or_add_service(service_to_update):
    async with services_lock:
        if service_to_update:
            services[service_to_update.url] = service_to_update


async def del_service(url):
    async with services_lock:
        if url:
            del services[url]


async def get_optimal_service_instance(service_type):
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < 30:  # Try for 30 seconds
        async with services_lock:
            service_instances = [service for service in services if service.type == service_type]

            if service_instances:
                optimal_service = await ServiceInfo.select_service(service_instances)
                if optimal_service:
                    # If an optimal media engine is found, return its information
                    return optimal_service.url

            # Wait a bit before retrying
            await asyncio.sleep(5)  # Wait for 5 seconds before retrying

    # If no services are found after 30 seconds, return nothing
    return None
