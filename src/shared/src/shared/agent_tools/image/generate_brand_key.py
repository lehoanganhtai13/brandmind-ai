"""generate_brand_key tool — Brand Key one-pager visual.

Creates a professional infographic showing the 9 Brand Key components
used as the capstone visual in Phase 5 deliverables.
"""

from __future__ import annotations

import re
from typing import Any

from loguru import logger

from config.system_config import SETTINGS
from prompts.brand_strategy.generate_brand_key import (
    BRAND_KEY_PROMPT_TEMPLATE,
)
from shared.agent_tools.image.gemini_image_client import GeminiImageClient


def generate_brand_key(
    brand_name: str,
    root_strength: str,
    competitive_environment: str,
    target: str,
    insight: str,
    benefits: str,
    values_personality: str,
    reasons_to_believe: str,
    discriminator: str,
    brand_essence: str,
    colors: str = "navy blue, white, gold accent",
    session_id: str | None = None,
) -> list[dict[str, Any]] | str:
    """Generate a Brand Key one-pager visual summary.

    Creates a professional infographic showing the 9 Brand Key
    components — used as the capstone visual in Phase 5 deliverables.

    NOTE: AI image generation may render text imperfectly (especially
    Vietnamese diacritics, small font sizes, dense layouts). This is
    a direction draft — for production quality, use generate_document
    (PDF/DOCX) for precise text layout.

    Args:
        brand_name: The brand name.
        root_strength: Core competency / heritage.
        competitive_environment: Key competitors and market.
        target: Target audience description.
        insight: Core consumer insight.
        benefits: Functional + emotional benefits.
        values_personality: Brand values and personality traits.
        reasons_to_believe: Evidence / proof points.
        discriminator: Key point of difference.
        brand_essence: 2-4 word brand essence / mantra.
        colors: Brand color palette description.
        session_id: Session ID for organizing output files.

    Returns:
        Path to generated Brand Key image + description.
    """
    replacements = {
        "brand_name": brand_name,
        "root_strength": root_strength,
        "competitive_environment": competitive_environment,
        "target": target,
        "insight": insight,
        "benefits": benefits,
        "values_personality": values_personality,
        "reasons_to_believe": reasons_to_believe,
        "discriminator": discriminator,
        "brand_essence": brand_essence,
        "colors": colors,
    }
    filled_prompt = BRAND_KEY_PROMPT_TEMPLATE
    for key, value in replacements.items():
        filled_prompt = filled_prompt.replace("{{" + key + "}}", value)

    client = GeminiImageClient(api_key=SETTINGS.GEMINI_API_KEY)

    try:
        safe_name = re.sub(r"[^\w\-]", "_", brand_name.lower())
        result = client.generate(
            prompt=filled_prompt,
            aspect_ratio="9:16",
            session_id=session_id,
            output_filename=f"brand_key_{safe_name}.jpeg",
        )
        return [
            {
                "type": "image",
                "base64": result.image_bytes_b64,
                "mime_type": result.mime_type,
            },
            {
                "type": "text",
                "text": (
                    f"Brand Key saved to: {result.file_path}\n"
                    f"Brand: {brand_name}\n"
                    f"Essence: {brand_essence}\n"
                    f"All 9 Brand Key sections rendered in infographic format.\n"
                    f"To refine, use edit_image with "
                    f'image_path="{result.file_path}".'
                ),
            },
        ]
    except (RuntimeError, ValueError) as e:
        logger.error(f"generate_brand_key failed: {e}")
        return f"Brand Key generation failed: {e}"
