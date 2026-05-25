"""Header bar for the BrandMind Web UI.

Sticky 56-px top bar split into a sidebar-column zone (wordmark on
the left, panel-toggle pinned to the right edge — matches the
ChatGPT pattern where the toggle lives at the right edge of the
sidebar header rather than the leftmost edge of the global bar) and
a main zone (session caption centred + canvas toggle on the right).
Matches ``docs/web_design.md`` § 9.1 with Codex-review Finding 1
applied: serif wordmark + sentence-case metadata + reserved mono
for code/tool payloads only.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens
from .sidebar import _PHASE_DISPLAY_EN


def _sidebar_toggle() -> rx.Component:
    """Render the sidebar collapse / expand button.

    Uses the chevron-free ``panel_left`` glyph for both states so the
    affordance reads as a friendly panel handle (Gemini / ChatGPT
    pattern) rather than a directional arrow that suggests motion the
    user did not request.
    """
    return rx.button(
        rx.icon(tag="panel_left", size=18),
        on_click=BrandMindState.toggle_sidebar,
        variant="ghost",
        color_scheme="gray",
        aria_label=rx.cond(
            BrandMindState.sidebar_is_collapsed,
            "Open sidebar",
            "Close sidebar",
        ),
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


def _canvas_toggle() -> rx.Component:
    """Header button that toggles the canvas drawer.

    Surfaces a top-right notification badge over the icon only when
    the session has artifacts the user has not yet acknowledged AND
    the canvas drawer is closed. Acknowledgement is tracked through
    ``BrandMindState.artifacts_seen_count`` (see
    :meth:`BrandMindState.toggle_canvas` for the snapshot rule on
    close), so opening the canvas once dismisses the pip and it
    re-appears only when a NEW artifact arrives — matching the
    Slack / iMessage / GitHub-bell "unread content waiting" mental
    model rather than a static "files exist" indicator. Connection
    state has no header counterpart here: ``degraded_banner`` already
    surfaces the loud-error case and the composer disables itself
    when offline, so a permanent "Connected" pill would be pure
    happy-path noise.
    """
    show_badge = BrandMindState.has_unseen_artifacts & ~BrandMindState.canvas_open
    return rx.button(
        rx.box(
            rx.icon(tag="panel_right", size=18),
            rx.cond(
                show_badge,
                rx.box(
                    style={
                        "position": "absolute",
                        "top": "-3px",
                        "right": "-3px",
                        "width": "9px",
                        "height": "9px",
                        "border_radius": tokens.RADIUS_PILL,
                        "background_color": tokens.ACCENT_TEAL_SOLID,
                        "box_shadow": (
                            f"0 0 0 2px {tokens.GLASS_BG_SUBTLE}, "
                            "0 0 8px rgba(95, 179, 168, 0.45)"
                        ),
                        "pointer_events": "none",
                    },
                ),
                rx.fragment(),
            ),
            style={
                "position": "relative",
                "display": "inline-flex",
                "align_items": "center",
                "justify_content": "center",
                "width": "20px",
                "height": "20px",
            },
        ),
        on_click=BrandMindState.toggle_canvas,
        variant="ghost",
        color_scheme="gray",
        aria_label=rx.cond(
            show_badge,
            "Toggle files canvas — new files available",
            "Toggle files canvas",
        ),
        style={
            "color": tokens.TEXT_SECONDARY,
            "width": "36px",
            "height": "36px",
            "padding": "0",
            "border_radius": tokens.RADIUS_SM,
        },
    )


def header() -> rx.Component:
    """Sticky top bar matching docs/web_design.md § 9.1.

    The bar splits into two zones: the leftmost cluster reserves the
    same column width as the sidebar below (wordmark on the left, toggle
    pinned to the right edge — the ChatGPT pattern from Image #75 where
    the panel handle lives at the right edge of the sidebar header
    rather than the leftmost edge of the global bar). The wordmark
    hides while collapsed so the 56-px rail still has room for the
    toggle alone.
    """
    sidebar_zone = rx.hstack(
        rx.cond(
            BrandMindState.sidebar_is_collapsed,
            rx.fragment(),
            _wordmark(),
        ),
        rx.spacer(),
        _sidebar_toggle(),
        spacing="3",
        align="center",
        style={
            "width": rx.cond(
                BrandMindState.sidebar_is_collapsed,
                f"{tokens.SIDEBAR_COLLAPSED_PX}px",
                f"{tokens.SIDEBAR_EXPANDED_PX}px",
            ),
            "min_width": rx.cond(
                BrandMindState.sidebar_is_collapsed,
                f"{tokens.SIDEBAR_COLLAPSED_PX}px",
                f"{tokens.SIDEBAR_EXPANDED_PX}px",
            ),
            "height": "100%",
            "padding": "0 12px",
            "border_right": f"1px solid {tokens.GLASS_BORDER}",
            "transition": "width 240ms cubic-bezier(0.4, 0, 0.2, 1)",
            "flex_shrink": "0",
        },
    )

    main_zone = rx.hstack(
        rx.spacer(),
        _session_caption(),
        rx.spacer(),
        _canvas_toggle(),
        spacing="3",
        align="center",
        style={
            "flex": "1",
            "min_width": "0",
            "height": "100%",
            "padding": "0 20px",
        },
    )

    return rx.hstack(
        sidebar_zone,
        main_zone,
        spacing="0",
        align="center",
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
