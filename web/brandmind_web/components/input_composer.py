"""Sticky bottom InputComposer — textarea + send button.

Matches ``docs/web_design.md`` § 9.4. Two-way binding mirrors the
textarea value into ``BrandMindState.pending_input``; the send button
dispatches ``BrandMindState.send_message``. The composer disables
itself while a turn is streaming or when the backend is unreachable
so the user does not queue an in-flight request twice.

Note: Enter-to-send is intentionally NOT bound in v1. Reflex's text
area treats Enter as newline by default and overriding requires
JS-side keydown handling that adds complexity for marginal benefit at
this layer. The Send button is the canonical submit path.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens


def _send_disabled() -> rx.Var:
    """Compute whether the send affordance should be inert.

    Inert when:
    * the backend is unreachable (no point queuing),
    * a turn is already streaming,
    * the textarea is empty after trim.
    """
    return (
        ~BrandMindState.is_connected
        | BrandMindState.is_streaming
        | (BrandMindState.pending_input == "")
    )


def input_composer() -> rx.Component:
    """Sticky composer with multi-line textarea + send button."""
    placeholder = rx.cond(
        BrandMindState.is_connected,
        "Nhập tin nhắn...",
        "Đang chờ kết nối lại...",
    )

    return rx.hstack(
        rx.text_area(
            value=BrandMindState.pending_input,
            placeholder=placeholder,
            on_change=BrandMindState.set_pending_input,
            disabled=~BrandMindState.is_connected | BrandMindState.is_streaming,
            rows="2",
            auto_height=True,
            style={
                "flex": "1",
                "background_color": tokens.BG_SURFACE_2,
                "color": tokens.TEXT_PRIMARY,
                "font_family": tokens.FONT_SANS,
                "font_size": "15px",
                "border": f"1px solid {tokens.GLASS_BORDER}",
                "border_radius": tokens.RADIUS_MD,
                "padding": "12px",
                "resize": "none",
            },
        ),
        rx.button(
            rx.icon(tag="arrow_up", size=20),
            on_click=BrandMindState.send_message,
            disabled=_send_disabled(),
            style={
                "background_color": tokens.ACCENT_TEAL_SOLID,
                "color": "#003732",
                "width": "44px",
                "height": "44px",
                "padding": "0",
                "border_radius": tokens.RADIUS_MD,
                "align_self": "flex-end",
            },
        ),
        spacing="2",
        align="end",
        padding="16px 24px",
        width="100%",
        style={
            "background_color": tokens.BG_CANVAS,
            "border_top": f"1px solid {tokens.GLASS_BORDER}",
        },
    )
