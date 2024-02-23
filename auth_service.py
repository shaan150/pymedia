import base64
import os

from fastapi import HTTPException, Request
from fastapi.logger import logger
from jwt import PyJWTError

from classes.enum.ServiceType import ServiceType
from classes.services.AuthService import AuthService
from utils.service_utils import start_service_endpoint

service = AuthService()
app = service.app


@app.get("/")
async def root():
    return await service.fetch_service_data()


@app.post("/validate_user")
async def auth_user(request: Request):

    if request is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        req = await request.json()
        username = req.get("username")
        password = req.get("password")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        db_service_url = await service.get_service_url(ServiceType.DATABASE_SERVICE)
        params = {"username": username}
        res = await service.service_exception_handling(db_service_url, "users/user/salt", "GET", params=params)
        salt = base64.b64decode(res[0]['salt'])
        hashed_password = await service.hash_password(password, salt)
        hashed_password = base64.b64encode(hashed_password).decode('utf-8')
        user = {"username": username, "password": hashed_password}
        await service.service_exception_handling(db_service_url, "users/user/validate", "POST", data=user)

        token = await service.generate_token(username)

        return {"detail": f"{username} validated", "token": token}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create_user")
async def create_user(request: Request):
    req = await request.json()

    username = req.get("username")
    password = req.get("password")
    email = req.get("email")

    if username is None or password is None or email is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        db_service_url = await service.get_service_url(ServiceType.DATABASE_SERVICE)
        params = {"username": username}
        user = await service.service_exception_handling(db_service_url, "users/user", "GET", params=params)
        # if user already exists raise a 409 error
        raise HTTPException(status_code=409, detail=f"User {username} already exists")
    except HTTPException as e:
        if e.status_code == 404:
            try:
                salt = os.urandom(32)
                salt_str = base64.b64encode(salt).decode('utf-8')

                hashed_password = await service.hash_password(password, salt)
                hashed_password_str = base64.b64encode(hashed_password).decode('utf-8')
                user = {"username": username, "password": hashed_password_str, "salt": salt_str, "email": email}
                await service.service_exception_handling(db_service_url, "users/user/create", "POST",
                                                         data=user)
                return {"detail": f"User {username} created"}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"User could not be created, due to an internal error {str(e)}")
                raise HTTPException(status_code=500, detail="User could not be created, due to an internal error")
        else:
            raise
    except Exception as e:
        logger.error(f"User could not be created, due to an internal error {str(e)}")
        raise HTTPException(status_code=500, detail="User could not be created, due to an internal error")


@app.post("/generate_token")
async def generate_token(request: Request):
    req = await request.json()

    username = req.get("username")

    if username is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        params = {"username": username}
        await service.service_exception_handling(service.db_service_url, "users/user", "GET", params=params)
        token = await service.generate_token(username)
        return {"detail": f"{username} logged in successfully", "token": token}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/validate_token")
async def validate_token(token: str):
    if token is None:
        raise HTTPException(status_code=406, detail="Invalid Request")

    try:
        await service.decode_token(token)
        return {"detail": "Token is valid"}
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start_service")
async def start_service(request: Request):
    try:
        await start_service_endpoint(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/stop")
async def stop_service():
    await service.stop()
    exit(0)



