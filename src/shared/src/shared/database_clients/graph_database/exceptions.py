class FalkorDBConnectionError(Exception):
    """Exception raised for errors connecting to FalkorDB."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class FalkorDBQueryError(Exception):
    """Exception raised for errors executing queries in FalkorDB."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class FalkorDBNodeError(Exception):
    """Exception raised for errors in node operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class FalkorDBRelationshipError(Exception):
    """Exception raised for errors in relationship operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class FalkorDBIndexError(Exception):
    """Exception raised for errors in index operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
