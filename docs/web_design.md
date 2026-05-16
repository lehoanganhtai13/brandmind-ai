# BrandMind Web UI v1 — Design System

> **Status**: Locked 2026-05-16 (Task #90). Source of truth for Tasks #91 (core
> layout + chat) and #92 (canvas + artifact rendering). Any deviation in
> implementation must update this doc first.

## 1. Design intent

BrandMind's web UI is the agentic-web face of the AI mentor: chat-first, with
a slide-in canvas where the agent's specialist activity (tool calls, sub-agent
work, generated artifacts) becomes legible to the user. The aesthetic anchors:

- **Calm, focused dark surfaces** so multi-turn reasoning sessions are easy on
  the eye. No bright whites; deep neutrals with one accent.
- **One accent — teal** carried from the TUI banner (`#5fb3a8`). The accent
  signals brand identity and the agent's voice; everything else is neutral.
- **Glass surfaces where backdrop blur clarifies hierarchy**, never on the
  chat scroll. Glass on streaming-token containers causes repaint judder.
- **Motion that respects the work**: slide-ins are 240–320 ms cubic-bezier;
  message bubbles fade in 160 ms; no transform animations on streaming text.
- **Information density tuned for an expert user**. Compact when the user is
  reading the agent's reasoning; expansive when they're choosing among
  artifacts.

Inspiration set:

- **Claude Chrome extension** — the canvas pattern (sidebar + main + slide-in
  workspace).
- **ChatGPT canvas** — the artifact preview that opens beside the chat.
- **Linear / Vercel** — glass headers, condensed phase sidebars, ambient depth.
- **TUI banner** — same teal warmth, same dark base; the web is the TUI's
  spiritual sibling at scale.

## 2. Color tokens

All tokens are written here as raw hex / rgba so Stitch can ingest them
directly. The Reflex/Radix theme (`web/rxconfig.py`) uses the `teal` /
`sage` Radix scales, which map to these tokens at the design-system level.

### 2.1 Base surfaces

| Token | Value | Usage |
|---|---|---|
| `bg.canvas` | `#0e1318` | App background. The lowest surface — what shows through every transparent layer. Matches the TUI banner background. |
| `bg.surface.1` | `#171c22` | Cards, sidebar, header, drawer body. Default container surface. |
| `bg.surface.2` | `#1f262d` | Elevated cards, hover state, dropdown menu, popover body. |
| `bg.surface.3` | `#272f37` | Active selection, focus background, pressed-button state. |
| `bg.overlay.scrim` | `rgba(8, 11, 14, 0.62)` | Modal scrim covering the page behind a dialog. |

### 2.2 Glass surfaces (backdrop-blur)

| Token | Value | Usage |
|---|---|---|
| `glass.bg.subtle` | `rgba(23, 28, 34, 0.55)` + `backdrop-filter: blur(20px) saturate(140%)` | Sidebar, header backdrop. |
| `glass.bg.elevated` | `rgba(31, 38, 45, 0.72)` + `backdrop-filter: blur(28px) saturate(160%)` | Drawer overlay, popover, settings dialog. |
| `glass.border` | `rgba(255, 255, 255, 0.06)` | 1 px hairline on every glass surface so the edge is legible against `bg.canvas`. |

### 2.3 Accent + brand

| Token | Value | Usage |
|---|---|---|
| `accent.teal.solid` | `#5fb3a8` | Brand wordmark, primary CTA fill, current-phase indicator, connected-state badge. |
| `accent.teal.hover` | `#71c2b7` | Hover state of solid accent. |
| `accent.teal.muted` | `rgba(95, 179, 168, 0.20)` | Selected message-bubble outline, sidebar item background when active, badge tints. |
| `accent.teal.text` | `#a4d3cb` | Text written *on* glass or surface backgrounds when teal foreground is needed (lifts contrast above `accent.teal.solid` direct text). |

### 2.4 Text + content

