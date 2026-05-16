"""Chat message bubble — user (right-aligned capsule) and agent (timeline + body).

Implements ``docs/web_design.md`` § 9.3.1 with the unified reasoning
timeline pattern (Claude / ChatGPT style):

- The user variant stays a right-aligned teal-tinted capsule.
- The agent variant renders its reasoning trace as ONE chronological
  timeline (thinking blocks + tool calls interleaved). The timeline
  auto-expands while ``is_streaming`` so the user can watch the trace
  build up live. After the turn closes, the timeline collapses to a
  single inline "Thought for Ns" toggle that re-expands on click.
- The final agent body markdown surfaces below the timeline as
  flowing prose, no enclosing box — Codex review Finding 3.
"""

from __future__ import annotations

import reflex as rx

from ..models import ChatMessage, TimelineEntry
from . import tokens
from .tool_timeline import humanize_tool_label

_MARKDOWN_PARAGRAPH_STYLE: dict[str, str] = {
    "color": tokens.TEXT_PRIMARY,
    "font_family": tokens.FONT_SANS,
    "font_size": "15px",
    "line_height": "1.65",
    "margin": "0 0 12px 0",
}

_THINKING_TEXT_STYLE: dict[str, str] = {
    "color": tokens.TEXT_SECONDARY,
    "font_family": tokens.FONT_SANS,
    "font_size": "13px",
    "font_style": "italic",
    "line_height": "1.6",
    "margin": "0 0 4px 0",
}

_THINKING_STRONG_STYLE: dict[str, str] = {
    "color": tokens.TEXT_SECONDARY,
    "font_family": tokens.FONT_SANS,
    "font_size": "13px",
    "font_style": "italic",
    "font_weight": "600",
}

_THINKING_EM_STYLE: dict[str, str] = {
    "color": tokens.TEXT_SECONDARY,
    "font_family": tokens.FONT_SANS,
    "font_size": "13px",
    "font_style": "italic",
}


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


def _thinking_markdown(text: rx.Var[str]) -> rx.Component:
    """Render thinking text as markdown with the italic secondary palette."""
    return rx.markdown(
        text,
        component_map={
            "p": lambda body: rx.text(body, style=_THINKING_TEXT_STYLE),
            "strong": lambda body: rx.el.span(body, style=_THINKING_STRONG_STYLE),
            "em": lambda body: rx.el.span(body, style=_THINKING_EM_STYLE),
            "ul": lambda items: rx.list.unordered(
                items,
                style={**_THINKING_TEXT_STYLE, "padding_left": "1.2em"},
            ),
            "ol": lambda items: rx.list.ordered(
                items,
                style={**_THINKING_TEXT_STYLE, "padding_left": "1.4em"},
            ),
            "li": lambda body: rx.list.item(body, style={"margin": "0 0 4px 0"}),
        },
    )


def _timeline_entry(entry: rx.Var[TimelineEntry]) -> rx.Component:
    """Render one chronological reasoning step within the timeline.

    The row is ``position: relative`` so the bullet can be absolutely
    placed centered on the wrapper's left rail. Content sits in the
    normal flow with a 28 px left padding that clears the bullet
    column.
    """
    is_thinking = entry.kind == "thinking"
    tool_done = (entry.tool_call is not None) & (
        entry.tool_call.result != ""
    )

    bullet = rx.cond(
        is_thinking,
        rx.box(
            style={
                "width": "8px",
                "height": "8px",
                "border_radius": tokens.RADIUS_PILL,
                "background_color": tokens.TEXT_MUTED,
                "position": "absolute",
                "left": "-4px",
                "top": "10px",
            },
        ),
        rx.center(
            rx.icon(
                tag=rx.cond(tool_done, "circle_check", "loader"),
                size=12,
                color=rx.cond(
                    tool_done,
                    tokens.ACCENT_TEAL_SOLID,
                    tokens.TEXT_MUTED,
                ),
            ),
            style={
                "width": "16px",
                "height": "16px",
                "background_color": tokens.BG_CANVAS,
                "border_radius": tokens.RADIUS_PILL,
                "position": "absolute",
                "left": "-8px",
                "top": "4px",
            },
        ),
    )

    content = rx.cond(
        is_thinking,
        _thinking_markdown(entry.thinking_text),
        rx.hstack(
            rx.text(
                humanize_tool_label(entry.tool_call.tool_name),
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "13px",
                },
            ),
            rx.text(
                rx.cond(tool_done, "done", "running"),
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "12px",
                    "font_style": "italic",
                },
            ),
            spacing="2",
            align="center",
            padding_top="2px",
        ),
    )

    return rx.box(
        bullet,
        content,
        style={
            "position": "relative",
            "padding_left": "20px",
            "padding_bottom": "10px",
            "width": "100%",
        },
    )


def _timeline_summary_label(message: rx.Var[ChatMessage]) -> rx.Var:
    """Short label shown next to the timeline chevron.

    While the turn streams: "Thinking…". After the turn closes: "Reasoning"
    — kept deliberately ambiguous on duration because Reflex's Pydantic
    serialisation drops some scalar defaults when a model is mutated
    in-place inside a list field, which historically rendered as
    ``Thought for undefined``.
    """
    return rx.cond(message.is_streaming, "Thinking…", "Reasoning")


def _reasoning_timeline(
    message: rx.Var[ChatMessage], message_index: int
) -> rx.Component:
    """Render the agent's interleaved reasoning trace as a connected thread."""
    from ..state import BrandMindState

    header = rx.hstack(
        rx.icon(
            tag=rx.cond(
                message.timeline_expanded, "chevron_down", "chevron_right"
            ),
            size=13,
            color=tokens.TEXT_MUTED,
        ),
        rx.el.span(
            _timeline_summary_label(message),
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
                "font_style": "italic",
            },
        ),
        spacing="1",
        align="center",
        on_click=BrandMindState.toggle_timeline(message_index),
        style={"cursor": "pointer", "user_select": "none"},
    )

    expanded = rx.box(
        rx.vstack(
            rx.foreach(message.timeline, _timeline_entry),
            spacing="0",
            align="stretch",
            width="100%",
        ),
        style={
            "padding": "8px 0 4px 0",
            "margin_left": "10px",
            "border_left": f"1px solid {tokens.GLASS_BORDER}",
        },
    )

    return rx.cond(
        message.timeline.length() > 0,
        rx.vstack(
            header,
            rx.cond(message.timeline_expanded, expanded, rx.fragment()),
            spacing="1",
            align="stretch",
            width="100%",
        ),
        rx.fragment(),
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


def _agent_bubble(
    message: rx.Var[ChatMessage], message_index: int
) -> rx.Component:
    """Agent turn — left-bordered editorial column, no enclosing box."""
    body = rx.vstack(
        _reasoning_timeline(message, message_index),
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


def message_bubble(
    message: rx.Var[ChatMessage], message_index: rx.Var[int]
) -> rx.Component:
    """Render the message bubble matching ``message.role``."""
    return rx.cond(
        message.role == "user",
        _user_bubble(message),
        _agent_bubble(message, message_index),
    )
