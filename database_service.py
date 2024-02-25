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
        result = await get_user(user.username)
        if result:
            raise HTTPException(status_code=409, detail="User already exists")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=422, detail="Could not create song")

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
    song_json = {"song_id": song[0], "song_name": song[1], "artist": song[2],
                 "md5": song[3], "username": song[4]}
    return song_json


@app.get("/songs")
async def get_songs_endpoint(name: Optional[str] = None, artist: Optional[str] = None, username: Optional[str] = None):
    """
    This method is the endpoint for retrieving songs. It accepts two optional parameters.

    :param name: The name of the song to filter by. Defaults to None if not provided.
    :param artist: The name of the artist to filter by. Defaults to None if not provided.
    :return: A list of dictionaries representing each song that matches the given criteria.
    :raises HTTPException 500: If there is an error while retrieving songs from the database.
    :raises HTTPException 404: If no songs are found matching the given criteria.
    """
    try:
        songs_sql = await get_songs(name, artist, username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not songs_sql or len(songs_sql) == 0:
        raise HTTPException(status_code=404, detail="No songs found with that name")

    songs = [Song(song_id=row[0], song_name=row[1], artist=row[2], md5=row[3]).dict() for row in songs_sql]
    return songs


@app.delete("/stop")
async def stop_service_endpoint():
    """
    Stop the service.

    :return: None
    """
    await service.stop()
    exit(0)
