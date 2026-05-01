# Task 56: Mount BRANDMIND_OUTPUT_DIR as virtual `/output/` filesystem

## 📌 Metadata

- **Epic**: Brand Strategy Agent — Production hardening
- **Priority**: High
- **Status**: Done
- **Estimated Effort**: 1 day
- **Team**: Backend / Agent
- **Related Tasks**: commit `f56eb2c` (sandbox helper, this task closes a regression it introduced)
- **Blocking**: M-7 round close-out decision (Option A / B / C — see `memory/project_pending_decision.md`)
- **Blocked by**: None

### ✅ Progress Checklist

- [x] 🤖 Agent Protocol — Read and confirmed
- [x] 🎯 Context & Goals — Problem definition and success metrics
- [x] 🛠 Solution Design — Architecture and technical approach
- [x] 🔬 Pre-Implementation Research — Findings logged below
- [x] 🔄 Implementation Plan — Phased execution
- [ ] 📋 Implementation Detail
    - [ ] ⏳ Component 1 — Restore tests broken by `f56eb2c` sandbox
    - [ ] ⏳ Component 2 — Add `/output/` route to `CompositeBackend`
    - [ ] ⏳ Component 3 — Surface virtual `/output/...` paths in artifact-tool result messages
    - [ ] ⏳ Component 4 — Update orchestrator system prompt to expose `/output/` filesystem
    - [ ] ⏳ Component 5 — Tighten artifact-tool `output_path` docstrings
- [ ] 🧪 Test Execution Log
- [ ] 📊 Decision Log
- [ ] 📝 Task Summary

## 🔗 Reference Documentation

- **Coding Standards**: `tasks/task_template.md` Rule 4 (Production-Grade Code Standards) and Rule 5 (Prompt Engineering Standards).
- **Prompt standards**: skills `prompt-engineering-patterns` (cross-cutting principles + system-prompt-design + tool-description-design).
- **Existing pattern**: `src/shared/src/shared/agent_skills/config.py` — current CompositeBackend setup with `/workspace/` and `/user/` routes.
- **Sandbox helper**: `src/shared/src/shared/agent_tools/document/_output_path.py` (introduced in `f56eb2c`).
- **Memory**: `memory/feedback_commit_discipline.md` (commit-per-concern, never auto-push).

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- The four artifact-generation tools (`generate_document`, `generate_presentation`, `generate_spreadsheet`, `export_to_markdown`) write physical files to the directory pointed to by `BRANDMIND_OUTPUT_DIR`. Sub-agents repeatedly passed bare filenames (e.g. `"strategy_signature.docx"`), causing 13 stray artifacts to land at the repo root across sessions on 2026-04-29 → 2026-04-30.
- The orchestrator's `FilesystemMiddleware` (via `CompositeBackend`) exposes three logical roots — `/` (skills, read-only), `/workspace/` (project notes), `/user/` (global profile). It does **not** mount `BRANDMIND_OUTPUT_DIR`. The agent therefore has no filesystem-level perception of where artifacts live; it sees `BRANDMIND_OUTPUT_DIR` only as a string returned in tool result messages, with no way to `ls` it, no way to verify what was written, and no way to cross-reference an artifact path against a workspace path.
- Commit `f56eb2c` patched the symptom by sandboxing `output_path` inside the four tools, but it (a) does not change the agent's mental model and (b) introduced three test regressions in `tests/unit/test_document_tools.py` because legitimate test paths under `tmp_path` are now redirected.

### Mục tiêu

Make `BRANDMIND_OUTPUT_DIR` a first-class virtual filesystem at `/output/` that the orchestrator perceives the same way it perceives `/workspace/` and `/user/`. Restore the failing tests, surface `/output/...` virtual paths in artifact-tool result messages so the agent can reason about them coherently, and tighten the docstrings + system prompt so neither the LLM nor the test suite has cause to write outside the configured base directory.

### Success Metrics / Acceptance Criteria

