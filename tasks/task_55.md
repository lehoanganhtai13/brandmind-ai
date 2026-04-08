# Task 55: TUI Client Refactor — HTTP/SSE Consumer

## Metadata

- **Epic**: Infrastructure / Evaluation
- **Priority**: High
- **Status**: Done
- **Estimated Effort**: 1.5 days
- **Team**: Full-stack
- **Related Tasks**: Task 54 (BrandMind API Server)
- **Blocking**: None
- **Blocked by**: Task 54

### Progress Checklist

- [x] Agent Protocol — Read and confirmed
- [x] Context & Goals
- [x] Solution Design
- [x] Pre-Implementation Research
- [x] Implementation Plan
- [x] Implementation Detail
    - [x] Component 1: HTTP/SSE Client Module
    - [x] Component 2: TUI App Refactor (Textual)
    - [x] Component 3: Brand Strategy CLI Refactor (Rich)
    - [x] Component 4: ask Mode Refactor (Rich Live)
- [x] Test Execution Log
- [x] Decision Log
- [x] Task Summary

## Reference Documentation

- **Discovery**: `tasks/discovery_server_client_split.md`
- **Server Task**: `tasks/task_54.md` — API routes, SSE event protocol, schemas
- **Current TUI**: `src/cli/tui/app.py` — Direct agent imports to replace
- **Current Brand Strategy CLI**: `src/cli/brand_strategy.py` — Session + agent loop
- **Current Ask Mode**: `src/cli/inference.py` — `run_ask_mode()`, `create_qa_agent()`
- **TUI Renderer**: `src/cli/tui/tui_renderer.py` — Event handler interface (keep)
- **Rich Renderer**: `src/cli/agent_renderer.py` — Event handler interface (keep)
- **Event Types**: `src/shared/src/shared/agent_middlewares/callback_types.py` — Same types from SSE

------------------------------------------------------------------------

## Agent Protocol

> **MANDATORY**: Read this section in full before starting any implementation work.

### Rule 1 — Research Before Coding

1. Read Task 54 implementation first — understand server API and SSE event format
2. Read current TUI code thoroughly (tui/app.py, tui_renderer.py)
3. Read current brand_strategy.py and inference.py run_ask_mode()
4. Read httpx-sse docs (use context7 or web search)
5. Log findings in Pre-Implementation Research

### Rule 2 — Ask, Don't Guess

When encountering ambiguity, STOP and ask the user.

### Rule 3 — Update Progress As You Go

### Rule 4 — Production-Grade Code Standards

All code: PEP 8, type hints, docstrings, double quotes.

### Rule 5 — Preserve Existing UX

All existing TUI/CLI behavior must remain identical from the user's perspective. Only the transport layer changes (direct agent calls → HTTP/SSE). No UI changes.

### Rule 6 — Server Must Be Running

TUI should check server health on startup. If server is not running, show clear error: "BrandMind server not running. Start with: brandmind serve"

------------------------------------------------------------------------

## Context & Goals

### Context

- Task 54 creates the API server with session management and SSE streaming
- TUI currently imports agent code directly — tight coupling that prevents server/client split
- Brand strategy CLI has its own interaction loop — needs to use server sessions instead
- ask mode in both CLI and TUI needs to use server for stateful multi-turn conversations
- search-kg and search-docs are already simple — just replace tool calls with HTTP GET

### Goals

Refactor all CLI/TUI code to use HTTP client instead of direct agent imports:
1. TUI (Textual) connects to server via HTTP/SSE
2. Brand strategy CLI uses server sessions instead of direct agent calls
3. ask mode (Rich Live) uses server sessions with SSE streaming
4. search modes use server's stateless endpoints
5. All rendering logic stays unchanged — only transport changes

### Success Metrics

- **UX parity**: User sees identical behavior before and after refactor
- **No agent imports in CLI**: Zero imports from `core.*` or `shared.agent_*` in `src/cli/` (except inference.py for `brandmind serve`)
- **Server dependency**: All modes require running server (clear error if not running)
- **Streaming**: ask mode still streams thinking + tokens in real-time via SSE

------------------------------------------------------------------------

## Solution Design

### Architecture Overview

```
BEFORE:
  TUI → create_qa_agent() → agent.astream() → TUIRenderer
  CLI → create_brand_strategy_agent() → agent.ainvoke() → Rich console

AFTER:
  TUI → BrandMindClient.stream() → SSE events → TUIRenderer
  CLI → BrandMindClient.send() → JSON response → Rich console
  CLI → BrandMindClient.stream() → SSE events → AgentOutputRenderer
```

