import asyncio
import sqlite3


async def run_in_executor(func, *args):
    """
    Execute a function in a separate thread using asyncio's run_in_executor.

    :param func: The function to execute.
    :param args: The arguments to pass to the function.
    :return: A coroutine that will resolve with the result of the function execution.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)


def create_tables_sync():
    """
    Create tables in the media database synchronously.

    :return: None
    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        tables_sql = {
            'users': '''
                            CREATE TABLE IF NOT EXISTS users (
                                username TEXT PRIMARY KEY,
                                email TEXT NOT NULL,
                                password TEXT NOT NULL,
                                salt TEXT NOT NULL
                            );
                        ''',
            'songs': '''
                            CREATE TABLE IF NOT EXISTS songs (
                                song_id TEXT PRIMARY KEY,
                                song_name TEXT NOT NULL,
                                artist TEXT NOT NULL,
                                md5 TEXT NOT NULL,
                                username TEXT NOT NULL,
                                FOREIGN KEY (username) REFERENCES users(username),
                                UNIQUE (song_name, artist)
                            );
                        ''',
            'playlists': '''
                            CREATE TABLE IF NOT EXISTS playlists (
                                playlist_id TEXT PRIMARY KEY,
                                playlist_name TEXT NOT NULL,
                                username TEXT NOT NULL,
                                FOREIGN KEY (username) REFERENCES users(username)
                            );
                        ''',
            'playlist_songs': '''
                            CREATE TABLE IF NOT EXISTS playlist_songs (
                                playlist_id INTEGER,
                                song_id INTEGER,
                                FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id),
                                FOREIGN KEY (song_id) REFERENCES songs(song_id)
                            );
                        '''
        }
        for create_sql in tables_sql.values():
            cursor.execute(create_sql)
        conn.commit()
    finally:
        conn.close()


async def create_tables():
    """
    Create tables.

    :return: None
    """
    await run_in_executor(create_tables_sync)


def create_user_sync(username, password, salt, email):
    """
    Create a user synchronously.

    :param username: The username of the user.
    :param password: The password of the user.
    :param salt: The salt for the password.
    :param email: The email address of the user.
    :return: True if the user was successfully created, False otherwise.
    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, salt, email) VALUES (?, ?, ?, ?)",
                       (username, password, salt, email))
        conn.commit()
        return cursor.lastrowid is not None
    finally:
        conn.close()


async def create_user(username, password, salt, email):
    """
    .. py:function:: create_user(username, password, salt, email)

       This method is used to create a user with the given parameters.

       :param username: The username of the user.
       :type username: str
       :param password: The password of the user.
       :type password: str
       :param salt: The salt used for password encryption.
       :type salt: str
       :param email: The email address of the user.
       :type email: str
       :return: Returns a coroutine object that creates a user.
       :rtype: Coroutine[None, None, None]

    """
    return await run_in_executor(create_user_sync, username, password, salt, email)


def get_user_salt_sync(username):
    """
    :param username: The username of the user for which to retrieve the salt.
    :return: The salt associated with the given username, or None if the user does not exist.

    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT salt FROM users WHERE username = ?", (username,))
        return cursor.fetchone()
    finally:
        conn.close()


async def get_user_salt(username):
    """
    :param username: The username of the user for which to retrieve the salt.
    :return: The salt associated with the specified user.
    """
    return await run_in_executor(get_user_salt_sync, username)


def get_user_sync(username):
    """
    :param username: The username of the user to retrieve from the database.
    :return: A tuple containing the username, email, and salt of the user with the specified username.
    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username, email, salt FROM users WHERE username = ?", (username,))
        return cursor.fetchone()
    finally:
        conn.close()


async def get_user(username):
    """
    :param username: The username of the user to retrieve
    :return: The user object with the specified username
    """
    return await run_in_executor(get_user_sync, username)


def get_user_email_sync(email):
    """
    :param email: The email of the user whose email is to be retrieved.
    :return: The email of the user as a string, or None if the email does not exist in the database.

    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE email = ?", (email,))
        return cursor.fetchone()
    finally:
        conn.close()


async def get_user_email(email):
    """
    Method to retrieve the email address of the user.

    :param email: The email address of the user.
    :return: The email address of the user.
    """
    return await run_in_executor(get_user_email_sync, email)


