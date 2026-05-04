# Judge Calibration Validation Results

> **Snapshot of Phase 4 hold-out validation, captured here so the data is
> in-repo (gitignored ``brandmind-output/eval/`` does not preserve it
> across rebuilds). For methodology and procedure see
> `docs/JUDGE_CALIBRATION_METHODOLOGY.md`.**

## Hold-out transcript

`brandmind-output/eval/brandmind_linh_phase_a_iso_v4_20260504_0246/`

This 10-turn Linh repositioning pilot was driven on 2026-05-04 with all
four sub-plans active (PDF font fallback `f6b7ad6`, browser-use Keychain
bypass `02277c2`, content-check additive-delta rejection `e2cd56f`,
stop-check finish-reason-agnostic detection `cd1771c`) plus the Phase A
v1 CORE PHILOSOPHY bullet (`8b8e45a`). Tier 1 = 4/4 artifacts produced;
no silent dispatch; no duplicate-pass at closure-turn.

The transcript was held back during Phase 1–3 of calibration: it never
informed golden-label authoring, deviation analysis, or prompt
adjustment. Phase 4 ran the calibrated 3-judge eval against the
hold-out and compared verdicts vs the golden hold-out labels.

## Per-criterion verdict table (post-calibration vs golden)

| Criterion | golden | claude-sonnet-4.6 | gemini-3.1-pro-preview | gpt-5.4 |
|-----------|--------|--------------------|------------------------|---------|
| M2-E1 | UNMET | UNMET ✓ | UNMET ✓ | UNMET ✓ |
| M2-S2 | UNMET | UNMET ✓ | MET ✗ | UNMET ✓ |
| P2-S2 | UNMET | UNMET ✓ | UNMET ✓ | UNMET ✓ |
| P3-E1 | UNMET | UNMET ✓ | UNMET ✓ | UNMET ✓ |
| P3-S3 | UNMET | UNMET ✓ | UNMET ✓ | UNMET ✓ |
| P4-E2 | UNMET | UNMET ✓ | UNMET ✓ | UNMET ✓ |
| P4-S3 | UNMET | UNMET ✓ | UNMET ✓ | UNMET ✓ |
| P4-S4 | UNMET | UNMET ✓ | UNMET ✓ | UNMET ✓ |
| Q1-S4 | MET | MET ✓ | MET ✓ | MET ✓ |
| Q3-S3 | MET | MET ✓ | MET ✓ | MET ✓ |
| Q4-E2 | UNMET | UNMET ✓ | UNMET ✓ | UNMET ✓ |

**Total alignment with golden on hold-out**: 32/33 verdicts agree.

## Alignment summary

| Judge | Pre-calibration alignment (training) | Post-calibration alignment (hold-out) | Improvement |
|-------|--------------------------------------|---------------------------------------|-------------|
| claude-sonnet-4.6 | 75.8% (25/33) | 100% (11/11) | +24.2 pp |
| gemini-3.1-pro-preview | 51.5% (17/33) | 90.9% (10/11) | +39.4 pp |
| gpt-5.4 | 66.7% (22/33) | 100% (11/11) | +33.3 pp |

## Cross-judge Kappa progression (Fleiss' Kappa, Landis & Koch interpretation)

| Stage | Kappa | Interpretation |
|-------|-------|----------------|
| r1 baseline (Apr 2026) | 0.168 | Slight |
| r1 with batched pipeline | 0.443 | Moderate |
| r12 pre-anchoring | 0.351 | Fair |
| r12 post-failed-anchoring | 0.319 | Fair (slight regression — failed Step 4) |
| **iso v4 hold-out post-calibration** | **0.592** | **Moderate** |

The post-calibration Kappa of 0.592 sits in the upper Moderate band,
0.018 below the 0.61 Substantial threshold typically cited as
research-grade for LLM-as-judge panels. The single residual deviation
(Gemini lenient on M2-S2, 1/11) is what holds the Kappa below
Substantial; Phase 3 iteration targeting M2-S2 specifically is the
recommended next step if research-grade Kappa is required.

## Hold-out per-judge dimension scores (post-calibration honest reading)

| Judge | Overall | Quality | Mentor | Personalization |
|-------|---------|---------|--------|-----------------|
| claude-sonnet-4.6 | 4.89 | 2.57 | 6.33 | 8.53 |
| gemini-3.1-pro-preview | 5.47 | 4.52 | 6.17 | 6.78 |
| gpt-5.4 | 1.47 | 1.48 | 1.75 | 1.0 |

GPT 5.4's low post-calibration scores reflect its strict reading after
calibration removed the prior lenience on Personalization criteria. The
lower aggregate average is the "reduce overrating, make averages
honest" outcome originally targeted by Step 4 design — calibration
delivered the variance reduction Step 4 sought without anchoring's
failure mode.

## Anti-discipline checks held during calibration

- Hold-out transcript not used during Phase 1, 2, or 3 — no answer-key
  leakage.
- Generalization signal real: 90–100% alignment on an unseen transcript
  not informed by prompt adjustment evidence.
- Single-variable per pattern: 5 deviation patterns received exactly
  one logical adjustment each; no bundling, traceable to Phase 2
  evidence.
- Cross-system fairness preserved: same calibrated rubric applies to
  BrandMind and to vanilla baseline judging chains.

## Residual + open work

- Gemini lenient on M2-S2 (1/11). Recommended Phase 3 iteration:
  tighten the M2-S2 wording so single-turn formatted long content does
  not satisfy "incremental" even when visually segmented. Expected
  effect: Gemini flips M2-S2 to UNMET on hold-out, alignment becomes
  11/11 across all three judges, cross-judge Kappa crosses 0.61
  Substantial threshold.
- Sub-agent labeler used paraphrase rather than verbatim evidence
  quotes. Verdicts are sound (keyword spot-check + reasoning audit
  confirmed); future iteration should re-label with strict verbatim
  discipline.
- Single-labeler golden may carry latent bias. Mitigation: every label
  carries evidence + reasoning so anh có thể audit any time, and
  cross-transcript consistency was verified during labeling.

## Reproduction commands

```bash
source .venv/bin/activate
# Re-derive deviation report from golden labels + cached eval results:
python evaluation/judge/calibrate_deviation.py
# Re-run 3-judge eval on hold-out with calibrated prompt:
python evaluation/judge/run_judges.py \
  --session-dir brandmind-output/eval/brandmind_linh_phase_a_iso_v4_20260504_0246/
```