| Token | Value | Usage |
|---|---|---|
| `text.primary` | `#e8eef0` | Body text, chat messages, headings. |
| `text.secondary` | `#9aa5ac` | Captions, timestamps, sub-headers, side-panel labels. |
| `text.muted` | `#5e6a72` | Disabled state, placeholder, tertiary metadata. |
| `text.inverted` | `#0e1318` | Text on solid teal CTA fill. |

### 2.5 Semantic

| Token | Value | Usage |
|---|---|---|
| `semantic.success.solid` | `#5fb3a8` | Same as accent — connected, completed phase, "saved" toast. |
| `semantic.success.muted` | `rgba(95, 179, 168, 0.16)` | Connected-badge backdrop. |
| `semantic.warning.solid` | `#dbb56a` | Pending action, gentle attention. |
| `semantic.warning.muted` | `rgba(219, 181, 106, 0.16)` | Warning-banner backdrop. |
| `semantic.error.solid` | `#d97559` | Disconnected, failed tool call, destructive action. |
| `semantic.error.muted` | `rgba(217, 117, 89, 0.16)` | Disconnected-banner backdrop, error toast. |

### 2.6 Border + divider

| Token | Value | Usage |
|---|---|---|
| `border.subtle` | `rgba(255, 255, 255, 0.06)` | Glass surface hairlines, divider rules. |
| `border.default` | `rgba(255, 255, 255, 0.10)` | Card outlines, input borders. |
| `border.strong` | `rgba(255, 255, 255, 0.18)` | Focus rings, selected state outlines. |

## 3. Typography

| Token | Family | Usage |
|---|---|---|
| `font.sans` | `"Inter", "SF Pro Text", system-ui, sans-serif` | All UI text. |
| `font.mono` | `"JetBrains Mono", "SFMono-Regular", "Menlo", monospace` | Tool-call payloads, code, IDs. |

Radix-aligned size scale (matches `rx.text(size=...)`):

| Token | px | Usage |
|---|---|---|
| `size.1` | 12 | Captions, metadata, timestamps. |
| `size.2` | 14 | Sidebar items, sub-headers, dense UI text. |
| `size.3` | 16 | Default body, chat-message text. |
| `size.4` | 18 | Subheading, panel titles. |
| `size.5` | 20 | Page section heading. |
| `size.6` | 24 | Wordmark "BrandMind". |
| `size.7` | 28 | Empty-state primary text. |
| `size.8` | 32 | Modal title. |
| `size.9` | 40 | Reserved (not used in v1). |

Weights: `400` (regular default), `500` (medium — labels, sidebar items),
`600` (semibold — headings, wordmark), `700` (bold — reserved for callouts).

Line-height defaults:

| Use case | Value |
|---|---|
| Chat body (size.3) | 1.6 |
| Headings | 1.3 |
| Sidebar / labels (size.2) | 1.4 |

## 4. Spacing scale

| Token | px | Common usage |
|---|---|---|
| `space.1` | 4 | Inline icon-text gap. |
| `space.2` | 8 | Element-internal padding, button x-padding. |
| `space.3` | 12 | Card padding, sidebar item padding. |
| `space.4` | 16 | Section gap, message bubble padding. |
| `space.5` | 24 | Pane padding, sidebar→chat gap. |
| `space.6` | 32 | Vertical rhythm between major sections. |
| `space.7` | 40 | Empty-state padding. |
| `space.8` | 48 | Reserved. |
| `space.9` | 64 | Reserved. |

## 5. Radius

| Token | Value | Usage |
|---|---|---|
| `radius.sm` | 4 px | Inline tags, code-line backgrounds. |
| `radius.md` | 8 px | Buttons, input fields, badge corners. |
| `radius.lg` | 12 px | Cards, message bubbles. |
| `radius.xl` | 16 px | Sidebar / drawer corners. |
| `radius.pill` | 9999 px | Status pills, avatar containers. |

