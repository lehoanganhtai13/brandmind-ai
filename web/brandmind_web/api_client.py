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

from .models import SessionInfo, StreamDonePayload

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
