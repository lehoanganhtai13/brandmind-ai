# C (Strategic Problem-Solving) judge — synthetic isolation test set

This directory holds the synthetic mini-transcripts and expected verdicts that the C Problem-Solving judge must clear BEFORE being applied to real pilot transcripts. The set is the kill gate for Phase B Step 3 per `eval_methodology_overhaul_plan_2026_05_03.md`: if the judge cannot reliably distinguish strategies that solve the diagnosed problem from strategies that do not, it has no business scoring real sessions.

## Why a separate set from the B coherence test

B and C measure different axes:

- **B Coherence** asks: does the strategy hang together as an integrated thing across phases? (Internal consistency.)
- **C Problem-Solving** asks: does the strategy plausibly solve the diagnosed business problem within stated constraints? (Causality + feasibility.)

A strategy can be B-coherent yet C-failing — e.g. positioning + identity + communication all align internally, but the strategy treats a weekday-occupancy problem as a brand-awareness problem (see `does_not_solve_weekday_problem_addressed_with_brand_awareness.json`). Reusing B samples would not adequately test 4 C-criteria that B does not cover (C3 Constraint feasibility, C6 Risk awareness, C7 Time-horizon match, C8 ROI plausibility), so this set is built fresh with explicit constraint statements + risk discussion + ROI math + time-phased roadmaps.

## Sample design

Five mini-transcripts, each 7–9 turns covering Phase 0 → Phase 5 with explicit Phase 0 constraint declarations + later-phase risk acknowledgement and ROI math:

| File | Label | Domain | Why this design |
|---|---|---|---|
| `solves_burgrr_lunch_office_growth.json` | SOLVES | fast-casual burger chain repositioning Q1 | All C1–C10 satisfied: Phase 5 KPIs trace HQ +30% gate, 80M budget split fits, CAC + LTV math, time-phased to 6-month deadline, sếp Q&A answered |
| `solves_traditional_bakery_intergenerational.json` | SOLVES | family bakery refresh Q5 | Different domain confirms generalization; key C-test is risk awareness (alienate core 40+ customers — physical store unchanged + interim survey mitigation) |
| `does_not_solve_weekday_problem_addressed_with_brand_awareness.json` | DOES_NOT_SOLVE | restaurant repositioning Q3 | Phase 0 specific (weekday lunch 35% + Saigon Bowl entry 150m + 4-month deadline) reframed as generic brand awareness — fails C1 / C4 / C7 / C8 / C9 cleanly |
| `does_not_solve_constraint_violation_overcommitted.json` | DOES_NOT_SOLVE | trà sữa craft launch Q1 | 25M budget + 1-person team stated; plan ~155M/tháng + 4+ person execution = 6.2x over — fails C3 cleanly + C6 / C7 / C8 / C9 cascade |
| `partially_solves_addresses_some_problem_components.json` | PARTIALLY_SOLVES | phở refresh Q10 | Strategy addresses 2 of 3 problem threads (brand identity + competition) cleanly but misses weekday-specific dimension — C1 / C2 / C4 / C9 PARTIAL while C3 / C5 / C6 / C7 / C8 / C10 SOLVES |

The two DOES_NOT_SOLVE samples target distinct failure modes: (1) problem-solution disconnect (strategy ignores the diagnosed problem) and (2) constraint violation (strategy beautifully designed but execution-impossible at stated budget / team). The PARTIALLY_SOLVES sample is internally well-designed where present but has a gap on one problem thread — letting us check the judge produces a mix of SOLVES and PARTIALLY_SOLVES verdicts rather than collapsing to a binary.

## Expected-verdict scoring rule

`expected_verdicts.json` lists the expected verdict per sample per criterion (C1–C10) with reasoning that anchors the verdict to specific evidence in the transcript. Judge alignment is the fraction of judge verdicts that match expected exactly across the 50 verdict slots (5 samples × 10 criteria). PARTIALLY_SOLVES is treated as a separate category from SOLVES and DOES_NOT_SOLVE, not a partial credit between them.

Pass gate: ≥ 80% judge-vs-expected alignment + evidence quotes returned by the judge accurately reflect the transcript (no hallucinated quotes). Both must hold; an aligned verdict with a hallucinated evidence quote does not pass.

Failure gate: < 80% alignment OR hallucinated evidence quotes. Diagnose miss pattern in `coherence_isolation_test_results.md`-style results doc and revise the judge prompt single-variable per the prompt-engineering iteration workflow before re-running.

## Anti-leakage discipline

Synthetic samples are constructed for this isolation test only — they are not derived from any rubric eval scenario, persona file, existing pilot transcript, or B coherence test set. Real pilots will be measured against the same calibrated judge after this gate clears, so the judge has not seen any pilot data when calibration completes. This mirrors the discipline applied to the chat rubric Step 4-bis hold-out validation and the B coherence isolation test.

## Reproduction

```bash
source .venv/bin/activate
uv run --env-file environments/.env python evaluation/judge/problem_solving_judge.py \
  --test-set evaluation/judge/problem_solving_test_set/
```

The runner emits a per-criterion alignment table and the overall percentage. If the percentage clears 80% and evidence quotes are accurate on spot-check, the judge is cleared to apply to r10–r13 + r14 (Phase D-1 #6 and #7).
