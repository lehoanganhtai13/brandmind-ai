# Phase 5: Strategy Plan & Deliverables

## Orchestrator Guidance

This phase continues with the `brand-communication-planning` sub-skill.
Document assembly delegates to `document-generator` sub-agent.

### Mentor Script

#### Opening
"Giai đoạn cuối — tổng hợp tất cả thành deliverables chuyên nghiệp. Mình sẽ tạo: Brand Strategy Document (PDF/DOCX), Pitch Deck (PPTX), Brand Key one-pager, KPI dashboard, và Implementation Roadmap."

#### Concepts to Explain
- **Brand Key Model** — one-pager tóm tắt toàn bộ brand strategy: Root Strength, Competitive Environment, Target, Insight, Benefits, Values, Reasons to Believe, Discriminator, Brand Essence
- **KPI Framework** — đo lường brand strategy bằng metrics cụ thể: awareness, consideration, preference, loyalty, advocacy
- **Implementation Roadmap** — 3 time horizons: Quick Wins (0-3 months), Foundation Building (3-6 months), Scale & Optimize (6-12 months)

### Delegation Pattern
1. YOU compile the Brand Brief with all phase outputs
2. Delegate Brand Key visual to `creative-studio` sub-agent
3. Delegate PDF/DOCX document to `document-generator` sub-agent
4. Delegate PPTX pitch deck to `document-generator` sub-agent
5. YOU present deliverables to user with summary

### Roadmap Structure (budget-tier aware)
**Quick Wins (Month 1-3)**:
- Brand name registration
- Logo and visual identity finalization
- Social media profile setup
- Basic collateral (business cards, menu)

**Foundation Building (Month 3-6)**:
- Website launch
- Content calendar execution
- Initial marketing campaigns
- Staff brand training

**Scale & Optimize (Month 6-12)**:
- Performance review and optimization
- Advanced marketing channels
- Partnership and collaboration
- Brand experience refinement

## Quality Gate

- [ ] **p5_knowledge_verified**: Key concepts verified via KG and/or doc search before applying (Brand Key model, KPI metrics, implementation roadmap, brand measurement)
- [ ] **p5_document**: Complete brand strategy document generated (PDF/DOCX)
- [ ] **p5_brand_key**: Brand Key one-pager included
- [ ] **p5_kpis**: At least 5 KPIs defined with baselines and targets
- [ ] **p5_roadmap**: Implementation roadmap with 3 time horizons, tied to budget_tier
- [ ] **p5_roadmap_priority**: Each roadmap item categorized Must Do / Nice to Have
- [ ] **p5_measurement**: Measurement plan with review cadence
- [ ] **p5_transition**: [Rebrand only] Transition & change management plan completed
- [ ] **p5_stakeholder**: [Rebrand only] Stakeholder communication plan defined

**On completion**: Call `report_progress(advance=True)` to mark strategy as complete.
