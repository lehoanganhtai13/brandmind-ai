"""generate_brand_key tool — deterministic Brand Key one-pager visual."""

from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any

from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from shared.agent_tools.document._output_path import (
    append_manifest,
    resolve_output_path,
)

_CANVAS_WIDTH = 1440
_CANVAS_HEIGHT = 2560
_MARGIN = 86
_PRIMARY = "#17324D"
_ACCENT = "#C99A3B"
_TEXT = "#24313D"
_MUTED = "#66717C"
_CARD_BG = "#FFFFFF"
_PAGE_BG = "#F7F5F0"

_FONT_PATH_ENV = "BRANDMIND_BRAND_KEY_FONT_PATH"
_BOLD_FONT_PATH_ENV = "BRANDMIND_BRAND_KEY_BOLD_FONT_PATH"
_FONT_CANDIDATES = (
    "DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "C:/Windows/Fonts/arial.ttf",
)
_BOLD_FONT_CANDIDATES = (
    "DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "C:/Windows/Fonts/arialbd.ttf",
)

_Font = ImageFont.FreeTypeFont | ImageFont.ImageFont
_font_fallback_warned = False

_BRAND_KEY_LABELS = (
    ("Root Strengths", "root_strength"),
    ("Competitive Environment", "competitive_environment"),
    ("Target", "target"),
    ("Insight", "insight"),
    ("Benefits", "benefits"),
    ("Values, Beliefs & Personality", "values_personality"),
    ("Reasons to Believe", "reasons_to_believe"),
    ("Discriminator", "discriminator"),
    ("Brand Essence", "brand_essence"),
)


def _configured_font_paths(env_name: str) -> tuple[str, ...]:
    """Read optional self-hosted font paths from a platform-safe env value."""
    value = os.getenv(env_name, "")
    return tuple(part.strip() for part in value.split(os.pathsep) if part.strip())


def _load_truetype_candidate(candidates: tuple[str, ...], size: int) -> _Font | None:
    """Return the first loadable TrueType font from configured/system candidates."""
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return None


def _load_default_font(size: int) -> _Font:
    """Return Pillow's bundled default font across Pillow versions."""
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _load_font(size: int, *, bold: bool = False) -> _Font:
    """Load a Unicode-capable font for portable Brand Key rendering."""
    global _font_fallback_warned

    configured = _configured_font_paths(_FONT_PATH_ENV)
    if bold:
        candidates = (
            *_configured_font_paths(_BOLD_FONT_PATH_ENV),
            *configured,
            *_BOLD_FONT_CANDIDATES,
            *_FONT_CANDIDATES,
        )
    else:
        candidates = (*configured, *_FONT_CANDIDATES)

    font = _load_truetype_candidate(candidates, size)
    if font is not None:
        return font

    if not _font_fallback_warned:
        logger.warning(
            "Brand Key renderer could not load a Unicode TrueType font; "
            "set BRANDMIND_BRAND_KEY_FONT_PATH for production deployments."
        )
        _font_fallback_warned = True
    return _load_default_font(size)


def _text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: _Font,
) -> int:
    """Measure rendered text width in pixels."""
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    return int(right - left)


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: _Font,
    max_width: int,
    max_lines: int,
) -> list[str]:
    """Wrap text to fit a card while preserving the strongest content cues."""
    words = re.sub(r"\s+", " ", text.strip()).split(" ")
    lines: list[str] = []
    current = ""

    for word in words:
        candidate = word if not current else f"{current} {word}"
        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) == max_lines:
            break

    if current and len(lines) < max_lines:
        lines.append(current)

    if len(lines) == max_lines and " ".join(lines) != " ".join(words):
        lines[-1] = lines[-1].rstrip(".,;: ") + "..."
    return lines


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    lines: list[str],
    font: _Font,
    fill: str,
    line_gap: int,
) -> int:
    """Draw wrapped lines and return the next vertical cursor."""
    x, y = position
    _, top, _, bottom = draw.textbbox((0, 0), "Ag", font=font)
    line_height = int(bottom - top) + line_gap
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def _parse_primary_color(colors: str) -> str:
    """Use the first hex color in the user palette when one is supplied."""
    match = re.search(r"#[0-9A-Fa-f]{6}", colors)
    return match.group(0) if match else _PRIMARY