def get_user_by_password_sync(username, password):
    """
    Retrieves a user from the database based on the given username and password.

    :param username: The username of the user.
    :param password: The password of the user.
    :return: A tuple containing the username of the user if found, or None if not found.
    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ? AND password = ?", (username, password))
        return cursor.fetchone()
    finally:
        conn.close()


async def get_user_by_password(username, password):
    """
    Retrieves a user based on the provided username and password.

    :param username: The username of the user.
    :param password: The password of the user.
    :return: The user object.
    """
    return await run_in_executor(get_user_by_password_sync, username, password)


def create_song_sync(song_id, song_name, artist, md5, username):
    """
    :param song_id: The ID of the song.
    :param song_name: The name of the song.
    :param artist: The name of the artist.
    :param md5: The MD5 hash of the song.
    :param username: The username of the user who created the song.
    :return: A boolean value indicating whether the song was successfully created.

    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO songs (song_id, song_name, artist, md5, username) VALUES (?, ?, ?, ?, ?)",
                       (song_id, song_name, artist, md5, username))
        conn.commit()
        return cursor.lastrowid is not None
    finally:
        conn.close()


async def create_song(song_id, song_name, artist, md5, username):
    """
    Create a new song.

    :param song_id: The ID of the song.
    :param song_name: The name of the song.
    :param artist: The artist of the song.
    :param md5: The MD5 hash of the song.
    :param username: The username of the user creating the song.
    :return: None
    """
    return await run_in_executor(create_song_sync, song_id, song_name, artist, md5, username)


def get_song_sync(song_id):
    """
    :param song_id: The ID of the song to retrieve
    :return: Returns the song with the given ID from the media database

    This method connects to the media database, retrieves the song with the given song_id,
    and returns it as a result. If no song is found with the given ID, None is returned.
    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM songs WHERE song_id = ?", (song_id,))
        return cursor.fetchone()
    finally:
        conn.close()


async def get_song(song_id):
    """Retrieve a song by its ID.

    :param song_id: The ID of the song to retrieve.
    :return: The requested song.

    """
    return await run_in_executor(get_song_sync, song_id)


def get_songs_sync(song_name, artist):
    """
    :param song_name: The name of the song to search for (optional)
    :param artist: The artist of the song to search for (optional)
    :return: A list of songs matching the given criteria

    This method queries the "songs" table in the "media_db.db" SQLite database and returns a list of songs
    matching the provided song name and artist. If both parameters are None, it returns all songs in the table.

    If only the song_name parameter is provided, it searches for songs with that specific name.
    If only the artist parameter is provided, it searches for songs by that specific artist.
    If both song_name and artist parameters are provided, it searches for songs matching both criteria.

    Example usage:
    songs = get_songs_sync("Song Name", "Artist")
    print(songs)
    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()

        query = "SELECT * FROM songs"
        if song_name is not None and artist is not None:
            query += " WHERE song_name = ? AND artist = ?"
            cursor.execute(query, (song_name, artist))
        elif song_name is not None:
            query += " WHERE song_name = ?"
            cursor.execute(query, (song_name,))
        elif artist is not None:
            query += " WHERE artist = ?"
            cursor.execute(query, (artist,))
        else:
            cursor.execute(query)

        return cursor.fetchall()
    finally:
        conn.close()


async def get_songs(song_name, artist):
    """
    :param song_name: The name of the song.
    :param artist: The name of the artist.
    :return: A list of songs matching the given song_name and artist.
    """
    return await run_in_executor(get_songs_sync, song_name, artist)


def create_playlist_sync(playlist_id, playlist_name, username):
    """
    :param playlist_id: The ID of the playlist to be created.
    :param playlist_name: The name of the playlist to be created.
    :param username: The username of the user who is creating the playlist.
    :return: True if the playlist was created successfully, False otherwise.

    This method creates a new playlist in the media database. It connects to the database, inserts the playlist details (ID, name, and username) into the playlists table, and commits the
    * changes. The method then returns True if the playlist was created successfully, or False otherwise.

    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO playlists (playlist_id, playlist_name, username) VALUES (?, ?, ?)",
                       (playlist_id, playlist_name, username))
        conn.commit()
        return cursor.lastrowid is not None
    finally:
        conn.close()


async def create_playlist(playlist_id, playlist_name, username):
    """
    Create a playlist with the given playlist_id, playlist_name, and username.

    :param playlist_id: The ID of the playlist to create.
    :type playlist_id: str
    :param playlist_name: The name of the playlist to create.
    :type playlist_name: str
    :param username: The username of the user creating the playlist.
    :type username: str
    :return: None
    :rtype: None
    """
    return await run_in_executor(create_playlist_sync, playlist_id, playlist_name, username)


def get_songs_by_playlist_sync(playlist_id):
    """
    :param playlist_id: The ID of the playlist for which to retrieve the songs.
    :return: A list of songs associated with the specified playlist.

    This method retrieves the songs associated with a specific playlist from the database.
    The `playlist_id` parameter specifies the ID of the playlist for which to retrieve the songs.
    The method establishes a connection to the database, executes a query to retrieve the songs, and returns the result as a list of tuples, where each tuple represents a song.

    Example usage:
        playlist_id = 1
        songs = get_songs_by_playlist_sync(playlist_id)

    Please note that this method assumes the existence of a database named 'media_db.db' in the parent directory of the current script.

    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        # create a link between the playlist and the songs for the song details
        cursor.execute("SELECT * FROM songs WHERE song_id IN (SELECT song_id FROM playlist_songs WHERE playlist_id = ?)"
                       ,(playlist_id,))
        return cursor.fetchall()
    finally:
        conn.close()


