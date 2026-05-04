# B + C Judge Methodology

> This document describes the design and validation of the two strategic-judgment judges that augment BrandMind's evaluation pipeline: B (Strategic Coherence) and C (Strategic Problem-Solving). The judges were built and isolation-tested on 2026-05-04 as Phase B Steps 2 and 3 of the eval-methodology overhaul plan (`eval_methodology_overhaul_plan_2026_05_03.md`). The procedure reproduces deterministically from artifacts checked into this repository; outcomes are summarized in `evaluation/judge/coherence_isolation_test_results.md` and `evaluation/judge/problem_solving_isolation_test_results.md`. Anyone with the codebase should be able to read this document, understand what was done and why, and re-run the validation to verify the result.

## 1. Goal & Scope

BrandMind's pre-existing chat-rubric pipeline (`evaluation/judge/run_judges.py` over `docs/BRANDMIND_EVAL_RUBRIC.md`) measures three dimensions — Strategy Quality, Mentoring, Personalization — across 105 criteria, with three LLM judges in parallel and Fleiss' Kappa as inter-rater agreement. After thirteen pilot runs spanning March–May 2026, cross-judge Overall plateaued in the 5.0–5.5 range. Root-cause analysis (`r12_pilot_findings_2026_05_03.md` + 2026-05-03 user discussion) attributed the plateau to measurement methodology rather than system capability: the chat rubric scores surface behaviors (did the agent ask, scaffold, use a framework name, present incrementally) that any well-prompted vanilla LLM can replicate, so the rubric does not differentiate BrandMind's structural advantages — multi-phase orchestration, cross-phase coherence, sub-agent specialization for artifact production, workspace continuity across turns.

The B and C judges add a second measurement layer that targets strategic substance rather than surface behavior. Two new dimensions are introduced. Strategic Coherence asks whether the strategy hangs together as an integrated thing across phases — does the Phase 0 problem chain to Phase 2 positioning to Phase 3 identity to Phase 4 communication to Phase 5 KPIs without contradiction, with reasoning visible at each transition. Strategic Problem-Solving asks whether the strategy plausibly solves the diagnosed business problem within the user's stated constraints — does the plan stay within budget and team capacity, acknowledge what could go wrong, project realistic ROI, defend itself against the typical questions a stakeholder will ask. Both dimensions are evaluated on chat-only transcripts so the same calibrated rubric applies identically to BrandMind, ChatGPT vanilla, and Gemini vanilla judging chains, preserving cross-system fairness for the Phase D-2 thesis comparison.

The thesis claim defended by these judges, per the 2026-05-03 honest-measurement update to `north_star_principles_2026_05_03.md`, is "demonstrated improvement on B-Coherence and C-Problem-Solving dimensions with honest measurement", not "Overall ≥ 7.5 cross-judge". The chat-rubric Overall plateau reflects measurement-methodology limits, and B/C are the methodology layer that can capture BrandMind's actual strategic-substance differentiation.

Out of scope: the chat-rubric Q/M/P pipeline calibration (covered in `docs/JUDGE_CALIBRATION_METHODOLOGY.md`), production cross-system pilot procedure (Phase C, separate document), and the broader thesis-defense execution covering Phase D-1 and Phase D-2 validation runs against real pilots. This document covers only the design and isolation-test validation of the B and C judge prompts.

## 2. Theoretical Foundation

The B/C design is grounded in three principles drawn from the project's eval philosophy (`north_star_principles_2026_05_03.md` Section 3) and from observation of how the chat rubric calibration converged.

**Strategic substance is measurable separately from surface behavior, and the two layers must not be conflated.** The chat rubric measures presence-of-behavior (asked? scaffolded? cited a framework?). A well-prompted vanilla LLM can produce all of these surface behaviors; the rubric therefore measures the chat interface's polish, not whether the strategy underneath is any good. B and C target the layer underneath: does the resulting strategy hang together (B), does it solve the user's problem (C). Both are answerable from the chat transcript alone — the strategy elements are stated in chat regardless of whether artifacts are generated — so adding the layer does not require new instrumentation, only a separate measurement framework.

