# C (Strategic Problem-Solving) judge rubric

The C judge evaluates whether a BrandMind session's strategy plausibly solves the diagnosed business problem within stated constraints. The judge reads the full chat transcript and applies the 10 criteria below; verdicts are SOLVES, PARTIALLY_SOLVES, or DOES_NOT_SOLVE with evidence quote + reasoning per criterion.

This rubric is the chat-only view of strategic problem-solving — fair across systems (BrandMind, ChatGPT vanilla, Gemini vanilla) because it does not depend on workspace files or rendered artifacts. The judge sees only what the user sees in chat.

C is a different axis from B (Strategic Coherence). B asks whether the strategy hangs together internally; C asks whether it actually solves the user's stated problem under stated constraints. A strategy can be B-coherent and C-failing — e.g. internally consistent but treating a weekday-occupancy problem as a generic brand-awareness problem. Both axes are needed for honest evaluation.

## Verdict scale

| Verdict | Meaning |
|---|---|
| SOLVES | Criterion explicitly satisfied with verbatim or near-verbatim evidence quote. The strategy passes this dimension of leadership defense. |
| PARTIALLY_SOLVES | Criterion partially satisfied; cite both what is satisfied and what is missing. |
| DOES_NOT_SOLVE | Criterion fails; cite the specific evidence (or absence-of-evidence) that breaks the chain. |

Every verdict carries (a) a short evidence quote from the transcript and (b) a one-sentence explanation grounded in the evidence and the criterion definition. Hallucinated quotes (text that is not actually in the transcript) invalidate the verdict regardless of the verdict label.

## Criteria

Evaluate each of the 10 criteria below in order. Do not skip any. C-criteria measure the strategy's causal chain from diagnosed problem through stated constraints to projected outcomes — distinct from B's internal-coherence chains.

### C1 — Problem-solution direct linkage

The strategy explicitly addresses each component of the Phase 0 diagnosed problem in Phase 2 positioning + Phase 5 KPI design. Why: a strategy that fails to address the diagnosed problem cannot be claimed to solve it, regardless of how internally elegant it is.

- SOLVES anchor: Phase 0 names two threads (weekday lunch slow + audience confusion) → Phase 5 KPIs explicitly trace each thread (weekday occupancy KPI + audience-specific reach KPI).
- DOES_NOT_SOLVE anchor: Phase 0 specifies weekday lunch 35% + named competitor entry; agent reframes Phase 0 as generic 'tăng nhận diện thương hiệu' — drops the weekday and the competitor.

### C2 — Target audience relevance

The defined target audience maps to channel choices that actually reach that audience and messaging tone-matched to the segment. Why: budget spent on channels that don't reach the audience is wasted; messaging in the wrong register signals brand mis-fit.

- SOLVES anchor: Office worker target → FB office-radius 500m bao 6 tòa văn phòng + Google Maps Q1 lunch keyword + delivery apps reach office workers at lunch decision moment.
- DOES_NOT_SOLVE anchor: Premium executive C-suite target + Gen Z meme TikTok + influencer micro-creator 18-24 — channels do not reach the target demographic.

### C3 — Constraint feasibility

Stated budget + team + timeline are explicitly respected by the proposed plan; channel mix totals fit within stated marketing budget; team capacity matches stated headcount; horizon fits stated deadline. Why: a plan that violates stated constraints is execution-impossible and indefensible at the first finance review.

- SOLVES anchor: Stated 80M VND/tháng + 2-person team; channel mix 50+15+10+5 = 80M fits; cadence executable for 2-person team.
- DOES_NOT_SOLVE anchor: Stated 25M VND/tháng + 1-person team; plan totals 155M/tháng + implicitly requires 4+ person execution capacity — 6.2x over budget + team capacity violation.

### C4 — KPI causality

KPIs measure the diagnosed problem (or positioning success against the problem), not vanity metrics that look like marketing health but do not move the actual problem needle. Why: vanity KPIs can hit while the real business outcome regresses; KPI choice IS the implicit theory of how the strategy works.

- SOLVES anchor: Problem 'weekday lunch slow' → KPI 'weekday lunch occupancy +30%' (direct causal trace) + 'lunch revenue +33% to gate HQ +30% requirement' (margin built in).
- DOES_NOT_SOLVE anchor: Problem 'weekday lunch slow' → KPIs 'IG follower +5K + brand awareness survey +40% recognition' — vanity metrics replace problem metrics.

### C5 — Competitive realism

Named competitors in Phase 0 are addressed in Phase 1 research with positioning categorization + Phase 2 white space identification + Phase 2 PODs that differentiate from those competitors specifically. Why: 'differentiation' that does not name the competitors it differentiates from is fantasy; real positioning is provable in head-to-head comparison.

