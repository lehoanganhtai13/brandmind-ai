"""ArtifactViewer — category-specific inline view inside the canvas drawer.

Mounts one of four sub-views based on the active artifact's category:

* ``images`` → Brand Key one-pager rendered inline via ``<img>``.
* ``documents`` → DOCX body rendered server-side via ``python-mammoth``.
* ``presentations`` / ``spreadsheets`` → Download card (v1 deferral —
  see ``docs/web_design.md`` § 9.5.4 + § 9.5.5).

The viewer reads :class:`BrandMindState.active_artifact_filename`,
``active_artifact_url``, and ``active_artifact_category`` so siblings
don't need direct access to ``ArtifactRef`` objects.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens

_DOCX_BODY_CSS = """
.bm-docx-body { color: #e8eef0; font-family: """ + tokens.FONT_SANS + """; }
.bm-docx-body h1, .bm-docx-body h2, .bm-docx-body h3,
.bm-docx-body h4, .bm-docx-body h5, .bm-docx-body h6 {
  color: #e8eef0;
  font-family: """ + tokens.FONT_DISPLAY + """;
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
  font-family: """ + tokens.FONT_MONO + """;
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


def _docx_view() -> rx.Component:
    """Sticky-TOC + scrollable HTML body for a DOCX artifact.

    The TOC sidebar sticks to the left while the body scrolls so the
    user never loses their place in long strategy documents. When the
    document has no headings the TOC collapses out so the body gets
    the full drawer width.
    """
    body = rx.hstack(
        rx.cond(
            BrandMindState.docx_toc.length() > 0,
            rx.box(
                rx.vstack(
                    rx.text(
                        "CONTENTS",
                        style={
                            "color": tokens.TEXT_MUTED,
                            "font_family": tokens.FONT_SANS,
                            "font_size": "10px",
                            "font_weight": "600",
                            "letter_spacing": "0.08em",
                            "padding": "0 8px 8px 8px",
                        },
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
            ),
            rx.fragment(),
        ),
        rx.box(
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


def _download_card(category_label: str, blurb: str) -> rx.Component:
    """Card view for PPTX / XLSX artifacts (v1 download-only).

    Inline rendering for these categories is deferred to v2 per
    ``docs/web_design.md`` § 9.5.4 + § 9.5.5. The card explains the
    deferral, surfaces the file metadata, and offers a download
    button that drops the file via the existing artifact endpoint.

    Args:
        category_label (str): Human label shown above the filename
            ("Executive deck" / "KPI tracker").
        blurb (str): Short explanation of why inline render is not
            available in v1.
    """
    return rx.center(
        rx.vstack(
            rx.icon(
                tag="cloud_download",
                size=40,
                color=tokens.ACCENT_TEAL_SOLID,
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
                    "font_size": "16px",
                    "font_weight": "500",
                    "max_width": "440px",
                    "text_align": "center",
                    "word_break": "break-all",
                },
            ),
            rx.text(
                blurb,
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "13px",
                    "line_height": "1.55",
                    "max_width": "420px",
                    "text_align": "center",
                },
            ),
            rx.link(
                rx.button(
                    rx.icon(tag="download", size=18),
                    rx.text(
                        "Download to view",
                        style={
                            "font_family": tokens.FONT_SANS,
                            "font_size": "14px",
                            "font_weight": "500",
                        },
                    ),
                    style={
                        "background_color": tokens.ACCENT_TEAL_SOLID,
                        "color": tokens.BG_CANVAS,
                        "padding": "10px 18px",
                        "border_radius": tokens.RADIUS_MD,
                        "_hover": {
                            "background_color": "#4ea69a",
                        },
                    },
                ),
                href=BrandMindState.active_artifact_url,
                is_external=True,
            ),
            spacing="4",
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
                    "Inline slide rendering is coming in BrandMind v2. "
                    "Download the deck to review the full pitch in "
                    "Keynote or PowerPoint.",
                ),
            ),
            (
                "spreadsheets",
                _download_card(
                    "KPI tracker",
                    "Inline spreadsheet rendering is coming in BrandMind "
                    "v2. Download the workbook to review the KPI grid in "
                    "Numbers or Excel.",
                ),
            ),
            _empty_viewer(),
        ),
    )
