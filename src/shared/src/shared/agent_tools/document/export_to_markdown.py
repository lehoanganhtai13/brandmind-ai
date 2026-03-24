"""export_to_markdown tool — Markdown export for brand strategy content.

Plain function callable by the agent. Converts structured phase
outputs to well-formatted Markdown with table of contents.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from loguru import logger

# Phase key → readable title mapping
_PHASE_TITLES: dict[str, str] = {
    "cover": "Cover",
    "executive_summary": "Executive Summary",
    "phase_0_output": "Business Context & Problem Statement",
    "phase_0_5_output": "Brand Equity Audit",
    "phase_1_output": "Market Intelligence & Research",
    "phase_2_output": "Brand Strategy Core",
    "phase_3_output": "Brand Identity & Expression",
    "phase_4_output": "Brand Communication Framework",
    "phase_5_output": "Implementation & Deliverables",
    "appendices": "Appendices",
}

# Short content threshold — below this, return directly instead of writing file
_SHORT_CONTENT_THRESHOLD = 2000


def export_to_markdown(
    content: str,
    sections: list[str] | None = None,
    output_path: str | None = None,
) -> str:
    """Export brand strategy content to well-formatted Markdown.

    Clean text export for documentation, README files, or wikis.
    Short exports are returned directly; longer ones are written
    to a file.

    Args:
        content: JSON string with phase outputs.
        sections: Specific section keys to export, or None for all.
        output_path: Custom output path (for file output).

    Returns:
        Markdown content directly (if short) or path to exported file.
    """
    try:
        content_dict: dict[str, Any] = json.loads(content)
    except (json.JSONDecodeError, TypeError) as e:
        return f"Invalid content JSON: {e}"

    if sections:
        filtered = {k: v for k, v in content_dict.items() if k in sections}
    else:
        filtered = content_dict

    md = _format_full_document(filtered)

    if len(md) < _SHORT_CONTENT_THRESHOLD:
        return md

    if not output_path:
        base_dir = os.environ.get(
            "BRANDMIND_OUTPUT_DIR",
            os.path.join(os.getcwd(), "brandmind-output"),
        )
        output_path = os.path.join(base_dir, "documents", "brand_strategy_export.md")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(md, encoding="utf-8")
    logger.info(f"Markdown exported: {output_path}")
    return f"Markdown exported to: {output_path}\n({len(md)} characters)"


def _format_full_document(content: dict[str, Any]) -> str:
    """Build complete Markdown document with TOC and all sections."""
    lines: list[str] = ["# Brand Strategy\n"]

    # Table of Contents
    lines.append("## Table of Contents\n")
    for key in content:
        title = _PHASE_TITLES.get(key, key.replace("_", " ").title())
        anchor = title.lower().replace(" ", "-").replace("&", "")
        lines.append(f"- [{title}](#{anchor})")
    lines.append("")

    # Sections
    for key, value in content.items():
        title = _PHASE_TITLES.get(key, key.replace("_", " ").title())
        lines.append(f"## {title}\n")
        lines.append(_render_value(value, level=3))
        lines.append("")

    return "\n".join(lines)


def _render_value(value: Any, level: int = 3) -> str:
    """Recursively render value to Markdown."""
    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        parts: list[str] = []
        prefix = "#" * min(level, 6)
        for key, val in value.items():
            label = key.replace("_", " ").title()
            parts.append(f"{prefix} {label}\n")
            parts.append(_render_value(val, level + 1))
            parts.append("")
        return "\n".join(parts)

    if isinstance(value, list):
        if value and isinstance(value[0], dict):
            return _format_table(value)
        return "\n".join(f"- {item}" for item in value)

    return str(value)


def _format_table(data: list[dict[str, Any]]) -> str:
    """Format list of dicts as Markdown table."""
    if not data:
        return ""

    headers = list(data[0].keys())
    header_row = "| " + " | ".join(h.replace("_", " ").title() for h in headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"

    rows: list[str] = [header_row, separator]
    for row in data:
        cells = [str(row.get(h, "")).replace("|", "\\|") for h in headers]
        rows.append("| " + " | ".join(cells) + " |")

    return "\n".join(rows)
