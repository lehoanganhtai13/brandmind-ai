"""PDF builder for brand strategy documents using fpdf2.

Generates professional branded PDFs with cover page, table of
contents, section rendering, tables, and image embedding.
Supports Vietnamese text via NotoSans Unicode fonts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fpdf import FPDF
from loguru import logger

from .templates.brand_strategy import BrandStrategyTemplate

_FONTS_DIR = Path(__file__).parent / "fonts"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


class BrandStrategyPDF(FPDF):
    """Extended FPDF with branded header/footer."""

    brand_name: str = "Brand"
    primary_color: tuple[int, int, int] = (27, 54, 93)
    accent_color: tuple[int, int, int] = (212, 168, 75)
    _skip_header: bool = False

    def header(self) -> None:
        """Branded header on all pages except page 1."""
        if self._skip_header or self.page_no() == 1:
            return
        self.set_font("NotoSans", "", 8)
        self.set_text_color(*self.primary_color)
        self.cell(0, 8, self.brand_name, align="L")
        self.cell(
            0, 8, "Brand Strategy Document", align="R", new_x="LMARGIN", new_y="NEXT"
        )
        self.set_draw_color(*self.accent_color)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(5)

    def footer(self) -> None:
        """Page number footer."""
        self.set_y(-15)
        self.set_font("NotoSans", "", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


class BrandStrategyPDFBuilder:
    """Builds professional branded PDF documents.

    Uses fpdf2 with NotoSans Unicode fonts for Vietnamese support.
    Falls back to Helvetica if font files are missing.
    """

    def __init__(self, template: BrandStrategyTemplate | None = None) -> None:
        self.template = template or BrandStrategyTemplate()
        self.colors = {
            "primary": _hex_to_rgb(self.template.brand_colors[0]),
            "secondary": (
                _hex_to_rgb(self.template.brand_colors[1])
                if len(self.template.brand_colors) > 1
                else (245, 240, 232)
            ),
            "accent": (
                _hex_to_rgb(self.template.brand_colors[2])
                if len(self.template.brand_colors) > 2
                else (212, 168, 75)
            ),
        }

    def build(
        self,
        content: dict[str, Any],
        output_path: str,
        images: dict[str, str] | None = None,
    ) -> str:
        """Build PDF document from content dict.

        Args:
            content: Dict with section content keyed by content_key.
            output_path: File path for output PDF.
            images: Optional dict mapping section_id to image file path.

        Returns:
            Path to generated PDF file.
        """
        pdf = BrandStrategyPDF()
        pdf.brand_name = self.template.brand_name
        pdf.primary_color = self.colors["primary"]
        pdf.accent_color = self.colors["accent"]
        pdf.set_auto_page_break(auto=True, margin=20)

        self._register_fonts(pdf)

        self._render_cover_page(pdf)
        self._render_toc(pdf, content)

        for section in self.template.sections:
            section_content = self._resolve_content(content, section.content_key)
            if section_content is None and not section.required:
                continue

            if section.page_break_before:
                pdf.add_page()

            self._render_section(pdf, section.title, section.subtitle, section_content)

            if images and section.id in images:
                self._embed_image(pdf, images[section.id])

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        pdf.output(output_path)
        logger.info(f"PDF generated: {output_path}")
        return output_path

    def _register_fonts(self, pdf: FPDF) -> None:
        """Register NotoSans Unicode fonts, fallback to Helvetica."""
        regular = _FONTS_DIR / "NotoSans-Regular.ttf"
        bold = _FONTS_DIR / "NotoSans-Bold.ttf"

        if regular.exists():
            pdf.add_font("NotoSans", "", str(regular))
            if bold.exists():
                pdf.add_font("NotoSans", "B", str(bold))
            else:
                pdf.add_font("NotoSans", "B", str(regular))
        else:
            logger.warning(
                f"NotoSans fonts not found in {_FONTS_DIR}. "
                "Falling back to Helvetica (poor Vietnamese support)."
            )
            pdf.add_font("NotoSans", "", "Helvetica")
            pdf.add_font("NotoSans", "B", "Helvetica")

    def _render_cover_page(self, pdf: BrandStrategyPDF) -> None:
        """Render branded cover page."""
        pdf._skip_header = True
        pdf.add_page()

        pdf.set_fill_color(*self.colors["primary"])
        pdf.rect(0, 0, pdf.w, 100, "F")

        pdf.set_y(35)
        pdf.set_font("NotoSans", "B", 28)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(
            0, 15, self.template.brand_name, align="C", new_x="LMARGIN", new_y="NEXT"
        )

        pdf.set_font("NotoSans", "", 16)
        pdf.cell(
            0, 10, "Brand Strategy Document", align="C", new_x="LMARGIN", new_y="NEXT"
        )

        pdf.set_draw_color(*self.colors["accent"])
        pdf.set_line_width(2)
        y = pdf.get_y() + 10
        pdf.line(pdf.w / 2 - 40, y, pdf.w / 2 + 40, y)

        pdf._skip_header = False

    def _render_toc(self, pdf: BrandStrategyPDF, content: dict[str, Any]) -> None:
        """Render table of contents."""
        pdf.add_page()
        pdf.set_font("NotoSans", "B", 18)
        pdf.set_text_color(*self.colors["primary"])
        pdf.cell(0, 12, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        pdf.set_font("NotoSans", "", 11)
        pdf.set_text_color(60, 60, 60)

        for i, section in enumerate(self.template.sections, 1):
            if section.id == "cover":
                continue
            section_content = self._resolve_content(content, section.content_key)
            if section_content is None and not section.required:
                continue
            pdf.cell(0, 8, f"{i}. {section.title}", new_x="LMARGIN", new_y="NEXT")

    def _render_section(
        self,
        pdf: BrandStrategyPDF,
        title: str,
        subtitle: str,
        content: Any,
    ) -> None:
        """Render a document section with title and content."""
        pdf.set_font("NotoSans", "B", 16)
        pdf.set_text_color(*self.colors["primary"])
        pdf.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")

        if subtitle:
            pdf.set_font("NotoSans", "", 10)
            pdf.set_text_color(128, 128, 128)
            pdf.cell(0, 6, subtitle, new_x="LMARGIN", new_y="NEXT")

        pdf.set_draw_color(*self.colors["accent"])
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y() + 2, pdf.w - 10, pdf.get_y() + 2)
        pdf.ln(8)

        if content is None:
            pdf.set_font("NotoSans", "", 11)
            pdf.set_text_color(128, 128, 128)
            pdf.cell(0, 8, "(No content available)", new_x="LMARGIN", new_y="NEXT")
        elif isinstance(content, str):
            pdf.set_font("NotoSans", "", 11)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 6, content)
        elif isinstance(content, dict):
            self._render_dict_content(pdf, content)
        elif isinstance(content, list):
            if content and isinstance(content[0], dict):
                self._render_table(pdf, content)
            else:
                for item in content:
                    pdf.set_font("NotoSans", "", 11)
                    pdf.set_text_color(60, 60, 60)
                    pdf.cell(6, 6, "•")
                    pdf.multi_cell(0, 6, str(item))

    def _render_dict_content(
        self, pdf: BrandStrategyPDF, data: dict[str, Any], level: int = 0
    ) -> None:
        """Recursively render dict content as labeled paragraphs."""
        for key, value in data.items():
            label = key.replace("_", " ").title()
            indent = level * 5

            pdf.set_x(10 + indent)
            pdf.set_font("NotoSans", "B", 11)
            pdf.set_text_color(*self.colors["primary"])
            pdf.cell(0, 7, label, new_x="LMARGIN", new_y="NEXT")

            if isinstance(value, str):
                pdf.set_x(10 + indent)
                pdf.set_font("NotoSans", "", 11)
                pdf.set_text_color(60, 60, 60)
                pdf.multi_cell(0, 6, value)
                pdf.ln(2)
            elif isinstance(value, dict):
                self._render_dict_content(pdf, value, level + 1)
            elif isinstance(value, list):
                for item in value:
                    pdf.set_x(10 + indent + 5)
                    pdf.set_font("NotoSans", "", 11)
                    pdf.set_text_color(60, 60, 60)
                    pdf.cell(5, 6, "•")
                    pdf.multi_cell(0, 6, str(item))

    def _render_table(self, pdf: BrandStrategyPDF, data: list[dict[str, Any]]) -> None:
        """Render data as a formatted table."""
        if not data:
            return

        headers = list(data[0].keys())
        col_width = (pdf.w - 20) / len(headers)

        pdf.set_font("NotoSans", "B", 9)
        pdf.set_fill_color(*self.colors["primary"])
        pdf.set_text_color(255, 255, 255)
        for header in headers:
            label = header.replace("_", " ").title()
            pdf.cell(col_width, 7, label, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("NotoSans", "", 9)
        pdf.set_text_color(60, 60, 60)
        for row in data:
            for header in headers:
                value = str(row.get(header, ""))
                if len(value) > 40:
                    value = value[:37] + "..."
                pdf.cell(col_width, 6, value, border=1)
            pdf.ln()

    def _embed_image(self, pdf: BrandStrategyPDF, image_path: str) -> None:
        """Embed an image centered on the page."""
        path = Path(image_path)
        if not path.exists():
            logger.warning(f"Image not found: {image_path}")
            return

        pdf.ln(5)
        max_width = pdf.w - 40
        pdf.image(str(path), x=(pdf.w - max_width) / 2, w=max_width)
        pdf.ln(5)

    def _resolve_content(self, content: dict[str, Any], content_key: str) -> Any:
        """Resolve dotted content key path like 'phase_5_output.roadmap'."""
        parts = content_key.split(".")
        current = content
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current
