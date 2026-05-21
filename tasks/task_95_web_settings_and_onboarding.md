# Task 95: Web Settings & First-Run Onboarding

## 📌 Metadata

- **Epic**: Web UI v1 personalization
- **Priority**: High
- **Status**: In Progress
- **Estimated Effort**: 1 day
- **Team**: Web / Full-stack
- **Related Tasks**: Task #88-#94 (Web UI v1 slice), 2026-05-21 backend profile settings contract (uncommitted on Codex side per shared wiki)
- **Blocking**: —
- **Blocked by**: —

### ✅ Progress Checklist

- [x] 🤖 Agent Protocol — Read and confirm before starting
- [x] 🎯 Context & Goals — Problem definition and success metrics
- [x] 🛠 Solution Design — Architecture and technical approach
- [x] 🔬 Pre-Implementation Research — Findings logged before coding
- [x] 🔄 Implementation Plan — Phased execution plan confirmed with user
- [ ] 📋 Implementation Detail — Full ready-to-apply code for every Requirement
    - [ ] ⏳ Component A: Wire-mirror Pydantic models
    - [ ] ⏳ Component B: API client helpers
    - [ ] ⏳ Component C: State surface
    - [ ] ⏳ Component D: Settings modal dialog
    - [ ] ⏳ Component E: First-run onboarding dialog
    - [ ] ⏳ Component F: Sidebar Settings footer entry
    - [ ] ⏳ Component G: Page-level dialog mount
    - [ ] ⏳ Component H: Unit tests for wire models + state helpers
- [ ] 🧪 Test Execution Log — All tests run and results recorded
- [ ] 📊 Decision Log — Key decisions documented
- [ ] 📝 Task Summary — Final implementation summary completed

## 🔗 Reference Documentation

- **Backend contract source**: `src/server/api/brand_strategy.py` (lines 51-111), `src/shared/src/shared/workspace/profile_settings.py`
- **Existing dialog pattern**: `web/brandmind_web/components/sidebar.py` (`chat_action_dialogs`, lines 514-638)
- **Existing model-picker pattern**: `web/brandmind_web/components/model_picker.py`
- **Existing state idioms**: `web/brandmind_web/state.py` (`initialize_app` lines 355-394, `_apply_metadata` lines 1280-1305)
- **Existing api-client idioms**: `web/brandmind_web/api_client.py` (`list_main_agent_models` lines 109-131, `update_session` lines 183-204)
- **Reflex Skill (frontend tone)**: `.claude/skills/frontend-design`
- **UI/UX Skill**: `ui-ux-pro-max:ui-ux-pro-max`

------------------------------------------------------------------------

## 🤖 Agent Protocol

Confirmed: applying Rules 1-5 from `tasks/task_template.md`. Production-grade docstrings (Rule 4), affirmative phrasing for any user-facing copy, prompt strings exempt from 100-char rule (none here — no LLM prompt strings touched). `awk 'length > 100'` audit on every changed file before commit.

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Codex landed a backend profile settings contract on 2026-05-21 — `GET / PUT /api/v1/brand-strategy/user-profile/settings` plus `UserProfileSettings`, `UserProfileSettingsOptions`, and `read_user_profile_markdown()`. The contract is uncommitted on the user's working tree per shared wiki notes; this web slice consumes it as-is and the user has confirmed the wire shape is stable.
- The web UI currently has no way for the user to set personalization priors (job domain, role, experience, brand-strategy familiarity, mentoring style, stakeholder context). Junior users start every chat from a cold context, so the agent's first turns burn capacity on intake-style questions that a one-time onboarding would have answered.
- A `BRANDMIND_HOME/user/profile.md` file is rendered server-side from these settings; the proactive-context middleware injects it into the agent's context. Without a UI entry-point, the file is invisible to web users.

### Mục tiêu

Add a Settings entry point to the sidebar that opens a ChatGPT-style modal dialog. The dialog hosts a "Personalization" section that lets the user view and edit the six structured profile fields. On a brand-new install (`onboarding_completed=False`), the same form auto-launches as a lightweight first-run onboarding panel — saveable or skippable — so the user can seed personalization before sending the first chat without being blocked from chatting if they prefer to skip.

### Success Metrics / Acceptance Criteria

- **Functional**: First-run user on a fresh `BRANDMIND_HOME/user/` directory sees the onboarding modal once; saving fills `profile_settings.json` + the managed block in `profile.md`. Subsequent loads do NOT auto-open the modal.
- **Functional**: Sidebar Settings button opens the dialog on any subsequent load; saving updates the same files and the in-memory state.
- **Functional**: All six field option lists are sourced from `options` in the backend response — no hard-coded labels on the web side.
- **Functional**: Skip on onboarding saves defaults with `onboarding_completed=true` so it does not reopen; user can change them later via Settings.
- **Non-functional**: `make typecheck` green; `awk 'length > 100'` clean on all changed files (including the new test file); new units tests pass under `uv run pytest tests/unit/test_brandmind_web_client.py`.
- **UX**: Modal matches the existing dark-glass aesthetic — teal accent, no new color tokens introduced. Dialog dismissible via Cancel button, Esc key, and click-outside (handled by `rx.dialog.root` semantics).

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Two-column dialog hosted at page root, fed by backend options**: A new `settings_dialog.py` component renders a Radix `rx.dialog.root` with a left navigation rail (currently one entry — "Personalization" — with the visual seam ready for a future "General" entry) and a right content panel. The Personalization form is a shared sub-component that is also wrapped by an `onboarding_dialog.py` modal which auto-opens on first run. Both dialogs are mounted once at the top of `index()`, visibility driven by `BrandMindState.settings_dialog_open` and `BrandMindState.onboarding_open`. The Settings sidebar entry sits in a new sidebar footer slot that is sticky to the bottom of the rail (visible in both expanded and collapsed states).

### Stack công nghệ

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| `rx.dialog.root` | Modal container with overlay + escape/click-outside dismissal | Same component the existing rename/delete dialogs use, no new dependency |
| `rx.select.root` | Field control for each of the 6 profile fields | Native Radix select, accepts `items=` driven by the backend options list, supports `value` + `on_change` |
| `httpx.AsyncClient` | GET + PUT to the backend endpoints | Already vendored by `api_client.py`; matches the existing patterns |
| `pydantic.BaseModel` | Wire-mirror models for `UserProfileSettings` + options | Matches `models.py` conventions for backend-mirror clients |

### Architecture Overview

```
brandmind_web.py
└── index()
    ├── settings_dialog()  ──┐  (mounted once at page root)
    ├── onboarding_dialog()──┤
    ├── chat_action_dialogs()│  (existing)
    ├── header()             │
    └── hstack               │
        ├── sidebar          │
        │   ├── chats        │
        │   ├── divider      │
        │   ├── phases       │
        │   └── settings_footer ──── triggers BrandMindState.open_settings ─┐
        │                                                                  │
        └── chat_pane                                                      │
                                                                           ▼
                                                                   open_settings() →
                                                                   settings_dialog open=True

BrandMindState.initialize_app() ─► fetch settings + options ─► if onboarding_completed=False ─► onboarding_open=True
```

