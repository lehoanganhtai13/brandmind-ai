"""ChatPane container — vertical scroll of messages + sticky composer.

Implements ``docs/web_design.md`` § 9.3. Solid (NON-glass) surfaces
because the chat scroll repaints frequently as streaming tokens
arrive; glass on this layer triggers full-frame repaints and produces
visible judder on mid-range hardware. Max chat width 768 px centered
so long lines stay readable.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens
from .input_composer import input_composer
from .message_bubble import message_bubble


def _empty_state() -> rx.Component:
    """Surface a calm starting prompt when no messages exist yet."""
    return rx.center(
        rx.vstack(
            rx.text(
                "Chào anh / chị, em là BrandMind.",
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "18px",
                    "font_weight": "500",
                },
            ),
            rx.text(
                "Nhập tin nhắn để bắt đầu hành trình "
                "xây dựng thương hiệu F&B.",
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "14px",
                },
            ),
            spacing="2",
            align="center",
        ),
        flex="1",
        width="100%",
    )


def _message_scroll() -> rx.Component:
    """Vertical scroll of message bubbles."""
    return rx.scroll_area(
        rx.vstack(
            rx.foreach(BrandMindState.messages, message_bubble),
            spacing="1",
            align="start",
            padding="24px 24px 16px 24px",
            max_width="768px",
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
            "overflow": "hidden",
        },
    )
