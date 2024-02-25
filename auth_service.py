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
    """
    :return: The service data fetched by the fetch_service_data function.
    """
    return await service.fetch_service_data()


@app.post("/validate_user")
async def auth_user(request: Request):
    """
    This method `auth_user` is used to validate a user's credentials and generate a token for authentication.

    :param request: A `Request` object representing the HTTP request made to this endpoint.
    :return: A dictionary containing the validation details and the generated token.

    Raises:
        HTTPException: if the request is empty or invalid, or if an error occurs during the validation process.

    Example Usage:
        request = Request()
        response = await auth_user(request)

    """
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
    """
    Create a new user.

    :param request: The incoming request object.
    :type request: Request
    :return: The response object containing the result of the user creation.
    :rtype: dict
    :raises HTTPException 400: If the request is invalid (missing parameters).
    :raises HTTPException 409: If the user already exists.
    :raises HTTPException 500: If an internal error occurs during user creation.
    """
    req = await request.json()

    username = req.get("username")
    password = req.get("password")
    email = req.get("email")

    if username is None or password is None or email is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        db_service_url = await service.get_service_url(ServiceType.DATABASE_SERVICE)
        params = {"username": username}
        await service.service_exception_handling(db_service_url, "users/user", "GET", params=params)
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

@app.get("/validate_token")
async def validate_token(token: str):
    """
    :param token: The token to be validated.
    :return: A dictionary with the detail of the validation result.

    This method is used to validate a token. It takes a token as a parameter and returns a dictionary with the detail of the validation result. If the token is None, it raises an HTTPException
    * with status code 406 and detail message "Invalid Request". If the token is invalid, it raises an HTTPException with status code 401 and detail message "Invalid Token". If any other
    * exception occurs during the token validation process, it raises an HTTPException with status code 500 and detail message containing the exception message.
    """
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
    """
    :param request: The request object containing the client's request data.
    :return: None

    This method is a POST endpoint that starts a service. It takes a request object as a parameter and does not have a return value.
    The method tries to execute the start_service_endpoint function with the provided request. If an HTTPException is raised, it is re-raised.
    If any other exception is raised, it is caught, and a new HTTPException with a 500 status code and the exception message as the detail is raised.
    """
    try:
        await start_service_endpoint(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/stop")
async def stop_service():
    """
    Stop the service.

    :return: None
    """
    await service.stop()
    exit(0)



