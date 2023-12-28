from fastapi import FastAPI, BackgroundTasks, HTTPException
import httpx
import asyncio
from setup import setup
import service_setup
import psutil
import random
import socket
import jwt
import datetime
import secrets


main_service_url = setup()
service_name = "media_engine"
service_type = "media_engine"
service_url = "http://localhost:50001"
auth_service_url = None
secret_key = ""
algorithm = "HS256"
connected_users = []

app = FastAPI()


async def check_users_heartbeat():
    # Create a list of heartbeat coroutines for all connected users
    heartbeat_tasks = [user.heartbeat() for user in connected_users]

    # Use asyncio.gather to run them concurrently
    results = await asyncio.gather(*heartbeat_tasks, return_exceptions=True)

    for user, result in zip(connected_users, results):
        if result is True:
            print(f"{user.username} is online.")
        elif result is False:
            print(f"{user.username} did not respond. Considered offline. Removing...")
            del connected_users[user.username]
        elif isinstance(result, Exception):
            print(f"An error occurred with {user.username}: {result}")
            del connected_users[user.username]


async def heartbeat_background_task():
    while True:
        await check_users_heartbeat()
        await asyncio.sleep(60)


async def set_auth_service():
    while True:
        global main_service_url, auth_service_url
        auth_service_url = await service_setup.handle_rest_request(main_service_url, main_service_url, "GET", "get_best_auth_engine")
        await asyncio.sleep(60)


@app.on_event("startup")
async def on_startup():
    global service_name, service_url, secret_key

    device_name = socket.gethostname()

    random_name = random.randrange(1, 50)

    time = datetime.datetime.utcnow()

    service_name = f"media_engine_{device_name}_{random_name}_{time}"
    service_url = service_setup.get_local_ip() + ":50001"
    secret_key = secrets.token_hex(32)

    service_data = await service_setup.get_service_data(service_name, service_type, service_url)
    await service_setup.handle_rest_request(main_service_url, service_data, "POST", "add_service")

    # Starting background tasks
    await asyncio.create_task(service_setup.update_main_service(main_service_url))
    await asyncio.create_task(set_auth_service())
    await asyncio.create_task(heartbeat_background_task())


@app.on_event("shutdown")
async def on_shutdown():
    BackgroundTasks().tasks.clear()
    service_data = {"url": service_url}
    await service_setup.single_update(main_service_url, service_data, "remove_service")


@app.get("/")
async def root():
    return {"detail": "Media Engine Online"}


# ... rest of your endpoints ...
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.put("/login/")
async def login(username: str, password: str):
    global secret_key, algorithm
    # Validate user credentials (this part of the code needs your implementation)
    data = {"username": username, "password": password}
    validated = await service_setup.handle_rest_request(auth_service_url, data, "GET", "validate_user")

    if validated:
        # Generate JWT token
        token_data = {"sub": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)}
        token = jwt.encode(token_data, secret_key, algorithm=algorithm)
        return {"detail": f"{username} logged in successfully", "token": token}
    else:
        raise HTTPException(status_code=400, detail="Invalid username or password")

@app.get("/validate_user/")
async def validate_user(username: str, token: str):
    if username is None or token is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    # Check token is 32 bits and a valid syntax
    if len(token) != 32 or not token.isalnum():
        raise HTTPException(status_code=400, detail="Invalid Token")

    # Check if user is already logged in
    u




@app.delete("/logout/{session_id}")
async def logout(username: str, session_id: str):
    return {"message": f"Goodbye {username}"}


@app.post("/register_user/")
async def register_user(username: str, password: str, salt: str, email: str):
    return {"message": f"User {username} registered"}
