import asyncio
import sqlite3


async def run_in_executor(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)


def create_tables_sync():
    conn = sqlite3.connect("media_db.db")
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
    await run_in_executor(create_tables_sync)


def create_user_sync(username, password, salt, email):
    conn = sqlite3.connect("media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, salt, email) VALUES (?, ?, ?, ?)",
                       (username, password, salt, email))
        conn.commit()
        return cursor.lastrowid is not None
    finally:
        conn.close()


async def create_user(username, password, salt, email):
    return await run_in_executor(create_user_sync, username, password, salt, email)


def get_user_salt_sync(username):
    conn = sqlite3.connect("media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT salt FROM users WHERE username = ?", (username,))
        return cursor.fetchone()
    finally:
        conn.close()


async def get_user_salt(username):
    return await run_in_executor(get_user_salt_sync, username)


def get_user_sync(username):
    conn = sqlite3.connect("media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username, email, salt FROM users WHERE username = ?", (username,))
        return cursor.fetchone()
    finally:
        conn.close()


async def get_user(username):
    return await run_in_executor(get_user_sync, username)


def get_user_email_sync(email):
    conn = sqlite3.connect("media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE email = ?", (email,))
        return cursor.fetchone()
    finally:
        conn.close()


async def get_user_email(email):
    return await run_in_executor(get_user_email_sync, email)


def get_user_by_password_sync(username, password):
    conn = sqlite3.connect("media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ? AND password = ?", (username, password))
        return cursor.fetchone()
    finally:
        conn.close()


async def get_user_by_password(username, password):
    return await run_in_executor(get_user_by_password_sync, username, password)


def create_song_sync(song_id, song_name, artist, md5, username):
    conn = sqlite3.connect("media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO songs (song_id, song_name, artist, md5, username) VALUES (?, ?, ?, ?, ?)",
                       (song_id, song_name, artist, md5, username))
        conn.commit()
        return cursor.lastrowid is not None
    finally:
        conn.close()


async def create_song(song_id, song_name, artist, md5, username):
    return await run_in_executor(create_song_sync, song_id, song_name, artist, md5, username)


def get_song_sync(song_id):
    conn = sqlite3.connect("media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM songs WHERE song_id = ?", (song_id,))
        return cursor.fetchone()
    finally:
        conn.close()


async def get_song(song_id):
    return await run_in_executor(get_song_sync, song_id)


def get_songs_sync(song_name, artist):
    conn = sqlite3.connect("media_db.db")
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
    return await run_in_executor(get_songs_sync, song_name, artist)


def create_playlist_sync(playlist_id, playlist_name, username):
    conn = sqlite3.connect("media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO playlists (playlist_id, playlist_name, username) VALUES (?, ?, ?)",
                       (playlist_id, playlist_name, username))
        conn.commit()
        return cursor.lastrowid is not None
    finally:
        conn.close()


async def create_playlist(playlist_id, playlist_name, username):
    return await run_in_executor(create_playlist_sync, playlist_id, playlist_name, username)


def get_songs_by_playlist_sync(playlist_id):
    conn = sqlite3.connect("media_db.db")
    try:
        cursor = conn.cursor()
        # create a link between the playlist and the songs for the song details
        cursor.execute("SELECT * FROM songs WHERE song_id IN (SELECT song_id FROM playlist_songs WHERE playlist_id = ?)"
                       ,(playlist_id,))
        return cursor.fetchall()
    finally:
        conn.close()


async def get_songs_by_playlist(playlist_id):
    return await run_in_executor(get_songs_by_playlist_sync, playlist_id)


def get_playlists_sync(username, playlist_name, playlist_id):
    conn = sqlite3.connect("media_db.db")
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
    return await run_in_executor(get_playlists_sync, username, playlist_name, playlist_id)


def add_song_to_playlist_sync(playlist_id, song_id):
    conn = sqlite3.connect("media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)",
                       (playlist_id, song_id))
        conn.commit()
        return cursor.lastrowid is not None
    finally:
        conn.close()


async def add_song_to_playlist(playlist_id, song_id):
    return await run_in_executor(add_song_to_playlist_sync, playlist_id, song_id)


def remove_song_from_playlist_sync(playlist_id, song_id):
    conn = sqlite3.connect("media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?",
                       (playlist_id, song_id))
        conn.commit()
        return cursor.lastrowid is not None
    finally:
        conn.close()


def get_playlist_songs_sync(playlist_id):
    conn = sqlite3.connect("media_db.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
        return cursor.fetchall()
    finally:
        conn.close()


async def get_playlist_songs(playlist_id):
    return await run_in_executor(get_playlist_songs_sync, playlist_id)


async def remove_song_from_playlist(playlist_id, song_id):
    return await run_in_executor(remove_song_from_playlist_sync, playlist_id, song_id)

