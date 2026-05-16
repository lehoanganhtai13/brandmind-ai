"""Chat message bubble — user (right-aligned capsule) and agent (left, framed).

Implements ``docs/web_design.md`` § 9.3.1 with Codex-review Findings 2, 3,
and 5 folded in:

- The agent variant no longer wraps its body in a heavy framed card.
  A 2 px teal left-border replaces the surrounding box so turns are
  distinguished by an editorial gutter, not an old-web panel border.
- Tool-call cards render BEFORE the "Thinking" accordion, so concrete
  actions surface first and the reasoning trace stays a secondary detail.
- The "Thinking" accordion is now a small italic toggle with a 12 px
  chevron; its body is rendered through :func:`rx.markdown` so bold /
  italic / list formatting survives the trip from the model.
- The user variant stays a right-aligned teal-tinted capsule.
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

_THINKING_MD_STYLE: dict[str, str] = {
    "color": tokens.TEXT_SECONDARY,
    "font_family": tokens.FONT_SANS,
    "font_size": "13px",
    "font_style": "italic",
    "line_height": "1.6",
    "margin": "0 0 8px 0",
}


def _thinking_body(message: rx.Var[ChatMessage]) -> rx.Component:
    """Render the thinking trace as markdown so emphasis survives.

    Inline elements (``strong`` / ``em``) render as ``<span>`` so they do
    not nest inside the paragraph's ``<p>`` — that combination triggers
    hydration errors in React 18.
    """
    inline_strong = {
        "color": tokens.TEXT_SECONDARY,
        "font_family": tokens.FONT_SANS,
        "font_size": "13px",
        "font_style": "italic",
        "font_weight": "600",
    }
    inline_em = {
        "color": tokens.TEXT_SECONDARY,
        "font_family": tokens.FONT_SANS,
        "font_size": "13px",
        "font_style": "italic",
    }
    return rx.markdown(
        message.thinking,
        component_map={
            "p": lambda text: rx.text(text, style=_THINKING_MD_STYLE),
            "strong": lambda text: rx.el.span(text, style=inline_strong),
            "em": lambda text: rx.el.span(text, style=inline_em),
            "ul": lambda items: rx.list.unordered(
                items,
                style={
                    **_THINKING_MD_STYLE,
                    "padding_left": "1.2em",
                },
            ),
            "ol": lambda items: rx.list.ordered(
                items,
                style={
                    **_THINKING_MD_STYLE,
                    "padding_left": "1.4em",
                },
            ),
            "li": lambda text: rx.list.item(text, style={"margin": "0 0 4px 0"}),
        },
    )


def _thinking_expansion(message: rx.Var[ChatMessage]) -> rx.Component:
    """Minimal collapsible "Thinking" toggle below tool pills.

    Renders as a small italic sans label with a 12 px chevron so it reads
    as inline metadata, not a primary UI control. Default collapsed.
    """
    return rx.cond(
        message.thinking != "",
        rx.accordion.root(
            rx.accordion.item(
                header=rx.hstack(
                    rx.icon(
                        tag="chevron_down",
                        size=12,
                        color=tokens.TEXT_MUTED,
                    ),
                    rx.text(
                        "Thinking",
                        style={
                            "color": tokens.TEXT_MUTED,
                            "font_family": tokens.FONT_SANS,
                            "font_size": "12px",
                            "font_style": "italic",
                        },
                    ),
                    spacing="1",
                    align="center",
                ),
                content=rx.box(
                    _thinking_body(message),
                    style={"padding": "6px 0 0 18px"},
                ),
                value="thinking",
            ),
            type="single",
            collapsible=True,
            default_value="",
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
    """Agent message body rendered as proper markdown."""
    return rx.box(
        rx.markdown(
            message.content,
            component_map={
                "p": lambda text: rx.text(text, style=_MARKDOWN_PARAGRAPH_STYLE),
                "strong": lambda text: rx.el.span(
                    text,
                    style={
                        "color": tokens.TEXT_PRIMARY,
                        "font_weight": "600",
                    },
                ),
                "em": lambda text: rx.el.span(
                    text,
                    style={
                        "color": tokens.TEXT_PRIMARY,
                        "font_style": "italic",
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
                "li": lambda text: rx.list.item(text, style={"margin": "0 0 4px 0"}),
                "code": lambda text: rx.el.code(
                    text,
                    style={
                        "font_family": tokens.FONT_MONO,
                        "font_size": "13px",
                        "background_color": tokens.BG_SURFACE_2,
                        "color": tokens.TEXT_PRIMARY,
                        "padding": "1px 6px",
                        "border_radius": tokens.RADIUS_SM,
                    },
                ),
            },
        ),
        rx.cond(message.is_streaming, _streaming_cursor(), rx.fragment()),
        style={"width": "100%"},
    )


def _agent_bubble(message: rx.Var[ChatMessage]) -> rx.Component:
    """Agent turn — left-bordered editorial column, no enclosing box."""
    body = rx.vstack(
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
        _thinking_expansion(message),
        _agent_body(message),
        spacing="3",
        align="start",
        width="100%",
        padding="6px 0 6px 18px",
        style={
            "border_left": f"2px solid {tokens.ACCENT_TEAL_MUTED}",
        },
    )
    return rx.flex(
        body,
        justify="start",
        width="100%",
        padding="10px 0",
    )


def _user_bubble(message: rx.Var[ChatMessage]) -> rx.Component:
    """User turn — right-aligned capsule with teal-tinted fill."""
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
