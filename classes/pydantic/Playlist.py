from typing import Optional

from pydantic import BaseModel


class Playlist(BaseModel):
    playlist_id: str
    playlist_name: Optional[str] = None
    username: Optional[str] = None