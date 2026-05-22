"""ArtifactViewer — category-specific inline view inside the canvas drawer.

Mounts one of four sub-views based on the active artifact's category:

* ``images`` → Brand Key one-pager rendered inline via ``<img>``.
* ``documents`` → DOCX body rendered server-side via ``python-mammoth``.
* ``presentations`` / ``spreadsheets`` → calm "no inline preview" card
  pointing the user back at the per-row download chip on the file
  list. The download itself lives on the artifact-panel row so the
  viewer does not repeat the affordance.

The viewer reads :class:`BrandMindState.active_artifact_filename`,
``active_artifact_url``, and ``active_artifact_category`` so siblings
don't need direct access to ``ArtifactRef`` objects.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens

_DOCX_BODY_CSS = (
    """
.bm-docx-body { color: #e8eef0; font-family: """
    + tokens.FONT_SANS
    + """; }
.bm-docx-body h1, .bm-docx-body h2, .bm-docx-body h3,
.bm-docx-body h4, .bm-docx-body h5, .bm-docx-body h6 {
  color: #e8eef0;
  font-family: """
    + tokens.FONT_DISPLAY
    + """;
  font-weight: 500;
  letter-spacing: -0.005em;
  margin: 1.6em 0 0.6em 0;
  line-height: 1.25;
  scroll-margin-top: 80px;
}
.bm-docx-body h1 { font-size: 26px; }
.bm-docx-body h2 { font-size: 22px; }
.bm-docx-body h3 { font-size: 18px; }
.bm-docx-body h4, .bm-docx-body h5, .bm-docx-body h6 { font-size: 16px; }
.bm-docx-body p {
  color: #e8eef0;
  font-size: 14px;
  line-height: 1.7;
  margin: 0 0 0.9em 0;
}
.bm-docx-body strong { color: #ffffff; font-weight: 600; }
.bm-docx-body em { color: #bdc9c6; }
.bm-docx-body ul, .bm-docx-body ol {
  color: #e8eef0;
  font-size: 14px;
  line-height: 1.7;
  margin: 0 0 0.9em 1.4em;
  padding: 0;
}
.bm-docx-body li { margin: 0.2em 0; }
.bm-docx-body code {
  background: #1f262d;
  border-radius: 4px;
  font-family: """
    + tokens.FONT_MONO
    + """;
  font-size: 12px;
  padding: 1px 6px;
}
.bm-docx-body table {
  border-collapse: collapse;
  font-size: 13px;
  margin: 1em 0;
  width: 100%;
}
.bm-docx-body th, .bm-docx-body td {
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 6px 10px;
  text-align: left;
}
.bm-docx-body th { background: #1f262d; color: #e8eef0; font-weight: 500; }
.bm-docx-body a { color: #5fb3a8; text-decoration: underline; }
"""
)


def _image_view() -> rx.Component:
    """Inline Brand Key viewer — ``<img>`` against a neutral backdrop.

    The Brand Key one-pager is the only artifact whose value is purely
    visual. Render it inline with object-fit contain so wide brand-key
    canvases scale to the drawer width without cropping.
    """
    return rx.center(
        rx.image(
            src=BrandMindState.active_artifact_url,
            alt=BrandMindState.active_artifact_filename,
            style={
                "max_width": "100%",
                "max_height": "100%",
                "object_fit": "contain",
                "border_radius": tokens.RADIUS_MD,
                "background_color": "#ffffff",
            },
        ),
        flex="1",
        width="100%",
        padding="24px",
        style={
            "background_color": tokens.BG_SURFACE_1,
            "overflow": "auto",
        },
    )


def _docx_toc_entry(entry) -> rx.Component:
    """One row of the DOCX table-of-contents sidebar.

    Anchors into the rendered body via ``#anchor`` so clicking jumps
    the viewer scroll to the matching heading without a state round
    trip. Indentation reflects the heading level so the outline reads
    as a real document map.
    """
    return rx.link(
        rx.text(
            entry.text,
            style={
                "color": tokens.TEXT_SECONDARY,
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
                "line_height": "1.45",
                "padding_left": (entry.level - 1).to_string() + "em",
                "overflow": "hidden",
                "text_overflow": "ellipsis",
                "white_space": "nowrap",
                "_hover": {"color": tokens.ACCENT_TEAL_SOLID},
            },
        ),
        href="#" + entry.anchor,
        style={
            "display": "block",
            "padding": "4px 8px",
            "border_radius": tokens.RADIUS_SM,
            "_hover": {
                "background_color": tokens.BG_SURFACE_2,
            },
        },
    )


def _docx_loading() -> rx.Component:
    """Spinner shown while mammoth fetches and renders the DOCX body."""
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text(
                "Rendering document…",
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "13px",
                },
            ),
            spacing="3",
            align="center",
        ),
        flex="1",
        width="100%",
    )