### Issues & Solutions

1. **Auto-opening onboarding once + only once** → `initialize_app` flips `onboarding_open` to true only when `profile_settings.onboarding_completed` is false AND the local flag `onboarding_has_auto_opened` is false; once opened (or skipped) the flag persists in `rx.LocalStorage` so the user is not nagged on refresh even before they hit save.
2. **Skip semantics** → Skip saves the current draft (or defaults if untouched) with `onboarding_completed=true`. The user can still tune fields later via Settings.
3. **Form-state isolation between Settings and Onboarding** → A single `settings_draft` dict holds the in-flight edits; both dialogs read/write the same draft. When either dialog is closed without save, the draft is reset to the saved snapshot so a half-edited dialog does not leak into the other.
4. **Backend reachability degraded** → On `httpx.HTTPError` during fetch or save, surface a short inline error in the dialog footer ("Could not load / save settings — backend unreachable"). Skip the auto-open if the fetch fails so the user is not stuck in a broken modal.
5. **Field option `description` rendering** → Render the description as the helper text below each field's label (matches Gemini Chat's pattern). The currently selected option's description floats under the select control to reinforce what the choice means.

------------------------------------------------------------------------

## 🔬 Pre-Implementation Research

### Codebase Audit

- **Files read**:
  - `src/server/api/brand_strategy.py` (endpoints + response model)
  - `src/shared/src/shared/workspace/profile_settings.py` (enums, defaults, options labels)
  - `web/brandmind_web/api_client.py` (httpx idiom + base URL helper)
  - `web/brandmind_web/state.py` (initialize_app, dialog event patterns from rename/delete flow)
  - `web/brandmind_web/components/sidebar.py` (chat_action_dialogs pattern, footer placement)
  - `web/brandmind_web/components/model_picker.py` (Radix `data-highlighted` hover override)
  - `web/brandmind_web/components/tokens.py` (existing color/spacing tokens — no new tokens required)
  - `web/brandmind_web/brandmind_web.py` (page root mount sequence)
- **Relevant patterns found**:
  - Existing dialogs mount at `index()` root via `chat_action_dialogs()` and read open-state from `BrandMindState` flags. New dialogs will mirror this.
  - State events use `@rx.event` for sync handlers, `@rx.event(background=True)` for async/IO handlers that wrap mutations in `async with self`.
  - Pydantic mirror models live in `web/brandmind_web/models.py` and never import server-side schemas.
  - Sidebar uses `rx.cond(BrandMindState.sidebar_is_collapsed, …)` everywhere — the Settings footer must do the same.
  - Tests for wire models live in `tests/unit/test_brandmind_web_client.py`.
- **Potential conflicts**: None. The backend endpoint paths are not yet consumed anywhere on the web side; no naming collisions with existing state vars (verified via `grep -n "profile_settings\|settings_dialog\|onboarding" web/brandmind_web/`).

### External Library / API Research

- **Library**: Reflex 0.9.2.post1
- **Documentation source**: Local install of `reflex`, `reflex_components_core`
- **Key findings**:
  - `rx.select.root(items=[(value, label)…], value=…, on_change=…)` returns a Radix Themes Select. Items take `(value, label)` tuples — descriptions cannot be embedded inside the select; surface them in helper text below the select instead.
  - `rx.dialog.root(content, open=..., on_open_change=...)` supports controlled mode the same way `chat_action_dialogs` already uses.
  - `rx.LocalStorage(default, name=...)` provides client-side persistence for the "already auto-opened" flag.
- **Interface confirmed**: backend wire shape from `UserProfileSettingsResponse` matches the user-supplied spec verbatim.

### Unknown / Risks Identified

- ✅ Resolved: confirmed `rx.select.root` exists in this Reflex version and accepts `items=` per existing component usage in `model_picker.py` (which uses `rx.menu` instead, but `rx.select` is available — verified via `uv run python -c "import reflex as rx; print(rx.select.root)"`).
- ✅ Resolved: `rx.LocalStorage` supports `default` parameter for first-load value (confirmed via `sidebar_collapsed` usage in state.py line 148).

### Research Status

- [x] All referenced documentation read
- [x] Existing codebase patterns understood
- [x] External dependencies verified
- [x] No unresolved ambiguities remain → Ready to implement

------------------------------------------------------------------------

## 🔄 Implementation Plan

### Phase 1: Wire-mirror models + API client (≈ 30 min)

1. **Add Pydantic mirror models** (`web/brandmind_web/models.py`)
   - `UserProfileOption` — value/label/description
   - `UserProfileSettings` — six enum-as-string fields + flags
   - `UserProfileSettingsOptions` — option lists keyed by field
   - `UserProfileSettingsPayload` — response envelope (settings + options + profile_markdown)
   - *Checkpoint*: `uv run python -c "from web.brandmind_web.models import UserProfileSettings; print(UserProfileSettings())"`

2. **Add API client helpers** (`web/brandmind_web/api_client.py`)
   - `get_user_profile_settings(api_base_url)` — GET
   - `save_user_profile_settings(api_base_url, settings)` — PUT
   - *Checkpoint*: ruff format + ruff check passes.

### Phase 2: State + business logic (≈ 45 min)

1. **Add state vars** (`web/brandmind_web/state.py`)
   - `profile_settings: UserProfileSettings` (saved snapshot)
   - `profile_settings_options: UserProfileSettingsOptions | None`
   - `profile_settings_draft: UserProfileSettings` (in-flight edits)
   - `settings_dialog_open: bool`
   - `settings_dialog_section: str` (currently always "personalization")
   - `onboarding_open: bool`
   - `onboarding_has_auto_opened: str` (rx.LocalStorage flag)
   - `profile_settings_saving: bool`
   - `profile_settings_error: str`

2. **Add events**
   - `open_settings`, `close_settings`
   - `update_setting_field(field, value)` — typed mutator
   - `save_profile_settings` — async PUT, then close dialog on success
   - `skip_onboarding` — save defaults with `onboarding_completed=true`
   - `_fetch_profile_settings` — internal helper used by `initialize_app`

3. **Hook into `initialize_app`**
   - Fetch profile settings + options after sessions + models. Failure is non-fatal.
   - If `onboarding_has_auto_opened == ""` AND `profile_settings.onboarding_completed == False`, set `onboarding_open=True` and flip the auto-opened flag.

   *Checkpoint*: `make typecheck` green.

### Phase 3: UI components (≈ 1.5 h)