Matches Radix `radius="medium"` setting in `rxconfig.py`.

## 6. Shadow + elevation

| Token | Value | Usage |
|---|---|---|
| `shadow.1` | `0 1px 2px rgba(0,0,0,0.18)` | Buttons, inputs, default cards. |
| `shadow.2` | `0 4px 12px rgba(0,0,0,0.28)` | Elevated cards, dropdown menus. |
| `shadow.3` | `0 8px 24px rgba(0,0,0,0.36)` | Drawers, popovers, glass-elevated. |
| `shadow.inset.highlight` | `inset 0 1px 0 rgba(255,255,255,0.04)` | Top-edge highlight pairs with every glass surface so the surface reads above `bg.canvas`. |

## 7. Glass scope — explicit map

The single most-asked-about decision in the v1 spec. **Where glass applies and
where it does not.**

### 7.1 Apply glass

| Surface | Token | Reason |
|---|---|---|
| Header bar | `glass.bg.subtle` | Sticky over scrolling chat — glass keeps page hierarchy without occluding content. |
| Phase progress sidebar | `glass.bg.subtle` | Same — sits beside the chat scroll. |
| Slide-in canvas drawer | `glass.bg.elevated` | Has higher visual weight than the sidebar; deeper blur sells the "this is workspace, not chrome" framing. |
| Modal / dialog | `glass.bg.elevated` + `bg.overlay.scrim` behind | Standard modal pattern; glass front, scrim back. |
| Popover (e.g. status badge details) | `glass.bg.elevated` | Floats over content. |
| Toast notifications | `glass.bg.elevated` | Bottom-right ephemeral. |
| Degraded banner overlay | `glass.bg.subtle` tinted `semantic.error.muted` | Banner sits between header and chat — glass keeps the chat partly visible. |

### 7.2 Do **NOT** apply glass

| Surface | Reason |
|---|---|
| Chat scroll area / message bubbles | Streaming tokens trigger continuous repaints; backdrop-blur on streaming content judders on 60 Hz displays and tanks Reflex hydration smoothness. The chat surface stays solid `bg.surface.1`. |
| Canvas content area (artifact viewer body) | Artifacts (DOCX rendered HTML, PPTX previews, Brand Key image) need a flat, predictable surface for the user to read / inspect; glass would muddy text. |
| Input composer (the textarea at the bottom of the chat) | Solid `bg.surface.2` with a visible top hairline — the composer is a focus surface, not chrome. |
| Phase progress sidebar *items* (the chrome around them is glass, the items themselves are flat) | Hover and selected states need crisp color transitions, which glass blunts. |

## 8. Layout grid

### 8.1 Desktop wide (≥ 1280 px) — default sidebar EXPANDED

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [≡] Header (56 px sticky, glass.bg.subtle)                                    │
├───────────┬──────────────────────────────────────────────┬───────────────────┤
│ Phase     │ Chat pane                                    │ Canvas drawer     │
│ sidebar   │ (max-w 768 px centered)                      │ (slide-in,        │
│ (240 px)  │                                              │  default 480 px,  │
│ glass.bg  │ bg.surface.1 (NO glass)                      │  resizable        │
│ .subtle   │                                              │  30%–70% vw)      │
│ EXPANDED  │                                              │ glass.bg.elevated │
│           │                                              │                   │
│           │  Input composer (sticky bottom)              │                   │
│           │  bg.surface.2                                │                   │
└───────────┴──────────────────────────────────────────────┴───────────────────┘
```

### 8.2 Desktop narrow / laptop (1024–1279 px) — default sidebar COLLAPSED

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [≡] Header (56 px sticky, glass.bg.subtle)                                    │
├──────┬────────────────────────────────────────────────────┬──────────────────┤
│ Rail │ Chat pane (max-w 768 px centered)                  │ Canvas drawer    │
│ 56 px│ bg.surface.1                                       │ (when open)      │
│ glass│                                                    │                  │
│ COLL │  Input composer (sticky bottom)                    │                  │
└──────┴────────────────────────────────────────────────────┴──────────────────┘
```

