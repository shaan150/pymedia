class FailedServiceCreationException(Exception):
    """Exception raised when an invalid service is provided."""

    def __init__(self, message="Failed to create service. Please try again."):
        self.message = message
        super().__init__(self.message)