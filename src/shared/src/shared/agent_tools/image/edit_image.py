"""edit_image tool — refine existing images with text instructions.

Uses Gemini 3 Pro Image to edit an existing image based on a text
prompt. The edited image is returned visually for evaluation.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from config.system_config import SETTINGS
from shared.agent_tools.image.gemini_image_client import GeminiImageClient


def edit_image(
    image_path: str,
    prompt: str,
    aspect_ratio: str = "1:1",
    session_id: str | None = None,
) -> list[dict[str, Any]] | str:
    """Edit an existing image using Gemini 3 Pro Image.

    Send a previously generated image along with edit instructions
    to refine colors, style, composition, or content. The model
    understands the source image and applies changes accordingly.

    Use for: adjusting colors, simplifying designs, changing style,
    adding/removing elements, resizing for different formats.

    Args:
        image_path: Path to the source image (from generate_image
            or a previous edit_image result).
        prompt: Edit instruction describing desired changes. Be
            specific: "change primary color to forest green",
            "simplify to 2 colors only", "add a coffee leaf motif".
        aspect_ratio: Output ratio — "1:1" (default), "16:9",
            "9:16", "4:3", "3:4".
        session_id: Session ID for organizing output files.

    Returns:
        Multimodal content with the edited image and file path,
        or error string if editing fails.
    """
    client = GeminiImageClient(api_key=SETTINGS.GEMINI_API_KEY)

    try:
        result = client.edit(
            image_path=image_path,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
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
                    f"Edited image saved to: {result.file_path}\n"
                    f"Edit applied: {prompt[:100]}\n"
                    f"To refine further, use edit_image with "
                    f'image_path="{result.file_path}".'
                ),
            },
        ]
    except (RuntimeError, ValueError, FileNotFoundError) as e:
        logger.error(f"edit_image failed: {e}")
        return f"Image editing failed: {e}"
