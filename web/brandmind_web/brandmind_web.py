"""BrandMind web UI — Reflex entry point.

Wires the application state and registers the root page. Phase 4
lands the full Header + collapsible PhaseProgressSidebar + ChatPane
layout with streaming chat. The Canvas pane and artifact rendering
land in Task #92.
"""

from __future__ import annotations

import reflex as rx

from .components.canvas_pane import canvas_pane
from .components.chat_pane import chat_pane
from .components.degraded_banner import degraded_banner
from .components.header import header
from .components.onboarding_dialog import onboarding_dialog
from .components.settings_dialog import settings_dialog
from .components.sidebar import chat_action_dialogs, phase_progress_sidebar
from .components.tokens import (
    BG_SURFACE_1,
    FONT_SANS,
    RAIL_HOVER_BG,
    TEXT_PRIMARY,
)
from .state import BrandMindState

_GLOBAL_KEYFRAMES = f"""
@keyframes bm-blink {{
  0%, 49% {{ opacity: 1; }}
  50%, 100% {{ opacity: 0; }}
}}
@keyframes bm-empty-reveal {{
  from {{ opacity: 0; transform: translateY(8px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}
.rt-TextAreaRoot:has([data-bm-composer-textarea]:where(:disabled, :read-only)) {{
  background-image: none !important;
  box-shadow: none !important;
  background-color: transparent !important;
}}
[data-bm-composer-textarea]:where(:disabled, :read-only) {{
  color: var(--gray-a11) !important;
  -webkit-text-fill-color: var(--gray-a11) !important;
  cursor: text !important;
}}
[data-bm-sidebar-brand]:hover {{
  background-color: {RAIL_HOVER_BG} !important;
}}
[data-bm-sidebar-brand]:hover [data-bm-logo-rest] {{
  opacity: 0;
}}
[data-bm-sidebar-brand]:hover [data-bm-logo-hover] {{
  opacity: 1;
}}
#bm-rail-tooltip-pill {{
  position: fixed;
  background-color: #eceeed;
  color: #101211;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 16px;
  font-family: var(--default-font-family);
  font-weight: 400;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 120ms ease;
  z-index: 100;
  top: 0;
  left: 0;
  transform: translate3d(-9999px, -9999px, 0);
}}
#bm-rail-tooltip-pill::before {{
  content: "";
  position: absolute;
  right: 100%;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-right: 5px solid #eceeed;
}}
#bm-rail-tooltip-pill[data-visible="true"] {{
  opacity: 1;
}}
"""

# Body-portal controller for `[data-bm-rail-tooltip]`. Rail buttons that act
# as Radix Popover triggers cannot use `rx.tooltip` (two Slot wrappers on one
# button collide — Tooltip wins data-state, Popover loses onClick), so the
# tooltip pill lives as a single body-level element controlled from JS.
_RAIL_TOOLTIP_SCRIPT = """
(function() {
  if (window.__bmRailTooltipInit) return;
  window.__bmRailTooltipInit = true;
  const pill = document.createElement('div');
  pill.id = 'bm-rail-tooltip-pill';
  document.body.appendChild(pill);
  let timer = null;
  let activeBtn = null;
  function hide() {
    clearTimeout(timer);
    timer = null;
    pill.dataset.visible = 'false';
    pill.style.transform = 'translate3d(-9999px, -9999px, 0)';
    activeBtn = null;
  }
  function place(btn) {
    const r = btn.getBoundingClientRect();
    pill.textContent = btn.getAttribute('data-bm-rail-tooltip') || '';
    const x = r.right + 13;
    const y = r.top + r.height / 2;
    pill.style.transform = 'translate3d(' + x + 'px, calc(' + y + 'px - 50%), 0)';
    pill.dataset.visible = 'true';
  }
  document.addEventListener('pointerover', function(e) {
    const btn = e.target.closest('[data-bm-rail-tooltip]');
    if (!btn) return;
    if (btn === activeBtn) return;
    activeBtn = btn;
    clearTimeout(timer);
    timer = setTimeout(function() {
      if (activeBtn === btn) place(btn);
    }, 280);
  }, true);
  document.addEventListener('pointerout', function(e) {
    const btn = e.target.closest('[data-bm-rail-tooltip]');
    if (!btn) return;
    const next = e.relatedTarget;
    if (next && btn.contains(next)) return;
    hide();
  }, true);
  document.addEventListener('pointerdown', hide, true);
})();
"""


def index() -> rx.Component:
    """Root page: Header + (Sidebar | ChatPane).

    Layout is a stacked column: a sticky header on top, an optional
    error banner, and a horizontal row that splits the remaining
    viewport between the sidebar and the chat column.
    """
    return rx.vstack(
        rx.html(f"<style>{_GLOBAL_KEYFRAMES}</style>"),
        rx.script(_RAIL_TOOLTIP_SCRIPT),
        chat_action_dialogs(),
        settings_dialog(),
        onboarding_dialog(),
        header(),
        degraded_banner(),
        rx.hstack(
            phase_progress_sidebar(),
            chat_pane(),
            canvas_pane(),
            spacing="0",
            align="stretch",
            style={
                "flex": "1",
                "min_height": "0",
                "width": "100%",
            },
        ),
        spacing="0",
        align="stretch",
        width="100vw",
        height="100vh",
        style={
            "background_color": BG_SURFACE_1,
            "color": TEXT_PRIMARY,
            "overflow": "hidden",
        },
        on_mount=[
            BrandMindState.normalize_timeline_text,
            BrandMindState.initialize_app,
            BrandMindState.poll_health,
        ],
    )


app = rx.App(
    style={
        "background_color": BG_SURFACE_1,
        "color": TEXT_PRIMARY,
        "font_family": FONT_SANS,
    },
    head_components=[
        rx.el.link(rel="icon", type="image/png", href="/brandmind-favicon.png"),
        rx.el.link(
            rel="apple-touch-icon",
            href="/brandmind-favicon.png",
        ),
    ],
    stylesheets=[
        "https://fonts.googleapis.com/css2?"
        "family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500;9..144,600&"
        "family=Geist:wght@400;500;600&"
        "family=Manrope:wght@400;500;600;700&"
        "family=JetBrains+Mono:wght@400;500&display=swap",
    ],
)
app.add_page(index, title="BrandMind")
