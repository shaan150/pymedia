from typing import Optional

from fastapi import HTTPException, Request

from utils.DatabaseAsyncQuery import create_user, get_user, create_song, get_song, create_playlist, get_playlists, \
    add_song_to_playlist, get_user_by_password, get_songs, remove_song_from_playlist, get_playlist_songs
from classes.pydantic.Playlist import Playlist
from classes.pydantic.Song import Song
from classes.pydantic.UserAccount import UserAccount
from classes.services.DatabaseService import DatabaseService

service = DatabaseService()

app = service.app


@app.get("/")
async def root():
    """
    This method is an HTTP GET handler for the root endpoint ("/"). It is used to fetch service data using the `service.fetch_service_data()` method.

    .. code-block:: python

        async def root():
            return await service.fetch_service_data()

    :return: None
    """
    return await service.fetch_service_data()

@app.post("/users/user/create")
async def create_user_endpoint(user: UserAccount):
    """
    Create a user endpoint.

    :param user: UserAccount object containing user information.
    :return: Dictionary with the detail of the user creation status.
    :rtype: Dict[str, str]
    """
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
    """
    :param username: The username of the user to retrieve.
    :return: A dictionary containing the username and email of the user.
    """
    try:
        user: UserAccount = await get_user(username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user[0], "email": user[1]}


@app.get("/users/user/salt")
async def get_user_endpoint(username: str):
    """
    Retrieve the salt for a user.

    :param username: The username of the user.
    :return: A dictionary containing the salt of the user.

    :raises HTTPException 500: If there is an internal server error while retrieving the user.
    :raises HTTPException 404: If the user is not found.

    """
    try:
        user: UserAccount = await get_user(username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"salt": user[2]}


@app.post("/users/user/validate")
async def validate_user_endpoint(user: UserAccount):
    """
    :param user: UserAccount object that contains the user's username and password
    :return: A dictionary with the detail of the validation process

    This method validates a user by checking their username and password. It takes a UserAccount object as a parameter,
    which contains the user's username and password. If the user parameter is None, it raises an HTTPException with a status_code of 400 and detail message "Invalid Request".

    The method then calls the get_user_by_password function to check if the username and password combination is valid.
    If an exception occurs during the execution of the get_user_by_password function, it raises an HTTPException with a status_code of 500 and the exception message as detail.

    If the result returned by get_user_by_password is None, it raises an HTTPException with a status_code of 401 and detail message "Not Valid Password".

    If the user is validated successfully, it returns a dictionary with the detail message "User Validated".
    """
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
    """
    :param song: The Song object representing the song to be created.
    :return: A dictionary containing the detail of the operation and the newly created song's ID.

    This method is used to create a new song in the system. It takes a Song object as input, which contains the necessary information about the song. The method first checks if the given
    * song is None. If it is, an HTTPException with a status code of 400 and detail message of "Invalid Request" is raised.

    Next, it checks if a song with the same artist and name already exists by calling the get_songs method. If an exception occurs during the database query, an HTTPException with a status
    * code of 500 and the exception message is raised.

    If a song with the same artist and name is found, an HTTPException with a status code of 409 and detail message of "Song already exists" is raised.

    If no existing song is found, the method proceeds to create a new song by calling the create_song method. If an exception occurs during the creation process, an HTTPException with a
    * status code of 500 and the exception message is raised.

    If the song creation is successful, a dictionary containing the detail message "Song created successfully" and the ID of the newly created song is returned.

    Note: Make sure to import the necessary modules and set up the appropriate routing configuration for the create_song_endpoint method to work correctly.
    """
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
    """
    This method retrieves a song based on the provided song ID.

    :param song_id: The ID of the song to retrieve.
    :return: A JSON object containing the song details.
    :raises HTTPException 400: if the request is invalid (song ID is None or empty).
    :raises HTTPException 404: if the song is not found.
    :raises HTTPException 500: if an error occurs while retrieving the song.
    """
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
    """
    :param playlist: The playlist object containing the playlist details.
    :return: Returns a dictionary with a message indicating the success of creating the playlist.

    """
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
    """
    This method is the endpoint for retrieving songs. It accepts two optional parameters.

    :param name: The name of the song to filter by. Defaults to None if not provided.
    :param artist: The name of the artist to filter by. Defaults to None if not provided.
    :return: A list of dictionaries representing each song that matches the given criteria.
    :raises HTTPException 500: If there is an error while retrieving songs from the database.
    :raises HTTPException 404: If no songs are found matching the given criteria.
    """
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
    """
    :param username: Optional. The username of the user you want to get playlists for. If not provided, all playlists will be returned.

    :param playlist_name: Optional. The name of the playlist you want to retrieve. If not provided, all playlists for the user will be returned.

    :return: A list of dictionaries representing the playlists. Each dictionary contains the following keys: 'playlist_id', 'playlist_name', and 'username'.
    """
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
    """
    :param playlist_id: The ID of the playlist to retrieve
    :return: The playlist information as a dictionary
    :raises HTTPException: If the request is invalid, if there is an error retrieving the playlist, or if the playlist is not found
    """
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
    """
    :param playlist_id: The ID of the playlist for which to retrieve songs.
    :return: A list of songs found in the specified playlist.

    This endpoint retrieves the songs associated with the given playlist ID. It first checks if the playlist ID is provided, and if not, it throws a HTTPException with a status code of
    *400 (Bad Request).

    Next, it calls the `get_playlist_songs` function with the provided playlist ID to fetch the songs data from the database. If any error occurs during this process, a HTTPException with
    * a status code of 500 (Internal Server Error) is raised.

    If no songs are found for the specified playlist ID, a HTTPException with a status code of 404 (Not Found) is raised.

    Finally, it creates a list of dictionaries representing each song using the retrieved songs data. Each dictionary contains the song ID, song name, artist, and md5 information. The list
    * of songs is then returned.

    Note: This method assumes the existence of a `get_playlist_songs` function that retrieves songs data based on the provided playlist ID.
    """
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
    """
    Adds a song to a playlist.

    :param request: The request object containing the playlist ID and song ID.
    :return: A dictionary with a message indicating if the song was added successfully.

    :raises HTTPException: If the request is invalid or the song cannot be added to the playlist.
    :raises Exception: If an error occurs while adding the song to the playlist.
    """
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
    """
    Remove a song from a playlist.

    :param playlist_id: The ID of the playlist.
    :param song_id: The ID of the song.
    :return: A dictionary containing a success message.
    :raises HTTPException 400: If the request is invalid.
    :raises HTTPException 404: If the playlist is not found.
    :raises HTTPException 500: If an error occurs while removing the song from the playlist.
    """
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
    """
    Stop the service.

    :return: None
    """
    await service.stop()
    exit(0)
