import os

from fastapi.logger import logger
from starlette.staticfiles import StaticFiles

from classes.enum.ServiceType import ServiceType
from classes.services.BaseService import BaseService
from classes.services.ExtendedService import ExtendedService


class FileService(ExtendedService):
    def __init__(self):
        super().__init__(ServiceType.FILE_SERVICE)
        self.file_dir = "files"
        self.image_dir = self.file_dir + "/images"
        self.music_dir = self.file_dir + "/music"