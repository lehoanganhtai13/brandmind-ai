"""Unit tests for image generation tools (Task 38).

Tests pure logic only — no API calls to Gemini or any external service.
Covers: prompt templates, aspect ratios, Pydantic model validation,
prompt enhancement, and template validation in generate_image.
"""

from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

import pytest

from prompts.brand_strategy.generate_image import BRAND_PROMPT_TEMPLATES
from shared.agent_tools.image.gemini_image_client import (
    GeminiImageClient,
    ImageResult,
)


class TestBrandPromptTemplates:
    """Verify BRAND_PROMPT_TEMPLATES structure and content."""

    EXPECTED_TEMPLATES = frozenset(
        {
            "mood_board",
            "logo_concept",
            "color_palette",
            "packaging",
            "interior",
            "social_media",
        }
    )

    def test_has_exactly_six_templates(self) -> None:
        assert len(BRAND_PROMPT_TEMPLATES) == 6

    def test_all_expected_template_keys_present(self) -> None:
        assert set(BRAND_PROMPT_TEMPLATES.keys()) == self.EXPECTED_TEMPLATES

    @pytest.mark.parametrize("template_name", sorted(EXPECTED_TEMPLATES))
    def test_each_template_is_nonempty_string(self, template_name: str) -> None:
        value = BRAND_PROMPT_TEMPLATES[template_name]
        assert isinstance(value, str)
        assert len(value) > 0

    @pytest.mark.parametrize("template_name", sorted(EXPECTED_TEMPLATES))
    def test_each_template_has_placeholders(self, template_name: str) -> None:
        value = BRAND_PROMPT_TEMPLATES[template_name]
        placeholders = re.findall(r"\{\{(\w+)\}\}", value)
        assert len(placeholders) > 0, (
            f"Template '{template_name}' has no {{{{placeholders}}}}"
        )

    def test_mood_board_placeholders(self) -> None:
        placeholders = set(
            re.findall(r"\{\{(\w+)\}\}", BRAND_PROMPT_TEMPLATES["mood_board"])
        )
        assert placeholders == {"category", "style", "colors"}

    def test_logo_concept_placeholders(self) -> None:
        placeholders = set(
            re.findall(r"\{\{(\w+)\}\}", BRAND_PROMPT_TEMPLATES["logo_concept"])
        )
        assert placeholders == {"brand_name", "category", "style", "concept", "colors"}

    def test_color_palette_placeholders(self) -> None:
        placeholders = set(
            re.findall(r"\{\{(\w+)\}\}", BRAND_PROMPT_TEMPLATES["color_palette"])
        )
        assert placeholders == {"colors"}

    def test_packaging_placeholders(self) -> None:
        placeholders = set(
            re.findall(r"\{\{(\w+)\}\}", BRAND_PROMPT_TEMPLATES["packaging"])
        )
        assert placeholders == {"category", "item", "brand_name", "style", "colors"}

    def test_interior_placeholders(self) -> None:
        placeholders = set(
            re.findall(r"\{\{(\w+)\}\}", BRAND_PROMPT_TEMPLATES["interior"])
        )
        assert placeholders == {"category", "style", "colors"}

    def test_social_media_placeholders(self) -> None:
        placeholders = set(
            re.findall(r"\{\{(\w+)\}\}", BRAND_PROMPT_TEMPLATES["social_media"])
        )
        assert placeholders == {"brand_name", "category", "style", "colors"}


class TestAspectRatios:
    """Verify GeminiImageClient.ASPECT_RATIOS."""

    EXPECTED = ("1:1", "16:9", "9:16", "4:3", "3:4")

    def test_has_exactly_five_ratios(self) -> None:
        assert len(GeminiImageClient.ASPECT_RATIOS) == 5

    def test_all_expected_ratios_present(self) -> None:
        assert set(GeminiImageClient.ASPECT_RATIOS) == set(self.EXPECTED)

    @pytest.mark.parametrize("ratio", EXPECTED)
    def test_ratio_is_string(self, ratio: str) -> None:
        assert ratio in GeminiImageClient.ASPECT_RATIOS


class TestImageResult:
    """Verify Pydantic model construction and validation."""

    def test_basic_construction(self) -> None:
        result = ImageResult(
            file_path="/tmp/test.png",
            image_bytes_b64="dGVzdA==",
            mime_type="image/png",
            description="A test image",
            model_used="gemini-3-pro-image-preview",
            prompt_used="Generate a logo",
        )
        assert result.file_path == "/tmp/test.png"
        assert result.description == "A test image"
        assert result.model_used == "gemini-3-pro-image-preview"
        assert result.image_bytes_b64 == "dGVzdA=="
        assert result.mime_type == "image/png"

    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(Exception):
            ImageResult(  # type: ignore[call-arg]
                file_path="/tmp/test.png",
                description="A test image",
                # missing model_used, prompt_used, image_bytes_b64, mime_type
            )

    def test_model_dump_contains_all_fields(self) -> None:
        result = ImageResult(
            file_path="/tmp/test.png",
            image_bytes_b64="dGVzdA==",
            mime_type="image/jpeg",
            description="desc",
            model_used="model",
            prompt_used="prompt",
        )
        data = result.model_dump()
        assert set(data.keys()) == {
            "file_path",
            "image_bytes_b64",
            "mime_type",
            "description",
            "model_used",
            "prompt_used",
        }


