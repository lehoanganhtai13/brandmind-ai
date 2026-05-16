"""Chat message bubble — user (right-aligned) or agent (left-aligned).

Matches ``docs/web_design.md`` § 9.3.1. The agent variant supports
three sub-features:

* :class:`ThinkingExpansion` — collapsible "Thinking" pre-amble
  (italic, ``text.secondary`` foreground, default collapsed).
* :class:`ToolCallTimeline` — inline tool-call cards interleaved
  above the body text.
* :class:`StreamingTokenContainer` — typing cursor while the agent
  message is still streaming. The cursor is a blinking ``▍`` that
  reuses the body text color so it reads as part of the same line.

Streaming tokens append directly to ``ChatMessage.content`` in state;
this component just renders the current text plus the optional cursor
without any animation on the container itself.
"""

from __future__ import annotations

import reflex as rx

from ..models import ChatMessage
from . import tokens
from .tool_timeline import tool_call_card


def _thinking_expansion(message: rx.Var[ChatMessage]) -> rx.Component:
    """Collapsible thinking section above the agent body text."""
    return rx.cond(
        message.thinking != "",
        rx.accordion.root(
            rx.accordion.item(
                header=rx.text(
                    "Thinking",
                    style={
                        "color": tokens.TEXT_MUTED,
                        "font_family": tokens.FONT_MONO,
                        "font_size": "11px",
                        "letter_spacing": "0.08em",
                    },
                ),
                content=rx.text(
                    message.thinking,
                    style={
                        "color": tokens.TEXT_SECONDARY,
                        "font_family": tokens.FONT_SANS,
                        "font_size": "13px",
                        "font_style": "italic",
                        "line_height": "1.5",
                        "white_space": "pre-wrap",
                    },
                ),
                value="thinking",
            ),
            type="single",
            collapsible=True,
            variant="ghost",
            width="100%",
        ),
        rx.fragment(),
    )


def _streaming_cursor() -> rx.Component:
    """Blinking 1-second-cycle cursor appended while streaming."""
    return rx.text(
        "▍",
        style={
            "color": tokens.ACCENT_TEAL_SOLID,
            "animation": "bm-blink 1s step-start infinite",
            "display": "inline-block",
            "margin_left": "2px",
        },
    )


def _agent_bubble(message: rx.Var[ChatMessage]) -> rx.Component:
    """Render the agent variant of a message bubble."""
    return rx.vstack(
        _thinking_expansion(message),
        rx.cond(
            message.tool_calls.length() > 0,
            rx.vstack(
                rx.foreach(message.tool_calls, tool_call_card),
                spacing="2",
                align="start",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.box(
            rx.text(
                message.content,
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "15px",
                    "line_height": "1.55",
                    "white_space": "pre-wrap",
                    "display": "inline",
                },
            ),
            rx.cond(message.is_streaming, _streaming_cursor(), rx.fragment()),
            style={
                "display": "block",
                "width": "100%",
            },
        ),
        spacing="2",
        align="start",
        padding="12px 0",
        width="100%",
        max_width="100%",
    )


def _user_bubble(message: rx.Var[ChatMessage]) -> rx.Component:
    """Render the user variant — right-aligned capsule."""
    return rx.hstack(
        rx.spacer(),
        rx.box(
            rx.text(
                message.content,
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "15px",
                    "line_height": "1.55",
                    "white_space": "pre-wrap",
                },
            ),
            padding="12px 16px",
            style={
                "background_color": tokens.BG_SURFACE_2,
                "border_radius": tokens.RADIUS_LG,
                "max_width": "70%",
            },
        ),
        spacing="0",
        align="start",
        padding="8px 0",
        width="100%",
    )


def message_bubble(message: rx.Var[ChatMessage]) -> rx.Component:
    """Render the message bubble matching ``message.role``."""
    return rx.cond(
        message.role == "user",
        _user_bubble(message),
        _agent_bubble(message),
    )
