"""Gemini image generation API client.

Wraps google-genai SDK for text-to-image generation and image editing
using gemini-3-pro-image-preview model via generate_content API.
Supports generation, editing, multiple aspect ratios, style prefixes,
and session-based file organization.
"""

from __future__ import annotations

import base64
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel


class ImageResult(BaseModel):
    """Result from image generation or editing."""

    file_path: str
    image_bytes_b64: str
    mime_type: str
    description: str
    model_used: str
    prompt_used: str


class GeminiImageClient:
    """Client for Gemini 3 Pro Image generation and editing.

    Uses generate_content API with response_modalities=["IMAGE"]
    for both text-to-image generation and image editing.

    Attributes:
        api_key: Google AI API key.
        model: Gemini image model.
        output_dir: Base directory for saving images.
    """

    ASPECT_RATIOS = ("1:1", "16:9", "9:16", "4:3", "3:4")

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3-pro-image-preview",
        output_dir: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.output_dir = output_dir or self._resolve_output_dir()
        self._client: Any = None

    @staticmethod
    def _resolve_output_dir() -> str:
        base = os.environ.get(
            "BRANDMIND_OUTPUT_DIR",
            os.path.join(os.getcwd(), "brandmind-output"),
        )
        return os.path.join(base, "images")

    def _get_client(self) -> Any:
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        style_prefix: str | None = None,
        output_filename: str | None = None,
        session_id: str | None = None,
    ) -> ImageResult:
        """Generate an image from a text prompt.

        Args:
            prompt: Image description.
            aspect_ratio: One of "1:1", "16:9", "9:16", "4:3", "3:4".
            style_prefix: Prepended to prompt (e.g., "minimalist, modern").
            output_filename: Custom filename (auto-generated if None).
            session_id: Session ID for folder organization.

        Returns:
            ImageResult with file path, base64 data, and metadata.
        """
        if aspect_ratio not in self.ASPECT_RATIOS:
            raise ValueError(
                f"Unsupported aspect_ratio '{aspect_ratio}'. "
                f"Choose from: {list(self.ASPECT_RATIOS)}"
            )

        enhanced_prompt = self._build_prompt(prompt, style_prefix)
        image_bytes, mime_type = self._call_generate_content(
            contents=f"Generate an image: {enhanced_prompt}",
            aspect_ratio=aspect_ratio,
        )

        filename = output_filename or self._generate_filename(
            self._ext_from_mime(mime_type)
        )
        file_path = self._save_image(image_bytes, filename, session_id)

        return ImageResult(
            file_path=str(file_path),
            image_bytes_b64=base64.b64encode(image_bytes).decode("ascii"),
            mime_type=mime_type,
            description=f"Generated image: {prompt[:100]}",
            model_used=self.model,
            prompt_used=enhanced_prompt,
        )

    def edit(
        self,
        image_path: str,
        prompt: str,
        aspect_ratio: str = "1:1",
        output_filename: str | None = None,
        session_id: str | None = None,
    ) -> ImageResult:
        """Edit an existing image with a text prompt.

        Args:
            image_path: Path to the source image to edit.
            prompt: Edit instruction describing desired changes.
            aspect_ratio: Output aspect ratio.
            output_filename: Custom filename (auto-generated if None).
            session_id: Session ID for folder organization.

        Returns:
            ImageResult with edited image data.
        """
        from google.genai import types

        source = Path(image_path)
        if not source.exists():
            raise FileNotFoundError(f"Source image not found: {image_path}")

        source_bytes = source.read_bytes()
        source_mime = self._mime_from_ext(source.suffix)

        image_bytes, mime_type = self._call_generate_content(
            contents=[
                types.Part.from_bytes(data=source_bytes, mime_type=source_mime),
                types.Part.from_text(text=prompt),
            ],
            aspect_ratio=aspect_ratio,
        )

        filename = output_filename or self._generate_filename(
            self._ext_from_mime(mime_type)
        )
        file_path = self._save_image(image_bytes, filename, session_id)

        return ImageResult(
            file_path=str(file_path),
            image_bytes_b64=base64.b64encode(image_bytes).decode("ascii"),
            mime_type=mime_type,
            description=f"Edited image: {prompt[:100]}",
            model_used=self.model,
            prompt_used=prompt,
        )

    def _call_generate_content(
        self,
        contents: Any,
        aspect_ratio: str,
    ) -> tuple[bytes, str]:
        """Call generate_content and extract image bytes from response.

        Returns:
            Tuple of (image_bytes, mime_type).
        """
        from google.genai import types

        try:
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                    ),
                ),
            )
        except Exception as e:
            if "SAFETY" in str(e).upper() or "BLOCKED" in str(e).upper():
                raise RuntimeError(
                    "Image generation blocked by content safety policy. "
                    f"Try rephrasing the prompt. Original error: {e}"
                ) from e
            raise RuntimeError(f"Image generation failed: {e}") from e

        if not response.candidates:
            raise RuntimeError("No candidates in response.")

        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                return part.inline_data.data, part.inline_data.mime_type

        # No image found — check for text feedback
        for part in response.candidates[0].content.parts:
            if part.text:
                raise RuntimeError(
                    f"Model returned text instead of image: {part.text[:200]}"
                )

        raise RuntimeError("No image data in response.")

    def _build_prompt(self, prompt: str, style_prefix: str | None) -> str:
        parts = []
        if style_prefix:
            parts.append(style_prefix.strip().rstrip("."))
        parts.append(prompt.strip().rstrip("."))
        parts.append("High quality, professional, detailed rendering")
        return ". ".join(parts) + "."

    def _save_image(
        self,
        image_bytes: bytes,
        filename: str,
        session_id: str | None,
    ) -> Path:
        if session_id:
            target_dir = Path(self.output_dir) / session_id
        else:
            target_dir = Path(self.output_dir)

        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / filename
        file_path.write_bytes(image_bytes)
        logger.debug(f"Image saved to {file_path}")
        return file_path

    @staticmethod
    def _generate_filename(extension: str = "jpeg") -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"generated_{timestamp}.{extension}"

    @staticmethod
    def _mime_from_ext(ext: str) -> str:
        return {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }.get(ext.lower(), "image/jpeg")

    @staticmethod
    def _ext_from_mime(mime: str) -> str:
        return {
            "image/png": "png",
            "image/jpeg": "jpeg",
            "image/webp": "webp",
        }.get(mime, "jpeg")
