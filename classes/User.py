class User:
    def __init__(self, username: str, token: str = ''):
        self.username = username
        self.token = token

    def __str__(self):
        return f"User(username={self.username}, token={self.token})"
