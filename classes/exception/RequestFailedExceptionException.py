class RequestFailedException(Exception):
    """Exception raised when a request fails after all retries."""
    def __init__(self, message="Request failed after retries", *args):
        super().__init__(message, *args)