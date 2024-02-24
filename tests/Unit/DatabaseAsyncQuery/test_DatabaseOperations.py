import unittest
from unittest.mock import patch, MagicMock
from utils.DatabaseAsyncQuery import create_tables, create_user, get_user_salt, get_user, \
    create_song, get_user_email, get_user_by_password, get_song, get_songs, create_playlist, \
    get_songs_by_playlist, get_playlists, add_song_to_playlist, remove_song_from_playlist  # Adjust the import path


class TestDatabaseOperations(unittest.IsolatedAsyncioTestCase):
    @patch('sqlite3.connect')
    async def test_create_tables(self, mock_connect):
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        await create_tables()

        # Assertions to ensure SQL execution
        self.assertTrue(mock_cursor.execute.called)
        self.assertTrue(mock_conn.commit.called)

    @patch('utils.DatabaseAsyncQuery.run_in_executor', new_callable=MagicMock)
    @patch('sqlite3.connect')
    async def test_create_user(self, mock_connect, mock_run_in_executor):
        # Mock `run_in_executor` to directly call the synchronous function
        async def async_wrapper(func, *args):
            return func(*args)

        mock_run_in_executor.side_effect = async_wrapper

        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        result = await create_user("test_user", "password123", "salt123", "test@example.com")

        # Assertions
        mock_cursor.execute.assert_called_with(
            "INSERT INTO users (username, password, salt, email) VALUES (?, ?, ?, ?)",
            ("test_user", "password123", "salt123", "test@example.com")
        )
        self.assertTrue(mock_conn.commit.called)

    @patch('utils.DatabaseAsyncQuery.run_in_executor', new_callable=MagicMock)
    @patch('sqlite3.connect')
    async def test_get_user_salt(self, mock_connect, mock_run_in_executor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ('some_salt',)
        mock_connect.return_value.cursor.return_value = mock_cursor

        async def async_wrapper(func, *args):
            return func(*args)
        mock_run_in_executor.side_effect = async_wrapper

        salt = await get_user_salt("test_user")
        self.assertEqual(salt, ('some_salt',))
        mock_cursor.execute.assert_called_with("SELECT salt FROM users WHERE username = ?", ("test_user",))

    @patch('utils.DatabaseAsyncQuery.run_in_executor', new_callable=MagicMock)
    @patch('sqlite3.connect')
    async def test_get_user(self, mock_connect, mock_run_in_executor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("test_user", "test@example.com", "some_salt")
        mock_connect.return_value.cursor.return_value = mock_cursor

        async def async_wrapper(func, *args):
            return func(*args)
        mock_run_in_executor.side_effect = async_wrapper

        user_info = await get_user("test_user")
        self.assertEqual(user_info, ("test_user", "test@example.com", "some_salt"))
        mock_cursor.execute.assert_called_with("SELECT username, email, salt FROM users WHERE username = ?", ("test_user",))


    @patch('utils.DatabaseAsyncQuery.run_in_executor', new_callable=MagicMock)
    @patch('sqlite3.connect')
    async def test_create_song(self, mock_connect, mock_run_in_executor):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1  # Simulate successful row insertion
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        async def async_wrapper(func, *args):
            return func(*args)
        mock_run_in_executor.side_effect = async_wrapper

        result = await create_song("song_id", "song_name", "artist", "md5hash", "test_user")
        self.assertTrue(result)
        mock_cursor.execute.assert_called_with(
            "INSERT INTO songs (song_id, song_name, artist, md5, username) VALUES (?, ?, ?, ?, ?)",
            ("song_id", "song_name", "artist", "md5hash", "test_user")
        )

    @patch('utils.DatabaseAsyncQuery.run_in_executor', new_callable=MagicMock)
    @patch('sqlite3.connect')
    async def test_get_user_email(self, mock_connect, mock_run_in_executor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("test_user",)
        mock_connect.return_value.cursor.return_value = mock_cursor

        async def async_wrapper(func, *args):
            return func(*args)

        mock_run_in_executor.side_effect = async_wrapper

        username = await get_user_email("test@example.com")
        self.assertEqual(username, ("test_user",))
        mock_cursor.execute.assert_called_with("SELECT username FROM users WHERE email = ?", ("test@example.com",))

    @patch('utils.DatabaseAsyncQuery.run_in_executor', new_callable=MagicMock)
    @patch('sqlite3.connect')
    async def test_get_user_by_password(self, mock_connect, mock_run_in_executor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("test_user",)
        mock_connect.return_value.cursor.return_value = mock_cursor

        async def async_wrapper(func, *args):
            return func(*args)

        mock_run_in_executor.side_effect = async_wrapper

        username = await get_user_by_password("test_user", "password123")
        self.assertEqual(username, ("test_user",))
        mock_cursor.execute.assert_called_with("SELECT username FROM users WHERE username = ? AND password = ?",
                                               ("test_user", "password123"))

    @patch('utils.DatabaseAsyncQuery.run_in_executor', new_callable=MagicMock)
    @patch('sqlite3.connect')
    async def test_get_song(self, mock_connect, mock_run_in_executor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("song_id", "song_name", "artist", "md5", "test_user")
        mock_connect.return_value.cursor.return_value = mock_cursor

        async def async_wrapper(func, *args):
            return func(*args)

        mock_run_in_executor.side_effect = async_wrapper

        song_info = await get_song("song_id")
        self.assertEqual(song_info, ("song_id", "song_name", "artist", "md5", "test_user"))
        mock_cursor.execute.assert_called_with("SELECT * FROM songs WHERE song_id = ?", ("song_id",))


    @patch('utils.DatabaseAsyncQuery.run_in_executor', new_callable=MagicMock)
    @patch('sqlite3.connect')
    async def test_get_songs(self, mock_connect, mock_run_in_executor):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("song_id1", "song_name1", "artist1", "md5_1", "test_user"),
                                             ("song_id2", "song_name2", "artist2", "md5_2", "test_user")]
        mock_connect.return_value.cursor.return_value = mock_cursor

        async def async_wrapper(func, *args):
            return func(*args)
        mock_run_in_executor.side_effect = async_wrapper

        songs = await get_songs("song_name1", "artist1")
        self.assertEqual(len(songs), 2)
        self.assertIn(("song_id1", "song_name1", "artist1", "md5_1", "test_user"), songs)
        mock_cursor.execute.assert_called()

    @patch('utils.DatabaseAsyncQuery.run_in_executor', new_callable=MagicMock)
    @patch('sqlite3.connect')
    async def test_create_playlist(self, mock_connect, mock_run_in_executor):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        async def async_wrapper(func, *args):
            return func(*args)

        mock_run_in_executor.side_effect = async_wrapper

        result = await create_playlist("playlist_id", "playlist_name", "test_user")
        self.assertTrue(result)
        mock_cursor.execute.assert_called_with(
            "INSERT INTO playlists (playlist_id, playlist_name, username) VALUES (?, ?, ?)",
            ("playlist_id", "playlist_name", "test_user"))

    @patch('utils.DatabaseAsyncQuery.run_in_executor', new_callable=MagicMock)
    @patch('sqlite3.connect')
    async def test_get_songs_by_playlist(self, mock_connect, mock_run_in_executor):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("song_id", "song_name", "artist", "md5", "test_user")]
        mock_connect.return_value.cursor.return_value = mock_cursor

        async def async_wrapper(func, *args):
            return func(*args)
        mock_run_in_executor.side_effect = async_wrapper

        songs = await get_songs_by_playlist("playlist_id")
        self.assertEqual(len(songs), 1)
        self.assertIn(("song_id", "song_name", "artist", "md5", "test_user"), songs)
        mock_cursor.execute.assert_called()

    @patch('utils.DatabaseAsyncQuery.run_in_executor', new_callable=MagicMock)
    @patch('sqlite3.connect')
    async def test_get_playlists(self, mock_connect, mock_run_in_executor):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("playlist_id1", "playlist_name1", "test_user"),
                                             ("playlist_id2", "playlist_name2", "test_user")]
        mock_connect.return_value.cursor.return_value = mock_cursor

        async def async_wrapper(func, *args):
            return func(*args)
        mock_run_in_executor.side_effect = async_wrapper

        playlists = await get_playlists("test_user")
        self.assertEqual(len(playlists), 2)
        self.assertIn(("playlist_id1", "playlist_name1", "test_user"), playlists)
        mock_cursor.execute.assert_called()

    @patch('utils.DatabaseAsyncQuery.run_in_executor', new_callable=MagicMock)
    @patch('sqlite3.connect')
    async def test_add_song_to_playlist(self, mock_connect, mock_run_in_executor):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        async def async_wrapper(func, *args):
            return func(*args)
        mock_run_in_executor.side_effect = async_wrapper

        result = await add_song_to_playlist("playlist_id", "song_id")
        self.assertTrue(result)
        mock_cursor.execute.assert_called_with("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)",
                                               ("playlist_id", "song_id"))

    @patch('utils.DatabaseAsyncQuery.run_in_executor', new_callable=MagicMock)
    @patch('sqlite3.connect')
    async def test_remove_song_from_playlist(self, mock_connect, mock_run_in_executor):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        async def async_wrapper(func, *args):
            return func(*args)

        mock_run_in_executor.side_effect = async_wrapper

        result = await remove_song_from_playlist("playlist_id", "song_id")
        self.assertTrue(result)
        mock_cursor.execute.assert_called_with("DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?",
                                               ("playlist_id", "song_id"))











