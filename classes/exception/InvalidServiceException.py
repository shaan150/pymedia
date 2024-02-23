class InvalidServiceException(Exception):
    """Exception raised when an invalid service is provided."""

    def __init__(self, message="Invalid Service. Please provide a valid service."):
        self.message = message
        super().__init__(self.message)