1. **Shared form sub-component** `_personalization_form()` (inside `settings_dialog.py`)
   - Six `rx.select` controls + helper text below each
   - Reads draft, writes via `update_setting_field`

2. **`settings_dialog.py`** — two-column modal
   - Left rail: `rx.vstack` with currently-active "Personalization" item
   - Right content: section heading + the shared form + footer (Cancel + Save)

3. **`onboarding_dialog.py`** — single-panel modal
   - Welcome header + brief explainer
   - Shared form
   - Footer: Skip + Save

4. **Sidebar Settings footer** — new `_settings_footer()` row in `sidebar.py`
   - Above the page-bottom hairline, sticky to the rail bottom via `margin_top: auto`
   - Gear icon + "Settings" label (expanded); gear-only (collapsed)
   - `on_click=BrandMindState.open_settings`

5. **Page mount** — `brandmind_web.py`
   - Add `settings_dialog()` + `onboarding_dialog()` calls right under `chat_action_dialogs()`

   *Checkpoint*: live Playwright smoke confirms entry button + dialog + form render.

### Phase 4: Tests + commit (≈ 30 min)

1. **Unit tests** (`tests/unit/test_brandmind_web_client.py`)
   - `UserProfileSettings()` defaults match the spec
   - `UserProfileSettingsPayload.model_validate` round-trips a representative response
   - `UserProfileOption` accepts empty description

2. **Pre-commit**: `awk 'length > 100'` on all changed files, `make typecheck`, ruff format, ruff check
3. **Commit**: single concern, scoped to web settings & onboarding

### Rollback Plan

`git revert <commit>` — the change is additive across web-side files only. New components are not referenced from anywhere except `brandmind_web.py` and `sidebar.py`, so the revert is clean.

------------------------------------------------------------------------

## 📋 Implementation Detail

> Full code bodies below — exactly what will land in each file. Once approved, each block applies via Edit/Write tool with no drift.

### Component A: Wire-mirror Pydantic models

> Status: ⏳ Pending

#### Requirement 1 — Add profile-settings models in `web/brandmind_web/models.py`

- **File**: `web/brandmind_web/models.py` `[MODIFY]`
- **Change kind**: Append four new Pydantic classes at end of file

- **Acceptance Criteria**:
  - [ ] `UserProfileSettings()` populates the same defaults as the backend spec (job_domain="unknown", mentoring_style="balanced", etc.)
  - [ ] `UserProfileSettingsPayload.model_validate(payload)` round-trips a representative response without raising
  - [ ] No imports from `src/server/*` or `src/shared/*` (web stays decoupled)

- **Full code to write** (appended after the last existing class, after the `DocxHtmlResponse` definition):

```python
class UserProfileOption(BaseModel):
    """One option for a profile-settings dropdown.

    Mirrors :class:`shared.workspace.profile_settings.UserProfileOption`
    so the settings + onboarding forms can render dropdowns without
    duplicating the canonical option list on the client.
    """

    value: str
    label: str
    description: str = ""


class UserProfileSettings(BaseModel):
    """Onboarding personalization settings synced with the backend.

    Mirrors :class:`shared.workspace.profile_settings.UserProfileSettings`.
    Each field carries the public enum value (e.g. ``"fb"``, ``"comfortable"``)
    rather than the enum itself so the wire shape stays string-only.
    Defaults match the backend's safe fallback (``BALANCED`` mentoring
    density + ``UNKNOWN`` for the rest) so the dialog can render before
    the backend round-trip completes.
    """

    job_domain: str = "unknown"
    role: str = "unknown"
    experience_years: str = "unknown"
    brand_strategy_familiarity: str = "unknown"
    mentoring_style: str = "balanced"
    stakeholder_context: str = "unknown"
    onboarding_completed: bool = False
    updated_at: str | None = None


class UserProfileSettingsOptions(BaseModel):
    """Option lists for the six profile-settings dropdowns.

    Mirrors :class:`shared.workspace.profile_settings.UserProfileSettingsOptions`
    so the dialog projects the backend-owned label and description for
    each option without re-stating the copy on the client side.
    """

    job_domain: list[UserProfileOption] = Field(default_factory=list)
    role: list[UserProfileOption] = Field(default_factory=list)
    experience_years: list[UserProfileOption] = Field(default_factory=list)
    brand_strategy_familiarity: list[UserProfileOption] = Field(default_factory=list)
    mentoring_style: list[UserProfileOption] = Field(default_factory=list)
    stakeholder_context: list[UserProfileOption] = Field(default_factory=list)


class UserProfileSettingsPayload(BaseModel):
    """Response envelope for the user-profile settings endpoints.

    Both ``GET`` and ``PUT /api/v1/brand-strategy/user-profile/settings``
    return this shape. ``profile_markdown`` is the prompt-facing managed
    block the agent will read and is shown in the dialog as a read-only
    preview for users who want to verify what context is being persisted.
    """

    settings: UserProfileSettings = Field(default_factory=UserProfileSettings)
    options: UserProfileSettingsOptions = Field(default_factory=UserProfileSettingsOptions)
    profile_markdown: str = ""
```

### Component B: API client helpers

> Status: ⏳ Pending

#### Requirement 1 — `get_user_profile_settings` + `save_user_profile_settings` in `web/brandmind_web/api_client.py`

- **File**: `web/brandmind_web/api_client.py` `[MODIFY]`
- **Change kind**: Add two async helpers + extend the import block

- **Acceptance Criteria**:
  - [ ] GET helper returns `UserProfileSettingsPayload` validated from JSON
  - [ ] PUT helper accepts a `UserProfileSettings` instance and forwards `model_dump()` as JSON body
  - [ ] Both raise `httpx.HTTPError` on transport / 4xx / 5xx — caller handles degradation

- **Locate the import line at the top** (≥3-line context):

```python
from .models import (
    ArtifactRef,
    DocxHtmlResponse,
    MainAgentModelOption,
    SessionInfo,
    SessionMessages,
)
```

- **Replace with**:

```python
from .models import (
    ArtifactRef,
    DocxHtmlResponse,
    MainAgentModelOption,
    SessionInfo,
    SessionMessages,
    UserProfileSettings,
    UserProfileSettingsPayload,
)
```

- **Append the two helpers at end of file** (after the existing `delete_session` function — they are top-level module functions like every other helper):

