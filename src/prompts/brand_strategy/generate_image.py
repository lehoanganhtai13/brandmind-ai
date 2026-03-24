"""Brand asset prompt templates for Gemini image generation.

Each template is optimized for Gemini 3.1 Flash Image Preview.
Templates use professional image generation best practices:
- Specific style descriptors (photorealistic, illustration, etc.)
- Explicit composition instructions (layout, framing, visual weight)
- Lighting specifications (natural, studio, golden hour, etc.)
- Material/texture details for realism
- Quality modifiers for professional output
"""

BRAND_PROMPT_TEMPLATES: dict[str, str] = {
    "mood_board": (
        "Professional brand mood board collage for a {{category}} brand. "
        "Visual style: {{style}}. Color palette: {{colors}}. "
        "Include: lifestyle photography, material textures, typography samples, "
        "color swatches with hex codes, spatial/architectural references, "
        "and product imagery that evokes the brand's emotional territory. "
        "Layout: organized grid collage with clean white borders between elements. "
        "Composition: overhead flat-lay arrangement, balanced visual weight "
        "across quadrants. "
        "Lighting: soft, natural, diffused — studio reference board aesthetic. "
        "Quality: high-resolution, print-ready, design agency presentation standard."
    ),
    "logo_concept": (
        "Logo concept design for '{{brand_name}}', a {{category}} brand. "
        "Design direction: {{style}}. Concept: {{concept}}. "
        "Clean vector-style logo mark on pure white background. "
        "Style: minimalist, geometric precision, scalable from favicon to billboard. "
        "Typography: modern sans-serif or custom lettering that reflects "
        "brand personality. "
        "Composition: centered, generous negative space around the mark. "
        "Include both: icon/symbol mark and wordmark lockup arranged vertically. "
        "Rendering: flat design, no gradients, no shadows, no 3D effects. "
        "Color: use {{colors}} as primary palette. Must work in single-color "
        "(black) version."
    ),
    "color_palette": (
        "Professional color palette reference board for brand identity design. "
        "Primary colors: {{colors}}. "
        "Show: large rectangular color swatches arranged horizontally with hex "
        "code labels beneath each, "
        "a color harmony wheel showing relationships between palette colors, "
        "sample usage — text on light and dark backgrounds, button styles, "
        "gradient combinations, and complementary accent suggestions. "
        "Layout: clean organized grid on white background, design system "
        "documentation aesthetic. "
        "Typography: small clean sans-serif labels for hex codes and color names. "
        "Quality: precise, clinical, design-reference-grade rendering."
    ),
    "packaging": (
        "Photorealistic packaging mockup for {{category}} product: {{item}}. "
        "Brand: '{{brand_name}}'. Design style: {{style}}. "
        "Brand colors: {{colors}}. "
        "Composition: 3/4 angle product hero shot with subtle drop shadow "
        "on clean neutral surface. "
        "Lighting: soft studio lighting with slight rim light for depth, "
        "no harsh shadows. "
        "Material rendering: realistic textures — matte paper, glossy finish, "
        "kraft paper, metallic foil, or transparent elements as appropriate "
        "for the product category. "
        "Environment: clean minimal set — product is the hero, "
        "no distracting elements. "
        "Quality: commercial product photography standard, suitable for "
        "pitch deck or e-commerce."
    ),
    "interior": (
        "Interior design concept visualization for a {{category}} establishment. "
        "Atmosphere and design style: {{style}}. "
        "Brand color integration: {{colors}}. "
        "Composition: wide-angle interior shot showing full spatial design — "
        "seating areas, counter and service area, brand elements "
        "(signage, menu boards, logo placement). "
        "Lighting: warm ambient lighting with accent spots, golden hour mood "
        "through large windows. "
        "Materials: natural wood, polished concrete, matte metal, and green "
        "plant elements as appropriate. "
        "People: empty space to focus purely on design intent (no people). "
        "Quality: architectural visualization standard, photorealistic rendering, "
        "warm inviting mood."
    ),
    "social_media": (
        "Social media post template design for '{{brand_name}}', "
        "a {{category}} brand. "
        "Visual style: {{style}}. Brand colors: {{colors}}. "
        "Layout: clean scroll-stopping composition with clear visual hierarchy — "
        "hero image area (60% of frame), text overlay zone (30%), "
        "brand mark corner placement (10%). "
        "Typography: bold headline area at top, clean body text zone, "
        "brand-consistent font pairing. "
        "Aspect ratio: square (1:1) optimized for Instagram feed. "
        "Include: subtle brand color accents, consistent border or frame "
        "treatment, space for text overlay that does not obscure key "
        "visual elements. "
        "Quality: digital-optimized, vibrant colors, high contrast "
        "for mobile screens."
    ),
}
