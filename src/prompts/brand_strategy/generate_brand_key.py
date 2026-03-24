"""Brand Key one-pager prompt template for image generation.

Creates a professional infographic showing the 9 Brand Key components
in consulting-firm visual style (McKinsey/BCG quality).
"""

BRAND_KEY_PROMPT_TEMPLATE = """\
Create a professional Brand Key one-pager infographic — a single-page \
visual summary of brand strategy, styled like a top-tier consulting \
firm deliverable (McKinsey, BCG quality).

## Brand Identity
Brand: {{brand_name}}
Brand Colors: {{colors}}

## Visual Design Specifications
- Layout: Vertical single-page infographic, portrait orientation \
(9:16 aspect ratio)
- Style: Clean, modern corporate — consulting-firm strategy \
document quality
- Typography: Bold sans-serif section headers in brand primary color, \
clean body text in dark gray (#333333), clear size hierarchy between \
header and content
- Color usage: Section headers and accent elements in brand colors; \
body text dark gray; background pure white or very light gray (#F8F8F8); \
thin colored accent bars between sections
- Visual elements: Subtle line icons or pictograms next to each \
section header for scannability; thin horizontal divider lines \
between sections

## Content Sections (ALL must be visible and readable, top to bottom)

1. **BRAND NAME** (large, bold, centered at top with brand-color \
accent bar beneath): {{brand_name}}
2. **ROOT STRENGTH** (heritage & core competency): {{root_strength}}
3. **COMPETITIVE ENVIRONMENT** (market context & key competitors): \
{{competitive_environment}}
4. **TARGET** (primary audience definition): {{target}}
5. **INSIGHT** (the consumer truth that drives brand relevance): \
{{insight}}
6. **BENEFITS** (functional + emotional benefits): {{benefits}}
7. **VALUES & PERSONALITY** (brand character traits): \
{{values_personality}}
8. **REASONS TO BELIEVE** (proof points & evidence): \
{{reasons_to_believe}}
9. **DISCRIMINATOR** (unique differentiator — visually emphasized \
with a highlight box): {{discriminator}}
10. **BRAND ESSENCE** (2-4 word mantra — large, prominent, centered \
at bottom with brand-color background block): {{brand_essence}}

## Quality Requirements
- Every section header MUST be clearly labeled and visually distinct \
from body text
- All text MUST be legible — no overlapping elements, no text smaller \
than caption size
- The DISCRIMINATOR section should stand out visually (bordered box \
or highlight background)
- The BRAND ESSENCE at the bottom should feel like the visual anchor \
and culmination of the page
- Overall: a strategy document you would confidently present to a \
CEO or board of directors\
"""
