"""generate_document tool — PDF/DOCX document generation.

Plain function callable by the agent. Routes to PDF or DOCX builder
based on doc_format parameter.
"""

from __future__ import annotations

import json
import os
from typing import Any

from loguru import logger

from .docx_builder import BrandStrategyDOCXBuilder
from .pdf_builder import BrandStrategyPDFBuilder
from .templates.brand_strategy import BrandStrategyTemplate


def generate_document(
    content: str,
    doc_format: str = "pdf",
    brand_name: str = "Brand",
    brand_colors: list[str] | None = None,
    images: str | None = None,
    output_path: str | None = None,
) -> str:
    """Generate brand strategy documents in PDF or DOCX format.

    Professional formatting with cover page, table of contents,
    and branded sections. Content is a JSON string parsed into a
    dict; each section in the document is populated by looking up
    a specific key in that dict. Missing keys render the literal
    placeholder "(No content available)" — the section is not
    silently dropped, so empty bodies indicate a key mismatch and
    must be fixed at the call site.

    Args:
        content: JSON string parsed into a dict. The dict MUST
            contain the following top-level keys (any missing key
            will produce a "(No content available)" placeholder
            in its section):

              - "cover": str, the cover-page tagline / sub-heading.
              - "executive_summary": str OR list[str] bullets, the
                1-page punchline summary.
              - "phase_0_output": str / dict / list. Phase 0 problem
                diagnosis. dict keys become subheadings; list[str]
                becomes bullets; list[dict] becomes a table.
              - "phase_0_5_output" (optional): same shape, brand
                equity audit. Can be omitted for new_brand scope.
              - "phase_1_output": same shape, market intelligence.
              - "phase_2_output": same shape, brand strategy core
                (positioning + POPs/PODs + essence).
              - "phase_3_output": same shape, brand identity
                (archetype + visual + verbal direction).
              - "phase_4_output": same shape, communication
                framework (messaging + Cialdini + AIDA + channels).
              - "phase_5_output": **must be a dict** (not a string)
                with TWO required nested keys; passing a single
                string here leaves both Implementation Roadmap and
                KPI Framework sections empty.
                  - "roadmap": str / dict / list — the 3-horizon
                    implementation plan (e.g. list[dict] like
                    [{"Horizon": "0-3 mo", "Items": "...", "Investment": "..."}]
                    renders as a table; list[str] renders as bullets).
                  - "measurement": str / dict / list — the KPI
                    framework + tracking plan (list[dict] preferred
                    so the KPI table renders, e.g.
                    [{"KPI": "...", "Target": "...", "Cadence": "..."}]).
              - "appendices" (optional): str / dict / list, raw
                source material the document should append.

            Each value can be:
              - str → rendered as one paragraph
              - dict → rendered as nested headings + body
              - list[str] → rendered as bullets
              - list[dict] → rendered as a table

            Minimal example (all required keys, brief content):
              {
                "cover": "Modern Saigonese Gastronomy",
                "executive_summary": "Reposition Signature as ...",
                "phase_0_output": {"Problem": "Brand dilution", "Scope": "Repositioning"},
                "phase_1_output": {"SWOT": {...}, "White space": "..."},
                "phase_2_output": {"Positioning statement": "...", "POD": [...]},
                "phase_3_output": {"Archetype": "Caregiver", "Visual": "..."},
                "phase_4_output": {"Messaging": [...], "Channels": [...]},
                "phase_5_output": {
                  "roadmap": [{"Horizon": "0-3 mo", "Items": "..."}, ...],
                  "measurement": [{"KPI": "...", "Target": "...", "Cadence": "..."}, ...]
                }
              }

        doc_format: Output format — "pdf" (default) or "docx".
        brand_name: Brand name for cover page and headers.
        brand_colors: List of 3 hex colors [primary, secondary, accent].
            Default: ["#1B365D", "#F5F0E8", "#D4A84B"].
        images: JSON string mapping section_id to image file path
            (e.g. {"brand_identity": "/path/to/mood_board.png"}).
        output_path: Custom output path. Default uses BRANDMIND_OUTPUT_DIR.

    Returns:
        Message with path to generated document file.
    """
    try:
        content_dict: dict[str, Any] = json.loads(content)
    except (json.JSONDecodeError, TypeError) as e:
        return f"Invalid content JSON: {e}"

    images_dict: dict[str, str] | None = None
    if images:
        try:
            images_dict = json.loads(images)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Invalid images JSON, ignoring images")

    colors = brand_colors or ["#1B365D", "#F5F0E8", "#D4A84B"]
    template = BrandStrategyTemplate(brand_name=brand_name, brand_colors=colors)

    if not output_path:
        base_dir = os.environ.get(
            "BRANDMIND_OUTPUT_DIR",
            os.path.join(os.getcwd(), "brandmind-output"),
        )
        safe_name = brand_name.lower().replace(" ", "_")
        ext = "pdf" if doc_format == "pdf" else "docx"
        output_path = os.path.join(
            base_dir, "documents", f"{safe_name}_brand_strategy.{ext}"
        )

    try:
        if doc_format == "docx":
            builder = BrandStrategyDOCXBuilder(template=template)
        else:
            builder = BrandStrategyPDFBuilder(template=template)  # type: ignore[assignment]

        result_path = builder.build(
            content=content_dict,
            output_path=output_path,
            images=images_dict,
        )
        return (
            f"Document FILE saved to disk.\n"
            f"Format: {doc_format.upper()}\n"
            f"Path: {result_path}\n\n"
            f"⚠️ IMPORTANT: File on disk ≠ user delivery. Summarize the "
            f"document's structure (sections included, key content per "
            f"section) in your next user-facing response so user knows what "
            f"was assembled — file path alone is not a delivery."
        )
    except Exception as e:
        logger.error(f"Document generation failed: {e}")
        return f"Document generation failed: {e}"
