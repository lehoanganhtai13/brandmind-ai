# Discovery: Server/Client Architecture Split

> **Purpose**: Pre-planning for splitting BrandMind's monolithic CLI into a server (agent logic) + client (TUI/API consumers) architecture.
>
> **Motivation**: Enable eval automation (Claude Code sends HTTP requests), future web client, and clean separation of concerns.

## Metadata

- **Date Started**: 2026-04-06
- **Initiated by**: User + Agent
- **Status**: Decided
- **Related Epic**: Infrastructure / Evaluation
- **Output**: tasks/task_54.md, tasks/task_55.md

### Discovery Checklist

- [x] Problem Definition — Confirmed with user
- [x] Clarifying Questions — All answered
- [x] Research & Analysis — Agent research complete
- [x] Options Analysis — Approach confirmed by user
- [x] Decision — User has confirmed the approach
- [x] Task Breakdown — Tasks created and linked

------------------------------------------------------------------------

## Problem Definition

### Problem Statement

**The problem**: BrandMind's TUI directly imports and calls agent code (create_qa_agent, agent.astream, agent.ainvoke). This makes it impossible to interact with the agent without running the TUI interactively. Claude Code cannot send turn-by-turn messages for evaluation, and no HTTP API exists for external consumers.

**Who is affected**: Evaluation pipeline (blocked), future web client (not possible), any non-TUI consumer.

**Why now**: Evaluation is the immediate priority. All eval infrastructure is ready but cannot run because there's no programmatic API to interact with BrandMind.

**Definition of done**: `brandmind serve` starts an HTTP server. Clients send messages via `POST /api/v1/sessions/:id/message` and receive responses (JSON or SSE stream). TUI uses HTTP client instead of direct agent imports.

### Scope Boundary

| In Scope | Out of Scope |
|----------|--------------|
| FastAPI server with session management | Web frontend (future) |
| SSE streaming for real-time events | Authentication/authorization |
| All existing modes (ask, brand-strategy, search-kg, search-docs) | Multi-user/multi-tenant |
| TUI refactored to use HTTP client | Mobile client |
| `brandmind serve` CLI command | Load balancing / horizontal scaling |
| brand-strategy as a session mode in server | Database-backed persistence (file-based is fine) |

------------------------------------------------------------------------

## Research & Analysis

### Codebase Audit

**Current architecture** (monolithic):
```
main() → inference.py
├── No args → BrandMindApp (Textual TUI)
│   ├── Directly imports create_qa_agent()
│   ├── Calls agent.astream() inline
│   ├── Processes AIMessageChunk manually
│   └── 3 modes: ask, search-kg, search-docs (stateless)
│
├── brand-strategy → run_brand_strategy_session()
│   ├── Directly imports create_brand_strategy_agent()
│   ├── Calls agent.ainvoke() in while loop
│   ├── Manages session (create/load/save) directly
│   └── Rich console.input() for interaction
│
├── ask → run_ask_mode() (Rich Live + streaming)
├── search-kg → direct tool call
└── search-docs → direct tool call
```

**3 critical coupling points:**

| Coupling | File:Line | What crosses boundary |
|----------|-----------|----------------------|
| Agent creation | tui/app.py:303 | `create_qa_agent()` import |
| Streaming chunks | tui/app.py:335-421 | `AIMessageChunk` processing |
| Session + agent | brand_strategy.py:48-68 | Session create/load + `agent.ainvoke()` |

**Event architecture (already well-designed):**
- 7 event types in `callback_types.py` — all Pydantic BaseModel, JSON-serializable
- Both renderers (AgentOutputRenderer, TUIRenderer) share `handle_event(BaseAgentEvent)` interface
- Events are the complete data contract — UI reads zero agent state directly

**Event catalog:**

| Event Type | Source | Data Fields | Rate |
|------------|--------|-------------|------|
| `ModelLoadingEvent` | Middleware | loading: bool | 2x/turn |
| `ThinkingEvent` | Middleware | thinking: str | ~1x/turn |
| `StreamingThinkingEvent` | Stream loop | token: str, done: bool | ~200-500x |
| `ToolCallEvent` | Middleware | tool_name, arguments | 1-5x/turn |
| `ToolResultEvent` | Middleware | tool_name, result | 1-5x/turn |
| `TodoUpdateEvent` | Middleware | todos: list | ~1x/turn |
| `StreamingTokenEvent` | Stream loop | token: str, done: bool | ~200-1000x |

### Technology Research

| Technology | Version | Purpose | Key Findings |
|------------|---------|---------|--------------|
| FastAPI | latest | HTTP server | Native SSE support since v0.135.0 |
| sse-starlette | latest | SSE with disconnect detection | 3-layer disconnect handling, CancelledError cleanup |
| httpx | latest | Async HTTP client for TUI | Supports SSE via httpx-sse, async streaming |

