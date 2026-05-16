"""ChatPane container — vertical scroll of messages + sticky composer.

Implements ``docs/web_design.md`` § 9.3 with Codex review Finding 4
applied: the empty state hero is smaller (28 px), anchored in the upper
third of the canvas, and offers three prefill prompt chips so the
first interaction has texture. Glass effects stay off the scroll
surface to avoid streaming-token repaint judder.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens
from .input_composer import input_composer
from .message_bubble import message_bubble

_STARTER_PROMPTS: tuple[str, ...] = (
    "I'm launching a specialty cafe and need a brand strategy.",
    "Help me reposition an existing F&B brand.",
    "Refresh the visual identity of my restaurant.",
)


def _prompt_chip(prompt: str) -> rx.Component:
    """One starter-prompt chip that prefills the composer on click."""
    return rx.button(
        rx.text(
            prompt,
            style={
                "color": tokens.TEXT_SECONDARY,
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "line_height": "1.45",
                "text_align": "left",
            },
        ),
        on_click=BrandMindState.set_pending_input(prompt),
        variant="ghost",
        style={
            "padding": "10px 14px",
            "border_radius": tokens.RADIUS_LG,
            "border": f"1px solid {tokens.GLASS_BORDER}",
            "background_color": "transparent",
            "cursor": "pointer",
            "height": "auto",
            "max_width": "100%",
            "white_space": "normal",
            "transition": "border-color 160ms ease, background-color 160ms ease",
            "_hover": {
                "border_color": "rgba(95, 179, 168, 0.35)",
                "background_color": "rgba(95, 179, 168, 0.06)",
            },
        },
    )


def _empty_state() -> rx.Component:
    """Calm hero with three prefill prompts to seed the first turn."""
    return rx.center(
        rx.vstack(
            rx.text(
                "Where would you like to start?",
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_DISPLAY,
                    "font_size": "28px",
                    "font_weight": "400",
                    "letter_spacing": "-0.01em",
                    "line_height": "1.2",
                    "text_align": "center",
                },
            ),
            rx.text(
                "BrandMind is your brand-strategy mentor for F&B. Pick a "
                "prompt below or write your own.",
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "14px",
                    "line_height": "1.6",
                    "max_width": "440px",
                    "text_align": "center",
                },
            ),
            rx.vstack(
                *[_prompt_chip(p) for p in _STARTER_PROMPTS],
                spacing="2",
                align="stretch",
                width="100%",
                max_width="440px",
                padding_top="8px",
            ),
            spacing="4",
            align="center",
            padding_top="14vh",
        ),
        flex="1",
        width="100%",
        padding="0 24px",
    )


def _message_scroll() -> rx.Component:
    """Vertical scroll of message bubbles within a centered reading column."""
    return rx.scroll_area(
        rx.vstack(
            rx.foreach(
                BrandMindState.messages,
                lambda msg, idx: message_bubble(msg, idx),
            ),
            spacing="1",
            align="stretch",
            padding="28px 24px 24px 24px",
            max_width="880px",
            width="100%",
            margin_x="auto",
        ),
        type="auto",
        scrollbars="vertical",
        style={
            "flex": "1",
            "min_height": "0",
            "width": "100%",
        },
    )


def chat_pane() -> rx.Component:
    """Render the ChatPane — message scroll + sticky InputComposer."""
    return rx.vstack(
        rx.cond(
            BrandMindState.messages.length() == 0,
            _empty_state(),
            _message_scroll(),
        ),
        input_composer(),
        spacing="0",
        align="stretch",
        flex="1",
        width="100%",
        height="100%",
        style={
            "background_color": tokens.BG_CANVAS,
            "background_image": tokens.CANVAS_AMBIENT,
            "overflow": "hidden",
        },
    )