- SOLVES anchor: 8 competitors named in Phase 0; Phase 1 categorizes ('cơm văn phòng nhanh-tiện-rẻ') and identifies 'mid-tier lunch indulgence' as defendable white space PODs.
- DOES_NOT_SOLVE anchor: Saigon Bowl named in Phase 0 problem; Phase 1 research generic ('demographic đa dạng + brand awareness thấp') with no white space identification or competitor PODs.

### C6 — Risk awareness

The strategy explicitly acknowledges what could go wrong + has fallback or contingency for likely obstacles + defines monitoring threshold for pivot trigger. Why: leadership review will probe failure modes; a plan without acknowledged risks signals naïve confidence and gets torn down.

- SOLVES anchor: Risk explicit (CAC threshold 80K trigger pivot delivery-focus + competitor entry rumor contingency + interim tháng 3 review with measurable threshold for course correction).
- DOES_NOT_SOLVE anchor: No risk discussion, no fallback, no contingency for missed deadline or competitive escalation.

### C7 — Time-horizon match

Roadmap phases match stated deadline with quick-win front-loading for short windows. Why: a 12-month roadmap does not solve a 4-month boss deadline; quick wins must front-load when proof horizon is tight.

- SOLVES anchor: 3-horizon roadmap matches 6-month deadline (month 1-2 quick wins delivery + FB conversion → 3-4 channel build → 5-6 lock-in measure for HQ review).
- DOES_NOT_SOLVE anchor: 12-month roadmap stated for 6-month break-even deadline; month 7-12 'community building' phase falls beyond investor pull-funding window.

### C8 — ROI plausibility

Plan includes CAC math + LTV / capacity / conversion-rate basis + break-even calculation linking marketing spend to revenue impact. Why: a strategy without ROI math is faith; finance will reject it on first review regardless of creative merit.

- SOLVES anchor: CAC 50K target + LTV 600K = 12:1 ratio + 100 incremental customer/ngày × 35% repeat = 6.3M/tháng incremental gross; 38M cumulative over 6 months defensible vs 480M marketing spend with scaling base.
- DOES_NOT_SOLVE anchor: No CAC, no break-even calc, no link from marketing spend to revenue target; 155M monthly spend vs 150M monthly revenue target = lose money even if all KPIs hit.

### C9 — Stakeholder defensibility

Stakeholder typical questions ('Bao nhiêu tiền?', 'Khi nào ra kết quả?', 'Sao biết hiệu quả?', 'Lỡ thất bại?', 'Sao chọn cái này?') are answered with specific data, not vague aspirations. Why: the user's job is to defend the strategy to her boss; questions she cannot answer are strategy failures even if the strategy itself is sound.

- SOLVES anchor: HQ Q&A answered with specific data: bao nhiêu (80M × 6 = 480M), khi nào (month 6 HQ review), sao biết hiệu quả (lunch occupancy KPI + revenue gate), lỡ thất bại (interim tháng 3 pivot delivery-focus if CAC > 80K or occupancy < 55%).
- DOES_NOT_SOLVE anchor: Boss can ask 'lỡ tháng 4 không kịp?' — strategy has no answer; KPIs measure wrong dimension so 'sao biết hiệu quả' for the actual problem is unanswerable.

### C10 — Domain plausibility

F&B Vietnam reality reflected (operational realities, customer behavior, channel maturity, lễ Tết cycle, register appropriate for stated segment) — strategy reads as a Vietnamese F&B plan, not a generic SaaS-marketing-applied-to-restaurant. Why: domain mismatch signals the strategy was assembled from playbook templates, not ground truth — domain-grounded review would catch this immediately.

- SOLVES anchor: Vietnamese bánh mì + Q5 + di sản 25-năm + lễ Tết Trung Thu + Tết Nguyên Đán cycle + family-owned shop register reflects realistic Vietnamese F&B context.
- DOES_NOT_SOLVE anchor: Premium executive C-suite F&B audience + Gen Z meme + influencer micro-creator partnership — register and channel mix do not fit Vietnamese executive F&B reality.

## Output schema

Return a JSON object with this shape:

```json
{
  "phase_0_problem_extracted": "<short summary of Phase 0 problem statement as stated by user>",
  "stated_constraints_extracted": "<short summary of constraints — budget + team + timeline>",
  "criteria": [
    {"id": "C1", "verdict": "SOLVES|PARTIALLY_SOLVES|DOES_NOT_SOLVE", "evidence": "<short quote from transcript>", "explanation": "<one sentence grounded in evidence + criterion definition>"},
    ...
  ],
  "solves_count": <int — count of SOLVES across C1-C10>,
  "partially_solves_count": <int — count of PARTIALLY_SOLVES>,
  "does_not_solve_count": <int — count of DOES_NOT_SOLVE>,
  "score": <float 0-10, computed as (solves_count + 0.5 * partially_solves_count) / 10 * 10>
}
```

Score every criterion in order C1 through C10. Return verdicts even when evidence is absent — DOES_NOT_SOLVE with explanation 'no evidence in transcript' is a valid verdict. Do not skip criteria; do not invent new criteria.