def _docx_error() -> rx.Component:
    """Recoverable error card — points the user at the download fallback."""
    return rx.center(
        rx.vstack(
            rx.icon(
                tag="triangle_alert",
                size=24,
                color=tokens.STATE_ERROR_FG,
            ),
            rx.text(
                BrandMindState.docx_error,
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "13px",
                    "max_width": "320px",
                    "text_align": "center",
                },
            ),
            rx.link(
                rx.button(
                    rx.icon(tag="download", size=16),
                    rx.text("Download instead"),
                    variant="soft",
                    style={
                        "background_color": tokens.BG_SURFACE_2,
                        "color": tokens.TEXT_PRIMARY,
                    },
                ),
                href=BrandMindState.active_artifact_url,
                is_external=True,
            ),
            spacing="3",
            align="center",
        ),
        flex="1",
        width="100%",
    )


def _docx_toc_sidebar() -> rx.Component:
    """Collapsible outline panel on the left of the DOCX body.

    Header carries the ``CONTENTS`` caption plus a close button so the
    user can dismiss the panel without leaving the document. Anchor
    links inside the list scroll the body to the matching heading.
    """
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    "CONTENTS",
                    style={
                        "color": tokens.TEXT_MUTED,
                        "font_family": tokens.FONT_SANS,
                        "font_size": "10px",
                        "font_weight": "600",
                        "letter_spacing": "0.08em",
                    },
                ),
                rx.spacer(),
                rx.button(
                    rx.icon(tag="x", size=14),
                    on_click=BrandMindState.toggle_docx_toc,
                    variant="ghost",
                    color_scheme="gray",
                    aria_label="Hide outline",
                    style={
                        "color": tokens.TEXT_MUTED,
                        "width": "24px",
                        "height": "24px",
                        "padding": "0",
                        "border_radius": tokens.RADIUS_SM,
                        "_hover": {
                            "background_color": tokens.BG_SURFACE_2,
                            "color": tokens.TEXT_PRIMARY,
                        },
                    },
                ),
                spacing="2",
                align="center",
                width="100%",
                padding="0 4px 8px 8px",
            ),
            rx.foreach(
                BrandMindState.docx_toc,
                _docx_toc_entry,
            ),
            spacing="0",
            align="stretch",
            padding="20px 12px",
        ),
        style={
            "width": "220px",
            "flex": "0 0 220px",
            "border_right": f"1px solid {tokens.GLASS_BORDER}",
            "background_color": tokens.BG_SURFACE_1,
            "overflow_y": "auto",
            "max_height": "100%",
        },
    )


def _docx_outline_chip() -> rx.Component:
    """Floating "Outline" pill that opens the TOC sidebar.

    Sits at the top-left of the document body when the outline is
    closed so the user has a discoverable, dismissable handle without
    permanent left-rail chrome eating the reading column. Rendered
    only when the current document actually has headings the TOC can
    point at.
    """
    return rx.cond(
        BrandMindState.docx_toc.length() > 0,
        rx.button(
            rx.icon(tag="list", size=14),
            rx.text(
                "Outline",
                style={
                    "font_family": tokens.FONT_SANS,
                    "font_size": "12px",
                    "font_weight": "500",
                    "letter_spacing": "0.01em",
                },
            ),
            on_click=BrandMindState.toggle_docx_toc,
            variant="ghost",
            color_scheme="gray",
            aria_label="Show outline",
            style={
                "position": "absolute",
                "top": "16px",
                "left": "16px",
                "z_index": "1",
                "color": tokens.TEXT_SECONDARY,
                "background_color": tokens.GLASS_BG_ELEVATED,
                "backdrop_filter": "blur(12px)",
                "border": f"1px solid {tokens.GLASS_BORDER}",
                "height": "32px",
                "padding": "0 12px",
                "border_radius": tokens.RADIUS_PILL,
                "cursor": "pointer",
                "transition": "color 120ms ease, background-color 120ms ease",
                "_hover": {
                    "background_color": tokens.BG_SURFACE_2,
                    "color": tokens.TEXT_PRIMARY,
                },
            },
        ),
        rx.fragment(),
    )