```python
async def get_user_profile_settings(api_base_url: str) -> UserProfileSettingsPayload:
    """Fetch saved onboarding settings + option metadata from the backend.

    Returns the current ``UserProfileSettings`` plus the option lists the
    dialog needs to render each dropdown. The web UI never invents option
    labels; everything user-facing comes from this payload so a backend
    label change does not require a web release.

    Args:
        api_base_url (str): Backend base URL.

    Returns:
        payload (UserProfileSettingsPayload): Settings, option lists, and
        the prompt-facing managed-block markdown.

    Raises:
        httpx.HTTPError: On network failure or non-2xx response.
    """
    url = f"{api_base_url}/api/v1/brand-strategy/user-profile/settings"
    async with httpx.AsyncClient(timeout=_HEALTH_TIMEOUT_SECONDS) as client:
        response = await client.get(url)
        response.raise_for_status()
    return UserProfileSettingsPayload.model_validate(response.json())


async def save_user_profile_settings(
    api_base_url: str,
    settings: UserProfileSettings,
) -> UserProfileSettingsPayload:
    """Persist onboarding settings and return the refreshed payload.

    Forwards the structured ``UserProfileSettings`` to the backend, which
    refreshes ``profile.md`` and returns the updated settings + the
    re-rendered managed block. The web UI swaps its local snapshot for
    the server response so any backend-side normalisation (timestamps,
    canonical defaults) is reflected immediately.

    Args:
        api_base_url (str): Backend base URL.
        settings (UserProfileSettings): The values to persist.

    Returns:
        payload (UserProfileSettingsPayload): Server-confirmed settings,
        option lists, and refreshed profile markdown.

    Raises:
        httpx.HTTPError: On network failure or non-2xx response.
    """
    url = f"{api_base_url}/api/v1/brand-strategy/user-profile/settings"
    async with httpx.AsyncClient(timeout=_CREATE_TIMEOUT_SECONDS) as client:
        response = await client.put(url, json=settings.model_dump())
        response.raise_for_status()
    return UserProfileSettingsPayload.model_validate(response.json())
```

### Component C: State surface

> Status: ⏳ Pending

#### Requirement 1 — Add state vars + events in `web/brandmind_web/state.py`

- **File**: `web/brandmind_web/state.py` `[MODIFY]`
- **Change kind**: Extend imports, add state fields, add events, hook into `initialize_app`

- **Acceptance Criteria**:
  - [ ] `open_settings` flips `settings_dialog_open=True` and seeds `profile_settings_draft` from the latest saved snapshot
  - [ ] `update_setting_field("job_domain", "fb")` mutates the draft, not the saved snapshot
  - [ ] `save_profile_settings` calls the PUT helper, applies the response, closes both dialogs, and clears any pending error
  - [ ] `skip_onboarding` sets `onboarding_completed=true` on the draft and persists, regardless of other field values
  - [ ] First page load with `onboarding_completed=False` AND empty `onboarding_has_auto_opened` flag opens the onboarding modal exactly once

- **Edit 1 — extend the `.api_client` import**:

  Locate (≥3 lines context):
  ```python
  from .api_client import (
      create_brand_strategy_session,
      delete_session,
      generate_session_title,
      get_session_messages,
      list_brand_strategy_sessions,
      list_main_agent_models,
      update_session,
  )
  ```

  Replace with:
  ```python
  from .api_client import (
      create_brand_strategy_session,
      delete_session,
      generate_session_title,
      get_session_messages,
      get_user_profile_settings,
      list_brand_strategy_sessions,
      list_main_agent_models,
      save_user_profile_settings,
      update_session,
  )
  ```

- **Edit 2 — extend the `.models` import**:

  Locate:
  ```python
  from .models import (
      ArtifactRef,
      BrandStrategyMetadata,
      ChatMessage,
      MainAgentModelOption,
      ...
  )
  ```

  Add at the appropriate alphabetical position:
  ```python
      UserProfileSettings,
      UserProfileSettingsOptions,
  ```

- **Edit 3 — add state fields below existing `delete_workspace_too: bool = False` block**:

  Locate (≥3 lines context):
  ```python
      rename_target: str = ""
      rename_draft: str = ""
      delete_target: str = ""
      delete_workspace_too: bool = False

      artifacts: list[ArtifactRef] = []
  ```

  Replace with:
  ```python
      rename_target: str = ""
      rename_draft: str = ""
      delete_target: str = ""
      delete_workspace_too: bool = False

      profile_settings: UserProfileSettings = UserProfileSettings()
      profile_settings_options: UserProfileSettingsOptions = UserProfileSettingsOptions()
      profile_settings_draft: UserProfileSettings = UserProfileSettings()
      profile_settings_saving: bool = False
      profile_settings_error: str = ""
      settings_dialog_open: bool = False
      settings_dialog_section: str = "personalization"
      onboarding_open: bool = False
      onboarding_has_auto_opened: str = rx.LocalStorage(
          default="",
          name="bm.web.onboarding.auto_opened",
      )

      artifacts: list[ArtifactRef] = []
  ```

- **Edit 4 — extend `initialize_app` to fetch settings + auto-open onboarding**:

  Locate the trailing `async with self:` block of `initialize_app`:
  ```python
          async with self:
              self.sessions = self._filter_chats(sessions)
              self.available_models = options
              if not self.selected_model_id:
                  self.selected_model_id = default_model_id
              self.is_connected = True
              self.error_message = ""
  ```

  Replace with:
  ```python
          try:
              profile_payload = await get_user_profile_settings(api_url)
          except httpx.HTTPError as exc:
              logger.warning(f"BrandMind web: profile settings fetch failed: {exc}")
              profile_payload = None
          async with self:
              self.sessions = self._filter_chats(sessions)
              self.available_models = options
              if not self.selected_model_id:
                  self.selected_model_id = default_model_id
              if profile_payload is not None:
                  self.profile_settings = profile_payload.settings
                  self.profile_settings_options = profile_payload.options
                  self.profile_settings_draft = profile_payload.settings.model_copy()
                  if (
                      not profile_payload.settings.onboarding_completed
                      and not self.onboarding_has_auto_opened
                  ):
                      self.onboarding_open = True
                      self.onboarding_has_auto_opened = "1"
              self.is_connected = True
              self.error_message = ""
  ```

