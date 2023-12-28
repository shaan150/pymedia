from fastapi import FastAPI, HTTPException, Request
import os
import DatabaseConnector
from utils import hash_password

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Invalid Endpoint"}


@app.get("/validate_user/")
async def auth_user(username: str, password: str):
    try:
        salt = await DatabaseConnector.get_user_salt(username)
        if salt is None:
            HTTPException(status_code=400, detail="Invalid Account")

        hashed_password = await hash_password(password, salt[0])
        user = await DatabaseConnector.validate_user(username, hashed_password)

        if user is None:
            return {"detail": "Invalid Details"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"detail": f"User Validated"}


@app.post("/create_user")
async def create_user(request: Request):
    data = await request.json()

    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if username is None or password is None or email is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    # Check if username is already taken
    try:
        user = await DatabaseConnector.get_user(username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if user is not None:
        raise HTTPException(status_code=400, detail="Duplicate Account")

    # Check if email is already taken
    try:
        user = await DatabaseConnector.get_user_email(email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if user is not None:
        raise HTTPException(status_code=400, detail="Duplicate Account")

    salt = os.urandom(32)
    try:
        hashed_password = await hash_password(password, salt)
        created = await DatabaseConnector.create_user(username, hashed_password, salt, email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if created is False:
        raise HTTPException(status_code=400, detail="User could not be created")

    return {"detail": f"User {username} created"}
