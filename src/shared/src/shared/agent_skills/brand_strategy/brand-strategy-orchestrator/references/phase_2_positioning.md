# Phase 2: Brand Strategy Core

## Orchestrator Guidance

This phase delegates to the `brand-positioning-identity` sub-skill.
Your role: ensure positioning is grounded in Phase 1 research, stress test the result.

### Mentor Script

#### Opening
"This is the Brand Positioning step. Use the Phase 1 insights to find the strategic sweet spot: where the brand is meaningfully different, relevant to the customer, and deliverable by the business."

#### Concepts to Explain
- **Positioning** — the intended place the brand occupies in the customer's mind; not only what the brand says, but what customers believe it stands for.
- **POPs/PODs** — Points of Parity (what the brand must have to compete) versus Points of Difference (what makes it meaningfully distinctive).
- **Value Ladder** — product attributes -> functional benefits -> emotional benefits -> final customer outcome.
- **Brand Essence** — 3-5 words that summarize the brand's core meaning.

### Stress Test (5 Criteria)
After positioning is drafted, stress test against — these match the `StressTestResult` Pydantic schema in `core.brand_strategy.analysis.positioning` and the canonical list in the `brand-positioning-identity` SKILL.md:
1. **Competitive vacancy**: no competitor currently owns this position.
2. **Deliverability**: the product truth supports the claim — the kitchen, service, and space can actually live up to it.
3. **Relevance**: the target audience cares about this position; it answers a real customer need.
4. **Defensibility**: the position can be sustained over time — operations, story, and assets reinforce it rather than make it copyable.
5. **Budget feasibility**: the position is communicable within the stated budget tier.

If any criterion fails -> PROACTIVE LOOP TRIGGER fires (see orchestrator: Deliverability fail → Phase 0; Relevance fail → Phase 1).

## Quality Gate

- [ ] **p2_knowledge_verified**: Key concepts verified via KG and/or doc search before applying (positioning statement, POPs/PODs, value ladder, brand essence, stress test criteria)
- [ ] **p2_positioning**: Positioning statement complete (target, frame, POD, RTB)
- [ ] **p2_pops_pods**: Points of Parity and Difference defined
- [ ] **p2_value_ladder**: Value ladder built (attributes -> functional -> emotional -> outcome)
- [ ] **p2_essence**: Brand essence / mantra articulated
- [ ] **p2_product_alignment**: Product-brand alignment checked (menu, pricing, service fit)
- [ ] **p2_stress_test**: Positioning stress test passed (5 criteria)

**Internal transition operation**: After the user confirms the positioning decision, call `report_progress(advance=True)` through the tool interface. Keep the tool name and call syntax out of chat; the user-facing reply should describe only the next business step.
