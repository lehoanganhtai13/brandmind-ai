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

### 8.1 Desktop (≥ 1024 px)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Header (56 px sticky, glass.bg.subtle)                                        │
├───────────┬──────────────────────────────────────────────┬───────────────────┤
│ Phase     │ Chat pane                                    │ Canvas drawer     │
│ sidebar   │ (max-w 768 px centered)                      │ (slide-in,        │
│ (240 px)  │                                              │  default 480 px,  │
│ glass.bg  │ bg.surface.1 (NO glass)                      │  resizable        │
│ .subtle   │                                              │  30%–70% vw)      │
│           │                                              │ glass.bg.elevated │
│           │                                              │                   │
│           │                                              │                   │
│           │  Input composer (sticky bottom)              │                   │
│           │  bg.surface.2                                │                   │
└───────────┴──────────────────────────────────────────────┴───────────────────┘
```

### 8.2 Tablet (768–1023 px)

- Sidebar collapses to icon-only rail (56 px). Expand on hover.
- Canvas drawer becomes 60% width when open; chat shrinks correspondingly.

### 8.3 Mobile (< 768 px)

- Sidebar becomes a drawer triggered by a header icon.
- Canvas drawer becomes a full-viewport modal.
- Chat pane drops max-width constraint; goes full-width with `space.3` x-padding.

## 9. Component inventory

For each component the spec lists: purpose, key props (informally), states it
must render, and which design tokens apply.

### 9.1 Header

- Purpose: brand wordmark + session selector + connected/disconnected status
  + settings menu.
- States: connected, disconnected, settings-open.
- Tokens: `glass.bg.subtle`, `accent.teal.solid` (wordmark), `text.primary`
  (session name), `text.secondary` (status caption).

### 9.2 PhaseProgressSidebar

- Purpose: visualise the 6-phase BrandMind workflow (0 → 5, plus optional 0.5
  for refresh / repositioning scopes).
- Per-item states: idle, current (accent fill bar on left), completed
  (checkmark icon), locked (text.muted).
- Bottom: collapse-to-rail icon button.

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

The 5 frames the Stitch project must produce, in order of priority for the
v1 build:

| # | Frame name | What it shows | Used by task |
|---|---|---|---|
| 1 | `chat_only` | Header + sidebar + chat with 3 sample message bubbles + 1 tool-call timeline card + InputComposer. Canvas hidden. | #91 |
| 2 | `chat_with_canvas` | Same as `chat_only` plus the CanvasPane open showing ArtifactPanel with 4 sample artifact items. | #92 |
| 3 | `artifact_viewer_brand_key` | Canvas drawer with the Brand Key image rendered inline (replace with a placeholder rectangle in the design). | #92 |
| 4 | `artifact_viewer_docx` | Canvas drawer with DocxView — TOC on left, HTML body on right. | #92 |
| 5 | `degraded_banner` | DegradedBanner red state visible between header and chat; InputComposer disabled. | #93 |

For each frame, the design system tokens above are the only allowed values
the screen may use. Stitch will receive this doc verbatim plus the frame
list as the source of truth.

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