- **Functional**: `read_file("/output/")`, `ls("/output/")`, `read_file("/output/documents/<file>.md")` all succeed from the orchestrator.
- **Sandboxing**: `resolve_output_path` continues to anchor every physical write under `BRANDMIND_OUTPUT_DIR/<category>/`. No artifact lands at the repo root or anywhere outside `BRANDMIND_OUTPUT_DIR`.
- **Tests**: `uv run pytest tests/unit/test_document_tools.py` passes (currently 3 known failures from `f56eb2c`); `uv run pytest tests/integration/test_brand_strategy_skills.py` passes; smoke test (`make eval-smoke`) maintains Tier 1 5/5.
- **Agent perception**: artifact-tool result messages reference virtual paths (`/output/documents/<file>.docx`) instead of raw absolute paths, matching the `/workspace/...` convention. Smoke transcript shows the agent receiving these virtual paths.
- **No regression** on the M-7-I content-judge baseline (canary aggregate ≥ 2/3 PASS).

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Mount `BRANDMIND_OUTPUT_DIR` as a `/output/` route in the existing `CompositeBackend`.** The orchestrator already uses `CompositeBackend` to multiplex skills + workspace + user; adding a fourth route is the smallest change that gives the agent first-class filesystem awareness of artifact output, while leaving the physical sandbox in `_output_path.py` in place as a defensive layer.

### Stack công nghệ

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| `deepagents.backends.filesystem.FilesystemBackend` | Read-write backend per route | Already in use for `/workspace/` and `/user/` — same idiom |
| `deepagents.backends.composite.CompositeBackend` | Multiplex routes | Already wired to `FilesystemMiddleware` |
| `deepagents.middleware.filesystem.FilesystemMiddleware` | Exposes `read_file` / `write_file` / `edit_file` / `ls` / `grep` to the agent | Gives the agent its filesystem tool set |

### Architecture Overview

```
Before:
    CompositeBackend
    ├── default       → skills/                    (read-only)
    ├── /workspace/   → ~/.brandmind/projects/<id>/workspace/
    └── /user/        → ~/.brandmind/user/

    BRANDMIND_OUTPUT_DIR/   ← physical only; agent has no filesystem view

After:
    CompositeBackend
    ├── default       → skills/                    (read-only)
    ├── /workspace/   → ~/.brandmind/projects/<id>/workspace/
    ├── /user/        → ~/.brandmind/user/
    └── /output/      → $BRANDMIND_OUTPUT_DIR/     ← NEW (read-write)

    Tool result messages now report "/output/<category>/<file>"
    instead of "$BRANDMIND_OUTPUT_DIR/<category>/<file>".
    Physical sandboxing in _output_path.py is unchanged — defense in
    depth.
```

### Issues & Solutions

1. **`tmp_path` test paths get redirected by the sandbox** → tests were passing arbitrary absolute paths and the sandbox now anchors under `BRANDMIND_OUTPUT_DIR`. Fix: use `monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))` so the test's tmp directory becomes the configured base, and any path under it is honoured.
2. **Backward compatibility for callers that still use physical paths** → the agent and existing scripts may still produce absolute paths. Resolve them in two steps: (a) the underlying tool keeps physical-disk semantics; (b) only the *return message* maps the physical path back to its virtual `/output/...` projection so the agent's view is consistent.
3. **`create_brand_strategy_skills_middleware` signature change** → callers are 1 production site (`agent_config.py`) and 1 test (`test_brand_strategy_skills.py`). Adding `output_dir: str | None = None` as an optional parameter avoids a breaking change.
4. **Sub-agents do not have filesystem middleware** → unchanged. The `/output/` route is for the main orchestrator's perception; sub-agents continue to call generate-* tools directly and the sandbox keeps writes safe regardless of what they pass.

------------------------------------------------------------------------

## 🔬 Pre-Implementation Research

### Codebase Audit

Files read end-to-end:

