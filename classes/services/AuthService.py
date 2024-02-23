import asyncio
import hashlib
from datetime import datetime, timedelta
from hashlib import pbkdf2_hmac

import jwt
from fastapi import HTTPException
from fastapi.logger import logger
from jwt import PyJWTError
from starlette.concurrency import run_in_threadpool

from classes.User import User
from classes.enum.ServiceType import ServiceType
from classes.exception.TokenCreationException import TokenCreationException
from classes.services.ExtendedService import ExtendedService


class AuthService(ExtendedService):
    """
    :class:`AuthService` is a subclass of :class:`ExtendedService`. It represents the authentication service.

    Methods:
        - `__init__()`: Initializes the :class:`AuthService` object.
        - `get_secret_key()`: Retrieves the secret key.
        - `hash_password(password: str, salt: bytes)`: Hashes the given password with the provided salt.
        - `generate_token(username: str)`: Generates a token for the given username.
        - `decode_token(token: str)`: Decodes the provided token.

    """
    def __init__(self):
        super().__init__(ServiceType.AUTH_SERVICE)

    async def get_secret_key(self):
        """
        Retrieve the secret key from the main service.

        :return: The secret key.
        """
        print("Inside get_secret_key")
        while True:
            try:
                print("Before awaiting service_exception_handling")
                secret_key = await self.service_exception_handling(self.main_service_url, "secret_key", "GET")
                print(f"Received from service_exception_handling: {secret_key}")
                return secret_key[0]["secret_key"]
            except Exception as e:
                logger.error(f"An error occurred while getting secret key: {str(e)}")

            await asyncio.sleep(1)


    @staticmethod
    async def hash_password(password: str, salt: bytes):
        """
        Hashes a password using PBKDF2 with the given salt.

        :param password: The password to be hashed.
        :param salt: The salt to be used in the hashing process.
        :return: The hashed password.

        """
        loop = asyncio.get_running_loop()
        hashed_password = await loop.run_in_executor(
            None,  # Uses the default executor (ThreadPoolExecutor)
            pbkdf2_hmac, 'sha256', password.encode('utf-8'), salt, 100000
        )
        return hashed_password

    async def generate_token(self, username: str):
        """
        Generate Token

        This method generates a token for a given username.

        :param username: The username for which the token is generated.
        :return: The generated token.
        :raises HTTPException: If no username is provided.
        :raises TokenCreationException: If an error occurs while creating the token.
        """
        if username is None:
            raise HTTPException(status_code=400, detail="No username provided")

        token_data = {"sub": username, "exp": datetime.now() + timedelta(hours=3)}
        try:
            secret_key = await self.get_secret_key()
            # Execute jwt.encode in a thread pool to avoid blocking the event loop
            token = jwt.encode(token_data, secret_key, algorithm=self.algorithm)

            return token
        except Exception as e:
            raise TokenCreationException(f"An error occurred while creating token: {str(e)}")

    async def decode_token(self, token: str):
        """
        :param token: The encoded token to be decoded.
        :return: The decoded token.

        This method decodes an encoded token using the specified secret key and algorithm. The token is decoded using the `jwt.decode` function, which is run in a separate thread using `run
        *_in_threadpool` to ensure asynchronous execution.

        :param token: The encoded token string.
        :return: The decoded token.

        :raises PyJWTError: If an error occurs during token decoding.
        :raises TypeError: If the token is invalid or in the wrong format.
        :raises Exception: If an unexpected error occurs during token decoding.
        """
        try:
            # run_in_threadpool is used to run the synchronous jwt.decode function in a separate thread
            secret_key = await self.get_secret_key()
            decoded_token = await run_in_threadpool(
                jwt.decode, token, secret_key, algorithms=[self.algorithm]
            )
            return decoded_token
        except PyJWTError as e:
            raise e
        except TypeError as e:
            raise PyJWTError(f"Invalid token: {str(e)}")
        except Exception as e:
            raise