- **Edit 5 — add settings event handlers near the rename/delete dialog handlers** (insert directly after the `confirm_delete` event handler block):

  ```python
      @rx.event
      def open_settings(self) -> None:
          """Open the Settings dialog seeded with the saved snapshot.

          Clones the saved settings into the draft so an in-progress edit
          can be cancelled without mutating the persisted state.
          """
          self.profile_settings_draft = self.profile_settings.model_copy()
          self.profile_settings_error = ""
          self.settings_dialog_open = True

      @rx.event
      def close_settings(self) -> None:
          """Dismiss the Settings dialog and discard any unsaved edits."""
          self.settings_dialog_open = False
          self.profile_settings_draft = self.profile_settings.model_copy()
          self.profile_settings_error = ""

      @rx.event
      def close_onboarding(self) -> None:
          """Dismiss the onboarding modal without saving.

          The local ``onboarding_has_auto_opened`` flag stays set so the
          modal does not auto-reappear; the user can still revisit the
          form via Settings.
          """
          self.onboarding_open = False
          self.profile_settings_draft = self.profile_settings.model_copy()
          self.profile_settings_error = ""

      @rx.event
      def update_setting_field(self, field: str, value: str) -> None:
          """Patch one field on the in-flight settings draft.

          The dialog dropdowns call this on every change so the draft
          accumulates edits without touching the saved snapshot until the
          user explicitly saves.
          """
          allowed = {
              "job_domain",
              "role",
              "experience_years",
              "brand_strategy_familiarity",
              "mentoring_style",
              "stakeholder_context",
          }
          if field not in allowed:
              return
          self.profile_settings_draft = self.profile_settings_draft.model_copy(
              update={field: value}
          )

      @rx.event(background=True)
      async def save_profile_settings(self) -> None:
          """Persist the draft, replace the saved snapshot, and close dialogs.

          ``onboarding_completed`` is forced to true on save so the user
          does not see the first-run modal again after explicitly setting
          their preferences. On HTTP failure the draft is preserved and an
          inline error message is surfaced.
          """
          async with self:
              if self.profile_settings_saving:
                  return
              self.profile_settings_saving = True
              self.profile_settings_error = ""
              payload = self.profile_settings_draft.model_copy(
                  update={"onboarding_completed": True}
              )
          api_url = _api_base_url()
          try:
              result = await save_user_profile_settings(api_url, payload)
          except httpx.HTTPError as exc:
              logger.warning(f"BrandMind web: profile settings save failed: {exc}")
              async with self:
                  self.profile_settings_saving = False
                  self.profile_settings_error = (
                      "Could not save — backend unreachable. Try again in a moment."
                  )
              return
          async with self:
              self.profile_settings = result.settings
              self.profile_settings_options = result.options
              self.profile_settings_draft = result.settings.model_copy()
              self.profile_settings_saving = False
              self.settings_dialog_open = False
              self.onboarding_open = False
              self.onboarding_has_auto_opened = "1"

      @rx.event(background=True)
      async def skip_onboarding(self) -> None:
          """Close the onboarding modal and persist defaults as accepted.

          Saves the current draft (or pristine defaults if untouched) with
          ``onboarding_completed=true`` so future loads no longer auto-open
          the modal. The user can still revisit and refine values later
          via the Settings entry in the sidebar.
          """
          async with self:
              if self.profile_settings_saving:
                  return
              self.profile_settings_saving = True
              self.profile_settings_error = ""
              payload = self.profile_settings_draft.model_copy(
                  update={"onboarding_completed": True}
              )
          api_url = _api_base_url()
          try:
              result = await save_user_profile_settings(api_url, payload)
          except httpx.HTTPError as exc:
              logger.warning(f"BrandMind web: skip onboarding save failed: {exc}")
              async with self:
                  self.profile_settings_saving = False
                  self.onboarding_open = False
                  self.onboarding_has_auto_opened = "1"
                  self.profile_settings_error = ""
              return
          async with self:
              self.profile_settings = result.settings
              self.profile_settings_options = result.options
              self.profile_settings_draft = result.settings.model_copy()
              self.profile_settings_saving = False
              self.onboarding_open = False
              self.onboarding_has_auto_opened = "1"
  ```

### Component D: Settings modal dialog

> Status: ⏳ Pending

#### Requirement 1 — New file `web/brandmind_web/components/settings_dialog.py`

- **File**: `web/brandmind_web/components/settings_dialog.py` `[NEW]`
- **Change kind**: Full new module

- **Acceptance Criteria**:
  - [ ] Two-column dialog: left nav (Personalization active), right content
  - [ ] Six dropdowns driven by `profile_settings_options` — no hard-coded option labels
  - [ ] Footer with Cancel + Save; Save shows "Saving…" label while in flight
  - [ ] Inline error visible when `profile_settings_error` is non-empty
  - [ ] All lines ≤ 100 chars

- **Full new file body**:

