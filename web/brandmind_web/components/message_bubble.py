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
from .tool_timeline import humanize_tool_call_label, tool_call_icon_tag

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


_RAIL_COLOR: str = "rgba(255, 255, 255, 0.32)"

_RAIL_STYLE: dict[str, str] = {
    "width": "1px",
    "background_color": _RAIL_COLOR,
    "align_self": "center",
}


def _rail_segment(*, flex: bool, height: str = "8px") -> rx.Component:
    """One vertical rail span inside a bullet column.

    ``flex=True`` lets the segment grow to fill remaining space below
    the icon; ``flex=False`` is a fixed stub used above the icon. The
    default 8 px stub plus the row's content padding-top combine to
    place each icon's vertical centre on the first text line's centre
    while keeping consecutive icons close enough to read as one trace.
    """
    style = {**_RAIL_STYLE}
    if flex:
        style["flex"] = "1"
        style["min_height"] = "10px"
    else:
        style["height"] = height
    return rx.box(style=style)


def _timeline_entry(entry: rx.Var[TimelineEntry], index: rx.Var[int]) -> rx.Component:
    """Render one chronological reasoning step within the timeline.

    The row is a horizontal pair of (bullet column, content). The
    bullet column is itself a vertical stack of (rail stub, icon, rail
    fill) so the icon naturally interrupts the rail with a small gap
    on both sides — the Claude / ChatGPT timeline pattern. Stacking
    rows with no inter-row spacing makes those segments form one
    continuous rail through the entire timeline. The very first row
    uses an invisible spacer in place of its rail stub so the trace
    visibly begins AT the first icon.
    """
    is_thinking = entry.kind == "thinking"
    tool_done = (entry.tool_call is not None) & (entry.tool_call.result != "")

    icon = rx.cond(
        is_thinking,
        rx.box(
            style={
                "width": "8px",
                "height": "8px",
                "border_radius": tokens.RADIUS_PILL,
                "background_color": tokens.TEXT_MUTED,
                "margin": "6px 0",
            },
        ),
        rx.icon(
            tag=tool_call_icon_tag(
                entry.tool_call.tool_name, entry.tool_call.arguments
            ),
            size=14,
            color=rx.cond(
                tool_done,
                tokens.ACCENT_TEAL_SOLID,
                tokens.TEXT_MUTED,
            ),
            style={"margin": "6px 0"},
        ),
    )

    rail_top = rx.cond(
        index == 0,
        rx.box(style={"width": "1px", "height": "8px"}),
        _rail_segment(flex=False),
    )

    bullet_column = rx.vstack(
        rail_top,
        icon,
        _rail_segment(flex=True),
        spacing="0",
        align="center",
        style={
            "width": "20px",
            "min_width": "20px",
            "align_self": "stretch",
        },
    )

    content = rx.cond(
        is_thinking,
        _thinking_markdown(entry.thinking_text),
        rx.hstack(
            rx.text(
                humanize_tool_call_label(
                    entry.tool_call.tool_name, entry.tool_call.arguments
                ),
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "13px",
                },
            ),
            rx.cond(
                tool_done,
                rx.fragment(),
                rx.text(
                    "running",
                    style={
                        "color": tokens.TEXT_MUTED,
                        "font_family": tokens.FONT_SANS,
                        "font_size": "12px",
                        "font_style": "italic",
                    },
                ),
            ),
            spacing="2",
            align="center",
        ),
    )

    return rx.hstack(
        bullet_column,
        rx.box(
            content,
            style={
                "flex": "1",
                "padding": "11px 0 8px 0",
            },
        ),
        spacing="3",
        align="stretch",
        width="100%",
    )


def _timeline_summary_label(message: rx.Var[ChatMessage]) -> rx.Var:
    """Short label shown next to the timeline chevron.

    While the turn streams: ``Thinking…``. After it closes: either
    ``Thought for Ns`` when a duration was captured, or a plain
    ``Reasoning`` fallback. The truthy check covers both empty
    strings and the JS ``undefined`` that Reflex emits when a freshly
    added ``ChatMessage`` field is read from a list whose entries were
    materialised before the field existed (the historic
    ``Thought for undefined`` bug).
    """
    closed_label = rx.cond(
        message.turn_duration_label,
        "Thought for " + message.turn_duration_label,
        "Reasoning",
    )
    return rx.cond(message.is_streaming, "Thinking…", closed_label)


def _final_summary_row(message: rx.Var[ChatMessage]) -> rx.Component:
    """Closing row that mirrors ChatGPT's "Thought for Ns / Done" cap.

    Rendered inside the expanded timeline body once the turn has
    stopped streaming and a duration was captured. The row reuses the
    same bullet-column construction as a regular tool row so the rail
    continues into a final check icon and stops cleanly.
    """
    bullet_column = rx.vstack(
        _rail_segment(flex=False, height="8px"),
        rx.icon(
            tag="circle_check",
            size=14,
            color=tokens.ACCENT_TEAL_SOLID,
            style={"margin": "6px 0"},
        ),
        spacing="0",
        align="center",
        style={
            "width": "20px",
            "min_width": "20px",
        },
    )

    content = rx.vstack(
        rx.text(
            "Thought for " + message.turn_duration_label,
            style={
                "color": tokens.TEXT_PRIMARY,
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
            },
        ),
        rx.text(
            "Done",
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
            },
        ),
        spacing="0",
        align="start",
    )

    row = rx.hstack(
        bullet_column,
        rx.box(
            content,
            style={"flex": "1", "padding": "11px 0 4px 0"},
        ),
        spacing="3",
        align="start",
        width="100%",
    )

    return rx.cond(
        message.is_streaming,
        rx.fragment(),
        rx.cond(message.turn_duration_label, row, rx.fragment()),
    )


def _reasoning_timeline(
    message: rx.Var[ChatMessage], message_index: int
) -> rx.Component:
    """Render the agent's interleaved reasoning trace as a connected thread."""
    from ..state import BrandMindState

    header = rx.hstack(
        rx.icon(
            tag=rx.cond(message.timeline_expanded, "chevron_down", "chevron_right"),
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
            rx.foreach(
                message.timeline,
                lambda entry, idx: _timeline_entry(entry, idx),
            ),
            _final_summary_row(message),
            spacing="0",
            align="stretch",
            width="100%",
        ),
        style={
            "padding": "4px 0 4px 0",
            "margin_left": "4px",
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


def _agent_bubble(message: rx.Var[ChatMessage], message_index: int) -> rx.Component:
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