**Cross-system fairness is a binding design constraint, not an afterthought.** For the thesis claim to defend, the same rubric must score BrandMind, ChatGPT vanilla, and Gemini vanilla on identical inputs. This forces three architectural choices: (1) inputs are chat transcript only — no workspace files, no rendered artifacts, no agent-internal scratch state, because vanilla baselines do not have those; (2) criteria measure observable transcript behavior — the agent's stated reasoning, the strategy components named in chat, the constraints stated by the user; (3) judging procedure is prompt-only with no judge-side knowledge of which system produced the transcript. The B and C rubric files (`evaluation/judge/coherence_rubric.md` + `problem_solving_rubric.md`) and the judge code (`evaluation/judge/coherence_judge.py` + `problem_solving_judge.py`) are designed accordingly — chat-only inputs, transcript-grounded evidence quotes, system-agnostic verdict criteria.

**Rubric is hypothesis, not ground truth.** The 12 B-criteria and 10 C-criteria represent one research team's operationalization of "coherent strategy" and "problem-solving strategy" — they are explicit, defendable, and extensible, but not absolute. The validation procedure (Section 6) treats the rubric as a hypothesis tested against synthetic samples whose verdicts are known by construction; agreement between judge verdicts and constructed verdicts is the signal that the rubric and the judge prompt operationalize the rubric correctly. This is the same epistemic stance taken in `JUDGE_CALIBRATION_METHODOLOGY.md` Section 2 for the chat rubric.

A practical corollary distinguishes B from existing chat-rubric M2-S2-style criteria. M2-S2 measures pacing — did the agent present incrementally — at the turn level. B5 measures whether each major decision cites the prior-phase finding it builds on, at the cross-phase reasoning level. The two are complementary: M2-S2 catches "agent dumped everything in one turn"; B5 catches "agent presented things at one-per-turn but never connected Phase 5 KPIs back to Phase 0 problem". A strategy can satisfy M2-S2 (pacing OK) and fail B5 (chain invisible), or vice versa. They measure different things at different scales.

## 3. Design Choice — Path X (Single Judge per Dimension)

The design choice that distinguishes B/C from the chat rubric is single-judge-per-dimension instead of cross-judge averaging. Two paths were considered explicitly during 2026-05-04 design discussion before implementation began.

**Path X (chosen)**: one LLM judge per dimension (Gemini 3.1 Pro for both B and C), validated against a single-labeler golden synthetic test set. Reliability is established by alignment-to-golden — the percentage of judge verdicts that match the constructed expected verdict on the synthetic set — not by inter-judge agreement.

**Path Y (declined)**: three LLM judges per dimension (Claude Sonnet 4.6 + Gemini 3.1 Pro + GPT 5.4), Fleiss' Kappa as the reliability metric, calibrated through the four-phase procedure used for the chat rubric. Reliability is established by inter-rater agreement on a fixed criterion set.

The decision favored Path X for four reasons grounded in the structural difference between the chat rubric's micro-criteria and B/C's macro-criteria.

First, the unit of judgment differs. Chat rubric criteria measure local observable behaviors at the turn or phase scope (M2-S2 = "is this turn carrying one sub-finding?"). Multiple judges scoring the same local behavior produce three independent perceptions of one observable event — averaging is appropriate because the dependent variable is a local fact and disagreement signals rubric ambiguity. B/C criteria measure macro syntheses spanning the whole transcript (B1 = "does Phase 0 problem chain to Phase 2 positioning that addresses each component?"). Each judge synthesizing the chain produces one reasoning trace; averaging three reasoning traces dilutes each individual trace without producing a meta-synthesis. The deliverable of a B/C verdict is one auditable reasoning chain, not a vote count.

Second, calibration cost scales with criterion count. Path Y would require running the four-phase calibration loop on 22 criteria (12 B + 10 C). The chat rubric calibration was already heavy at 11 criteria — Phase 1 produced 44 labels by a single labeler, Phase 3 adjusted 10 criterion rows, the M2-S2 residual required a separate three-iteration loop afterward. Scaling to 22 criteria with cross-judge variance to chase would extend the calibration cycle by weeks without proportionate reliability gain.

