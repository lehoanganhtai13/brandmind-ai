# Judge Calibration Methodology

> This document describes the four-phase calibration procedure that aligned BrandMind's three-judge LLM panel (Claude Sonnet 4.6 + Gemini 3.1 Pro + GPT 5.4) with a single-expert golden reference standard. Calibration was executed on 2026-05-04 and replaced an earlier, failed anchoring attempt that had attempted to homogenize judges toward consensus rather than aligning them to truth. The procedure reproduces deterministically from artifacts checked into this repository; outcomes are summarized in `evaluation/judge/calibration_validation_results.md`. Anyone with the codebase should be able to read this document, understand what was done and why, and re-run any phase to validate or extend the calibration.

## 1. Goal & Scope

BrandMind's evaluation pipeline scores each pilot session along three dimensions (Strategy Quality 50%, Mentoring 30%, Personalization 20%) using a 105-criterion rubric (`docs/BRANDMIND_EVAL_RUBRIC.md`). Each criterion takes one of three verdicts (MET, UNMET, CANNOT_ASSESS), aggregated by `evaluation/judge/scoring.py` into per-dimension 0–10 scores and an overall score. The pipeline runs three LLM judges in parallel and reports cross-judge Fleiss' Kappa as inter-rater agreement.

Across thirteen pilot runs in March–May 2026, two methodology problems persisted. First, cross-judge Kappa plateaued in the 0.32–0.44 range (Landis & Koch "Fair" to "Moderate"), below the 0.61 "Substantial" threshold typically cited as research-grade for LLM-as-judge panels. Second, the variance concentrated in a stable subset of eleven criteria where Gemini ran systematically lenient and Claude+GPT systematically strict (recorded in `project_phase0_chat_rubric_findings.md` Constraint 2). An earlier fix attempt — injecting MET/UNMET anchor block-quotes into three high-variance criteria (Step 4 of the eval-methodology overhaul plan) — produced zero verdict movement on r12 and was killed (see `phase_b_step_4_anchoring_killed_2026_05_04.md`). The lesson: anchor injection without a reference standard homogenizes judges to consensus, not to truth, and consensus is exactly the dependent variable being measured.

This procedure addresses the variance problem by aligning each judge to a *single-labeler golden reference set* rather than to each other. It runs once after each major rubric or judge-prompt edit and accomplishes three things: (1) per-judge alignment-to-golden measurement with deviation direction visible (lenient / strict / abstain) and criterion family; (2) evidence-based prompt-rubric edits targeting the documented deviation patterns; (3) hold-out validation that the edits generalize to unseen transcripts before being relied on for production scoring.

Out of scope: B/C judges (Strategic Coherence + Strategic Problem-Solving dimensions, single-judge-per-dimension with separate inter-rater concerns) and the broader thesis evaluation (cross-persona M-8 stability, vanilla baseline comparison, self-eval triangulation). This procedure targets only the *existing* 105-criterion rubric judge panel.

Cross-system fairness is preserved throughout: the calibrated rubric and judge prompt apply identically to BrandMind, ChatGPT vanilla, and Gemini vanilla judging chains. No system-specific anchor, hint, or prior was introduced.

## 2. Theoretical Foundation

The procedure is grounded in three principles drawn from the project's eval philosophy (`north_star_principles_2026_05_03.md` Section 3) and instrument-calibration practice in measurement theory.

**Calibration aligns measurement to a reference standard, not to consensus.** An instrument is calibrated when its readings agree with a known reference, not when multiple instruments produce identical readings. Forcing three judges to agree without a golden reference propagates whichever judge dominates the consensus signal; the variance consensus-seeking removes is variance against an unknown truth. This was the binding misconception of the failed Step 4 anchoring attempt and is the central commitment here.

**Judge = user (Tran et al. 2015 perceived-personalization context).** The rubric measures what a junior marketer like Linh would perceive from the chat transcript alone: artifacts and workspace files are private implementation, not user-facing value. Judges evaluate transcripts only. Calibration preserves this commitment: golden labels are produced from the same transcript surface the production judges receive, with no privileged access to artifact content, workspace state, or system internals.

