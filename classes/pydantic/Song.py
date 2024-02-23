from typing import Optional

from pydantic import BaseModel


class Song(BaseModel):
    song_id: str
    song_name: Optional[str] = None
    artist: Optional[str] = None
    md5: Optional[str] = None
    username: Optional[str] = None