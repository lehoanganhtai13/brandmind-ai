class LoadCrapelessDeepSerpTokenError(Exception):
    """Exception raised for errors in loading the Crapeless DeepSerp API key."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)