def _brand_key_components(
    *,
    root_strength: str,
    competitive_environment: str,
    target: str,
    insight: str,
    benefits: str,
    values_personality: str,
    reasons_to_believe: str,
    discriminator: str,
    brand_essence: str,
) -> list[dict[str, str]]:
    """Return the canonical Brand Key component list rendered in the image."""
    values = {
        "root_strength": root_strength,
        "competitive_environment": competitive_environment,
        "target": target,
        "insight": insight,
        "benefits": benefits,
        "values_personality": values_personality,
        "reasons_to_believe": reasons_to_believe,
        "discriminator": discriminator,
        "brand_essence": brand_essence,
    }
    return [{"label": label, "value": values[key]} for label, key in _BRAND_KEY_LABELS]


def _write_brand_key_source(
    *,
    output_path: str,
    brand_name: str,
    components: list[dict[str, str]],
) -> Path:
    """Persist machine-readable source text for artifact QA and accessibility."""
    sidecar_path = Path(output_path).with_suffix(".brand_key.json")
    payload = {
        "artifact_type": "brand_key_image",
        "brand_name": brand_name,
        "components": components,
    }
    sidecar_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return sidecar_path


def _render_brand_key_image(
    *,
    brand_name: str,
    root_strength: str,
    competitive_environment: str,
    target: str,
    insight: str,
    benefits: str,
    values_personality: str,
    reasons_to_believe: str,
    discriminator: str,
    brand_essence: str,
    colors: str,
    output_path: str,
) -> None:
    """Render a text-faithful Brand Key image for stakeholder handoff."""
    primary = _parse_primary_color(colors)
    image = Image.new("RGB", (_CANVAS_WIDTH, _CANVAS_HEIGHT), _PAGE_BG)
    draw = ImageDraw.Draw(image)

    title_font = _load_font(54, bold=True)
    subtitle_font = _load_font(28)
    section_font = _load_font(29, bold=True)
    body_font = _load_font(27)
    essence_font = _load_font(43, bold=True)

    draw.rectangle((0, 0, _CANVAS_WIDTH, 210), fill=primary)
    draw.text((_MARGIN, 54), brand_name, font=title_font, fill="white")
    draw.text(
        (_MARGIN, 128),
        "Brand Key one-pager",
        font=subtitle_font,
        fill="#F2E7C9",
    )

    sections = [
        ("ROOT STRENGTHS", root_strength),
        ("COMPETITIVE ENVIRONMENT", competitive_environment),
        ("TARGET", target),
        ("INSIGHT", insight),
        ("BENEFITS", benefits),
        ("VALUES, BELIEFS & PERSONALITY", values_personality),
        ("REASONS TO BELIEVE", reasons_to_believe),
        ("DISCRIMINATOR", discriminator),
    ]

    y = 245
    card_h = 198
    gap = 22
    card_w = _CANVAS_WIDTH - (_MARGIN * 2)
    text_w = card_w - 58

    for title, body in sections:
        draw.rounded_rectangle(
            (_MARGIN, y, _MARGIN + card_w, y + card_h),
            radius=18,
            fill=_CARD_BG,
            outline="#E3DDD2",
            width=2,
        )
        draw.rectangle((_MARGIN, y, _MARGIN + 12, y + card_h), fill=_ACCENT)
        draw.text((_MARGIN + 30, y + 24), title, font=section_font, fill=primary)
        lines = _wrap_text(draw, body, body_font, text_w, max_lines=3)
        _draw_wrapped(
            draw,
            (_MARGIN + 30, y + 76),
            lines,
            body_font,
            _TEXT,
            line_gap=8,
        )
        y += card_h + gap

    essence_top = y + 8
    essence_bottom = _CANVAS_HEIGHT - 90
    draw.rounded_rectangle(
        (_MARGIN, essence_top, _MARGIN + card_w, essence_bottom),
        radius=20,
        fill=primary,
    )
    draw.text(
        (_MARGIN + 36, essence_top + 30),
        "BRAND ESSENCE",
        font=section_font,
        fill="#F2E7C9",
    )
    essence_lines = _wrap_text(draw, brand_essence, essence_font, text_w, 2)
    _draw_wrapped(
        draw,
        (_MARGIN + 36, essence_top + 90),
        essence_lines,
        essence_font,
        "white",
        line_gap=14,
    )
    draw.text(
        (_MARGIN + 36, essence_bottom - 44),
        "Prepared for stakeholder review",
        font=_load_font(22),
        fill=_MUTED,
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="JPEG", quality=94)


