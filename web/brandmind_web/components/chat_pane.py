"""ChatPane container — vertical scroll of messages + sticky composer.

Implements ``docs/web_design.md`` § 9.3 with a wider 920 px reading column and
a subtle teal ambient gradient layered on the dark canvas so the unused
horizontal space reads as atmosphere rather than a dead void. Glass effects
stay off the scroll surface to avoid streaming-token repaint judder.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens
from .input_composer import input_composer
from .message_bubble import message_bubble


def _empty_state() -> rx.Component:
    """Calm hero shown before the first user message lands.

    Uses the display serif for an editorial opening line so the empty page
    feels intentional, not unfinished. The supporting line stays in the
    body sans so the contrast between welcome + helper is clearly typographic.
    """
    return rx.center(
        rx.vstack(
            rx.text(
                "Chào anh / chị.",
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_DISPLAY,
                    "font_size": "40px",
                    "font_weight": "400",
                    "letter_spacing": "-0.01em",
                    "line_height": "1.1",
                },
            ),
            rx.text(
                "Em là BrandMind — người đồng hành cùng anh / chị xây dựng "
                "chiến lược thương hiệu F&B. Khi nào sẵn sàng, gửi em vài "
                "dòng về quán của mình nhé.",
                style={
                    "color": tokens.TEXT_SECONDARY,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "15px",
                    "line_height": "1.6",
                    "max_width": "520px",
                    "text_align": "center",
                },
            ),
            spacing="4",
            align="center",
        ),
        flex="1",
        width="100%",
        padding="0 24px",
    )


def _message_scroll() -> rx.Component:
    """Vertical scroll of message bubbles within a centered 920 px column."""
    return rx.scroll_area(
        rx.vstack(
            rx.foreach(BrandMindState.messages, message_bubble),
            spacing="1",
            align="stretch",
            padding="32px 24px 24px 24px",
            max_width="920px",
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
