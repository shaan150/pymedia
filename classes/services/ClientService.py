import asyncio
import hashlib

import aiofiles
from fastapi import UploadFile
from fastapi.logger import logger
from starlette.staticfiles import StaticFiles

from classes.enum.ServiceType import ServiceType
from classes.services.StandardExtendedService import StandardExtendedService


class ClientService(StandardExtendedService):
    def __init__(self):
        super().__init__(ServiceType.CLIENT_SERVICE)
        self.app.mount("/templates", StaticFiles(directory="templates"), name="static")


    async def calculate_md5(self, upload_file: UploadFile) -> str:
        hash_md5 = hashlib.md5()
    # Read the file content asynchronously
        while content := await upload_file.read(4096):  # This reads the file content in chunks
            hash_md5.update(content)
        await upload_file.seek(0)  # Reset the file pointer to the beginning if you need to read the file again later
        return hash_md5.hexdigest()

    async def is_optimal_service(self):
        try:
            res = await self.get_optimal_service_instance(self.service_type)
            url = res[0]['url']
            return url
        except Exception as e:
            logger.error(f"Failed to update Service URL: {e}")
            return self.service_url