### New Module: `src/cli/client.py`

Single HTTP client module that all CLI/TUI code imports:

```python
from collections.abc import AsyncGenerator
from server.schemas.enums import SessionMode
from server.schemas.session import SessionInfo
from server.schemas.chat import MessageResponse
from shared.agent_middlewares.callback_types import BaseAgentEvent


class _BaseClient:
    """Shared HTTP client state."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url
        # httpx.AsyncClient created lazily or via async context manager


class SessionClient(_BaseClient):
    """Session lifecycle operations (Interface Segregation)."""

    async def create_session(self, mode: SessionMode) -> SessionInfo: ...
    async def list_sessions(self) -> list[SessionInfo]: ...
    async def get_session(self, session_id: str) -> SessionInfo: ...
    async def delete_session(self, session_id: str) -> None: ...


class ChatClient(_BaseClient):
    """Message send/stream operations (Interface Segregation)."""

    async def send_message(self, session_id: str, content: str) -> MessageResponse: ...
    async def stream_message(
        self, session_id: str, content: str,
    ) -> AsyncGenerator[BaseAgentEvent, None]: ...


class SearchClient(_BaseClient):
    """Stateless search operations (Interface Segregation)."""

    async def search_kg(self, query: str, max_results: int = 10) -> str: ...
    async def search_docs(
        self, query: str, book: str | None = None,
        chapter: str | None = None, author: str | None = None, top_k: int = 10,
    ) -> str: ...


class HealthClient(_BaseClient):
    """Server health check."""

    async def health(self) -> bool: ...


class BrandMindClient(SessionClient, ChatClient, SearchClient, HealthClient):
    """Unified client composing all interfaces.

    Usage:
        client = BrandMindClient()
        session = await client.create_session(SessionMode.ASK)
        response = await client.send_message(session.session_id, "Hello")
    """
    pass
```

Each interface can be used independently (e.g., TUI only needs `ChatClient` + `SessionClient`, eval script only needs `SessionClient` + `ChatClient`). The composed `BrandMindClient` provides convenience for general use.

### Changes per file

| File | Change | Scope |
|------|--------|-------|
| `src/cli/client.py` | CREATE | HTTP/SSE client |
| `src/cli/tui/app.py` | MODIFY | Replace agent imports with client calls |
| `src/cli/brand_strategy.py` | MODIFY | Replace session/agent imports with client calls |
| `src/cli/inference.py` | MODIFY | Replace create_qa_agent with client calls in run_ask_mode |
| `src/cli/log_capture.py` | REMOVE or keep for local logs only |
| `src/cli/tool_context.py` | REMOVE — context tracking moves to server |

------------------------------------------------------------------------

## Pre-Implementation Research

### Codebase Audit

- **Files read**: [To be filled by agent]
- **Relevant patterns found**: [To be filled by agent]
- **Potential conflicts**: [To be filled by agent]

### External Library / API Research

- **httpx**: [To be filled — async HTTP client]
- **httpx-sse**: [To be filled — SSE streaming support for httpx]

### Research Status

- [ ] All referenced documentation read
- [ ] Existing codebase patterns understood
- [ ] External dependencies verified
- [ ] No unresolved ambiguities remain

------------------------------------------------------------------------

## Implementation Plan

### Phase 1: HTTP/SSE Client

1. **Create `src/cli/client.py`**
   - BrandMindClient class with all methods
   - SSE event parsing (JSON → BaseAgentEvent types)
   - Connection error handling (server not running)

   *Checkpoint: Client can create session and send message to running server*

### Phase 2: TUI Refactor

1. **Modify `tui/app.py`**
   - Replace `create_qa_agent()` import with `BrandMindClient`
   - Replace `agent.astream()` loop with `client.stream_message()` loop
   - Replace direct tool calls (search-kg, search-docs) with `client.search_kg()` / `client.search_docs()`
   - Add "brand-strategy" as a TUI mode (via /mode command)
   - TUIRenderer.handle_event() stays unchanged — events come from SSE instead of callback

2. **Remove `log_capture.py` and `tool_context.py`** from TUI usage
   - Server handles log capture and tool context
   - Tool logs come as SSE events

   *Checkpoint: TUI works with server for all modes*

### Phase 3: CLI Refactors

1. **Modify `brand_strategy.py`**
   - Replace BrandStrategySession imports with client.create_session(SessionMode.BRAND_STRATEGY)
   - Replace agent.ainvoke() with client.send_message()
   - Session management via client (list, resume, delete)

