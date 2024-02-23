class InvalidRequestMethodException(Exception):
    """Exception raised for an invalid request method."""
    def __init__(self, message="Invalid Request Method", *args):
        super().__init__(message, *args)