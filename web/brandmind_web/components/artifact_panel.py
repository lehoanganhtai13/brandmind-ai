"""ArtifactPanel — list of session artifacts inside the canvas drawer.

Renders the manifest entries fetched from
``GET /api/v1/sessions/{id}/artifacts`` as a vertical list of rows
keyed by filename. Each row surfaces a category-specific icon, the
filename, the relative generated-at timestamp, and the size; clicking
the row body swaps the canvas to the matching viewer, while a small
download icon button on the right of each row triggers a native
download without opening the viewer (per-row affordance so the user
never has to dig through a viewer to grab the file).

Mirrors ``docs/web_design.md`` § 9.5.1.
"""

from __future__ import annotations

import reflex as rx

from ..models import ArtifactRef
from ..state import BrandMindState, _api_base_url
from . import tokens

_API_BASE = _api_base_url()

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


def _download_href(download_url: rx.Var[str] | str) -> rx.Var[str] | str:
    """Build the absolute URL that forces a download regardless of category.

    Appends ``?disposition=attachment`` to the artifact endpoint so
    the server returns ``Content-Disposition: attachment`` even for
    categories that default to ``inline`` (currently images). Because
    the web UI page (``8501``) and the FastAPI server (``8000``) live
    on different origins, the browser is cross-origin to the artifact
    response and silently strips the HTML5 ``download`` attribute from
    the anchor — making the server's ``Content-Disposition`` header
    the only mechanism that can reliably trigger a download.

    The helper assumes the manifest's ``download_url`` does not
    already carry a query string. This holds today: the manifest
    schema emits paths shaped like
    ``/api/v1/artifacts/{session_id}/{filename}`` with no query. A
    safer ``"?" vs "&"`` join would require a Reflex
    ``Var.contains("?")`` branch because ``download_url`` arrives as a
    reactive Var at render time and Python-level string operations on
    a Var evaluate at component-build time when the actual value is
    unknown. If the manifest schema ever grows query params (signed
    URLs, cache busters), update this helper to use
    ``rx.cond(download_url.contains("?"), "&", "?")`` for the
    separator and adjust the return type.

    Args:
        download_url (rx.Var[str] | str): The server-relative artifact
            path from the manifest record
            (``ArtifactRef.download_url``). Accepted both as a Reflex
            Var (from ``rx.foreach`` item attributes) and as a plain
            ``str`` (so unit tests can call the helper directly).

    Returns:
        href (rx.Var[str] | str): Absolute URL with the disposition
            override appended, ready to use as an ``<a href>`` value.
            The concrete type mirrors the input — Var in, Var out;
            str in, str out.
    """
    return _API_BASE + download_url + "?disposition=attachment"


def _row_download_button(artifact: ArtifactRef) -> rx.Component:
    """Trailing download chip on an artifact row.

    Implemented as a raw anchor (``rx.el.a``) so the ``download`` HTML
    attribute reaches the rendered tag — harmless cross-origin (it is
    silently ignored, see :func:`_download_href`) and load-bearing in
    the same-origin future where it sets the suggested filename for
    the save-as dialog. The cross-origin-safe path is the server's
    ``Content-Disposition: attachment`` header, triggered via the
    ``?disposition=attachment`` query param appended by
    :func:`_download_href`. ``on_click=rx.stop_propagation`` keeps the
    row's parent ``on_click`` from firing in parallel so the user
    grabs the file without detouring through the artifact viewer.
    """
    return rx.tooltip(
        rx.el.a(
            rx.icon(tag="download", size=16),
            href=_download_href(artifact.download_url),
            download=artifact.filename,
            on_click=rx.stop_propagation,
            aria_label="Download " + artifact.filename,
            style={
                "display": "inline-flex",
                "align_items": "center",
                "justify_content": "center",
                "width": "32px",
                "height": "32px",
                "flex": "0 0 auto",
                "border_radius": tokens.RADIUS_MD,
                "color": tokens.TEXT_MUTED,
                "background_color": "transparent",
                "text_decoration": "none",
                "cursor": "pointer",
                "transition": "background-color 120ms ease, color 120ms ease",
                "_hover": {
                    "background_color": tokens.BG_SURFACE_2,
                    "color": tokens.ACCENT_TEAL_SOLID,
                },
                "_focus_visible": {
                    "outline": f"2px solid {tokens.ACCENT_TEAL_SOLID}",
                    "outline_offset": "2px",
                },
            },
        ),
        content="Download",
    )


def _artifact_row(artifact: ArtifactRef) -> rx.Component:
    """Render one artifact row inside the canvas list.

    The row body is clickable as a whole and selects the artifact for
    inline viewing; the trailing download icon (see
    :func:`_row_download_button`) is a separate affordance with
    ``stop_propagation`` so the user can grab the file without
    detouring through the viewer. For non-previewable types (PPTX /
    XLSX) the caption inserts an "External app" badge so the user
    knows up front that the file opens outside the browser; the row
    still routes to the viewer, where a calm fallback explains the
    constraint without repeating the download CTA.
    """
    is_active = BrandMindState.active_artifact_filename == artifact.filename
    is_external_only = (artifact.category == "presentations") | (
        artifact.category == "spreadsheets"
    )
    dot_style = {
        "color": tokens.TEXT_MUTED,
        "font_size": "11px",
    }
    caption_style = {
        "color": tokens.TEXT_MUTED,
        "font_family": tokens.FONT_SANS,
        "font_size": "11px",
        "letter_spacing": "0.04em",
        "text_transform": "uppercase",
    }
    return rx.flex(
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
                "display": "flex",
                "align_items": "center",
                "justify_content": "center",
                "width": "32px",
                "height": "32px",
                "border_radius": tokens.RADIUS_MD,
                "background_color": "rgba(95, 179, 168, 0.10)",
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
                    style=caption_style,
                ),
                rx.cond(
                    is_external_only,
                    rx.hstack(
                        rx.text("·", style=dot_style),
                        rx.text(
                            "External app",
                            style={
                                **caption_style,
                                "color": tokens.TEXT_SECONDARY,
                            },
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.fragment(),
                ),
                rx.text("·", style=dot_style),
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
        _row_download_button(artifact),
        spacing="3",
        align="center",
        width="100%",
        on_click=BrandMindState.select_artifact(artifact.filename),
        style={
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
