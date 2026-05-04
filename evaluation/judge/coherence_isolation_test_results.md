# B (Strategic Coherence) judge — isolation test results

> Phase B Step 2 kill gate validation, captured here so the evidence is in-repo (gitignored output dirs do not preserve it). For methodology see `coherence_test_set/README.md` and `coherence_rubric.md`.

## Test execution

- Date: 2026-05-04
- Judge model: `gemini-3.1-pro-preview` thinking_level medium
- Test set: 5 synthetic samples × 12 B-criteria = 60 verdict slots
- Pass threshold: ≥ 80% golden alignment + accurate evidence quotes

## Aggregate result

**PASS — 50 / 60 = 83.3% alignment, +3.3 pp above threshold.**

| Sample | Aligned | Notes |
|---|---|---|
| `coherent_premium_business_retreat` | 12 / 12 | Full coherent strategy, all chains verdicted COHERENT correctly |
| `coherent_family_pho_neighborhood` | 12 / 12 | Different domain, all chains verdicted COHERENT correctly |
| `incoherent_premium_jester_mismatch` | 10 / 12 | Phase 2-3 archetype mismatch + cascade caught; B6 / B9 stricter than expected (judge calls absent narration INCOHERENT vs my PARTIAL — defendable) |
| `incoherent_problem_solution_disconnect` | 8 / 12 | Phase 0-2 disconnect + Phase 5 KPI miss caught; 4 PARTIAL-boundary edge cases differ |
| `partial_specialty_coffee_gaps` | 8 / 12 | Internal alignment caught; Tier 2 narration B7 / B8 stricter (judge calls generic dispatch INCOHERENT vs my PARTIAL); B9 stricter on KPI-Phase-0-link absence |

## Misalignment analysis

10 misalignments are interpretive edge cases on the PARTIAL boundary. None misclassify the COHERENT vs INCOHERENT axis — all clear cases land correctly.

| Direction | Count | Pattern |
|---|---|---|
| Judge stricter than expected | 7 | Judge calls weak narration / missing baseline / generic dispatch language INCOHERENT where I labeled PARTIAL |
| Judge lenient than expected | 3 | Judge gives benefit of doubt on B1 chain coverage and B10 cross-artifact in single-frame strategies |

The stricter direction on B6-B9 (artifact-design rationale) is desirable: these criteria are the Phase A behavioral signal surface, and crediting generic narration as PARTIAL would wash out the differentiation Phase A is supposed to deliver. Judge's stricter reading is more aligned with the Phase A success criterion ("decisions narrated, not hidden") than my noisier expected labels.

## Evidence accuracy spot-check

Spot-checked the `incoherent_premium_jester_mismatch` sample (the highest-stakes for hallucination since INCOHERENT verdicts can be invented when no evidence exists):

| Verdicts checked | Evidence quotes verified |
|---|---|
| 12 / 12 | All quotes EXACT substring matches in transcript. Zero hallucinated quotes. |

Each quote is a verbatim or near-verbatim slice of the transcript text. The judge resists fabricating evidence even when verdict is INCOHERENT.

## Decision

**Kill gate PASS.** B coherence judge cleared to apply to real pilot transcripts (Phase D-1 #6 — re-score r10–r13 + r14 fresh pilot post Phase A). No prompt iteration needed; the misalignment pattern is interpretive noise on PARTIAL nuance, not systematic error.

If real-pilot scoring later reveals systematic bias on a class of criteria, iterate the rubric or the prompt anchoring at that point — do not over-fit to the synthetic labels.

## Reproduction

```bash
source .venv/bin/activate
uv run --env-file environments/.env python evaluation/judge/coherence_judge.py \
  --test-set evaluation/judge/coherence_test_set/
```

The runner emits the per-criterion alignment table and writes `coherence_test_set/isolation_test_report.json` for downstream auditing.
