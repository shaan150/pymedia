class TokenCreationException(Exception):
    def __init__(self, message="Failed to generate token. Please try again."):
        self.message = message
        super().__init__(self.message)