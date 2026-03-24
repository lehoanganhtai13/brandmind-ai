# Phase 1: Market Intelligence & Research

## Orchestrator Guidance

This phase delegates heavily to the `market-research` sub-skill and `market-research` sub-agent.
Your role as orchestrator: frame the research brief, validate completeness, synthesize findings.

### Mentor Script

#### Opening
"Bây giờ mình cần hiểu thị trường — đối thủ, khách hàng, và xu hướng. Giai đoạn này gọi là 'Market Intelligence'. Giống như trước khi mở quán, bạn phải đi khảo sát khu vực vậy."

#### Key Questions
1. Bạn biết đối thủ trực tiếp nào trong khu vực?
2. Khách hàng mục tiêu của bạn trông như thế nào? (tuổi, lifestyle, thói quen)
3. Có xu hướng nào trong ngành F&B mà bạn thấy đang lên?

### Research Brief Template
Frame research tasks for the sub-agent:
- "Research top 5-7 competitors in [location] for [category]"
- "Analyze customer reviews for [category] in [area]"
- "Research F&B market trends in Vietnam for [year]"
- "Analyze search patterns for [category keywords]"

### Delegation Pattern
1. Delegate competitor profiling to `market-research` sub-agent via `task()` tool
2. Delegate review analysis to `market-research` sub-agent
3. Delegate trend research to `market-research` sub-agent
4. YOU synthesize all sub-agent findings into strategic insights

## Quality Gate

- [ ] **p1_knowledge_verified**: Key concepts verified via KG and/or doc search before applying (STP segmentation, competitor analysis framework, SWOT, customer insight, perceptual map)
- [ ] **p1_competitors**: At least 3 direct competitors profiled
- [ ] **p1_audience**: Target audience defined with psychographic + behavioral data
- [ ] **p1_insights**: At least 3 actionable customer insights identified
- [ ] **p1_swot**: SWOT analysis completed with market data support
- [ ] **p1_perceptual_map**: Competitive perceptual map created with white space identified
- [ ] **p1_synthesis**: Strategic synthesis completed (sweet spot + prioritized insights)

**BEFORE proceeding**: Call `report_progress(advance=True)` to move to the next phase in sequence.
