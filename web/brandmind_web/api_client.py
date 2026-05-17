"""HTTP / SSE client for the BrandMind backend.

Keeps the web sub-project self-contained per Task #89 Decision 4: the
backend ``BrandMindClient`` in ``src/cli/client.py`` is not imported
here because the web container ships independently of the
chatbot/CLI install. Functions are thin wrappers around
``httpx.AsyncClient`` and ``httpx_sse.aconnect_sse`` so the Reflex
state layer can stay focused on UI orchestration.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx
from httpx_sse import aconnect_sse

from .models import (
    ArtifactRef,
    DocxHtmlResponse,
    SessionInfo,
    SessionMessages,
    StreamDonePayload,
)

_HEALTH_TIMEOUT_SECONDS = 3
_CREATE_TIMEOUT_SECONDS = 10
_STREAM_CONNECT_TIMEOUT_SECONDS = 10
_STREAM_READ_TIMEOUT_SECONDS = 600


@dataclass(frozen=True)
class SSEEvent:
    """One decoded SSE event line from the stream.

    Carries the raw ``event`` name from the wire and the JSON-decoded
    ``data`` payload so the state layer can dispatch on event name
    without re-parsing the body. ``parsed`` is left as a plain dict so
    the state can decide whether to validate against a model or read a
    single field — this keeps the client cheap.
    """

    event: str
    data: dict


async def health_check(api_base_url: str) -> bool:
    """Return ``True`` when the backend ``/api/v1/health`` endpoint is reachable.

    Any 2xx response is treated as healthy; timeouts, connection errors,
    and non-2xx responses all read as unhealthy. The caller surfaces
    this back to the UI as the connected / disconnected status.

    Args:
        api_base_url (str): Backend base URL without trailing slash, for
            example ``"http://localhost:8000"``.

    Returns:
        connected (bool): ``True`` when the endpoint returned 2xx,
        ``False`` otherwise.
    """
    url = f"{api_base_url}/api/v1/health"
    try:
        async with httpx.AsyncClient(timeout=_HEALTH_TIMEOUT_SECONDS) as client:
            response = await client.get(url)
        return response.is_success
    except httpx.HTTPError:
        return False


async def create_brand_strategy_session(api_base_url: str) -> SessionInfo:
    """Create a fresh brand-strategy session on the backend.

    The web UI calls this once per browser session before the user
    sends their first message. The returned ``SessionInfo`` seeds the
    sidebar state — even if the scope is not yet classified, the
    ``phase_sequence`` and ``phase_display_labels`` fields arrive as
    empty placeholders that the sidebar can render as "loading".

    Args:
        api_base_url (str): Backend base URL.

    Returns:
        info (SessionInfo): The newly-created session metadata.

    Raises:
        httpx.HTTPError: On network failure or non-2xx response.
    """
    url = f"{api_base_url}/api/v1/sessions"
    payload = {"mode": "brand-strategy"}
    async with httpx.AsyncClient(timeout=_CREATE_TIMEOUT_SECONDS) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
    return SessionInfo.model_validate(response.json())


async def list_brand_strategy_sessions(api_base_url: str) -> list[SessionInfo]:
    """Fetch all known brand-strategy sessions on the backend.

    Powers the chat-picker in the sidebar. The web UI filters
    server-side ask-mode sessions out client-side because the brand
    strategy UI does not surface them.

    Args:
        api_base_url (str): Backend base URL.

    Returns:
        sessions (list[SessionInfo]): Every active session the backend
        currently exposes; the caller filters by mode if needed.

    Raises:
        httpx.HTTPError: On network failure or non-2xx response.
    """
    url = f"{api_base_url}/api/v1/sessions"
    async with httpx.AsyncClient(timeout=_CREATE_TIMEOUT_SECONDS) as client:
        response = await client.get(url)
        response.raise_for_status()
    raw = response.json()
    return [SessionInfo.model_validate(entry) for entry in raw]


async def get_session_messages(
    api_base_url: str, session_id: str
) -> SessionMessages:
    """Fetch persisted message history for a session.

    Called when the user switches between chats so the scroll can
    repaint the previous conversation. The endpoint omits tool calls
    and reasoning blocks — those are stream-only artefacts.

    Args:
        api_base_url (str): Backend base URL.
        session_id (str): Identifier returned by a prior session creation.

    Returns:
        messages (SessionMessages): Ordered list of user/agent turns.

    Raises:
        httpx.HTTPError: On network failure or non-2xx response.
    """
    url = f"{api_base_url}/api/v1/sessions/{session_id}/messages"
    async with httpx.AsyncClient(timeout=_CREATE_TIMEOUT_SECONDS) as client:
        response = await client.get(url)
        response.raise_for_status()
    return SessionMessages.model_validate(response.json())


async def update_session(
    api_base_url: str,
    session_id: str,
    *,
    title: str | None = None,
    pinned: bool | None = None,
) -> SessionInfo:
    """Patch a session's UX metadata (title / pinned) and return the new state.

    Both fields are optional. Sending ``title=""`` clears the title back
    to the sidebar placeholder; ``None`` means "leave unchanged".
    """
    url = f"{api_base_url}/api/v1/sessions/{session_id}"
    body: dict = {}
    if title is not None:
        body["title"] = title
    if pinned is not None:
        body["pinned"] = pinned
    async with httpx.AsyncClient(timeout=_CREATE_TIMEOUT_SECONDS) as client:
        response = await client.patch(url, json=body)
        response.raise_for_status()
    return SessionInfo.model_validate(response.json())


async def generate_session_title(
    api_base_url: str,
    session_id: str,
    message: str | None = None,
) -> SessionInfo:
    """Ask the backend to summarise the first user message into a chat title.

    Returns the updated ``SessionInfo`` so the caller can replace its
    cached entry in one step. When ``message`` is omitted the backend
    falls back to the persisted first ``HumanMessage`` on the session.
    """
    url = f"{api_base_url}/api/v1/sessions/{session_id}/title"
    body: dict = {}
    if message:
        body["message"] = message
    async with httpx.AsyncClient(timeout=_CREATE_TIMEOUT_SECONDS) as client:
        response = await client.post(url, json=body)
        response.raise_for_status()
    return SessionInfo.model_validate(response.json())


async def delete_session(api_base_url: str, session_id: str) -> None:
    """Remove a session from the backend."""
    url = f"{api_base_url}/api/v1/sessions/{session_id}"
    async with httpx.AsyncClient(timeout=_CREATE_TIMEOUT_SECONDS) as client:
        response = await client.delete(url)
        response.raise_for_status()


async def get_session(api_base_url: str, session_id: str) -> SessionInfo:
    """Fetch the current state of an existing session from the backend.

    Used to rehydrate sidebar state on reconnect or after the user
    navigates back to a previously-active session. The returned
    metadata is the same shape ``create_brand_strategy_session``
    returns.

    Args:
        api_base_url (str): Backend base URL.
        session_id (str): Identifier returned by a prior session creation.

    Returns:
        info (SessionInfo): The current session state.

    Raises:
        httpx.HTTPError: On network failure, 404, or other non-2xx.
    """
    url = f"{api_base_url}/api/v1/sessions/{session_id}"
    async with httpx.AsyncClient(timeout=_CREATE_TIMEOUT_SECONDS) as client:
        response = await client.get(url)
        response.raise_for_status()
    return SessionInfo.model_validate(response.json())


async def list_session_artifacts(
    api_base_url: str, session_id: str
) -> list[ArtifactRef]:
    """Fetch every artifact the backend recorded for one session.

    Powers the canvas pane's artifact list. The backend returns an
    empty list when the session has produced nothing yet — that is
    indistinguishable from "unknown session" and the canvas treats
    both as "no artifacts to show".

    Args:
        api_base_url (str): Backend base URL without trailing slash.
        session_id (str): Identifier of the session to query.

    Returns:
        refs (list[ArtifactRef]): Zero or more artifact references in
        manifest order (oldest first).

    Raises:
        httpx.HTTPError: On network failure or non-2xx response.
    """
    url = f"{api_base_url}/api/v1/sessions/{session_id}/artifacts"
    async with httpx.AsyncClient(timeout=_CREATE_TIMEOUT_SECONDS) as client:
        response = await client.get(url)
        response.raise_for_status()
    raw = response.json()
    return [ArtifactRef.model_validate(entry) for entry in raw]


async def fetch_artifact_html(
    api_base_url: str, session_id: str, filename: str
) -> DocxHtmlResponse:
    """Fetch the server-rendered HTML projection of a DOCX artifact.

    The canvas pane's DocxView consumes this payload to paint both the
    rendered body and the sticky table of contents without doing any
    DOCX parsing client-side. Only valid for artifacts of category
    ``documents``; the backend rejects other categories with 400.

    Args:
        api_base_url (str): Backend base URL without trailing slash.
        session_id (str): Owner of the artifact.
        filename (str): Artifact basename. Must end in ``.docx``.

    Returns:
        rendered (DocxHtmlResponse): HTML body + heading outline +
        mammoth warnings for the requested document.

    Raises:
        httpx.HTTPError: On network failure or non-2xx response.
    """
    url = f"{api_base_url}/api/v1/artifacts/{session_id}/{filename}/html"
    async with httpx.AsyncClient(timeout=_CREATE_TIMEOUT_SECONDS) as client:
        response = await client.get(url)
        response.raise_for_status()
    return DocxHtmlResponse.model_validate(response.json())


async def stream_message(
    api_base_url: str,
    session_id: str,
    content: str,
) -> AsyncIterator[SSEEvent]:
    """Yield SSE events from the backend message stream.

    Opens a streaming POST to ``/api/v1/sessions/{id}/message?stream=true``
    and yields one :class:`SSEEvent` per decoded SSE block. The agent's
    event taxonomy is documented in
    ``src/shared/.../callback_types.py``: ``streaming_token``,
    ``streaming_thinking``, ``thinking``, ``tool_call``, ``tool_result``,
    ``todo_update``, ``model_loading``, ``phase_advance``, plus the
    server-only ``done`` and ``error`` events. Consumers dispatch on
    ``event.event`` and validate ``event.data`` against the matching
    payload model when they need typed access.

    Args:
        api_base_url (str): Backend base URL.
        session_id (str): Target session identifier.
        content (str): User message content.

    Yields:
        events (SSEEvent): Stream of decoded SSE events in
        chronological order until the backend emits ``done`` (or
        ``error``), at which point the generator returns.
    """
    url = f"{api_base_url}/api/v1/sessions/{session_id}/message"
    timeout = httpx.Timeout(
        _STREAM_READ_TIMEOUT_SECONDS,
        connect=_STREAM_CONNECT_TIMEOUT_SECONDS,
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with aconnect_sse(
            client,
            "POST",
            url,
            params={"stream": "true"},
            json={"content": content},
        ) as event_source:
            async for sse in event_source.aiter_sse():
                try:
                    payload = json.loads(sse.data) if sse.data else {}
                except json.JSONDecodeError:
                    payload = {"raw": sse.data}
                yield SSEEvent(event=sse.event, data=payload)
                if sse.event in {"done", "error"}:
                    break


def extract_final_metadata(done_payload: dict) -> StreamDonePayload:
    """Validate a raw ``done`` payload into the typed ``StreamDonePayload``.

    Used by the state layer when it sees the ``done`` event so it can
    settle the agent message's tool-call list and refresh the sidebar
    metadata in one place.

    Args:
        done_payload (dict): Raw JSON-decoded body of the ``done`` event.

    Returns:
        payload (StreamDonePayload): The validated final-state payload.
    """
    return StreamDonePayload.model_validate(done_payload)
