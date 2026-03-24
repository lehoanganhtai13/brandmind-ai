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
    and branded sections. Content should be a JSON string with
    phase outputs from the brand strategy workflow.

    Args:
        content: JSON string with phase outputs. Keys like
            "phase_0_output", "phase_1_output", etc.
        doc_format: Output format — "pdf" or "docx".
        brand_name: Brand name for cover page and headers.
        brand_colors: List of 3 hex colors [primary, secondary, accent].
            Default: ["#1B365D", "#F5F0E8", "#D4A84B"].
        images: JSON string mapping section_id to image file path.
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
            f"Document generated successfully.\n"
            f"Format: {doc_format.upper()}\n"
            f"Path: {result_path}"
        )
    except Exception as e:
        logger.error(f"Document generation failed: {e}")
        return f"Document generation failed: {e}"