- `src/shared/src/shared/agent_skills/config.py` — confirms `CompositeBackend` is the existing multiplex point; routes are passed as a `dict[str, FilesystemBackend]`. Adding `/output/` follows the exact same idiom as `/workspace/` and `/user/`.
- `src/shared/src/shared/agent_skills/__init__.py` — exports `create_brand_strategy_skills_middleware` only; signature change with default-None preserves the public surface.
- `src/core/src/core/brand_strategy/agent_config.py` — single production caller of `create_brand_strategy_skills_middleware` (line 377). Already resolves `workspace_dir` and `user_dir` from the active session; we will add `output_dir` resolution via `SETTINGS.BRANDMIND_OUTPUT_DIR`.
- `src/config/system_config.py` (lines 64–68) — `SETTINGS.BRANDMIND_OUTPUT_DIR` already resolves the env var with a sane default.
- `src/shared/src/shared/agent_tools/document/_output_path.py` — sandbox introduced in `f56eb2c`. Will keep `resolve_output_path` as the physical-disk source of truth; add a thin `physical_to_virtual` helper for the result-message projection.
- `src/shared/src/shared/agent_tools/document/{generate_document,generate_presentation,generate_spreadsheet,export_to_markdown}.py` — four tools whose return messages currently surface raw physical paths. Each needs the virtual-path projection.
- `src/prompts/brand_strategy/system_prompt.py` — already documents `/workspace/` and `/user/` (lines 405–408). Add a parallel `/output/` row + a one-line mention in the Phase 5 section so the agent treats it as a peer filesystem.
- `tests/unit/test_document_tools.py` (lines 318–346) — three `tmp_path` tests must be updated; will use `monkeypatch.setenv` so the sandbox's "under base_dir" check passes naturally.
- `tests/integration/test_brand_strategy_skills.py` (lines 75, 81, 86) — calls `create_brand_strategy_skills_middleware()` with no args; backward-compat preserved by default-None on the new param.

Other call sites that must not be missed (full grep):

- `BRANDMIND_OUTPUT_DIR` / `brandmind-output` references: configuration (`environments/.env`, `scripts/setup_env.sh`), evaluation tooling (`evaluation/artifact_audit.py`, `evaluation/judge/run_judges.py`, `evaluation/judge/artifact_judge.py`, `evaluation/smoke_test.py`, `evaluation/eval_session.py`), tests (`tests/manual/*`, `tests/unit/test_document_tools.py`), and `.gitignore`. **None of these need to change** — they already use the physical path convention and are external to the agent's filesystem view. The only files touched in this task are the orchestrator middleware setup, the four artifact tools' return messages, the system prompt, and the unit-test fix.

### External Library / API Research

- **`deepagents.backends.composite.CompositeBackend`**: `routes: dict[str, FilesystemBackend]`, `default: FilesystemBackend`. Routes are matched by longest-prefix; the route key is the virtual prefix (`"/output/"`). Constructor and behaviour identical to existing `/workspace/` mount — no new API surface.
- **`deepagents.backends.filesystem.FilesystemBackend`**: signature `FilesystemBackend(root_dir: str, virtual_mode: bool = False)`. Already used twice in `config.py` (workspace_backend, user_backend). `virtual_mode=True` so the agent only sees the virtual prefix, not the physical disk path.
- **`deepagents.middleware.filesystem.FilesystemMiddleware`**: provides `read_file`, `write_file`, `edit_file`, `ls`, `grep` automatically over whatever backend it is constructed with. No tool-list change needed when we add the route — the same tool calls just gain visibility into one more virtual prefix.

### Unknown / Risks Identified

- [x] Confirm `tmp_path`-based unit tests can use `monkeypatch.setenv` to point `BRANDMIND_OUTPUT_DIR` at the test's own tmp directory — verified by reading the existing tool source: `_base_dir()` reads the env var on every call, so the test path becomes the base and any path under `tmp_path` is honoured by the sandbox.
- [x] Confirm sub-agents are unaffected — sub-agents do not receive `FilesystemMiddleware`; they call generate-* tools directly. The new `/output/` route is purely an addition for the orchestrator's filesystem view. No sub-agent contract changes.
- [x] Backward compatibility — `create_brand_strategy_skills_middleware` gains `output_dir: str | None = None`; existing callers (1 production, 1 test) are unaffected.

### Research Status

- [x] All referenced documentation read
- [x] Existing codebase patterns understood
- [x] External dependencies verified
- [x] No unresolved ambiguities remain → Ready to implement

------------------------------------------------------------------------

## 🔄 Implementation Plan

### Phase 1: Restore broken unit tests — 10 min

1. **Fix `tmp_path` tests in `tests/unit/test_document_tools.py`**
   - Add `monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))` to each affected test (`test_long_content_writes_to_file`, `test_long_content_creates_parent_dirs`, `test_long_content_reports_char_count`).
   - Adjust assertions to match the post-sandbox path (the file lives under `tmp_path/documents/<basename>` rather than the raw `tmp_path/<filename>`).
   - *Checkpoint*: `uv run pytest tests/unit/test_document_tools.py -q` shows 0 failures.

### Phase 2: Mount `/output/` in the orchestrator backend — 20 min

