"""generate_document tool — PDF/DOCX document generation.

Plain function callable by the agent. Routes to PDF or DOCX builder
based on doc_format parameter.
"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from ._output_path import append_manifest, resolve_output_path
from .docx_builder import BrandStrategyDOCXBuilder
from .pdf_builder import BrandStrategyPDFBuilder
from .templates.brand_strategy import BrandStrategyTemplate


def _coerce_content_dict(
    content: dict[str, Any] | str,
) -> tuple[dict[str, Any] | None, str]:
    """Normalize structured document content from current and legacy callers."""
    if isinstance(content, dict):
        return content, ""
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        preview = content[:200] if isinstance(content, str) else type(content).__name__
        logger.error(
            "generate_document content parse error: "
            f"{exc!r}; content_preview={preview!r}"
        )
        return None, f"Invalid content JSON: {exc}"
    if not isinstance(parsed, dict):
        logger.error(
            "generate_document content parse error: "
            f"expected object, got {type(parsed).__name__}"
        )
        return None, "Invalid content JSON: top-level content must be an object"
    return parsed, ""


def generate_document(
    content: dict[str, Any] | str,
    doc_format: str = "docx",
    brand_name: str = "Brand",
    brand_colors: list[str] | None = None,
    images: str | None = None,
    output_path: str | None = None,
) -> str:
    """Build a long-form branded PDF or DOCX deliverable from phase content.

    Renders a professionally formatted document with cover page, table of
    contents, and per-section narrative — driven by ``content`` (a dict
    whose keys map to template sections; missing
    keys yield a literal "(No content available)" placeholder so empty
    bodies surface a key mismatch instead of being silently dropped).

    Use when the user needs a strategy document, brand guidelines, or any
    formal long-form stakeholder report. Do NOT use when the deliverable
    is a slide deck (use ``generate_presentation``), a tabular dashboard
    (use ``generate_spreadsheet``), or a quick lightweight share (use
    ``export_to_markdown``).

    Args:
        content: Dict of document sections. Legacy callers may pass a
            JSON string, but agent callers should pass a structured
            object directly to avoid malformed function calls on large
            strategy documents. The dict MUST contain the following
            top-level keys (any missing key will produce a
            "(No content available)" placeholder in its section):

              - "cover": str, the cover-page tagline / sub-heading.
              - "executive_summary": str OR list[str] bullets, the
                1-page punchline summary.
              - "phase_0_output": str / dict / list. Phase 0 problem
                diagnosis. dict keys become subheadings; list[str]
                becomes bullets; list[dict] becomes a table.
              - "phase_0_5_output" (optional): same shape, brand
                equity audit. Can be omitted for new_brand scope.
              - "phase_1_output": same shape, market intelligence.
              - "phase_2_output": same shape, brand strategy core
                (positioning + POPs/PODs + essence).
              - "phase_3_output": same shape, brand identity
                (archetype + visual + verbal direction).
              - "phase_4_output": same shape, communication
                framework (messaging + persuasion mechanics + journey flow + channels).
              - "phase_5_output": **must be a dict** (not a string)
                with TWO required nested keys; passing a single
                string here leaves both Implementation Roadmap and
                KPI Framework sections empty.
                  - "roadmap": str / dict / list — the 3-horizon
                    implementation plan (e.g. list[dict] like
                    [{"Horizon": "0-3 mo", "Items": "...", "Investment": "..."}]
                    renders as a table; list[str] renders as bullets).
                  - "measurement": str / dict / list — the KPI
                    framework + tracking plan (list[dict] preferred
                    so the KPI table renders, e.g.
                    [{"KPI": "...", "Target": "...", "Cadence": "..."}]).
              - "appendices" (optional): str / dict / list, raw
                source material the document should append.

            Each value can be:
              - str → rendered as one paragraph
              - dict → rendered as nested headings + body
              - list[str] → rendered as bullets
              - list[dict] → rendered as a table

            Minimal example (all required keys, brief content):
              {
                "cover": "Modern Saigonese Gastronomy",
                "executive_summary": "Reposition Signature as ...",
                "phase_0_output": {
                  "Problem": "Brand dilution",
                  "Scope": "Repositioning"
                },
                "phase_1_output": {
                  "SWOT": {...},
                  "White space": "..."
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
                    {"Horizon": "0-3 mo", "Items": "..."},
                    ...
                  ],
                  "measurement": [
                    {"KPI": "...", "Target": "...", "Cadence": "..."},
                    ...
                  ]
                }
              }

        doc_format: Output format — "docx" (default) or "pdf".
        brand_name: Brand name for cover page and headers.
        brand_colors: List of 3 hex colors [primary, secondary, accent].
            Default: ["#1B365D", "#F5F0E8", "#D4A84B"].
        images: JSON string mapping section_id to image file path
            (e.g. {"brand_identity": "/path/to/mood_board.png"}).
        output_path: Optional override. **Leave None in normal use** —
            the tool anchors output under
            ``$BRANDMIND_OUTPUT_DIR/documents/<brand-slug>/<timestamp>_brand_strategy.<ext>``
            automatically so concurrent or repeated runs never overwrite
            each other. Provide a value only when you specifically need
            to control the filename; bare filenames or paths outside
            the configured base are redirected back into the
            per-brand subdir for safety.

    Returns:
        Message with path to generated document file.
    """
    content_dict, content_error = _coerce_content_dict(content)
    if content_error:
        return content_error
    assert content_dict is not None

    images_dict: dict[str, str] | None = None
    if images:
        try:
            images_dict = json.loads(images)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Invalid images JSON, ignoring images")

    colors = brand_colors or ["#1B365D", "#F5F0E8", "#D4A84B"]
    template = BrandStrategyTemplate(brand_name=brand_name, brand_colors=colors)

    ext = "pdf" if doc_format == "pdf" else "docx"
    output_path = resolve_output_path(
        output_path,
        category="documents",
        brand_name=brand_name,
        default_filename=f"brand_strategy.{ext}",
    )

    try:
        if doc_format == "docx":
            builder = BrandStrategyDOCXBuilder(template=template)
        else:
            builder = BrandStrategyPDFBuilder(template=template)  # type: ignore[assignment]

        result_path = builder.build(
            content=content_dict,
            output_path=output_path,
            images=images_dict,
        )
        append_manifest(
            brand_name=brand_name,
            category="documents",
            tool="generate_document",
            path=result_path,
        )
        return (
            f"Document FILE saved to disk.\n"
            f"Format: {doc_format.upper()}\n"
            f"Path: {result_path}\n\n"
            f"⚠️ IMPORTANT: File on disk ≠ user delivery. Summarize the "
            f"document's structure (sections included, key content per "
            f"section) in your next user-facing response so user knows what "
            f"was assembled — file path alone is not a delivery."
        )
    except Exception as e:
        logger.error(f"Document generation failed: {e}")
        return f"Document generation failed: {e}"
