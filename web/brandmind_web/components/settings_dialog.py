"""Settings dialog hosting BrandMind's personalization preferences.

Renders a refined ChatGPT-style modal with a left navigation rail and a
right content panel. Currently surfaces a single "Personalization"
section that lets the user view and edit the six structured profile
fields the backend persists under ``BRANDMIND_HOME/user/`` and renders
into the managed block of ``profile.md``. The nav rail is built as a
list so adding a future "General" section is a one-line change.

The polish anchors the 20-35 audience: editorial section heading in
the display serif, tight 4 px spacing rhythm, type-led hierarchy
(labels carry weight, not boxes), restrained teal accent used only on
focus + the active nav pill + the primary action, and quiet motion
(160 ms easing) on every state change.
"""

from __future__ import annotations

import reflex as rx

from ..models import UserProfileOption
from ..state import BrandMindState
from . import tokens

# Surface palette — refined, dark-native, no harsh contrast.
SURFACE_DIALOG = "#13181c"
SURFACE_FIELD = "#191f24"
SURFACE_FIELD_HOVER = "#1d242a"
SURFACE_DROPDOWN = "#161c20"

# Hairlines — quieter than tokens.GLASS_BORDER so borders don't dominate.
HAIRLINE_QUIET = "rgba(255, 255, 255, 0.07)"
HAIRLINE_HOVER = "rgba(95, 179, 168, 0.30)"
HAIRLINE_FOCUS = "rgba(95, 179, 168, 0.55)"
FOCUS_RING = "0 0 0 3px rgba(95, 179, 168, 0.16)"

# Active-nav tint — 8% teal so the pill reads as a calm selection,
# not a button asking to be clicked again.
NAV_ACTIVE_BG = "rgba(95, 179, 168, 0.10)"
NAV_ACTIVE_BG_HOVER = "rgba(95, 179, 168, 0.14)"
NAV_HOVER_BG = "rgba(255, 255, 255, 0.04)"

# Type tokens — labels slightly off-white so they don't compete with
# the actual input text for the eye's anchor point.
LABEL_COLOR = "rgba(255, 255, 255, 0.88)"
INPUT_COLOR = "rgba(255, 255, 255, 0.96)"
HELPER_COLOR = "rgba(255, 255, 255, 0.48)"

ACTION_BUTTON_TEXT = {
    "font_family": tokens.FONT_DIALOG,
    "font_size": "13px",
    "font_weight": "500",
    "line_height": "1.4",
    "letter_spacing": "-0.005em",
}


def _nav_item(label: str, section: str) -> rx.Component:
    """Render one entry in the dialog's left navigation rail."""
    is_active = BrandMindState.settings_dialog_section == section
    return rx.button(
        rx.text(
            label,
            style={
                "color": rx.cond(is_active, INPUT_COLOR, LABEL_COLOR),
                "font_family": tokens.FONT_DIALOG,
                "font_size": "13px",
                "font_weight": rx.cond(is_active, "600", "500"),
                "letter_spacing": "-0.005em",
            },
        ),
        on_click=BrandMindState.set_settings_dialog_section(section),
        variant="ghost",
        style={
            "width": "100%",
            "justify_content": "flex-start",
            "padding": "9px 12px",
            "border_radius": tokens.RADIUS_MD,
            "cursor": "pointer",
            "transition": "background-color 160ms cubic-bezier(0.16, 1, 0.3, 1)",
            "background_color": rx.cond(is_active, NAV_ACTIVE_BG, "transparent"),
            "_hover": {
                "background_color": rx.cond(
                    is_active, NAV_ACTIVE_BG_HOVER, NAV_HOVER_BG
                ),
            },
        },
    )


