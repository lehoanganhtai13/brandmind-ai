# Phase 0.5: Brand Equity Audit (Rebrand Only)

## Mentor Script

### Opening
"Before changing anything, understand which current brand assets are worth preserving. This is the Brand Equity Audit step: inventory the brand assets before deciding what to keep, evolve, or discard."

### Key Questions
1. Current logo / visual identity: do customers recognize it quickly?
2. Slogan / tagline: does anyone remember it, and is it attached to the brand?
3. Which in-store experiences do customers mention most?
4. What is the user most proud of in the current brand?
5. What does the user most want to change?

### Concepts to Explain
- **Brand Equity** — intangible value created by the brand, such as recognition, trust, willingness to pay, and remembered experiences.
- **Preserve-Discard Matrix** — classify brand assets into Keep (high equity), Evolve (adapt while preserving essence), and Discard (no longer strategically useful).

### Closing
"Summarize the assets worth preserving and the elements that should change. Ask the user to confirm before moving on."

## Quality Gate

- [ ] **p05_knowledge_verified**: Key concepts verified via KG and/or doc search before applying (brand equity, brand audit, preserve-discard matrix)
- [ ] **p05_inventory**: Brand Inventory completed (visual, verbal, experiential audit)
- [ ] **p05_perception**: Current brand perception assessed (reviews, social, customer voice)
- [ ] **p05_equity**: Brand equity sources identified (what to keep, evolve, discard)
- [ ] **p05_preserve_discard**: Preserve-Discard Matrix completed with user alignment

**BEFORE proceeding**: Call `report_progress(advance=True)` to move to the next phase in sequence.

## Audit Procedure

### Brand Inventory (3 dimensions)
1. **Visual**: Logo, colors, typography, imagery, signage, packaging, uniforms
2. **Verbal**: Name, tagline, tone of voice, key messages, menu descriptions
3. **Experiential**: Service style, ambiance, music, scent, customer journey touchpoints

### Perception Assessment
- Use `deep_research` and `scrape_web_content` to gather customer sentiment from review platforms
- Use `analyze_social_profile` to assess online brand perception
- Use `search_web` for press mentions and third-party reviews

### Preserve-Discard Matrix
| Asset | Recognition | Equity | Action |
|-------|-----------|--------|--------|
| (each asset) | High/Medium/Low | Positive/Neutral/Negative | Keep/Evolve/Discard |
