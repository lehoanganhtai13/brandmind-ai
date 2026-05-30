# BrandMind Web UI v1 — Design System

> **Status**: Locked 2026-05-16 (Task #90); updated 2026-05-25 with the collapsed-rail polish round (rail button factory, tooltip pill pattern, composer pill, canvas flex-sibling, empty-state hero).
>
> **Source-of-truth ordering** — this doc is the canonical human-readable spec for every visual decision; `web/brandmind_web/components/tokens.py` is its in-code machine-readable mirror. Both files MUST stay in lockstep — any token / spacing / radius / font / hover-state edit lands in the **same commit** that updates this doc, and any rail / composer / canvas / dialog component MUST source values from `tokens` (never inline literals). New UI work consults this doc + `tokens.py` first; deviations require updating both files before the implementation lands.

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

| Token | Code constant | Value | Usage |
|---|---|---|---|
| `glass.bg.subtle` | `GLASS_BG_SUBTLE` | `rgba(22, 24, 26, 0.62)` + `backdrop-filter: blur(20px)` | Sidebar, header backdrop. |
| `glass.bg.elevated` | `GLASS_BG_ELEVATED` | `rgba(22, 24, 26, 0.72)` + `backdrop-filter: blur(28px) saturate(160%)` | Drawer overlay, popover content surface, settings dialog. |
| `glass.border` | `GLASS_BORDER` | `rgba(255, 255, 255, 0.06)` | 1 px hairline on every glass surface so the edge is legible against `bg.canvas`. |

### 2.3 Accent + brand

| Token | Code constant | Value | Usage |
|---|---|---|---|
| `accent.teal.solid` | `ACCENT_TEAL_SOLID` | `#5fb3a8` | Brand wordmark, primary CTA fill, current-phase indicator, unseen-artifact pip, send-button fill. |
| `accent.teal.muted` | `ACCENT_TEAL_MUTED` | `rgba(95, 179, 168, 0.18)` | Selected message-bubble outline, sidebar item background when active, badge tints. |

### 2.4 Text + content

| Token | Code constant | Value | Usage |
|---|---|---|---|
| `text.primary` | `TEXT_PRIMARY` | `#e8eef0` | Body text, chat messages, headings. |
| `text.secondary` | `TEXT_SECONDARY` | `#bdc9c6` | Captions, sub-headers, ghost-button icon idle, model-picker chip text. |
| `text.muted` | `TEXT_MUTED` | `#9ca3af` | Disabled state, placeholder, tertiary metadata, idle phase number. |

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

### 2.7 State (error)

| Token | Code constant | Value | Usage |
|---|---|---|---|
| `state.error.fg` | `STATE_ERROR_FG` | `#ffb4ab` | Error banner text + icon. |
| `state.error.bg` | `STATE_ERROR_BG` | `rgba(147, 0, 10, 0.20)` | Error banner background tint. |
| `state.error.border` | `STATE_ERROR_BORDER` | `#5e1c1c` | Error banner left-edge border. |

## 3. Typography

Four stacks — picked so each surface has the right register without forcing a single family to carry every voice. Each stack ships from the Google Fonts CDN bundle declared in `web/brandmind_web/brandmind_web.py:stylesheets` (Fraunces + Geist + Manrope + JetBrains Mono).

| Token | Code constant | Family | Usage |
|---|---|---|---|
| `font.display` | `FONT_DISPLAY` | `"Fraunces", "Cormorant Garamond", "Times New Roman", Georgia, serif` | Editorial / hero voice — wordmark "BrandMind", empty-state greeting "Where would you like to start?", popover panel titles ("Recents"). 40 px in the empty-state hero; 20 px on the header wordmark. |
| `font.sans` | `FONT_SANS` | `"Geist", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` | Default UI text — body, sidebar items, chat messages, captions, buttons. |
| `font.dialog` | `FONT_DIALOG` | `"Manrope", "Geist", -apple-system, …` | Settings + onboarding modals — Manrope's slightly warmer character distinguishes the focused-task surface from the rest of the chat shell. |
| `font.mono` | `FONT_MONO` | `"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace` | Tool-call payloads, code, IDs, model-picker chip ("Gemini 3.5 Flash"). |

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

| Token | Code constant | Value | Usage |
|---|---|---|---|
| `radius.sm` | `RADIUS_SM` | 4 px | Inline tags, code-line backgrounds, tooltip pill. |
| `radius.md` | `RADIUS_MD` | 8 px | Input fields, badge corners, popover trigger states. |
| `radius.btn` | `RADIUS_BTN` | 10 px | Rail icon buttons (brand, new-chat, recents, settings, sidebar-toggle, canvas-toggle) — single source for every 40×40 ghost button on the collapsed rail. |
| `radius.lg` | `RADIUS_LG` | 12 px | Cards, message bubbles, popover content surface. |
| `radius.xl` | `RADIUS_XL` | 16 px | Sidebar / drawer corners. |
| `radius.composer` | `RADIUS_COMPOSER` | 28 px | InputComposer pill — single value pinned to every composer surface so the pill geometry never drifts when the textarea auto-grows. |
| `radius.pill` | `RADIUS_PILL` | 9999 px | Status pills, avatar containers, unseen-artifact notification badge. |

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

## 8A. Collapsed-rail button system

Every button that lives on the 56-px collapsed rail (or the rail-equivalent column in the header) MUST be built through the single factory `_rail_button_bare(icon_tag, aria_label, on_click=None, css_tooltip=None)` in `web/brandmind_web/components/sidebar.py`. This is the discipline that keeps the sidebar coherent — there is exactly one place to change the geometry, hover behavior, and corner radius, and every rail entry inherits the same look automatically.

### 8A.1 Button geometry (single source)

| Property | Code constant | Value | Note |
|---|---|---|---|
| Hit size | `RAIL_ICON_BUTTON_PX` | 40 × 40 px | Wide enough to hit without aiming; same as the toggle/canvas buttons in the header so the rail and header line up. |
| Corner radius | `RADIUS_BTN` | 10 px | Matches the brand button + sidebar toggle; soft enough to read as a friendly tap target, sharp enough to feel modern. |
| Icon size | `ICON_GHOST_BUTTON` | 20 px | Lucide stroke 1.5 px; the de-facto Radix `size="2"` icon weight. |
| Idle background | — | `transparent` | The rail's glass surface shows through. |
| Hover background | `RAIL_HOVER_BG` | `rgba(255, 255, 255, 0.12)` | One value for every rail button — brand, new-chat, recents, settings, sidebar-toggle, canvas-toggle. |
| Active background (popover open) | `RAIL_HOVER_BG` | same | Applied via `&[data-state='open']` so the icon stays highlighted while its attached popover/menu is open — matches how Radix would handle it natively. |
| Transition | — | `background-color 160ms ease` | |

### 8A.2 Icon dictionary

The rail keeps a small fixed vocabulary so users learn the affordances quickly. Every glyph is Lucide.

| Button | Icon (Lucide tag) | Why |
|---|---|---|
| Brand (collapsed rail header) | logo image at rest, cross-fades to `panel_left` on hover | Mirrors ChatGPT / Gemini — the brand mark doubles as the re-open affordance. The hover swap reveals it's clickable without losing the brand landmark. |
| Sidebar-toggle (expanded sidebar header) | `panel_left` | Chevron-free "panel handle" reading — matches Gemini / ChatGPT, avoids a directional arrow that suggests motion the user did not request. |
| New chat | `square_pen` | ChatGPT / Gemini compose glyph — universally legible "create" affordance. |
| Recents | `message_circle` | ChatGPT "message-bubble" recents handle. Click → list popover. |
| Settings | `settings` | Standard cog. |
| Canvas-toggle (header right) | `panel_right` | Same panel-handle family as sidebar-toggle; mirrored side reads as "open right pane". |

### 8A.3 Membership rule

Any new rail entry — search, prompt library, history filter, etc. — MUST be built via `_rail_button_bare`, pick its glyph from a Lucide set that fits the same stroke / proportion family, and inherit hover + radius automatically. Inline button construction in collapsed-rail contexts is a code smell that defeats the system.

## 8B. Rail tooltip pill

Every rail button surfaces its label as a small dark-mode-inverted pill anchored to its right side with a 5×10 px arrow. **Both rendering variants below produce a pixel-identical pill** — the variant is a function of the wrapper structure, not a visual choice. Hover-only behavior, identical placement, identical color / radius / font / arrow.

### 8B.1 Pill specification (both variants render this)

| Property | Value |
|---|---|
| Background | `#eceeed` (the Radix Themes `--gray-12` resolved value inside `.radix-themes` dark scope) |
| Text color | `#101211` (Radix `--gray-1`) |
| Padding | 4 px 8 px |
| Border radius | 4 px (`RADIUS_SM`) |
| Font | `FONT_SANS`, 12 px / 16 px line-height, weight 400 |
| Arrow | 5 px × 10 px left-pointing triangle, same color as pill, centered vertically, projecting 5 px past the pill's left edge toward the trigger |
| Open delay | 280 ms (Radix default minus the user-perceived-latency cut, matched by the CSS-pill JS controller) |
| Side / offset | `side="right"`, anchored 8 px past the button's right edge |

### 8B.2 Variant A — Radix Tooltip (default)

Use whenever the rail button is NOT the trigger for a Popover, DropdownMenu, ContextMenu, or any other Radix overlay that uses an asChild Slot wrapper. Example: new-chat, settings, sidebar-toggle, brand (collapsed-rail logo).

```python
rx.tooltip(
    _rail_button_bare(icon_tag="square_pen", aria_label="New chat", on_click=...),
    content="New chat",
    side="right",
    side_offset=8,
)
```

The Radix Tooltip primitive supplies the pill + the SVG arrow + the delay automatically. Helper: `_rail_icon_button(icon_tag, on_click, aria_label, tooltip_text)` in `sidebar.py` bundles this pattern.

### 8B.3 Variant B — CSS pill via body portal (Slot-collision case)

Required whenever the rail button is wrapped in `rx.popover.trigger`, `rx.dropdown_menu.trigger`, or any other Radix Themes trigger. The reason: Radix Themes' `Popover.Trigger` is hard-coded to `asChild` (`@radix-ui/themes/src/components/popover.tsx`), so it uses a Slot to merge props onto its child. `rx.tooltip` ALSO uses a Slot internally. Two Slot wrappers cannot both merge onto the same DOM button — Tooltip's Slot wins the `data-state`, Popover's loses `onClick`, and clicks no longer open the popover. Reflex 0.9.x doesn't expose Radix Tooltip's `Root` / `Trigger` / `Content` subcomponents separately, so we cannot nest the asChild chain manually.

Pattern:

```python
_rail_button_bare(
    icon_tag="message_circle",
    aria_label="Recent chats",
    css_tooltip="Recent chats",   # stamps data-bm-rail-tooltip="..." on the button
)
```

`css_tooltip` writes a `data-bm-rail-tooltip="<label>"` attribute onto the button. The body-level controller in `web/brandmind_web/brandmind_web.py`:

- Mounts a single `<div id="bm-rail-tooltip-pill">` at body level (escapes the sidebar's `overflow: hidden auto` clip).
- Listens for `pointerover` / `pointerout` on `[data-bm-rail-tooltip]`, fires the show after 280 ms, hides on leave and on `pointerdown`.
- Positions the pill at `r.right + 13, r.top + r.height/2` (the +13 matches the empirical x-position Radix Tooltip places its own pill at, so Variants A and B land on the same pixel column).
- Renders the arrow via a `::before` triangle on the pill (`border-right: 5px solid #eceeed`, transparent top/bottom 5 px borders) — same shape Radix's SVG arrow draws.

Variant B is part of the design system; it is NOT a fallback or a hack. Treat it as the official tooltip wrapper for any rail-trigger button.

## 9. Component inventory

For each component the spec lists: purpose, key props (informally), states it
must render, and which design tokens apply.

### 9.1 Header

- Purpose: 56-px sticky bar split into two zones — a **sidebar-column zone** that reserves the same width as the sidebar below (wordmark on the left, panel-toggle pinned to the right edge — the ChatGPT pattern where the toggle lives at the right edge of the sidebar header rather than the leftmost edge of the global bar), and a **main zone** with the session caption centered + canvas-toggle on the right.
- States: sidebar-expanded, sidebar-collapsed, canvas-open, canvas-closed, has-unseen-artifacts.
- **Expanded sidebar header** (sidebar-zone): Fraunces 20-px "BrandMind" wordmark on the left + `panel_left` Lucide icon (built via `_rail_button_bare` → § 8A) pinned to the right edge with a Radix tooltip "Close sidebar".
- **Collapsed sidebar header**: a single brand button centered on the 56-px rail — the BrandMind cat logo at rest, cross-fading to `panel_left` glyph on hover (Images #77 / #78 ChatGPT-Gemini pattern). Radix tooltip "Open sidebar" anchored right. Same `RADIUS_BTN` + `RAIL_HOVER_BG` as every other rail entry per § 8A.
- **Main-zone session caption**: agent's classified brand name + middle-dot + current-phase English label, both `text.muted` 13-px sans, hidden until the agent has classified the scope (the raw `phase_0` id is never user-meaningful and floats awkwardly on a fresh session).
- **Canvas-toggle** (main-zone right): `panel_right` Lucide icon, built via `_rail_button_bare` rules. Adds a 9-px teal notification badge at top-right when `has_unseen_artifacts AND NOT canvas_open` — same "unread content waiting" mental model as Slack / iMessage / GitHub-bell. Connection state has no header counterpart; `DegradedBanner` + composer-disabled cover the disconnected path, so a permanent "Connected" pill would be pure happy-path noise.
- Tokens: `glass.bg.subtle`, `text.primary` (wordmark + classified brand name), `text.muted` (session caption metadata), `text.secondary` (rail icons idle), `accent.teal.solid` (unseen-artifact badge fill).

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
- **Agent variant — ordered live blocks**: an agent turn renders as a vertical sequence of `ContentBlock` items in the order events arrived on the SSE wire. Two block kinds: `assistant_text` (a markdown paragraph from one or more `streaming_token` events, including the agent's user-facing working notes — backend emits `share_working_note` content as ordinary streaming-token text, never as a visible tool row) and `reasoning_timeline` (an interleaved thinking + tool-call trace from `streaming_thinking` / `tool_call` events). The dispatch layer opens a fresh `assistant_text` block whenever a token arrives after a reasoning block, so a working note authored before the agent starts thinking appears as its own paragraph ABOVE the timeline rather than being concatenated with the final answer at the bottom. The `done` event closes every block. Persisted history (`GET /api/v1/sessions/{id}/messages`) carries the same `blocks: list[PersistedContentBlockWire]` shape, so refresh / chat-switch restores the ordered layout including per-block `duration_label` on reasoning blocks. Legacy sessions saved before the blocks contract landed fall through to the single-content + single-timeline fallback layout.

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

- Sticky bottom **pill** (`radius.composer` = 28 px) — single `rx.hstack(textarea, model_picker, send)` row with `align="end"` so the model-picker chip and the send button pin to the bottom-right of the pill even when the textarea grows multiline. `bg.surface.2` fill, 1 px `glass.border` hairline, no shadow.
- Textarea: `font.sans` 14 px, `field-sizing: content` for native auto-grow (owned by the global `[data-bm-composer-textarea] { field-sizing: content }` rule so it shrinks back after a multi-line send), with a `CSS.supports`-gated `scrollHeight` JS fallback in `_COMPOSER_BOOTSTRAP_SCRIPT` capped at 180 px. Placeholder: `"Message BrandMind"`.
- **Uncontrolled by design (IME-safety).** The textarea has no `value` bound to server state — the DOM owns the text, so a server round-trip can never overwrite it mid-keystroke. A bound value previously re-asserted the stale server echo during a Vietnamese Telex composition and duplicated the just-typed syllable ("phát" → "phátphát"). With no bound value Reflex also drops the `DebounceInput` wrapper, so `on_change` fires per keystroke and syncs one way into `pending_input` (the send button + send body read it; it is never the display source). A React `key` bound to `composer_epoch` (incremented on every send) remounts the field empty to clear it.
- Model picker (left of send): `JetBrains Mono` chip rendering the selected model display name + chevron. Opens a Radix dropdown listing all `GET /api/v1/brand-strategy/models` entries with per-model trade-off blurbs. Locked to read-only after the first user message lands (per-session model decision).
- Send button: circular `accent.teal.solid` fill, white `arrow_up` Lucide glyph, sits at the pill's bottom-right via the parent's `align="end"`.
- Enter sends; Shift+Enter newline. Submit is blocked while `is_streaming` is true to prevent double-fires; the Reflex `KeyInputInfo` keydown handler discriminates Shift+Enter from bare Enter.
- Disabled state when backend disconnected — placeholder reads *"Backend disconnected. Reconnect to send."*, send button greys to `text.muted`. The pill's inner Radix textarea overlay rectangle is suppressed via the global `_GLOBAL_KEYFRAMES` `:has([data-bm-composer-textarea]:disabled)` rule so the pill stays visually clean during the lockout.

### 9.5 CanvasPane (side-by-side workspace viewer)

- **Side-by-side flex sibling** of the chat column, NOT a slide-over overlay drawer. Width: `CANVAS_DRAWER_PX = 720` px. Open/close still animates width via `DRAWER_DURATION_MS = 280` ms + `DRAWER_EASING = cubic-bezier(0.2, 0.8, 0.3, 1)`; the chat column shrinks correspondingly so user can read chat + artifact at the same time (Claude Cowork pattern). Reflex 0.9 transitions the explicit `width` property — no `transform: translateX` is used.
- **Two modes**, switched in-place inside the pane:
  - **List mode** (default after open): scrollable `ArtifactPanel` of `ArtifactRef` rows. Per-row: category icon, filename, generated timestamp, file size, hover-revealed download chip (`?disposition=attachment` query param so cross-origin downloads work).
  - **Viewer mode**: triggered by clicking a row in list mode. Renders the active `ArtifactViewer` (DOCX outline + body, Brand Key image, or placeholder card for PPTX/XLSX). Back-to-list button returns to the list without unmounting state.
- Header within: artifact title + breadcrumb (category + filename in viewer mode; "Files" pill in list mode), close-pane button on the right.
- **Unseen-artifact tracking** (header notification badge — § 9.1): `artifacts_seen_count` snapshots in BOTH `toggle_canvas` AND `close_canvas` so the badge clears when the user opens the canvas and only re-appears when a NEW artifact streams in. Matches the Slack / iMessage / GitHub-bell "unread content waiting" mental model.
- Tokens: `glass.bg.elevated` for the pane background, `RADIUS_LG` for inner cards, `SHADOW_DRAWER` for the left-edge shadow that separates the pane from the chat column.

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

- Top-of-chat banner (between header and chat scroll), full-width minus sidebar.
- States: **hidden** (default), **warning** (a recent SSE turn failed but the backend is healthy — offers "Try again"), **error** (backend unreachable — offers "Try again").
- **Recovery is silent.** No "Back online" celebration banner — the existing offline / warning banner simply disappears as soon as the underlying state clears. Matches Slack / Gmail / iMessage behavior, where reconnection is implicit (the inbox starts updating again) and a "back online" announcement would interrupt the chat surface to declare a non-actionable state change.

### 9.7 ToastNotifications

- Bottom-right, max 3 stacked, `glass.bg.elevated`.
- Variants: success (teal), warning (warm), error (red).

### 9.8 SettingsDialog

- Triggered from header gear icon. Glass modal.
- Sections (v1): backend URL display (read-only), theme toggle
  (placeholder — locked to dark in v1), version info, link to GitHub.

### 9.9 Recents popover (collapsed rail entry)

- Click-open (not hover) Radix Popover anchored to the Recents `message_circle` rail button per § 8A. Hover reveals the tooltip pill per § 8B Variant B; click opens the panel.
- Panel: 280 px wide, max-height 480 px, `bg.surface.1` glass-elevated with `RADIUS_LG` corners and a deep shadow (`0 16px 40px rgba(0, 0, 0, 0.42)`).
- Content: `FONT_DISPLAY` 16-px "Recents" heading + the 10 most recent sessions, each row wrapped in `rx.popover.close` so picking a chat dismisses the popover and routes through `switch_chat` in one motion. Empty state: italic muted "No chats yet — send a message to start."

### 9.10 EmptyState (fresh chat hero)

- Shown when no messages exist in the active chat (Claude / ChatGPT / Gemini fresh-chat pattern).
- Layout: vertically + horizontally centered column. One `FONT_DISPLAY` 40-px greeting ("Where would you like to start?"), then a 24-px gap, then an inline `InputComposer` reusing the same pill from § 9.4.
- Motion: single 600 ms `bm-empty-reveal` keyframe — `opacity 0 → 1` + `translateY(8px → 0)`. No starter-prompt chips, no description paragraph — minimal-by-design, consistent with the empty-state register of Claude.ai.

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
| 15 | Single rail-button factory | `_rail_button_bare` in `web/brandmind_web/components/sidebar.py` is the only construction site for collapsed-rail buttons. All geometry comes from `tokens.RAIL_ICON_BUTTON_PX / RADIUS_BTN / RAIL_HOVER_BG / ICON_GHOST_BUTTON` (§ 8A). | Without one factory, each new rail entry diverged on hover bg / radius / icon size and the user had to flag each drift individually. Centralizing the spec eliminates the class of "each spot a different number" bugs. |
| 16 | CSS tooltip pill for Slot-collision triggers (§ 8B Variant B) | Rail buttons wrapped in `rx.popover.trigger` / `rx.dropdown_menu.trigger` cannot also be wrapped in `rx.tooltip` — both wrappers use a Radix Slot and the inner Slot wins data-state while the outer Slot loses onClick. We render the pill via a body-portal `<div id="bm-rail-tooltip-pill">` driven by a tiny pointer-event controller, matched pixel-for-pixel to Radix Tooltip's spec (color, padding, radius, arrow, delay). | The discovery cost was high (verified via Radix Themes' `popover.tsx:26` source showing `asChild` is hard-coded); recording the WHY here prevents future contributors from "fixing" Variant B by re-wrapping in `rx.tooltip` and silently breaking the popover. Variant B is part of the design system, not a fallback. |
| 17 | Composer pill (§ 9.4) over the original "framed textarea" | 28-px pill with model picker + send pinned bottom-right via `align="end"` matches the ChatGPT / Claude composer convention. Field auto-grows up to 180 px via `field-sizing: content` + JS `scrollHeight` fallback. | The earlier 16-px-radius rectangle composer looked dated and the model-picker row floated above the textarea, wasting vertical real estate on a "where am I" anchor. The pill collapses input + model + send into one read. |
| 18 | Canvas pane as flex sibling (§ 9.5), not overlay drawer | Width animation, not transform translate; chat shrinks to keep both panes readable side-by-side. | The original drawer pattern obscured the chat scroll under a `glass.bg.elevated` overlay — fine for a quick file peek, wrong for "I want to keep reading the agent's mentor message while inspecting the brief". The flex-sibling layout is the Claude Cowork pattern and tested cleanly with no chat-scroll repaint regressions. |
| 19 | Empty-state hero (§ 9.10) is one Fraunces sentence + an inline composer, nothing else | Removed the starter-prompt chips + description paragraph that the original v0 empty state shipped with. | Claude / ChatGPT / Gemini all converge on minimal empty states — one sentence and an input. Anything more invents personas the agent doesn't have. Fraunces 40-px sets the editorial register that distinguishes BrandMind from generic chat UIs. |
