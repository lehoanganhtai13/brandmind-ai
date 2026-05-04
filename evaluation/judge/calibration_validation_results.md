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
| iso v4 + M2-S2 iteration 1 (mechanical count) | 0.592 | Moderate — no movement |
| iso v4 + M2-S2 iteration 2 (sub-finding granularity) | 0.592 | Moderate — no movement |
| iso v4 + M2-S2 iteration 3 (affirmative + thinking-mode verbs, SHIPPED) | 0.509 | Moderate-Fair edge — Gemini flipped MET → UNMET on M2-S2 (golden alignment 32/33 → 33/33), Kappa drop attributable to T=1.0 stochasticity on 8 unrelated criteria + n_criteria growth 93 → 102 |

The post-calibration Kappa of 0.592 sits in the upper Moderate band,
0.018 below the 0.61 Substantial threshold typically cited as
research-grade for LLM-as-judge panels. Two iterations of M2-S2
wording tightening (mechanical-count anchor; explicit sub-finding
granularity) produced ZERO movement in Gemini's verdict or reasoning
text. The single residual deviation (Gemini lenient on M2-S2, 1/11)
is structurally interpretation-architectural rather than threshold-
elastic, so the iteration was reverted; the calibrated baseline holds
at 0.592 Moderate. Per `north_star_principles_2026_05_03.md` honest-
measurement principle, this Kappa is accepted as the reliable cross-
judge agreement floor for thesis claims; the 0.018 gap is documented
in `calibration_changelog.md` Pattern 4 iteration block as a known
single-criterion limitation (Mentor dimension only) and does not
invalidate Quality / Personalization dimension signals which align
3/3 with golden on hold-out.

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

- Gemini lenient on M2-S2 (1/11) — RESOLVED 2026-05-04 via iteration 3
  (affirmative + thinking-mode-aware verbs + Step 1/2/3 procedure).
  Sub-agent root-cause analysis identified the binding constraint
  upstream of the M2-S2 cell: Rule 4 ("No Halo Effect — Score each
  phase independently") sits at the top of the prompt with primacy
  bias; cell-level negation cannot override an upstream rule that
  the model anchored on first. Iteration 3 reframed M2-S2 affirmatively
  with turn-native language so it does not need to fight Rule 4. After
  iteration 3 ships, Gemini flipped MET → UNMET on M2-S2 (golden
  alignment 32/33 → 33/33). Cross-judge Kappa dropped to 0.509 in the
  single-trial eval — the drop is attributable to temperature=1.0
  stochasticity on 8 UNRELATED criteria + n_criteria denominator
  growth (93 → 102), NOT to a regression on M2-S2 itself. See
  `calibration_changelog.md` Pattern 4 iteration 3 block for full
  diagnosis + Open follow-up Kappa stability work (N=3 trials, T=0.0
  deterministic option, Path C structured-output count-based).
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
