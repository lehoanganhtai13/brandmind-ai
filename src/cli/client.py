"""HTTP/SSE client for BrandMind API server.

Provides typed interfaces for session management, message sending,
streaming, and search. Uses Interface Segregation Principle.

Usage:
    client = BrandMindClient()
    session = await client.create_session(SessionMode.ASK)
    async for event in client.stream_message(session.session_id, "Hello"):
        renderer.handle_event(event)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import httpx
from httpx_sse import aconnect_sse

from server.schemas.chat import MessageResponse
from server.schemas.enums import SessionMode
from server.schemas.events import StreamDoneEvent
from server.schemas.session import SessionInfo
from shared.agent_middlewares.callback_types import (
    BaseAgentEvent,
    ModelLoadingEvent,
    StreamingThinkingEvent,
    StreamingTokenEvent,
    ThinkingEvent,
    TodoUpdateEvent,
    ToolCallEvent,
    ToolResultEvent,
)

# Map SSE event type strings to Pydantic event classes
_EVENT_TYPE_MAP: dict[str, type[BaseAgentEvent]] = {
    "model_loading": ModelLoadingEvent,
    "thinking": ThinkingEvent,
    "streaming_thinking": StreamingThinkingEvent,
    "tool_call": ToolCallEvent,
    "tool_result": ToolResultEvent,
    "todo_update": TodoUpdateEvent,
    "streaming_token": StreamingTokenEvent,
}


class ServerNotRunningError(ConnectionError):
    """Raised when the BrandMind server is not reachable."""

    pass


class _BaseClient:
    """Shared HTTP client configuration.

    Default base_url is constructed from SETTINGS (BRANDMIND_HOST/PORT).
    Can be overridden explicitly for testing or remote servers.
    """

    def __init__(self, base_url: str | None = None) -> None:
        if base_url is None:
            from config.system_config import SETTINGS

            host = SETTINGS.BRANDMIND_HOST
            port = SETTINGS.BRANDMIND_PORT
            # Use localhost for client even if server binds 0.0.0.0
            if host == "0.0.0.0":  # nosec B104
                host = "localhost"
            base_url = f"http://{host}:{port}"
        self._base_url = base_url

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"


class HealthClient(_BaseClient):
    """Server health check."""

    async def health(self) -> bool:
        """Check if the server is running and healthy.

        Returns:
            True if server responds with 200.

        Raises:
            ServerNotRunningError: If the server is not reachable.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self._url("/api/v1/health"), timeout=5.0)
                return resp.status_code == 200
        except httpx.ConnectError as e:
            raise ServerNotRunningError(
                "BrandMind server not running. Start with: brandmind serve"
            ) from e


class SessionClient(_BaseClient):
    """Session lifecycle operations."""

    async def create_session(self, mode: SessionMode) -> SessionInfo:
        """Create a new session with the specified mode.

        Args:
            mode: Session mode (ASK or BRAND_STRATEGY).

        Returns:
            SessionInfo with session_id and initial metadata.

        Raises:
            ServerNotRunningError: If the server is not reachable.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self._url("/api/v1/sessions"),
                    json={"mode": mode.value},
                    timeout=10.0,
                )
                resp.raise_for_status()
                return SessionInfo.model_validate(resp.json())
        except httpx.ConnectError as e:
            raise ServerNotRunningError(
                "BrandMind server not running. Start with: brandmind serve"
            ) from e

    async def list_sessions(self) -> list[SessionInfo]:
        """List all active sessions.

        Returns:
            List of SessionInfo for all active sessions.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self._url("/api/v1/sessions"), timeout=10.0)
                resp.raise_for_status()
                return [SessionInfo.model_validate(s) for s in resp.json()]
        except httpx.ConnectError as e:
            raise ServerNotRunningError(
                "BrandMind server not running. Start with: brandmind serve"
            ) from e

    async def get_session(self, session_id: str) -> SessionInfo:
        """Get session info by ID.

        Args:
            session_id: Session identifier.

        Returns:
            SessionInfo with current session state.

        Raises:
            httpx.HTTPStatusError: If session not found (404).
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    self._url(f"/api/v1/sessions/{session_id}"),
                    timeout=10.0,
                )
                resp.raise_for_status()
                return SessionInfo.model_validate(resp.json())
        except httpx.ConnectError as e:
            raise ServerNotRunningError(
                "BrandMind server not running. Start with: brandmind serve"
            ) from e

    async def delete_session(self, session_id: str) -> None:
        """Delete a session and clean up resources.

        Args:
            session_id: Session identifier.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.delete(
                    self._url(f"/api/v1/sessions/{session_id}"),
                    timeout=10.0,
                )
                resp.raise_for_status()
        except httpx.ConnectError as e:
            raise ServerNotRunningError(
                "BrandMind server not running. Start with: brandmind serve"
            ) from e