```python
"""Settings dialog hosting BrandMind's personalization preferences.

Renders a ChatGPT-style modal with a left navigation rail and a right
content panel. Currently surfaces a single "Personalization" section
that lets the user view and edit the six structured profile fields the
backend persists under ``BRANDMIND_HOME/user/`` and renders into the
managed block of ``profile.md``. The nav rail is built as a list so
adding a future "General" section is a one-line change.
"""

from __future__ import annotations

import reflex as rx

from ..models import UserProfileOption
from ..state import BrandMindState
from . import tokens


def _nav_item(label: str, section: str) -> rx.Component:
    """Render one entry in the dialog's left navigation rail."""
    is_active = BrandMindState.settings_dialog_section == section
    return rx.button(
        rx.text(
            label,
            style={
                "color": rx.cond(is_active, tokens.TEXT_PRIMARY, tokens.TEXT_SECONDARY),
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "font_weight": rx.cond(is_active, "600", "500"),
                "letter_spacing": "-0.01em",
            },
        ),
        on_click=BrandMindState.set_settings_dialog_section(section),
        variant="ghost",
        style={
            "width": "100%",
            "justify_content": "flex-start",
            "padding": "8px 12px",
            "border_radius": tokens.RADIUS_SM,
            "cursor": "pointer",
            "background_color": rx.cond(
                is_active,
                "rgba(95, 179, 168, 0.12)",
                "transparent",
            ),
            "_hover": {
                "background_color": rx.cond(
                    is_active,
                    "rgba(95, 179, 168, 0.16)",
                    "rgba(255, 255, 255, 0.04)",
                ),
            },
        },
    )


def _select_items(options: rx.Var[list[UserProfileOption]]) -> rx.Var:
    """Project an option list into ``rx.select`` ``items`` tuples."""
    return options.foreach(lambda option: (option.value, option.label))


def _field_helper_text(
    options: rx.Var[list[UserProfileOption]],
    selected_value: rx.Var[str],
) -> rx.Component:
    """Render the description of the currently-selected option.

    Lets the dropdown stay terse (label only) while still surfacing the
    backend-owned trade-off blurb the user picks against; mirrors the
    pattern Gemini Chat uses on personalization controls.
    """
    description = options.foreach(
        lambda option: rx.cond(option.value == selected_value, option.description, "")
    ).join("")
    return rx.cond(
        description != "",
        rx.text(
            description,
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
                "line_height": "1.5",
                "margin_top": "6px",
            },
        ),
        rx.fragment(),
    )


def _personalization_field(
    label: str,
    field: str,
    options: rx.Var[list[UserProfileOption]],
    selected_value: rx.Var[str],
) -> rx.Component:
    """One labelled dropdown for a single profile field."""
    return rx.vstack(
        rx.text(
            label,
            style={
                "color": tokens.TEXT_PRIMARY,
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "font_weight": "500",
                "letter_spacing": "-0.01em",
            },
        ),
        rx.select.root(
            rx.select.trigger(
                placeholder="Choose…",
                style={
                    "background_color": tokens.BG_SURFACE_2,
                    "border": f"1px solid {tokens.GLASS_BORDER}",
                    "color": tokens.TEXT_PRIMARY,
                    "width": "100%",
                },
            ),
            rx.select.content(
                rx.foreach(
                    options,
                    lambda option: rx.select.item(option.label, value=option.value),
                ),
                style={
                    "background_color": tokens.GLASS_BG_ELEVATED,
                    "border": f"1px solid {tokens.GLASS_BORDER}",
                },
            ),
            value=selected_value,
            on_change=lambda value: BrandMindState.update_setting_field(field, value),
            size="2",
        ),
        _field_helper_text(options, selected_value),
        spacing="1",
        align="stretch",
        width="100%",
    )


def personalization_form() -> rx.Component:
    """Render the six profile-field dropdowns shared by Settings + Onboarding."""
    draft = BrandMindState.profile_settings_draft
    options = BrandMindState.profile_settings_options
    return rx.vstack(
        _personalization_field(
            "Job domain",
            "job_domain",
            options.job_domain,
            draft.job_domain,
        ),
        _personalization_field(
            "Role",
            "role",
            options.role,
            draft.role,
        ),
        _personalization_field(
            "Experience",
            "experience_years",
            options.experience_years,
            draft.experience_years,
        ),
        _personalization_field(
            "Brand-strategy familiarity",
            "brand_strategy_familiarity",
            options.brand_strategy_familiarity,
            draft.brand_strategy_familiarity,
        ),
        _personalization_field(
            "Preferred mentoring style",
            "mentoring_style",
            options.mentoring_style,
            draft.mentoring_style,
        ),
        _personalization_field(
            "Primary stakeholder",
            "stakeholder_context",
            options.stakeholder_context,
            draft.stakeholder_context,
        ),
        spacing="4",
        align="stretch",
        width="100%",
    )


def _personalization_panel() -> rx.Component:
    """Right-side content panel for the Personalization section."""
    return rx.vstack(
        rx.text(
            "Personalization",
            style={
                "color": tokens.TEXT_PRIMARY,
                "font_family": tokens.FONT_DISPLAY,
                "font_size": "20px",
                "font_weight": "500",
                "letter_spacing": "-0.01em",
            },
        ),
        rx.text(
            "Set personalization priors so BrandMind can calibrate its "
            "mentoring density and decision framing from the first turn.",
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "line_height": "1.55",
                "margin_top": "4px",
                "margin_bottom": "20px",
            },
        ),
        personalization_form(),
        spacing="0",
        align="stretch",
        width="100%",
    )


def _dialog_footer() -> rx.Component:
    """Cancel + Save row with inline error when present."""
    return rx.vstack(
        rx.cond(
            BrandMindState.profile_settings_error != "",
            rx.text(
                BrandMindState.profile_settings_error,
                style={
                    "color": "#f3a59c",
                    "font_family": tokens.FONT_SANS,
                    "font_size": "12px",
                    "line_height": "1.5",
                },
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.button(
                "Cancel",
                on_click=BrandMindState.close_settings,
                variant="soft",
                color_scheme="gray",
            ),
            rx.button(
                rx.cond(
                    BrandMindState.profile_settings_saving,
                    "Saving…",
                    "Save",
                ),
                on_click=BrandMindState.save_profile_settings,
                disabled=BrandMindState.profile_settings_saving,
                style={
                    "background_color": tokens.ACCENT_TEAL_SOLID,
                    "color": "#003732",
                },
            ),
            spacing="3",
            justify="end",
        ),
        spacing="2",
        align="stretch",
        margin_top="20px",
        width="100%",
    )


def settings_dialog() -> rx.Component:
    """Page-level Settings dialog driven by ``BrandMindState.settings_dialog_open``."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "Settings",
                        style={
                            "color": tokens.TEXT_MUTED,
                            "font_family": tokens.FONT_SANS,
                            "font_size": "11px",
                            "font_weight": "500",
                            "letter_spacing": "0.06em",
                            "text_transform": "uppercase",
                            "padding": "0 12px 8px 12px",
                        },
                    ),
                    _nav_item("Personalization", "personalization"),
                    spacing="1",
                    align="stretch",
                    width="200px",
                    padding_top="6px",
                    style={
                        "border_right": f"1px solid {tokens.GLASS_BORDER}",
                        "min_height": "440px",
                    },
                ),
                rx.box(
                    _personalization_panel(),
                    _dialog_footer(),
                    style={
                        "flex": "1",
                        "padding": "8px 24px 0 24px",
                    },
                ),
                spacing="0",
                align="stretch",
                width="100%",
            ),
            style={
                "background_color": tokens.BG_SURFACE_1,
                "border": f"1px solid {tokens.GLASS_BORDER}",
                "max_width": "780px",
                "width": "92vw",
                "padding": "20px",
            },
        ),
        open=BrandMindState.settings_dialog_open,
        on_open_change=BrandMindState.close_settings,
    )
```

> **Note**: introduces a new state event `set_settings_dialog_section(section: str)`. Add it alongside the other Settings events in Component C as:
> ```python
>     @rx.event
>     def set_settings_dialog_section(self, section: str) -> None:
>         """Switch the visible content panel inside the Settings dialog."""
>         self.settings_dialog_section = section
> ```

### Component E: First-run onboarding dialog

> Status: ⏳ Pending

#### Requirement 1 — New file `web/brandmind_web/components/onboarding_dialog.py`

- **File**: `web/brandmind_web/components/onboarding_dialog.py` `[NEW]`
- **Change kind**: Full new module — re-uses the shared `personalization_form()` from Component D

- **Acceptance Criteria**:
  - [ ] Auto-opens when state flag flips to true (driven by `initialize_app`)
  - [ ] Welcome header + brief explainer
  - [ ] Same six dropdowns as the Settings dialog
  - [ ] Footer: Skip + Save buttons; both disable while saving
  - [ ] Inline error visible when `profile_settings_error` is non-empty

- **Full new file body**:

