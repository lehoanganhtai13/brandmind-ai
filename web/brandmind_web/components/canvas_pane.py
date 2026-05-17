"""CanvasPane — slide-in drawer hosting the artifact list and inline viewer.

The drawer mounts as a fixed-position layer on the right edge of the
viewport so it overlays the chat instead of resizing it — the chat
scroll never reflows when the drawer opens or closes, which keeps
streaming tokens smooth. Glass-on-backdrop styling per
``docs/web_design.md`` § 7.1; slide animation per § 10
(280 ms cubic-bezier).

The drawer keeps an "open" mode (transform: translateX(0)) and a
closed mode (transform: translateX(100%)) so the React tree stays
mounted across toggles, eliminating remount jank.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens
from .artifact_panel import artifact_panel
from .artifact_viewer import artifact_viewer


def _drawer_header() -> rx.Component:
    """Sticky header inside the canvas drawer — title + close button."""
    return rx.hstack(
        rx.vstack(
            rx.text(
                "Files",
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_DISPLAY,
                    "font_size": "18px",
                    "font_weight": "500",
                    "letter_spacing": "-0.005em",
                },
            ),
            rx.text(
                rx.cond(
                    BrandMindState.active_artifact_filename != "",
                    BrandMindState.active_artifact_filename,
                    "Brand-strategy deliverables for this session.",
                ),
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "12px",
                    "line_height": "1.4",
                    "overflow": "hidden",
                    "text_overflow": "ellipsis",
                    "white_space": "nowrap",
                    "max_width": "440px",
                },
            ),
            spacing="1",
            align="start",
            flex="1",
            min_width="0",
        ),
        rx.button(
            rx.icon(tag="x", size=18),
            on_click=BrandMindState.close_canvas,
            variant="ghost",
            aria_label="Close canvas",
            style={
                "color": tokens.TEXT_SECONDARY,
                "background_color": "transparent",
                "padding": "8px",
                "border_radius": tokens.RADIUS_MD,
                "cursor": "pointer",
                "_hover": {
                    "background_color": tokens.BG_SURFACE_2,
                    "color": tokens.TEXT_PRIMARY,
                },
            },
        ),
        spacing="3",
        align="start",
        padding="14px 18px",
        width="100%",
        style={
            "border_bottom": f"1px solid {tokens.GLASS_BORDER}",
            "background_color": tokens.GLASS_BG_ELEVATED,
            "backdrop_filter": "blur(18px)",
            "flex": "0 0 auto",
        },
    )


def _drawer_body() -> rx.Component:
    """Two-column body — list on the left, viewer on the right.

    The list column has a fixed width so the viewer stays the
    "content surface" the user reads from. When no artifact is active
    the viewer shows its empty-state hint; once the user clicks a
    row the viewer swaps in the category-specific render.
    """
    return rx.hstack(
        rx.box(
            artifact_panel(),
            style={
                "width": "260px",
                "flex": "0 0 260px",
                "border_right": f"1px solid {tokens.GLASS_BORDER}",
                "background_color": tokens.BG_SURFACE_1,
                "overflow_y": "auto",
                "height": "100%",
            },
        ),
        rx.box(
            artifact_viewer(),
            style={
                "flex": "1",
                "min_width": "0",
                "height": "100%",
                "display": "flex",
                "flex_direction": "column",
                "background_color": tokens.BG_CANVAS,
            },
        ),
        spacing="0",
        align="stretch",
        flex="1",
        width="100%",
        style={
            "min_height": "0",
        },
    )


def canvas_pane() -> rx.Component:
    """Fixed-position right-side drawer hosting the artifact UI.

    Renders unconditionally (so the React tree stays mounted across
    open/close cycles); the ``transform`` CSS controls whether the
    drawer sits onscreen. A semi-transparent backdrop fades in behind
    the drawer when open so the user gets a quick way to dismiss it
    via clicking outside.
    """
    backdrop = rx.box(
        on_click=BrandMindState.close_canvas,
        style={
            "position": "fixed",
            "top": "0",
            "left": "0",
            "right": "0",
            "bottom": "0",
            "background_color": "rgba(0, 0, 0, 0.32)",
            "opacity": rx.cond(BrandMindState.canvas_open, "1", "0"),
            "pointer_events": rx.cond(
                BrandMindState.canvas_open, "auto", "none"
            ),
            "transition": (
                f"opacity {tokens.DRAWER_DURATION_MS}ms {tokens.DRAWER_EASING}"
            ),
            "z_index": "40",
        },
    )
    drawer = rx.box(
        rx.vstack(
            _drawer_header(),
            _drawer_body(),
            spacing="0",
            align="stretch",
            width="100%",
            height="100%",
        ),
        style={
            "position": "fixed",
            "top": "0",
            "right": "0",
            "bottom": "0",
            "width": f"{tokens.CANVAS_DRAWER_PX}px",
            "max_width": "92vw",
            "background_color": tokens.GLASS_BG_ELEVATED,
            "backdrop_filter": "blur(22px) saturate(140%)",
            "border_left": f"1px solid {tokens.GLASS_BORDER}",
            "box_shadow": tokens.SHADOW_DRAWER,
            "transform": rx.cond(
                BrandMindState.canvas_open,
                "translateX(0)",
                "translateX(100%)",
            ),
            "transition": (
                f"transform {tokens.DRAWER_DURATION_MS}ms "
                f"{tokens.DRAWER_EASING}"
            ),
            "z_index": "50",
            "display": "flex",
            "flex_direction": "column",
        },
    )
    return rx.fragment(backdrop, drawer)
