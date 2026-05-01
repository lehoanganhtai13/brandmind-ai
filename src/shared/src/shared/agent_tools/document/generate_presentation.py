"""generate_presentation tool — PPTX pitch deck generation.

Plain function callable by the agent. Generates brand strategy
pitch decks using python-pptx.
"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from ._output_path import append_manifest, resolve_output_path
from .pptx_builder import BrandStrategyPPTXBuilder
from .templates.brand_strategy import BrandStrategyDeckTemplate


def generate_presentation(
    content: str,
    brand_name: str = "Brand",
    brand_colors: list[str] | None = None,
    images: dict[str, str] | None = None,
    output_path: str | None = None,
) -> str:
    """Build a 10–12 slide branded executive PPTX deck from phase content.

    Renders title, content, two-column, image, and table slides with
    speaker notes — driven by ``content`` (a JSON string parsed into a
    dict whose keys map to slide content_keys; a missing required-slide
    key yields an empty body, optional slides are skipped, so empty
    slides surface a key mismatch instead of silently passing).

    Use when the user needs to pitch a strategy, summarise for
    stakeholders, or run a live presentation. Do NOT use when long-form
    prose narrative is needed (use ``generate_document``) or when the
    artifact is primarily quantitative tables or KPI tracking (use
    ``generate_spreadsheet``).

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
                "executive_summary": [
                  "Reposition Signature ...",
                  "Win Q1 executives"
                ],
                "phase_0_output": {
                  "Problem": "Brand dilution",
                  "Scope": "Repositioning"
                },
                "phase_1_output": {
                  "Top finding": "...",
                  "target_segments": [
                    {"Segment": "Q1 executives", "JTBD": "..."},
                    ...
                  ]
                },
                "phase_2_output": {
                  "Positioning statement": "...",
                  "POD": [...]
                },
                "phase_3_output": {
                  "Archetype": "Caregiver",
                  "Visual": "..."
                },
                "phase_4_output": {
                  "Messaging": [...],
                  "Channels": [...]
                },
                "phase_5_output": {
                  "roadmap": [
                    {
                      "Horizon": "0-3 mo",
                      "Items": "...",
                      "Investment": "..."
                    },
                    ...
                  ],
                  "measurement": [
                    {"KPI": "...", "Target": "...", "Cadence": "..."},
                    ...
                  ]
                }
              }

        brand_name: Brand name for title slide.
        brand_colors: List of 3 hex colors [primary, secondary, accent].
        images: Optional dict mapping slide_id (e.g. "brand_key",
            "mood_board") to image file path; embedded into the
            corresponding image-layout slides.
        output_path: Optional override. **Leave None in normal use** —
            the tool anchors output under
            ``$BRANDMIND_OUTPUT_DIR/presentations/<brand-slug>/<timestamp>_strategy_deck.pptx``
            automatically so concurrent or repeated runs never
            overwrite each other. Provide a value only when you
            specifically need to control the filename; bare filenames
            or paths outside the configured base are redirected back
            into the per-brand subdir for safety.

    Returns:
        Message with path to generated PPTX file.
    """
    try:
        content_dict: dict[str, Any] = json.loads(content)
    except (json.JSONDecodeError, TypeError) as e:
        return f"Invalid content JSON: {e}"

    colors = brand_colors or ["#1B365D", "#F5F0E8", "#D4A84B"]
    template = BrandStrategyDeckTemplate(brand_name=brand_name, brand_colors=colors)

    output_path = resolve_output_path(
        output_path,
        category="presentations",
        brand_name=brand_name,
        default_filename="strategy_deck.pptx",
    )

    try:
        builder = BrandStrategyPPTXBuilder(template=template)
        result_path = builder.build(
            content=content_dict,
            output_path=output_path,
            images=images,
        )
        append_manifest(
            brand_name=brand_name,
            category="presentations",
            tool="generate_presentation",
            path=result_path,
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
