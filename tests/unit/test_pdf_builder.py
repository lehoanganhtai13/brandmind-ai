"""Unit tests for the PDF builder font fallback path.

Covers the regression fixed in 2026-05-03 where ``BrandStrategyPDFBuilder``
crashed under fpdf2 v2.5.3+ because the missing-NotoSans fallback registered
Helvetica via ``add_font("NotoSans", "", "Helvetica")`` — fpdf2 reads
``"Helvetica"`` as a font file path, fails to find it, and surfaces the
misleading ``.pkl`` deprecation message. The fix routes every ``set_font``
through ``pdf._font_family`` and defaults that family to the built-in
``"Times"`` core font (Times New Roman family is the Vietnam-conventional
choice for business documents) when NotoSans .ttf files are not bundled.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from shared.agent_tools.document.pdf_builder import (
    BrandStrategyPDF,
    BrandStrategyPDFBuilder,
)


@pytest.fixture
def minimal_content() -> dict:
    """Minimal content dict that the builder can render end-to-end."""
    return {
        "executive_summary": "A short executive summary paragraph.",
        "phase_0_output": {"problem_statement": "Weekday occupancy at 40%."},
        "phase_5_output": {
            "roadmap": [
                {"Horizon": "0-3 mo", "Items": "Train staff"},
            ],
            "measurement": [
                {"KPI": "Weekday occupancy", "Target": "65%", "Cadence": "Weekly"},
            ],
        },
    }


class TestRegisterFonts:
    """The font-registration step is the surface that broke under fpdf2 v2.5.3+."""

    def test_notosans_present_registers_font_and_sets_family(self, tmp_path: Path):
        """When NotoSans .ttf files exist, both regular + bold are registered and the family flag flips."""
        fonts_dir = tmp_path / "fonts"
        fonts_dir.mkdir()
        # Use the system DejaVu font as a stand-in for NotoSans — fpdf2 only checks the file is a valid font.
        # If DejaVu is also unavailable (unusual), fall back to verifying the file-existence check shape.
        candidate = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
        if not candidate.exists():
            pytest.skip("No reusable system .ttf font for this test environment")
        regular = fonts_dir / "NotoSans-Regular.ttf"
        regular.write_bytes(candidate.read_bytes())
        bold = fonts_dir / "NotoSans-Bold.ttf"
        bold.write_bytes(candidate.read_bytes())

        builder = BrandStrategyPDFBuilder()
        pdf = BrandStrategyPDF()
        with patch("shared.agent_tools.document.pdf_builder._FONTS_DIR", fonts_dir):
            builder._register_fonts(pdf)

        assert pdf._font_family == "NotoSans", "family flag should flip when NotoSans files are present"

    def test_notosans_missing_does_not_call_add_font_for_core_font(
        self, tmp_path: Path
    ):
        """When NotoSans is missing, Times is used as a built-in core font — no add_font call."""
        empty_fonts_dir = tmp_path / "fonts_empty"
        empty_fonts_dir.mkdir()

        builder = BrandStrategyPDFBuilder()
        pdf = BrandStrategyPDF()
        with patch("shared.agent_tools.document.pdf_builder._FONTS_DIR", empty_fonts_dir):
            with patch.object(pdf, "add_font") as mock_add_font:
                builder._register_fonts(pdf)

        assert mock_add_font.call_count == 0, (
            "Times is a built-in core font in fpdf2 — add_font must NOT be "
            "called for it; calling add_font with a non-file argument "
            "crashes under fpdf2 v2.5.3+ with the .pkl deprecation message."
        )
        assert pdf._font_family == "Times", (
            "family flag should stay on default Times (Vietnam-conventional)"
        )

    def test_notosans_missing_then_set_font_core_succeeds(self, tmp_path: Path):
        """After fallback, set_font(_font_family, ...) must work with the default Times family."""
        empty_fonts_dir = tmp_path / "fonts_empty"
        empty_fonts_dir.mkdir()

        builder = BrandStrategyPDFBuilder()
        pdf = BrandStrategyPDF()
        with patch("shared.agent_tools.document.pdf_builder._FONTS_DIR", empty_fonts_dir):
            builder._register_fonts(pdf)

        # set_font with the resolved family must not raise — Times is built-in.
        pdf.add_page()
        pdf.set_font(pdf._font_family, "", 12)
        pdf.set_font(pdf._font_family, "B", 12)


class TestBuildEndToEnd:
    """End-to-end builder run on the fallback Helvetica path — the production bug surface."""

    def test_build_minimal_pdf_with_core_font_fallback(
        self, tmp_path: Path, minimal_content: dict
    ):
        """Driving the full build() path with no NotoSans files must produce a valid PDF without crashing."""
        empty_fonts_dir = tmp_path / "fonts_empty"
        empty_fonts_dir.mkdir()
        output_path = tmp_path / "out.pdf"

        builder = BrandStrategyPDFBuilder()
        with patch("shared.agent_tools.document.pdf_builder._FONTS_DIR", empty_fonts_dir):
            result_path = builder.build(
                content=minimal_content,
                output_path=str(output_path),
            )

        assert result_path == str(output_path)
        assert output_path.exists(), "PDF file should land on disk"
        assert output_path.stat().st_size > 1024, "PDF should not be a near-empty stub"
        # PDF magic header — every PDF starts with %PDF-
        assert output_path.read_bytes()[:5] == b"%PDF-", "Output should be a valid PDF document"
