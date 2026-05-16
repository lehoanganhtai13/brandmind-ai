# Task 88: Backend Artifact-Serving Endpoint

## 📌 Metadata

- **Epic**: Web UI v1 (#88 → #94)
- **Priority**: High
- **Status**: In Progress
- **Estimated Effort**: 0.5 day
- **Team**: Backend
- **Related Tasks**: Task #89 (Reflex scaffold consumes these endpoints)
- **Blocking**: Task #89, Task #92
- **Blocked by**: —

### ✅ Progress Checklist

- [x] 🤖 Agent Protocol — Read and confirmed
- [x] 🎯 Context & Goals — Problem definition + success metrics
- [x] 🛠 Solution Design — Architecture + technical approach
- [x] 🔬 Pre-Implementation Research — Findings logged
- [x] 🔄 Implementation Plan — Phases defined
- [x] 📋 Implementation Detail — Full ready-to-apply code (pre-apply review surface)
    - [ ] ⏳ Component 1 — `src/server/api/artifacts.py` (NEW)
    - [ ] ⏳ Component 2 — `src/server/api/router.py` (MODIFY)
    - [ ] ⏳ Component 3 — `tests/unit/test_artifacts_api.py` (NEW)
- [ ] 🧪 Test Execution Log
- [ ] 📊 Decision Log
- [ ] 📝 Task Summary

## 🔗 Reference Documentation

- **Coding Standards**: `tasks/task_template.md` Rule 4 + Rule 5
- **Roadmap Memory**: `~/.claude/projects/-Users-lehoanganhtai-projects-brandmind-ai/memory/web_ui_v1_roadmap_2026_05_16.md`
- **Manifest schema**: `src/shared/src/shared/agent_tools/document/_output_path.py:147-194` (`append_manifest`)
- **Existing pattern**: `src/server/api/sessions.py`, `src/server/api/search.py`, `tests/unit/test_server.py::TestAPIRoutes`
- **FastAPI FileResponse**: `https://fastapi.tiangolo.com/advanced/custom-response` — `path`, `media_type`, `filename`, `content_disposition_type` parameters

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- BrandMind viết artifacts ra `$BRANDMIND_OUTPUT_DIR/<category>/<brand_slug>/<timestamp>_<filename>` (default `brandmind-output/`) và append metadata JSONL vào `.manifest.jsonl`. Manifest record có: `session_id, brand_name, category, tool, filename, path, size_bytes, generated_at`.
- Hiện tại chỉ có in-process tool `list_artifacts` cho orchestrator (returns text). Web UI cần structured JSON + binary file serving qua HTTP.
- Không endpoint nào exposed cho web UI hôm nay.

### Mục tiêu

Hai stateless HTTP endpoints cho web UI consume artifacts của một session bất kỳ (live hoặc historical):
1. `GET /api/v1/sessions/{session_id}/artifacts` → `list[ArtifactRef]` từ manifest
2. `GET /api/v1/artifacts/{session_id}/{filename}` → `FileResponse` streaming bytes

### Success Metrics / Acceptance Criteria

- **Functional**: list endpoint returns correct records filtered by `session_id`, ordered by `generated_at`; download endpoint streams the right file for `(session_id, filename)` pair.
- **Security**: path traversal attempts (`..`, absolute paths, unsafe extensions) rejected at 3 layers — URL segment regex, manifest lookup, and `Path.resolve().relative_to(base)` containment.
- **Reliability**: missing manifest → empty list (not 500); missing file on disk → 404 (not 500); malformed JSONL lines skipped silently.
- **Code quality**: `make typecheck` passes; `awk 'length > 100'` zero output; new tests cover all branches.
- **No regressions**: existing 18 routes still work; existing `tests/unit/test_server.py` still passes.

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Manifest-driven stateless artifact router** — new module `src/server/api/artifacts.py` registered under the existing `/api/v1` prefix via `router.py`. Reads `_manifest_path()` and `_base_dir()` from `shared.agent_tools.document._output_path` (existing private helpers; reuse pattern from `list_artifacts.py`). No SessionManager dependency, no active-session requirement — the manifest is the only state.

### Stack công nghệ

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| FastAPI `APIRouter` | Endpoint registration | Mirrors existing `sessions.py` / `search.py` pattern |
| FastAPI `FileResponse` | Stream binary file | Built-in, supports `Content-Disposition`, `Content-Length`, ETag, Last-Modified automatically |
| Pydantic v2 `BaseModel` | Typed response schema | Matches `server.schemas.session.SessionInfo` pattern |
| `pathlib.Path.resolve()` + `relative_to()` | Path-traversal defense | Stdlib, no extra dep; defense-in-depth alongside URL segment regex |

### Architecture Overview

```
Web UI                             FastAPI Server                         Disk
─────                              ──────────────                         ────

GET /api/v1/sessions/{sid}/        ─► list_session_artifacts()
    artifacts                          │
                                       │ _iter_manifest_records()  ──►   .manifest.jsonl
                                       │ filter by session_id            (read-only)
                                       │ _record_to_ref()
                                       ▼
                                   list[ArtifactRef]   ◄── JSON

GET /api/v1/artifacts/{sid}/{fn}   ─► download_artifact()
                                       │ regex validate sid + fn
                                       │ _find_manifest_record()  ──►    .manifest.jsonl
                                       │ Path.resolve().relative_to(_base_dir())
                                       │ verify file exists
                                       ▼
                                   FileResponse        ◄── bytes streamed from disk
```

### Issues & Solutions

1. **Path traversal** → 3-layer defense: (a) URL segment regex `[A-Za-z0-9_-]+` for session_id + `[A-Za-z0-9._-]+\.(docx|pptx|xlsx|png|jpg|jpeg|webp)` for filename rejects `..`, `/`, unsafe extensions at the route level; (b) manifest lookup — only files recorded in `.manifest.jsonl` are servable, never an arbitrary `Path(filename)`; (c) `Path(record.path).resolve().relative_to(_base_dir().resolve())` containment, catching symlinks/absolute paths pointing outside the base.
2. **Manifest path leakage** → `ArtifactRef` exposes `download_url`, never the absolute server-side filesystem `path`. Server filesystem layout stays private.
3. **Malformed manifest lines** → `json.JSONDecodeError` and non-dict records skipped silently per existing `list_artifacts.py` pattern; one bad line does not blank out the entire artifact panel.
4. **Empty / missing manifest** → return `[]` (HTTP 200) for list; return 404 for download — no false 500s.
5. **Inline vs attachment** → `content_disposition_type="inline"` for `images` (so `<img src=...>` works); default `attachment` for documents / presentations / spreadsheets (so direct anchor downloads behave; mammoth-js / SheetJS use `fetch()` which ignores disposition).

------------------------------------------------------------------------

## 🔬 Pre-Implementation Research

### Codebase Audit

- **Files read**:
  - `src/server/api/router.py` — router aggregation pattern (4 sub-routers)
  - `src/server/api/sessions.py` — endpoint shape (decorator + `Depends`)
  - `src/server/api/health.py` / `search.py` — stateless endpoint pattern
  - `src/server/api/chat.py` — `EventSourceResponse` for SSE (not used here, but verified import path)
  - `src/server/main.py` — `create_app()` registers `api_router` with `prefix="/api/v1"`
  - `src/server/schemas/session.py` — Pydantic v2 `BaseModel` pattern
  - `src/shared/src/shared/agent_tools/document/_output_path.py` — `_base_dir()`, `_manifest_path()`, `append_manifest()` (manifest schema source of truth)
  - `src/shared/src/shared/agent_tools/document/list_artifacts.py` — existing manifest reader pattern, JSONL parsing, JSONDecodeError handling
  - `tests/unit/test_server.py` — `TestClient(create_app())` fixture pattern
  - `brandmind-output/.manifest.jsonl` (5 sample records) — schema confirmed: `session_id, brand_name, category, tool, filename, path, size_bytes, generated_at`
- **Relevant patterns found**:
  - Routers tagged + included via `api_router.include_router(...)` in `router.py`; ordering does not affect correctness.
  - Pydantic v2 schemas in `server/schemas/<topic>.py` using `BaseModel` directly; my `ArtifactRef` is colocated in `api/artifacts.py` since it has no consumers outside this endpoint (mirrors `MessageResponse` colocation in `schemas/chat.py` — actually MessageResponse IS in schemas; but for a single-endpoint type the colocation cost is lower than a one-line schema file).
  - **Decision**: keep `ArtifactRef` in `api/artifacts.py` — single-use schema, no reuse outside this module. Refactor to `server/schemas/artifacts.py` only if Task #89/#92 ends up importing it from the Reflex web layer (which sits in `src/cli/web/`, separate package).
  - Existing `list_artifacts.py` imports `_base_dir` and `_manifest_path` (underscore-prefixed module-private helpers) directly from `_output_path.py`. New endpoint follows the same import pattern.
- **Potential conflicts**: none. No existing `src/server/api/artifacts.py` or `tests/unit/test_artifacts_api.py`. No clash with existing routes — `/sessions/{id}/...` paths from `sessions.py` already exist but use different suffixes (`message`, no suffix). FastAPI routes by exact path so `/sessions/{sid}/artifacts` is unambiguous.

### External Library / API Research

- **Library**: FastAPI 0.118.x (project uses `fastapi>=0.118`)
- **Documentation source**: Context7 `/websites/fastapi_tiangolo` — verified 2026-05-16
- **Key findings**:
  - `FileResponse(path, status_code=200, headers=None, media_type=None, background=None, filename=None, stat_result=None, content_disposition_type="attachment")`
  - `media_type=None` → guessed from filename extension (`mimetypes` stdlib). DOCX/PPTX/XLSX/PNG all return correct MIME types automatically.
  - `Content-Length`, `Last-Modified`, `ETag` headers auto-set; no manual streaming code needed.
  - `content_disposition_type="inline"` valid for images so `<img>` and `<embed>` work.

### GitNexus Impact Analysis

- **Target inspected**: `_manifest_path` (existing private helper, `direction=upstream`)
- **Risk**: CRITICAL for *modifications* to `_manifest_path` itself — 4 direct callers + 15 affected processes. **Not relevant to Task #88**: this task only ADDS new callers (reads), no modification to the existing function.
- **New module risk**: LOW — `src/server/api/artifacts.py` is additive; only consumed by `router.py` (1-line import + 1-line `include_router`). No existing symbol changes shape.

### Unknown / Risks Identified

- [x] FastAPI `FileResponse` parameters → resolved via Context7 doc.
- [x] Manifest record shape → confirmed by reading 5 real records + `append_manifest()` source.
- [x] Path containment idiom in Python → `Path.resolve().relative_to(base.resolve())` raises `ValueError` on escape; stdlib-canonical.
- [x] Pydantic v2 + Literal compatibility → verified via existing `server.schemas.session.BrandStrategyMetadata`.
- [x] `BRANDMIND_OUTPUT_DIR` env override behavior in `_base_dir()` → re-evaluated per call (no caching) → monkeypatch in tests works.

### Research Status

- [x] All referenced documentation read
- [x] Existing codebase patterns understood
- [x] External dependencies verified
- [x] No unresolved ambiguities remain → Ready to implement

------------------------------------------------------------------------

## 🔄 Implementation Plan

### Phase 1: Implementation — 30 min

1. **Create `src/server/api/artifacts.py`** with `router`, `ArtifactRef` model, helpers, and 2 endpoints.
2. **Modify `src/server/api/router.py`** to import and include the new router.
   - *Checkpoint*: `uv run python -c "from server.api.router import api_router; print([r.path for r in api_router.routes])"` shows the two new paths.

### Phase 2: Tests — 30 min

3. **Create `tests/unit/test_artifacts_api.py`** with 13 test cases covering list filtering, ordering, malformed lines, path validation, traversal defense, missing files.
   - *Checkpoint*: `uv run pytest tests/unit/test_artifacts_api.py -v` all green.

### Phase 3: Verify — 15 min

4. **Run existing test_server.py** to confirm zero regressions.
5. **`make typecheck`** — must pass.
6. **`awk 'length > 100' src/server/api/artifacts.py src/server/api/router.py tests/unit/test_artifacts_api.py`** — must be empty.
7. **`gitnexus_detect_changes(scope="unstaged")`** — review risk + affected processes before commit.
8. **Live smoke** — start `brandmind serve`, `curl /api/v1/sessions/<known-session>/artifacts` and verify shape; `curl -I /api/v1/artifacts/<sid>/<filename>` and verify headers.
9. **PAUSE CHECKPOINT 1** — report results to user before proceeding to Task #89.

### Rollback Plan

- `git restore src/server/api/router.py` reverts the include; `rm src/server/api/artifacts.py tests/unit/test_artifacts_api.py` removes the new files. No data migrations, no schema changes, no env var additions in this task.

------------------------------------------------------------------------

## 📋 Implementation Detail

### Component 1: `src/server/api/artifacts.py` `[NEW]`

> Status: ⏳ Pending

- **File**: `src/server/api/artifacts.py` `[NEW]`
- **Change kind**: New file
- **Full code to write**:

```python
"""Artifact-serving endpoints for the BrandMind web UI.

Two stateless endpoints exposing the artifact manifest produced by the
brand-strategy workflow:

* ``GET /sessions/{session_id}/artifacts`` — list every artifact
  recorded in ``$BRANDMIND_OUTPUT_DIR/.manifest.jsonl`` for the given
  session, as structured metadata the web UI uses to populate its
  artifact panel.
* ``GET /artifacts/{session_id}/{filename}`` — stream a single artifact
  file by manifest lookup. The URL path segments are validated as
  opaque keys (never used to construct a filesystem path), and the
  file the manifest points at is resolved and required to stay under
  the configured output root before serving. These two checks together
  defeat path-traversal attempts (``..``, absolute paths, symlinks
  escaping the base).

Stateless by design — no active session, no SessionManager
dependency — so the web UI can browse historical session artifacts
even when the brand-strategy agent is not running.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from shared.agent_tools.document._output_path import _base_dir, _manifest_path

router = APIRouter(tags=["artifacts"])

_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_FILENAME_RE = re.compile(
    r"^[A-Za-z0-9._-]+\.(docx|pptx|xlsx|png|jpg|jpeg|webp)$"
)
_INLINE_CATEGORIES = {"images"}

ArtifactCategory = Literal[
    "documents", "presentations", "spreadsheets", "images"
]


class ArtifactRef(BaseModel):
    """Public metadata about one artifact recorded in the manifest.

    Mirrors the manifest record's externally-relevant fields. The
    absolute filesystem path is intentionally omitted so the web UI
    never sees server-side layout; the ``download_url`` is the only
    handle clients need to fetch the bytes.
    """

    session_id: str
    brand_name: str
    category: ArtifactCategory
    tool: str
    filename: str
    size_bytes: int
    generated_at: str
    download_url: str


def _iter_manifest_records() -> list[dict[str, object]]:
    """Read every parseable record from the artifact manifest.

    Manifest writes are best-effort and append-only; malformed lines
    are skipped without raising so a single corrupt line never blanks
    out the artifact panel. Returns an empty list when the manifest
    file does not exist yet (no artifacts have ever been produced).

    Returns:
        records (list[dict[str, object]]): One dict per valid JSONL
            line, preserving file order.
    """
    manifest_file = Path(_manifest_path())
    if not manifest_file.is_file():
        return []

    records: list[dict[str, object]] = []
    with manifest_file.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def _record_to_ref(record: dict[str, object]) -> ArtifactRef | None:
    """Project a manifest record into an ``ArtifactRef`` for the API.

    Returns ``None`` when the record is missing required fields or the
    ``category`` value falls outside the four supported artifact types
    — those records exist on disk but cannot be surfaced through the
    web UI's typed schema.

    Args:
        record (dict[str, object]): One parsed JSONL line from the
            manifest.

    Returns:
        ref (ArtifactRef | None): The typed projection, or ``None``
            when the record cannot be safely surfaced.
    """
    category = record.get("category")
    if category not in {"documents", "presentations", "spreadsheets", "images"}:
        return None

    session_id = str(record.get("session_id", ""))
    filename = str(record.get("filename", ""))
    if not session_id or not filename:
        return None

    return ArtifactRef(
        session_id=session_id,
        brand_name=str(record.get("brand_name", "")),
        category=category,  # type: ignore[arg-type]
        tool=str(record.get("tool", "")),
        filename=filename,
        size_bytes=int(record.get("size_bytes", 0) or 0),
        generated_at=str(record.get("generated_at", "")),
        download_url=f"/api/v1/artifacts/{session_id}/{filename}",
    )


def _find_manifest_record(
    session_id: str, filename: str
) -> dict[str, object] | None:
    """Return the latest manifest record matching the key pair.

    Reads the manifest top-to-bottom and keeps the last match, so if a
    tool ever re-emits the same filename for the same session the
    freshest entry wins. Returns ``None`` when no record matches.

    Args:
        session_id (str): Session identifier from the URL.
        filename (str): Artifact basename from the URL.

    Returns:
        record (dict[str, object] | None): The latest matching record,
            or ``None`` when no match exists.
    """
    latest: dict[str, object] | None = None
    for record in _iter_manifest_records():
        if str(record.get("session_id", "")) != session_id:
            continue
        if str(record.get("filename", "")) != filename:
            continue
        latest = record
    return latest


@router.get("/sessions/{session_id}/artifacts")
def list_session_artifacts(session_id: str) -> list[ArtifactRef]:
    """List every artifact recorded for ``session_id`` in the manifest.

    Returns an empty list (HTTP 200) when the session has no manifest
    entries — there is no concept of "session not found" here, since
    the manifest is the only state this endpoint reads and an unknown
    session id is indistinguishable from a session that produced
    nothing. Records sort by ``generated_at`` ascending so the UI can
    render them in production order without re-sorting.

    Args:
        session_id (str): The session identifier as recorded in the
            manifest. Validated against a strict regex to reject path
            traversal attempts.

    Returns:
        refs (list[ArtifactRef]): Zero or more typed artifact
            references, ordered oldest to newest.

    Raises:
        HTTPException 400: ``session_id`` fails the shape-validation
            regex.
    """
    if not _SESSION_ID_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id")

    refs: list[ArtifactRef] = []
    for record in _iter_manifest_records():
        if str(record.get("session_id", "")) != session_id:
            continue
        ref = _record_to_ref(record)
        if ref is not None:
            refs.append(ref)
    refs.sort(key=lambda r: r.generated_at)
    return refs


@router.get("/artifacts/{session_id}/{filename}")
def download_artifact(session_id: str, filename: str) -> FileResponse:
    """Stream a single artifact file by ``(session_id, filename)`` lookup.

    The two URL segments are validated as opaque manifest keys and
    never used to construct a filesystem path. The artifact's absolute
    path is read from the manifest record itself and required to
    resolve under ``$BRANDMIND_OUTPUT_DIR`` before serving — this is
    the defense-in-depth check that catches both ``..`` traversal and
    symlinks pointing outside the base.

    Args:
        session_id (str): Session identifier from the URL segment.
        filename (str): Artifact basename from the URL segment.

    Returns:
        response (FileResponse): Streamed artifact bytes. ``images``
            are served with ``inline`` content disposition so they
            render in ``<img>`` tags; every other category uses the
            FastAPI default ``attachment`` disposition so direct links
            trigger a download.

    Raises:
        HTTPException 400: ``session_id`` or ``filename`` fails the
            shape-validation regex.
        HTTPException 404: no manifest record matches the
            ``(session_id, filename)`` pair, the manifest path escapes
            the output root, or the file is missing on disk.
    """
    if not _SESSION_ID_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id")
    if not _FILENAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    record = _find_manifest_record(session_id, filename)
    if record is None:
        raise HTTPException(status_code=404, detail="Artifact not found")

    file_path = Path(str(record.get("path", ""))).resolve()
    base = Path(_base_dir()).resolve()
    try:
        file_path.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=404, detail="Artifact not found")

    if not file_path.is_file():
        raise HTTPException(
            status_code=404, detail="Artifact file missing on disk"
        )

    category = str(record.get("category", ""))
    disposition = "inline" if category in _INLINE_CATEGORIES else "attachment"
    return FileResponse(
        path=file_path,
        filename=filename,
        content_disposition_type=disposition,
    )
```

- **Acceptance Criteria**:
  - [ ] `from server.api.artifacts import router, ArtifactRef` succeeds in `uv run python`
  - [ ] `router.routes` contains two routes: `/sessions/{session_id}/artifacts` and `/artifacts/{session_id}/{filename}`
  - [ ] `make typecheck` reports zero errors for this file
  - [ ] `awk 'length > 100' src/server/api/artifacts.py` produces zero output

### Component 2: `src/server/api/router.py` `[MODIFY]`

> Status: ⏳ Pending

- **File**: `src/server/api/router.py` `[MODIFY]`
- **Change kind**: Add import + add `include_router` call
- **For `[MODIFY]` — locate the change**:

```python
# old_string (full file body):
"""API router aggregation — includes all sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from server.api.chat import router as chat_router
from server.api.health import router as health_router
from server.api.search import router as search_router
from server.api.sessions import router as sessions_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(sessions_router)
api_router.include_router(chat_router)
api_router.include_router(search_router)
```

- **Full code to write** (new full body — alphabetical import order, append `artifacts_router` to the include block):

```python
"""API router aggregation — includes all sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from server.api.artifacts import router as artifacts_router
from server.api.chat import router as chat_router
from server.api.health import router as health_router
from server.api.search import router as search_router
from server.api.sessions import router as sessions_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(sessions_router)
api_router.include_router(chat_router)
api_router.include_router(search_router)
api_router.include_router(artifacts_router)
```

- **Acceptance Criteria**:
  - [ ] `uv run python -c "from server.api.router import api_router; print(sorted({getattr(r, 'path', '') for r in api_router.routes}))"` lists `/sessions/{session_id}/artifacts` and `/artifacts/{session_id}/{filename}`
  - [ ] `make typecheck` still passes (no impact on existing typing)

### Component 3: `tests/unit/test_artifacts_api.py` `[NEW]`

> Status: ⏳ Pending

- **File**: `tests/unit/test_artifacts_api.py` `[NEW]`
- **Change kind**: New file
- **Full code to write**:

```python
"""Unit tests for the artifact-serving API endpoints.

Covers manifest parsing, session filtering, response shape, path-
traversal defense (URL regex + manifest containment), and file
streaming. Uses FastAPI's ``TestClient`` against ``create_app()`` and
a per-test temporary ``BRANDMIND_OUTPUT_DIR`` so the manifest path
resolution and containment check operate inside an isolated tree.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.main import create_app


@pytest.fixture
def output_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Path]:
    """Point ``BRANDMIND_OUTPUT_DIR`` at a clean per-test directory.

    ``_base_dir()`` re-reads the environment on every call, so the
    monkeypatch propagates into the lazy lookups performed inside the
    request handlers. The output root is a sub-directory of
    ``tmp_path`` so tests can place files outside it to verify the
    containment defense.
    """
    root = tmp_path / "brandmind-output"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(root))
    yield root


@pytest.fixture
def client(output_root: Path) -> Iterator[TestClient]:
    """FastAPI TestClient bound to the temporary output directory."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def _write_manifest(
    output_root: Path, records: list[dict[str, object]]
) -> None:
    """Write one JSONL line per record to the manifest file."""
    manifest = output_root / ".manifest.jsonl"
    with manifest.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def _stub_artifact(output_root: Path, category: str, filename: str) -> Path:
    """Create a small binary file under ``<category>/brand/`` and return it."""
    target = output_root / category / "brand" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"FAKE_BINARY_PAYLOAD")
    return target


class TestListSessionArtifacts:
    """Behavior of ``GET /api/v1/sessions/{session_id}/artifacts``."""

    def test_returns_empty_when_manifest_missing(
        self, client: TestClient
    ) -> None:
        resp = client.get("/api/v1/sessions/abc123/artifacts")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_filters_by_session_id(
        self, client: TestClient, output_root: Path
    ) -> None:
        path_a = _stub_artifact(output_root, "documents", "a.docx")
        path_b = _stub_artifact(output_root, "documents", "b.docx")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "a.docx",
                    "path": str(path_a),
                    "size_bytes": 100,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                },
                {
                    "session_id": "s_beta",
                    "brand_name": "Beta",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "b.docx",
                    "path": str(path_b),
                    "size_bytes": 200,
                    "generated_at": "2026-05-16T10:01:00+07:00",
                },
            ],
        )

        resp = client.get("/api/v1/sessions/s_alpha/artifacts")
        assert resp.status_code == 200
        payload = resp.json()
        assert len(payload) == 1
        assert payload[0]["session_id"] == "s_alpha"
        assert payload[0]["filename"] == "a.docx"
        assert payload[0]["download_url"] == "/api/v1/artifacts/s_alpha/a.docx"

    def test_skips_unknown_categories_and_malformed_lines(
        self, client: TestClient, output_root: Path
    ) -> None:
        path_doc = _stub_artifact(output_root, "documents", "ok.docx")
        manifest = output_root / ".manifest.jsonl"
        manifest.write_text(
            json.dumps(
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "ok.docx",
                    "path": str(path_doc),
                    "size_bytes": 100,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            )
            + "\n"
            + "this-is-not-json\n"
            + json.dumps(
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "scratch",
                    "tool": "some_tool",
                    "filename": "x.txt",
                    "path": str(output_root / "scratch" / "x.txt"),
                    "size_bytes": 0,
                    "generated_at": "2026-05-16T10:02:00+07:00",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        resp = client.get("/api/v1/sessions/s_alpha/artifacts")
        assert resp.status_code == 200
        payload = resp.json()
        assert len(payload) == 1
        assert payload[0]["category"] == "documents"

    def test_rejects_invalid_session_id_shape(
        self, client: TestClient
    ) -> None:
        resp = client.get("/api/v1/sessions/abc..123/artifacts")
        assert resp.status_code == 400

    def test_orders_by_generated_at_ascending(
        self, client: TestClient, output_root: Path
    ) -> None:
        path_a = _stub_artifact(output_root, "documents", "early.docx")
        path_b = _stub_artifact(output_root, "documents", "late.docx")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "late.docx",
                    "path": str(path_b),
                    "size_bytes": 1,
                    "generated_at": "2026-05-16T11:00:00+07:00",
                },
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "early.docx",
                    "path": str(path_a),
                    "size_bytes": 1,
                    "generated_at": "2026-05-16T09:00:00+07:00",
                },
            ],
        )
        resp = client.get("/api/v1/sessions/s_alpha/artifacts")
        names = [item["filename"] for item in resp.json()]
        assert names == ["early.docx", "late.docx"]


class TestDownloadArtifact:
    """Behavior of ``GET /api/v1/artifacts/{session_id}/{filename}``."""

    def test_streams_valid_artifact(
        self, client: TestClient, output_root: Path
    ) -> None:
        path = _stub_artifact(output_root, "documents", "strategy.docx")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "strategy.docx",
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_alpha/strategy.docx")
        assert resp.status_code == 200
        assert resp.content == b"FAKE_BINARY_PAYLOAD"

    def test_inline_disposition_for_images(
        self, client: TestClient, output_root: Path
    ) -> None:
        path = _stub_artifact(output_root, "images", "brand_key.png")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "images",
                    "tool": "generate_brand_key",
                    "filename": "brand_key.png",
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_alpha/brand_key.png")
        assert resp.status_code == 200
        assert "inline" in resp.headers.get("content-disposition", "")

    def test_attachment_disposition_for_pptx(
        self, client: TestClient, output_root: Path
    ) -> None:
        path = _stub_artifact(output_root, "presentations", "deck.pptx")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "presentations",
                    "tool": "generate_presentation",
                    "filename": "deck.pptx",
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_alpha/deck.pptx")
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("content-disposition", "")

    def test_404_when_session_id_unknown(
        self, client: TestClient, output_root: Path
    ) -> None:
        path = _stub_artifact(output_root, "documents", "strategy.docx")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "strategy.docx",
                    "path": str(path),
                    "size_bytes": 1,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_unknown/strategy.docx")
        assert resp.status_code == 404

    def test_404_when_filename_not_in_manifest(
        self, client: TestClient, output_root: Path
    ) -> None:
        path = _stub_artifact(output_root, "documents", "real.docx")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "real.docx",
                    "path": str(path),
                    "size_bytes": 1,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_alpha/forged.docx")
        assert resp.status_code == 404

    def test_400_on_traversal_filename(self, client: TestClient) -> None:
        resp = client.get("/api/v1/artifacts/s_alpha/..passwd")
        assert resp.status_code == 400

    def test_400_on_unsafe_extension(self, client: TestClient) -> None:
        resp = client.get("/api/v1/artifacts/s_alpha/script.sh")
        assert resp.status_code == 400

    def test_400_on_invalid_session_id(self, client: TestClient) -> None:
        resp = client.get("/api/v1/artifacts/bad..sid/file.docx")
        assert resp.status_code == 400

    def test_404_when_manifest_path_escapes_base(
        self, client: TestClient, output_root: Path, tmp_path: Path
    ) -> None:
        outside = tmp_path / "outside-evil" / "evil.docx"
        outside.parent.mkdir(parents=True, exist_ok=True)
        outside.write_bytes(b"SECRET")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "evil.docx",
                    "path": str(outside),
                    "size_bytes": outside.stat().st_size,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_alpha/evil.docx")
        assert resp.status_code == 404

    def test_404_when_file_missing_on_disk(
        self, client: TestClient, output_root: Path
    ) -> None:
        phantom = output_root / "documents" / "brand" / "phantom.docx"
        phantom.parent.mkdir(parents=True, exist_ok=True)
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "phantom.docx",
                    "path": str(phantom),
                    "size_bytes": 0,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_alpha/phantom.docx")
        assert resp.status_code == 404
```

- **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/test_artifacts_api.py -v` → 14 passed (5 list + 9 download)
  - [ ] `awk 'length > 100' tests/unit/test_artifacts_api.py` → zero output
  - [ ] `uv run pytest tests/unit/test_server.py -q` → still passes (no regression)

------------------------------------------------------------------------

## 🧪 Test Execution Log

> Filled after running. Pending until Implementation is applied + tests run.

### Test 1: `pytest tests/unit/test_artifacts_api.py -v`
- **Status**: ⏳ Pending

### Test 2: `pytest tests/unit/test_server.py -q` (regression)
- **Status**: ⏳ Pending

### Test 3: `make typecheck`
- **Status**: ⏳ Pending

### Test 4: `awk 'length > 100'` across the 3 changed files
- **Status**: ⏳ Pending

### Test 5: `gitnexus_detect_changes(scope="unstaged")`
- **Status**: ⏳ Pending

### Test 6: Live smoke against running `brandmind serve`
- **Steps**:
  1. `uv run brandmind serve` in one terminal
  2. `curl http://localhost:8000/api/v1/sessions/1b4cfcf3/artifacts | jq .` (uses real historical session from manifest)
  3. Pick one filename from the response
  4. `curl -I http://localhost:8000/api/v1/artifacts/1b4cfcf3/<filename>` — verify `Content-Type`, `Content-Length`, `Content-Disposition`
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📊 Decision Log

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | Schema location | (A) `server/schemas/artifacts.py`, (B) colocated in `api/artifacts.py` | (B) Colocated | `ArtifactRef` has no consumer outside this endpoint module today; web (Task #89) lives in a separate package and will import from `server.api.artifacts`. Single-file scope keeps the new surface lean. Promote to `schemas/` if a 3rd consumer appears. |
| 2 | Path-traversal defense | (A) Filename regex only, (B) Manifest lookup only, (C) Containment check only, (D) Combine A+B+C | (D) Three layers | Each layer catches a different class: regex stops obvious traversal at the routing layer; manifest lookup means only files BrandMind itself wrote are servable (an attacker would have to inject into `.manifest.jsonl`); containment check defends against symlinks and absolute paths the manifest might point at. Defense-in-depth is cheap here (3 lines per check). |
| 3 | `content_disposition_type` policy | (A) Always `attachment`, (B) Always `inline`, (C) Category-based | (C) `inline` for images, `attachment` otherwise | `<img src>` needs `inline` to render Brand Key without a download prompt; PPTX/XLSX direct links should trigger a download; DOCX is fetched by mammoth-js via `fetch()` which ignores disposition entirely — `attachment` is the safer browser default. |
| 4 | Active-session gating | (A) Require active brand-strategy session, (B) Stateless | (B) Stateless | Web UI should be able to browse historical sessions (thesis demo replays from past pilots) without re-launching an agent. The manifest is the persistent state; there's no privacy boundary because the manifest is local-only on the operator's machine. |
| 5 | Where to import `_base_dir` and `_manifest_path` from | (A) Re-export as public via `_output_path.py`, (B) Import private symbols directly | (B) Direct import | `list_artifacts.py` already does this; following the existing convention. Promoting these to public adds a deprecation surface for a single in-repo caller. |

------------------------------------------------------------------------

## 📝 Task Summary

> Filled after task is fully complete and tests pass.

### What Was Implemented

- [ ] *Pending implementation*

### Validation Results

- [ ] *Pending*

### Deployment Notes

- [ ] No new dependencies — all imports are stdlib, FastAPI built-in, or existing internal modules.
- [ ] No new environment variables.
- [ ] No schema migration.
- [ ] Reads `BRANDMIND_OUTPUT_DIR` (already used by `_base_dir()` for artifact writes).