1. **Add `output_dir` parameter to `create_brand_strategy_skills_middleware`**
   - Append `output_dir: str | None = None` to the signature; document in the docstring.
   - When provided, instantiate a `FilesystemBackend(root_dir=output_dir, virtual_mode=True)` and add it to the `routes` dict under key `"/output/"`.
   - Update the log line that lists configured routes so operators see the `/output/` mount in startup logs.
   - *Checkpoint*: `tests/integration/test_brand_strategy_skills.py` still passes (default-None signature change is non-breaking).

2. **Wire `BRANDMIND_OUTPUT_DIR` through `agent_config.py`**
   - Import `SETTINGS` (already imported; reuse `SETTINGS.BRANDMIND_OUTPUT_DIR`).
   - Resolve the absolute path via the same logic the tools use: `os.environ.get("BRANDMIND_OUTPUT_DIR")` falls back to `os.path.join(os.getcwd(), "brandmind-output")`. Reuse `resolve_output_path._base_dir` if reasonable, otherwise inline.
   - Pass `output_dir=<resolved>` to `create_brand_strategy_skills_middleware`.
   - *Checkpoint*: server start (`brandmind serve`) logs the new route; quick interactive `read_file("/output/")` returns directory listing (smoke).

### Phase 3: Surface virtual `/output/...` paths in artifact-tool messages — 15 min

1. **Add `physical_to_virtual` helper in `_output_path.py`**
   - Pure function that maps an absolute path under `BRANDMIND_OUTPUT_DIR` to its `/output/<...>` projection. Return the input path unchanged when it is not under the configured base (fail-soft for unexpected paths).

2. **Update the four artifact tools' return messages**
   - `generate_document`, `generate_presentation`, `generate_spreadsheet`, `export_to_markdown` each currently embed the resolved `output_path` in their return string. Replace that with the virtual projection so the agent reads `Path: /output/documents/<file>.docx` instead of `Path: /Users/.../brandmind-output/documents/<file>.docx`.
   - The physical write itself is unchanged.
   - *Checkpoint*: unit tests still pass; smoke transcript shows virtual paths.

### Phase 4: Document `/output/` in the orchestrator system prompt — 15 min

1. **Add `/output/` row to the workspace-files table in `system_prompt.py`**
   - Treat as a peer to `/workspace/`, `/user/`. One line: "Artifact filesystem at `/output/<category>/`. Read-only browsing for verifying what was generated; writes happen via `generate_document` / `generate_presentation` / `generate_spreadsheet` / `export_to_markdown`."
2. **Mention briefly in Phase 5 closure section**
   - One sentence referencing that the four artifact tools land their output under `/output/` so the orchestrator can verify each file landed before declaring closure.
   - Affirmative phrasing with a Why anchor (per `prompt-engineering-patterns` cross-cutting principle 1 + 4); no MUST blocks.

### Phase 5: Tighten artifact-tool docstrings — 10 min

1. **Replace the vague `output_path: Custom output path. Default uses BRANDMIND_OUTPUT_DIR.`**
   - Across all four tools: state that `output_path` should normally be left `None`; the tool anchors output under `/output/<category>/<default_filename>` automatically. Provide an explicit example only when a specific filename is required.
   - *Checkpoint*: agent-side smoke (next pilot or canary) shows the agent stops passing bare filenames in `output_path`.

### Phase 6: Verify end-to-end — 10 min

1. Run `uv run pytest tests/unit/test_document_tools.py tests/integration/test_brand_strategy_skills.py -q`.
2. Run `make eval-smoke` to confirm Tier 1 5/5 unchanged + canary content judge does not regress.
3. Inspect a smoke session's pilot state file: artifact-tool result messages should now contain `/output/...` paths.

### Rollback Plan

- `git revert <task_56 commit>` reverts the `/output/` route, the system-prompt mention, the docstring tightening, and the test fixes in one shot. The sandbox helper from `f56eb2c` remains in place as the defensive layer; physical path semantics are unchanged. No data loss possible — this task is metadata + path-display + tests only.

------------------------------------------------------------------------

## 📋 Implementation Detail

### Component 1: Restore tests broken by `f56eb2c` sandbox

> Status: ⏳ Pending

#### Requirement 1 — `tmp_path` tests must coexist with the sandbox

