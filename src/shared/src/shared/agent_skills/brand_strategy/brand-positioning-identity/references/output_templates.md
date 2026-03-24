# Phase 2 & Phase 3 Output Templates

## Phase2Output Schema

```yaml
competitive_frame:
  category: "e.g., Specialty Coffee Shop"
  competitive_set: ["Competitor A", "Competitor B"]
  category_associations: ["quality", "craftsmanship"]

positioning:
  points_of_parity:
    - type: "category"
      description: "Fresh, quality coffee"
      evidence: "Standard expectation in specialty segment"
    - type: "competitive"
      description: "Comfortable seating"
      evidence: "Neutralizes Competitor A's advantage"
  points_of_difference:
    - description: "Single-origin sourcing with farm stories"
      desirable: true
      deliverable: true
      differentiating: true
      evidence: "No competitor tells origin stories"
  positioning_statement: "For [target] who [need], [brand] is..."
  positioning_rationale: "Why this position works"

value_architecture:
  attributes: ["Single-origin beans", "Pour-over brewing"]
  functional_benefits: ["Rich, complex flavor profiles"]
  emotional_benefits: ["Feeling of discovery and sophistication"]
  customer_outcomes: ["A daily ritual of mindful self-reward"]
  reasons_to_believe: ["Direct farm partnerships", "Barista certifications"]

brand_essence:
  core_idea: "1-2 sentence brand soul"
  brand_promise: "What the brand commits to"
  brand_mantra: "3-5 word mantra"

strategic_alignment:
  problem_addressed: "Links to Phase 0 business problem"
  insight_leveraged: "Links to Phase 1 customer insight"
  differentiation_logic: "Why this creates competitive advantage"

product_brand_alignment:
  product_truth: "What product objectively delivers"
  menu_positioning_fit: "Menu reinforces/contradicts positioning"
  pricing_positioning_fit: "Price matches positioning tier"
  service_brand_fit: "Service style embodies personality"
  gap_actions: ["Action for gap 1"]

positioning_stress_test:
  competitive_vacancy: true
  deliverability: true
  relevance: true
  defensibility: true
  budget_feasibility: true
  notes:
    competitive_vacancy: "No competitor owns this position"
    deliverability: "Product truth supports claim"
  overall_verdict: "PASS — all 5 criteria met"
```

## Phase3Output Schema

```yaml
brand_personality:
  archetype: "e.g., Explorer"
  traits: ["Curious", "Authentic", "Warm"]
  trait_descriptors:
    - trait: "Curious"
      means: "Always exploring new origins and brewing methods"
      does_not_mean: "Pretentious or exclusionary"
  brand_character: "1-paragraph character description"

brand_voice:
  tone_spectrum:
    formal_casual: 3
    playful_serious: 6
    bold_understated: 4
    technical_accessible: 5
  voice_principles: ["Lead with story", "Invite, don't lecture"]
  voice_examples:
    - do: "Discover the story behind your cup"
      dont: "Our premium beans are sourced from..."

visual_identity:
  color_palette:
    primary: "#2C1810 (deep espresso brown)"
    secondary: "#F5E6D3 (warm cream)"
    accent: "#D4A574 (caramel gold)"
    rationale: "Earthy tones evoke craft and warmth"
  typography_direction: "Modern serif for headlines, clean sans for body"
  imagery_style: "Documentary-style photography, warm tones"
  logo_direction: "Wordmark with subtle bean motif"
  mood_board_images: ["path/to/image1.png"]

distinctive_brand_assets:
  priority_assets: ["Espresso brown color", "Bean motif", "Tagline"]
  asset_strategy: "Build color recognition first, then symbol"

sensory_identity:
  taste_profile: "Bold, complex, single-origin focused"
  aroma_signature: "Fresh-roasted coffee with subtle vanilla"
  ambient_experience: "Warm lighting, acoustic music, wood textures"
  packaging_tactile: "Matte kraft paper with embossed logo"

brand_naming:
  naming_approach: "suggestive"
  selected_name: "Brand Name"
  selection_rationale: "Why this name was chosen"
  skipped: false

identity_transition: null  # or filled for rebrand scopes
```
