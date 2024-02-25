import hashlib
import os
from typing import Optional

from fastapi import UploadFile
from fastapi.logger import logger
from starlette.staticfiles import StaticFiles

from classes.enum.ServiceType import ServiceType
from classes.services.ExtendedService import ExtendedService


class ClientService(ExtendedService):
    """

    ClientService
    ==============

    .. module:: client_service
       :platform: Unix, Windows
       :synopsis: This module contains the implementation of the ClientService class.

    .. inheritance-diagram:: client_service.ClientService

    Summary
    -------
    The ``ClientService`` class is a subclass of the ``StandardExtendedService`` class and provides functionality for client-side operations.

    Constructor
    -----------
    .. automethod:: __init__

    Methods
    -------
    .. automethod:: calculate_md5
    .. automethod:: is_optimal_service

    """
    def __init__(self):
        super().__init__(ServiceType.CLIENT_SERVICE)
        if not os.getenv("DEBUG", "True") == "True":
            self.app.mount("/templates", StaticFiles(directory="templates"), name="static")

    async def calculate_md5(self, upload_file: UploadFile) -> str:
        """
        Calculates the MD5 hash value of the given upload file.

        :param upload_file: The file for which the MD5 hash value needs to be calculated.
        :type upload_file: UploadFile

        :return: The MD5 hash value as a string.
        :rtype: str
        """
        hash_md5 = hashlib.md5()
        # Read the file content asynchronously
        while content := await upload_file.read(4096):  # This reads the file content in chunks
            hash_md5.update(content)
        await upload_file.seek(0)
        return hash_md5.hexdigest()

    async def is_optimal_service(self):
        """
        Checks if the current service instance is optimal.

        :return: The URL of the optimal service instance if it is available,
                 otherwise returns the current service URL.
        """
        try:
            res = await self.get_optimal_service_instance(self.service_type)
            url = res[0]['url']
            return url
        except Exception as e:
            logger.error(f"Failed to update Service URL: {e}")
            return self.service_url
