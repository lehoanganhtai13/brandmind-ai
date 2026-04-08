"""Server configuration for BrandMind API.

Reads from centralized SETTINGS (src/config/system_config.py).
Supports override via constructor args (e.g., CLI --port flag).
"""

from __future__ import annotations

from config.system_config import SETTINGS


class ServerConfig:
    """Configuration for the BrandMind API server.

    Attributes:
        host: Bind address for the server.
        port: Port number for the server.
        session_ttl: Time-to-live for idle sessions in seconds.
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        session_ttl: int | None = None,
    ) -> None:
        self.host = host or SETTINGS.BRANDMIND_HOST
        self.port = port or SETTINGS.BRANDMIND_PORT
        self.session_ttl = session_ttl or SETTINGS.BRANDMIND_SESSION_TTL