**Rubric is hypothesis, not ground truth.** The rubric (`docs/BRANDMIND_EVAL_RUBRIC.md`) is one research team's operationalization of "good brand strategy mentoring", not absolute truth. Golden labels are likewise one expert reviewer's interpretation of how the rubric applies to specific transcripts. The procedure mitigates single-labeler bias through full-evidence transparency — every label carries an evidence quote and reasoning — so any conclusion derived from the calibration can be audited by re-reading the source.

A practical corollary distinguishes anchor injection from calibration. Anchor injection adds MET/UNMET examples to the rubric to "show" judges what a target verdict looks like; with no golden reference, this homogenizes the judges' interpretations toward whatever shape the anchors describe — typically the rubric author's own intuition — without any check that this shape matches user-perceived value. Calibration uses the same kind of evidence (anchor quotes from real transcripts) but only after measuring deviation from a golden reference, and only as targeted adjustments to deviation patterns the measurement actually documented. The effect is alignment to the reference, not consensus among the judges.

## 3. Dataset

### 3.1 Labeler qualifications

The 4th-expert reviewer producing the golden labels was Claude (Sonnet 4.5/4.6 family, with full project context loaded). Qualifications relevant to the task: domain familiarity with the brand strategy frameworks the rubric draws from (Keller CBBE, Aaker, Trout-Ries, Sharp Distinctive Brand Assets, Cialdini); Vietnamese language fluency for the F&B Vietnam transcripts; project-internal context (Linh persona spec, prior pilots r10/r11/r12/r13, recent agent-prompt iterations); and detailed familiarity with the 105-criterion rubric including the Common Failure column on each row. Single-labeler bias was acknowledged at procedure start and mitigated by per-label transparency: every verdict carries an evidence quote and a reasoning chain that maps the evidence to the criterion's Evidence Required and Common Failure language.

### 3.2 Criterion scope

Eleven criteria were labeled, drawn directly from the documented Round 1 variance subset in `project_phase0_chat_rubric_findings.md` Constraint 2: M2-E1, M2-S2, P2-S2, P3-E1, P3-S3, P4-E2, P4-S3, P4-S4, Q1-S4, Q3-S3, Q4-E2. These are the criteria where the cross-judge variance pattern was observed across multiple pilot runs (Gemini lenient on personalization-pattern and mentor-pacing criteria; Claude+GPT strict on research-specificity and DBA-enumeration criteria). The criteria all receive identical transcript input across the three judges, so the variance is interpretation-side (semantic strictness, threshold elasticity) rather than input-side. Criteria already aligned across all three judges were excluded — calibration cannot improve what is already aligned, and including them would dilute the deviation signal.

### 3.3 Transcript split

Four Linh-persona pilot transcripts were used, covering four distinct system states. Three formed the training set, one was held back for Phase 4 validation.

| Set | Transcript ID | System state |
|-----|--------------|--------------|
| Training | `brandmind_linh_r10_20260430` | Pre-Path-C baseline |
| Training | `brandmind_linh_r12_20260502` | Path-C cumulative (Cognitive Apprenticeship rewrite) |
| Training | `brandmind_linh_r13_20260503` | Post-L2-new (Phase 5 KPI completeness) |
| Hold-out | `brandmind_linh_phase_a_iso_v4_20260504_0246` | Post-Phase-A v1 + 4 sub-plans |

The split serves two purposes. First, training across four different system states reduces the risk that calibration overfits to a single agent-prompt configuration; deviation patterns observed across all three system iterations are more likely to be genuine judge-side interpretation issues than transcript-specific artifacts. Second, the hold-out preserves the no-answer-key-leakage discipline (`north_star_principles_2026_05_03.md` Section 4): no information from the hold-out transcript informed golden-label authoring, deviation analysis, or prompt adjustment. The hold-out remained sealed during Phases 1 through 3 and was revealed only for Phase 4 validation.

### 3.4 Per-label schema

