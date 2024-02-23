import unittest
from unittest.mock import patch, AsyncMock

from fastapi import HTTPException
from jwt import PyJWTError

from classes.exception.TokenCreationException import TokenCreationException
from classes.services.AuthService import AuthService


@patch('builtins.open', unittest.mock.mock_open(read_data='{"main_service_url": "http://example.com"}'))
class TestUserAuthentication(unittest.IsolatedAsyncioTestCase):
    """
    TestUserAuthentication

    Unit tests for the UserAuthentication class.

    """
    async def test_hash_password(self):
        """
        Test method for hashing a password using AuthService.hash_password.

        :return: None
        """
        password = "test_password"
        salt = b"test_salt"  # Ensure this is bytes

        # Call the static method directly without instance
        hashed_password = await AuthService().hash_password(password, salt)

        # Assertions
        self.assertIsNotNone(hashed_password)

    @patch('classes.services.AuthService.AuthService.get_secret_key', new_callable=AsyncMock)
    @patch('jwt.encode')
    async def test_generate_token_success(self, mock_jwt_encode, mock_get_secret_key):
        """
        Test case to verify the successful generation of a token.

        :param mock_jwt_encode: A mock object for the `jwt.encode` function.
        :param mock_get_secret_key: A mock object for the `AuthService.get_secret_key` method.
        :return: None
        """
        mock_secret_key = "mocked_secret_key"
        mock_get_secret_key.return_value = mock_secret_key
        mock_jwt_encode.return_value = "mocked_token"

        auth_service = AuthService()
        token = await auth_service.generate_token("test_username")

        self.assertEqual(token, "mocked_token")
        mock_get_secret_key.assert_awaited_once()
        mock_jwt_encode.assert_called_once()

    async def test_generate_token_no_username(self):
        """
        Test case to ensure that an HTTPException is raised when no username is provided to the generate_token method.

        :return: None
        """
        auth_service = AuthService()
        with self.assertRaises(HTTPException) as context:
            await auth_service.generate_token(None)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "No username provided")

    @patch('classes.services.AuthService.AuthService.get_secret_key', new_callable=AsyncMock)
    async def test_generate_token_creation_exception(self, mock_get_secret_key):
        """
        Test if an error occurred while creating a token.

        :param mock_get_secret_key: Mock function for AuthService.get_secret_key.
        :return: None
        """
        mock_get_secret_key.side_effect = Exception("Mock exception")

        auth_service = AuthService()
        with self.assertRaises(TokenCreationException) as context:
            await auth_service.generate_token("test_username")

        self.assertIn("An error occurred while creating token", str(context.exception))

    @patch('classes.services.AuthService.AuthService.get_secret_key', new_callable=AsyncMock)
    @patch('jwt.decode')
    async def test_decode_token_success(self, mock_jwt_decode, mock_get_secret_key):
        """
        :param mock_jwt_decode: The mock function for jwt.decode that will be used during the test.
        :param mock_get_secret_key: The mock function for AuthService.get_secret_key that will be used during the test.
        :return: None
        """
        # Setup mocks
        mock_get_secret_key.return_value = "mocked_secret_key"
        mock_decoded_token = {"user": "test_user"}
        mock_jwt_decode.return_value = mock_decoded_token

        # Create an instance of AuthService
        auth_service = AuthService()

        # Use a structurally correct mock token for clarity, even though jwt.decode is mocked
        mock_token = "header.payload.signature"
        decoded_token = await auth_service.decode_token(mock_token)

        # Assertions
        self.assertEqual(decoded_token, mock_decoded_token)
        mock_jwt_decode.assert_called_once_with(mock_token, "mocked_secret_key",
                                                algorithms=["HS256"])  # Adjust algorithm as needed
    @patch('classes.services.AuthService.AuthService.get_secret_key', new_callable=AsyncMock)
    @patch('starlette.concurrency.run_in_threadpool', new_callable=AsyncMock)
    async def test_decode_token_type_error(self, mock_get_secret_key, mock_run_in_threadpool):
        """
        :param mock_get_secret_key: Mock object for the `get_secret_key` method of `AuthService`.
        :param mock_run_in_threadpool: Mock object for the `run_in_threadpool` function of `starlette.concurrency`.
        :return: None
        """
        # Setup to raise TypeError, which should be caught and raise PyJWTError
        mock_get_secret_key.return_value = "mocked_secret_key"
        mock_run_in_threadpool.side_effect = TypeError("Invalid token format")

        auth_service = AuthService()

        with self.assertRaises(PyJWTError) as context:
            await auth_service.decode_token("invalid_token")

        self.assertIn("Invalid token", str(context.exception))
