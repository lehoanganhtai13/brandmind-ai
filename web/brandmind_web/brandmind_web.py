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
    TEXT_PRIMARY,
)
from .state import BrandMindState

_GLOBAL_KEYFRAMES = """
@keyframes bm-blink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0; }
}
@keyframes bm-empty-reveal {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
"""


def index() -> rx.Component:
    """Root page: Header + (Sidebar | ChatPane).

    Layout is a stacked column: a sticky header on top, an optional
    error banner, and a horizontal row that splits the remaining
    viewport between the sidebar and the chat column.
    """
    return rx.vstack(
        rx.html(f"<style>{_GLOBAL_KEYFRAMES}</style>"),
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
    stylesheets=[
        "https://fonts.googleapis.com/css2?"
        "family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500;9..144,600&"
        "family=Geist:wght@400;500;600&"
        "family=Manrope:wght@400;500;600;700&"
        "family=JetBrains+Mono:wght@400;500&display=swap",
    ],
)
app.add_page(index, title="BrandMind")
