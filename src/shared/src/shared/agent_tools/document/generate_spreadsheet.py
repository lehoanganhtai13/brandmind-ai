"""generate_spreadsheet tool — XLSX spreadsheet generation.

Plain function callable by the agent. Generates brand strategy
spreadsheets from templates with formulas and formatting.
"""

from __future__ import annotations

import json
import os
from typing import Any

from loguru import logger

from .spreadsheet_templates import SPREADSHEET_TEMPLATES
from .xlsx_builder import BrandStrategyXLSXBuilder


def generate_spreadsheet(
    content: str,
    template: str = "competitor_analysis",
    brand_name: str = "Brand",
    brand_colors: list[str] | None = None,
    output_path: str | None = None,
) -> str:
    """Generate brand strategy spreadsheets in XLSX format.

    Formula-driven with auto-calculations, professional formatting,
    and frozen header rows.

    Available templates: competitor_analysis, brand_audit,
    content_calendar, kpi_dashboard, budget_plan.

    Args:
        content: JSON string mapping sheet names to list of row dicts.
            Example: {"Overview": [{"Competitor": "A", "Rating": 4.5}]}
        template: Template key from SPREADSHEET_TEMPLATES.
        brand_name: Brand name for title rows.
        brand_colors: List of hex colors (reserved for future use).
        output_path: Custom output path. Default uses BRANDMIND_OUTPUT_DIR.

    Returns:
        Message with path to generated XLSX file.
    """
    if template not in SPREADSHEET_TEMPLATES:
        return (
            f"Unknown template '{template}'. "
            f"Available: {', '.join(SPREADSHEET_TEMPLATES.keys())}"
        )

    try:
        data: dict[str, list[dict[str, Any]]] = json.loads(content)
    except (json.JSONDecodeError, TypeError) as e:
        return f"Invalid content JSON: {e}"

    if not output_path:
        base_dir = os.environ.get(
            "BRANDMIND_OUTPUT_DIR",
            os.path.join(os.getcwd(), "brandmind-output"),
        )
        safe_name = brand_name.lower().replace(" ", "_")
        output_path = os.path.join(
            base_dir,
            "spreadsheets",
            f"{safe_name}_{template}.xlsx",
        )

    try:
        template_config = SPREADSHEET_TEMPLATES[template]
        builder = BrandStrategyXLSXBuilder(brand_name=brand_name)
        builder.build_from_template(
            template_config=template_config,
            data=data,
        )
        result_path = builder.save(output_path)
        return (
            f"Spreadsheet generated successfully.\n"
            f"Template: {template}\n"
            f"Path: {result_path}"
        )
    except Exception as e:
        logger.error(f"Spreadsheet generation failed: {e}")
        return f"Spreadsheet generation failed: {e}"
