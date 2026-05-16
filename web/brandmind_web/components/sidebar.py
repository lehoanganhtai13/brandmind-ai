"""PhaseProgressSidebar — collapsible left rail showing phase progress.

Matches ``docs/web_design.md`` § 9.2: scope-dependent phase list with
per-item states (idle / current / completed), expanded (240 px) and
collapsed (56 px rail) variants, and a hover tooltip on the collapsed
rail surfacing the full label. State source-of-truth is
:class:`BrandMindState` (``phase_sequence``, ``phase_display_labels``,
``current_phase``, ``completed_phases``, ``sidebar_is_collapsed``); the
component only renders.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens


def _expanded_row(phase_key: rx.Var) -> rx.Component:
    """One row in the expanded sidebar — icon + numeric prefix + label."""
    is_current = phase_key == BrandMindState.current_phase
    is_done = BrandMindState.completed_phases.contains(phase_key)

    return rx.hstack(
        rx.box(
            style={
                "width": "4px",
                "height": "100%",
                "background_color": rx.cond(
                    is_current, tokens.ACCENT_TEAL_SOLID, "transparent"
                ),
                "border_radius": "0 2px 2px 0",
            },
        ),
        rx.cond(
            is_done,
            rx.icon(tag="check", size=18, color=tokens.ACCENT_TEAL_SOLID),
            rx.cond(
                is_current,
                rx.icon(tag="circle_dot", size=18, color=tokens.ACCENT_TEAL_SOLID),
                rx.icon(tag="circle", size=18, color=tokens.TEXT_MUTED),
            ),
        ),
        rx.text(
            BrandMindState.phase_display_labels.get(phase_key, phase_key),
            style={
                "color": rx.cond(
                    is_current | is_done,
                    tokens.TEXT_PRIMARY,
                    tokens.TEXT_MUTED,
                ),
                "font_family": tokens.FONT_SANS,
                "font_size": "14px",
                "font_weight": rx.cond(is_current, "600", "400"),
            },
        ),
        spacing="3",
        align="center",
        padding_y="12px",
        padding_right="16px",
        width="100%",
    )


def _collapsed_rail_item(phase_key: rx.Var) -> rx.Component:
    """One indicator on the collapsed rail with hover tooltip."""
    is_current = phase_key == BrandMindState.current_phase
    is_done = BrandMindState.completed_phases.contains(phase_key)

    indicator = rx.cond(
        is_done,
        rx.icon(tag="circle_check", size=20, color=tokens.ACCENT_TEAL_SOLID),
        rx.cond(
            is_current,
            rx.icon(tag="circle_dot", size=22, color=tokens.ACCENT_TEAL_SOLID),
            rx.icon(tag="circle", size=20, color=tokens.TEXT_MUTED),
        ),
    )

    return rx.tooltip(
        rx.center(
            indicator,
            width="100%",
            padding_y="10px",
        ),
        content=BrandMindState.phase_display_labels.get(phase_key, phase_key),
        side="right",
    )


def _section_label() -> rx.Component:
    """Top-of-sidebar caps label rendered only when expanded."""
    return rx.cond(
        BrandMindState.sidebar_is_collapsed,
        rx.fragment(),
        rx.text(
            "PHASES",
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_MONO,
                "font_size": "11px",
                "font_weight": "500",
                "letter_spacing": "0.08em",
                "padding_left": "16px",
                "padding_top": "16px",
                "padding_bottom": "8px",
            },
        ),
    )


def _empty_state() -> rx.Component:
    """Placeholder when scope has not been classified yet."""
    return rx.cond(
        BrandMindState.sidebar_is_collapsed,
        rx.center(
            rx.icon(tag="loader", size=18, color=tokens.TEXT_MUTED),
            padding_y="16px",
        ),
        rx.text(
            "Đang chờ scope...",
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "padding": "16px",
            },
        ),
    )


def phase_progress_sidebar() -> rx.Component:
    """Render the collapsible PhaseProgressSidebar.

    Reactive width tracks ``BrandMindState.sidebar_is_collapsed``; the
    240-to-56 px transition runs as a CSS width animation so the chat
    pane reflows smoothly.
    """
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
                ),
                rx.vstack(
                    rx.foreach(
                        BrandMindState.phase_sequence,
                        _expanded_row,
                    ),
                    spacing="0",
                    width="100%",
                    padding_left="0",
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