Hover any rail item → tooltip with full phase label. Click sidebar toggle in header → expand to § 8.1 layout.

### 8.3 Tablet (768–1023 px)

- Sidebar forced to collapsed rail (56 px). Header toggle still works to expand temporarily as an overlay (slide-over pattern, scrim behind).
- Canvas drawer becomes 60% width when open; chat shrinks correspondingly.

### 8.4 Mobile (< 768 px)

- Sidebar becomes a slide-over drawer triggered by Header `panel-left-open` icon. Drawer covers chat with scrim behind. Auto-dismiss on item-click or scrim-click.
- Canvas drawer becomes a full-viewport modal.
- Chat pane drops max-width constraint; goes full-width with `space.3` x-padding.

### 8.5 Persisted state

User-toggled sidebar state stored via `rx.LocalStorage` key `bm.web.sidebar.collapsed: "0" | "1"`. Override the responsive default on subsequent visits. First-ever visit: pick default per breakpoint above. Reset-to-default mechanism: cleared on `Clear site data` only — no in-app reset button in v1.

## 9. Component inventory

For each component the spec lists: purpose, key props (informally), states it
must render, and which design tokens apply.

### 9.1 Header

- Purpose: sidebar toggle (leftmost) + brand wordmark + session selector + connected/disconnected status + settings menu.
- States: connected, disconnected, settings-open, sidebar-expanded, sidebar-collapsed.
- **Sidebar toggle button** (NEW): Lucide `panel-left-close` icon when sidebar is expanded; `panel-left-open` icon when collapsed. Sits at leftmost edge of header at fixed 40×40 hit area. Click toggles sidebar state and persists the choice via `rx.LocalStorage` key `bm.web.sidebar.collapsed: "0" | "1"`.
- Tokens: `glass.bg.subtle`, `accent.teal.solid` (wordmark), `text.primary` (session name), `text.secondary` (status caption), `text.secondary` → `text.primary` (toggle icon idle → hover).

### 9.2 PhaseProgressSidebar