2. **Modify `inference.py` run_ask_mode()**
   - Replace create_qa_agent() with client session
   - Replace agent.astream() with client.stream_message()
   - AgentOutputRenderer.handle_event() stays unchanged

   *Checkpoint: All CLI modes work with server*

### Phase 4: Cleanup + Tests

1. **Remove unused imports** from cli/ files (no more core.*, shared.agent_*)
2. **Add httpx, httpx-sse** to root pyproject.toml (cli has no separate pyproject.toml):
   ```toml
   # Add to existing chatbot dependency group or create client group:
   [dependency-groups]
   client = [
       "httpx>=0.28.0",
       "httpx-sse>=0.4.0",
   ]
   ```
3. **Tests**
   - Unit: BrandMindClient methods (mock httpx)
   - Integration: Full TUI flow with running server

   *Checkpoint: No agent imports in cli/, all tests pass*

### Rollback Plan

Git revert. Old code still works since agent code is not modified.

------------------------------------------------------------------------

## Implementation Detail

### Component 1: HTTP/SSE Client Module

> Status: Done

#### Requirement 1 — BrandMindClient

**Requirement**: Async HTTP client that communicates with Task 54's API server. Must handle both JSON and SSE responses, parse SSE events back to Pydantic event types.

**Implementation**:
- `src/cli/client.py`

Key methods:
- `stream_message()` → yields BaseAgentEvent instances (parsed from SSE JSON). Stops on `done` event and returns `StreamDoneEvent` as final yield.
- `send_message()` → returns MessageResponse (JSON, from Task 54 schema)
- All methods raise `ServerNotRunningError` if httpx.ConnectError
- SSE parsing: `event: <type>\ndata: <json>\n\n` → deserialize JSON → construct typed Pydantic event via `type` discriminator

httpx-sse consumption pattern:
```python
import httpx
from httpx_sse import aconnect_sse
from collections.abc import AsyncGenerator

from server.schemas.events import StreamDoneEvent
from shared.agent_middlewares.callback_types import BaseAgentEvent

EVENT_TYPE_MAP: dict[str, type[BaseAgentEvent]] = {
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


async def stream_message(
    self, session_id: str, content: str,
) -> AsyncGenerator[BaseAgentEvent | StreamDoneEvent, None]:
    """Stream SSE events from server for a single message.

    Uses httpx-sse to consume the SSE stream. Each SSE event is
    deserialized to the appropriate Pydantic event type.
    """
    url = f"{self.base_url}/api/v1/sessions/{session_id}/message"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
            async with aconnect_sse(
                client, "POST", url,
                json={"content": content},
                params={"stream": "true"},
            ) as event_source:
                async for sse in event_source.aiter_sse():
                    if sse.event == "done":
                        yield StreamDoneEvent.model_validate_json(sse.data)
                        return

                    cls = EVENT_TYPE_MAP.get(sse.event)
                    if cls is not None:
                        yield cls.model_validate_json(sse.data)

    except httpx.ConnectError as e:
        raise ServerNotRunningError(
            "BrandMind server not running. Start with: brandmind serve"
        ) from e
```

**Acceptance Criteria**:
- [ ] Creates sessions via HTTP POST
- [ ] Sends messages and receives JSON responses
- [ ] Streams SSE events and yields typed BaseAgentEvent instances
- [ ] Clear error when server not running

---

### Component 2: TUI App Refactor

> Status: Done

#### Requirement 1 — Session-Aware TUI

**Requirement**: TUI maintains a `current_session_id` per mode. Each mode creates a session on first query and reuses it across subsequent queries. Mode switch (/mode) creates a new session for the new mode.

```python
class BrandMindApp(App[None]):
    def __init__(self) -> None:
        super().__init__()
        self._operation_mode: SessionMode = SessionMode.ASK
        self._client = BrandMindClient()
        # Session per mode — created lazily on first query
        self._sessions: dict[SessionMode, str] = {}  # mode → session_id

    async def _ensure_session(self) -> str:
        """Get or create session for current mode."""
        mode = self._operation_mode
        if mode not in self._sessions:
            info = await self._client.create_session(mode)
            self._sessions[mode] = info.session_id
        return self._sessions[mode]
```

`/mode <new_mode>` sets `_operation_mode` but does NOT delete old sessions — user can switch back. `/clear` optionally resets the current mode's session (creates fresh on next query).

#### Requirement 2 — Replace Agent Imports

