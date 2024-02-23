from enum import Enum


class ServiceType(Enum):
    MAIN_SERVICE = "main_service"
    FILE_SERVICE = "file_service"
    DATABASE_SERVICE = "database_service"
    CLIENT_SERVICE = "client_service"
    AUTH_SERVICE = "auth_service"


