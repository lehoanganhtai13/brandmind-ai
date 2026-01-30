"""
Custom exceptions for search tools.

Exception hierarchy follows Python standard conventions (similar to `requests` library):
- SearchError (base)
  ├── SearchValidationError (input validation issues)
  ├── APIKeyNotFoundError (authentication issues)
  ├── SearchAPIError (HTTP/API response errors)
  ├── SearchTimeoutError (request timeout)
  ├── SearchConnectionError (network issues)
  └── SearchResponseError (parsing/data issues)
"""

from typing import Any


class SearchError(Exception):
    """Base exception for all search-related errors."""

    pass


class SearchValidationError(SearchError):
    """Raised when input validation fails (e.g., too many queries, empty input)."""

    def __init__(self, message: str, field: str = "", value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(message)


class APIKeyNotFoundError(SearchError):
    """Raised when API key is not found in environment variables."""

    def __init__(self, provider: str, env_var: str):
        self.provider = provider
        self.env_var = env_var
        super().__init__(
            f"{provider} API key not found. Please set {env_var} environment variable."
        )


class SearchAPIError(SearchError):
    """Raised when search API returns an error response."""

    def __init__(self, provider: str, status_code: int, response_text: str = ""):
        self.provider = provider
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(f"{provider} API error: {status_code} - {response_text}")


class SearchTimeoutError(SearchError):
    """Raised when search API request times out."""

    def __init__(self, provider: str, query: str = ""):
        self.provider = provider
        self.query = query
        msg = f"{provider} request timed out"
        if query:
            msg += f" for query: {query}"
        super().__init__(msg)


class SearchConnectionError(SearchError):
    """Raised when unable to connect to the search API."""

    def __init__(self, provider: str, error: str = ""):
        self.provider = provider
        self.error = error
        msg = f"{provider} connection failed"
        if error:
            msg += f": {error}"
        super().__init__(msg)


class SearchResponseError(SearchError):
    """Raised when unable to parse or process search response."""

    def __init__(self, provider: str, error: str = ""):
        self.provider = provider
        self.error = error
        msg = f"{provider} response error"
        if error:
            msg += f": {error}"
        super().__init__(msg)
