# Phase 1 Output Templates

## Phase1Output Schema

Structure your Phase 1 output to match this schema exactly.

### market_overview
```yaml
market_overview:
  industry_trends: ["trend 1", "trend 2", ...]
  category_dynamics: "Description of category dynamics"
  market_size_estimate: "e.g., $X billion, growing at Y%"
  growth_direction: "growing | stable | declining"
```

### competitive_landscape
```yaml
competitive_landscape:
  direct_competitors:
    - name: "Competitor A"
      location: "Address"
      category: "e.g., Specialty Coffee"
      rating: 4.5
      review_count: 200
      price_range: "e.g., 50k-120k VND"
      positioning: "Their core positioning claim"
      strengths: ["strength 1", "strength 2"]
      weaknesses: ["weakness 1", "weakness 2"]
      brand_perception: "How customers perceive this brand"
      social_presence: "Summary of social media presence"
      key_differentiator: "What makes them stand out"
  indirect_competitors:
    - name: "Indirect Competitor B"
      # Same fields as direct competitors
  competitive_gaps: ["gap 1", "gap 2"]
```

### target_audience
```yaml
target_audience:
  primary_segment:
    name: "Segment name"
    demographics: "Age, income, occupation, location"
    psychographics: "Values, lifestyle, attitudes"
    behaviors: "Purchase habits, frequency, triggers"
    jobs_to_be_done: ["job 1", "job 2"]
    pain_points: ["pain 1", "pain 2"]
    desires: ["desire 1", "desire 2"]
    size_estimate: "Estimated segment size"
  secondary_segment:
    # Same structure as primary
```

### customer_insights
```yaml
customer_insights:
  - insight: "We noticed [observation]..."
    evidence: "Source/data supporting this"
    implication: "...which means [strategic implication]"
```

### opportunities
```yaml
opportunities:
  market_gaps: ["gap 1", "gap 2"]
  unmet_needs: ["need 1", "need 2"]
  trend_opportunities: ["trend 1", "trend 2"]
```

### strategic_synthesis
```yaml
strategic_synthesis:
  swot:
    strengths: ["S1: ...", "S2: ..."]
    weaknesses: ["W1: ...", "W2: ..."]
    opportunities: ["O1: ...", "O2: ..."]
    threats: ["T1: ...", "T2: ..."]
  perceptual_map:
    x_axis:
      label: "Axis name"
      low_label: "Low end"
      high_label: "High end"
    y_axis:
      label: "Axis name"
      low_label: "Low end"
      high_label: "High end"
    competitors:
      - name: "Competitor A"
        x_score: 7.0
        y_score: 4.0
        notes: "Known for..."
    white_space: "Description of unoccupied positions"
    recommended_position: "Where our brand should target"
  strategic_sweet_spot: "Where opportunity meets capability"
  prioritized_insights:
    - observation: "..."
      motivation: "..."
      implication: "..."
      strategic_value: 5
      actionability: 4
      evidence_strength: 4
  key_strategic_questions:
    - "Question for Phase 2 to resolve"
```

### current_brand_position (Rebrand Only)
```yaml
current_brand_position:
  actual_perception: "How customers describe the brand"
  position_vs_competitors: "Where brand sits vs competition"
  perception_gaps: ["gap 1", "gap 2"]
```