def generate_brand_key(
    brand_name: str,
    root_strength: str,
    competitive_environment: str,
    target: str,
    insight: str,
    benefits: str,
    values_personality: str,
    reasons_to_believe: str,
    discriminator: str,
    brand_essence: str,
    colors: str = "navy blue, white, gold accent",
    session_id: str | None = None,
) -> list[dict[str, Any]] | str:
    """Generate a Brand Key one-pager visual summary.

    Creates a deterministic text-faithful infographic showing the 9
    Brand Key components used as the capstone visual in Phase 5
    deliverables.

    Args:
        brand_name: The brand name.
        root_strength: Core competency / heritage.
        competitive_environment: Key competitors and market.
        target: Target audience description.
        insight: Core consumer insight.
        benefits: Functional + emotional benefits.
        values_personality: Brand values and personality traits.
        reasons_to_believe: Evidence / proof points.
        discriminator: Key point of difference.
        brand_essence: 2-4 word brand essence / mantra.
        colors: Brand color palette description.
        session_id: Session ID for organizing output files.

    Returns:
        Multimodal image payload plus path and component summary.
    """
    try:
        safe_name = re.sub(r"[^\w\-]+", "_", brand_name.lower()).strip("_")
        output_path = resolve_output_path(
            None,
            category="images",
            brand_name=brand_name,
            default_filename=f"brand_key_{safe_name or 'brand'}.jpeg",
        )
        components = _brand_key_components(
            root_strength=root_strength,
            competitive_environment=competitive_environment,
            target=target,
            insight=insight,
            benefits=benefits,
            values_personality=values_personality,
            reasons_to_believe=reasons_to_believe,
            discriminator=discriminator,
            brand_essence=brand_essence,
        )
        _render_brand_key_image(
            brand_name=brand_name,
            root_strength=root_strength,
            competitive_environment=competitive_environment,
            target=target,
            insight=insight,
            benefits=benefits,
            values_personality=values_personality,
            reasons_to_believe=reasons_to_believe,
            discriminator=discriminator,
            brand_essence=brand_essence,
            colors=colors,
            output_path=output_path,
        )
        _write_brand_key_source(
            output_path=output_path,
            brand_name=brand_name,
            components=components,
        )
        append_manifest(
            brand_name=brand_name,
            category="images",
            tool="generate_brand_key",
            path=output_path,
        )
        image_bytes = Path(output_path).read_bytes()
        return [
            {
                "type": "image",
                "base64": base64.b64encode(image_bytes).decode("ascii"),
                "mime_type": "image/jpeg",
            },
            {
                "type": "text",
                "text": (
                    f"Brand Key IMAGE FILE saved to disk: {output_path}\n"
                    f"Brand: {brand_name}\n"
                    f"Essence: {brand_essence}\n\n"
                    f"⚠️ IMPORTANT: File on disk ≠ user delivery. "
                    f"To complete delivery, describe all 9 Brand Key components "
                    f"(Root Strengths, Competitive Environment, Target, "
                    f"Insight, Benefits, Values, Beliefs & Personality, "
                    f"Reasons to Believe, Discriminator, Brand Essence) "
                    f"in your next user-facing response with actual "
                    f"brand-specific content.\n\n"
                    f"To refine visual, use edit_image with "
                    f'image_path="{output_path}".'
                ),
            },
        ]
    except (RuntimeError, ValueError) as e:
        logger.error(f"generate_brand_key failed: {e}")
        return f"Brand Key generation failed: {e}"