```python
"""First-run onboarding modal that primes BrandMind's personalization.

Auto-opens once on a fresh ``BRANDMIND_HOME/user/`` when the backend
reports ``onboarding_completed=False``. The form shares its dropdowns
with the Settings dialog so a save here is identical to a save from
Settings; Skip persists ``onboarding_completed=True`` against the
current (possibly default) draft so the modal does not reappear after a
deliberate dismissal.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens
from .settings_dialog import personalization_form


def _header() -> rx.Component:
    """Welcome lockup at the top of the onboarding modal."""
    return rx.vstack(
        rx.text(
            "Welcome to BrandMind",
            style={
                "color": tokens.TEXT_PRIMARY,
                "font_family": tokens.FONT_DISPLAY,
                "font_size": "22px",
                "font_weight": "500",
                "letter_spacing": "-0.01em",
                "line_height": "1.2",
            },
        ),
        rx.text(
            "Tell BrandMind a little about how you work so the first chat "
            "starts at the right depth. You can update or skip this any "
            "time from Settings.",
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "line_height": "1.6",
                "margin_top": "4px",
            },
        ),
        spacing="0",
        align="stretch",
        margin_bottom="20px",
    )


def _footer() -> rx.Component:
    """Skip + Save row plus inline error when present."""
    return rx.vstack(
        rx.cond(
            BrandMindState.profile_settings_error != "",
            rx.text(
                BrandMindState.profile_settings_error,
                style={
                    "color": "#f3a59c",
                    "font_family": tokens.FONT_SANS,
                    "font_size": "12px",
                    "line_height": "1.5",
                },
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.button(
                "Skip for now",
                on_click=BrandMindState.skip_onboarding,
                disabled=BrandMindState.profile_settings_saving,
                variant="soft",
                color_scheme="gray",
            ),
            rx.button(
                rx.cond(
                    BrandMindState.profile_settings_saving,
                    "Saving…",
                    "Save and continue",
                ),
                on_click=BrandMindState.save_profile_settings,
                disabled=BrandMindState.profile_settings_saving,
                style={
                    "background_color": tokens.ACCENT_TEAL_SOLID,
                    "color": "#003732",
                },
            ),
            spacing="3",
            justify="end",
        ),
        spacing="2",
        align="stretch",
        margin_top="20px",
        width="100%",
    )


def onboarding_dialog() -> rx.Component:
    """Page-level first-run modal driven by ``BrandMindState.onboarding_open``."""
    return rx.dialog.root(
        rx.dialog.content(
            _header(),
            personalization_form(),
            _footer(),
            style={
                "background_color": tokens.BG_SURFACE_1,
                "border": f"1px solid {tokens.GLASS_BORDER}",
                "max_width": "560px",
                "width": "92vw",
                "padding": "24px",
            },
        ),
        open=BrandMindState.onboarding_open,
        on_open_change=BrandMindState.close_onboarding,
    )
```

### Component F: Sidebar Settings footer entry

> Status: ⏳ Pending

#### Requirement 1 — Add `_settings_footer()` row + thread it into the sidebar root in `web/brandmind_web/components/sidebar.py`

- **File**: `web/brandmind_web/components/sidebar.py` `[MODIFY]`
- **Change kind**: Add a new helper + extend `phase_progress_sidebar()` to render the footer pinned to the bottom

- **Acceptance Criteria**:
  - [ ] Footer visible in both expanded and collapsed states
  - [ ] Expanded: gear icon + "Settings" label, full-width clickable row
  - [ ] Collapsed: gear-only centered button
  - [ ] Sticky to the bottom of the rail via `margin_top: auto`
  - [ ] `on_click=BrandMindState.open_settings`

- **Edit 1 — append new helpers above `phase_progress_sidebar`**:

  Locate (≥3 lines context):
  ```python
  def _section_divider() -> rx.Component:
      """Hairline between the Chats and Phases sections."""
      return rx.box(
          style={
              "height": "1px",
              "background_color": tokens.GLASS_BORDER,
              "margin": "8px 16px",
          },
      )
  ```

  Add directly above this function:
  ```python
  def _settings_footer() -> rx.Component:
      """Sidebar bottom row that opens the Settings dialog.

      Pinned to the bottom of the rail via ``margin_top: auto`` on the
      enclosing vstack. In the collapsed rail the row reduces to a single
      gear-icon button so the affordance survives the 56-px width.
      """
      return rx.cond(
          BrandMindState.sidebar_is_collapsed,
          rx.center(
              rx.button(
                  rx.icon(tag="settings", size=18, color=tokens.TEXT_SECONDARY),
                  on_click=BrandMindState.open_settings,
                  variant="ghost",
                  aria_label="Open settings",
                  style={
                      "width": "32px",
                      "height": "32px",
                      "padding": "0",
                      "border_radius": tokens.RADIUS_PILL,
                      "cursor": "pointer",
                      "_hover": {
                          "background_color": "rgba(255, 255, 255, 0.04)",
                      },
                  },
              ),
              width="100%",
              padding="12px 0 16px 0",
          ),
          rx.box(
              rx.button(
                  rx.hstack(
                      rx.icon(tag="settings", size=16, color=tokens.TEXT_SECONDARY),
                      rx.text(
                          "Settings",
                          style={
                              "color": tokens.TEXT_SECONDARY,
                              "font_family": tokens.FONT_SANS,
                              "font_size": "13px",
                              "font_weight": "500",
                          },
                      ),
                      spacing="2",
                      align="center",
                  ),
                  on_click=BrandMindState.open_settings,
                  variant="ghost",
                  style={
                      "width": "100%",
                      "justify_content": "flex-start",
                      "padding": "10px 12px",
                      "border_radius": tokens.RADIUS_SM,
                      "cursor": "pointer",
                      "_hover": {
                          "background_color": "rgba(255, 255, 255, 0.04)",
                      },
                  },
              ),
              padding="8px 12px 16px 12px",
              width="100%",
          ),
      )
  ```

- **Edit 2 — wire the footer into `phase_progress_sidebar`**:

  Locate (≥3 lines context):
  ```python
  def phase_progress_sidebar() -> rx.Component:
      """Render the collapsible sidebar with both Chats and Phases sections."""
      return rx.vstack(
          _chats_section(),
          _section_divider(),
          _phases_section(),
          spacing="0",
          align="stretch",
          style={
  ```

  Replace with:
  ```python
  def phase_progress_sidebar() -> rx.Component:
      """Render the collapsible sidebar with chats, phases, and the Settings footer."""
      return rx.vstack(
          _chats_section(),
          _section_divider(),
          _phases_section(),
          rx.box(flex="1", width="100%"),
          _settings_footer(),
          spacing="0",
          align="stretch",
          style={
  ```

### Component G: Page-level dialog mount

> Status: ⏳ Pending

#### Requirement 1 — Mount the new dialogs at the top of `index()` in `brandmind_web.py`

- **File**: `web/brandmind_web/brandmind_web.py` `[MODIFY]`
- **Change kind**: Extend imports + add the two dialog calls

- **Acceptance Criteria**:
  - [ ] Dialogs render in the DOM regardless of which section of the app is active
  - [ ] Render order keeps overlays above main content (already implicit because both are page-root siblings)

- **Edit 1 — add imports**:

  Locate:
  ```python
  from .components.chat_pane import chat_pane
  from .components.degraded_banner import degraded_banner
  from .components.header import header
  from .components.sidebar import chat_action_dialogs, phase_progress_sidebar
  ```

  Replace with:
  ```python
  from .components.chat_pane import chat_pane
  from .components.degraded_banner import degraded_banner
  from .components.header import header
  from .components.onboarding_dialog import onboarding_dialog
  from .components.settings_dialog import settings_dialog
  from .components.sidebar import chat_action_dialogs, phase_progress_sidebar
  ```