def _select_item(option: rx.Var[UserProfileOption]) -> rx.Component:
    """One dropdown row — single-line label with a right-aligned check.

    The per-option descriptions live in the form's helper line rather
    than in the dropdown so the picker stays a quick "pick the value"
    surface — closer to ChatGPT / Linear settings than to a wizard.
    """
    return rx.select.item(
        rx.text(
            option.label,
            style={
                "color": INPUT_COLOR,
                "font_family": tokens.FONT_DIALOG,
                "font_size": "13.5px",
                "font_weight": "500",
                "line_height": "1.4",
                "letter_spacing": "-0.005em",
            },
        ),
        value=option.value,
        text_value=option.label,
        style={
            "position": "relative",
            "display": "flex",
            "align_items": "center",
            "height": "36px",
            "min_height": "0",
            "border_radius": tokens.RADIUS_MD,
            "padding": "0 36px 0 12px",
            "margin": "1px 0",
            "cursor": "pointer",
            "transition": "background-color 140ms cubic-bezier(0.16, 1, 0.3, 1)",
            "&[data-highlighted]": {
                "background_color": "rgba(95, 179, 168, 0.14)",
                "outline": "none",
            },
            "&:hover": {
                "background_color": "rgba(95, 179, 168, 0.14)",
            },
            "& .rt-SelectItemIndicator": {
                "left": "auto",
                "right": "12px",
                "top": "50%",
                "transform": "translateY(-50%)",
                "color": tokens.ACCENT_TEAL_SOLID,
            },
        },
    )