- **Requirement**: The three `test_long_content_*` cases in `TestExportToMarkdown` write to `tmp_path` and assert the file landed there. After the sandbox, paths outside `BRANDMIND_OUTPUT_DIR` are redirected. Bind `BRANDMIND_OUTPUT_DIR` to the test's `tmp_path` so the sandbox honours the test's intent without weakening the production guarantee.

- **Test Specification**:
  ```python
  # Test case 1 (test_long_content_writes_to_file): set BRANDMIND_OUTPUT_DIR=tmp_path,
  #     pass output_path=tmp_path/"export.md", assert resulting file lives at
  #     tmp_path/"documents"/"export.md" (sandbox anchors under the configured category).
  # Test case 2 (test_long_content_creates_parent_dirs): same monkeypatch; output_path
  #     pointing at a nested tmp_path subdir is honoured because tmp_path is the
  #     configured base.
  # Test case 3 (test_long_content_reports_char_count): same; assert the char-count
  #     marker appears in the result message regardless of where the file lands.
  ```

- **Implementation**: `tests/unit/test_document_tools.py`
  - Add `monkeypatch` fixture to each affected test signature.
  - Set `monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))` at the top of each body.
  - Update assertions to reference the sandboxed path `tmp_path / "documents" / <basename>`.

- **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/test_document_tools.py -q` reports 0 failures.
  - [ ] No production code in `_output_path.py` is weakened.

### Component 2: Add `/output/` route to `CompositeBackend`

> Status: ⏳ Pending

#### Requirement 1 — `create_brand_strategy_skills_middleware` mounts `/output/` when an `output_dir` is supplied

- **Requirement**: Extend the existing tri-route composite (skills + `/workspace/` + `/user/`) with a fourth route `/output/` mapped to a read-write `FilesystemBackend(root_dir=output_dir, virtual_mode=True)`. When `output_dir` is `None`, behaviour is unchanged.

- **Test Specification**:
  ```python
  # Test case 1: workspace + user + output → CompositeBackend has 3 routes.
  # Test case 2: workspace + user only → CompositeBackend has 2 routes (no /output/).
  # Test case 3: with output_dir set, FilesystemMiddleware can read_file the
  #              directory listing of "/output/" and find any file written there.
  ```

- **Implementation**: `src/shared/src/shared/agent_skills/config.py`
  - Add `output_dir: str | None = None` to `create_brand_strategy_skills_middleware`.
  - When provided alongside `workspace_dir` + `user_dir`, instantiate `output_backend = FilesystemBackend(root_dir=output_dir, virtual_mode=True)` and include `"/output/": output_backend` in the routes dict.
  - Extend the `logger.info(...)` line so the new route is visible at startup.

- **Acceptance Criteria**:
  - [ ] `tests/integration/test_brand_strategy_skills.py` still passes with default-None.
  - [ ] Manual smoke: `read_file("/output/")` from the orchestrator shell returns a non-empty directory listing after a generate-* tool runs.

#### Requirement 2 — `agent_config.py` resolves and passes `output_dir`

- **Requirement**: Compute the absolute output base (`SETTINGS.BRANDMIND_OUTPUT_DIR` falling back to `os.path.join(os.getcwd(), "brandmind-output")`) and pass it through to `create_brand_strategy_skills_middleware`.

- **Implementation**: `src/core/src/core/brand_strategy/agent_config.py`
  - Reuse the resolution helper from `_output_path._base_dir()` (or inline equivalent) so we keep a single source of truth for the base directory.
  - Forward as `output_dir=<resolved>` to the existing call site (line 377).

- **Acceptance Criteria**:
  - [ ] Server startup logs include the new `/output/` route.
  - [ ] Tier 1 smoke unchanged (5/5).

### Component 3: Surface virtual `/output/...` paths in artifact-tool messages

> Status: ⏳ Pending

#### Requirement 1 — Pure helper that maps physical → virtual

- **Requirement**: Add a `physical_to_virtual(absolute_path: str) -> str` helper next to `resolve_output_path`. Returns `/output/...` when the input is under the configured base, otherwise returns the input unchanged.

- **Test Specification**:
  ```python
  # Case 1: path under base → "/output/documents/foo.docx".
  # Case 2: path outside base → returned unchanged (defensive — caller's choice).
  # Case 3: BRANDMIND_OUTPUT_DIR unset → defaults to ./brandmind-output, helper still works.
  ```

- **Implementation**: `src/shared/src/shared/agent_tools/document/_output_path.py`
  - Pure function; no I/O.
  - Reuses `_base_dir()`.
  - Exposes `physical_to_virtual` from the module.

#### Requirement 2 — Tools report virtual paths in their result messages

- **Requirement**: Each of `generate_document`, `generate_presentation`, `generate_spreadsheet`, `export_to_markdown` returns a message containing `Path: /output/<category>/<file>` instead of the raw physical path.

- **Implementation**: Edit each tool's return-message construction to call `physical_to_virtual(result_path)`.

- **Acceptance Criteria**:
  - [ ] Smoke transcript or unit test on a tool's result shows `/output/...` in the path field.
  - [ ] Physical writes continue to land at the same disk location (verify by inspecting `os.path.exists` on the underlying physical path).

### Component 4: Update orchestrator system prompt

> Status: ⏳ Pending

#### Requirement 1 — Document `/output/` as a peer filesystem

- **Requirement**: Extend the existing workspace-files table (currently lists `/workspace/`, `/user/`) with a `/output/` row so the agent reads it as a parallel concept.

- **Implementation**: `src/prompts/brand_strategy/system_prompt.py`
  - Add one row to the table block. One sentence in the Phase 5 closure section: artifact tools land under `/output/<category>/`; you can `ls /output/<category>/` to verify before declaring closure.
  - Affirmative phrasing, with a Why anchor (parallel filesystem view = same mental model as workspace notes); no MUST block.

- **Acceptance Criteria**:
  - [ ] Word count for the addition stays under ~80 words (preserve prompt budget).
  - [ ] No deviation from existing voice/structure of the prompt.

### Component 5: Tighten artifact-tool `output_path` docstrings

> Status: ⏳ Pending

#### Requirement 1 — Discourage gratuitous `output_path` overrides

- **Requirement**: Replace the current `output_path: Custom output path. Default uses BRANDMIND_OUTPUT_DIR.` text in all four tools with explicit guidance: leave `None` so the tool anchors under `/output/<category>/<default>`; provide a value only when a specific filename is required, and prefer `/output/...` virtual paths when you do.

- **Implementation**: edit the `Args:` section of each of the four tool docstrings.

- **Acceptance Criteria**:
  - [ ] Per-tool sub-agent retries no longer pass bare filenames in `output_path` on the next pilot.
  - [ ] Docstring length stays within reasonable bounds (no doubling of the section).

------------------------------------------------------------------------

## 🧪 Test Execution Log

### Test 1: `tests/unit/test_document_tools.py`

- **Purpose**: Confirm the three `tmp_path` tests pass after the sandbox + `monkeypatch.setenv` fix.
- **Steps**:
  1. `uv run pytest tests/unit/test_document_tools.py -q`
- **Expected Result**: All tests pass; the previously failing trio is green.
- **Actual Result**: TBD
- **Status**: ⏳ Pending

### Test 2: `tests/integration/test_brand_strategy_skills.py`

- **Purpose**: Confirm the `create_brand_strategy_skills_middleware` signature change with default-None is non-breaking.
- **Steps**:
  1. `uv run pytest tests/integration/test_brand_strategy_skills.py -q`
- **Expected Result**: All tests pass; existing zero-arg calls still return a valid (skills-only) backend.
- **Actual Result**: TBD
- **Status**: ⏳ Pending

### Test 3: `make eval-smoke`

- **Purpose**: Verify Tier 1 health stays 5/5 and the canary content judge does not regress vs the M-7-I baseline (3/3 PASS reproducible).
- **Steps**:
  1. `BRANDMIND_DEBUG_TOOLS=true uv run brandmind serve &`
  2. `make eval-smoke`
  3. `python evaluation/judge/artifact_judge.py --session-dir <smoke session>`
- **Expected Result**: Tier 1 5/5; aggregate ≥ 2/3 PASS.
- **Actual Result**: TBD
- **Status**: ⏳ Pending

### Test 4: Agent perception of `/output/`

- **Purpose**: Confirm the orchestrator now sees `/output/` as a real filesystem.
- **Steps**:
  1. After smoke run, find any pilot state JSON.
  2. Search agent replies and tool results for `/output/` substring.
- **Expected Result**: Tool result messages contain `/output/<category>/<file>`; agent's own text references `/output/...` paths when describing artifacts.
- **Actual Result**: TBD
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📊 Decision Log

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | Mount `BRANDMIND_OUTPUT_DIR` as `/output/` route vs. continue with sandbox-only | (A) `/output/` mount + virtual paths in messages, (B) keep sandbox-only and rely on docstrings, (C) split into per-category routes (`/output/documents/`, `/output/presentations/`) | (A) | The sandbox-only path leaves the agent without a coherent mental model — the very gap the user flagged. Adding `/output/` mirrors the existing `/workspace/`+`/user/` pattern and is the smallest change that gives the orchestrator filesystem-level perception. (C) is over-engineered: the existing category subdirectories live inside the route already and are visible via `ls`. |
| 2 | Restore broken tests via `monkeypatch.setenv` vs. weakening the sandbox to "honour any provided path" | (A) Tests pin `BRANDMIND_OUTPUT_DIR` to `tmp_path`, sandbox stays strict; (B) Sandbox always honours absolute paths (revert defensive behaviour) | (A) | Option (B) reintroduces the production leak the sandbox was designed to prevent. Option (A) keeps the production guarantee intact and clarifies the test's intent (the test is exercising path resolution, not bypassing the sandbox). |
| 3 | Filesystem-mount abstraction vs. tool-API abstraction for orchestrator visibility | (A) `/output/` filesystem mount that the orchestrator can `ls`/`read_file`; (B) tool-API: `list_artifacts(scope, category)` reads an append-only manifest; orchestrator never sees raw filesystem | (B) | The mount is the wrong abstraction for two reasons. First, binary artifacts (DOCX/PPTX/XLSX) cannot be meaningfully `read_file`-ed; the agent gets bytes it cannot reason over. Second, the sub-agent's `FILE saved` confirmation lives in the sub-agent's own context — main agent only sees `task()` text return, not the inner tool result, so a mount does not give it the verification view it actually needs. The tool API returns structured metadata (path, brand, category, generated_at, size) that main agent can act on, and the manifest doubles as cross-session provenance. The user's filesystem stays the same: `BRANDMIND_OUTPUT_DIR` is still a real OS-level directory the user browses with Finder/Explorer; only the agent's access changes. |
| 4 | Output-path layout: shared filename vs. per-brand subdir + timestamp filename | (A) keep flat `<base>/<category>/<safe_brand>_<filename>` (current pre-Task-56); (B) per-session subdir `<base>/sessions/<session_id>/...` (rejected: breaks cross-session continuity for the same brand); (C) per-brand subdir + timestamp filename `<base>/<category>/<brand-slug>/<timestamp>_<filename>` | (C) | Option (A) silently overwrites previous sessions' artifacts whenever the agent reuses a `brand_name`, and the smoke test reproduced an agent confusion mode where stale files from prior sessions were claimed as the current run's deliverables. Option (B) destroys the "artifacts as the user's brand workspace" promise — opening Finder to a session-id directory is not how a junior marketer organises their brand work. Option (C) preserves cross-session continuity (one brand's history stays together) and prevents collisions through the timestamp prefix. The user can still pick the latest artifact via mtime sort or browse the version history. |
| 5 | Document-generator dispatch shape: one call with three formats vs. three single-format calls (B1) | (A) one `task()` packages DOCX + PPTX + XLSX schemas in a single description; (B) three `task()` calls, each carrying one format's schema | (B) | Smoke v1 with shape (A) returned Tier 1 health 3/5 — sub-agent (Gemini 2.5 Flash Lite) reliably produced the first artifact but skipped or under-filled the second and third. Sub-agent isolation test confirmed the model is capable of the work given a focused brief, so the regression is in the multi-output-per-dispatch shape, not the model. Splitting in (B) trades modest extra latency for a deterministic per-artifact bar; smoke v4 returned Tier 1 5/5 with all four artifact categories present and DOCX semantically full. Content-depth follow-ups (PPTX trailing slides, XLSX Monthly Tracking sheet) are tracked as a separate task; (B) closes the artifact-existence gate, not the content-depth one. |

------------------------------------------------------------------------

## 📝 Task Summary

### What Was Implemented

**Output abstraction (Task 56 core)**:
- `BRANDMIND_OUTPUT_DIR` is no longer mounted as a virtual `/output/` filesystem; the prior `ReadOnlyOutputBackend`, the `output_dir` parameter on `create_brand_strategy_skills_middleware`, the `agent_config.py` wiring, and the `/output/<category>/` row in the workspace-files table are all gone.
- `resolve_output_path` reworked to anchor every artifact under `$BRANDMIND_OUTPUT_DIR/<category>/<brand-slug>/<timestamp>_<filename>`. Per-brand subdirectory + timestamp prefix removes both cross-session filename collisions and cross-brand co-mingling while preserving the user's "browse the brand's artifacts in Finder" experience.
- `append_manifest` writes one JSONL line per artifact production to `$BRANDMIND_OUTPUT_DIR/.manifest.jsonl` carrying `session_id`, `brand_name`, `category`, `tool`, `filename`, absolute `path`, `size_bytes`, and ISO-8601 `generated_at`. A late-import on `core.brand_strategy.session.get_active_session` keeps the `shared` package free of a hard `core` dependency; CLI / unit-test callers fall back to the sentinel `unbound`.
- New `list_artifacts(scope, category)` tool registered in `main_agent_tools` lets the orchestrator read the manifest and confirm what the current session has produced. The Phase 5 closure rule in `system_prompt.py` calls it as the last gate before declaring the strategy done.
- Each of the four artifact-tool entry points (`generate_document`, `generate_presentation`, `generate_spreadsheet`, `export_to_markdown`) now passes `brand_name` into `resolve_output_path` and appends to the manifest after a successful builder save. Tool result messages return the absolute filesystem path the user can open directly.

**Orchestrator dispatch split (B1, bundled here so the smoke gate passes)**:
- The Phase 5 dispatch templates in `system_prompt.py` direct the orchestrator to send three separate `task(subagent_type="document-generator", …)` calls — one for DOCX, one for PPTX, one for XLSX — each carrying the verbatim workspace excerpt plus only the format-specific schema.
- The document-generator sub-agent system prompt locks in a one-artifact-per-dispatch contract and names the matching tool per format, so the sub-agent knows it is handling a single-output run, not a three-output one.

**Files Created / Modified**:
```
src/shared/src/shared/agent_tools/document/
├── _output_path.py          # rework: per-brand subdir + timestamp + manifest
├── list_artifacts.py        # NEW: manifest query tool
├── __init__.py              # export list_artifacts
├── generate_document.py     # brand_name → resolve_output_path; manifest append
├── generate_presentation.py # brand_name → resolve_output_path; manifest append
├── generate_spreadsheet.py  # brand_name → resolve_output_path; manifest append
└── export_to_markdown.py    # add brand_name param; manifest append
src/shared/src/shared/agent_skills/config.py     # revert /output/ mount + ReadOnlyOutputBackend
src/core/src/core/brand_strategy/agent_config.py # revert output_dir wiring; add list_artifacts to main_agent_tools
src/prompts/brand_strategy/system_prompt.py      # Phase 5 closure rule + tool inventory entry; split dispatch templates
src/prompts/brand_strategy/subagents/document_generator.py # one-format-per-dispatch contract
tests/unit/test_document_tools.py                # 18 new + 3 updated assertions for new layout
```

### Validation Results

**Test Results**:
- `make typecheck` clean (ruff format / ruff check / mypy / bandit).
- `uv run pytest tests/unit/test_document_tools.py tests/integration/test_brand_strategy_skills.py -q` → 114 passed.
- `uv run python evaluation/subagent_isolation_test.py` → 3/3 cases passed (creative-studio Brand Key, document-generator strategy DOCX + PPTX, document-generator KPI XLSX).
- `make eval-smoke` → Tier 1 health 5/5; brand-key, DOCX, PPTX, XLSX all produced; manifest at `<base>/.manifest.jsonl` records every artifact with the brand-strategy session id; per-brand-subdir paths visible under `<base>/<category>/<brand-slug>/`.

**Known follow-ups** (separate task, out of scope):
- PPTX slide 9 (Implementation Roadmap) and slide 10 (KPIs) come back content-light, even with B1 split. Same pattern observed in the subagent isolation output. The trailing-slide gap is a schema-to-tool-args mapping issue inside the sub-agent, not a multi-tool-per-dispatch issue.
- XLSX Monthly Tracking sheet is similarly under-filled (header + title only).
- Orchestrator over-dispatches at Phase 5 (smoke v4 produced 3 DOCX, 3 PPTX, 5 XLSX where 1 of each suffices). Tier 1 still passes (existence gate) but cost / latency would benefit from de-duplication.
