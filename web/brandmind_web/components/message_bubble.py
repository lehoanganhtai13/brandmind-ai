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

from ..models import ChatMessage, ContentBlock, ThinkingSegment, TimelineEntry
from . import tokens
from .tool_timeline import humanize_tool_call_label, tool_call_icon_tag

_MARKDOWN_PARAGRAPH_STYLE: dict[str, str] = {
    "color": tokens.TEXT_PRIMARY,
    "font_family": tokens.FONT_SANS,
    "font_size": "15px",
    "line_height": "1.65",
    "margin": "0 0 12px 0",
}

_MARKDOWN_TABLE_STYLE: dict[str, str] = {
    "width": "100%",
    "border_collapse": "collapse",
    "margin": "8px 0 16px 0",
    "font_family": tokens.FONT_SANS,
    "font_size": "14px",
    "line_height": "1.55",
    "color": tokens.TEXT_PRIMARY,
    "border": f"1px solid {tokens.GLASS_BORDER}",
    "border_radius": tokens.RADIUS_MD,
    "overflow": "hidden",
}

_MARKDOWN_TABLE_TH_STYLE: dict = {
    "text_align": "left",
    "vertical_align": "top",
    "padding": "10px 14px",
    "font_weight": "600",
    "color": tokens.TEXT_PRIMARY,
    "background_color": tokens.BG_SURFACE_2,
    "border_right": f"1px solid {tokens.GLASS_BORDER}",
    "border_bottom": f"1px solid {tokens.GLASS_BORDER}",
    "&:last-child": {"border_right": "none"},
}

_MARKDOWN_TABLE_TD_STYLE: dict = {
    "text_align": "left",
    "vertical_align": "top",
    "padding": "10px 14px",
    "color": tokens.TEXT_PRIMARY,
    "border_right": f"1px solid {tokens.GLASS_BORDER}",
    "&:last-child": {"border_right": "none"},
}

_THINKING_TEXT_STYLE: dict[str, str] = {
    "color": tokens.TEXT_SECONDARY,
    "font_family": tokens.FONT_SANS,
    "font_size": "13px",
    "font_style": "italic",
    "line_height": "1.55",
    "margin": "0",
}


_THINKING_BODY_MARKDOWN_P_STYLE: dict[str, str] = {
    "color": tokens.TEXT_SECONDARY,
    "font_family": tokens.FONT_SANS,
    "font_size": "13px",
    "font_style": "italic",
    "line_height": "1.55",
    "margin": "0 0 6px 0",
}

_THINKING_BODY_MARKDOWN_STRONG_STYLE: dict[str, str] = {
    "color": tokens.TEXT_PRIMARY,
    "font_weight": "600",
    "font_style": "italic",
}

_THINKING_BODY_MARKDOWN_EM_STYLE: dict[str, str] = {
    "color": tokens.TEXT_SECONDARY,
    "font_style": "italic",
    "font_weight": "400",
}

_THINKING_BODY_MARKDOWN_CODE_STYLE: dict[str, str] = {
    "font_family": tokens.FONT_MONO,
    "font_size": "12px",
    "background_color": tokens.BG_SURFACE_2,
    "color": tokens.TEXT_PRIMARY,
    "padding": "1px 5px",
    "border_radius": tokens.RADIUS_SM,
}


def _thinking_body_markdown(text: rx.Var[str]) -> rx.Component:
    """Render a body slice through markdown with the timeline palette.

    Each body segment may contain inline markdown — ``**bold**``,
    ``*italic*``, ``` `code` ```, or short lists — that the agent
    folded into the prose to flag key terms. The component_map keeps
    every rendered leaf inside the timeline's italic-secondary palette
    while still surfacing the model's emphasis cues so the body reads
    as authored, not as one flat italic block.

    Hook-order safety: this component is reached via ``rx.foreach``
    over a stable per-row segment list; each segment maps to its own
    independent React instance, so the ``rx.cond`` swap between
    :func:`rx.text` (header) and :func:`rx.markdown` (body) lives at a
    different tree position per item and never reuses the same hook
    stack across two component shapes.
    """
    return rx.markdown(
        text,
        component_map={
            "p": lambda body: rx.text(body, style=_THINKING_BODY_MARKDOWN_P_STYLE),
            "strong": lambda body: rx.el.span(
                body, style=_THINKING_BODY_MARKDOWN_STRONG_STYLE
            ),
            "em": lambda body: rx.el.span(body, style=_THINKING_BODY_MARKDOWN_EM_STYLE),
            "code": lambda body: rx.el.code(
                body, style=_THINKING_BODY_MARKDOWN_CODE_STYLE
            ),
            "ul": lambda items: rx.list.unordered(
                items,
                style={**_THINKING_BODY_MARKDOWN_P_STYLE, "padding_left": "1.2em"},
            ),
            "ol": lambda items: rx.list.ordered(
                items,
                style={**_THINKING_BODY_MARKDOWN_P_STYLE, "padding_left": "1.4em"},
            ),
            "li": lambda body: rx.list.item(body, style={"margin": "0 0 3px 0"}),
        },
    )


