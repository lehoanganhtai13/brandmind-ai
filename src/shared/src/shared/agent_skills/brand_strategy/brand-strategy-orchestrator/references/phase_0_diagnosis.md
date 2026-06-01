# Phase 0: Business Problem Diagnosis

## Mentor Script

### Opening
"First, understand the user's business context clearly. This is the Brand Problem Diagnosis step: identify the right problem before solving it. In sparse openings, ask one decision-changing question first and collect the rest in later turns."

Do not announce the full workflow, the number of phases, or the raw label "Phase 0" in the opening chat turn. If the situation resembles a known scope, call it a working hypothesis until the user confirms the missing facts.

### Staged Question Bank

Use this as an internal diagnosis bank, not as a user-facing intake form. Choose the smallest question set needed for the next decision; in the opening turn, usually choose one. Do not copy all questions into chat.

1. What kind of F&B business is this? (cafe, restaurant, bar, bakery...)
2. Is this a new brand or an existing brand?
3. What is the primary goal? (launch, refresh, repositioning, full rebrand, expansion...)
4. Which location or market area matters most?
5. What budget range should the strategy and implementation respect?

### Explicit Research Request

If the user explicitly asks for quick market, competitor, or customer research during diagnosis, dispatch one bounded `market-research` pass before presenting market findings. Keep the brief narrow (2-3 targets or signals, query budget, stop condition), then return to the staged diagnosis question bank. Do not present a "market scan" from KG/doc search alone; KG/doc search grounds theory, not current market evidence.

### Concepts to Explain
- **5W1H framework** — comprehensive diagnosis backbone: What (business type), Who (target), Where (market/location), When (timeline), Why (brand-strategy need), How (budget/resources)
- **Scope classification** — why the correct scope matters: new brand vs refresh vs repositioning vs full rebrand changes the entire downstream workflow

### Closing
"Summarize the business context and ask the user to confirm before moving to market intelligence."

## Quality Gate

- [ ] **p0_knowledge_verified**: Decision-grade concepts should be verified via KG and/or doc search when they determine scope, brand architecture, or stakeholder-defensible diagnosis. For simple concept explanations or a sparse opening question, do not block a useful diagnosis reply on source lookup.
- [ ] **p0_problem**: Clear problem statement articulated
- [ ] **p0_scope**: Scope classified (new_brand/refresh/repositioning/full_rebrand)
- [ ] **p0_category**: F&B category and concept understood
- [ ] **p0_location**: Target location/market identified
- [ ] **p0_budget**: Budget tier identified for implementation planning
- [ ] **p0_user_confirm**: User confirms understanding and agrees to proceed

**Internal transition operation**: After the user confirms this diagnosis, set scope and brand through `report_progress(scope="...", brand_name="...")`, then call `report_progress(advance=True)` through the tool interface. Keep the tool name and call syntax out of chat; the user-facing reply should describe only the next business step.

## Special: Rebrand Decision Matrix

If user has an existing brand, proactively run the Rebrand Decision Matrix.
Read `references/rebrand_decision_matrix.md` for the full 6-signal scoring system.
