"""generate_image tool — brand asset image generation.

Plain function callable by the agent via create_agent(). Uses
Gemini 3 Pro Image for text-to-image generation with brand-specific
prompt templates. Returns multimodal content (image + text) so the
agent can visually evaluate the result.
"""

from __future__ import annotations

import re
from typing import Any

from loguru import logger

from config.system_config import SETTINGS
from prompts.brand_strategy.generate_image import BRAND_PROMPT_TEMPLATES
from shared.agent_tools.image.gemini_image_client import GeminiImageClient


def generate_image(
    prompt: str,
    style: str | None = None,
    aspect_ratio: str = "1:1",
    template: str | None = None,
    template_vars: dict[str, str] | None = None,
    session_id: str | None = None,
) -> list[dict[str, Any]] | str:
    """Generate brand-related images using Gemini 3 Pro Image.

    The generated image is returned visually so you can evaluate it.
    If the result needs refinement, use edit_image with the file path
    and an edit instruction.

    Use for: mood boards, logo concepts, color palettes, packaging
    mockups, interior concepts, social media templates.

    IMPORTANT: Generated images are DIRECTION DRAFTS — use them
    to communicate visual intent to the user.

    Args:
        prompt: Detailed image description. Be specific about style,
            colors, composition, lighting, and subject.
        style: Style modifier. Options: "minimalist", "vintage",
            "modern", "rustic", "luxury", "playful", "industrial",
            "organic", "bold", "elegant".
        aspect_ratio: "1:1" (default), "16:9", "9:16", "4:3", "3:4".
        template: Pre-built prompt template. Options: "mood_board",
            "logo_concept", "color_palette", "packaging", "interior",
            "social_media".
        template_vars: Variables for the template (e.g., brand_name,
            category, colors, style, concept, item).
        session_id: Session ID for organizing output files.

    Returns:
        Multimodal content with the generated image and file path,
        or error string if generation fails.
    """
    if template:
        if template not in BRAND_PROMPT_TEMPLATES:
            return (
                f"Unknown template '{template}'. "
                f"Available: {', '.join(BRAND_PROMPT_TEMPLATES.keys())}"
            )
        vars_dict = template_vars or {}
        final_prompt = BRAND_PROMPT_TEMPLATES[template]
        for key, value in vars_dict.items():
            final_prompt = final_prompt.replace("{{" + key + "}}", str(value))

        remaining = re.findall(r"\{\{(\w+)\}\}", final_prompt)
        if remaining:
            return (
                f"Missing template variables for '{template}': "
                f"{', '.join(remaining)}. "
                f"Provide these in template_vars."
            )
    else:
        final_prompt = prompt

    client = GeminiImageClient(api_key=SETTINGS.GEMINI_API_KEY)

    try:
        result = client.generate(
            prompt=final_prompt,
            aspect_ratio=aspect_ratio,
            style_prefix=style,
            session_id=session_id,
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
                    f"Image saved to: {result.file_path}\n"
                    f"To refine this image, use edit_image with "
                    f'image_path="{result.file_path}" and your edit instructions.'
                ),
            },
        ]
    except (RuntimeError, ValueError) as e:
        logger.error(f"generate_image failed: {e}")
        return f"Image generation failed: {e}"
