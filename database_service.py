from typing import Optional

from fastapi import HTTPException, Request

from DatabaseAsyncQuery import create_user, get_user, create_song, get_song, create_playlist, get_playlists, \
    add_song_to_playlist, get_user_by_password, get_songs, remove_song_from_playlist, get_playlist_songs
from classes.pydantic.Playlist import Playlist
from classes.pydantic.Song import Song
from classes.pydantic.UserAccount import UserAccount
from classes.services.DatabaseService import DatabaseService

service = DatabaseService()

app = service.app


@app.get("/")
async def root():
    return await service.fetch_service_data()

@app.post("/users/user/create")
async def create_user_endpoint(user: UserAccount):
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        result = await create_user(user.username, user.password, user.salt, user.email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not result:
        raise HTTPException(status_code=400, detail="Could not create user")
    return {"detail": "User created successfully"}


@app.get("/users/user")
async def get_user_endpoint(username: str):
    try:
        user: UserAccount = await get_user(username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user[0], "email": user[1]}


@app.get("/users/user/salt")
async def get_user_endpoint(username: str):
    try:
        user: UserAccount = await get_user(username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"salt": user[2]}


@app.post("/users/user/validate")
async def validate_user_endpoint(user: UserAccount):
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        result = await get_user_by_password(user.username, user.password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if result is None:
        raise HTTPException(status_code=401, detail="Not Valid Password")

    return {"detail": "User Validated"}


@app.post("/songs/song/create")
async def create_song_endpoint(song: Song):
    if song is None:
        raise HTTPException(status_code=400, detail="Invalid Request")
    # check if song with artist and name already exists
    try:
        result = await get_songs(song.song_name, song.artist)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if result:
        raise HTTPException(status_code=409, detail="Song already exists")

    try:
        result = await create_song(song.song_id, song.song_name, song.artist, song.md5, song.username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not result:
        raise HTTPException(status_code=400, detail="Could not create song")

    return {"detail": "Song created successfully", "song_id": result}


@app.get("/songs/song")
async def get_song_endpoint(song_id: str):
    if song_id is None or song_id == "":
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        song:Song = await get_song(song_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if song is None:
        raise HTTPException(status_code=404, detail="Song not found")
    song_json = {"song_id": song[0], "song_name": song[1], "artist": song[2], "md5": song[3], "username": song[4]}
    return song_json


@app.post("/playlists/playlist/create")
async def create_playlist_endpoint(playlist: Playlist):
    if playlist is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        result = await get_playlists(playlist.username, playlist.playlist_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if result:
        raise HTTPException(status_code=409, detail="Playlist already exists")

    try:
        result = await create_playlist(playlist.playlist_id, playlist.playlist_name, playlist.username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not result:
        raise HTTPException(status_code=400, detail="Could not create playlist")

    return {"message": "Playlist created successfully"}


@app.get("/songs")
async def get_songs_endpoint(name: Optional[str] = None, artist: Optional[str] = None):
    try:
        songs_sql = await get_songs(name, artist)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not songs_sql or len(songs_sql) == 0:
        raise HTTPException(status_code=404, detail="No songs found with that name")

    songs = [Song(song_id=row[0], song_name=row[1], artist=row[2], md5=row[3]).dict() for row in songs_sql]
    return songs


@app.get("/playlists")
async def get_playlists_endpoint(username: Optional[str] = None, playlist_name: Optional[str] = None):
    # list of playlists
    try:
        playlists_sql = await get_playlists(username, playlist_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if playlists_sql is None or len(playlists_sql) == 0:
        raise HTTPException(status_code=404, detail="No playlists found for that user")
    playlists = [Playlist(playlist_id=row[0], playlist_name=row[1], username=row[2]).dict() for row in playlists_sql]
    return playlists

@app.get("/playlists/playlist")
async def get_playlist_endpoint(playlist_id: str):
    if playlist_id is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        playlist = await get_playlists(playlist_id=playlist_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if playlist is None or len(playlist) == 0:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return {"playlist_id": playlist[0], "playlist_name": playlist[1], "username": playlist[2]}


@app.get("/playlists/playlist/songs")
async def get_playlist_songs_endpoint(playlist_id: str):
    if playlist_id is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        songs_sql = await get_playlist_songs(playlist_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if songs_sql is None or len(songs_sql) == 0:
        raise HTTPException(status_code=404, detail="No songs found for that playlist")

    songs = [Song(song_id=row[0], song_name=row[1], artist=row[2], md5=row[3]).dict() for row in songs_sql]

    return songs

@app.post("/playlists/playlist/add_song/")
async def add_song_to_playlist_endpoint(request: Request):
    req = await request.json()
    if req is None:
        raise HTTPException(status_code=400, detail="Invalid Request")
    playlist_id = req.get("playlist_id")
    song_id = req.get("song_id")

    if playlist_id is None or song_id is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        result = await add_song_to_playlist(playlist_id, song_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not result:
        raise HTTPException(status_code=400, detail="Could not add song to playlist")

    return {"message": "Song added to playlist successfully"}


@app.delete("/playlists/playlist/remove_song/")
async def remove_song_from_playlist_endpoint(playlist_id: int, song_id: int):
    if playlist_id is None or song_id is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    if playlist_id == "" or song_id == "":
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        playlist = await remove_song_from_playlist(playlist_id, song_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    return {"message": "Song removed from playlist successfully"}


@app.delete("/stop")
async def stop_service_endpoint():
    await service.stop()
    exit(0)
