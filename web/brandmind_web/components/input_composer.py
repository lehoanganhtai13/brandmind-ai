"""Sticky bottom InputComposer — unified textarea + inline send button.

Matches ``docs/web_design.md`` § 9.4 (Enter = send / Shift+Enter = newline).
The composer renders as a single rounded card so the textarea and the send
button read as one affordance rather than two disjointed controls: the
textarea fills the card with a transparent background while the send button
sits inside the bottom-right corner. The card's border picks up the teal
accent on focus-within for a clear active state.

Two-way binding mirrors the textarea value into ``BrandMindState.pending_input``;
``debounce_timeout=0`` keeps Reflex's :class:`DebounceInput` wrapper from
caching the in-flight value when the state clears post-send.
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
    """Sticky composer card containing a textarea and an inline send button."""
    placeholder = rx.cond(
        BrandMindState.is_connected,
        "Nhập tin nhắn — Enter để gửi, Shift+Enter để xuống dòng.",
        "Đang chờ kết nối lại...",
    )

    composer_card = rx.box(
        rx.text_area(
            value=BrandMindState.pending_input,
            placeholder=placeholder,
            on_change=BrandMindState.set_pending_input,
            on_key_down=BrandMindState.on_composer_key_down,
            disabled=~BrandMindState.is_connected | BrandMindState.is_streaming,
            debounce_timeout=0,
            style={
                "width": "100%",
                "min_height": "52px",
                "max_height": "200px",
                "background_color": "transparent",
                "color": tokens.TEXT_PRIMARY,
                "font_family": tokens.FONT_SANS,
                "font_size": "15px",
                "line_height": "1.55",
                "border": "none",
                "outline": "none",
                "box_shadow": "none",
                "padding": "14px 56px 14px 18px",
                "resize": "none",
            },
        ),
        rx.button(
            rx.icon(tag="arrow_up", size=18),
            on_click=BrandMindState.send_message,
            disabled=_send_disabled(),
            style={
                "position": "absolute",
                "right": "10px",
                "bottom": "10px",
                "background_color": tokens.ACCENT_TEAL_SOLID,
                "color": "#003732",
                "width": "36px",
                "height": "36px",
                "min_width": "36px",
                "padding": "0",
                "border_radius": tokens.RADIUS_PILL,
                "cursor": "pointer",
            },
        ),
        style={
            "position": "relative",
            "width": "100%",
            "max_width": "920px",
            "margin": "0 auto",
            "background_color": tokens.BG_SURFACE_2,
            "border": f"1px solid {tokens.GLASS_BORDER}",
            "border_radius": tokens.RADIUS_LG,
            "transition": "border-color 160ms ease, box-shadow 160ms ease",
            "_focus_within": {
                "border_color": tokens.ACCENT_TEAL_SOLID,
                "box_shadow": f"0 0 0 4px {tokens.ACCENT_TEAL_MUTED}",
            },
        },
    )

    return rx.box(
        composer_card,
        padding="16px 24px 20px 24px",
        width="100%",
        style={
            "background_color": tokens.BG_CANVAS,
            "border_top": f"1px solid {tokens.GLASS_BORDER}",
        },
    )
