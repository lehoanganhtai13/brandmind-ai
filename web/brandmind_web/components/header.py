"""Header bar for the BrandMind Web UI.

Sticky 56-px top bar with the sidebar toggle on the leftmost edge, the
BrandMind wordmark, the session caption, and the connection indicator
on the right. Matches ``docs/web_design.md`` § 9.1.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens


def _sidebar_toggle() -> rx.Component:
    """Render the sidebar collapse / expand button.

    The icon name flips between ``panel-left-close`` (when the sidebar
    is expanded) and ``panel-left-open`` (when collapsed) so the icon
    direction always reflects the action the click will perform.
    """
    return rx.button(
        rx.cond(
            BrandMindState.sidebar_is_collapsed,
            rx.icon(tag="panel_left_open", size=20),
            rx.icon(tag="panel_left_close", size=20),
        ),
        on_click=BrandMindState.toggle_sidebar,
        variant="ghost",
        color_scheme="gray",
        style={
            "color": tokens.TEXT_SECONDARY,
            "width": "40px",
            "height": "40px",
            "padding": "0",
            "border_radius": tokens.RADIUS_SM,
        },
    )


def _wordmark() -> rx.Component:
    """Brand wordmark in teal small-caps."""
    return rx.text(
        "BRANDMIND",
        style={
            "color": tokens.ACCENT_TEAL_SOLID,
            "font_family": tokens.FONT_MONO,
            "font_size": "13px",
            "font_weight": "600",
            "letter_spacing": "0.08em",
        },
    )


def _session_caption() -> rx.Component:
    """Mid-bar caption — brand name + current phase label when classified.

    The caption is intentionally blank until the backend classifies the
    scope. The raw ``phase_0`` ID is not a user-meaningful label, so
    the phase suffix only renders once ``phase_display_labels`` has
    been populated (i.e. ``BrandMindState.scope`` is non-empty).
    """
    return rx.hstack(
        rx.cond(
            BrandMindState.brand_name != "",
            rx.text(
                BrandMindState.brand_name,
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "14px",
                    "font_weight": "500",
                },
            ),
            rx.fragment(),
        ),
        rx.cond(
            BrandMindState.scope != "",
            rx.text(
                rx.cond(BrandMindState.brand_name != "", "· ", "")
                + BrandMindState.phase_display_labels.get(
                    BrandMindState.current_phase,
                    "",
                ),
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "14px",
                },
            ),
            rx.fragment(),
        ),
        spacing="2",
        align="center",
    )


def _connection_indicator() -> rx.Component:
    """Right-side connection dot — teal when connected, grey when not."""
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
            rx.cond(BrandMindState.is_connected, "CONNECTED", "OFFLINE"),
            style={
                "color": rx.cond(
                    BrandMindState.is_connected,
                    tokens.ACCENT_TEAL_SOLID,
                    tokens.TEXT_MUTED,
                ),
                "font_family": tokens.FONT_MONO,
                "font_size": "11px",
                "font_weight": "500",
                "letter_spacing": "0.08em",
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
        padding_x="16px",
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