class ChatClient(_BaseClient):
    """Message send/stream operations."""

    async def send_message(self, session_id: str, content: str) -> MessageResponse:
        """Send a message and wait for the complete response.

        Non-streaming mode — blocks until the agent finishes.

        Args:
            session_id: Target session ID.
            content: User message text.

        Returns:
            MessageResponse with full response text, metadata, tool calls.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self._url(f"/api/v1/sessions/{session_id}/message"),
                    json={"content": content},
                    params={"stream": "false"},
                    timeout=httpx.Timeout(300.0),
                )
                resp.raise_for_status()
                return MessageResponse.model_validate(resp.json())
        except httpx.ConnectError as e:
            raise ServerNotRunningError(
                "BrandMind server not running. Start with: brandmind serve"
            ) from e

    async def stream_message(
        self, session_id: str, content: str
    ) -> AsyncGenerator[BaseAgentEvent | StreamDoneEvent, None]:
        """Stream SSE events from the server for a message.

        Yields typed event instances parsed from the SSE stream.
        The final event is always StreamDoneEvent with the complete
        response and updated metadata.

        Args:
            session_id: Target session ID.
            content: User message text.

        Yields:
            BaseAgentEvent subclass instances, then StreamDoneEvent.

        Raises:
            ServerNotRunningError: If the server is not reachable.
        """
        url = self._url(f"/api/v1/sessions/{session_id}/message")
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
                async with aconnect_sse(
                    client,
                    "POST",
                    url,
                    json={"content": content},
                    params={"stream": "true"},
                ) as event_source:
                    async for sse in event_source.aiter_sse():
                        if sse.event == "done":
                            yield StreamDoneEvent.model_validate_json(sse.data)
                            return

                        if sse.event == "error":
                            return

                        cls = _EVENT_TYPE_MAP.get(sse.event)
                        if cls is not None:
                            yield cls.model_validate_json(sse.data)

        except httpx.ConnectError as e:
            raise ServerNotRunningError(
                "BrandMind server not running. Start with: brandmind serve"
            ) from e


class SearchClient(_BaseClient):
    """Stateless search operations (no session required)."""

    async def search_kg(self, query: str, max_results: int = 10) -> str:
        """Search the Knowledge Graph.

        Args:
            query: Conceptual query about marketing.
            max_results: Maximum results to return.

        Returns:
            Formatted markdown results from KG search.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    self._url("/api/v1/search/kg"),
                    params={"q": query, "max_results": max_results},
                    timeout=60.0,
                )
                resp.raise_for_status()
                return resp.json()["result"]
        except httpx.ConnectError as e:
            raise ServerNotRunningError(
                "BrandMind server not running. Start with: brandmind serve"
            ) from e

    async def search_docs(
        self,
        query: str,
        book: str | None = None,
        chapter: str | None = None,
        author: str | None = None,
        top_k: int = 10,
    ) -> str:
        """Search the Document Library with optional filters.

        Args:
            query: Text to search for in documents.
            book: Filter by book name (exact match).
            chapter: Filter by chapter (partial match).
            author: Filter by author (exact match).
            top_k: Number of results to return.

        Returns:
            Formatted text results from document search.
        """
        params: dict[str, str | int] = {"q": query, "top_k": top_k}
        if book:
            params["book"] = book
        if chapter:
            params["chapter"] = chapter
        if author:
            params["author"] = author

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    self._url("/api/v1/search/docs"),
                    params=params,
                    timeout=60.0,
                )
                resp.raise_for_status()
                return resp.json()["result"]
        except httpx.ConnectError as e:
            raise ServerNotRunningError(
                "BrandMind server not running. Start with: brandmind serve"
            ) from e


class BrandMindClient(HealthClient, SessionClient, ChatClient, SearchClient):
    """Unified client composing all interfaces.

    Each interface can be used independently (e.g., TUI only needs
    ChatClient + SessionClient). The composed BrandMindClient provides
    convenience for general use.

    Usage:
        client = BrandMindClient()
        session = await client.create_session(SessionMode.ASK)
        response = await client.send_message(session.session_id, "Hello")
    """

    pass