- **Edit 2 — add the dialog mounts under the existing `chat_action_dialogs()` line**:

  Locate (≥3 lines context):
  ```python
      return rx.vstack(
          rx.html(f"<style>{_CURSOR_BLINK_KEYFRAMES}</style>"),
          chat_action_dialogs(),
          canvas_pane(),
          header(),
  ```

  Replace with:
  ```python
      return rx.vstack(
          rx.html(f"<style>{_CURSOR_BLINK_KEYFRAMES}</style>"),
          chat_action_dialogs(),
          settings_dialog(),
          onboarding_dialog(),
          canvas_pane(),
          header(),
  ```

### Component H: Unit tests for wire models + state helpers

> Status: ⏳ Pending

#### Requirement 1 — Append four tests to `tests/unit/test_brandmind_web_client.py`

- **File**: `tests/unit/test_brandmind_web_client.py` `[MODIFY]`
- **Change kind**: Extend the import list + add four `def test_…` functions at end of file

- **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/test_brandmind_web_client.py -q` passes including the new tests
  - [ ] No line exceeds 100 chars

- **Edit 1 — extend the model import at the top of the test file**:

  Locate the existing model-import block (the actual line layout will be confirmed when the file is read at apply time — current importer is `from web.brandmind_web.models import (...)` covering all existing mirror models). Add the four new model names alphabetically:

  ```
  UserProfileOption,
  UserProfileSettings,
  UserProfileSettingsOptions,
  UserProfileSettingsPayload,
  ```

- **Append at end of file**:

```python
def test_user_profile_settings_defaults_match_backend_safe_fallback() -> None:
    """Defaults mirror BrandMind's backend safe-fallback for an empty install."""
    settings = UserProfileSettings()

    assert settings.job_domain == "unknown"
    assert settings.role == "unknown"
    assert settings.experience_years == "unknown"
    assert settings.brand_strategy_familiarity == "unknown"
    assert settings.mentoring_style == "balanced"
    assert settings.stakeholder_context == "unknown"
    assert settings.onboarding_completed is False
    assert settings.updated_at is None


def test_user_profile_option_accepts_empty_description() -> None:
    """Options with no description still validate cleanly."""
    option = UserProfileOption(value="fb", label="F&B")

    assert option.value == "fb"
    assert option.label == "F&B"
    assert option.description == ""


def test_user_profile_settings_options_defaults_to_empty_lists() -> None:
    """Empty defaults let the dialog render before the backend round-trip."""
    options = UserProfileSettingsOptions()

    assert options.job_domain == []
    assert options.role == []
    assert options.experience_years == []
    assert options.brand_strategy_familiarity == []
    assert options.mentoring_style == []
    assert options.stakeholder_context == []


def test_user_profile_settings_payload_round_trips_representative_response() -> None:
    """A backend-shaped payload validates end-to-end without data loss."""
    raw = {
        "settings": {
            "job_domain": "fb",
            "role": "marketing_executive",
            "experience_years": "1_3",
            "brand_strategy_familiarity": "comfortable",
            "mentoring_style": "compact_first",
            "stakeholder_context": "boss",
            "onboarding_completed": True,
            "updated_at": "2026-05-21T00:00:00+00:00",
        },
        "options": {
            "job_domain": [
                {"value": "fb", "label": "F&B", "description": "Food and beverage."},
                {"value": "retail", "label": "Retail", "description": ""},
            ],
            "role": [],
            "experience_years": [],
            "brand_strategy_familiarity": [],
            "mentoring_style": [],
            "stakeholder_context": [],
        },
        "profile_markdown": "# User Profile\n\n<!-- managed -->\n",
    }

    payload = UserProfileSettingsPayload.model_validate(raw)

    assert payload.settings.job_domain == "fb"
    assert payload.settings.onboarding_completed is True
    assert payload.options.job_domain[0].label == "F&B"
    assert payload.options.job_domain[0].description == "Food and beverage."
    assert payload.profile_markdown.startswith("# User Profile")
```

------------------------------------------------------------------------

## 🧪 Test Execution Log

> Filled in during apply phase.

### Test 1: Web unit suite
- Steps: `uv run pytest tests/unit/test_brandmind_web_client.py -q`
- Expected: green including 4 new tests
- Status: ⏳ Pending

### Test 2: Static gates
- Steps: `make typecheck` + `awk 'length > 100' <each changed file>`
- Expected: all green
- Status: ⏳ Pending

### Test 3: Live UX smoke (Playwright)
- Steps:
  1. Delete `~/.brandmind/user/profile_settings.json` (simulate first-run)
  2. Reload `localhost:8501` → onboarding modal auto-opens
  3. Fill one field, click "Save and continue"
  4. Confirm modal closes; `profile_settings.json` written; `profile.md` managed block present
  5. Click sidebar Settings → dialog opens with saved values
  6. Edit a field → Save → reload → values persist
- Expected: each step passes; backend `GET` returns the saved values
- Status: ⏳ Pending

### Test 4: Skip path
- Steps: from a fresh state, click "Skip for now"
- Expected: modal closes; reload does not re-open it; `onboarding_completed=true` written to backend
- Status: ⏳ Pending

### Test 5: Backend-unreachable degradation
- Steps: stop the backend; reload web; verify no broken-modal state surfaces
- Expected: onboarding does NOT auto-open; sidebar Settings button still clickable (dialog opens with empty options); Save returns inline error
- Status: ⏳ Pending

------------------------------------------------------------------------

## 📊 Decision Log

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | Onboarding form layout | Multi-step wizard vs. single-panel form | Single-panel | User said "lightweight"; wizard is heavier UX and adds nav state for a 6-field form |
| 2 | Settings dialog nav rail | Drop the rail (single section) vs. keep but only show "Personalization" | Keep | User explicitly called out a future "General" section; keeping the rail surfaces the seam |
| 3 | Skip semantics | Skip leaves `onboarding_completed=false` vs. true | Save with `=true` | Avoids re-nagging the user every reload; user can still revisit via Settings |
| 4 | Auto-open guard | Server-side flag only vs. additional client flag | Both | LocalStorage flag protects against repeated auto-open before the user has clicked Save; without it, a slow PUT could re-trigger onboarding on next reload |
| 5 | Settings entry placement | Sidebar footer vs. header menu | Sidebar footer | Matches user's reference mockup + ChatGPT pattern; header is already crowded with brand + canvas + connection indicator |

------------------------------------------------------------------------

## 📝 Task Summary

> Filled in after implementation completes.

### What Was Implemented
TBD

### Technical Highlights
TBD

### Validation Results
TBD

### Deployment Notes
TBD