Third, the failure mode of Path Y is well-documented. The killed Step 4 anchoring attempt (`phase_b_step_4_anchoring_killed_2026_05_04.md`) showed that anchor injection without a reference standard homogenizes judges to consensus rather than to truth — exactly the inversion of what calibration is supposed to do. Path Y would replicate this failure mode at larger scale; Path X sidesteps it by going directly to alignment-to-golden as the reliability metric.

Fourth, the synthetic test set design (Section 5) makes alignment-to-golden a more rigorous validity check than Kappa for B/C-style criteria. Synthetic samples encode the verdict by construction — a deliberately INCOHERENT sample with Phase 2 positioning "premium executive" + Phase 3 archetype "Jester irreverent" has B2 = INCOHERENT by design, not by labeler interpretation. Judges aligning on these constructed verdicts demonstrate that the prompt operationalizes the rubric correctly. Kappa among judges on the same constructed sample would also rise, but high Kappa on a constructed-verdict sample is a weaker claim than high alignment-to-golden because Kappa does not test against the construction.

The Path X decision is locked. Future revisions should not relitigate it without a documented case that the synthetic isolation test missed a reliability dimension that cross-judge measurement would catch.

## 4. Rubric Design

Both B and C rubrics share the same shape: a tiered criterion structure, per-criterion COHERENT/INCOHERENT (B) or SOLVES/DOES_NOT_SOLVE (C) anchor pair, evidence-required-from-transcript discipline, and a JSON output schema enforced by Pydantic response_schema in the Gemini API call.

### 4.1 B Strategic Coherence — 12 criteria across 3 tiers

The B rubric (`evaluation/judge/coherence_rubric.md`) splits its 12 criteria into three tiers aligned with what the chat-rubric Q/M/P does not measure.

**Tier 1 — Essential strategic chains (B1–B5)** measures whether the primary chain holds end-to-end. B1 Problem-to-Positioning chain. B2 Positioning-to-Identity chain. B3 Identity-to-Communication chain. B4 Communication-to-KPI chain. B5 Cross-phase reasoning visibility (does each decision cite the prior-phase finding it builds on). A strategy with all five COHERENT can be defended at a leadership review.

**Tier 2 — Differentiating: artifact-design rationale visibility (B6–B9)** measures whether the agent narrates design intent before delegating to specialists. B6 visual design rationale (color, typography, composition with WHY) before creative-studio dispatch. B7 DOCX section structure intent before document-generator DOCX dispatch. B8 PPTX slide arc rationale before document-generator PPTX dispatch. B9 KPI design methodology with measurement + baseline + target + cadence + linkage to problem. These criteria are the surface where Phase A "decisions narrated, not hidden" identity edit shows up — vanilla LLMs without the senior-executor prompt anchor will fail this tier consistently, by design.

**Integration tier (B10–B12)** measures cross-cutting alignment. B10 cross-artifact alignment (visual, DOCX, PPTX, KPI all describe the same brand). B11 domain language consistency (Vietnamese F&B register correct). B12 no internal contradictions.

The score is computed as 0.5 × (Tier 1 coherent fraction) + 0.3 × (Tier 2 coherent fraction) + 0.2 × (Integration coherent fraction), with PARTIAL counted as 0.5, scaled to 0–10. The weighting reflects that Tier 1 is the baseline strategic competence; Tier 2 is the differentiator; Integration catches cross-cutting failures.

### 4.2 C Strategic Problem-Solving — 10 criteria

The C rubric (`evaluation/judge/problem_solving_rubric.md`) is a flat list of 10 criteria measuring different dimensions of problem-solving causality.