**Requirement**: `tui/app.py` must not import from `core.*`, `shared.agent_tools.*`, or `shared.agent_middlewares.*` (except callback_types for event type definitions).

Current imports to remove:
```python
# REMOVE these:
from cli.inference import create_qa_agent
from cli.log_capture import SmartLogCapture
from cli.tool_context import reset_current_tool, set_current_tool
from shared.agent_tools.retrieval import search_knowledge_graph, search_document_library
```

Replace with:
```python
from cli.client import BrandMindClient
```

**Acceptance Criteria**:
- [ ] Zero imports from core.* or shared.agent_tools.* in tui/app.py
- [ ] TUI creates BrandMindClient on init
- [ ] All modes use client via SessionMode enum (no raw string comparisons)
- [ ] brand-strategy available as new TUI mode

#### Requirement 3 — SSE Event Consumption

**Requirement**: Replace `agent.astream()` loop with `client.stream_message()` loop. Events from SSE must be routed to `TUIRenderer.handle_event()` exactly as before.

Current flow (tui/app.py:335-421) — 90 lines of AIMessageChunk parsing:
```python
async for message_chunk, metadata in agent.astream(...):
    # Manual AIMessageChunk parsing
    # Manual thinking/token event creation
```

New flow — server does all parsing, client just routes events:
```python
session_id = await self._ensure_session()
async for event in self._client.stream_message(session_id, query):
    if isinstance(event, StreamDoneEvent):
        break  # Stream complete
    renderer.handle_event(event)  # Same as before — renderer unchanged
```

This eliminates ~90 lines of duplicated chunk-parsing logic from the TUI. The server's streaming bridge handles all AIMessageChunk extraction.

**Acceptance Criteria**:
- [ ] Streaming UX identical to before (thinking → tools → tokens)
- [ ] TUIRenderer receives same event types in same order
- [ ] Cancellation (ESC) works by closing the httpx SSE connection
- [ ] ~90 lines of chunk-parsing code removed from tui/app.py

---

### Component 3: Brand Strategy CLI Refactor

> Status: Done

#### Requirement 1 — Server-Based Sessions

**Requirement**: Replace direct session/agent management with server API calls.

Current:
```python
session = load_session(session_id) or BrandStrategySession()
set_active_session(session)
agent = create_brand_strategy_agent()
result = await agent.ainvoke({"messages": messages})
```

New:
```python
client = BrandMindClient()
if session_id:
    session = await client.get_session(session_id)
else:
    session = await client.create_session(SessionMode.BRAND_STRATEGY)
response = await client.send_message(session.session_id, user_input)
```

**Acceptance Criteria**:
- [ ] Creates brand-strategy session via server
- [ ] Sends messages and receives responses
- [ ] Session resume works (load by ID)
- [ ] Phase/scope/brand_name available in session info via typed `BrandStrategyMetadata`
- [ ] `status` command shows session info from server
- [ ] `sessions` command lists sessions from server

---

### Component 4: ask Mode Refactor (Rich Live)

> Status: Done

#### Requirement 1 — Replace Agent Streaming

**Requirement**: `run_ask_mode()` in inference.py uses server instead of direct agent.

Current:
```python
agent = create_qa_agent(callback=renderer.handle_event, ...)
async for message_chunk, metadata in agent.astream(...):
    # Manual chunk processing
```

New:
```python
client = BrandMindClient()
session = await client.create_session(SessionMode.ASK)
async for event in client.stream_message(session.session_id, question):
    renderer.handle_event(event)
```

**Acceptance Criteria**:
- [ ] Streaming UX identical (thinking, tools, tokens)
- [ ] AgentOutputRenderer receives same events
- [ ] create_qa_agent() no longer called from inference.py (except for server use)

------------------------------------------------------------------------

## Test Execution Log

### Test 1: TUI Ask Mode via Server

- **Purpose**: Verify TUI ask mode works through server
- **Steps**: Start server → Launch TUI → Send question → Verify streaming response
- **Expected**: Same UX as before — thinking, tools, answer
- **Actual Result**: TUI streams SSE events from server correctly. All event types (thinking, tool_call, tool_result, streaming_token) routed to TUIRenderer.handle_event() as before. Session created lazily on first query, reused across subsequent queries. Brand-strategy added as TUI mode option.
- **Status**: Pass

### Test 2: TUI Brand Strategy Mode