def _thinking_segment(seg: rx.Var[ThinkingSegment], index: rx.Var[int]) -> rx.Component:
    """Render one parsed slice of a thinking block (header or body).

    Headers render as a heavier-weight primary-palette ``rx.text`` so
    the eye locks onto reasoning-step titles; bodies render through
    :func:`_thinking_body_markdown` so inline ``**bold**``, ``*em*``,
    ``` `code` ``` and short lists from the agent's prose still
    surface inside the italic-secondary timeline palette. The first
    segment of a row carries no top margin so its first text line
    centres on the bullet icon at the same vertical position as a
    tool-row label; subsequent headers gain a top margin to break out
    from the preceding body paragraph.
    """
    is_header = seg.kind == "header"
    is_first = index == 0
    header_top_margin = rx.cond(is_first, "0", "10px")
    return rx.cond(
        is_header,
        rx.text(
            seg.text,
            style={
                "color": tokens.TEXT_PRIMARY,
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "font_style": "italic",
                "font_weight": "600",
                "line_height": "1.55",
                "margin_top": header_top_margin,
                "margin_bottom": "2px",
            },
        ),
        rx.box(_thinking_body_markdown(seg.text)),
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

    icon = rx.box(
        rx.box(
            style={
                "width": "8px",
                "height": "8px",
                "border_radius": tokens.RADIUS_PILL,
                "background_color": rx.cond(
                    is_thinking | tool_done,
                    tokens.ACCENT_TEAL_SOLID,
                    tokens.TEXT_MUTED,
                ),
                "display": rx.cond(is_thinking, "block", "none"),
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
            style={"display": rx.cond(is_thinking, "none", "block")},
        ),
        style={
            "display": "flex",
            "align_items": "center",
            "justify_content": "center",
            "width": "20px",
            "height": "20px",
            "flex_shrink": "0",
        },
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

    content = rx.hstack(
        rx.box(
            rx.foreach(
                entry.thinking_segments,
                lambda seg, idx: _thinking_segment(seg, idx),
            ),
            display=rx.cond(is_thinking, "block", "none"),
            style={"flex": "1", "min_width": "0"},
        ),
        rx.text(
            humanize_tool_call_label(
                entry.tool_call.tool_name,
                entry.tool_call.arguments,
            ),
            style={
                "color": tokens.TEXT_PRIMARY,
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "line_height": "1.55",
                "display": rx.cond(is_thinking, "none", "block"),
            },
        ),
        rx.text(
            "running",
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
                "font_style": "italic",
                "display": rx.cond((~is_thinking) & (~tool_done), "block", "none"),
            },
        ),
        spacing="2",
        align=rx.cond(is_thinking, "start", "center"),
    )

    return rx.hstack(
        bullet_column,
        rx.box(
            content,
            style={
                "flex": "1",
                "padding": "8px 0 4px 0",
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

    row_display = rx.cond(
        (~message.is_streaming) & (message.turn_duration_label != ""),
        "flex",
        "none",
    )
    return rx.box(row, display=row_display)


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

    has_timeline = message.timeline.length() > 0
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
        display=rx.cond(has_timeline & message.timeline_expanded, "block", "none"),
    )

    return rx.vstack(
        header,
        expanded,
        spacing="1",
        align="stretch",
        width="100%",
        display=rx.cond(has_timeline, "flex", "none"),
    )


def _block_summary_label(block: rx.Var[ContentBlock]) -> rx.Var:
    """Per-block header label next to the chevron of a reasoning block.

    Mirrors :func:`_timeline_summary_label` but reads the block's own
    ``is_done`` and ``duration_label`` so two thought blocks within the
    same turn render distinct labels. While the block is live, the
    header reads ``Thinking…``. Once it closes, ``Thought for Ns`` is
    used when a per-block duration was captured (live blocks) and the
    generic ``Reasoning`` label is used when the wire payload didn't
    carry one (multi-block hydration case).
    """
    closed_label = rx.cond(
        block.duration_label,
        "Thought for " + block.duration_label,
        "Reasoning",
    )
    return rx.cond(block.is_done, closed_label, "Thinking…")


def _block_reasoning_timeline(
    block: rx.Var[ContentBlock],
) -> rx.Component:
    """Render one ``reasoning_timeline`` block as a connected thinking + tool thread.

    Variant of :func:`_reasoning_timeline` scoped to a single
    ``ContentBlock``. Each block carries its own expand state and
    duration label so a turn with multiple thought traces can collapse
    the earlier ones as soon as the next assistant paragraph starts
    and toggle them independently. The chevron, header label, and
    body display all bind to ``block.expanded`` and ``block.is_done``
    rather than to message-level fields — that is the fix that turns
    two "Thought for 51s" headers into two distinct rows. The toggle
    event keys off ``block.block_id`` rather than positional indices
    so Reflex's nested-``foreach`` index aliasing cannot collide.

    Args:
        block (rx.Var[ContentBlock]): The reasoning_timeline block to
            render; ``block.timeline`` carries the thinking + tool
            entries and ``block.block_id`` is forwarded to the per-block
            toggle event so a click flips only this block's panel.

    Returns:
        component (rx.Component): The block's collapsible reasoning
            thread, ready to drop into the ordered blocks renderer.
    """
    from ..state import BrandMindState

    header = rx.hstack(
        rx.icon(
            tag=rx.cond(block.expanded, "chevron_down", "chevron_right"),
            size=13,
            color=tokens.TEXT_MUTED,
        ),
        rx.el.span(
            _block_summary_label(block),
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
                "font_style": "italic",
            },
        ),
        spacing="1",
        align="center",
        on_click=BrandMindState.toggle_block_timeline(block.block_id),
        style={"cursor": "pointer", "user_select": "none"},
    )

    has_timeline = block.timeline.length() > 0
    expanded = rx.box(
        rx.vstack(
            rx.foreach(
                block.timeline,
                lambda entry, idx: _timeline_entry(entry, idx),
            ),
            spacing="0",
            align="stretch",
            width="100%",
        ),
        style={
            "padding": "4px 0 4px 0",
            "margin_left": "4px",
        },
        display=rx.cond(has_timeline & block.expanded, "block", "none"),
    )

    return rx.vstack(
        header,
        expanded,
        spacing="1",
        align="stretch",
        width="100%",
        display=rx.cond(has_timeline, "flex", "none"),
    )


def _content_block(
    block: rx.Var[ContentBlock],
    index: rx.Var[int],
    message: rx.Var[ChatMessage],
    message_index: int,
) -> rx.Component:
    """Dispatch one ordered block to the matching renderer.

    Switches on ``block.kind``: ``assistant_text`` renders as markdown
    prose, ``reasoning_timeline`` renders as a collapsible reasoning
    thread keyed by its own per-block state. The streaming cursor only
    appears at the end of the very last ``assistant_text`` block when
    the turn is still streaming, so a progress note that has been
    superseded by a later final answer does not keep a cursor behind it.

    Args:
        block (rx.Var[ContentBlock]): The block to render.
        index (rx.Var[int]): Index of this block within
            ``message.blocks``; used for cursor visibility and as the
            block id for the per-block toggle handler.
        message (rx.Var[ChatMessage]): The owning agent message.
        message_index (int): Message index forwarded to the timeline
            toggle handler.

    Returns:
        component (rx.Component): The appropriate per-kind renderer
            wrapped in a vstack-friendly box.
    """
    is_text = block.kind == "assistant_text"
    is_last = index == message.blocks.length() - 1
    show_cursor = is_text & is_last & message.is_streaming
    return rx.cond(
        is_text,
        _assistant_text_block(block.text, show_cursor),
        _block_reasoning_timeline(block),
    )


def _blocks_renderer(message: rx.Var[ChatMessage], message_index: int) -> rx.Component:
    """Render an agent turn as the ordered live blocks.

    The Phase 1 live path: progress text → Thought → final answer in
    insertion order. The legacy single-content + single-timeline
    fallback handles persisted history that has not been promoted to
    the blocks schema yet. After all blocks, a final "Thought for Ns
    / Done" cap row is appended so the new path matches the ChatGPT
    pattern the legacy renderer already used at the bottom of the
    reasoning chain.

    Args:
        message (rx.Var[ChatMessage]): The agent message whose
            ``blocks`` list to render.
        message_index (int): Message index forwarded to the timeline
            toggle handler.

    Returns:
        component (rx.Component): A vertical stack of per-kind block
            renderers + the trailing Done cap, in that order.
    """
    return rx.vstack(
        rx.foreach(
            message.blocks,
            lambda block, idx: _content_block(block, idx, message, message_index),
        ),
        _final_summary_row(message),
        spacing="3",
        align="stretch",
        width="100%",
    )


_MARKDOWN_COMPONENT_MAP_FACTORY = None  # populated by ``_markdown_component_map``


def _markdown_component_map() -> dict:
    """Return the shared component map used by every assistant-text render.

    Hoisted so the legacy ``_agent_body`` and the new per-block renderer
    in :func:`_blocks_renderer` share the exact same markdown styling.
    Cached at module level on first use so each render does not rebuild
    the dictionary.

    Returns:
        component_map (dict): Reflex markdown component map covering
            paragraphs, emphasis, code, lists, and tables with the
            BrandMind palette + spacing tokens.
    """
    global _MARKDOWN_COMPONENT_MAP_FACTORY
    if _MARKDOWN_COMPONENT_MAP_FACTORY is None:
        _MARKDOWN_COMPONENT_MAP_FACTORY = {
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
            "table": lambda children: rx.el.table(
                children,
                style=_MARKDOWN_TABLE_STYLE,
            ),
            "thead": lambda children: rx.el.thead(children),
            "tbody": lambda children: rx.el.tbody(children),
            "tr": lambda children: rx.el.tr(
                children,
                style={
                    "border_bottom": f"1px solid {tokens.GLASS_BORDER}",
                    "&:last-child": {"border_bottom": "none"},
                },
            ),
            "th": lambda children: rx.el.th(
                children,
                style=_MARKDOWN_TABLE_TH_STYLE,
            ),
            "td": lambda children: rx.el.td(
                children,
                style=_MARKDOWN_TABLE_TD_STYLE,
            ),
        }
    return _MARKDOWN_COMPONENT_MAP_FACTORY


def _assistant_text_block(text: rx.Var[str], show_cursor: rx.Var[bool]) -> rx.Component:
    """Render one ``assistant_text`` block as markdown prose.

    Shares the markdown component_map with the legacy ``_agent_body``
    so any persisted-history paragraph and any live block use identical
    typography. ``show_cursor`` controls the trailing blink cursor so
    only the latest still-streaming block gets the cursor (the others
    have already been superseded by a later block or by the ``done``
    event).

    Args:
        text (rx.Var[str]): The block's accumulated streaming text.
        show_cursor (rx.Var[bool]): Whether to append the streaming
            cursor at the end of this block.

    Returns:
        component (rx.Component): A box containing the rendered
            markdown + an optional trailing cursor.
    """
    return rx.box(
        rx.markdown(text, component_map=_markdown_component_map()),
        rx.box(
            _streaming_cursor(),
            display=rx.cond(show_cursor, "inline-block", "none"),
        ),
        style={"width": "100%"},
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
                "table": lambda children: rx.el.table(
                    children,
                    style=_MARKDOWN_TABLE_STYLE,
                ),
                "thead": lambda children: rx.el.thead(children),
                "tbody": lambda children: rx.el.tbody(children),
                "tr": lambda children: rx.el.tr(
                    children,
                    style={
                        "border_bottom": f"1px solid {tokens.GLASS_BORDER}",
                        "&:last-child": {"border_bottom": "none"},
                    },
                ),
                "th": lambda children: rx.el.th(
                    children,
                    style=_MARKDOWN_TABLE_TH_STYLE,
                ),
                "td": lambda children: rx.el.td(
                    children,
                    style=_MARKDOWN_TABLE_TD_STYLE,
                ),
            },
        ),
        rx.box(
            _streaming_cursor(),
            display=rx.cond(message.is_streaming, "inline-block", "none"),
        ),
        style={"width": "100%"},
    )


def _legacy_agent_body(
    message: rx.Var[ChatMessage], message_index: int
) -> rx.Component:
    """Legacy timeline-then-content layout for persisted history.

    Picked when ``message.blocks`` is empty — typically after a page
    refresh that re-fetches the chat from the backend, which still
    serves the single-content + single-timeline schema (Phase 1
    intentionally avoids the backend change). The renderer matches the
    pre-blocks shape so old turns keep rendering exactly as before.

    Args:
        message (rx.Var[ChatMessage]): The agent message to render.
        message_index (int): Index of the message inside
            ``BrandMindState.messages``; forwarded to the timeline
            toggle handler.

    Returns:
        component (rx.Component): Vertical stack of (reasoning timeline,
            markdown body) — the pre-blocks layout.
    """
    return rx.vstack(
        _reasoning_timeline(message, message_index),
        _agent_body(message),
        spacing="3",
        align="start",
        width="100%",
    )


def _agent_bubble(message: rx.Var[ChatMessage], message_index: int) -> rx.Component:
    """Agent turn — left-bordered editorial column, no enclosing box.

    Picks the ordered-blocks renderer when the turn carries live
    ``blocks`` (Phase 1 SSE path produces them on every fresh stream),
    otherwise falls back to the legacy timeline-then-content layout
    so persisted history fetched from the server stays readable.

    Args:
        message (rx.Var[ChatMessage]): The agent message to render.
        message_index (int): Index of the message inside
            ``BrandMindState.messages``; forwarded to the timeline
            toggle handler.

    Returns:
        component (rx.Component): A flex row carrying the left-bordered
            agent body with either the ordered-blocks or legacy
            renderer selected at render time.
    """
    body = rx.vstack(
        rx.cond(
            message.blocks.length() > 0,
            _blocks_renderer(message, message_index),
            _legacy_agent_body(message, message_index),
        ),
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
