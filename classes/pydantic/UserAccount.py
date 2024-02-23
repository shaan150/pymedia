from typing import Optional

from pydantic import BaseModel


class UserAccount(BaseModel):
    username: str
    password: Optional[str] = None
    salt: Optional[str] = None
    email: Optional[str] = None
