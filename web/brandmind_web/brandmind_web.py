"""BrandMind web UI — Reflex entry point.

Wires the application state and registers the root page. Phase 3 lands
the Header + collapsible PhaseProgressSidebar layout (canonical
sidebar implementation matching ``docs/web_design.md`` § 8 + § 9.1 +
§ 9.2). The center chat column stays a placeholder until Phase 4
ships the ChatPane components — that work plugs into the slot left
open in :func:`_chat_placeholder`.
"""

from __future__ import annotations

import reflex as rx

from .components.header import header
from .components.sidebar import phase_progress_sidebar
from .components.tokens import (
    BG_CANVAS,
    BG_SURFACE_1,
    GLASS_BORDER,
    HEADER_HEIGHT_PX,
    STATE_ERROR_BG,
    STATE_ERROR_BORDER,
    STATE_ERROR_FG,
    TEXT_MUTED,
    TEXT_PRIMARY,
)
from .state import BrandMindState


def _error_banner() -> rx.Component:
    """Surface ``BrandMindState.error_message`` as a thin top-of-chat banner."""
    return rx.cond(
        BrandMindState.error_message != "",
        rx.hstack(
            rx.icon(tag="triangle_alert", size=18, color=STATE_ERROR_FG),
            rx.text(
                BrandMindState.error_message,
                style={
                    "color": STATE_ERROR_FG,
                    "font_size": "14px",
                },
            ),
            spacing="2",
            align="center",
            padding="12px 16px",
            style={
                "background_color": STATE_ERROR_BG,
                "border_bottom": f"1px solid {STATE_ERROR_BORDER}",
                "width": "100%",
            },
        ),
        rx.fragment(),
    )


def _chat_placeholder() -> rx.Component:
    """Placeholder centre column until Phase 4 lands ChatPane components.

    Surfaces enough state today to verify Phase 3 visually: session id,
    current phase label, streaming indicator. Phase 4 replaces this
    box with the real chat scroll + InputComposer.
    """
    return rx.center(
        rx.vstack(
            rx.text(
                "Chat pane comes in Task #91 Phase 4",
                style={"color": TEXT_MUTED, "font_size": "14px"},
            ),
            rx.text(
                "Session:",
                style={"color": TEXT_MUTED, "font_size": "12px"},
            ),
            rx.text(
                BrandMindState.session_id,
                style={
                    "color": TEXT_PRIMARY,
                    "font_size": "13px",
                    "font_family": "monospace",
                },
            ),
            rx.text(
                "Current phase:",
                style={"color": TEXT_MUTED, "font_size": "12px"},
            ),
            rx.text(
                BrandMindState.phase_display_labels.get(
                    BrandMindState.current_phase,
                    BrandMindState.current_phase,
                ),
                style={"color": TEXT_PRIMARY, "font_size": "14px"},
            ),
            rx.cond(
                BrandMindState.is_streaming,
                rx.text(
                    "Streaming...",
                    style={"color": TEXT_MUTED, "font_size": "12px"},
                ),
                rx.fragment(),
            ),
            spacing="2",
            align="center",
        ),
        flex="1",
        width="100%",
        style={
            "background_color": BG_CANVAS,
        },
    )


def index() -> rx.Component:
    """Root page: Header + (Sidebar | ChatPane placeholder).

    Layout is a stacked column: a sticky header on top, a horizontal
    flex row below that splits the remaining viewport between the
    sidebar and the chat column. Phase 4 fills the chat column.
    """
    return rx.vstack(
        header(),
        _error_banner(),
        rx.hstack(
            phase_progress_sidebar(),
            _chat_placeholder(),
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
            BrandMindState.initialize_session,
            BrandMindState.poll_health,
        ],
    )


app = rx.App(
    style={
        "background_color": BG_SURFACE_1,
        "color": TEXT_PRIMARY,
    },
)
app.add_page(index, title="BrandMind")


_ = HEADER_HEIGHT_PX  # token re-export — referenced by future layout polish
_ = GLASS_BORDER
