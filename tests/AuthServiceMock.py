import pytest
from unittest.mock import AsyncMock, patch

from classes.services.AuthService import AuthService


class AuthServiceMock(AuthService):
    def __init__(self):
        super().__init__()
        self.main_service_url = "http://localhost:8000"

