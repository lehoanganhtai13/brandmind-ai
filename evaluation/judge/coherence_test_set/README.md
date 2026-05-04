# B (Strategic Coherence) judge — synthetic isolation test set

This directory holds the synthetic mini-transcripts and expected verdicts that the B Coherence judge must clear BEFORE being applied to real pilot transcripts. The set is the kill gate for Phase B Step 2 per `eval_methodology_overhaul_plan_2026_05_03.md`: if the judge cannot reliably distinguish coherent from incoherent strategies on samples whose verdicts are constructed by design, it has no business scoring real sessions.

## Why a synthetic set rather than re-using r10–r13

Real pilot transcripts mix coherent and incoherent signals throughout the same session — useful for downstream calibration but useless as a kill gate, because the verdict per criterion is itself a judgment call. The synthetic samples encode the verdict by construction: each sample is built so its expected verdict per criterion is unambiguous when read against the rubric. Judge alignment on this set therefore measures judge prompt quality, not labeler agreement.

This mirrors the discipline used in the chat-rubric Step 4-bis Phase 4 hold-out validation: golden labels created with explicit evidence anchoring, then judge alignment measured vs golden as the truth metric.

## Sample design

Five mini-transcripts, each 8–10 turns covering Phase 0 → Phase 5 + a Phase A artifact-rationale narration step before sub-agent dispatch:

| File | Label | Domain | Why this design |
|---|---|---|---|
| `coherent_premium_business_retreat.json` | COHERENT | premium business retreat F&B Q1 | All B1–B12 chains hold end-to-end with explicit cross-phase reasoning + rich Phase A narration |
| `coherent_family_pho_neighborhood.json` | COHERENT | mid-tier family pho shop refresh | Different domain confirms judge generalizes beyond premium F&B |
| `incoherent_premium_jester_mismatch.json` | INCOHERENT | premium executive cocktail bar with Jester archetype | Phase 2-Phase 3 mismatch cascades — Phase A narration absent |
| `incoherent_problem_solution_disconnect.json` | INCOHERENT | repositioning where strategy ignores Phase 0 problem | Phase 0 specifies weekday slow + competitors; Phase 2 reframes as generic awareness — Phase 5 KPIs do not measure Phase 0 problem |
| `partial_specialty_coffee_gaps.json` | PARTIAL | specialty coffee, internally aligned but missing competition response | Phase 2 addresses 1 of 2 Phase 0 components — internal chain Sage to craft to expertise OK but problem not fully solved |

The two INCOHERENT samples target two distinct failure modes: (1) archetype-positioning mismatch (clear B2 break + cascade) and (2) problem-solution disconnect (clear B1 break + cascade). The PARTIAL sample is internally aligned where present but has gaps that should produce a mix of COHERENT and PARTIAL verdicts — letting us check the judge does not just emit binary verdicts.

## Expected-verdict scoring rule

`expected_verdicts.json` lists the expected verdict per sample per criterion (B1–B12) with reasoning that anchors the verdict to specific evidence in the transcript. Judge alignment is the fraction of judge verdicts that match expected exactly across the 60 verdict slots (5 samples × 12 criteria). PARTIAL is treated as a separate category from COHERENT and INCOHERENT, not a partial credit between them.

Pass gate: ≥ 80% judge-vs-expected alignment + evidence quotes returned by the judge accurately reflect the transcript (no hallucinated quotes). Both must hold; an aligned verdict with a hallucinated evidence quote does not pass.

Failure gate: < 80% alignment OR hallucinated evidence quotes. Diagnose miss pattern in `coherence_judge_isolation_results.md` and revise the judge prompt single-variable per the prompt-engineering iteration workflow before re-running.

## Anti-leakage discipline

Synthetic samples are constructed for this isolation test only — they are not derived from any rubric eval scenario, persona file, or existing pilot transcript. Real pilots will be measured against the same calibrated judge after this gate clears, so the judge has not seen any pilot data when calibration completes. This is the same discipline applied to the chat rubric Step 4-bis hold-out (iso v4 was withheld through Phases 1–3).

## Reproduction

```bash
source .venv/bin/activate
python evaluation/judge/coherence_judge.py --test-set evaluation/judge/coherence_test_set/
```

The runner emits a per-criterion alignment table and the overall percentage. If the percentage clears 80% and evidence quotes are accurate on spot-check, the judge is cleared to apply to r10–r13 + r14 (Phase D-1 #6 and #7).
