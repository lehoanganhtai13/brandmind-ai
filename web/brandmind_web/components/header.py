"""Header bar for the BrandMind Web UI.

Sticky 56-px top bar with the sidebar toggle on the leftmost edge, the
BrandMind wordmark in the display serif, the session caption, and the
connection indicator on the right. Matches ``docs/web_design.md`` § 9.1
with Codex-review Finding 1 applied: serif wordmark + sentence-case
metadata + reserved mono for code/tool payloads only.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens
from .sidebar import _PHASE_DISPLAY_EN


def _sidebar_toggle() -> rx.Component:
    """Render the sidebar collapse / expand button."""
    return rx.button(
        rx.cond(
            BrandMindState.sidebar_is_collapsed,
            rx.icon(tag="panel_left_open", size=18),
            rx.icon(tag="panel_left_close", size=18),
        ),
        on_click=BrandMindState.toggle_sidebar,
        variant="ghost",
        color_scheme="gray",
        style={
            "color": tokens.TEXT_SECONDARY,
            "width": "36px",
            "height": "36px",
            "padding": "0",
            "border_radius": tokens.RADIUS_SM,
        },
    )


def _wordmark() -> rx.Component:
    """Brand wordmark in the display serif — editorial, not terminal."""
    return rx.text(
        "BrandMind",
        style={
            "color": tokens.TEXT_PRIMARY,
            "font_family": tokens.FONT_DISPLAY,
            "font_size": "20px",
            "font_weight": "500",
            "letter_spacing": "-0.01em",
        },
    )


def _phase_label(phase_key: rx.Var) -> rx.Var:
    """Project a phase id to its English UI label, falling back to the id."""
    label: rx.Var = phase_key
    for key, value in _PHASE_DISPLAY_EN.items():
        label = rx.cond(phase_key == key, value, label)
    return label


def _session_caption() -> rx.Component:
    """Mid-bar caption — brand name + current phase label when classified.

    Hides entirely until the agent has classified the scope; the raw
    ``phase_0`` id was never user-meaningful and floats awkwardly on a
    fresh session.
    """
    return rx.hstack(
        rx.cond(
            BrandMindState.brand_name != "",
            rx.text(
                BrandMindState.brand_name,
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "13px",
                    "font_weight": "500",
                },
            ),
            rx.fragment(),
        ),
        rx.cond(
            BrandMindState.scope != "",
            rx.text(
                rx.cond(BrandMindState.brand_name != "", "·  ", "")
                + _phase_label(BrandMindState.current_phase),
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "13px",
                    "font_style": "italic",
                },
            ),
            rx.fragment(),
        ),
        spacing="2",
        align="center",
    )


def _connection_indicator() -> rx.Component:
    """Right-side connection dot — teal when connected, grey when not.

    Status label rendered in sentence-case sans (Finding 1) so the
    indicator reads as a refined status pill, not a terminal banner.
    """
    return rx.hstack(
        rx.box(
            style={
                "width": "8px",
                "height": "8px",
                "border_radius": tokens.RADIUS_PILL,
                "background_color": rx.cond(
                    BrandMindState.is_connected,
                    tokens.ACCENT_TEAL_SOLID,
                    tokens.TEXT_MUTED,
                ),
            },
        ),
        rx.text(
            rx.cond(BrandMindState.is_connected, "Connected", "Offline"),
            style={
                "color": rx.cond(
                    BrandMindState.is_connected,
                    tokens.ACCENT_TEAL_SOLID,
                    tokens.TEXT_MUTED,
                ),
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
                "font_weight": "500",
                "letter_spacing": "0.01em",
            },
        ),
        spacing="2",
        align="center",
    )


def header() -> rx.Component:
    """Sticky top bar matching docs/web_design.md § 9.1."""
    return rx.hstack(
        _sidebar_toggle(),
        _wordmark(),
        rx.spacer(),
        _session_caption(),
        rx.spacer(),
        _connection_indicator(),
        spacing="3",
        align="center",
        padding_x="20px",
        style={
            "height": f"{tokens.HEADER_HEIGHT_PX}px",
            "min_height": f"{tokens.HEADER_HEIGHT_PX}px",
            "background_color": tokens.GLASS_BG_SUBTLE,
            "backdrop_filter": "blur(20px)",
            "-webkit-backdrop-filter": "blur(20px)",
            "border_bottom": f"1px solid {tokens.GLASS_BORDER}",
            "position": "sticky",
            "top": "0",
            "z_index": "20",
        },
        width="100%",
    )
