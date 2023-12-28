import asyncio
import time

from fastapi import WebSocket


class User:
    def __init__(self, username: str, token: str = ''):
        self.username = username
        self.token = token
        self.last_heartbeat = time.localtime()

    async def receive_text(self):
        return await self.websocket.receive_text()

    async def receive_json(self):
        return await self.websocket.receive_json()

    async def send_message(self, message: str):
        await self.websocket.send_text(message)

    async def send_json(self, message):
        await self.websocket.send_json(message)

    async def ping(self):
        await self.websocket.send_text("ping")

    async def receive_heartbeat(self, timeout=60):
        try:
            # Wait for a pong response with a timeout
            await asyncio.wait_for(self.websocket.receive_text(), timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def heartbeat(self):
        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            await self.websocket.send_text("ping")
            if await self.receive_heartbeat():
                self.last_heartbeat = time.time()
                return True
            else:
                retry_count += 1

        return False  # User did not respond after retries

    async def close(self):
        await self.websocket.close()

    def __str__(self):
        return f"User(username={self.username}, token={self.token}, email={self.email})"
