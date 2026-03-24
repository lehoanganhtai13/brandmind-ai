"""generate_presentation tool — PPTX pitch deck generation.

Plain function callable by the agent. Generates brand strategy
pitch decks using python-pptx.
"""

from __future__ import annotations

import json
import os
from typing import Any

from loguru import logger

from .pptx_builder import BrandStrategyPPTXBuilder
from .templates.brand_strategy import BrandStrategyDeckTemplate


def generate_presentation(
    content: str,
    brand_name: str = "Brand",
    brand_colors: list[str] | None = None,
    images: dict[str, str] | None = None,
    output_path: str | None = None,
) -> str:
    """Generate brand strategy presentations in PPTX format.

    Executive pitch decks with branded slides, speaker notes,
    and support for images, tables, and two-column layouts.

    Args:
        content: JSON string with phase outputs.
        brand_name: Brand name for title slide.
        brand_colors: List of 3 hex colors [primary, secondary, accent].
        images: Dict mapping slide_id to image file path.
        output_path: Custom output path. Default uses BRANDMIND_OUTPUT_DIR.

    Returns:
        Message with path to generated PPTX file.
    """
    try:
        content_dict: dict[str, Any] = json.loads(content)
    except (json.JSONDecodeError, TypeError) as e:
        return f"Invalid content JSON: {e}"

    colors = brand_colors or ["#1B365D", "#F5F0E8", "#D4A84B"]
    template = BrandStrategyDeckTemplate(brand_name=brand_name, brand_colors=colors)

    if not output_path:
        base_dir = os.environ.get(
            "BRANDMIND_OUTPUT_DIR",
            os.path.join(os.getcwd(), "brandmind-output"),
        )
        safe_name = brand_name.lower().replace(" ", "_")
        output_path = os.path.join(
            base_dir,
            "presentations",
            f"{safe_name}_strategy_deck.pptx",
        )

    try:
        builder = BrandStrategyPPTXBuilder(template=template)
        result_path = builder.build(
            content=content_dict,
            output_path=output_path,
            images=images,
        )
        return (
            f"Presentation generated successfully.\n"
            f"Path: {result_path}\n"
            f"Slides: {len(template.slides)}"
        )
    except Exception as e:
        logger.error(f"Presentation generation failed: {e}")
        return f"Presentation generation failed: {e}"
