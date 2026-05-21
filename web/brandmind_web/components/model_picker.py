"""Model picker pill + dropdown for the main-agent profile.

Renders the small chip-shaped trigger that sits inside the composer
card and a Radix-driven dropdown of supported profiles. The chip
becomes a lock when the active chat has already committed a profile,
so the user reads "this chat is on model X" instead of a clickable
control that silently does nothing.

The picker is a session-level affordance — the active chat is locked
to whatever was chosen at first send, mirroring the ChatGPT pattern
without the per-message switching footgun.
"""

from __future__ import annotations

import reflex as rx

from ..models import MainAgentModelOption
from ..state import BrandMindState
from . import tokens


def _option_row(option: rx.Var[MainAgentModelOption]) -> rx.Component:
    """Render one supported model as a checkable dropdown item."""
    is_active = option.model_id == BrandMindState.picker_active_model_id

    label_stack = rx.vstack(
        rx.text(
            option.display_name,
            style={
                "color": tokens.TEXT_PRIMARY,
                "font_family": tokens.FONT_MONO,
                "font_size": "13px",
                "font_weight": rx.cond(is_active, "500", "400"),
                "line_height": "1.3",
                "letter_spacing": "-0.01em",
            },
        ),
        rx.cond(
            option.description,
            rx.text(
                option.description,
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "12px",
                    "line_height": "1.4",
                    "margin_top": "6px",
                },
            ),
            rx.fragment(),
        ),
        spacing="0",
        align="start",
        style={"flex": "1"},
    )

    check = rx.cond(
        is_active,
        rx.icon(
            tag="check",
            size=14,
            color=tokens.ACCENT_TEAL_SOLID,
        ),
        rx.box(style={"width": "14px", "height": "14px"}),
    )

    row = rx.hstack(
        label_stack,
        check,
        spacing="3",
        align="start",
        style={"width": "100%"},
    )

    return rx.menu.item(
        row,
        on_click=BrandMindState.select_model(option.model_id),
        style={
            "padding": "12px 14px",
            "border_radius": tokens.RADIUS_SM,
            "cursor": "pointer",
            "height": "auto",
            "min_height": "0",
            "align_items": "flex-start",
            "background_color": "transparent",
            "color": tokens.TEXT_PRIMARY,
            "&[data-highlighted]": {
                "background_color": tokens.ACCENT_TEAL_MUTED,
                "color": tokens.TEXT_PRIMARY,
                "outline": "none",
            },
            "&:hover": {
                "background_color": tokens.ACCENT_TEAL_MUTED,
                "color": tokens.TEXT_PRIMARY,
            },
            "&:focus": {
                "background_color": tokens.ACCENT_TEAL_MUTED,
                "color": tokens.TEXT_PRIMARY,
                "outline": "none",
            },
        },
    )


def _picker_trigger() -> rx.Component:
    """Compact chip that reads the active model and opens the dropdown."""
    icon_tag = rx.cond(
        BrandMindState.picker_is_locked,
        "lock",
        "chevron_down",
    )
    label_color = rx.cond(
        BrandMindState.picker_is_locked,
        tokens.TEXT_MUTED,
        tokens.TEXT_SECONDARY,
    )
    cursor = rx.cond(BrandMindState.picker_is_locked, "default", "pointer")

    return rx.hstack(
        rx.text(
            BrandMindState.picker_active_model_label,
            style={
                "color": label_color,
                "font_family": tokens.FONT_MONO,
                "font_size": "12px",
                "font_weight": "500",
                "letter_spacing": "-0.01em",
                "line_height": "1",
            },
        ),
        rx.icon(
            tag=icon_tag,
            size=12,
            color=tokens.TEXT_MUTED,
        ),
        spacing="2",
        align="center",
        padding="5px 10px 5px 12px",
        style={
            "background_color": "transparent",
            "border": f"1px solid {tokens.GLASS_BORDER}",
            "border_radius": tokens.RADIUS_PILL,
            "cursor": cursor,
            "transition": "background-color 140ms ease, border-color 140ms ease",
            "_hover": rx.cond(
                BrandMindState.picker_is_locked,
                {},
                {
                    "background_color": "rgba(255, 255, 255, 0.04)",
                    "border_color": "rgba(255, 255, 255, 0.12)",
                },
            ),
        },
    )


def model_picker() -> rx.Component:
    """Model picker pill + dropdown anchored above the composer.

    Renders nothing when the available-models list is empty (degraded
    discovery fetch) so the composer does not show a meaningless
    empty chip.
    """
    locked_footer = rx.cond(
        BrandMindState.picker_is_locked,
        rx.text(
            "Locked for this chat — start a new chat to switch models.",
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "11px",
                "font_style": "italic",
                "padding": "6px 12px 4px 12px",
                "line_height": "1.4",
            },
        ),
        rx.fragment(),
    )

    content = rx.menu.content(
        rx.foreach(BrandMindState.available_models, _option_row),
        locked_footer,
        align="start",
        side="top",
        side_offset=10,
        style={
            "min_width": "260px",
            "background_color": tokens.GLASS_BG_ELEVATED,
            "border": f"1px solid {tokens.GLASS_BORDER}",
            "border_radius": tokens.RADIUS_LG,
            "padding": "4px",
            "backdrop_filter": "blur(18px) saturate(140%)",
            "box_shadow": (
                "0 18px 36px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(255, 255, 255, 0.02)"
            ),
        },
    )

    menu = rx.menu.root(
        rx.menu.trigger(_picker_trigger()),
        content,
    )

    return rx.cond(
        BrandMindState.available_models.length() > 0,
        menu,
        rx.fragment(),
    )
