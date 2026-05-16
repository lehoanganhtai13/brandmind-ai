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


def _humanize(tool_name: rx.Var[str]) -> rx.Var:
    """Project a raw tool name to its English label, fall back to the raw value."""
    label: rx.Var = tool_name
    for raw, human in _TOOL_LABELS.items():
        label = rx.cond(tool_name == raw, human, label)
    return label


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
            _humanize(call.tool_name),
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
