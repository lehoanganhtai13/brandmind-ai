"""First-run onboarding modal that primes BrandMind's personalization.

Auto-opens once on a fresh ``BRANDMIND_HOME/user/`` when the backend
reports ``onboarding_completed=False``. The form shares its dropdowns
with the Settings dialog so a save here is identical to a save from
Settings; Skip persists ``onboarding_completed=True`` against the
current (possibly default) draft so the modal does not reappear after a
deliberate dismissal.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens
from .settings_dialog import personalization_form


def _header() -> rx.Component:
    """Welcome lockup at the top of the onboarding modal."""
    return rx.vstack(
        rx.text(
            "Welcome to BrandMind",
            style={
                "color": tokens.TEXT_PRIMARY,
                "font_family": tokens.FONT_DISPLAY,
                "font_size": "22px",
                "font_weight": "500",
                "letter_spacing": "-0.01em",
                "line_height": "1.2",
            },
        ),
        rx.text(
            "Tell BrandMind a little about how you work so the first chat "
            "starts at the right depth. You can update or skip this any "
            "time from Settings.",
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "line_height": "1.6",
                "margin_top": "4px",
            },
        ),
        spacing="0",
        align="stretch",
        margin_bottom="20px",
    )


def _footer() -> rx.Component:
    """Skip + Save row plus inline error when present."""
    return rx.vstack(
        rx.cond(
            BrandMindState.profile_settings_error != "",
            rx.text(
                BrandMindState.profile_settings_error,
                style={
                    "color": "#f3a59c",
                    "font_family": tokens.FONT_SANS,
                    "font_size": "12px",
                    "line_height": "1.5",
                },
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.button(
                "Skip for now",
                on_click=BrandMindState.skip_onboarding,
                disabled=BrandMindState.profile_settings_saving,
                variant="soft",
                color_scheme="gray",
            ),
            rx.button(
                rx.cond(
                    BrandMindState.profile_settings_saving,
                    "Saving…",
                    "Save and continue",
                ),
                on_click=BrandMindState.save_profile_settings,
                disabled=BrandMindState.profile_settings_saving,
                style={
                    "background_color": tokens.ACCENT_TEAL_SOLID,
                    "color": "#003732",
                },
            ),
            spacing="3",
            justify="end",
        ),
        spacing="2",
        align="stretch",
        margin_top="20px",
        width="100%",
    )


def onboarding_dialog() -> rx.Component:
    """Page-level first-run modal driven by ``onboarding_open``."""
    return rx.dialog.root(
        rx.dialog.content(
            _header(),
            personalization_form(),
            _footer(),
            style={
                "background_color": tokens.BG_SURFACE_1,
                "border": f"1px solid {tokens.GLASS_BORDER}",
                "max_width": "560px",
                "width": "92vw",
                "padding": "24px",
            },
        ),
        open=BrandMindState.onboarding_open,
        on_open_change=BrandMindState.close_onboarding,
    )
