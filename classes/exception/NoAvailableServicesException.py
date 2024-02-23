class NoAvailableServicesException(Exception):
    """Exception raised when no available services are found."""

    def __init__(self, message="No available services found"):
        self.message = message
        super().__init__(self.message)