### Key Constraints

- **Performance**: Agent initialization is heavy (~2-5s). Must stay in memory across turns, not re-create per request.
- **Streaming**: Both thinking tokens and response tokens must stream in real-time for TUI UX.
- **Session state**: Brand strategy sessions have complex state (phase, scope, workspace files). Must persist across turns.
- **Backward compatibility**: `brandmind` (no args) should still launch TUI. New command: `brandmind serve`.

------------------------------------------------------------------------

## Decision

### Chosen Approach

**Decision**: FastAPI server + HTTP/SSE client in TUI

**Rationale**: Event architecture already exists and maps 1:1 to SSE. Minimal new code — server wraps existing agent factories, TUI replaces imports with HTTP calls. Unblocks eval immediately.

### Architecture

```
brandmind serve (FastAPI server, port 8000)
├── SessionManager (in-memory agents + disk persistence)
│   ├── "ask" mode → create_qa_agent() — now stateful with history
│   └── "brand-strategy" mode → create_brand_strategy_agent()
│
├── POST /api/v1/sessions              → create session
├── GET  /api/v1/sessions              → list sessions
├── GET  /api/v1/sessions/:id          → get session info
├── DELETE /api/v1/sessions/:id        → delete session
├── POST /api/v1/sessions/:id/message  → send message (JSON or SSE)
│     ?stream=true  → SSE (thinking + tools + tokens)
│     ?stream=false → JSON (complete response)
│
├── GET /api/v1/search/kg?q=...        → stateless KG search
└── GET /api/v1/search/docs?q=...      → stateless doc search

brandmind (TUI client)
├── Connects to server via HTTP/SSE
├── Sends messages → receives event stream
└── All rendering stays local (TUIRenderer unchanged)
```

### SSE Event Protocol

Server → Client events (same types as callback_types.py):

```
event: model_loading
data: {"type":"model_loading","loading":true}

event: streaming_thinking
data: {"type":"streaming_thinking","token":"Analyzing...","done":false}

event: tool_call
data: {"type":"tool_call","tool_name":"search_web","arguments":{"query":"..."}}

event: tool_result
data: {"type":"tool_result","tool_name":"search_web","result":"..."}

event: streaming_token
data: {"type":"streaming_token","token":"The brand","done":false}

event: done
data: {"type":"done","response":"Full response text"}
```

### Deferred Items

- **Web client**: Architecture supports it, but not built now.
- **Authentication**: Not needed for local eval. Add later if serving remotely.
- **Database persistence**: File-based session storage is sufficient for now.

------------------------------------------------------------------------

## Task Breakdown

### Proposed Tasks

| Task # | Title | Effort | Blocking | Blocked By | Priority |
|--------|-------|--------|----------|------------|----------|
| Task 54 | BrandMind API Server | 2 days | Task 55 | None | High |
| Task 55 | TUI Client Refactor | 1.5 days | None | Task 54 | High |

### Dependency Graph

```
Task 54 (Server — Foundation + Routes + Streaming)
└── Task 55 (TUI Client — HTTP/SSE consumer)
```

### Implementation Order

1. **Task 54** — Server must exist before client can connect
2. **Task 55** — TUI refactored to use server. Can be deferred if eval only needs API.

**Fast path for eval**: After Task 54, Claude Code can already send HTTP requests for eval sessions. Task 55 (TUI refactor) can happen in parallel or after eval.

------------------------------------------------------------------------

## Summary

### What We're Building

A FastAPI server (`brandmind serve`) that wraps BrandMind's agent logic behind HTTP/SSE endpoints. Sessions are managed server-side with agents living in memory. The TUI becomes a thin client that sends HTTP requests and renders SSE events. This unblocks eval automation and enables future web/API consumers.

### Why This Approach

The existing event architecture (7 Pydantic event types, handle_event interface) maps directly to SSE. The refactor is mostly routing changes — agent code stays untouched, TUI rendering stays untouched. The boundary is clean because UI already has zero hard dependencies on agent state.

### Key Constraints and Risks

- **Agent memory**: Each active session holds an agent in memory (~50-100MB). Mitigated by TTL-based cleanup.
- **Streaming complexity**: SSE requires careful disconnect handling. Mitigated by sse-starlette's 3-layer detection.
- **Session serialization**: Already fixed (messages_to_dict/messages_from_dict). Server can save/restore sessions on restart.

### Definition of Done

- [x] Discovery confirmed
- [ ] `brandmind serve` starts FastAPI server
- [ ] POST /api/v1/sessions creates ask or brand-strategy session
- [ ] POST /api/v1/sessions/:id/message returns response (JSON mode)
- [ ] POST /api/v1/sessions/:id/message streams events (SSE mode)
- [ ] TUI connects to server via HTTP (no direct agent imports)
- [ ] Eval can run: Claude Code sends HTTP requests, receives responses
