import httpx

auth_service_url = "localhost:8001"


async def validate_user(username: str, session_id: str):
    url = f"{auth_service_url}/auth_user"
    response = httpx.get(url, params={"username": username, "session_id": session_id})
    return response.json()