def _docx_view() -> rx.Component:
    """Body-first DOCX reader with on-demand outline sidebar.

    The document body claims the full canvas width by default so a
    reader can scan the strategy without competing chrome. A small
    "Outline" pill in the body's top-left reveals the heading
    sidebar when the user wants a map of the document; the sidebar
    carries its own close button so the user can collapse it back to
    full-width reading. When the DOCX has no headings, the pill
    stays hidden so the surface does not promise an outline that
    doesn't exist.
    """
    body = rx.hstack(
        rx.cond(
            BrandMindState.docx_toc_open & (BrandMindState.docx_toc.length() > 0),
            _docx_toc_sidebar(),
            rx.fragment(),
        ),
        rx.box(
            _docx_outline_chip(),
            rx.html(
                BrandMindState.docx_html,
                class_name="bm-docx-body",
                style={
                    "padding": "32px 44px 64px 44px",
                    "max_width": "760px",
                    "margin_x": "auto",
                },
            ),
            style={
                "position": "relative",
                "flex": "1",
                "min_width": "0",
                "overflow_y": "auto",
                "background_color": tokens.BG_SURFACE_1,
            },
        ),
        spacing="0",
        align="stretch",
        flex="1",
        width="100%",
        height="100%",
    )
    return rx.cond(
        BrandMindState.docx_loading,
        _docx_loading(),
        rx.cond(
            BrandMindState.docx_error != "",
            _docx_error(),
            body,
        ),
    )


def _download_card(
    category_label: str, icon_tag: str, native_app_hint: str
) -> rx.Component:
    """Calm "preview not available" card for PPTX / XLSX artifacts.

    The download CTA itself lives on each artifact row in the list
    pane, so this surface only needs to explain why the panel is not
    rendering the file inline and point at the native application
    that opens it. Repeating a big teal Download button here would be
    a duplicate affordance.

    Args:
        category_label (str): Uppercase caption shown above the
            filename ("Executive deck" / "KPI tracker").
        icon_tag (str): Lucide icon for the artifact type — kept the
            same shape as the artifact-row icon so the user reads
            "same file, just no preview" rather than "different
            surface".
        native_app_hint (str): Short sentence naming the apps that
            open this file type, so the user knows what they'll need.
    """
    return rx.center(
        rx.vstack(
            rx.box(
                rx.icon(tag=icon_tag, size=28),
                style={
                    "color": tokens.ACCENT_TEAL_SOLID,
                    "display": "flex",
                    "align_items": "center",
                    "justify_content": "center",
                    "width": "64px",
                    "height": "64px",
                    "border_radius": tokens.RADIUS_LG,
                    "background_color": "rgba(95, 179, 168, 0.10)",
                },
            ),
            rx.text(
                category_label,
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "11px",
                    "font_weight": "600",
                    "letter_spacing": "0.08em",
                    "text_transform": "uppercase",
                },
            ),
            rx.text(
                BrandMindState.active_artifact_filename,
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "15px",
                    "font_weight": "500",
                    "max_width": "440px",
                    "text_align": "center",
                    "word_break": "break-all",
                    "line_height": "1.4",
                },
            ),
            rx.text(
                "No inline preview for this file type. " + native_app_hint,
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "13px",
                    "line_height": "1.55",
                    "max_width": "380px",
                    "text_align": "center",
                },
            ),
            rx.hstack(
                rx.icon(
                    tag="arrow_left",
                    size=14,
                    color=tokens.TEXT_MUTED,
                ),
                rx.text(
                    "Use the download icon on the file list to save a copy.",
                    style={
                        "color": tokens.TEXT_MUTED,
                        "font_family": tokens.FONT_SANS,
                        "font_size": "12px",
                        "font_style": "italic",
                    },
                ),
                spacing="2",
                align="center",
            ),
            spacing="3",
            align="center",
        ),
        flex="1",
        width="100%",
        padding="48px 24px",
    )


def _empty_viewer() -> rx.Component:
    """Placeholder body shown when no artifact has been selected yet."""
    return rx.center(
        rx.vstack(
            rx.icon(
                tag="layout_panel_left",
                size=28,
                color=tokens.TEXT_MUTED,
            ),
            rx.text(
                "Pick a file from the list to view it here.",
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "13px",
                    "max_width": "300px",
                    "text_align": "center",
                },
            ),
            spacing="3",
            align="center",
        ),
        flex="1",
        width="100%",
        padding="40px",
    )


def artifact_viewer() -> rx.Component:
    """Route to the correct inline viewer based on the active category.

    The renderer reads ``active_artifact_category`` from state so the
    parent canvas drawer does not have to branch — every category
    decision lives here and stays close to the category-specific view
    code.
    """
    return rx.fragment(
        rx.el.style(_DOCX_BODY_CSS),
        rx.match(
            BrandMindState.active_artifact_category,
            ("images", _image_view()),
            ("documents", _docx_view()),
            (
                "presentations",
                _download_card(
                    "Executive deck",
                    "presentation",
                    "Open the .pptx in PowerPoint or Keynote.",
                ),
            ),
            (
                "spreadsheets",
                _download_card(
                    "KPI tracker",
                    "table_2",
                    "Open the .xlsx in Excel or Numbers.",
                ),
            ),
            _empty_viewer(),
        ),
    )
