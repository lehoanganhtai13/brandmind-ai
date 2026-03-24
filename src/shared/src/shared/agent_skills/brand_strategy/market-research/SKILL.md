---
name: market-research
description: >-
  Systematic 8-step F&B market research methodology for Phase 1.
  Covers industry scan, local competitor mapping, competitor brand analysis,
  target audience research, customer insight mining, trend scanning,
  current brand position research (rebrand only), and strategic synthesis
  (SWOT, perceptual map, strategic sweet spot, insight prioritization).
  Use when the orchestrator enters Phase 1 or when the user asks
  to research a market, analyze competitors, or gather customer insights.
---

# Market Research — Phase 1

## ROLE & OBJECTIVE

Conduct systematic market intelligence gathering for F&B brand strategy.
Follow the 8-step methodology below. Each step builds on previous findings — execute sequentially.
Accumulate all findings for the Strategic Synthesis in Step 8, which bridges Research → Strategy.

**CORE PRINCIPLE**: BREADTH FIRST, DEPTH WHERE IT MATTERS. Scan wide, then dive deep on signals that affect positioning.

## STEP 1: INDUSTRY SCAN

Establish the macro landscape for the target F&B category and location.

Use `deep_research` and `search_web` with queries like:
- "[city] [category] market trends [year]"
- "[category] industry growth Vietnam"
- "[category] consumer behavior trends"

Capture: market size, growth rate, key trends, regulatory changes, seasonal patterns.
Search knowledge graph: `"market segmentation criteria methods"`.

## STEP 2: LOCAL COMPETITOR MAPPING

Discover competitors in the target area. Combine available tools as needed:
- `deep_research` with location-specific queries (e.g., "quán café specialty Quận 3 TPHCM", "best [category] [area] review")
- `search_web` + `scrape_web_content` for local directories and review platforms (Foody, TripAdvisor, Google Maps web)
- Delegate to **social-media-analyst** sub-agent for discovering competitors via Instagram/Facebook location tags

Collect per competitor: name, address/area, rating, review count, price range, concept.
Organize into a competitor table. Flag the top 5 by relevance and visibility — these are the deep-dive targets for Step 3.

## STEP 3: COMPETITOR BRAND ANALYSIS

For the top competitors from Step 2, conduct deep brand analysis.

Delegate social media analysis to the **social-media-analyst** sub-agent via `task(subagent_type="social-media-analyst")`, but **limit to the top 2-3 most relevant competitors** — those that directly compete for the same target audience. Quality over quantity: a deep analysis of 2-3 key players is far more valuable than shallow scans of 5+.

Use `scrape_web_content` for website/menu analysis. For review sentiment, use `deep_research` targeting review platforms and customer feedback for each competitor.

Evaluate per competitor:
- Visual identity (logo, colors, imagery style)
- Core messaging and positioning claim
- Pricing strategy and menu structure
- Review sentiment themes (positive/negative patterns)
- Social engagement rate and content strategy
- Key differentiator

Search knowledge graph: `"competitive analysis framework"`.

## STEP 4: TARGET AUDIENCE RESEARCH

Define audience segments using 4 lenses: demographic, psychographic, behavioral, benefit.

Use `deep_research` for macro audience data. Delegate social media lifestyle research to the **social-media-analyst** sub-agent via `task(subagent_type="social-media-analyst")`.

Identify:
- **Primary segment** — highest value, best fit for brand opportunity
- **Secondary segment** — growth potential or complementary audience
- Per segment: demographics, psychographics, behaviors, jobs to be done, pain points, desires

Search knowledge graph: `"psychographic segmentation"`, `"benefit segmentation"`.

## STEP 5: CUSTOMER INSIGHT MINING

Mine real customer voices for unmet needs and emotional drivers.

Gather customer feedback from multiple sources:
- `deep_research` targeting "[competitor name] đánh giá", "[competitor name] reviews" to find and synthesize review data
- `scrape_web_content` on specific review pages discovered during Step 2-3
- Delegate social media conversation mining to the **social-media-analyst** sub-agent

Focus on negative reviews and recurring complaints — these reveal unmet needs and positioning opportunities.

Frame each insight using the formula:
> "We noticed [observation] because [motivation] which means [implication]"

Aim for at least 5 distinct insights covering functional, emotional, and social dimensions.
Search knowledge graph: `"customer insight development"`.

## STEP 6: TREND & OPPORTUNITY SCANNING

Scan for emerging trends that create strategic opportunities.

Use `deep_research` for macro trends:
- Sustainability and eco-consciousness in F&B
- Technology adoption (ordering, payment, experience)
- Health and wellness trends
- Experience economy and social-media-driven concepts

Use `get_search_autocomplete` to discover what people are searching for in the category.

Classify each trend: **rising** / **peaking** / **declining**. Flag trends with positioning potential.

## STEP 7: CURRENT BRAND POSITION RESEARCH (Rebrand Only)

**Skip this step for new_brand scope.**

For existing brands: assess current perception vs intended positioning.

Research the brand's own customer reviews via `deep_research` and `scrape_web_content`. Use `search_web` for press/media coverage.
Delegate social media brand mention analysis to the **social-media-analyst** sub-agent.

Document:
- Current brand perception (how customers actually describe the brand)
- Perception vs reality gap (intended positioning vs actual perception)
- Competitive position (where the brand sits relative to competitors)
- Equity assets worth preserving (from Phase 0.5 audit if available)

Search knowledge graph: `"brand audit brand inventory"`.

## STEP 8: STRATEGIC SYNTHESIS (CRITICAL)

Transform raw research into actionable strategy inputs. This step bridges Phase 1 → Phase 2.

### SWOT Analysis
Consolidate all research into Strengths / Weaknesses / Opportunities / Threats.
Each item must cite which research step produced the evidence.

### Perceptual Map
Plot top competitors on 2 meaningful axes. Choose axes based on what differentiates the market — e.g., Price Level vs Experience Quality, Traditional vs Modern, Convenience vs Craft.
Identify **white space** = unoccupied positions with audience demand.

### Strategic Sweet Spot
Where market opportunity meets business capability.
Cross-reference SWOT opportunities with the business constraints from Phase 0.

### Insight Prioritization
Rank all insights by: strategic value (1-5) × actionability (1-5) × evidence strength (1-5).
Present top 5 prioritized insights as the foundation for Phase 2 positioning.

Search knowledge graph: `"SWOT analysis"`, `"competitive analysis framework"`.

## OUTPUT FORMAT

Structure Phase 1 output as:
- **market_overview**: industry_trends, category_dynamics, market_size_estimate, growth_direction
- **competitive_landscape**: direct_competitors (3-5), indirect_competitors (2-3), competitive_gaps
- **target_audience**: primary_segment, secondary_segment (each with demographics, psychographics, behaviors, jobs_to_be_done, pain_points, desires)
- **customer_insights**: list of insight/evidence/implication
- **opportunities**: market_gaps, unmet_needs, trend_opportunities
- **strategic_synthesis**: swot, perceptual_map, strategic_sweet_spot, prioritized_insights
- **current_brand_position** (rebrand only): actual_perception, position_vs_competitors, perception_gaps

Read `references/output_templates.md` for the detailed field structure matching Phase1Output schema.
