"""DegradedBanner — connectivity + transient-error banner.

Renders a thin banner between the header and the chat scroll whenever
the web UI cannot reach ``/api/v1/health`` or the live SSE stream has
recently failed. The banner offers a retry control so the user can
force a health re-check without waiting for the next polling tick,
and auto-dismisses a short time after recovery.

Mirrors ``docs/web_design.md`` § 9.6:

* Hidden (default) — backend healthy AND no stale stream error.
* Error — backend disconnected; offers retry.
* Warning — backend healthy but the last stream failed; offers retry
  for the stalled turn.
* Recovered (transient) — fades out 5 s after recovery so the user
  notices the state flip before the banner disappears.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens

_VARIANT_PRESETS: dict[str, dict[str, str]] = {
    "error": {
        "background_color": tokens.STATE_ERROR_BG,
        "border_color": tokens.STATE_ERROR_BORDER,
        "fg": tokens.STATE_ERROR_FG,
        "icon": "wifi_off",
    },
    "warning": {
        "background_color": "rgba(238, 165, 75, 0.16)",
        "border_color": "rgba(238, 165, 75, 0.42)",
        "fg": "#f3c270",
        "icon": "triangle_alert",
    },
    "recovered": {
        "background_color": "rgba(95, 179, 168, 0.12)",
        "border_color": "rgba(95, 179, 168, 0.40)",
        "fg": tokens.ACCENT_TEAL_SOLID,
        "icon": "wifi",
    },
}


def _banner_shell(
    variant: str,
    text: rx.Var | str,
    show_retry: bool,
) -> rx.Component:
    """Common banner row — icon + text + optional retry button.

    The shell is rendered once per variant and switched in via
    :func:`rx.match` so each banner state stays a static React tree.

    Args:
        variant (str): One of ``error`` / ``warning`` / ``recovered``;
            selects the preset color palette and icon.
        text (rx.Var | str): The visible message body, reactive or
            literal.
        show_retry (bool): Whether to render the "Try again" button on
            the right edge — hidden for ``recovered``.
    """
    preset = _VARIANT_PRESETS[variant]
    return rx.hstack(
        rx.icon(tag=preset["icon"], size=16, color=preset["fg"]),
        rx.text(
            text,
            style={
                "color": preset["fg"],
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "line_height": "1.4",
                "flex": "1",
                "min_width": "0",
            },
        ),
        rx.cond(
            show_retry,
            rx.button(
                rx.text(
                    "Try again",
                    style={
                        "color": preset["fg"],
                        "font_family": tokens.FONT_SANS,
                        "font_size": "12px",
                        "font_weight": "500",
                    },
                ),
                on_click=BrandMindState.retry_connection,
                variant="ghost",
                style={
                    "border": f"1px solid {preset['border_color']}",
                    "border_radius": tokens.RADIUS_SM,
                    "padding": "4px 10px",
                    "cursor": "pointer",
                    "background_color": "transparent",
                    "_hover": {
                        "background_color": "rgba(255, 255, 255, 0.04)",
                    },
                },
            ),
            rx.fragment(),
        ),
        spacing="3",
        align="center",
        padding="10px 18px",
        width="100%",
        style={
            "background_color": preset["background_color"],
            "border_bottom": f"1px solid {preset['border_color']}",
            "flex": "0 0 auto",
        },
    )


def degraded_banner() -> rx.Component:
    """Mount the banner with variant chosen by the current state.

    Reads :attr:`BrandMindState.banner_variant` so the dispatch logic
    lives in one place; an empty string from state means "no banner".
    """
    return rx.match(
        BrandMindState.banner_variant,
        (
            "error",
            _banner_shell(
                "error",
                BrandMindState.connectivity_message,
                show_retry=True,
            ),
        ),
        (
            "warning",
            _banner_shell(
                "warning",
                BrandMindState.error_message,
                show_retry=True,
            ),
        ),
        (
            "recovered",
            _banner_shell(
                "recovered",
                "Back online.",
                show_retry=False,
            ),
        ),
        rx.fragment(),
    )
