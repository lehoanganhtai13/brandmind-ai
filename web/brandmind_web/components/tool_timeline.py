"""Inline tool-call timeline card.

Renders one entry inside an agent message body for each tool call the
agent dispatches. Matches ``docs/web_design.md`` § 9.3.4 — tool icon,
human-readable tool label, status pill (running / completed). Cards
are inline with the message body rather than in a separate panel so
the chat reads as a single chronological strip.
"""

from __future__ import annotations

import reflex as rx

from ..models import ToolCallInfo
from . import tokens

_TOOL_LABELS: dict[str, str] = {
    "ls": "Liệt kê tệp workspace",
    "read_file": "Đọc tệp workspace",
    "write_file": "Ghi tệp workspace",
    "edit_file": "Cập nhật tệp workspace",
    "write_todos": "Cập nhật danh sách todo",
    "tool_search": "Tìm công cụ phù hợp",
    "load_tools": "Nạp công cụ chuyên biệt",
    "task": "Giao việc cho agent chuyên biệt",
    "report_progress": "Cập nhật tiến độ phase",
    "kg_search": "Tra cứu Knowledge Graph",
    "search_knowledge_graph": "Tra cứu Knowledge Graph",
    "search_documents": "Tra cứu tài liệu chuyên môn",
    "search_docs": "Tra cứu tài liệu chuyên môn",
    "search_document_library": "Tra cứu tài liệu chuyên môn",
    "search_document": "Tra cứu tài liệu chuyên môn",
    "scrape_url": "Đọc nội dung trang web",
    "smart_search": "Tìm kiếm thông tin trên web",
    "web_search": "Tìm kiếm thông tin trên web",
    "generate_brand_key": "Tạo Brand Key một trang",
    "generate_document": "Soạn tài liệu chiến lược",
    "generate_presentation": "Soạn bộ slide trình bày",
    "generate_spreadsheet": "Lập bảng KPI",
    "use_browser": "Mở trình duyệt khảo sát",
    "browser_navigate": "Điều hướng trình duyệt",
    "extract_content": "Trích xuất nội dung trang",
}


def _humanize(tool_name: rx.Var[str]) -> rx.Var:
    """Map raw tool name to a Vietnamese label, fall back to the raw value.

    Reflex Vars cannot be looked up with a Python dict at compile time, so
    the mapping is unrolled into a chained :func:`rx.cond` ladder. New tool
    names should be added both to ``_TOOL_LABELS`` and to the chain below.
    """
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
            size=14,
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
            rx.cond(is_done, "đã xong", "đang chạy"),
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "11px",
                "font_style": "italic",
            },
        ),
        spacing="2",
        align="center",
        padding="6px 10px",
        style={
            "background_color": tokens.BG_SURFACE_2,
            "border_radius": tokens.RADIUS_PILL,
            "border": f"1px solid {tokens.GLASS_BORDER}",
            "width": "fit-content",
        },
    )