- Purpose: visualise the BrandMind brand-strategy workflow phases — sequence is **scope-dependent**, NOT hardcoded 0→5. Source of truth: `src/core/src/core/brand_strategy/session.py:32 PHASE_SEQUENCES`.
- **Canonical scope-specific phase sequence** (Vietnamese-first display labels; backend constant `_PHASE_DISPLAY_LABELS` to be added in Task #91 export pipeline):

| Phase key (canonical) | Display label (VI) | Display label (EN tooltip on hover) | Appears in scopes |
|---|---|---|---|
| `phase_0` | Chẩn đoán hiện trạng | Diagnosis | all 4 scopes |
| `phase_0_5` | Audit thương hiệu hiện có | Existing-brand audit | refresh, repositioning, full_rebrand |
| `phase_1` | Phân tích thị trường | Market intelligence | all 4 scopes |
| `phase_2` | Định vị thương hiệu | Positioning | new_brand, repositioning, full_rebrand (NOT refresh) |
| `phase_3` | Bộ nhận diện | Brand identity | all 4 scopes |
| `phase_4` | Truyền thông | Communication | all 4 scopes |
| `phase_5` | KPI & Lộ trình | KPI & roadmap | all 4 scopes |

  Concrete sequences rendered by sidebar:
  - `new_brand` → Phase 0 → 1 → 2 → 3 → 4 → 5 (6 items)
  - `refresh` → Phase 0 → 0.5 → 1 → 3 → 4 → 5 (6 items — note Phase 2 SKIPPED)
  - `repositioning` → Phase 0 → 0.5 → 1 → 2 → 3 → 4 → 5 (7 items)
  - `full_rebrand` → Phase 0 → 0.5 → 1 → 2 → 3 → 4 → 5 (7 items)
- **Per-item states**:
  - `completed` — checkmark icon (Lucide `check`) in `accent.teal.solid`; label in `text.primary`.
  - `current` — accent fill bar on left (4px wide, `accent.teal.solid`); label in `text.primary` bold; phase number in `accent.teal.solid`.
  - `idle` (future phases) — no decoration; label in `text.muted`; phase number in `text.muted`.
- **Expanded state** (default ≥ 1280 px): 240 px wide; full phase label + number + status icon visible.
- **Collapsed state** (default < 1280 px): 56 px wide rail; only the phase number circle + current-state indicator visible; hover tooltip shows full label (Lucide `Tooltip` pattern, 200 ms delay, glass.bg.elevated surface). Click any rail item to expand sidebar AND scroll to that phase.
- **State sync mechanism**:
  - Initial render: web calls `GET /api/v1/sessions/{session_id}` and reads `current_phase`, `completed_phases`, `scope`. Backend already exposes these (`src/server/schemas/session.py:26 BrandStrategyMetadata`). Sidebar derives phase sequence from `scope` using the canonical table above (or, after Task #91, from a new `phase_sequence: list[str]` field on `SessionInfo`).
  - Live updates: web subscribes to SSE stream and listens for a new `PhaseAdvanceEvent` (to be added in Task #91 backend pass; emitted from `ContentCheckAdvanceMiddleware` at `src/core/src/core/brand_strategy/content_check.py:285` when verdict=ADVANCE). Event payload: `{event: "phase_advance", from_phase, to_phase, completed_phases}`.
  - Fallback if SSE drops: degraded-mode polling of `GET /api/v1/sessions/{session_id}` every 5 s while SSE reconnect is in-flight.
- **Toggle behavior**: collapse/expand toggled from Header (§ 9.1). Animation: 240 ms ease-out cubic-bezier(0.4, 0, 0.2, 1) on `width`. Items inside use `opacity` transition to avoid jarring layout shift on labels.

### 9.3 ChatPane

- Purpose: vertical scroll of message bubbles + streaming containers +
  tool-call timeline cards.
- Sub-components: MessageBubble, StreamingTokenContainer, ThinkingExpansion,
  ToolCallTimeline, ModelLoadingPlaceholder.

#### 9.3.1 MessageBubble

- Two variants: `user` (right-aligned, `accent.teal.muted` background) and
  `agent` (left-aligned, `bg.surface.1` with `border.default` hairline).
- Markdown content inside; code blocks use `font.mono` + `bg.surface.2`.

#### 9.3.2 StreamingTokenContainer

- Renders incoming streaming tokens with a typing cursor (1 s blink).
- Same surface as agent MessageBubble — no animation on the container
  itself, only on the cursor.

#### 9.3.3 ThinkingExpansion

- Collapsible "Thinking" section above an agent message.
- Default collapsed; chevron toggles. Body uses `text.secondary` and italic.

#### 9.3.4 ToolCallTimeline

- Inline cards (not separate panel) interleaved with messages.
- Per-card: tool icon, tool name, optional input summary, status pill
  (running / completed / failed), duration.
- Click → expand to show full input + result payload.

### 9.4 InputComposer

- Sticky bottom textarea, Enter sends / Shift+Enter newline.
- Disabled state when backend disconnected — placeholder reads
  *"Backend disconnected. Reconnect to send."* and the send button greys out
  to `text.muted`.

### 9.5 CanvasPane (drawer)

- Slide-in from right with `transform: translateX(0)`,
  `transition: transform 280ms cubic-bezier(0.2, 0.8, 0.3, 1)`.
- Header within: artifact title, breadcrumb (artifact category + filename),
  close button.
- Body: ArtifactPanel (list) OR active ArtifactViewer.

#### 9.5.1 ArtifactPanel

- List of `ArtifactRef` records from `/api/v1/sessions/{id}/artifacts`.
- Per-item: category icon (image / doc / deck / sheet), filename, generated
  timestamp (relative), size.
- Hover: `bg.surface.2`; click: opens corresponding viewer in the same pane.

#### 9.5.2 BrandKeyImageView (`images` category)

- `<img>` with `inline` content-disposition served by the backend.
- Zoom controls: fit-to-width (default), 100%, 200%.

#### 9.5.3 DocxView (`documents` category)

- Mammoth-js client-side conversion (DOCX → HTML).
- TOC sidebar on left of viewer (auto-extracted from heading tags).
- Body scrolls; TOC sticks.

#### 9.5.4 PptxView (`presentations` category) — **v1 unsupported inline**

- Placeholder card: "Download to view in PowerPoint" + size + generated time.
- v2 will add LibreOffice headless thumbnail rendering.

#### 9.5.5 XlsxView (`spreadsheets` category) — **v1 unsupported inline**

- Same pattern as PptxView. v2 will render via SheetJS.

### 9.6 DegradedBanner

- Top-of-chat banner (between header and chat scroll), full-width minus
  sidebar.
- States: hidden (default), warning (backend slow), error (backend
  disconnected).
- Auto-dismisses when recovery condition holds for 5 s.

### 9.7 ToastNotifications

- Bottom-right, max 3 stacked, `glass.bg.elevated`.
- Variants: success (teal), warning (warm), error (red).

### 9.8 SettingsDialog

- Triggered from header gear icon. Glass modal.
- Sections (v1): backend URL display (read-only), theme toggle
  (placeholder — locked to dark in v1), version info, link to GitHub.

## 10. Motion + interaction

| Pattern | Duration | Easing |
|---|---|---|
| Canvas slide-in / out | 280 ms | `cubic-bezier(0.2, 0.8, 0.3, 1)` |
| Message bubble fade-in | 160 ms | `ease-out` |
| Toast slide-up + fade | 220 ms in / 180 ms out | `ease-out` / `ease-in` |
| Sidebar collapse | 200 ms | `ease-out` |
| Streaming cursor pulse | 1 s loop | `step-start` toggle |
| Hover transitions (color, bg) | 120 ms | `ease-out` |
| Focus ring fade | 90 ms | `ease-out` |

**No** transform animations on the chat scroll, on streaming tokens, on the
ToolCallTimeline cards, or on MessageBubble — they sit inside the scroll
container that hydrates often. Restrict transforms to chrome (drawers,
overlays, toasts).

## 11. Iconography

- Lucide icon set (already used by Radix Themes plugin).
- Stroke 1.5 px, size scaled to text size (size.2 → 16 px, size.3 → 18 px,
  size.4 → 20 px, size.5 → 22 px).
- Status icons: `check` (connected, completed phase), `circle-x`
  (disconnected, failed), `loader` (running tool call), `square`
  (queued).

## 12. Accessibility

- WCAG AA contrast minimum on text/background pairs. The chosen tokens hit
  AA at minimum and AAA for body text on `bg.surface.1`.
- Keyboard navigation: Tab through header → sidebar → chat → composer →
  canvas (when open). Esc closes any drawer / modal.
- Focus ring: 2 px `border.strong` outline with 2 px offset.
- Reduced motion: when `prefers-reduced-motion: reduce`, replace all
  transitions ≥ 160 ms with instant state changes; cursor pulse stays.

## 13. Frame inventory for Stitch

The 6 frames the Stitch project must produce, in order of priority for the v1 build. **All frames must use the canonical Vietnamese phase labels from § 9.2** — Stitch must not invent labels like "Brand Audit / Positioning / Visual Identity / Tone of Voice / Rollout Strategy". Sidebar toggle button (§ 9.1) is visible in the header of every frame.

| # | Frame name | Sidebar state | Persona scope shown | What it shows | Used by task |
|---|---|---|---|---|---|
| 1 | `chat_only_expanded` | EXPANDED (240 px) | `new_brand` (Linh) — 6 phases | Header with toggle + expanded sidebar showing "Phase 0 Chẩn đoán hiện trạng → Phase 1 Phân tích thị trường → Phase 2 Định vị thương hiệu (CURRENT) → Phase 3 Bộ nhận diện → Phase 4 Truyền thông → Phase 5 KPI & Lộ trình" + chat with 3 sample message bubbles + 1 tool-call timeline card + InputComposer. Canvas hidden. | #91 |
| 2 | `chat_with_canvas_expanded` | EXPANDED (240 px) | `repositioning` (Hài) — 7 phases including 0.5 | Same as #1 but with `repositioning` 7-phase sequence (Phase 0 → 0.5 Audit thương hiệu hiện có → 1 → 2 → 3 → 4 (CURRENT) → 5) + CanvasPane open showing ArtifactPanel with 4 sample artifact items (Brand Key one-pager, brand_strategy.docx, strategy_deck.pptx, kpi_tracker.xlsx). | #92 |
| 3 | `artifact_viewer_brand_key_collapsed` | COLLAPSED (56 px rail) | `new_brand` (Linh) | Header with sidebar-toggle button (showing expand-icon since sidebar is collapsed) + 56 px rail with phase number circles (Phase 5 in current state, prior phases checkmarked) + canvas drawer with the Brand Key 3×3 grid as in current Frame 3. Demonstrates the chat real-estate gain when sidebar collapses. | #92 |
| 4 | `artifact_viewer_docx_expanded` | EXPANDED (240 px) | `refresh` (Hải) — 6 phases (NOTE Phase 2 SKIPPED) | Sidebar shows `refresh` scope: Phase 0 → 0.5 → Phase 1 → Phase 3 (CURRENT) → Phase 4 → Phase 5 (no Phase 2 entry — proves scope-dependence) + canvas drawer with DocxView — TOC on left, rendered HTML body on right. | #92 |
| 5 | `degraded_banner_expanded` | EXPANDED (240 px) | `repositioning` (Hài) | Same sidebar as #2 + DegradedBanner red state visible between header and chat + InputComposer disabled + Header right-side shows "OFFLINE" with grey dot. | #93 |
| 6 | `sidebar_collapsed_showcase` (NEW) | COLLAPSED (56 px rail) | `new_brand` (Linh) | Side-by-side comparison: same chat content as #1 but sidebar collapsed to 56 px rail. One rail item shows hover tooltip surfacing the full label "Phase 2 — Định vị thương hiệu". Demonstrates the toggle interaction visually. | #91 (collapsed-state implementation reference) |

For each frame, the design system tokens above are the only allowed values the screen may use. Stitch will receive this doc verbatim plus the frame list as the source of truth.

**Stitch generation discipline** (added after first-pass drift on 2026-05-16):
- Each frame prompt must enumerate the EXACT phase labels from § 9.2 with diacritics intact ("Chẩn đoán hiện trạng", "Định vị thương hiệu", "Bộ nhận diện", "Truyền thông", "KPI & Lộ trình", "Audit thương hiệu hiện có").
- Each frame prompt must call out the sidebar toggle button position + icon name in the Header.
- Each frame prompt must specify which scope's phase sequence is rendered (so Stitch does not invent its own product taxonomy).

## 14. Reference cross-links

- Reflex theme config: `web/rxconfig.py` (RadixThemesPlugin teal/dark).
- Live aesthetic anchor (TUI banner): `src/cli/tui/widgets/banner.py`.
- Backend endpoints the canvas will call: `src/server/api/artifacts.py`
  (`GET /sessions/{id}/artifacts`, `GET /artifacts/{id}/{filename}`).
- Roadmap: `tasks/task_88_…md` (backend), `tasks/task_89_…md` (scaffold),
  `tasks/task_91_…` and `tasks/task_92_…` (consumers of this design).
- Pause-checkpoint discipline:
  `~/.claude/projects/-Users-lehoanganhtai-projects-brandmind-ai/memory/feedback_checkpoint_discipline_2026_05_16.md`.

## 15. Decisions log (v1)

| # | Decision | Choice | Why |
|---|---|---|---|
| 1 | Light vs dark default | Dark-only in v1 | Mentor sessions are long-form reading + reasoning; dark surfaces match the TUI face and reduce eye strain. Light mode is a v2 follow-up if user demand surfaces. |
| 2 | Accent color | Teal `#5fb3a8` | Anchored to the TUI banner color so the two faces of BrandMind read as one product. |
| 3 | Glass on chat scroll | Banned | Repaint judder on streaming tokens; smoothness > visual effect per user constraint. |
| 4 | Icon family | Lucide | Default ship in Radix Themes; no extra dep; ample coverage. |
| 5 | Modal pattern | Glass-elevated front + scrim back | Standard agentic-UI modal; legible at a glance. |
| 6 | Canvas default width | 480 px (≈ 40 % of 1280 px viewport) | Wide enough to read DOCX body comfortably; not so wide it starves the chat at standard laptop widths. |
| 7 | Mobile canvas | Full-viewport modal | The drawer pattern doesn't survive narrow screens; full-screen modal is the honest answer. |
| 8 | Streaming cursor style | 1 s blink, step-start | Common pattern (ChatGPT, Claude.ai); reads as "agent is thinking", not as "input field". |
| 9 | DocxView TOC | Auto-from-headings | Heading structure is BrandMind's strategy-doc spine (10 sections); TOC navigation is the highest-leverage UX win for stakeholder review. |
| 10 | PPTX / XLSX inline | Deferred to v2 | LibreOffice / SheetJS each add significant build complexity; download-only is a defensible v1 ceiling. |
| 11 | Sidebar default state | Responsive — expanded ≥ 1280 px, collapsed < 1280 px; user toggle persisted via `rx.LocalStorage` | Mentoring product needs phase structure visible on first-open to assert value, but on common laptop widths (1280×800 student / dev) a 240 px sidebar starves the chat. Responsive collapse is the honest middle ground; persisted state respects user preference on subsequent visits. |
| 12 | Phase labels source-of-truth | `docs/web_design.md` § 9.2 canonical table, mirrored into backend `_PHASE_DISPLAY_LABELS` in Task #91 | Code (`session.py:_PHASE_HEADINGS`) currently only has nominal labels ("Phase 0", "Phase 0.5"). Semantic Vietnamese labels live here and will be exported via the API in Task #91 so web is consumer not generator. Vietnamese-first because BrandMind's user personas (Linh, Minh, Hài, Thảo, Hương) are Vietnamese F&B SME marketers. |
| 13 | Phase advance event mechanism | New SSE `PhaseAdvanceEvent` emitted from `ContentCheckAdvanceMiddleware` + `phase_sequence` field added to `SessionInfo`, both in Task #91 | Backend already tracks `current_phase` / `completed_phases` / `scope` in `BrandStrategySession` and exposes them via `GET /sessions/{id}`. Adding 1 SSE event type + 1 schema field gives push-based sidebar updates without polling; ~40 LOC backend change scheduled in Task #91. |
| 14 | Stitch frames as visual approval gate, not implementation source | Frames are regenerated when they drift from canonical labels; implementation always reads from `docs/web_design.md` + backend constants, never from Stitch HTML | First-pass Stitch generation (2026-05-16) substituted invented labels ("Brand Audit / Positioning / Visual Identity / Tone of Voice / Rollout Strategy") that did not match `PHASE_SEQUENCES`. User feedback (same date): regenerate frames with stricter prompts pinning canonical labels. Frame discipline now lives in § 13. |
