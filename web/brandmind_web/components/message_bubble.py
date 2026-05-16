"""Chat message bubble — user (right-aligned capsule) and agent (left, framed).

Implements ``docs/web_design.md`` § 9.3.1:
- ``user`` variant: right-aligned, teal-tinted capsule.
- ``agent`` variant: left-aligned, ``bg.surface.1`` framed page with hairline
  border. Markdown rendered inline via :func:`rx.markdown`; code blocks use
  ``font.mono`` against ``bg.surface.2`` per § 9.3.1.

The agent variant also surfaces:
- :func:`_thinking_expansion` — collapsible "Suy nghĩ" pre-amble.
- :func:`tool_call_card` — inline tool-call cards above the body.
- :func:`_streaming_cursor` — typing cursor while the turn streams.
"""

from __future__ import annotations

import reflex as rx

from ..models import ChatMessage
from . import tokens
from .tool_timeline import tool_call_card

_MARKDOWN_PARAGRAPH_STYLE: dict[str, str] = {
    "color": tokens.TEXT_PRIMARY,
    "font_family": tokens.FONT_SANS,
    "font_size": "15px",
    "line_height": "1.65",
    "margin": "0 0 12px 0",
}


def _thinking_expansion(message: rx.Var[ChatMessage]) -> rx.Component:
    """Collapsible "Suy nghĩ" section above the agent body text."""
    return rx.cond(
        message.thinking != "",
        rx.accordion.root(
            rx.accordion.item(
                header=rx.text(
                    "Suy nghĩ",
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
                        "line_height": "1.55",
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
    """Blinking 1-second-cycle cursor appended while a turn streams."""
    return rx.text(
        "▍",
        style={
            "color": tokens.ACCENT_TEAL_SOLID,
            "animation": "bm-blink 1s step-start infinite",
            "display": "inline-block",
            "margin_left": "2px",
        },
    )


def _agent_body(message: rx.Var[ChatMessage]) -> rx.Component:
    """Render the agent message body with proper markdown styling.

    Uses :func:`rx.markdown` so the agent's bold / italic / list formatting
    surfaces as real typography instead of leaking raw markdown literals into
    the chat. The trailing streaming cursor renders only while the turn is
    still in flight.
    """
    return rx.box(
        rx.markdown(
            message.content,
            component_map={
                "p": lambda text: rx.text(text, style=_MARKDOWN_PARAGRAPH_STYLE),
                "strong": lambda text: rx.text(
                    text,
                    style={
                        "color": tokens.TEXT_PRIMARY,
                        "font_weight": "600",
                        "display": "inline",
                    },
                ),
                "em": lambda text: rx.text(
                    text,
                    style={
                        "color": tokens.TEXT_PRIMARY,
                        "font_style": "italic",
                        "display": "inline",
                    },
                ),
                "ul": lambda items: rx.list.unordered(
                    items,
                    style={
                        "color": tokens.TEXT_PRIMARY,
                        "font_family": tokens.FONT_SANS,
                        "font_size": "15px",
                        "line_height": "1.65",
                        "padding_left": "1.2em",
                        "margin": "0 0 12px 0",
                    },
                ),
                "ol": lambda items: rx.list.ordered(
                    items,
                    style={
                        "color": tokens.TEXT_PRIMARY,
                        "font_family": tokens.FONT_SANS,
                        "font_size": "15px",
                        "line_height": "1.65",
                        "padding_left": "1.4em",
                        "margin": "0 0 12px 0",
                    },
                ),
                "li": lambda text: rx.list.item(
                    text,
                    style={
                        "margin": "0 0 4px 0",
                    },
                ),
                "code": lambda text: rx.text(
                    text,
                    style={
                        "font_family": tokens.FONT_MONO,
                        "font_size": "13px",
                        "background_color": tokens.BG_SURFACE_2,
                        "color": tokens.TEXT_PRIMARY,
                        "padding": "1px 6px",
                        "border_radius": tokens.RADIUS_SM,
                        "display": "inline",
                    },
                ),
            },
        ),
        rx.cond(message.is_streaming, _streaming_cursor(), rx.fragment()),
        style={"width": "100%"},
    )


def _agent_bubble(message: rx.Var[ChatMessage]) -> rx.Component:
    """Render the agent variant — left-aligned framed page on ``bg.surface.1``."""
    body = rx.vstack(
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
        _agent_body(message),
        spacing="3",
        align="start",
        width="100%",
        padding="16px 20px",
        style={
            "background_color": tokens.BG_SURFACE_1,
            "border": f"1px solid {tokens.GLASS_BORDER}",
            "border_radius": tokens.RADIUS_LG,
            "max_width": "100%",
        },
    )
    return rx.flex(
        body,
        justify="start",
        width="100%",
        padding="10px 0",
    )


def _user_bubble(message: rx.Var[ChatMessage]) -> rx.Component:
    """Render the user variant — right-aligned capsule with teal-tinted fill."""
    bubble = rx.box(
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
        padding="10px 14px",
        style={
            "background_color": tokens.ACCENT_TEAL_MUTED,
            "border": f"1px solid {tokens.ACCENT_TEAL_MUTED}",
            "border_radius": tokens.RADIUS_LG,
            "max_width": "min(620px, 75%)",
        },
    )
    return rx.flex(
        bubble,
        justify="end",
        width="100%",
        padding="8px 0",
    )


def message_bubble(message: rx.Var[ChatMessage]) -> rx.Component:
    """Render the message bubble matching ``message.role``."""
    return rx.cond(
        message.role == "user",
        _user_bubble(message),
        _agent_bubble(message),
    )