async def get_songs_by_playlist(playlist_id):
    """
    Retrieves songs from a playlist based on the given playlist ID.

    :param playlist_id: The ID of the playlist to retrieve songs from.
    :return: The songs in the playlist.
    """
    return await run_in_executor(get_songs_by_playlist_sync, playlist_id)


def get_playlists_sync(username, playlist_name, playlist_id):
    """
    Retrieve playlists from the media database synchronously.

    :param username: The username associated with the playlists to retrieve.
    :param playlist_name: The name of the playlist to retrieve.
    :param playlist_id: The ID of the playlist to retrieve.
    :return: A list of playlists matching the specified criteria.

    Example usage:
        >>> playlists = get_playlists_sync("john_doe", "My Playlist", None)
        >>> for playlist in playlists:
        >>>     print(playlist)
        ('My Playlist', 'john_doe', 1, '2021-07-15 10:30:00')
    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM playlists"
        if playlist_id is not None:
            query += " WHERE playlist_id = ?"
            cursor.execute(query, (playlist_id,))
            return cursor.fetchone()

        if playlist_name is not None and username is not None:
            query += " WHERE playlist_name = ? AND username = ?"
            cursor.execute(query, (playlist_name, username))
        elif username is not None:
            query += " WHERE username = ?"
            cursor.execute(query, (username,))
        elif playlist_name is not None:
            query += " WHERE playlist_name = ?"
            cursor.execute(query, (playlist_name,))
        else:
            cursor.execute(query)

        return cursor.fetchall()
    finally:
        conn.close()


async def get_playlists(username=None, playlist_name=None, playlist_id=None):
    """
    Get playlists from the server.

    :param username: The username of the user whose playlists should be retrieved. If not provided, all playlists will be returned.
    :param playlist_name: The name of the playlist to search for. Only playlists with a matching name will be returned. If not provided, all playlists will be returned.
    :param playlist_id: The ID of the playlist to search for. Only the playlist with the matching ID will be returned. If not provided, all playlists will be returned.
    :return: A list of playlists matching the search parameters.
    """
    return await run_in_executor(get_playlists_sync, username, playlist_name, playlist_id)


def add_song_to_playlist_sync(playlist_id, song_id):
    """

    :param playlist_id: The ID of the playlist to which the song will be added.
    :param song_id: The ID of the song to be added to the playlist.
    :return: True if the song was successfully added to the playlist, False otherwise.

    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)",
                       (playlist_id, song_id))
        conn.commit()
        return cursor.lastrowid is not None
    finally:
        conn.close()


async def add_song_to_playlist(playlist_id, song_id):
    """
    Add a song to a playlist.

    :param playlist_id: The ID of the playlist to add the song to.
    :param song_id: The ID of the song to be added.
    :return: A coroutine that adds the song to the given playlist.
    """
    return await run_in_executor(add_song_to_playlist_sync, playlist_id, song_id)


def remove_song_from_playlist_sync(playlist_id, song_id):
    """
    Remove a song from a playlist synchronously.

    :param playlist_id: The ID of the playlist from which to remove the song.
    :param song_id: The ID of the song to be removed.
    :return: True if the song was successfully removed, False otherwise.
    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?",
                       (playlist_id, song_id))
        conn.commit()
        return cursor.lastrowid is not None
    finally:
        conn.close()


def get_playlist_songs_sync(playlist_id):
    """
    :param playlist_id: The ID of the playlist for which to retrieve the songs.
    :return: A list of tuples representing the songs in the playlist.

    """
    conn = sqlite3.connect("../media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
        return cursor.fetchall()
    finally:
        conn.close()


async def get_playlist_songs(playlist_id):
    """
    Retrieve songs from a playlist.

    :param playlist_id: The ID of the playlist to retrieve songs from.
    :return: A list of songs in the playlist.
    """
    return await run_in_executor(get_playlist_songs_sync, playlist_id)


async def remove_song_from_playlist(playlist_id, song_id):
    """
    Remove a song from a playlist.

    :param playlist_id: The ID of the playlist.
    :type playlist_id: int
    :param song_id: The ID of the song to be removed.
    :type song_id: int
    :return: A coroutine that will remove the song from the playlist.
    :rtype: Coroutine
    """
    return await run_in_executor(remove_song_from_playlist_sync, playlist_id, song_id)

