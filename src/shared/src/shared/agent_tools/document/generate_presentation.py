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
    and support for images, tables, and two-column layouts. Content
    is a JSON string parsed into a dict; each slide in the deck is
    populated by looking up a specific key in that dict. Missing
    keys silently produce an empty slide body (`required=False`
    slides are skipped entirely) — so empty slides indicate a key
    mismatch and must be fixed at the call site.

    Args:
        content: JSON string parsed into a dict. The 12-slide
            default deck pulls content from these keys (any missing
            key leaves that slide empty):

              - "cover": str, cover-slide tagline.
              - "executive_summary": str / list[str], used for the
                Executive Summary slide bullets.
              - "phase_0_output": str / dict / list, Business Context
                slide.
              - "phase_1_output": str / dict / list, Market Intelligence
                slide. Also REQUIRED to contain a nested key
                "target_segments" (list[dict] preferred) for the
                Target Audience two-column slide:
                  phase_1_output.target_segments → list of segment
                  dicts (e.g. [{"Segment": "Q1 executives", ...}]).
              - "phase_2_output": str / dict / list, Brand Positioning slide.
              - "phase_3_output": str / dict / list, Brand Identity
                two-column slide.
              - "phase_4_output": str / dict / list, Communication
                Framework slide.
              - "phase_5_output": **must be a dict** with two
                nested keys; a string value here leaves both
                Roadmap and KPIs slides empty.
                  - "roadmap": list[dict] preferred (renders as a
                    table on the Implementation Roadmap slide;
                    e.g. [{"Horizon": "0-3 mo", "Items": "...", "Investment": "..."}]).
                  - "measurement": list[dict] preferred (renders
                    as a table on the KPIs & Measurement slide;
                    e.g. [{"KPI": "...", "Target": "...", "Cadence": "..."}]).
                    Include a row per metric even when a column is
                    unknown — use "no data — measure pre-launch"
                    rather than dropping the row.
              - "images" (optional): dict with keys "mood_board" and
                "brand_key" mapping to image file paths. Both slides
                are `required=False`; if the key is absent the
                corresponding slide is skipped.

            Each value (other than `images`) can be:
              - str → split into bullet lines on newline
              - list[str] → bullets directly
              - list[dict] → rendered as a table on table-layout
                slides (Roadmap, KPIs)
              - dict → rendered as "Label: value" bullets

            Minimal example (covers every required slide):
              {
                "cover": "Modern Saigonese Gastronomy",
                "executive_summary": ["Reposition Signature ...", "Win Q1 executives"],
                "phase_0_output": {"Problem": "Brand dilution", "Scope": "Repositioning"},
                "phase_1_output": {
                  "Top finding": "...",
                  "target_segments": [{"Segment": "Q1 executives", "JTBD": "..."}, ...]
                },
                "phase_2_output": {"Positioning statement": "...", "POD": [...]},
                "phase_3_output": {"Archetype": "Caregiver", "Visual": "..."},
                "phase_4_output": {"Messaging": [...], "Channels": [...]},
                "phase_5_output": {
                  "roadmap": [{"Horizon": "0-3 mo", "Items": "...", "Investment": "..."}, ...],
                  "measurement": [{"KPI": "...", "Target": "...", "Cadence": "..."}, ...]
                }
              }

        brand_name: Brand name for title slide.
        brand_colors: List of 3 hex colors [primary, secondary, accent].
        images: Optional dict mapping slide_id (e.g. "brand_key",
            "mood_board") to image file path; embedded into the
            corresponding image-layout slides.
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
            f"Presentation FILE saved to disk.\n"
            f"Path: {result_path}\n"
            f"Slides: {len(template.slides)}\n\n"
            f"⚠️ IMPORTANT: File on disk ≠ user delivery. List the slide "
            f"structure (title + key point per slide) in your next "
            f"user-facing response so user knows what was built — file path "
            f"alone is not a delivery."
        )
    except Exception as e:
        logger.error(f"Presentation generation failed: {e}")
        return f"Presentation generation failed: {e}"
