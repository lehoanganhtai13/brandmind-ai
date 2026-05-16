# Task 89: Reflex Scaffold + `brandmind web` CLI Subcommand

## 📌 Metadata

- **Epic**: Web UI v1 (#88 → #94)
- **Priority**: High
- **Status**: In Progress
- **Estimated Effort**: 0.5 day
- **Team**: Backend + Web Foundation
- **Related Tasks**: Task #88 (consumed by Reflex layer via `BrandMindClient`), Task #91 (real UI on top of this scaffold)
- **Blocking**: Task #91, Task #92, Task #93, Task #94
- **Blocked by**: —

### ✅ Progress Checklist

- [x] 🤖 Agent Protocol — Read and confirmed
- [x] 🎯 Context & Goals — Problem definition + success metrics
- [x] 🛠 Solution Design — Architecture + technical approach (incl. revision to top-level `web/`)
- [x] 🔬 Pre-Implementation Research — Findings logged
- [x] 🔄 Implementation Plan — Phases defined
- [x] 📋 Implementation Detail — Full ready-to-apply code
- [ ] 🧪 Test Execution Log
- [ ] 📊 Decision Log
- [ ] 📝 Task Summary

## 🔗 Reference Documentation

- **Coding Standards**: `tasks/task_template.md` Rule 4 + Rule 5
- **Roadmap Memory**: `~/.claude/projects/-Users-lehoanganhtai-projects-brandmind-ai/memory/web_ui_v1_roadmap_2026_05_16.md`
- **Reflex CLI**: `https://reflex.dev/docs/api-reference/cli/` — `reflex run` flags `--frontend-port`, `--backend-port`, `--backend-host`, `--env [dev|prod]`
- **Reflex config**: `https://reflex.dev/docs/advanced-onboarding/configuration/` — `rxconfig.py` schema
- **Reflex theme**: `https://reflex.dev/docs/styling/theming/` — `rx.theme(color_mode, accent_color)`
- **Existing CLI pattern**: `src/cli/inference.py:466-548` (subparser dispatch + `serve` mode)
- **Existing client**: `src/cli/client.py` (`BrandMindClient.health`, `BrandMindClient.SessionClient` — reused later in #91)

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- BrandMind có TUI launched via `brandmind` (no args). No web UI exists. Web UI is the Task #88 → #94 roadmap; Task #89 is the scaffold gate that unblocks subsequent UI layers.
- Reflex is the locked framework (compile Python → Next.js + React + Tailwind). User constraint: source code must be Python; rendered output language is irrelevant.

### Mục tiêu

Land a runnable Reflex scaffold reachable via `brandmind web` CLI, with:
- Locked dependency group `web` (opt-in install).
- Locked env vars `BRANDMIND_WEB_PORT`, `BRANDMIND_WEB_BACKEND_PORT`, `BRANDMIND_API_URL` for non-clashing port assignment + backend pointer.
- Locked project layout `web/` at repo root (separate from `src/cli/`).
- Placeholder page: header with "BrandMind" wordmark + center health-status badge polling `BRANDMIND_API_URL/health` every 10 s, with teal accent on dark base matching TUI tone.
- `brandmind web --help` works; `brandmind web` launches Reflex via subprocess with correct ports and respects the env-driven backend URL.

### Success Metrics / Acceptance Criteria

- **CLI**: `uv run brandmind web --help` exits 0 with subcommand-level help. `uv run brandmind web` (when web group installed) spawns `reflex run` on `BRANDMIND_WEB_PORT` (default 8501) and `BRANDMIND_WEB_BACKEND_PORT` (default 8502), respecting `BRANDMIND_API_URL` for status polling.
- **Dependency**: `uv sync --group web` installs Reflex without touching the default install. Default `uv sync` leaves Reflex out so the CLI install stays light.
- **Reflex bootstrap**: `web/rxconfig.py` parses, `web/brandmind_web/brandmind_web.py` exports `app: rx.App`. `uv run --group web reflex compile` succeeds inside `web/`.
- **Browser behavior**: with `brandmind serve` running on port 8000, the placeholder page shows "Backend status: Connected ✓". With `brandmind serve` killed, the same page transitions to "Backend status: Disconnected ✗" within ~10 s.
- **Code quality**: `make typecheck` clean; `awk 'length > 100'` zero output on production Python files.
- **No regressions**: `tests/unit/test_server.py` 33/33 pass; `tests/unit/test_artifacts_api.py` 16/16 pass (web changes do not touch backend code).

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Top-level `web/` Reflex sub-project + thin CLI launcher** in `src/cli/inference.py`. The CLI launcher spawns `uv run reflex run` as a subprocess from the `web/` directory with explicit `--frontend-port`, `--backend-port`, `--backend-host` flags resolved from `SETTINGS`. The Reflex app reads `BRANDMIND_API_URL` and polls `/api/v1/health` on a background task; the UI re-renders a connected/disconnected badge based on the latest poll result.

### Stack công nghệ

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| Reflex ≥ 0.8 | Python → React/Next.js compiler | Locked framework (see roadmap memory). Pure-Python authoring; compile target = agentic-web stack. |
| `httpx` (Reflex bundled) | Backend health poll | Already a Reflex transitive dep — no extra install. |
| `@rx.event(background=True)` | Periodic health poll | Reflex-idiomatic background task pattern (`async with self:` for safe state mutation). |
| `subprocess.Popen` | Launch `reflex run` from `brandmind web` | Reflex manages its own event loop + Node frontend; in-process embedding is not supported. |

### Architecture Overview

```
$ brandmind web
  └─ src/cli/inference.py::_handle_web_mode()
       └─ subprocess.run(["uv", "run", "reflex", "run",
                          "--frontend-port", "8501",
                          "--backend-port", "8502",
                          "--backend-host", "0.0.0.0"],
                         cwd="web")
             └─ Reflex compile + serve
                  ├─ Next.js dev server → http://localhost:8501 (browser)
                  └─ Reflex state-sync server → http://localhost:8502 (WebSocket)

Browser → http://localhost:8501
  └─ index() page
       ├─ Header: "BrandMind" wordmark, teal accent on dark base
       └─ HealthBadge: reads HealthState.is_connected
            └─ HealthState.poll_health (background task, every 10s)
                 └─ httpx.AsyncClient.get(BRANDMIND_API_URL + "/api/v1/health")
                      └─ "Connected ✓" if 200, else "Disconnected ✗"

(Concurrently)
$ brandmind serve  →  http://localhost:8000  (BrandMind FastAPI backend)
```

### Issues & Solutions

1. **Port collision** — Reflex's default backend (8000) collides with `brandmind serve` (also 8000). **Fix**: hard-code different default ports in `SETTINGS` (frontend 8501, backend 8502) and pass them via `--frontend-port` / `--backend-port`.
2. **Project layout vs Reflex's strict expectations** — Roadmap memory said `src/cli/web/`, but Reflex generates `.web/` build artifacts, `assets/` Node modules, package.json, etc. that don't belong in a Python source tree. **Fix**: relocate to top-level `web/` (sibling of `infra/`, `tests/`, `evaluation/`); add `.web/` and friends to `.gitignore`. Decision logged below.
3. **Opt-in Reflex install** — Reflex install is heavy (~200 MB+ including Node bootstrap). Existing chatbot / server / indexer groups should not pull it. **Fix**: separate dep group `web = ["reflex>=0.8", "httpx>=0.28"]`; user runs `uv sync --group web` only when they need the web UI.
4. **CLI launch ergonomics** — `reflex run` must run from the directory containing `rxconfig.py`. **Fix**: subprocess `cwd=web_dir` resolved via `pathlib` relative to `src/cli/inference.py`'s repo root.
5. **Health-poll reliability** — single-point check fails on transient blip. **Fix**: poll every 10 s; consider any 2xx response as connected; treat exception / non-2xx / timeout as disconnected. No retry inside one poll — the next poll covers it.

------------------------------------------------------------------------

## 🔬 Pre-Implementation Research

### Codebase Audit

- **Files read**:
  - `src/cli/inference.py:466-585` — subparser dispatch pattern. `serve` mode dispatched synchronously in `main()` (line 568-577) because uvicorn manages its own loop; the same pattern applies to `web` (Reflex also manages its own loop).
  - `src/config/system_config.py:60-72` — env var registration: simple `os.getenv` calls in `Settings.__init__`.
  - `environments/.template.env:26-33` — server-section template.
  - `pyproject.toml:29-68` — `[dependency-groups]` table; `chatbot`, `server`, `indexer`, `migration`, `dev` groups; `[tool.ruff]` excludes `src/prompts`, `tests`, `src/cli/tui/widgets/banner.py` (line 77).
  - `.gitignore` — existing ignores; needs `.web`, `assets/external`, etc. for the new `web/` directory.
  - `src/cli/client.py` — `BrandMindClient` already supports `health()` via `HealthClient`; not used in #89 (we issue our own `httpx` poll for simplicity at scaffold stage), but will be reused in #91 for real chat streaming.

- **Relevant patterns found**:
  - CLI subparsers are added near line 466 in `async_main`. `serve` mode is special-cased in `main()` (sync entry) because of uvicorn's loop. `web` follows the same special-case path.
  - Settings are simple attribute assignments in `Settings.__init__`. New env vars slot in alongside existing `BRANDMIND_*` block.

- **Potential conflicts**:
  - Ruff excludes do not currently mention `web/`. Decision: do NOT exclude — Reflex Python source files should be linted/typechecked along with the rest of the project. `.web/` (build output) is git-ignored so ruff never sees it.
  - Mypy: namespace packages may be confused by `web/brandmind_web/` since it's not under any of the `[packages]` listed in `pyproject.toml`. Solution: leave `web/` out of `[packages]` (Reflex doesn't need it as a wheel target); use `# type: ignore` only if strictly necessary. Test by running `make typecheck` after applying.

### External Library / API Research

- **Library**: Reflex ≥ 0.8 (verified via Context7 `/reflex-dev/reflex` + `/reflex-dev/reflex-web`, 2026-05-16).
- **CLI**: `reflex run [--env dev|prod] [--frontend-only] [--backend-only] [--frontend-port N] [--backend-port N] [--backend-host HOST] [--loglevel debug|info|warning|error|critical]`.
- **App skeleton**: `rxconfig.py` exports `config = rx.Config(app_name="brandmind_web", ...)`. Sibling package `brandmind_web/` contains a module of the same name exporting `app = rx.App(...)`.
- **State**: subclass `rx.State`; class-level annotated vars become reactive. Mutating inside `@rx.event(background=True)` requires `async with self:` re-entry.
- **Theming**: `rx.theme(color_mode="dark", accent_color="teal", radius="medium")` applied to the `rx.App` constructor.

### Unknown / Risks Identified

- [x] Reflex CLI flag shape → confirmed via Context7.
- [x] Reflex project layout → confirmed via Context7 (`rxconfig.py` + sibling package).
- [x] Reflex state-sync backend port collision → resolved (8502 default).
- [x] `subprocess.run` cwd resolution → use `pathlib.Path(__file__).resolve().parents[N] / "web"`.
- [x] Reflex telemetry default → off via `telemetry_enabled=False` in `rxconfig.py`.

### Research Status

- [x] All referenced documentation read
- [x] Existing codebase patterns understood
- [x] External dependencies verified
- [x] No unresolved ambiguities remain → Ready to implement

------------------------------------------------------------------------

## 🔄 Implementation Plan

### Phase 1: Dependency + Settings — 10 min

1. Add `web` dependency group in `pyproject.toml`.
2. Register `BRANDMIND_WEB_PORT`, `BRANDMIND_WEB_BACKEND_PORT`, `BRANDMIND_API_URL` in `system_config.py` + `.template.env`.
3. Add Reflex build artifacts to `.gitignore`.

### Phase 2: Reflex Scaffold — 20 min

4. Create `web/rxconfig.py`.
5. Create `web/brandmind_web/__init__.py`.
6. Create `web/brandmind_web/brandmind_web.py` — Reflex app + HealthState + index page.

### Phase 3: CLI Wiring — 10 min

7. Modify `src/cli/inference.py` — add `web` subparser + `_handle_web_mode()` sync dispatcher in `main()`.

### Phase 4: Verification — 20 min

8. `uv sync --group web` to install Reflex.
9. `uv run brandmind web --help` — sub-help shows.
10. `uv run --group web --directory web reflex compile` — Reflex side compiles clean.
11. Start `brandmind serve` and `brandmind web` in two shells. Browse to `http://localhost:8501` — expect "Connected ✓" badge. Kill `brandmind serve`, expect "Disconnected ✗" within ~10 s.
12. `make typecheck` + `awk 'length > 100'` + `gitnexus detect_changes(scope="staged")` before commit.

### Rollback Plan

- Per-file restore is enough: `git restore` `pyproject.toml`, `src/config/system_config.py`, `environments/.template.env`, `src/cli/inference.py`, `.gitignore`; `rm -rf web/` removes the new directory. No data, no schema, no env-vars in production usage (env vars have safe defaults).

------------------------------------------------------------------------

## 📋 Implementation Detail

### Component 1: `pyproject.toml` `[MODIFY]` — add `web` dep group

- **For `[MODIFY]` — locate the change**:

```toml
# old_string (relevant block):
server = [
    "shared",
    "core[retrieval]",
    "fastapi>=0.115.0",
    "sse-starlette>=2.0.0",
    "uvicorn>=0.34.0",
]
migration = [
```

- **Full code to write**:

```toml
server = [
    "shared",
    "core[retrieval]",
    "fastapi>=0.115.0",
    "sse-starlette>=2.0.0",
    "uvicorn>=0.34.0",
]
web = [
    "reflex>=0.8.0",
    "httpx>=0.28.0",
]
migration = [
```

### Component 2: `src/config/system_config.py` `[MODIFY]` — register web env vars

- **For `[MODIFY]` — locate the change**:

```python
# old_string:
        self.BRANDMIND_DEBUG_TOOLS = (
            os.getenv("BRANDMIND_DEBUG_TOOLS", "false").strip().lower() == "true"
        )

        # Vector Database Collection Names
```

- **Full code to write**:

```python
        self.BRANDMIND_DEBUG_TOOLS = (
            os.getenv("BRANDMIND_DEBUG_TOOLS", "false").strip().lower() == "true"
        )

        # Web UI settings (`brandmind web`)
        # `BRANDMIND_WEB_PORT` — Reflex frontend (Next.js dev server) port the
        #   user opens in their browser. Default 8501 sidesteps the FastAPI
        #   backend on 8000.
        # `BRANDMIND_WEB_BACKEND_PORT` — Reflex's own state-sync backend port;
        #   internal to Reflex, never user-facing. Default 8502 avoids the
        #   FastAPI server.
        # `BRANDMIND_API_URL` — URL the web UI uses to reach `brandmind serve`
        #   over HTTP/SSE. Defaults to localhost + the server port so a stock
        #   single-machine install works without configuration; override when
        #   running the web UI in Docker or against a remote backend.
        self.BRANDMIND_WEB_PORT = int(os.getenv("BRANDMIND_WEB_PORT", 8501))
        self.BRANDMIND_WEB_BACKEND_PORT = int(
            os.getenv("BRANDMIND_WEB_BACKEND_PORT", 8502)
        )
        self.BRANDMIND_API_URL = os.getenv(
            "BRANDMIND_API_URL",
            f"http://localhost:{self.BRANDMIND_PORT}",
        )

        # Vector Database Collection Names
```

### Component 3: `environments/.template.env` `[MODIFY]` — document web env vars

- **For `[MODIFY]` — locate the change**:

```
# old_string:
BRANDMIND_OUTPUT_DIR=
BRANDMIND_DEBUG_TOOLS=false

# -----------------------------------------------------------------------------
# Embedding Configuration
```

- **Full code to write**:

```
BRANDMIND_OUTPUT_DIR=
BRANDMIND_DEBUG_TOOLS=false

# -----------------------------------------------------------------------------
# BrandMind Web UI (Optional - `brandmind web` opt-in)
# -----------------------------------------------------------------------------
# Reflex frontend port the browser opens (default 8501)
BRANDMIND_WEB_PORT=8501
# Reflex's own state-sync backend port (internal, default 8502)
BRANDMIND_WEB_BACKEND_PORT=8502
# URL the web UI uses to reach `brandmind serve` (default localhost:BRANDMIND_PORT)
BRANDMIND_API_URL=

# -----------------------------------------------------------------------------
# Embedding Configuration
```

### Component 4: `.gitignore` `[MODIFY]` — ignore Reflex build artifacts

- **For `[MODIFY]` — locate the change** (anchor at the end of the file):

```
# old_string (a tail of the file with surrounding context):
.webassets-cache
```

- **Full code to write** (append a new section at the end of `.gitignore`):

Append (do not replace surrounding content):

```
# -----------------------------------------------------------------------------
# Reflex web UI (web/) — build output + downloaded assets
# -----------------------------------------------------------------------------
web/.web/
web/assets/external/
web/.states/
```

### Component 5: `web/rxconfig.py` `[NEW]`

- **File**: `web/rxconfig.py`
- **Change kind**: New file
- **Full code to write**:

```python
"""Reflex configuration for the BrandMind web UI.

Runs as a separate Reflex sub-project at the repo root, distinct from the
Python source tree under ``src/``. The Reflex CLI (`reflex run`) discovers
this file when invoked with ``web/`` as the working directory; the
sibling ``brandmind_web/`` package contains the app definition.

Ports are intentionally non-default so they do not collide with the
FastAPI backend (`brandmind serve` on port 8000). The actual port values
come from environment variables read in :mod:`config.system_config` and
forwarded through the ``brandmind web`` CLI launcher's ``reflex run``
command-line arguments — Reflex picks the CLI arguments over this file,
so the values here act as fallbacks for direct ``reflex run`` invocations
outside the CLI launcher.
"""

from __future__ import annotations

import os

import reflex as rx

_FRONTEND_PORT_DEFAULT = 8501
_BACKEND_PORT_DEFAULT = 8502


config = rx.Config(
    app_name="brandmind_web",
    frontend_port=int(os.getenv("BRANDMIND_WEB_PORT", _FRONTEND_PORT_DEFAULT)),
    backend_port=int(
        os.getenv("BRANDMIND_WEB_BACKEND_PORT", _BACKEND_PORT_DEFAULT)
    ),
    telemetry_enabled=False,
    show_built_with_reflex=False,
)
```

### Component 6: `web/brandmind_web/__init__.py` `[NEW]`

- **File**: `web/brandmind_web/__init__.py`
- **Change kind**: New file
- **Full code to write**:

```python
"""BrandMind web UI Reflex app package.

The Reflex CLI imports the module named identically to the ``app_name``
in ``rxconfig.py`` (here: ``brandmind_web.brandmind_web``). This
``__init__.py`` keeps the package importable without re-exporting the
``app`` object so Reflex's auto-discovery is the single source of truth.
"""
```

### Component 7: `web/brandmind_web/brandmind_web.py` `[NEW]`

- **File**: `web/brandmind_web/brandmind_web.py`
- **Change kind**: New file
- **Full code to write**:

```python
"""BrandMind web UI — placeholder page with backend health badge.

Scaffold deliverable for Task #89. The real chat / phase-sidebar /
canvas / artifact UI lands in Tasks #91 and #92 on top of this skeleton.

What this module ships today:

* :class:`HealthState` — a Reflex state class with one reactive flag
  (``is_connected``) and a background coroutine that polls the FastAPI
  backend's ``/api/v1/health`` endpoint every ten seconds. Reading a
  reactive var in a component re-renders that component when the var
  changes, so the badge follows the poll result without any extra
  wiring.
* :func:`index` — the root page. Header with the BrandMind wordmark
  and a centered status badge.
* ``app`` — the :class:`reflex.App` instance Reflex auto-discovers
  through the ``app_name`` in ``rxconfig.py``.

Aesthetic anchors:

* Color mode ``dark`` with accent ``teal`` matches the TUI banner and
  the locked Web UI v1 design tone (teal ``#5fb3a8`` on dark base).
* Glass-effect surfaces are deferred to Task #91 where they fit the
  larger layout; this scaffold uses a flat centered card so the smoke
  test reads obviously connected / disconnected at a glance.
"""

from __future__ import annotations

import os

import httpx
import reflex as rx

_DEFAULT_API_URL = "http://localhost:8000"
_HEALTH_POLL_INTERVAL_SECONDS = 10
_HEALTH_REQUEST_TIMEOUT_SECONDS = 3


def _api_base_url() -> str:
    """Return the FastAPI backend base URL the web UI should reach.

    Reads ``BRANDMIND_API_URL`` from the environment so a Docker
    deployment can swap the host without rebuilding the image. Falls
    back to ``localhost:8000`` which matches a default
    ``brandmind serve`` install on the same machine.
    """
    return os.getenv("BRANDMIND_API_URL", _DEFAULT_API_URL).rstrip("/")


class HealthState(rx.State):
    """Reactive backend-connectivity state for the placeholder page.

    The single reactive var :attr:`is_connected` drives every
    health-aware component. Components that read this var re-render
    automatically when the background poll flips its value.
    """

    is_connected: bool = False

    @rx.event(background=True)
    async def poll_health(self) -> None:
        """Poll ``/api/v1/health`` on a fixed cadence and mirror the result.

        Runs as a Reflex background task so the UI stays responsive
        while the request is in flight. Any 2xx response counts as
        connected; exceptions, non-2xx codes, and timeouts count as
        disconnected. State mutations happen inside ``async with self``
        so Reflex serialises them against UI reads.
        """
        url = f"{_api_base_url()}/api/v1/health"
        timeout = _HEALTH_REQUEST_TIMEOUT_SECONDS
        while True:
            connected = False
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(url)
                connected = response.is_success
            except httpx.HTTPError:
                connected = False

            async with self:
                self.is_connected = connected

            await rx.utils.misc.async_sleep(_HEALTH_POLL_INTERVAL_SECONDS)


def _status_badge() -> rx.Component:
    """Render the connected / disconnected backend-status badge.

    The badge's text and color are driven by ``HealthState.is_connected``;
    Reflex re-renders this subtree whenever the reactive var flips.
    """
    return rx.cond(
        HealthState.is_connected,
        rx.hstack(
            rx.icon(tag="check", size=20),
            rx.text("Backend: Connected", size="4", weight="medium"),
            spacing="2",
            align="center",
            padding="3",
            border_radius="medium",
            background_color=rx.color("teal", 3),
            color=rx.color("teal", 11),
        ),
        rx.hstack(
            rx.icon(tag="circle-x", size=20),
            rx.text("Backend: Disconnected", size="4", weight="medium"),
            spacing="2",
            align="center",
            padding="3",
            border_radius="medium",
            background_color=rx.color("red", 3),
            color=rx.color("red", 11),
        ),
    )


def _header() -> rx.Component:
    """Render the top bar with the BrandMind wordmark and aesthetic anchor."""
    return rx.hstack(
        rx.text(
            "BrandMind",
            size="6",
            weight="bold",
            color=rx.color("teal", 11),
        ),
        rx.text(
            "Web UI v1 — scaffold",
            size="2",
            color=rx.color("gray", 10),
        ),
        spacing="4",
        align="center",
        padding="4",
        width="100%",
        border_bottom=f"1px solid {rx.color('gray', 5)}",
    )


def index() -> rx.Component:
    """Root page: header + centered health badge.

    Reflex calls :meth:`HealthState.poll_health` once via ``on_mount`` so
    the background polling starts on first navigation and lives for the
    lifetime of the session.
    """
    return rx.vstack(
        _header(),
        rx.center(
            rx.vstack(
                rx.text(
                    "BrandMind backend status",
                    size="3",
                    color=rx.color("gray", 11),
                ),
                _status_badge(),
                rx.text(
                    f"Polling {_api_base_url()}/api/v1/health every "
                    f"{_HEALTH_POLL_INTERVAL_SECONDS}s",
                    size="1",
                    color=rx.color("gray", 9),
                ),
                spacing="3",
                align="center",
            ),
            width="100%",
            flex="1",
        ),
        spacing="0",
        width="100vw",
        height="100vh",
        on_mount=HealthState.poll_health,
    )


app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="teal",
        radius="medium",
    ),
)
app.add_page(index, title="BrandMind")
```

### Component 8: `src/cli/inference.py` `[MODIFY]` — add `web` subcommand

- **For `[MODIFY]` — locate the change (Part A: subparser registration)**:

```python
# old_string:
    # Mode: serve
    subparsers.add_parser(
        "serve",
        help="Start BrandMind API server (config via BRANDMIND_HOST/PORT in .env)",
    )

    # Mode: browser
```

- **Full code to write (Part A)**:

```python
    # Mode: serve
    subparsers.add_parser(
        "serve",
        help="Start BrandMind API server (config via BRANDMIND_HOST/PORT in .env)",
    )

    # Mode: web
    subparsers.add_parser(
        "web",
        help=(
            "Start the BrandMind web UI (Reflex). "
            "Install with `uv sync --group web` first. "
            "Backend reached via BRANDMIND_API_URL."
        ),
    )

    # Mode: browser
```

- **For `[MODIFY]` — locate the change (Part B: serve dispatch in async_main)**:

```python
# old_string:
    # Dispatch to handlers
    if args.mode == "serve":
        # Serve runs synchronously (uvicorn manages its own event loop)
        # Return early so async_main doesn't try to await it
        return args.mode
    elif args.mode == "brand-strategy":
```

- **Full code to write (Part B)**:

```python
    # Dispatch to handlers
    if args.mode == "serve":
        # Serve runs synchronously (uvicorn manages its own event loop)
        # Return early so async_main doesn't try to await it
        return args.mode
    elif args.mode == "web":
        # Web mode launches Reflex as a subprocess from `main()` (sync)
        # for the same reason serve runs sync — Reflex manages its own
        # event loop + Node.js frontend dev server.
        return args.mode
    elif args.mode == "brand-strategy":
```

- **For `[MODIFY]` — locate the change (Part C: sync main() dispatch)**:

```python
# old_string:
    # Handle 'serve' mode synchronously (uvicorn runs its own loop)
    if len(sys.argv) >= 2 and sys.argv[1] == "serve":
        import uvicorn

        from config.system_config import SETTINGS
        from server.main import create_app

        app = create_app()
        uvicorn.run(app, host=SETTINGS.BRANDMIND_HOST, port=SETTINGS.BRANDMIND_PORT)
        return

    # Otherwise run the async CLI
    asyncio.run(async_main())
```

- **Full code to write (Part C)**:

```python
    # Handle 'serve' mode synchronously (uvicorn runs its own loop)
    if len(sys.argv) >= 2 and sys.argv[1] == "serve":
        import uvicorn

        from config.system_config import SETTINGS
        from server.main import create_app

        app = create_app()
        uvicorn.run(app, host=SETTINGS.BRANDMIND_HOST, port=SETTINGS.BRANDMIND_PORT)
        return

    # Handle 'web' mode synchronously (Reflex manages its own loop + Node)
    if len(sys.argv) >= 2 and sys.argv[1] == "web":
        _launch_web_ui()
        return

    # Otherwise run the async CLI
    asyncio.run(async_main())
```

- **For `[MODIFY]` — locate the change (Part D: add helper function before `def main`)**:

```python
# old_string:
def main() -> None:
    """Synchronous entry point for CLI."""
    import os
    import sys
```

- **Full code to write (Part D)** — insert a new helper *above* `def main()`:

```python
def _launch_web_ui() -> None:
    """Spawn the Reflex frontend / state-sync backend for the web UI.

    Resolves the Reflex project root (``<repo>/web``) relative to this
    file, builds the ``reflex run`` command with explicit frontend +
    backend ports drawn from :data:`config.system_config.SETTINGS`, and
    runs it as a foreground subprocess so Ctrl-C from the user shell
    terminates Reflex cleanly. ``BRANDMIND_API_URL`` is propagated into
    the child process so the placeholder page polls the right backend
    without separate configuration.
    """
    import os
    import shutil
    import subprocess  # nosec B404
    import sys
    from pathlib import Path

    from config.system_config import SETTINGS

    repo_root = Path(__file__).resolve().parents[2]
    web_dir = repo_root / "web"
    if not (web_dir / "rxconfig.py").is_file():
        console.print(
            "[red]Reflex project not found at "
            f"{web_dir}/rxconfig.py.[/red] Did the repo move?"
        )
        sys.exit(1)

    reflex_cmd = shutil.which("reflex")
    if reflex_cmd is None:
        console.print(
            "[yellow]Reflex is not installed in the active environment.[/yellow]\n"
            "Install with: [bold]uv sync --group web[/bold]\n"
            "Then re-run: [bold]brandmind web[/bold]"
        )
        sys.exit(1)

    env = os.environ.copy()
    env.setdefault("BRANDMIND_API_URL", SETTINGS.BRANDMIND_API_URL)

    command = [
        reflex_cmd,
        "run",
        "--frontend-port",
        str(SETTINGS.BRANDMIND_WEB_PORT),
        "--backend-port",
        str(SETTINGS.BRANDMIND_WEB_BACKEND_PORT),
        "--backend-host",
        SETTINGS.BRANDMIND_HOST,
    ]
    console.print(
        f"[cyan]Launching BrandMind web UI on "
        f"http://localhost:{SETTINGS.BRANDMIND_WEB_PORT}[/cyan]\n"
        f"Backend pollee: [bold]{SETTINGS.BRANDMIND_API_URL}[/bold]\n"
        f"Start the BrandMind API server in another shell with: "
        f"[bold]brandmind serve[/bold]"
    )
    try:
        subprocess.run(command, cwd=web_dir, env=env, check=False)  # nosec B603
    except KeyboardInterrupt:
        # Reflex propagates Ctrl-C internally; suppress the traceback
        # so the user gets a clean shell prompt back.
        return


def main() -> None:
    """Synchronous entry point for CLI."""
    import os
    import sys
```

------------------------------------------------------------------------

## 🧪 Test Execution Log

> Filled after running.

### Test 1: `uv sync --group web` installs Reflex
- **Status**: ⏳ Pending

### Test 2: `uv run brandmind web --help` shows subcommand help
- **Status**: ⏳ Pending

### Test 3: `uv run --directory web reflex compile` clean compile
- **Status**: ⏳ Pending

### Test 4: Browser smoke — connected ↔ disconnected toggle
- **Status**: ⏳ Pending

### Test 5: `make typecheck` clean
- **Status**: ⏳ Pending

### Test 6: `awk 'length > 100'` zero output on production files
- **Status**: ⏳ Pending

### Test 7: Existing regression (`test_server.py`, `test_artifacts_api.py`)
- **Status**: ⏳ Pending

### Test 8: `gitnexus_detect_changes(scope="staged")` pre-commit
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📊 Decision Log

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | Reflex project location | (A) `src/cli/web/` per original roadmap, (B) top-level `web/` | (B) Top-level `web/` | Reflex generates `.web/` build dir, `assets/` Node modules, `package.json` — these don't belong inside the Python source tree. Top-level `web/` mirrors `infra/`, `evaluation/`, `tests/`. Roadmap memory updated. |
| 2 | Reflex port assignment | (A) Default 3000/8000 (conflicts with `brandmind serve`), (B) 8501 + 8502 | (B) 8501 + 8502 | Reflex's default backend port 8000 collides with `BRANDMIND_PORT` 8000. Frontend default 3000 is fine but choosing 8501 keeps both Reflex ports in the 850x band for easy mental grouping. |
| 3 | Dep group strategy | (A) Add Reflex to `chatbot` group, (B) New `web` group | (B) New `web` group | Reflex install is heavy (~200 MB+ with Node bootstrap). Existing chatbot users (TUI install) should not pay that cost. Web users opt in with `uv sync --group web`. |
| 4 | Health poll mechanism | (A) Reuse `BrandMindClient.HealthClient`, (B) Direct `httpx` call | (B) Direct `httpx` call | `BrandMindClient` lives in `src/cli/` (Python source tree) and uses workspace-style imports that Reflex's `web/` sub-project would have to resolve. Direct `httpx` keeps the Reflex app self-contained at scaffold stage. Will re-evaluate in #91 when full SSE chat streaming needs `BrandMindClient`. |
| 5 | Launch mechanism | (A) Spawn `reflex run` via subprocess, (B) Embed Reflex in `brandmind` process | (A) Subprocess | Reflex manages its own asyncio loop + Node.js frontend dev server. Embedding requires significant glue and breaks Ctrl-C semantics. Subprocess matches the existing `serve` mode pattern (sync dispatch from `main()`). |
| 6 | Reflex version pin | (A) `>=0.6` per stale roadmap memory, (B) `>=0.8` per current stable | (B) `>=0.8` | Roadmap memory was written before the 0.8 release line. 0.8 is current stable with the events / state-isolation guarantees this scaffold relies on. |

------------------------------------------------------------------------

## 📝 Task Summary

> Filled after task is fully complete.

### What Was Implemented

- [ ] *Pending implementation*

### Validation Results

- [ ] *Pending*

### Deployment Notes

- [ ] **Opt-in install**: users run `uv sync --group web` before `brandmind web`.
- [ ] **Three new env vars** with safe defaults: `BRANDMIND_WEB_PORT=8501`, `BRANDMIND_WEB_BACKEND_PORT=8502`, `BRANDMIND_API_URL=http://localhost:8000`.
- [ ] **No backend changes** — Task #88 endpoints remain untouched.
- [ ] **Build artifacts ignored** — `.gitignore` covers `web/.web/`, `web/assets/external/`, `web/.states/`.
