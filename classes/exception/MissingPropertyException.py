class MissingPropertyException(Exception):
    """Exception raised for an invalid request method."""
    def __init__(self, message="Property not found in file", *args):
        super().__init__(message, *args)