from hashlib import pbkdf2_hmac
from binascii import hexlify


async def hash_password(password: str, salt: bytes):
    return pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
