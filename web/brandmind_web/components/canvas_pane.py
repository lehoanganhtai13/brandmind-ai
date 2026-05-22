"""CanvasPane — side-by-side workspace viewer that cohabits the chat.

The pane mounts as a flex sibling of the chat column inside the main
hstack and animates its width between 0 (closed) and ``min(720px,
50%)`` (open). The inner stack switches between two modes based on
whether an artifact is selected: list mode shows the full-width file
roster, viewer mode shows the rendered artifact. The list ↔ viewer
swap mirrors the Claude Cowork pattern so the user always sees the
content surface at its natural width instead of competing for space
inside a two-column split.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens
from .artifact_panel import artifact_panel
from .artifact_viewer import artifact_viewer

_HEADER_ICON_BUTTON = {
    "color": tokens.TEXT_SECONDARY,
    "background_color": "transparent",
    "padding": "8px",
    "border_radius": tokens.RADIUS_MD,
    "cursor": "pointer",
    "_hover": {
        "background_color": tokens.BG_SURFACE_2,
        "color": tokens.TEXT_PRIMARY,
    },
}


def _list_mode_header() -> rx.Component:
    """Header when the canvas is in the file-list mode."""
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
                "Brand-strategy deliverables for this session.",
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "12px",
                    "line_height": "1.4",
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
            style=_HEADER_ICON_BUTTON,
        ),
        spacing="3",
        align="center",
        padding="14px 18px",
        width="100%",
        style={
            "border_bottom": f"1px solid {tokens.GLASS_BORDER}",
            "background_color": tokens.GLASS_BG_ELEVATED,
            "backdrop_filter": "blur(18px)",
            "flex": "0 0 auto",
        },
    )


def _viewer_mode_header() -> rx.Component:
    """Header when the canvas is in the file-viewer mode.

    Mirrors the Claude Cowork pattern: a back chevron returns to the
    file list, the active filename centers as the document title, and
    the X closes the whole canvas. The back action is the primary
    affordance — it keeps the user inside the workspace surface; X is
    reserved for dismissing the panel entirely.
    """
    return rx.hstack(
        rx.button(
            rx.icon(tag="arrow-left", size=18),
            on_click=BrandMindState.back_to_artifact_list,
            variant="ghost",
            aria_label="Back to files",
            style=_HEADER_ICON_BUTTON,
        ),
        rx.text(
            BrandMindState.active_artifact_filename,
            style={
                "color": tokens.TEXT_PRIMARY,
                "font_family": tokens.FONT_SANS,
                "font_size": "14px",
                "font_weight": "500",
                "letter_spacing": "-0.005em",
                "line_height": "1.4",
                "overflow": "hidden",
                "text_overflow": "ellipsis",
                "white_space": "nowrap",
                "flex": "1",
                "min_width": "0",
            },
        ),
        rx.button(
            rx.icon(tag="x", size=18),
            on_click=BrandMindState.close_canvas,
            variant="ghost",
            aria_label="Close canvas",
            style=_HEADER_ICON_BUTTON,
        ),
        spacing="3",
        align="center",
        padding="12px 14px",
        width="100%",
        style={
            "border_bottom": f"1px solid {tokens.GLASS_BORDER}",
            "background_color": tokens.GLASS_BG_ELEVATED,
            "backdrop_filter": "blur(18px)",
            "flex": "0 0 auto",
        },
    )


def _drawer_header() -> rx.Component:
    """Sticky header that switches shape between list and viewer modes.

    List mode renders the "Files" title plus a close button. Viewer
    mode swaps in the back-arrow + active filename + close button so
    the user can return to the list without dismissing the canvas.
    """
    return rx.cond(
        BrandMindState.active_artifact_filename != "",
        _viewer_mode_header(),
        _list_mode_header(),
    )


def _drawer_body() -> rx.Component:
    """Single-pane body that swaps between list mode and viewer mode.

    Claude-Cowork pattern: while no file is selected, the file list
    occupies the entire canvas pane width. The moment the user clicks
    a row, the list is replaced by the file viewer, giving the rendered
    content (Brand Key image / strategy DOCX / PPTX / KPI XLSX) the
    full panel space. The back-arrow in the header returns to list
    mode without closing the canvas.
    """
    return rx.box(
        rx.cond(
            BrandMindState.active_artifact_filename != "",
            artifact_viewer(),
            artifact_panel(),
        ),
        style={
            "flex": "1",
            "min_width": "0",
            "min_height": "0",
            "width": "100%",
            "height": "100%",
            "display": "flex",
            "flex_direction": "column",
            "background_color": rx.cond(
                BrandMindState.active_artifact_filename != "",
                tokens.BG_CANVAS,
                tokens.BG_SURFACE_1,
            ),
            "overflow_y": "auto",
            "overflow_x": "hidden",
        },
    )


def canvas_pane() -> rx.Component:
    """Side-by-side workspace viewer that cohabits the chat column.

    Mounts as a flex sibling of the chat column inside the page's main
    horizontal row. When closed, the panel collapses its width to ``0``;
    when open, it expands to ``CANVAS_DRAWER_PX`` (with a 360 px min and
    a 60% max so chat is never starved). The inner stack always stays
    in the DOM at its natural width and is clipped by ``overflow:
    hidden`` on the collapsing container — that keeps the open/close
    transition smooth even though the content's intrinsic size doesn't
    change. The chat column carries ``flex: 1; min-width: 0`` so it
    absorbs the squeeze as the canvas appears.

    The Claude Cowork-style cohabitation removes the modal scrim — both
    panels are interactive at the same time. The X button in the canvas
    header remains the only dismiss affordance.
    """
    return rx.box(
        rx.box(
            rx.vstack(
                _drawer_header(),
                _drawer_body(),
                spacing="0",
                align="stretch",
                width="100%",
                height="100%",
            ),
            style={
                "width": f"{tokens.CANVAS_DRAWER_PX}px",
                "min_width": "360px",
                "max_width": "100%",
                "height": "100%",
                "display": "flex",
                "flex_direction": "column",
                "background_color": tokens.GLASS_BG_ELEVATED,
                "backdrop_filter": "blur(22px) saturate(140%)",
                "border_left": f"1px solid {tokens.GLASS_BORDER}",
                "box_shadow": tokens.SHADOW_DRAWER,
            },
        ),
        style={
            "width": rx.cond(
                BrandMindState.canvas_open,
                f"min({tokens.CANVAS_DRAWER_PX}px, 50%)",
                "0",
            ),
            "min_width": rx.cond(BrandMindState.canvas_open, "360px", "0"),
            "max_width": "60%",
            "height": "100%",
            "overflow": "hidden",
            "flex_shrink": "0",
            "transition": (
                f"width {tokens.DRAWER_DURATION_MS}ms "
                f"{tokens.DRAWER_EASING}, "
                f"min-width {tokens.DRAWER_DURATION_MS}ms "
                f"{tokens.DRAWER_EASING}"
            ),
        },
    )
