# Task 90: Stitch-Driven Design System + 5 Frame Mockups

## 📌 Metadata

- **Epic**: Web UI v1 (#88 → #94)
- **Priority**: High (pause checkpoint 2 — visual approval required)
- **Status**: Awaiting User Visual Approval
- **Estimated Effort**: 0.5 day
- **Team**: Web Foundation
- **Related Tasks**: Task #89 (Reflex scaffold consumes nothing from here; #91 onward consumes `docs/web_design.md`), Task #91 (core layout + chat), Task #92 (canvas + artifact rendering)
- **Blocking**: Task #91, Task #92, Task #93
- **Blocked by**: Task #89 (scaffold landed `d203eee`)

### ✅ Progress Checklist

- [x] 🤖 Agent Protocol — Read and confirmed
- [x] 🎯 Context & Goals — Problem definition + success metrics
- [x] 🛠 Solution Design — Stitch as upstream-of-truth ingestion, `docs/web_design.md` as canonical source of truth
- [x] 🔬 Pre-Implementation Research — Stitch capability + framework alignment confirmed
- [x] 🔄 Implementation Plan — design doc → Stitch project → 5 frames
- [x] 📋 Implementation Detail — Design doc landed, Stitch frames generated
- [ ] 🧪 Test Execution Log — N/A (no source code; visual approval is the gate)
- [x] 📊 Decision Log
- [ ] 📝 Task Summary — Awaiting user visual approval at PAUSE CHECKPOINT 2

## 🔗 Reference Documentation

- **Coding Standards**: `tasks/task_template.md` Rule 2.5 (review surface) + Rule 4 (line length ≤100)
- **Roadmap Memory**: `~/.claude/projects/-Users-lehoanganhtai-projects-brandmind-ai/memory/web_ui_v1_roadmap_2026_05_16.md`
- **Stitch MCP**: `mcp__stitch__create_project`, `mcp__stitch__upload_design_md`, `mcp__stitch__create_design_system_from_design_md`, `mcp__stitch__generate_screen_from_text`
- **TUI banner reference**: `src/cli/tui/app.py` — same teal `#5fb3a8` accent on dark base; web is its spiritual sibling
- **Inspiration corpus**: Claude Chrome canvas extension, ChatGPT canvas pattern, Linear/Vercel ambient depth

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Task #89 landed a runnable Reflex scaffold (`d203eee`) but it is just a teal wordmark + health badge. Tasks #91 onward will render the real UI (chat pane, canvas drawer, artifact viewers, degraded states). Before any source code goes in, the design language needs to be locked at one place so subsequent task surfaces reference a stable spec rather than re-debating tokens per task.
- Stitch is the MCP-driven design tool we agreed to use to turn a design.md specification into Figma-grade frame mockups. Stitch's value here is twofold: it forces the spec to be precise enough to compile, and it produces visual artifacts the user can approve before code is written.

### Mục tiêu

Produce two deliverables in one commit:

1. **`docs/web_design.md`** — the canonical, in-repo source of truth for the web UI design system. Locked color tokens, glass-surface rules with explicit "glass-yes / glass-no" map, typography scale, spacing scale, component inventory (Header, PhaseProgressSidebar, ChatPane, MessageBubble, StreamingTokenContainer, ThinkingExpansion, ToolCallTimeline, InputComposer, CanvasPane, ArtifactPanel + 4 artifact viewers, DegradedBanner, ToastNotifications, SettingsDialog), motion spec, iconography set (Lucide), accessibility minimums, 5-frame inventory pointing into Stitch.
2. **Stitch project** with 5 frames generated from the locked design system:
   - Frame 1: `chat_with_canvas` — three-column showcase (sidebar | chat | canvas drawer with artifact list)
   - Frame 2: `chat_only` — two-column with canvas hidden
   - Frame 3: `artifact_viewer_brand_key` — 3×3 Brand Key grid in canvas drawer
   - Frame 4: `artifact_viewer_docx` — DocxView with TOC + rendered body in canvas drawer
   - Frame 5: `degraded_banner` — red DegradedBanner + OFFLINE status + disabled InputComposer

### Success Metrics / Acceptance Criteria

- **`docs/web_design.md`** is the only place we change to amend the design system. Tasks #91 / #92 / #93 read from it; if implementation needs to deviate, the doc updates first.
- **Token consistency**: `bg.canvas = #0e1318`, `accent.teal.solid = #5fb3a8`, `text.primary = #e8eef0` appear in every Stitch frame's color palette. Glass surfaces appear ONLY on backdrop layers (header, sidebar, canvas drawer) — NOT on chat scroll or streaming-token containers.
- **5 Stitch frames** generated and viewable via screenshot URL + downloadable HTML. Each frame matches the verbal description in `docs/web_design.md § 13 Frame inventory`.
- **No source code** in this commit. Pure design/spec artifacts only. Source code starts at Task #91.
- **Pause checkpoint 2** triggers user visual approval — the next commit cannot land until the user has visually inspected the 5 frames and either approved or requested revisions.

------------------------------------------------------------------------

## 🛠 Solution Design

### Approach

The flow is single-direction and deliberately friction-heavy at the top so the bottom (implementation) gets cheap:

1. Author `docs/web_design.md` from first principles (color tokens → glass rules → typography → spacing → component inventory → motion → frame inventory). This is the high-leverage surface — every later decision references it.
2. Create a Stitch project, upload `docs/web_design.md` as the design system source. Stitch's `create_design_system_from_design_md` ingests the YAML frontmatter + prose and produces a design system asset (color palette, typography scale, named tokens).
3. Generate 5 frames against that design system asset using `generate_screen_from_text`. Each frame prompt is a verbal description of one UI state, with explicit token references (e.g. "bg #0e1318", "accent #5fb3a8") so Stitch substitutions are tightly bounded.
4. Inspect each frame's screenshot URL. Land the docs commit. Pause for user visual approval.

### Why Stitch upstream of source code

Stitch is a one-way ratchet for the design language: once the design system asset is created, every frame inherits the same tokens, fonts, spacing, and radius. That stops per-frame drift. The HTML the frames produce is throw-away (Tailwind + a Geist font that we won't ship); the value is the **visual spec the user approves**, which then drives `web/brandmind_web/components/**` in Task #91.

The alternative (write Tailwind/Radix components first, iterate visually in Reflex) is more loops and more places to debate tokens. The Stitch pass collapses the design conversation into one approval gate.

### Glass-scope discipline

The user's locked aesthetic constraint is "glass on backdrop layers only, NOT chat scroll". `docs/web_design.md § 3 Glass surfaces` materializes this as an explicit table:

| Surface | Glass? | Why |
|---|---|---|
| Header (top bar) | YES | Backdrop layer; doesn't repaint per token |
| PhaseProgressSidebar | YES | Backdrop layer; static while chat scrolls |
| CanvasPane drawer | YES | Slide-in overlay; signals temporary higher-order surface |
| ChatPane scroll | NO | Streaming tokens repaint frequently; blur causes judder |
| MessageBubble | NO | Same reason; bubbles fade-in 160ms, no transform animations |
| StreamingTokenContainer | NO | Hardest-hit by repaint — solid background only |
| InputComposer | NO | Bottom of chat, also subject to caret/cursor repaint |
| ToastNotifications | NO (solid) | Short-lived; solid surface keeps focus |

Every Stitch frame inherits this rule because the prompts call out which surface is glass and which is not.

### Frame inventory

| Frame | UI State | Purpose | Consumed by |
|---|---|---|---|
| 1 | `chat_with_canvas` | Default working state — sidebar + chat + canvas open with artifact list | Task #91 (layout), Task #92 (canvas) |
| 2 | `chat_only` | Canvas hidden — narrow two-column chat-first view | Task #91 |
| 3 | `artifact_viewer_brand_key` | Brand Key 3×3 grid open in canvas drawer | Task #92 (image-inline rendering) |
| 4 | `artifact_viewer_docx` | DocxView with TOC + rendered HTML body | Task #92 (mammoth-js DOCX rendering) |
| 5 | `degraded_banner` | Server unreachable — red DegradedBanner + OFFLINE + disabled InputComposer | Task #93 (resilience) |

------------------------------------------------------------------------

## 🔬 Pre-Implementation Research

### Stitch capability check

- **`create_design_system_from_design_md`** — confirmed: ingests YAML frontmatter (colors, typography, spacing, radius) + prose body. Returns an asset ID reusable across `generate_screen_from_text` calls. Tested 2026-05-16: design-system asset `e93e7bc48f594c75998c6eb335dbebe2` produced from `docs/web_design.md`.
- **`generate_screen_from_text`** — confirmed: each call accepts `designSystem` parameter that scopes color/typography/spacing substitutions. Without it, Stitch invents tokens per frame. With it, tokens stay consistent across 5 frames.
- **Substitutions observed**: Stitch translates some tokens (`bg.canvas #0e1318` → `surface-deep #0F1113`; Geist instead of Inter). These substitutions are at the visual-rendering layer, not the spec layer; `docs/web_design.md` remains the source of truth and the Reflex/Radix implementation in Task #91 will use the canonical tokens directly.

### Glass-scope alignment

- The chat-scroll repaint concern is real: Chrome's backdrop-filter triggers a full repaint on every paint of the layer behind it. With streaming tokens appending every ~50ms, a glass chat surface would judder visibly on mid-range hardware.
- Confirmed by inspecting the locked aesthetic constraint in user-feedback memory `feedback_checkpoint_discipline_2026_05_16.md` and the project-level constraint that "smoothness > visual effect".

------------------------------------------------------------------------

## 🔄 Implementation Plan

### Phases

1. **Design doc authoring** ✓
   - Color tokens (base surfaces, glass surfaces, accent teal, semantic state, text colors).
   - Typography scale (Geist sans + JetBrains Mono for label-caps; 6 sizes).
   - Spacing + radius + shadow scales.
   - Glass-yes / glass-no explicit map.
   - Layout grid (sidebar 240px, chat max-width 768px, canvas 720px drawer).
   - Component inventory (17 components).
   - Motion spec (durations, easings).
   - Iconography (Lucide default).
   - Accessibility minimums (contrast, focus, ARIA).
   - 5-frame inventory pointing into Stitch.

2. **Stitch project setup** ✓
   - `create_project` — "BrandMind Web UI v1" (project ID `11570918663683429747`).
   - `upload_design_md` — design.md uploaded (screen ID `14614662870257837870`).
   - `create_design_system_from_design_md` — asset `e93e7bc48f594c75998c6eb335dbebe2`.

3. **Frame generation** ✓
   - Frame 1 `chat_with_canvas` — screen ID `401623cba00f4ffc842f91450534b4a9`.
   - Frame 2 `chat_only` — screen ID `c0fafc745f5649c894f8b6ef86eff962`.
   - Frame 3 `artifact_viewer_brand_key` — screen ID `bace16a0971a4fdd8d99524e6b0c096f`.
   - Frame 4 `artifact_viewer_docx` — screen ID `af171f6d4e71416ca994e28c35656f9b`.
   - Frame 5 `degraded_banner` — screen ID `5f63d1ec095b4eccaf7be877fd7ab9c4`.

4. **Commit + pause checkpoint 2** — IN PROGRESS
   - Commit `docs/web_design.md` + this task surface as single-concern docs commit.
   - GitNexus `detect_changes` before commit.
   - Update auto memory + shared wiki.
   - Pause for user visual approval before starting Task #91.

------------------------------------------------------------------------

## 📋 Implementation Detail

### File changes (in this commit)

| File | Action | Why |
|---|---|---|
| `docs/web_design.md` | NEW (410 lines) | Canonical design system source of truth |
| `tasks/task_90_design_system_and_stitch_frames.md` | NEW | Rule 2.5 review surface for the design decision |

No source code changes. No `src/`, `web/`, `tests/` modifications. Source code begins at Task #91.

### Stitch project artifacts (off-repo)

- Project: `projects/11570918663683429747` — "BrandMind Web UI v1"
- Design system asset: `assets/e93e7bc48f594c75998c6eb335dbebe2`
- 5 frame screen IDs as listed in Phase 3 above.

User accesses via the Stitch web UI to visually review.

------------------------------------------------------------------------

## 📊 Decision Log

### Decision 1: Stitch upstream of code (vs. Reflex-first iteration)

- **Context**: Two ways to land web UI design — author Reflex components and iterate visually in browser, or author a design spec + Stitch frames first and then implement.
- **Decision**: Stitch upstream.
- **Why**:
  1. The aesthetic is a taste call by the user. Stitch's frame screenshots are the cheapest possible artifact for that approval — no Reflex compile, no port-collision risk, no `.web/` build artifacts to clean up after a rejected design.
  2. Token drift across components is the #1 cost of design-while-you-code. A locked design system asset (Stitch + `docs/web_design.md`) eliminates that class of bug.
  3. Tasks #91 / #92 / #93 each only need to reference `docs/web_design.md § X` for design questions, never re-debate tokens or glass scope.
- **Trade-off**: Stitch HTML is throw-away (not used in production). That cost is small because the goal was the visual spec, not the markup.

### Decision 2: `docs/web_design.md` vs `web/DESIGN.md`

- **Context**: Where does the design source-of-truth live?
- **Decision**: `docs/` (top-level docs folder).
- **Why**: `docs/` already contains research and thesis docs; `web/` is the Reflex sub-project and is gitignored partially (`.web/`, `assets/external/`, generated configs). Putting the design doc inside a partially-gitignored sub-project risks future accidental ignores. `docs/web_design.md` is unambiguously tracked and easy to reference from any other task surface.

### Decision 3: Glass on backdrop layers only (chat scroll is solid)

- **Context**: Glass adds visual depth but causes repaint judder on streaming-token surfaces.
- **Decision**: Glass on Header / Sidebar / Canvas drawer. Solid on ChatPane / MessageBubble / StreamingTokenContainer / InputComposer / ToastNotifications.
- **Why**: Streaming token append (~50ms cadence) + backdrop-filter blur = full-layer repaint on every paint. On mid-range hardware this is visibly janky. The user's locked constraint is "smoothness > visual effect"; this rule is the operationalization.

### Decision 4: 5 frames, not more

- **Context**: There are at least 12 distinct UI states (initial empty, chat with thinking expansion, chat with tool-call timeline, sub-agent dispatch, canvas with each of 4 artifact types, settings dialog, error toast, mobile breakpoint, etc.). Stitch is per-frame paid.
- **Decision**: 5 frames covering the canonical states only — the rest is derived in Task #91 / #92 by composing the same components.
- **Why**: Stitch's value is the visual approval gate, not exhaustive screen coverage. Once the user approves these 5 (which span the major layout configurations), variations follow from the locked component inventory in `docs/web_design.md` without new frames.

### Decision 5: Stitch model `GEMINI_3_1_PRO`

- **Context**: Frame quality varies by model.
- **Decision**: `GEMINI_3_1_PRO` for all 5 frames.
- **Why**: Highest-quality model in the Stitch lineup. Frame generation latency is acceptable (~60s per frame); the cost difference vs Flash is small for a one-off design pass.

------------------------------------------------------------------------

## 🧪 Test Execution Log

No automated tests. Visual approval at PAUSE CHECKPOINT 2 is the gate.

User-facing verification:

1. Open Stitch web UI → project `BrandMind Web UI v1`.
2. Inspect each of 5 frame screenshots.
3. Cross-reference against `docs/web_design.md § 13 Frame inventory`.
4. Approve (proceed to Task #91) or request revisions (regenerate frames with adjusted prompts; design doc updates first).

------------------------------------------------------------------------

## 📝 Task Summary

PENDING USER VISUAL APPROVAL.

After approval:
- Auto memory + shared wiki updated.
- Task #91 unblocked.
- Design doc + this task surface remain authoritative for all subsequent web UI work.
