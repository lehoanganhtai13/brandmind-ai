# C (Strategic Problem-Solving) judge — isolation test results

> Phase B Step 3 kill gate validation, captured here so the evidence is in-repo (gitignored output dirs do not preserve it). For methodology see `problem_solving_test_set/README.md` and `problem_solving_rubric.md`.

## Test execution

- Date: 2026-05-04
- Judge model: `gemini-3.1-pro-preview` thinking_level medium
- Test set: 5 synthetic samples × 10 C-criteria = 50 verdict slots
- Pass threshold: ≥ 80% golden alignment + accurate evidence quotes

## Aggregate result

**PASS — 41 / 50 = 82.0% alignment, +2.0 pp above threshold.**

| Sample | Aligned | Notes |
|---|---|---|
| `solves_burgrr_lunch_office_growth` | 10 / 10 | Perfect — all C1–C10 SOLVES verdicted correctly with explicit constraint + risk + ROI + roadmap + sếp Q&A coverage |
| `solves_traditional_bakery_intergenerational` | 9 / 10 | C8 ROI: judge stricter on cumulative gross 135M < 360M total spend in 12-month window — defendable |
| `does_not_solve_weekday_problem_addressed_with_brand_awareness` | 8 / 10 | All 8 C1/C4/C5-C9 DOES_NOT_SOLVE verdicts caught; C3 / C10 differ on PARTIAL nuance |
| `does_not_solve_constraint_violation_overcommitted` | 9 / 10 | Constraint violation 6.2x over budget caught cleanly on C3; cascade C6/C7/C8/C9 all correct; C10 lenient |
| `partially_solves_addresses_some_problem_components` | 5 / 10 | Hardest sample — judge stricter than my labels on C7 / C8 / C9 (correctly catching "month 1-3 social presence build" is not revenue-quick-win + break-even month 11 falls past 9-month deadline) |

## Misalignment analysis

9 misalignments. Direction split: 6 stricter than expected, 3 lenient than expected.

| Misalignment | Direction | Honest reading |
|---|---|---|
| solves_bakery C8 SOLVES → DOES_NOT_SOLVE | stricter | Judge defendable: 360M spend vs 135M cumulative gross over 12 months means the business is still net-negative at the deadline. My label gave benefit of doubt; judge strict is more defendable. |
| weekday-problem C3 PARTIALLY → DOES_NOT_SOLVE | stricter | Judge defendable: 60M budget fit numerically but channel cadence vague enough to fail constraint feasibility. |
| weekday-problem C10 SOLVES → PARTIALLY | stricter | Judge defendable: domain plausibility weakens when strategy ignores stated weekday F&B reality. |
| constraint-violation C10 PARTIALLY → SOLVES | lenient | Judge gave benefit of doubt on Bảo Lộc + Vietnamese aesthetic — defendable read. |
| partial-solve C2 PARTIALLY → SOLVES | lenient | Judge sees gen-trẻ Q10 channel reach as adequate — defendable. |
| partial-solve C6 PARTIALLY → SOLVES | lenient | Judge sees risk awareness as adequate (interim threshold + pivot trigger) — defendable. |
| partial-solve C7 SOLVES → DOES_NOT_SOLVE | stricter | Judge correct: "month 1-3 social presence build" is not revenue-quick-win for 9-month deadline; my SOLVES label was too lenient. |
| partial-solve C8 SOLVES → DOES_NOT_SOLVE | stricter | Judge correct: ROI math itself states "break-even month 11" — that falls AFTER the 9-month deadline; SOLVES is wrong, judge caught it. |
| partial-solve C9 PARTIALLY → DOES_NOT_SOLVE | stricter | Cascade from C7/C8 — once roadmap and ROI fail the deadline, stakeholder cannot defend. Defendable strict read. |

The most informative finding: judge made 4–5 verdicts that contradict my expected labels but are MORE DEFENDABLE on re-reading the transcript. The partial-solve sample's C7 / C8 are particularly telling — judge correctly diagnosed that my "SOLVES" labels were ungrounded against the explicit "break-even month 11" / "month 1-3 social presence build" evidence in the transcript. This is a positive signal for production use: the judge isn't just matching labeler intent, it makes independent reasonable peer-reviewer calls.

## Evidence accuracy spot-check

Spot-checked the `does_not_solve_constraint_violation_overcommitted` sample (high-stakes for hallucination since DOES_NOT_SOLVE verdicts can be invented when no evidence exists):

| Verdicts checked | Result |
|---|---|
| 10 / 10 | 6 EXACT verbatim matches + 3 composite quotes (parts joined by "...") whose components are each verifiable in the transcript + 1 correct "no evidence in transcript" for C6 risk-absence verdict. Zero hallucinated quotes. |

The composite-quote pattern is a useful judge behavior — when a verdict requires comparing two locations in the transcript (e.g. C8 needs both "stated 25M budget" and "channel mix 155M") the judge stitches them with an ellipsis rather than forging a single sentence.

## Decision

**Kill gate PASS.** C problem-solving judge cleared to apply to real pilot transcripts (Phase D-1 #6 — re-score r10–r13 + r14 fresh pilot post Phase A). No prompt iteration needed; the misalignment pattern reveals judge stricter than my labels in defendable directions, which is desirable for production use.

If real-pilot scoring later reveals systematic bias on a class of criteria, iterate the rubric or the prompt anchoring at that point — do not over-fit to the synthetic labels.

## Reproduction

```bash
source .venv/bin/activate
uv run --env-file environments/.env python evaluation/judge/problem_solving_judge.py \
  --test-set evaluation/judge/problem_solving_test_set/
```

The runner emits the per-criterion alignment table and writes `problem_solving_test_set/isolation_test_report.json` for downstream auditing.
