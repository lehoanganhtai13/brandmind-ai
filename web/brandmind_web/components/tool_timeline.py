"""Inline tool-call timeline card.

Renders one entry inside an agent message body for each tool call the
agent dispatches. Matches ``docs/web_design.md`` § 9.3.4 — tool icon,
human-readable English label, status pill (running / done). Cards are
inline with the message body so the chat reads as a single chronological
strip. The label table is restricted to tools actually registered in
:mod:`core.brand_strategy.agent_config` — alias keys (Codex review
Finding 4) have been removed.
"""

from __future__ import annotations

import reflex as rx

from ..models import ToolCallInfo
from . import tokens

_TOOL_LABELS: dict[str, str] = {
    "ls": "List workspace files",
    "read_file": "Read workspace file",
    "edit_file": "Update workspace file",
    "grep": "Search workspace",
    "write_todos": "Update todo list",
    "tool_search": "Search for tools",
    "load_tools": "Load specialist tools",
    "unload_tools": "Unload specialist tools",
    "task": "Delegate to specialist agent",
    "report_progress": "Advance phase",
    "search_knowledge_graph": "Search Knowledge Graph",
    "search_document_library": "Search document library",
    "search_web": "Search the web",
    "scrape_web_content": "Read web page",
    "browse_and_research": "Browse and research",
    "deep_research": "Deep research",
    "analyze_social_profile": "Analyze social profile",
    "get_search_autocomplete": "Get customer search suggestions",
    "generate_image": "Generate brand image",
    "edit_image": "Edit image",
    "export_to_markdown": "Export to Markdown",
    "list_artifacts": "List artifacts",
    "generate_brand_key": "Compose Brand Key one-pager",
    "generate_document": "Compose strategy document",
    "generate_presentation": "Compose presentation deck",
    "generate_spreadsheet": "Compose KPI spreadsheet",
}

_TOOL_ICON_TAGS: dict[str, str] = {
    "ls": "folder",
    "read_file": "file_text",
    "edit_file": "file_pen_line",
    "grep": "search",
    "write_todos": "list_checks",
    "tool_search": "search",
    "load_tools": "wrench",
    "unload_tools": "wrench",
    "task": "users",
    "report_progress": "arrow_right",
    "search_knowledge_graph": "search",
    "search_document_library": "search",
    "search_web": "globe",
    "scrape_web_content": "globe",
    "browse_and_research": "globe",
    "deep_research": "globe",
    "analyze_social_profile": "users",
    "get_search_autocomplete": "search",
    "generate_image": "image",
    "edit_image": "image",
    "export_to_markdown": "file_text",
    "list_artifacts": "folder",
    "generate_brand_key": "palette",
    "generate_document": "file_text",
    "generate_presentation": "presentation",
    "generate_spreadsheet": "table_2",
}

_DEFAULT_TOOL_ICON: str = "code"


def humanize_tool_label(tool_name: rx.Var[str]) -> rx.Var:
    """Project a raw tool name to its English label, fall back to the raw value.

    The mapping is unrolled into a chained :func:`rx.cond` ladder because
    Reflex Vars cannot be looked up against a Python dict at compile time.
    Used by the reasoning-timeline rows as well as legacy tool pill cards.
    """
    label: rx.Var = tool_name
    for raw, human in _TOOL_LABELS.items():
        label = rx.cond(tool_name == raw, human, label)
    return label


def tool_icon_tag(tool_name: rx.Var[str]) -> rx.Var:
    """Project a raw tool name to its Lucide icon tag.

    Falls back to a generic code-fence glyph (``"code"`` / ``</>``) when
    the tool isn't in the known set so newly added catalog tools still
    surface with a sensible glyph instead of an empty box.
    """
    tag: rx.Var = rx.Var.create(_DEFAULT_TOOL_ICON)
    for raw, icon in _TOOL_ICON_TAGS.items():
        tag = rx.cond(tool_name == raw, icon, tag)
    return tag


def _report_progress_label(arguments: rx.Var) -> rx.Var:
    """Pick the user-facing label for a :func:`report_progress` invocation.

    ``report_progress`` is a multi-purpose tool: it may set scope or
    brand name, advance to the next phase, or loop back to a prior
    phase. The base mapping renders the same "Advance phase" label for
    every call, which misleads the user when the agent is only updating
    metadata. This ladder inspects the arguments at render time so the
    timeline label tracks intent.
    """
    return rx.cond(
        arguments.get("loop_back_to", "") != "",
        "Loop back to phase",
        rx.cond(
            arguments.get("advance", False),
            "Advance phase",
            "Update phase metadata",
        ),
    )


def _report_progress_icon(arguments: rx.Var) -> rx.Var:
    """Pick the icon for a :func:`report_progress` invocation.

    Mirrors :func:`_report_progress_label` so the glyph reads the same
    intent the label conveys: an undo arrow when looping back, the
    forward arrow when advancing, and a pencil when only writing
    metadata.
    """
    return rx.cond(
        arguments.get("loop_back_to", "") != "",
        "undo_2",
        rx.cond(
            arguments.get("advance", False),
            "arrow_right",
            "file_pen_line",
        ),
    )


def humanize_tool_call_label(tool_name: rx.Var[str], arguments: rx.Var) -> rx.Var:
    """Project a tool name + arguments pair to its English label.

    Wrapper around :func:`humanize_tool_label` that special-cases tools
    whose meaning depends on their arguments. Today only
    ``report_progress`` needs this — see :func:`_report_progress_label`.
    """
    base = humanize_tool_label(tool_name)
    return rx.cond(
        tool_name == "report_progress",
        _report_progress_label(arguments),
        base,
    )


def tool_call_icon_tag(tool_name: rx.Var[str], arguments: rx.Var) -> rx.Var:
    """Project a tool name + arguments pair to its Lucide icon tag.

    Wrapper around :func:`tool_icon_tag` that special-cases tools whose
    icon should track a sub-intent encoded in arguments.
    """
    base = tool_icon_tag(tool_name)
    return rx.cond(
        tool_name == "report_progress",
        _report_progress_icon(arguments),
        base,
    )


def tool_call_card(call: rx.Var[ToolCallInfo]) -> rx.Component:
    """Render one inline timeline card for a single tool call.

    Args:
        call (rx.Var[ToolCallInfo]): Reflex var pointing at a
            :class:`ToolCallInfo`. The card re-renders when the underlying
            ``result`` field flips from empty (running) to non-empty (done).

    Returns:
        component (rx.Component): A horizontal pill with humanized tool label
        + status indicator.
    """
    is_done = call.result != ""

    return rx.hstack(
        rx.icon(
            tag=rx.cond(is_done, "circle_check", "loader"),
            size=13,
            color=rx.cond(is_done, tokens.ACCENT_TEAL_SOLID, tokens.TEXT_MUTED),
        ),
        rx.text(
            humanize_tool_call_label(call.tool_name, call.arguments),
            style={
                "color": tokens.TEXT_SECONDARY,
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
            },
        ),
        rx.text(
            rx.cond(is_done, "done", "running"),
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "11px",
                "font_style": "italic",
            },
        ),
        spacing="2",
        align="center",
        padding="5px 10px",
        style={
            "background_color": "rgba(255, 255, 255, 0.03)",
            "border_radius": tokens.RADIUS_PILL,
            "border": f"1px solid {tokens.GLASS_BORDER}",
            "width": "fit-content",
        },
    )
