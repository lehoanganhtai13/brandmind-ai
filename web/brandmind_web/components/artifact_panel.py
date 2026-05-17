"""ArtifactPanel — list of session artifacts inside the canvas drawer.

Renders the manifest entries fetched from
``GET /api/v1/sessions/{id}/artifacts`` as a vertical list of rows
keyed by filename. Each row surfaces a category-specific icon, the
filename, the relative generated-at timestamp, and the size; clicking
the row swaps the canvas body to the matching viewer.

Mirrors ``docs/web_design.md`` § 9.5.1.
"""

from __future__ import annotations

import reflex as rx

from ..models import ArtifactRef
from ..state import BrandMindState
from . import tokens

_CATEGORY_ICON_TAGS: dict[str, str] = {
    "images": "image",
    "documents": "file_text",
    "presentations": "presentation",
    "spreadsheets": "table_2",
}

_CATEGORY_LABELS: dict[str, str] = {
    "images": "Brand Key",
    "documents": "Strategy document",
    "presentations": "Executive deck",
    "spreadsheets": "KPI tracker",
}


def _category_icon_tag(category: rx.Var[str] | str) -> str:
    """Return the Lucide icon name for a given artifact category.

    Reflex Var routing means category arrives as a reactive value at
    render time. The mapping must therefore be a plain dict lookup
    with a stable fallback so the component never raises on an
    unexpected category.
    """
    if isinstance(category, str):
        return _CATEGORY_ICON_TAGS.get(category, "file")
    return "file"


def _format_size_bytes(size: int) -> str:
    """Format ``size`` (bytes) as a short ``KB`` / ``MB`` label.

    Args:
        size (int): Byte count from the manifest record.

    Returns:
        label (str): Human-readable size such as ``"38 KB"`` or
        ``"1.2 MB"``.
    """
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size // 1024} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _artifact_row(artifact: ArtifactRef) -> rx.Component:
    """Render one artifact row inside the canvas list.

    The row is a button so keyboard activation works without extra
    affordances; hover state lifts the background by one surface step
    per the design doc § 9.5.1, and the active row shows a teal
    left-border so the user can keep their place when they scrub the
    list with a viewer already open.
    """
    is_active = BrandMindState.active_artifact_filename == artifact.filename
    return rx.button(
        rx.hstack(
            rx.box(
                rx.match(
                    artifact.category,
                    ("images", rx.icon(tag="image", size=18)),
                    ("documents", rx.icon(tag="file_text", size=18)),
                    ("presentations", rx.icon(tag="presentation", size=18)),
                    ("spreadsheets", rx.icon(tag="table_2", size=18)),
                    rx.icon(tag="file", size=18),
                ),
                style={
                    "color": tokens.ACCENT_TEAL_SOLID,
                    "flex": "0 0 auto",
                    "padding_top": "2px",
                },
            ),
            rx.vstack(
                rx.text(
                    artifact.filename,
                    style={
                        "color": tokens.TEXT_PRIMARY,
                        "font_family": tokens.FONT_SANS,
                        "font_size": "13px",
                        "font_weight": "500",
                        "line_height": "1.35",
                        "overflow": "hidden",
                        "text_overflow": "ellipsis",
                        "white_space": "nowrap",
                        "width": "100%",
                    },
                ),
                rx.hstack(
                    rx.text(
                        rx.match(
                            artifact.category,
                            ("images", "Brand Key"),
                            ("documents", "Strategy document"),
                            ("presentations", "Executive deck"),
                            ("spreadsheets", "KPI tracker"),
                            "File",
                        ),
                        style={
                            "color": tokens.TEXT_MUTED,
                            "font_family": tokens.FONT_SANS,
                            "font_size": "11px",
                            "letter_spacing": "0.04em",
                            "text_transform": "uppercase",
                        },
                    ),
                    rx.text(
                        "·",
                        style={
                            "color": tokens.TEXT_MUTED,
                            "font_size": "11px",
                        },
                    ),
                    rx.text(
                        artifact.size_label,
                        style={
                            "color": tokens.TEXT_MUTED,
                            "font_family": tokens.FONT_SANS,
                            "font_size": "11px",
                        },
                    ),
                    spacing="2",
                    align="center",
                ),
                spacing="1",
                align="start",
                flex="1",
                min_width="0",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        on_click=BrandMindState.select_artifact(artifact.filename),
        variant="ghost",
        style={
            "width": "100%",
            "padding": "12px 14px",
            "border_radius": tokens.RADIUS_MD,
            "border": rx.cond(
                is_active,
                f"1px solid {tokens.ACCENT_TEAL_SOLID}",
                f"1px solid {tokens.GLASS_BORDER}",
            ),
            "background_color": rx.cond(
                is_active,
                tokens.ACCENT_TEAL_MUTED,
                "transparent",
            ),
            "transition": "background-color 120ms ease, border-color 120ms ease",
            "cursor": "pointer",
            "height": "auto",
            "_hover": {
                "background_color": tokens.BG_SURFACE_2,
            },
        },
    )


def artifact_panel() -> rx.Component:
    """Vertical list of artifacts inside the canvas drawer.

    Renders an empty-state hint when the session has produced nothing
    yet so first-time users see a clear "Why is this pane empty?"
    explanation. Otherwise hands off to :func:`_artifact_row` for each
    manifest entry.
    """
    empty = rx.center(
        rx.vstack(
            rx.icon(
                tag="package_open",
                size=28,
                color=tokens.TEXT_MUTED,
            ),
            rx.text(
                "No files yet",
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "14px",
                    "font_weight": "500",
                },
            ),
            rx.text(
                "Once the agent finishes Phase 5 it will produce a "
                "Brand Key image, strategy document, executive deck "
                "and KPI tracker — they'll appear here.",
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "12px",
                    "line_height": "1.5",
                    "max_width": "260px",
                    "text_align": "center",
                },
            ),
            spacing="3",
            align="center",
        ),
        padding="40px 24px",
        flex="1",
        width="100%",
    )
    rows = rx.vstack(
        rx.foreach(
            BrandMindState.artifacts,
            _artifact_row,
        ),
        spacing="2",
        align="stretch",
        padding="16px",
        width="100%",
    )
    return rx.cond(BrandMindState.has_artifacts, rows, empty)
