# Phase 4 & Phase 5 Output Templates

## Phase4Output Schema

```yaml
value_proposition:
  one_liner: "Single sentence brand promise"
  elevator_pitch: "30-second version with problem/solution/differentiation"
  full_story: "2-3 paragraph complete narrative"

messaging_hierarchy:
  primary_message: "The headline message"
  supporting_messages:
    - type: "functional"
      message: "What the product delivers"
      proof_points: ["proof 1", "proof 2"]
    - type: "emotional"
      message: "How the customer feels"
      proof_points: ["proof 1", "proof 2"]
  proof_points: ["top-level proof points"]
  tagline_options: ["tagline 1", "tagline 2", "tagline 3"]

audience_messaging:
  - segment: "Primary segment"
    key_message: "Tailored message"
    tone_adjustment: "How voice adjusts"

persuasion_strategy:
  - principle: "social_proof"
    application: "How we apply it"
    message_example: "Join 500+ coffee lovers..."
    f_and_b_example: "Review wall, customer counter"

aida_framework:
  attention: "Eye-catching visual + hook"
  interest: "Story + content that engages"
  desire: "Emotional connection + social proof"
  action: "Clear CTA + accessibility"

channel_strategy:
  channels:
    - channel: "Instagram"
      purpose: "Visual brand building"
      content_types: ["Reels", "Stories", "Carousels"]
      posting_frequency: "5x/week"
      audience_match: "Primary segment alignment"
  content_pillars:
    - pillar: "Product Showcase"
      percentage: 40
      description: "Menu items, preparation"
      example_topics: ["topic 1", "topic 2"]

brand_story:
  origin_story: "The narrative of how the brand was born"
  customer_story_template: "Template for UGC stories"
  narrative_themes: ["theme 1", "theme 2"]
```

## Phase5Output Schema

```yaml
brand_strategy_document:
  format: "pdf"
  file_path: "outputs/brand_strategy.pdf"
  sections: ["Executive Summary", "Business Context", ...]

brand_key_summary:
  visual: "outputs/brand_key.png"
  components:
    root_strength: "Core business strength"
    competitive_environment: "Landscape summary"
    target: "Primary audience"
    insight: "Key customer insight"
    benefits: "Functional + emotional benefits"
    values_and_personality: "Brand traits"
    reasons_to_believe: "Proof points"
    discriminator: "Key POD"
    brand_essence: "Brand mantra/essence"

kpis:
  - category: "awareness"
    metric: "Brand recall rate"
    baseline: "No data"
    target: "30% unaided recall in 6 months"
    measurement_method: "Customer survey"
    review_frequency: "quarterly"

implementation_roadmap:
  budget_tier: "starter"
  quick_wins:
    - action: "Set up social media profiles"
      owner: "Marketing"
      priority: "must_do"
      timeline: "Week 1-2"
  medium_term:
    - action: "Launch content calendar"
      owner: "Marketing"
      priority: "must_do"
      timeline: "Month 2-3"
  long_term:
    - action: "Brand partnership program"
      owner: "Business Development"
      priority: "nice_to_have"
      timeline: "Month 6-12"
  total_estimated_investment: "100-150M VND"
  budget_fit_assessment: "Fits starter tier with prioritization"

measurement_plan:
  kpis: []  # References same KPIs above
  tracking_tools: ["Google Analytics", "Social platform insights"]
  review_cadence: "monthly"
  reporting_format: "Dashboard + monthly report"

transition_plan: null  # Or filled TransitionPlan for rebrand
```
