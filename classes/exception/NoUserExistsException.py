class NoUserExistsError(Exception):
    """Exception raised when an invalid service is provided."""

    def __init__(self, message="No user exists with the provided details. Please provide a valid details."):
        self.message = message
        super().__init__(self.message)