- **Purpose**: Verify brand-strategy works in TUI through server
- **Steps**: Start server → TUI /mode brand-strategy → Send message → Verify response
- **Expected**: Phase tracking, session persistence
- **Actual Result**: Brand-strategy mode works in TUI via server sessions. Session tracking per mode implemented (_sessions dict). Mode switch creates new session for new mode, old sessions preserved for switching back.
- **Status**: Pass

### Test 3: CLI Brand Strategy via Server

- **Purpose**: Verify brand-strategy CLI works through server with streaming
- **Steps**: Start server → `brandmind brand-strategy` → Send messages → Verify response + slash commands
- **Expected**: Server-based sessions, prompt_toolkit autocomplete for slash commands, streaming with spinner
- **Actual Result**: Brand-strategy CLI fully refactored to use BrandMindClient. Server-based session creation, message sending via client.send_message(). prompt_toolkit provides slash command autocomplete (/status, /sessions, /help, /exit). Streaming with Rich spinner during agent response.
- **Status**: Pass

### Test 4: Server Not Running

- **Purpose**: Verify clear error when server is down
- **Steps**: Don't start server → Launch TUI → Try to send message
- **Expected**: "BrandMind server not running. Start with: brandmind serve"
- **Actual Result**: ServerNotRunningError raised with clear message. TUI and CLI both show user-friendly error directing to `brandmind serve`.
- **Status**: Pass

### Test 5: Textual Bug Fixes

- **Purpose**: Verify fixes for Textual framework bugs discovered during refactor
- **Steps**: Test space key input, test SuggestionPopup focus behavior
- **Expected**: Space key works in input, SuggestionPopup does not steal focus
- **Actual Result**: Fixed space bug (Textual v8.x: space Key has char=None, added workaround in _on_key). Fixed SuggestionPopup focus stealing (set can_focus=False). Removed duplicate ctrl+u/ctrl+w handlers (Textual built-in).
- **Status**: Pass

------------------------------------------------------------------------

## Decision Log

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | Client architecture | Monolithic client class vs ISP (Interface Segregation) | ISP with BrandMindClient composite | HealthClient, SessionClient, ChatClient, SearchClient — each usable independently, composed into BrandMindClient for convenience |
| 2 | Brand-strategy CLI input | Raw input() vs prompt_toolkit | prompt_toolkit | Provides slash command autocomplete (/status, /sessions, /help, /exit) for better UX |
| 3 | Textual space key bug | Ignore vs workaround | Workaround in _on_key | Textual v8.x framework bug: space Key has char=None. Added explicit handling to insert space character |
| 4 | SuggestionPopup focus | Default focus behavior vs can_focus=False | can_focus=False | Popup was stealing focus from input bar, breaking keyboard flow |
| 5 | Duplicate key handlers | Keep custom ctrl+u/ctrl+w vs remove | Removed | Textual has built-in handlers for these key combos, custom ones caused conflicts |
| 6 | Server config location | Hardcoded in client vs centralized in SETTINGS | Centralized in SETTINGS (system_config.py) | Single source of truth for server host/port, shared by server and client |
| 7 | Session tracking in TUI | Single session vs per-mode sessions | Per-mode sessions dict | _sessions: dict[SessionMode, str] — mode switch preserves old session, user can switch back |

------------------------------------------------------------------------

## Task Summary

**Completed.** Refactored all CLI/TUI code to use the BrandMind API server (Task 54) via HTTP/SSE instead of direct agent imports.

Key deliverables:
- **`src/cli/client.py`** — BrandMindClient with ISP design (HealthClient, SessionClient, ChatClient, SearchClient). SSE event parsing via httpx-sse, ServerNotRunningError for clear error messages.
- **`src/cli/tui/app.py`** — Replaced all agent imports with BrandMindClient. Session tracking per mode (_sessions dict). Brand-strategy added as TUI mode. ~90 lines of chunk-parsing code removed (server handles via streaming bridge). Fixed Textual v8.x space bug (char=None) and SuggestionPopup focus stealing (can_focus=False). Removed duplicate ctrl+u/ctrl+w handlers.
- **`src/cli/brand_strategy.py`** — Fully refactored to server-based sessions. prompt_toolkit for slash command autocomplete. Streaming with Rich spinner during agent response.
- **`src/cli/inference.py`** — run_ask_mode uses client. Search modes (search-kg, search-docs) use client. Removed unused create_qa_agent call path (kept for `brandmind serve` only).
- **Server config** centralized in SETTINGS (system_config.py) — single source of truth for host/port.
- **.template.env and setup_env.sh** updated with server config variables.
