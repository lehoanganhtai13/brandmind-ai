"""Sticky bottom InputComposer — unified textarea + inline send button.

Matches ``docs/web_design.md`` § 9.4 (Enter = send / Shift+Enter = newline).
Codex review Finding 6 applied: 1 px low-alpha focus ring, warmer neutral
surface, send button is the only saturated teal element so the action
hierarchy reads cleanly. The composer renders as a single rounded card so
the textarea and the send button feel like one affordance.

Two-way binding mirrors the textarea value into ``BrandMindState.pending_input``;
``debounce_timeout=0`` keeps Reflex's :class:`DebounceInput` wrapper from
caching the in-flight value when the state clears post-send.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens
from .model_picker import model_picker


def _send_disabled() -> rx.Var:
    """Compute whether the send affordance should be inert."""
    return (
        ~BrandMindState.is_connected
        | BrandMindState.is_streaming
        | (BrandMindState.pending_input == "")
    )


def input_composer() -> rx.Component:
    """Sticky composer card containing a textarea and an inline send button."""
    placeholder = rx.cond(
        BrandMindState.is_connected,
        "Message BrandMind — Enter to send, Shift+Enter for newline.",
        "Reconnecting...",
    )

    footer = rx.hstack(
        model_picker(),
        rx.spacer(),
        rx.button(
            rx.icon(tag="arrow_up", size=16),
            on_click=BrandMindState.send_message,
            disabled=_send_disabled(),
            style={
                "background_color": tokens.ACCENT_TEAL_SOLID,
                "color": "#003732",
                "width": "32px",
                "height": "32px",
                "min_width": "32px",
                "padding": "0",
                "border_radius": tokens.RADIUS_PILL,
                "cursor": "pointer",
            },
        ),
        align="center",
        spacing="2",
        padding="6px 10px 10px 12px",
        style={"width": "100%"},
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
                "padding": "14px 18px 6px 18px",
                "resize": "none",
            },
        ),
        footer,
        style={
            "display": "flex",
            "flex_direction": "column",
            "width": "100%",
            "max_width": "880px",
            "margin": "0 auto",
            "background_color": tokens.BG_SURFACE_1,
            "border": f"1px solid {tokens.GLASS_BORDER}",
            "border_radius": tokens.RADIUS_LG,
            "transition": "border-color 160ms ease, box-shadow 160ms ease",
            "_focus_within": {
                "border_color": "rgba(95, 179, 168, 0.45)",
                "box_shadow": "0 0 0 1px rgba(95, 179, 168, 0.20)",
            },
        },
    )

    return rx.box(
        composer_card,
        padding="12px 24px 20px 24px",
        width="100%",
        style={
            "background_color": tokens.BG_CANVAS,
        },
    )