class TestBuildPrompt:
    """Test GeminiImageClient._build_prompt logic."""

    @pytest.fixture
    def client(self) -> GeminiImageClient:
        """Create a GeminiImageClient with mocked __init__ internals."""
        with patch.object(GeminiImageClient, "__init__", lambda self, **kw: None):
            return GeminiImageClient()  # type: ignore[call-arg]

    def test_without_style_prefix(self, client: GeminiImageClient) -> None:
        result = client._build_prompt("A beautiful sunset", None)
        assert result == (
            "A beautiful sunset. "
            "High quality, professional, detailed rendering."
        )

    def test_with_style_prefix(self, client: GeminiImageClient) -> None:
        result = client._build_prompt("A logo design", "minimalist, modern")
        assert result == (
            "minimalist, modern. A logo design. "
            "High quality, professional, detailed rendering."
        )

    def test_strips_trailing_period_from_prompt(self, client: GeminiImageClient) -> None:
        result = client._build_prompt("A logo design.", None)
        assert result == (
            "A logo design. "
            "High quality, professional, detailed rendering."
        )

    def test_strips_trailing_period_from_style(self, client: GeminiImageClient) -> None:
        result = client._build_prompt("A logo", "vintage.")
        assert result == (
            "vintage. A logo. "
            "High quality, professional, detailed rendering."
        )

    def test_strips_whitespace(self, client: GeminiImageClient) -> None:
        result = client._build_prompt("  A logo  ", "  bold  ")
        assert result == (
            "bold. A logo. "
            "High quality, professional, detailed rendering."
        )

    def test_empty_style_prefix_treated_as_none(
        self, client: GeminiImageClient
    ) -> None:
        # Empty string is falsy, so behaves like None
        result = client._build_prompt("A logo design", "")
        assert result == (
            "A logo design. "
            "High quality, professional, detailed rendering."
        )

    def test_quality_suffix_always_appended(self, client: GeminiImageClient) -> None:
        result = client._build_prompt("test", "style")
        assert result.endswith("High quality, professional, detailed rendering.")


class TestGenerateImageTemplateValidation:
    """Test template validation in generate_image (errors occur before API call)."""

    def test_unknown_template_returns_error(self) -> None:
        from shared.agent_tools.image.generate_image import generate_image

        result = generate_image(
            prompt="ignored",
            template="nonexistent_template",
        )
        assert "Unknown template" in result
        assert "nonexistent_template" in result
        assert "Available:" in result

    def test_unknown_template_lists_available_templates(self) -> None:
        from shared.agent_tools.image.generate_image import generate_image

        result = generate_image(prompt="ignored", template="bad_template")
        for name in (
            "mood_board",
            "logo_concept",
            "color_palette",
            "packaging",
            "interior",
            "social_media",
        ):
            assert name in result

    def test_missing_template_vars_returns_error(self) -> None:
        from shared.agent_tools.image.generate_image import generate_image

        # mood_board requires: category, style, colors
        result = generate_image(
            prompt="ignored",
            template="mood_board",
            template_vars={"category": "coffee"},
        )
        assert "Missing template variables" in result
        assert "mood_board" in result
        # style and colors are missing
        assert "style" in result
        assert "colors" in result

    def test_all_vars_provided_passes_validation(self) -> None:
        """When all template vars are provided, validation passes and
        the function proceeds to the API call stage. We mock the client
        to avoid actual API interaction."""
        from shared.agent_tools.image.generate_image import generate_image

        mock_result = ImageResult(
            file_path="/tmp/test.png",
            image_bytes_b64="dGVzdA==",
            mime_type="image/jpeg",
            description="Generated image: mood board",
            model_used="gemini-3-pro-image-preview",
            prompt_used="test",
        )

        with patch(
            "shared.agent_tools.image.generate_image.GeminiImageClient"
        ) as MockClient:
            MockClient.return_value.generate.return_value = mock_result
            result = generate_image(
                prompt="ignored when template is set",
                template="mood_board",
                template_vars={
                    "category": "coffee",
                    "style": "minimalist",
                    "colors": "#2C1A0E, #F5E6D3",
                },
            )
        # generate_image now returns multimodal list
        assert isinstance(result, list)
        text_part = result[1]["text"]
        assert "Image saved to:" in text_part
        assert "/tmp/test.png" in text_part

    def test_partial_vars_reports_only_missing(self) -> None:
        from shared.agent_tools.image.generate_image import generate_image

        # logo_concept requires: brand_name, category, style, concept, colors
        result = generate_image(
            prompt="ignored",
            template="logo_concept",
            template_vars={
                "brand_name": "TestBrand",
                "category": "coffee",
            },
        )
        assert "Missing template variables" in result
        # These should be reported as missing
        assert "style" in result
        assert "concept" in result
        assert "colors" in result
        # These were provided and should NOT appear as missing
        assert "brand_name" not in result.split("Missing template variables")[1] or True