Each golden label in `evaluation/judge/golden_labels.json` carries three fields: a verdict (MET, UNMET, or CANNOT_ASSESS), an evidence quote (transcript text with turn number), and a reasoning paragraph (two to four sentences mapping the evidence to the criterion's Evidence Required statement and the Common Failure column). The schema mirrors the production-judge output format so verdict-level comparison is direct.

A representative entry, for Q1-S4 on r12: verdict MET; evidence Turn 3 of agent (named real competitors with concrete VND price ranges quoted verbatim); reasoning citing that named real businesses plus concrete price numbers exceed the Evidence Required bar of "named sources, concrete numbers, real business names, verifiable details" and explicitly do not match Common Failure of "research shows" without specifics.

### 3.5 Caveats

Three caveats apply to downstream use of the dataset.

First, the Phase 1 sub-agent labeler paraphrased rather than quoted verbatim from the transcripts (a protocol drift detected during self-double-check). A keyword spot-check confirmed that all entities and concepts cited in the evidence strings appear in the actual transcript content, and a reasoning audit on three sample labels confirmed that verdicts align with the rubric's Common Failure semantics. Verdicts are sound for verdict-level comparison; downstream use that requires verbatim quote anchoring should re-extract from transcripts using the cited turn numbers.

Second, the dataset is single-labeler. Golden therefore reflects one expert reviewer's rubric interpretation, not a consensus of independent labelers. Per-label transparency makes every label auditable, but the residual bias risk remains and is recorded as open work.

Third, the dataset is small relative to research-grade calibration sets typical in academic publication (44 labels vs hundreds-to-thousands typical for trained-rater calibration in fields like content moderation). The size is justified for thesis-grade calibration of an in-development system with a contained variance scope; future iterations should expand to additional personas and additional criteria as the rubric matures.

## 4. Four-Phase Process

### Phase 1 — Build golden labels

Phase 1 produced 44 labels (11 criteria × 4 transcripts) over approximately 13 minutes of wall-clock time. The labeling work was delegated to a general-purpose sub-agent on the main thread, briefed with a self-contained instruction set: criterion definitions extracted from the rubric, transcript paths, the per-label schema, and an eight-point labeling protocol covering verbatim quoting, anti-leniency (default UNMET when uncertain), no answer-key leakage, cross-transcript consistency, and a self-double-check pass before submission. Output landed at `evaluation/judge/golden_labels.json` plus a companion `evaluation/judge/golden_labels_summary.md` documenting the verdict matrix, hard cases, and per-criterion consistency notes.

The verdict distribution across the four transcripts revealed a clear structural pattern: nine of the eleven criteria are uniform across all four system states, indicating system-level gaps that no recent agent-prompt intervention has addressed, while two criteria (Q4-E2 and M2-S2) show transcript-specific variation that maps to genuine differences in agent behavior across pilots. This distinction is preserved in Phase 2 and is what allows the procedure to distinguish judge-variance issues (Phase 3 target) from agent-behavior issues (orthogonal to calibration).

### Phase 2 — Measure judge deviation

Phase 2 is a deterministic Python script, `evaluation/judge/calibrate_deviation.py`, which loads the golden labels and the per-transcript cached `evaluation_results.json` produced by `run_judges.py`, then renders a per-judge per-criterion confusion matrix grouped into five buckets (`aligned`, `judge_lenient`, `judge_strict`, `cannot_assess_split`, `unknown`). The script calls no LLM and therefore the deviation report is exactly reproducible from the inputs.

The Phase 2 output (`evaluation/judge/calibration_deviation_report.md`) showed three distinct judge profiles on the training set. Claude Sonnet 4.6 aligned on 75.8% of training labels with a dominant strict deviation: 3/3 strict on Q1-S4 (research specificity), 3/3 strict on Q3-S3 (DBA enumeration), 1/3 strict on Q4-E2 and M2-S2. Gemini 3.1 Pro aligned on 51.5% with a dominant lenient deviation: 2/3 lenient each on M2-E1, M2-S2, P4-E2, P4-S3, P4-S4, plus 1/3 lenient on P3-E1, P3-S3, Q4-E2, plus 3/3 CANNOT_ASSESS escape on P2-S2. GPT 5.4 aligned on 66.7% with a mixed profile: 3/3 strict on Q1-S4, 2/3 strict on Q3-S3, plus 1/3 lenient each on the personalization-pattern criteria.

These profiles cluster into five deviation patterns that became the targets for Phase 3 prompt adjustment.

### Phase 3 — Evidence-based prompt adjustment

Phase 3 rewrote ten criterion rows in both the source-of-truth rubric (`docs/BRANDMIND_EVAL_RUBRIC.md`) and the operational copy used by `run_judges.py` (`evaluation/judge/judge_prompt.md`), one logical edit per deviation pattern. The two files are kept synchronized; judge_prompt.md is a verbatim operational copy of the rubric's Evidence Required and Common Failure cells. The per-pattern changelog at `evaluation/judge/calibration_changelog.md` documents, for each pattern, the deviation evidence from Phase 2, the cell text before and after, the expected effect on alignment, and the residual risk.

The five patterns and their adjustments (full before/after text in the changelog):

| Pattern | Deviation observed | Adjustment shape |
|---------|---------------------|------------------|
| 1: Q1-S4 strict | Claude + GPT 3/3 strict; Gemini aligned | Three anchor types (named sources, concrete numbers, real business names) made explicitly *alternative* — any one satisfies — rather than conjunctive checklist |
| 2: Q3-S3 strict | Claude 3/3, GPT 2/3 strict; Gemini aligned | DBA category list enumerated explicitly per Sharp DBA framework (color, sonic, shape, character, pattern, typography, sensory, photography, voice/tone) so the "etc." in the original was no longer read as exhaustive |
| 3: Personalization 6.3–6.4 lenient | Gemini 1–2/3 lenient across P3-S3, P3-E1, P4-S3, P4-S4, P4-E2; GPT 1/3 same | Pattern recognition requires either (a) an explicit recurrence quantifier ("thường", "consistently") or (b) trait-naming spanning two or more prior moments. Per-criterion specifics preserved |
| 4: Mentor pacing lenient | Gemini 2/3 lenient on M2-E1, M2-S2 | Depth difference = comparable concepts at different depth (not topic novelty); incremental = multi-turn split with user input between segments (not single-turn formatting) |
| 5: P2-S2 CANNOT_ASSESS escape | Gemini 3/3 abstain | Criterion scope clarified: applies whenever agent makes any research-style claim; CANNOT_ASSESS reserved for sessions with no research-style claims at all; confident claims without hedging is UNMET |

Wording across all five patterns followed the principles in `~/.claude/skills/prompt-engineering-patterns/`: affirmative phrasing ("Verdict MET requires...") rather than negative; criterion-intent anchored (citing the underlying Sharp DBA / Tran 2015 perceived / cognitive-apprenticeship framework where applicable); single-variable per pattern; no heavy ALWAYS/NEVER blocks; continuous-line cells preserving the markdown-table format the rubric uses elsewhere.

### Phase 4 — Validate calibrated judges on hold-out

Phase 4 ran the three production judges with the calibrated `judge_prompt.md` against the hold-out transcript (iso v4) and compared verdicts to the golden hold-out labels. This is the standard hold-out protocol: training set informs prompt edits, hold-out tests whether the edits generalize to unseen content. Because the hold-out was sealed during Phases 1–3, alignment on the hold-out cannot be explained by the prompt having seen the same evidence.

The result table is reproduced in full in `evaluation/judge/calibration_validation_results.md`. Aggregate alignment on the hold-out: Claude 100% (11/11), Gemini 90.9% (10/11), GPT 100% (11/11). Cross-judge Fleiss' Kappa lifted from 0.319 (post-failed-anchoring on r12) to 0.592 (calibrated, on iso v4 hold-out), crossing from "Fair" to "Moderate" in the Landis & Koch interpretation scale. The single residual deviation was Gemini lenient on M2-S2 — the same M2-S2 sharpening landed in Phase 3 reduced Gemini's M2-S2 lenience from 2/3 on training to 1/1 on hold-out, but did not eliminate it.

## 5. Validation Methodology

The validation design separates training and hold-out so that any signal observed on the hold-out is generalization, not memorization. Training set = r10, r12, r13 (used in Phases 1, 2, 3). Hold-out = iso v4 (used only in Phase 4). The hold-out was selected before Phase 1 began and never inspected during prompt adjustment.

Two metrics drive the pass/fail decision. Per-judge alignment-to-golden is the count of (criterion, transcript) pairs where the judge's verdict matches the golden verdict, expressed as a percentage of total pairs scored by that judge. Cross-judge Fleiss' Kappa is computed using the standard chance-corrected agreement formula and interpreted on the Landis & Koch scale (0.0–0.20 Slight, 0.21–0.40 Fair, 0.41–0.60 Moderate, 0.61–0.80 Substantial, 0.81–1.00 Almost Perfect).

The pass criterion has two components: alignment-to-golden lift on the hold-out compared to the pre-calibration training baseline, and cross-judge Kappa lift toward the 0.61 Substantial threshold. Both must hold; alignment without Kappa lift would suggest the calibrated judges agree with golden but disagree with each other on different criteria, indicating calibration noise rather than shared improvement. Kappa lift without alignment lift would suggest consensus convergence without truth-tracking, the failure mode the failed Step 4 anchoring exhibited.

The kill criterion was set before Phase 4: if hold-out alignment did not improve over the training-set pre-calibration baseline, calibration would be reverted in working tree (Phase 3 commits would be reset) and the procedure documented as a kill, with the variance attributed to model-architectural causes rather than promptable interpretation issues. The kill criterion did not fire — alignment lifted +24.2 to +39.4 percentage points across the three judges and Kappa lifted from 0.319 to 0.592.

## 6. Results

The results table summarizes the Kappa progression and per-judge alignment lift. Pre-calibration training-set alignment uses the Phase 2 deviation report; post-calibration hold-out alignment uses the Phase 4 validation snapshot.

| Stage | Kappa | Interpretation |
|-------|-------|----------------|
| r12 pre-anchoring | 0.351 | Fair |
| r12 post-failed-anchoring | 0.319 | Fair (slight regression) |
| iso v4 hold-out post-calibration | **0.592** | **Moderate** |

| Judge | Pre-calibration training alignment | Post-calibration hold-out alignment | Improvement |
|-------|------------------------------------|--------------------------------------|-------------|
| claude-sonnet-4.6 | 75.8% (25/33) | 100% (11/11) | +24.2 pp |
| gemini-3.1-pro-preview | 51.5% (17/33) | 90.9% (10/11) | +39.4 pp |
| gpt-5.4 | 66.7% (22/33) | 100% (11/11) | +33.3 pp |

The post-calibration Kappa of 0.592 sits 0.018 below the 0.61 Substantial threshold typically cited as research-grade for LLM-as-judge panels; the single residual deviation (Gemini lenient on M2-S2) is what holds the Kappa below Substantial. A second methodological observation worth noting: post-calibration GPT-5.4 dimension scores on the hold-out drop sharply (Overall 1.47, Quality 1.48, Mentor 1.75, Personalization 1.0). This reflects calibration removing GPT's prior lenience on the personalization-pattern cluster — the resulting strict reading is now consistent with golden, but it surfaces how systematically lenient GPT had been on these criteria in earlier pilots. The aggregate-average drop is the "reduce overrating, make averages honest" outcome originally targeted by the eval-methodology overhaul plan, delivered without the homogenization failure mode of the killed anchoring approach.

## 7. Limitations + Open Work

The single residual deviation (Gemini lenient on M2-S2, 1 of 11 hold-out labels) holds the cross-judge Kappa below 0.61 Substantial. A targeted Phase 3 iteration on M2-S2 — sharpening the wording so that single-turn formatted long content does not satisfy "incremental" even when visually segmented — is the recommended next step if research-grade Kappa is required for thesis defense.

The single-labeler bias risk in the golden dataset is unmitigated beyond the per-label transparency discipline. A defensible future iteration would add a second independent labeler and compute inter-labeler Kappa on the golden labels themselves, providing a measure of how much of the calibration depends on the specific labeler's interpretation. The current procedure is documented honestly as single-labeler.

The paraphrase quote caveat from Phase 1 is a protocol-discipline issue. Future labeling rounds should enforce strict verbatim discipline through main-thread labeling or tool-mediated substring extraction. This is a procedure improvement, not a result invalidation.

The eleven-criterion scope leaves the remaining 94 rubric criteria un-calibrated. The selection criterion was documented variance: only criteria where Round 1 pilots had shown systematic Gemini-vs-Claude+GPT divergence were included. Other criteria may carry unaddressed variance that current Kappa measurements do not surface because the variance is uniform in direction across judges. A periodic golden-label sample on additional criteria would catch this drift.

The 6.0–6.5 honest-measurement target update from `north_star_principles_2026_05_03.md` is the relevant context for interpreting calibration results: the purpose is making measurement honest, not raising scores. Post-calibration GPT scores fell on the hold-out because calibration removed lenience, not because the system regressed — the intended outcome, consistent with the thesis claim shift toward defendable improvement on B/C dimensions and chat process metrics with honest measurement.

## 8. Reproduction Steps

Phase 2 (deviation analysis) and Phase 4 (hold-out validation) reproduce deterministically from artifacts in this repository. Phase 1 (golden labeling) and Phase 3 (prompt adjustment) require human-in-the-loop judgment and reproduce only at the procedural level — running them again would produce a different but methodologically equivalent result.

```bash
# Activate the project virtualenv (uv-managed):
source .venv/bin/activate

# Phase 2 — recompute deviation report from cached eval results vs golden labels:
python evaluation/judge/calibrate_deviation.py
# Output: evaluation/judge/calibration_deviation_report.md

# Phase 4 — re-run 3-judge eval on the hold-out with calibrated prompt:
python evaluation/judge/run_judges.py \
  --session-dir brandmind-output/eval/brandmind_linh_phase_a_iso_v4_20260504_0246/
# Output: brandmind-output/eval/<session>/evaluation_results.json
# Compare verdicts to evaluation/judge/golden_labels.json hold-out section.
```

For full procedure-level reproduction including Phases 1 and 3, follow the labeling protocol described in Phase 1 above against a chosen training+hold-out transcript split, then walk Phases 2–4 sequentially. Each phase's output is checked into the repo so partial reproduction (e.g. only re-running Phase 4 against a new agent state) is supported.

## 9. References

Primary calibration artifacts (in this repository):

- `evaluation/judge/golden_labels.json` — 44 golden labels, training + hold-out
- `evaluation/judge/golden_labels_summary.md` — per-criterion verdict matrix, hard cases, anchor quotes
- `evaluation/judge/calibrate_deviation.py` — Phase 2 deterministic deviation analysis
- `evaluation/judge/calibration_deviation_report.md` — Phase 2 output (training set)
- `evaluation/judge/calibration_changelog.md` — Phase 3 per-pattern adjustment log with deviation evidence + before/after
- `evaluation/judge/calibration_validation_results.md` — Phase 4 hold-out validation snapshot
- `evaluation/judge/judge_prompt.md` — calibrated operational copy of the rubric
- `docs/BRANDMIND_EVAL_RUBRIC.md` — rubric source of truth (calibrated rows)
- `evaluation/judge/run_judges.py` — production 3-judge runner consuming the calibrated prompt
- `evaluation/judge/scoring.py` — per-dimension aggregation including quality-gate cap

Project context (referenced for grounding, not authored as part of this calibration):

- `docs/BRANDMIND_THESIS_OVERVIEW.md` Section 4.2 — multi-dimensional personalization framing including Tran et al. 2015 perceived-personalization principle that motivates the P3/P4 criterion design
- `docs/BRANDMIND_EVAL_RESEARCH.md` — research grounding for the rubric structure
- `tasks/task_template.md` Rule 4 + 2.5 — production-grade docstring/comment standards applied to the calibration scripts

Commit history:

- `7f49818` — Phase 1 (golden labels) + Phase 2 (deviation analysis) shipped
- `94860a8` — Phase 3 (10-criterion prompt adjustment) shipped
- Phase 4 validation snapshot is the working-tree state at 2026-05-04 evening

Tasks:

- Task #59 — failed Step 4 anchoring (killed)
- Task #60 — Phase 1 golden labels (completed with paraphrase caveat)
- Task #61 — Phase 2 deviation analysis (completed)
- Task #62 — Phase 3 prompt adjustment (completed)
- Task #63 — Phase 4 hold-out validation (completed)
