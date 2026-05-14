# Phase 1: Market Intelligence & Research

## Orchestrator Guidance

This phase builds decision-grade market understanding. Use the `market-research` sub-skill as a methodology reference, but do not delegate by default when the user has already supplied competitor context. Your role as orchestrator: inventory what is already known, decide whether one missing evidence question would change the strategy, validate sufficiency, and synthesize findings.

### Mentor Script

#### Opening
"Now build decision-grade market understanding: competitors, customers, and trends. This is the Market Intelligence step. Explain in the user's language why strategy needs market context before positioning."

#### Key Questions
1. Which direct competitors in the area does the user already know?
2. What does the target customer look like? (age, lifestyle, habits, occasion)
3. Which F&B trends has the user observed as relevant?

### Research Brief Template
Frame bounded research tasks only when the missing evidence would change SWOT, target definition, perceptual map, or the strategic sweet spot:
- "Validate the price tier and target occasion for the top 2 direct competitors in [location]."
- "Check whether review sentiment confirms or contradicts the user's stated customer perception for [category]."
- "Find one current trend that directly affects the positioning choice for [category]."
- "Check search-language signals for [category keywords] only if target-language evidence is missing."

### Delegation Pattern
1. Inventory first-party inputs from the conversation: named competitors, positioning impressions, price ranges, weak spots, customer perceptions, and user constraints.
2. If those inputs are enough for Phase 1 synthesis, do not call `task()`; synthesize directly and name any caveat.
3. If one evidence gap would change the strategy, delegate one bounded `market-research` pass with the exact question and stop condition.
4. YOU synthesize conversation evidence, KG/doc frameworks, and any specialist findings into strategic insights.

## Quality Gate

- [ ] **p1_knowledge_verified**: Key concepts verified via KG and/or doc search before applying (STP segmentation, competitor analysis framework, SWOT, customer insight, perceptual map)
- [ ] **p1_competitors**: At least 3 direct competitors profiled
- [ ] **p1_audience**: Target audience defined with psychographic + behavioral data
- [ ] **p1_insights**: At least 3 actionable customer insights identified
- [ ] **p1_swot**: SWOT analysis completed with market data support
- [ ] **p1_perceptual_map**: Competitive perceptual map created with white space identified
- [ ] **p1_synthesis**: Strategic synthesis completed (sweet spot + prioritized insights)

**BEFORE proceeding**: Call `report_progress(advance=True)` to move to the next phase in sequence.