def _personalization_field(
    label: str,
    helper: str,
    field: str,
    options: rx.Var[list[UserProfileOption]],
    selected_value: rx.Var[str],
) -> rx.Component:
    """One field cluster — label + ghost trigger row, helper line below.

    The helper sits on its own line so the row stays one-glance scannable
    while still explaining what the choice changes in the mentor. Type
    weight does the hierarchy; no surrounding boxes, no field divider.
    """
    return rx.vstack(
        rx.hstack(
            rx.text(
                label,
                style={
                    "color": INPUT_COLOR,
                    "font_family": tokens.FONT_DIALOG,
                    "font_size": "14px",
                    "font_weight": "600",
                    "letter_spacing": "-0.012em",
                    "line_height": "1.35",
                    "flex": "1",
                    "min_width": "0",
                },
            ),
            rx.select.root(
                rx.select.trigger(
                    placeholder="Choose…",
                    style={
                        "background_color": "rgba(255, 255, 255, 0.025)",
                        "border": f"1px solid {HAIRLINE_QUIET}",
                        "color": INPUT_COLOR,
                        "font_family": tokens.FONT_DIALOG,
                        "font_size": "13.5px",
                        "font_weight": "500",
                        "line_height": "1.4",
                        "letter_spacing": "-0.005em",
                        "min_height": "34px",
                        "padding": "0 8px 0 14px",
                        "border_radius": tokens.RADIUS_MD,
                        "min_width": "168px",
                        "transition": (
                            "background-color 160ms cubic-bezier(0.16, 1, 0.3, 1), "
                            "border-color 160ms cubic-bezier(0.16, 1, 0.3, 1), "
                            "box-shadow 160ms cubic-bezier(0.16, 1, 0.3, 1)"
                        ),
                        "_hover": {
                            "background_color": "rgba(255, 255, 255, 0.05)",
                            "border_color": "rgba(255, 255, 255, 0.14)",
                        },
                        "_focus": {
                            "background_color": "rgba(255, 255, 255, 0.06)",
                            "border_color": HAIRLINE_FOCUS,
                            "box_shadow": FOCUS_RING,
                        },
                        "&[data-state='open']": {
                            "background_color": "rgba(255, 255, 255, 0.06)",
                            "border_color": HAIRLINE_FOCUS,
                            "box_shadow": FOCUS_RING,
                        },
                        "& .rt-SelectTriggerInner": {
                            "font_family": tokens.FONT_DIALOG,
                            "font_size": "13.5px",
                            "font_weight": "500",
                            "line_height": "1.4",
                        },
                    },
                ),
                rx.select.content(
                    rx.foreach(options, _select_item),
                    position="popper",
                    side="bottom",
                    align="end",
                    side_offset=8,
                    style={
                        "background_color": SURFACE_DROPDOWN,
                        "border": f"1px solid {HAIRLINE_QUIET}",
                        "border_radius": tokens.RADIUS_LG,
                        "box_shadow": (
                            "0 24px 48px rgba(0, 0, 0, 0.55), "
                            "0 0 0 1px rgba(255, 255, 255, 0.025)"
                        ),
                        "padding": "6px",
                        "backdrop_filter": "blur(20px) saturate(140%)",
                        "min_width": "200px",
                    },
                ),
                value=selected_value,
                on_change=lambda value: BrandMindState.update_setting_field(
                    field, value
                ),
                size="2",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        rx.text(
            helper,
            style={
                "color": HELPER_COLOR,
                "font_family": tokens.FONT_DIALOG,
                "font_size": "12.5px",
                "font_weight": "400",
                "line_height": "1.55",
                "letter_spacing": "-0.002em",
                "max_width": "560px",
            },
        ),
        spacing="1",
        align="stretch",
        width="100%",
    )


def personalization_form() -> rx.Component:
    """Render the six profile-field clusters shared by Settings + Onboarding."""
    draft = BrandMindState.profile_settings_draft
    options = BrandMindState.profile_settings_options
    return rx.vstack(
        _personalization_field(
            "Job domain",
            "The industry you primarily work in.",
            "job_domain",
            options.job_domain,
            draft.job_domain,
        ),
        _personalization_field(
            "Role",
            "Your primary role on a brand team.",
            "role",
            options.role,
            draft.role,
        ),
        _personalization_field(
            "Experience",
            "Years working in marketing or branding.",
            "experience_years",
            options.experience_years,
            draft.experience_years,
        ),
        _personalization_field(
            "Brand-strategy familiarity",
            "How fluent you are with brand-strategy frameworks.",
            "brand_strategy_familiarity",
            options.brand_strategy_familiarity,
            draft.brand_strategy_familiarity,
        ),
        _personalization_field(
            "Preferred mentoring style",
            "How directive or exploratory you prefer guidance to feel.",
            "mentoring_style",
            options.mentoring_style,
            draft.mentoring_style,
        ),
        _personalization_field(
            "Primary stakeholder",
            "Who you typically report to.",
            "stakeholder_context",
            options.stakeholder_context,
            draft.stakeholder_context,
        ),
        spacing="5",
        align="stretch",
        width="100%",
    )


def _section_header() -> rx.Component:
    """Editorial section heading + sub-copy + hairline closing rule."""
    return rx.vstack(
        rx.text(
            "Personalization",
            style={
                "color": INPUT_COLOR,
                "font_family": tokens.FONT_DISPLAY,
                "font_size": "24px",
                "font_weight": "400",
                "letter_spacing": "-0.022em",
                "line_height": "1.12",
            },
        ),
        rx.text(
            "Set personalization priors so BrandMind can calibrate its "
            "mentoring density and decision framing from the first turn.",
            style={
                "color": HELPER_COLOR,
                "font_family": tokens.FONT_DIALOG,
                "font_size": "13.5px",
                "line_height": "1.55",
                "margin_top": "8px",
                "letter_spacing": "-0.003em",
                "max_width": "520px",
            },
        ),
        rx.box(
            style={
                "height": "1px",
                "background_color": HAIRLINE_QUIET,
                "margin_top": "16px",
                "margin_bottom": "22px",
                "width": "100%",
            },
        ),
        spacing="0",
        align="stretch",
        width="100%",
    )


def _personalization_panel() -> rx.Component:
    """Right-side content panel for the Personalization section."""
    return rx.vstack(
        _section_header(),
        personalization_form(),
        spacing="0",
        align="stretch",
        width="100%",
    )


def _dialog_footer() -> rx.Component:
    """Cancel + Save row with hairline rule above and inline error when present."""
    return rx.vstack(
        rx.box(
            style={
                "height": "1px",
                "background_color": HAIRLINE_QUIET,
                "width": "100%",
                "margin_top": "20px",
                "margin_bottom": "14px",
            },
        ),
        rx.cond(
            BrandMindState.profile_settings_error != "",
            rx.text(
                BrandMindState.profile_settings_error,
                style={
                    "color": "#f3a59c",
                    "font_family": tokens.FONT_DIALOG,
                    "font_size": "12px",
                    "line_height": "1.55",
                    "margin_bottom": "12px",
                },
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.button(
                "Cancel",
                on_click=BrandMindState.close_settings,
                variant="ghost",
                style={
                    **ACTION_BUTTON_TEXT,
                    "color": LABEL_COLOR,
                    "padding": "0 14px",
                    "min_height": "32px",
                    "border_radius": tokens.RADIUS_MD,
                    "transition": (
                        "background-color 160ms cubic-bezier(0.16, 1, 0.3, 1), "
                        "color 160ms cubic-bezier(0.16, 1, 0.3, 1)"
                    ),
                    "_hover": {
                        "background_color": "rgba(255, 255, 255, 0.05)",
                        "color": INPUT_COLOR,
                    },
                },
            ),
            rx.button(
                rx.cond(
                    BrandMindState.profile_settings_saving,
                    "Saving…",
                    "Save",
                ),
                on_click=BrandMindState.save_profile_settings,
                disabled=BrandMindState.profile_settings_saving,
                style={
                    **ACTION_BUTTON_TEXT,
                    "background_color": tokens.ACCENT_TEAL_SOLID,
                    "color": "#002923",
                    "padding": "0 16px",
                    "min_height": "32px",
                    "border_radius": tokens.RADIUS_MD,
                    "box_shadow": (
                        "0 1px 0 rgba(255, 255, 255, 0.10) inset, "
                        "0 8px 20px rgba(95, 179, 168, 0.18)"
                    ),
                    "transition": (
                        "background-color 160ms cubic-bezier(0.16, 1, 0.3, 1), "
                        "transform 140ms cubic-bezier(0.16, 1, 0.3, 1), "
                        "box-shadow 160ms cubic-bezier(0.16, 1, 0.3, 1)"
                    ),
                    "_hover": {
                        "background_color": "#6cc3b7",
                        "box_shadow": (
                            "0 1px 0 rgba(255, 255, 255, 0.12) inset, "
                            "0 10px 24px rgba(95, 179, 168, 0.26)"
                        ),
                    },
                    "_active": {
                        "transform": "translateY(1px)",
                    },
                },
            ),
            spacing="3",
            justify="end",
            width="100%",
        ),
        spacing="0",
        align="stretch",
        width="100%",
    )


def settings_dialog() -> rx.Component:
    """Page-level Settings dialog driven by ``settings_dialog_open``.

    Layout follows the ChatGPT settings pattern: the left nav rail and
    the right content panel sit side by side with spacing + the active
    pill's tint doing the visual separation, no vertical divider line
    bisecting the dialog.
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "Settings",
                        style={
                            "color": HELPER_COLOR,
                            "font_family": tokens.FONT_DIALOG,
                            "font_size": "10.5px",
                            "font_weight": "700",
                            "letter_spacing": "0.12em",
                            "text_transform": "uppercase",
                            "padding": "0 12px 14px 12px",
                        },
                    ),
                    _nav_item("Personalization", "personalization"),
                    spacing="1",
                    align="stretch",
                    width="200px",
                    padding="6px 24px 0 0",
                ),
                rx.box(
                    _personalization_panel(),
                    _dialog_footer(),
                    style={
                        "flex": "1",
                        "padding": "4px 4px 0 24px",
                    },
                ),
                spacing="0",
                align="stretch",
                width="100%",
            ),
            style={
                "background_color": SURFACE_DIALOG,
                "border": f"1px solid {HAIRLINE_QUIET}",
                "border_radius": tokens.RADIUS_XL,
                "max_width": "760px",
                "width": "90vw",
                "padding": "28px 30px",
                "font_family": tokens.FONT_DIALOG,
                "box_shadow": (
                    "0 1px 0 rgba(255, 255, 255, 0.04) inset, "
                    "0 36px 72px rgba(0, 0, 0, 0.58), "
                    "0 0 0 1px rgba(255, 255, 255, 0.02)"
                ),
            },
        ),
        open=BrandMindState.settings_dialog_open,
        on_open_change=BrandMindState.close_settings,
    )