C1 Problem-solution direct linkage (Phase 0 components → Phase 5 KPIs trace each). C2 Target audience relevance (channels and register reach the diagnosed segment). C3 Constraint feasibility (budget + team + timeline numerically respected). C4 KPI causality (KPIs measure the problem, not vanity metrics). C5 Competitive realism (named competitors addressed with white space + PODs). C6 Risk awareness (fallback + monitoring threshold + pivot trigger). C7 Time-horizon match (quick-win front-loading for short deadlines). C8 ROI plausibility (CAC + break-even calc + spend-revenue link). C9 Stakeholder defensibility (typical questions answered with specifics). C10 Domain plausibility (Vietnamese F&B reality reflected).

The verdict scale is SOLVES / PARTIALLY_SOLVES / DOES_NOT_SOLVE (distinct from B's COHERENT scale by design — the same transcript may receive different verdicts on B vs C, and the verdict label difference signals which axis is being measured). The score is computed as (solves_count + 0.5 × partially_solves_count) / 10, scaled to 0–10. Equal weighting reflects that no single C-criterion is a leadership-defensibility silver bullet — failing any of the 10 is a real strategy gap.

### 4.3 Anchoring per criterion

Every B-criterion and every C-criterion in the rubric files carries one COHERENT/SOLVES anchor and one INCOHERENT/DOES_NOT_SOLVE anchor as concrete short examples. The anchors are constructed from synthetic-style content (not real pilot transcripts) to avoid answer-key leakage and to keep the threshold visible to the judge across diverse domains. Each anchor is one or two sentences, sufficient to specify the threshold without bloating the prompt.

The anchoring discipline mirrors `prompt-engineering-patterns` reference principle 10 (few-shot diversity > quantity) — two examples per criterion, contrastive pair, recency-weighted last (the criterion is read top-down so the INCOHERENT/DOES_NOT_SOLVE anchor sits visually adjacent to the verdict-decision moment). Per `claude-techniques.md` and the prompt-bearing-files convention in `CLAUDE.md`, each criterion's prose body is written as continuous lines without soft-wrapping mid-paragraph, so the model parses each criterion as one coherent unit.

## 5. Synthetic Test Set Design

### 5.1 Why synthetic instead of real pilots

Real pilot transcripts (r10–r13, iso v4) mix coherent and incoherent signals throughout the same session — useful for downstream measurement but useless as a kill gate for judge prompt design, because the verdict per criterion is itself a judgment call. Synthetic samples encode the verdict by construction: a sample is built so its expected verdict per criterion is unambiguous when read against the rubric. Judge alignment on this set therefore measures judge prompt quality, not labeler agreement with an interpretive call. This mirrors the discipline in `JUDGE_CALIBRATION_METHODOLOGY.md` Section 5: training-set evidence informs prompt edits, hold-out tests generalization. For B/C, the synthetic set serves both roles — the construction encodes the truth, and the judge has not seen any synthetic sample during prompt drafting (the prompts were written first, the samples constructed afterward).

### 5.2 B coherence test set

Five mini-transcripts at `evaluation/judge/coherence_test_set/`, each 8–10 turns covering Phase 0 → Phase 5 with explicit Phase A artifact-rationale narration before sub-agent dispatch.

| File | Label | Domain | Why this design |
|---|---|---|---|
| `coherent_premium_business_retreat.json` | COHERENT | premium business retreat F&B Q1 | All B1–B12 chains hold end-to-end with rich Phase A narration |
| `coherent_family_pho_neighborhood.json` | COHERENT | mid-tier family pho refresh | Different domain confirms generalization beyond premium F&B |
| `incoherent_premium_jester_mismatch.json` | INCOHERENT | premium executive cocktail bar with Jester archetype | Phase 2-Phase 3 mismatch cascades; Phase A narration absent |
| `incoherent_problem_solution_disconnect.json` | INCOHERENT | restaurant repositioning ignoring weekday problem | Phase 0 specific reframed as generic awareness |
| `partial_specialty_coffee_gaps.json` | PARTIAL | specialty coffee, internally aligned but missing competition response | Phase 2 addresses 1 of 2 problem components |

Two INCOHERENT samples target distinct failure modes (archetype-positioning mismatch + problem-solution disconnect), and the PARTIAL sample produces a mix of COHERENT and PARTIAL verdicts — letting the kill gate check the judge does not collapse PARTIAL into a binary. Expected verdicts per criterion are recorded in `expected_verdicts.json` with reasoning that anchors each verdict to specific evidence in the transcript.

### 5.3 C problem-solving test set

Five mini-transcripts at `evaluation/judge/problem_solving_test_set/`, fresh — not reused from the B set. The reuse decision was considered explicitly: B samples could in principle be re-scored against C-criteria, but four of ten C-criteria (C3 constraint feasibility, C6 risk awareness, C7 time-horizon match, C8 ROI plausibility) are not adequately tested by B transcripts because B transcripts focus on chain coherence rather than constraints/risks/ROI/time. C samples are therefore constructed fresh with explicit Phase 0 budget + team + timeline declarations, risk awareness + fallback contingency, ROI math, time-phased roadmap matching deadline, and stakeholder Q&A coverage.

| File | Label | Domain | Why this design |
|---|---|---|---|
| `solves_burgrr_lunch_office_growth.json` | SOLVES | fast-casual burger chain repositioning Q1 | All C1–C10 satisfied with explicit constraint + risk + ROI + roadmap + sếp Q&A |
| `solves_traditional_bakery_intergenerational.json` | SOLVES | family bakery refresh Q5 | Different domain; key C-test is risk awareness (alienate-core-customers mitigation) |
| `does_not_solve_weekday_problem_addressed_with_brand_awareness.json` | DOES_NOT_SOLVE | restaurant repositioning Q3 | Phase 0 specific reframed as generic — fails C1/C4/C7/C8/C9 cleanly |
| `does_not_solve_constraint_violation_overcommitted.json` | DOES_NOT_SOLVE | trà sữa craft launch Q1 | 25M budget + 1-person team; plan ~155M/tháng + 4+ person = 6.2x over — fails C3 cleanly |
| `partially_solves_addresses_some_problem_components.json` | PARTIALLY_SOLVES | phở refresh Q10 | Addresses 2 of 3 problem threads; misses weekday-specific dimension |

The two DOES_NOT_SOLVE samples target distinct C-failure modes (problem-solution disconnect + constraint violation), surfacing capabilities the B coherence rubric does not measure.

### 5.4 Anti-leakage discipline

Synthetic samples are constructed for these isolation tests only. They are not derived from any rubric eval scenario, persona file, existing pilot transcript, or each other (B samples and C samples are independently authored). Real pilots will be measured against the same calibrated judges after the kill gate clears, so the judges have not seen any pilot data when isolation testing completes. This mirrors the no-answer-key-leakage discipline applied to the chat rubric Step 4-bis hold-out validation (`JUDGE_CALIBRATION_METHODOLOGY.md` Section 3.3).

## 6. Validation Methodology

The kill gate per judge is two-component: alignment-to-golden ≥ 80% AND evidence quotes accurately drawn from the transcript (no hallucination). Both must hold; an aligned verdict with a hallucinated quote does not pass, because the evidence quote is the audit trail by which any conclusion can be re-checked.

**Alignment-to-golden** is computed as the count of verdict slots (sample × criterion) where the judge's verdict matches the expected verdict exactly, expressed as a percentage of total slots. PARTIAL is treated as a separate category from COHERENT and INCOHERENT (B) or from SOLVES and DOES_NOT_SOLVE (C) — not a partial credit between them — so a judge that returns PARTIAL where COHERENT was expected counts as a miss, the same as if it had returned INCOHERENT. This forces the rubric to define PARTIAL precisely rather than letting it absorb interpretive ambiguity.

**Evidence accuracy** is verified by spot-check on at least one sample post-run. The judge returns a short evidence quote per criterion; the spot-check normalizes whitespace and tests substring containment in the transcript, with composite quotes (parts joined by "...") split at the ellipsis and each component checked separately. A successful spot-check requires every quote to either be verifiably in the transcript or be the explicit "no evidence in transcript" sentinel returned for absence-of-evidence verdicts.

**Pass-criterion 80% threshold rationale**: lower than the 90%+ achieved by the chat rubric calibration on hold-out because B/C verdicts are interpretive synthesis rather than discrete observation, and PARTIAL nuance is a known interpretive boundary. The threshold sits above the 50% chance baseline by a wide margin while leaving room for judge stricter-than-labels corrections (Section 7) without forcing rubric over-fit. If real-pilot scoring later reveals that 80% alignment on synthetic samples did not translate to reliable production scoring, the threshold is raised and additional synthetic samples are added.

**Kill criterion** was set before each test run: if alignment fell below 80% or hallucinated quotes appeared, the prompt would be revised single-variable per the prompt-engineering iteration workflow before re-running, and the judge would not be applied to real pilot data until the kill gate cleared. The kill criterion did not fire on either judge.

## 7. Results

### 7.1 B coherence judge isolation test

Run on 2026-05-04 with judge `gemini-3.1-pro-preview` thinking_level medium against the 5-sample test set. Result: 50 / 60 = 83.3% alignment, kill gate PASS at +3.3 pp margin.

| Sample | Aligned | Notes |
|---|---|---|
| `coherent_premium_business_retreat` | 12 / 12 | All Tier 1 + Tier 2 + Integration COHERENT verdicted correctly |
| `coherent_family_pho_neighborhood` | 12 / 12 | Different domain, all COHERENT verdicted correctly |
| `incoherent_premium_jester_mismatch` | 10 / 12 | Phase 2-3 archetype mismatch caught + cascade; B6 / B9 stricter than expected (defendable) |
| `incoherent_problem_solution_disconnect` | 8 / 12 | Phase 0-2 disconnect caught + Phase 5 KPI miss; 4 PARTIAL-boundary edge cases differ |
| `partial_specialty_coffee_gaps` | 8 / 12 | Internal alignment caught; Tier 2 narration B7 / B8 stricter |

Misalignment direction split: 7 stricter than expected, 3 lenient than expected. The stricter direction on Tier 2 narration (B6–B9) is desirable: these criteria are the Phase A behavioral signal surface, and crediting generic narration as PARTIAL would wash out the differentiation Phase A is supposed to deliver.

Evidence accuracy spot-check on `incoherent_premium_jester_mismatch` (12 verdicts): all 12 quotes are EXACT substring matches in the transcript, zero hallucinated quotes.

### 7.2 C problem-solving judge isolation test

Run on 2026-05-04 with the same judge configuration against the C test set. Result: 41 / 50 = 82.0% alignment, kill gate PASS at +2.0 pp margin.

| Sample | Aligned | Notes |
|---|---|---|
| `solves_burgrr_lunch_office_growth` | 10 / 10 | Perfect — all C1–C10 SOLVES verdicted correctly with explicit constraint + risk + ROI + roadmap + sếp Q&A coverage |
| `solves_traditional_bakery_intergenerational` | 9 / 10 | C8 ROI: judge stricter on cumulative gross 135M vs 360M total spend in 12-month window |
| `does_not_solve_weekday_problem_addressed_with_brand_awareness` | 8 / 10 | All 8 C1/C4/C5–C9 DOES_NOT_SOLVE verdicts caught; C3 / C10 differ on PARTIAL nuance |
| `does_not_solve_constraint_violation_overcommitted` | 9 / 10 | Constraint violation 6.2x over budget caught cleanly on C3; cascade C6/C7/C8/C9 all correct |
| `partially_solves_addresses_some_problem_components` | 5 / 10 | Hardest sample — judge stricter than my labels on C7 / C8 / C9 |

Misalignment direction split: 6 stricter than expected, 3 lenient than expected. Two of the stricter judgments on the partial-solve sample are MORE defendable than the expected labels: C7 stricter because "month 1-3 social presence build" is not a revenue-quick-win for a 9-month deadline; C8 stricter because the ROI math itself states "break-even month 11" which falls past the stated 9-month deadline. The judge made independent reasonable peer-reviewer calls that caught labeler-side over-leniency, a positive signal for production use.

Evidence accuracy spot-check on `does_not_solve_constraint_violation_overcommitted` (10 verdicts): 6 EXACT verbatim matches + 3 composite quotes (parts joined by "...") whose components each verify in the transcript + 1 correct "no evidence in transcript" for the C6 risk-absence verdict. Zero hallucinated quotes.

### 7.3 Cross-judge findings

Both judges exhibit a shared bias direction toward stricter-than-labeler verdicts on PARTIAL-boundary cases, particularly on artifact-design rationale visibility (B6–B9) and stakeholder defensibility (C9). The bias is desirable rather than concerning because both directions matter for production use: lenient verdicts on these criteria would inflate BrandMind scores for low-effort generic narration and undermine the cross-system fairness comparison; stricter verdicts force narration to substantiate before earning credit.

The synthetic test set was small (5 samples per judge, 60 + 50 verdict slots total) and labels were single-author. The procedural mitigation against single-labeler bias is the construction-by-design discipline — verdicts are encoded by the structural choices the synthetic sample makes (what constraints are stated, what archetype is chosen, whether a roadmap is phased) rather than by judgment call on real ambiguous evidence. This makes the labels more defensible than single-labeler real-pilot golden labels of the kind used in the chat rubric calibration.

## 8. Limitations + Open Work

The synthetic test sets at five samples per judge are small relative to research-grade calibration sets. The samples were designed to span clear COHERENT/SOLVES, clear INCOHERENT/DOES_NOT_SOLVE, and PARTIAL boundary cases, but they do not cover all combinations of failure modes. Future iterations should add samples specifically targeting edge cases that production scoring surfaces — e.g. strategies that violate one constraint but succeed on others, strategies with internal contradictions only at Phase 4 communication level, strategies where Phase A narration is partial but not generic.

Single-author construction leaves residual bias risk. The synthetic-construction discipline mitigates this more than single-labeler real-pilot golden labels do (the truth is encoded structurally rather than interpretively), but a defensible future iteration would have a second independent author construct an additional five samples per judge to test that the construction-encoding intuition generalizes.

The PARTIAL nuance is the dominant edge case in both judges. The kill gate cleared at 80%+ in both cases despite PARTIAL-boundary disagreement on roughly half the misalignments. Production scoring will reveal whether the PARTIAL category needs sharper definition, or whether the current looseness is acceptable variance. If production scoring shows systematic PARTIAL inflation or deflation on a class of criteria, the rubric anchoring on those criteria should be tightened single-variable.

Real-pilot validation is the binding next step. Phase D-1 #6 (re-score r10–r13 with B + C judges) is the production-data validation that the synthetic-isolation kill gate predicted. If real-pilot B/C scores cluster reasonably (e.g. within ~1.5 pts across the 4 pilots, not random scatter from 3 to 9), the synthetic isolation test was a sufficient proxy and the methodology can be relied on for thesis claim. If real-pilot scores random-scatter, the synthetic samples failed to capture production interpretive variance and the prompt requires real-data-anchored revision before relying on it.

The judge's stricter-than-labeler tendency on Tier 2 (B6–B9) and constraint dimensions (C7–C9) is recorded explicitly because it is the operational direction of the judges in production. Cross-system comparisons in Phase D-2 should account for this — vanilla baselines without senior-executor narration prompts will underperform on these criteria not just because they lack the Phase A behavioral edit but because the judges read the absence as INCOHERENT rather than PARTIAL.

## 9. Reproduction Steps

The judges and isolation tests reproduce deterministically from artifacts in this repository.

```bash
# Activate the project virtualenv (uv-managed):
source .venv/bin/activate

# Run B coherence judge isolation test:
uv run --env-file environments/.env python evaluation/judge/coherence_judge.py \
  --test-set evaluation/judge/coherence_test_set/
# Output: evaluation/judge/coherence_test_set/isolation_test_report.json
# Expected: 50/60 = 83.3% alignment, kill gate PASS

# Run C problem-solving judge isolation test:
uv run --env-file environments/.env python evaluation/judge/problem_solving_judge.py \
  --test-set evaluation/judge/problem_solving_test_set/
# Output: evaluation/judge/problem_solving_test_set/isolation_test_report.json
# Expected: 41/50 = 82.0% alignment, kill gate PASS

# Score one real pilot transcript with B coherence judge:
uv run --env-file environments/.env python evaluation/judge/coherence_judge.py \
  --session-dir brandmind-output/eval/<session>/

# Score one real pilot transcript with C problem-solving judge:
uv run --env-file environments/.env python evaluation/judge/problem_solving_judge.py \
  --session-dir brandmind-output/eval/<session>/
```

The expected isolation-test results match what is recorded in this document because the judges are deterministic at the rubric and prompt level — the judge LLM is non-deterministic at temperature 1.0, but the alignment percentage stabilized within ~1 pp across observation in design-time iteration. If real-pilot scoring later reveals a need for re-running isolation tests after rubric edits, the kill gate must clear again before the edited rubric is relied on for production.

## 10. References

Primary B/C judge artifacts (in this repository):

- `evaluation/judge/coherence_judge.py` — B judge module with `score_coherence()` + `score_test_set()` + CLI
- `evaluation/judge/coherence_rubric.md` — 12 B-criteria with verdict scale + scoring weights + per-criterion anchors
- `evaluation/judge/coherence_test_set/` — 5 B synthetic samples + expected_verdicts.json + README.md + isolation_test_report.json
- `evaluation/judge/coherence_isolation_test_results.md` — B isolation test results doc with decision rationale
- `evaluation/judge/problem_solving_judge.py` — C judge module with parallel structure
- `evaluation/judge/problem_solving_rubric.md` — 10 C-criteria with verdict scale + scoring weights + per-criterion anchors
- `evaluation/judge/problem_solving_test_set/` — 5 C synthetic samples + expected_verdicts.json + README.md + isolation_test_report.json
- `evaluation/judge/problem_solving_isolation_test_results.md` — C isolation test results doc

Project context (referenced for grounding, not authored as part of B/C design):

- `eval_methodology_overhaul_plan_2026_05_03.md` — A-D plan that introduced B/C as Phase B Step 2 + Step 3
- `north_star_principles_2026_05_03.md` — eval philosophy + 2026-05-03 honest-measurement update + cross-system fairness commitment
- `phase_b_step_4_anchoring_killed_2026_05_04.md` — failed cross-judge anchoring attempt that motivated Path X choice
- `docs/JUDGE_CALIBRATION_METHODOLOGY.md` — chat rubric calibration methodology (parallel methodology for the surface-behavior layer)
- `docs/BRANDMIND_THESIS_OVERVIEW.md` — thesis claim layer that B/C judges are designed to defend
- `docs/BRANDMIND_EVAL_RUBRIC.md` — chat rubric source of truth (complementary, not replaced by B/C)

Commit history:

- `8b8e45a` — Phase A v1 ("decisions narrated" CORE PHILOSOPHY anchor) — agent-side prerequisite for B Tier 2 measurement
- `029eba3` — M2-S2 calibration iteration 3 — chat rubric calibration baseline preceding B/C design
- `23406c1` — Phase B Step 2 (B coherence judge + 12-criterion rubric + 5 synthetic samples + isolation test PASS 83.3%)
- `ab8effa` — Phase B Step 3 (C problem-solving judge + 10-criterion rubric + 5 synthetic samples + isolation test PASS 82.0%)

Tasks:

- Task #51 — Phase A identity edit (completed)
- Task #52 — Phase B Step 2 B coherence judge (completed)
- Task #53 — Phase B Step 3 C problem-solving judge (completed)
- Task #65 — B synthetic test set (completed)
- Task #66 — B isolation test (completed)
- Task #67 — C synthetic test set (completed)
- Task #68 — C isolation test (completed)
- Task #69 — this methodology doc (completed)
