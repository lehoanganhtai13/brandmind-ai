"""PhaseProgressSidebar — collapsible left rail showing phase progress.

Matches ``docs/web_design.md`` § 9.2: scope-dependent phase list with
per-item states (idle / current / completed), expanded (240 px) and
collapsed (56 px rail) variants. The collapsed rail renders a numbered
phase pill per slot (Codex review Finding 5) so the rail communicates
position even without text labels. State source-of-truth is
:class:`BrandMindState` — the component only renders.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens

_PHASE_DISPLAY_EN: dict[str, str] = {
    "phase_0": "Diagnosis",
    "phase_0_5": "Brand audit",
    "phase_1": "Market analysis",
    "phase_2": "Positioning",
    "phase_3": "Identity system",
    "phase_4": "Communication",
    "phase_5": "KPIs & roadmap",
}


def _phase_label(phase_key: rx.Var) -> rx.Var:
    """Project a phase id to its English UI label, falling back to the id."""
    label: rx.Var = phase_key
    for key, value in _PHASE_DISPLAY_EN.items():
        label = rx.cond(phase_key == key, value, label)
    return label


def _phase_number(phase_key: rx.Var) -> rx.Var:
    """Render the rail glyph for a phase id (numeric, with the 0.5 case)."""
    glyph: rx.Var = phase_key
    glyph = rx.cond(phase_key == "phase_0", "0", glyph)
    glyph = rx.cond(phase_key == "phase_0_5", "½", glyph)
    glyph = rx.cond(phase_key == "phase_1", "1", glyph)
    glyph = rx.cond(phase_key == "phase_2", "2", glyph)
    glyph = rx.cond(phase_key == "phase_3", "3", glyph)
    glyph = rx.cond(phase_key == "phase_4", "4", glyph)
    glyph = rx.cond(phase_key == "phase_5", "5", glyph)
    return glyph


def _expanded_row(phase_key: rx.Var) -> rx.Component:
    """One row in the expanded sidebar — number pill + label."""
    is_current = phase_key == BrandMindState.current_phase
    is_done = BrandMindState.completed_phases.contains(phase_key)

    pill = rx.center(
        rx.text(
            _phase_number(phase_key),
            style={
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
                "font_weight": "600",
                "color": rx.cond(
                    is_current | is_done,
                    "#003732",
                    tokens.TEXT_SECONDARY,
                ),
            },
        ),
        style={
            "width": "26px",
            "height": "26px",
            "border_radius": tokens.RADIUS_PILL,
            "background_color": rx.cond(
                is_current | is_done,
                tokens.ACCENT_TEAL_SOLID,
                "transparent",
            ),
            "border": rx.cond(
                is_current | is_done,
                "none",
                f"1px solid {tokens.GLASS_BORDER}",
            ),
        },
    )

    return rx.hstack(
        pill,
        rx.text(
            _phase_label(phase_key),
            style={
                "color": rx.cond(
                    is_current | is_done,
                    tokens.TEXT_PRIMARY,
                    tokens.TEXT_MUTED,
                ),
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "font_weight": rx.cond(is_current, "600", "400"),
                "line_height": "1.4",
            },
        ),
        spacing="3",
        align="center",
        padding="6px 16px",
        width="100%",
    )


def _collapsed_rail_item(phase_key: rx.Var) -> rx.Component:
    """One numbered pill on the collapsed rail with hover tooltip."""
    is_current = phase_key == BrandMindState.current_phase
    is_done = BrandMindState.completed_phases.contains(phase_key)

    pill = rx.center(
        rx.text(
            _phase_number(phase_key),
            style={
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
                "font_weight": "600",
                "color": rx.cond(
                    is_current | is_done,
                    "#003732",
                    tokens.TEXT_SECONDARY,
                ),
            },
        ),
        style={
            "width": "28px",
            "height": "28px",
            "border_radius": tokens.RADIUS_PILL,
            "background_color": rx.cond(
                is_current | is_done,
                tokens.ACCENT_TEAL_SOLID,
                "transparent",
            ),
            "border": rx.cond(
                is_current | is_done,
                "none",
                f"1px solid {tokens.GLASS_BORDER}",
            ),
        },
    )

    return rx.tooltip(
        rx.center(pill, width="100%", padding_y="6px"),
        content=_phase_label(phase_key),
        side="right",
    )


def _section_label() -> rx.Component:
    """Top-of-sidebar label rendered only when expanded.

    Uses sentence-case sans (not all-caps mono) per Codex review Finding 1
    — the all-caps mono treatment read as "terminal product chrome".
    """
    return rx.cond(
        BrandMindState.sidebar_is_collapsed,
        rx.fragment(),
        rx.text(
            "Phases",
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
                "font_weight": "500",
                "letter_spacing": "0.02em",
                "padding": "20px 16px 8px 16px",
            },
        ),
    )


def _empty_state() -> rx.Component:
    """Placeholder when scope has not been classified yet.

    Hides entirely on the collapsed rail (Codex review Finding 1) so the
    rail does not show a lone spinning glyph that reads as a debug
    indicator; expanded view shows a brief explanatory line instead.
    """
    return rx.cond(
        BrandMindState.sidebar_is_collapsed,
        rx.fragment(),
        rx.text(
            "Awaiting scope classification.",
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
                "font_style": "italic",
                "padding": "0 16px 16px 16px",
                "line_height": "1.5",
            },
        ),
    )


def phase_progress_sidebar() -> rx.Component:
    """Render the collapsible PhaseProgressSidebar."""
    return rx.vstack(
        _section_label(),
        rx.cond(
            BrandMindState.phase_sequence.length() == 0,
            _empty_state(),
            rx.cond(
                BrandMindState.sidebar_is_collapsed,
                rx.vstack(
                    rx.foreach(
                        BrandMindState.phase_sequence,
                        _collapsed_rail_item,
                    ),
                    spacing="0",
                    width="100%",
                    padding_top="12px",
                ),
                rx.vstack(
                    rx.foreach(
                        BrandMindState.phase_sequence,
                        _expanded_row,
                    ),
                    spacing="0",
                    width="100%",
                    padding_top="4px",
                ),
            ),
        ),
        spacing="0",
        align="start",
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
            "background_color": tokens.GLASS_BG_SUBTLE,
            "backdrop_filter": "blur(20px)",
            "-webkit-backdrop-filter": "blur(20px)",
            "border_right": f"1px solid {tokens.GLASS_BORDER}",
            "transition": "width 240ms cubic-bezier(0.4, 0, 0.2, 1)",
            "overflow_y": "auto",
            "overflow_x": "hidden",
        },
    )
