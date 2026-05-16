"""Inline tool-call timeline card.

Renders one entry inside an agent message body for each tool call the
agent dispatches. Matches ``docs/web_design.md`` § 9.3.4 — tool icon,
tool name in mono, optional argument preview, status pill (running /
completed). Cards are inline with the message body rather than in a
separate panel so the chat reads as a single chronological strip.
"""

from __future__ import annotations

import reflex as rx

from ..models import ToolCallInfo
from . import tokens


def tool_call_card(call: rx.Var[ToolCallInfo]) -> rx.Component:
    """Render one inline timeline card for a single tool call.

    Args:
        call: Reflex var pointing at a :class:`ToolCallInfo`. The card
            re-renders when the underlying ``result`` field flips from
            empty (running) to non-empty (completed).

    Returns:
        component (rx.Component): A horizontal pill with tool name +
        status indicator.
    """
    is_done = call.result != ""

    return rx.hstack(
        rx.icon(
            tag=rx.cond(is_done, "circle_check", "loader"),
            size=14,
            color=rx.cond(is_done, tokens.ACCENT_TEAL_SOLID, tokens.TEXT_MUTED),
        ),
        rx.text(
            call.tool_name,
            style={
                "color": tokens.ACCENT_TEAL_SOLID,
                "font_family": tokens.FONT_MONO,
                "font_size": "12px",
            },
        ),
        rx.text(
            rx.cond(is_done, "completed", "running"),
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_MONO,
                "font_size": "11px",
            },
        ),
        spacing="2",
        align="center",
        padding="6px 10px",
        style={
            "background_color": tokens.BG_SURFACE_2,
            "border_radius": tokens.RADIUS_PILL,
            "border": f"1px solid {tokens.GLASS_BORDER}",
            "width": "fit-content",
        },
    )
