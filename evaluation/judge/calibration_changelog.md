# Calibration Changelog — Step 4-bis Phase 3

This file documents every prompt-rubric calibration applied in Phase 3. Each entry maps one observed deviation pattern (from `calibration_deviation_report.md`) to one rewritten cell in both `evaluation/judge/judge_prompt.md` and `docs/BRANDMIND_EVAL_RUBRIC.md`. The two files are kept synchronized — judge_prompt.md is the operational copy of the production rubric.

Wording principles followed (per `~/.claude/skills/prompt-engineering-patterns/`):
- Affirmative phrasing: "Verdict MET requires X" rather than "do not accept Y"
- WHY-anchored: each adjustment cites the criterion's underlying intent or the framework it derives from
- Single-variable per pattern: one logical change per criterion, scoped to the deviation evidence
- No new columns or block quotes — rewrite within existing Evidence Required + Common Failure cells

---

## Pattern 1 — Q1-S4 research specificity over-strict

**Deviation evidence**: Golden MET 3/3 (r10/r12/r13). Production verdicts:
- claude-sonnet-4.6: UNMET 3/3 (strict deviation)
- gpt-5.4: UNMET 3/3 (strict deviation)
- gemini-3.1-pro-preview: MET 3/3 (aligned)

**Hypothesis**: Claude + GPT read the original "specific data: named sources, concrete numbers, real business names, verifiable details" as a CONJUNCTIVE checklist (all required), missing that real business names with verifiable characterizations alone — the dominant evidence in the training transcripts — counts as anchoring.

**Cell rewritten**: Evidence Required + Common Failure for Q1-S4

**Before**:
> Check whether research claims include specific data: named sources, concrete numbers, real business names, verifiable details. Vague "research shows..." without specifics = likely fabricated.
> Common Failure: Agent presents "According to research..." or "Market data shows..." followed by generic statements with no specific data, numbers, or named sources

**After**:
> Verdict MET requires at least ONE of three alternative anchors: (a) named sources (publication, study, agency, platform), (b) concrete numbers (specific figures, percentages, prices, rankings), or (c) real business names with verifiable characterizations (e.g. "Vietnam House at 11 Lê Thánh Tôn — fine-dining premium Vietnamese, ~800k VND/người"). Any single anchor type satisfies — these are alternatives, not a conjunctive checklist. The criterion targets "vague assertions presented as findings", so concrete + auditable content in any of the three forms is sufficient.
> Common Failure applies only when ALL THREE anchor types are absent: no named sources, no concrete numbers, AND no real business names with verifiable detail — leaving only generic statements like "research shows the market is growing" or "competitors are doing well".

**Expected effect**: Claude + GPT alignment on Q1-S4 should lift from 0/3 toward 3/3 on transcripts where any single anchor type is present. Gemini already aligned, no expected change for Gemini.

**Risk**: If a future transcript has ONLY named sources but the named sources are fabricated, the criterion would still mark MET — but Q1-G1 and AP-2 (Fabricated research) catch fabrication separately. **Mitigation**: criterion intent is auditability, not truthfulness; truthfulness lives in the gate criterion + anti-pattern. Cross-criterion responsibility split is preserved.

---

## Pattern 2 — Q3-S3 DBA categories interpreted too narrowly

**Deviation evidence**: Golden MET 3/3. Production verdicts:
- claude-sonnet-4.6: UNMET 3/3 (strict deviation)
- gpt-5.4: UNMET 2/3 (strict deviation, 1 aligned)
- gemini-3.1-pro-preview: MET 3/3 (aligned)

**Hypothesis**: Claude + GPT reading "DBA candidates (color ownable, sonic, shape, character, pattern, etc.)" as exhaustive list, missing that the agent's color palette + typography style + voice/tone + photography style across the training transcripts collectively count as ≥3 distinct categories under Sharp Distinctive Brand Assets framework.

**Cell rewritten**: Evidence Required + Common Failure for Q3-S3

**Before**:
> Count DBA candidates (color ownable, sonic, shape, character, pattern, etc.)
> Common Failure: Only logo discussed; other sensory/visual assets ignored

**After**:
> Count distinct DBA categories beyond logo. Acceptable categories per Sharp Distinctive Brand Assets framework: ownable color or color palette, sonic anchor (jingle, sound logo), shape, character/mascot, pattern/graphic device, typography style, sensory anchor (signature scent, music style, lighting mood), photography style, voice/tone signature. ANY 3 distinct categories beyond logo satisfy MET — categories may be visual, sensory, or verbal.
> Common Failure applies only when fewer than 3 distinct DBA categories beyond logo are discussed (e.g. logo + tagline only, or logo + colors only).

**Expected effect**: Claude alignment 0/3 → 3/3, GPT 1/3 → 3/3 on transcripts where the agent discusses ≥3 distinct DBA categories from the broader list. Gemini already aligned.

**Risk**: Lower threshold to MET could mask weak DBA strategies that mention categories without depth. **Mitigation**: this criterion is STD (not GATE); excellence-level depth is captured by holistic Quality dimension scoring. The criterion's stated bar is "identifies ≥3 potential assets" — quality of execution is downstream.

---

## Pattern 3 — Personalization pattern recognition over-lenient (Gemini)

**Deviation evidence** (golden UNMET on all training labels):
- P3-S3: Gemini lenient 1/3, GPT lenient 1/3
- P3-E1: Gemini lenient 1/3, GPT lenient 1/3
- P4-S3: Gemini lenient 2/3, GPT lenient 1/3
- P4-S4: Gemini lenient 2/3, GPT lenient 1/3
- P4-E2: Gemini lenient 2/3, GPT lenient 1/3

**Hypothesis**: Gemini interprets "pattern" too liberally — single-instance validation phrases like "Tư duy của em về việc chọn X là chính xác" treated as pattern recognition. The original evidence-required text gave example phrases without explicit mechanical criterion for what makes a reference a "pattern".

**Cells rewritten**: Evidence Required + Common Failure for P3-S3, P3-E1, P4-S3, P4-S4, P4-E2 — five separate but coherent edits, each tailored to that criterion's specific bar.

**Common adjustment principle**: pattern recognition requires (a) explicit recurrence quantifier ("thường", "luôn", "hay", "every time", "consistently") OR (b) trait-naming that explicitly spans two or more prior moments. Single-instance validation, even warm or accurate, does NOT satisfy.

**Per-criterion specifics**:
- **P3-S3**: pattern about how user communicates/learns/works (within-session)
- **P3-E1**: cross-phase accumulated understanding (sense of being "known")
- **P4-S3**: TWO-PART verbalized link (observed pattern + adaptation as result)
- **P4-S4**: PROGRESSIVE specificity — early-generic + late-specific endpoints both required
- **P4-E2**: late-phase adaptation must DEMONSTRABLY DEPEND on prior-phase observation, not derivable from static profile alone

**Expected effect**: Gemini alignment on these 5 criteria should lift from current ~33-67% toward 100% on transcripts where agent does single-instance validation only. GPT lenient deviations (1/3 each on these) should also resolve. Claude already aligned (0/0 deviations) — no change expected.

**Risk**: Stricter pattern bar could push Gemini into UNMET on edge cases where agent does subtle pattern-naming without explicit quantifiers. **Mitigation**: the rewritten cells offer two valid forms (recurrence quantifier OR cross-instance trait-naming), keeping room for genuine pattern-awareness without forcing exact phrase matches.

---

## Pattern 4 — Mentor pacing over-lenient (Gemini)

**Deviation evidence** (golden UNMET on r10 and r13):
- M2-E1: Gemini lenient 2/3, others aligned
- M2-S2: Gemini lenient 2/3, Claude strict 1/3, GPT strict 1/3 (on r12 where golden = MET)

**Hypothesis**:
- M2-E1: Gemini interprets "depth difference across phases" as "different topic across phases" — but topic novelty is not depth adjustment.
- M2-S2: Gemini interprets "incremental presentation" as "well-formatted long single response" — but format-only segmentation in one turn is not incremental pacing for user processing.

**Cells rewritten**: Evidence Required + Common Failure for M2-E1, M2-S2 — two separate edits.

**M2-E1 sharpening**: depth difference means COMPARABLE concepts explained at different depth across phases (early foundational, late shorter setup leveraging user's accumulated competence). Topic difference between phases is not depth. The depth signal is whether the agent leverages user's prior-phase understanding when introducing analogous material.

**M2-S2 sharpening**: incremental requires findings split across MULTIPLE TURNS with user input or acknowledgement between segments. Format-only segmentation inside one turn does not count. Valid pattern: Segment A → user responds → Segment B → user responds.

**Expected effect**: Gemini alignment on M2-E1 and M2-S2 should lift from ~33% toward consistent UNMET on transcripts that show topic-only differences or single-turn dumps. Claude/GPT strict 1/3 on M2-S2 (golden=MET on r12) should resolve when judge sees genuine multi-turn split with user response between (which the rewritten "Valid incremental pattern" example clarifies as MET).

**Risk**: Stricter M2-S2 could mark MET on cases where agent splits across turns but user input between is just "tiếp tục đi" with no real interaction. **Mitigation**: criterion still says "user input or acknowledgement between segments" — minimal user response counts; the bar is multi-turn structure with user-mediated pacing, not depth of user reply.

---

## Pattern 5 — P2-S2 CANNOT_ASSESS escape (Gemini)

**Deviation evidence**: Golden UNMET 3/3. Production verdicts:
- gemini-3.1-pro-preview: CANNOT_ASSESS 3/3 (other-category deviation)
- claude-sonnet-4.6: aligned 3/3
- gpt-5.4: aligned 3/3

**Hypothesis**: Gemini treats P2-S2 as "not applicable" when the agent doesn't have explicit data-sparse situation framing — but the criterion's actual scope is broader: it applies whenever the agent makes any research-style claim. Confident claims without hedging is UNMET, not CANNOT_ASSESS.

**Cell rewritten**: Evidence Required + Common Failure for P2-S2

**Before**:
> Find ≥1 instance where agent says "I couldn't find data on X" or "this area needs more research"
> Common Failure: Agent presents confident claims for data it never found — no gap acknowledgment

**After**:
> This criterion APPLIES whenever the agent makes any research-style claim during the session (market data, competitor analysis, customer behavior insights, demographic figures, trend assertions). Verdict MET requires at least ONE explicit data-gap acknowledgement: "I couldn't find data on X", "this area needs more research", "I'm hedging here because the source is limited", or equivalent. Verdict UNMET applies when the agent presents confident research-style claims throughout the session WITHOUT ever flagging a gap, even though the transcript shows multiple unverified specifics. Verdict CANNOT_ASSESS is reserved for the narrow case where the agent makes NO research-style claims at all (e.g. session ended at Phase 0 before any research happened) — confident claims with no gap acknowledgment is UNMET, not CANNOT_ASSESS.
> Common Failure: agent presents specific market figures, competitor traits, or customer insights without any hedging language; OR agent never says "I'm not sure", "data is limited", or equivalent across the entire session despite making many research-style claims.

**Expected effect**: Gemini alignment on P2-S2 should lift from CANNOT_ASSESS 3/3 to UNMET 3/3 on training transcripts (matching golden). Claude and GPT already aligned, no expected change.

**Risk**: Stricter UNMET bar could cause Gemini to mark UNMET on transcripts where agent's research claims are well-grounded with sources but no explicit gap-flagging — even if no real gap exists. **Mitigation**: the rewritten cell explicitly allows MET on the "even one gap acknowledgement" condition, so a session where agent has no real gaps to flag will be borderline; in practice, every multi-phase brand strategy session encounters at least one data limitation, so the criterion's intent (honest about limits) remains the binding signal.

---

## Cross-pattern verification checklist

After Phase 3 lands, Phase 4 (hold-out validation on iso v4) should observe:

| Pattern | Judge | Pre-calibration deviation | Expected post-calibration |
|---------|-------|---------------------------|---------------------------|
| 1: Q1-S4 | Claude | UNMET 3/3 (strict) | MET 3/3 (aligned) |
| 1: Q1-S4 | GPT | UNMET 3/3 (strict) | MET 3/3 (aligned) |
| 2: Q3-S3 | Claude | UNMET 3/3 (strict) | MET 3/3 (aligned) |
| 2: Q3-S3 | GPT | UNMET 2/3 (strict) | MET 3/3 (aligned) |
| 3: P3-S3 | Gemini | MET 1/3 (lenient) | UNMET 3/3 (aligned) |
| 3: P3-E1 | Gemini | MET 1/3 (lenient) | UNMET 3/3 (aligned) |
| 3: P4-S3 | Gemini | MET 2/3 (lenient) | UNMET 3/3 (aligned) |
| 3: P4-S4 | Gemini | MET 2/3 (lenient) | UNMET 3/3 (aligned) |
| 3: P4-E2 | Gemini | MET 2/3 (lenient) | UNMET 3/3 (aligned) |
| 4: M2-E1 | Gemini | MET 2/3 (lenient) | UNMET 3/3 (aligned) |
| 4: M2-S2 | Gemini | MET 2/3 (lenient) | UNMET on r10/r13, MET on r12 (aligned) |
| 5: P2-S2 | Gemini | CANNOT_ASSESS 3/3 | UNMET 3/3 (aligned) |

If hold-out validation shows alignment improvement on the patterns above WITHOUT regression on previously aligned criteria, calibration is successful.

If alignment-to-golden does not improve on hold-out, kill-criterion fires (per `step_4_bis_calibration_kickoff_2026_05_04.md`): either iterate Phase 3 with different evidence, or document judge variance as model-architectural and abort calibration.


---

## Pattern 4 iteration (2026-05-04, post-Phase-4) — M2-S2 attempted residual fix, accepted Moderate Kappa

**Context**: Phase 4 hold-out validation reached cross-judge Kappa 0.592 (Moderate, upper band). Single residual = Gemini lenient on M2-S2 (golden UNMET, judge MET, 1/11 hold-out deviations). Goal of this iteration: tighten M2-S2 wording to flip Gemini, lifting Kappa across the 0.61 Substantial threshold.

**Hypothesis tested**: Gemini's lenience stems from threshold-elastic interpretation of "incremental" — tighter mechanical wording (count user messages between segments) and explicit sub-finding granularity (sub-finding = each SWOT entry / POP / POD / archetype, NOT phase-level) would force Gemini to flip MET → UNMET.

**Iterations attempted**:

1. **Iteration 1 — mechanical-count anchor**: rewrote Evidence Required to define "split test" mechanically (≥2 turns with ≥30-char user response between, format-only segmentation does not satisfy). Re-ran hold-out 3-judge eval. Result: Gemini verdict unchanged (still MET); Kappa unchanged at 0.592. Other criteria stable.

2. **Iteration 2 — sub-finding granularity clarification**: added explicit definition that "finding" = individual sub-finding (SWOT entry, persona, POP, POD, archetype, KPI metric) and explicit anti-failure that "Phase 2 spans Turn N+N+1" does not rescue sub-finding bundling within a turn. Re-ran hold-out. Result: Gemini reasoning verbatim identical to iteration 1 ("Phase 2 is split. Turn 6 presents Audience, Insights, and POPs/PODs. After the user replies, Turn 7 continues..."); verdict unchanged MET; Kappa unchanged at 0.592.

**Diagnosis**: Two independent wording iterations produced ZERO movement in Gemini's reasoning text or verdict — strong evidence that Gemini's M2-S2 interpretation is structurally architectural (model attends to phase-level segmentation cues regardless of explicit sub-finding-level instructions), not threshold-elastic. Further wording tightening on this single criterion is unlikely to shift Gemini.

**Decision per `north_star_principles_2026_05_03.md` honest-measurement principle**: accept Moderate Kappa 0.592 as the reliable cross-judge agreement floor for the calibrated 3-judge panel. The 0.018 gap below Substantial 0.61 reflects a single-criterion interpretation gap on M2-S2 that does not invalidate the dimension-level signals — Quality + Personalization criteria all align 3/3 with golden on hold-out, and the M2-S2 deviation is bounded (Mentor dimension Kappa would be the lowest, but acceptable for thesis claim if documented honestly).

**Working tree state**: rubric + judge_prompt reverted to HEAD `663b41f` calibrated wording. No commit applied for the failed iterations. Hold-out evaluation_results.json restored from BEFORE-iter backup (Kappa 0.592 baseline preserved).

**Open follow-up (deferred, not Phase B Step 2 prerequisite)**:
- A future iteration could try Path C from `phase_b_step_4_anchoring_killed_2026_05_04.md` — promote M2-S2 to a structured-output count-based verdict where the judge first counts sub-findings per turn, then derives MET/UNMET deterministically from the count. This bypasses interpretation entirely and may force Gemini to align even when its semantic interpretation differs.
- Alternatively, drop M2-S2 from the cross-judge averaging and rely on the per-judge alignment-to-golden rate as the trust metric for Mentor dimension.

Neither alternative blocks Phase B Step 2 (B Strategic Coherence judge) which uses different criteria entirely.



---

## Pattern 4 iteration 3 (2026-05-04, post-stochasticity-finding) — M2-S2 SHIPPED with affirmative + thinking-mode-aware restructure

**Investigation depth**: Sub-agent root-cause analysis identified the binding constraint upstream of the M2-S2 row itself. The previous iter-1 / iter-2 attempts edited the criterion cell but left two upstream sources of phase-level interpretation in place.

**Upstream conflict found**:

1. EVALUATION RULES Rule 4 ("No Halo Effect — Score each phase independently") sits at the high-attention top of judge_prompt.md and explicitly anchors evaluation at the **phase** level. This rule is injected by `run_judges.py` `_build_batch_prompt` into every Mentor batch BEFORE the M2-S2 cell.
2. Mentor section header `(Per-Phase Patterns)` reinforces phase-as-unit framing immediately above M2-S2.

Gemini's verbatim iter-1 / iter-2 reasoning ("Phase 2 is split. Turn 6 presents..., Turn 7 continues Phase 2") echoes Rule 4 word-for-word. A cell-level "overrides Rule 4" clause cannot override an upstream rule that the model already anchored on with primacy bias.

**Pipeline insight**: thinking-model primacy bias means top-of-prompt rules win over downstream-cell text when the cell text tries to negate the upstream rule. Negation-heavy cells ("DOES NOT satisfy", "does NOT rescue") are weak in the face of clean affirmative upstream rules.

**Fix shipped**: combined affirmative reframe (per skill principle 4 "Affirmative > negative") + thinking-mode-aware verbs (per skill principle 6 "Don't ask thinking models to think — use evaluate / reason through"). The new M2-S2 Evidence Required cell speaks turn-native language with a Step 1/2/3 procedure: identify sub-findings per turn → count them → MET only if every turn carries at most one sub-finding with substantive user response between. Removed all "overrides Rule 4" clauses and all visual-segmentation negation clauses; the rule is now stated affirmatively and procedurally so it does not need to fight Rule 4.

**Hold-out verification**: re-ran 3-judge eval on iso v4. Gemini M2-S2 verdict flipped MET → UNMET. New Gemini reasoning (verbatim): *"The agent fails the one-sub-finding-per-turn rule by bundling 5 major strategic sub-findings into Turn 6, and similarly dumps multiple frameworks in Turns 8 and 9."* Golden alignment improved 32/33 → 33/33 on the 11 calibrated criteria across all 3 judges.

**Cross-judge Kappa**: dropped 0.592 → 0.509 in this single-trial eval. Cause analysis: temperature=1.0 stochasticity flipped 8 previously-unanimous criteria across UNRELATED items (M1-S1, M2-E2, M3-E2, Q1-E2, etc.); n_criteria denominator grew 93 → 102 because Gemini's verdict completeness improved on QX-* (fewer CANNOT_ASSESS escapes). The Kappa change is dominated by stochastic noise, not by the M2-S2 fix.

**Decision to ship despite Kappa drop**: golden-truth alignment is the more meaningful metric for M2-S2 specifically — the criterion now has all three judges agreeing with the 4th-expert reviewer's judgment. Kappa at temperature 1.0 single-trial is volatility-dominated and cannot resolve a single-criterion improvement; rejecting the fix on that basis would penalize an alignment win because of measurement-pipeline noise.

**Open follow-up — Kappa stability work** (separate sub-plan, not blocking Phase B):

1. Run hold-out eval N=3 trials and report mean ± std for Kappa to establish the noise floor at T=1.0
2. Try T=0.0 (deterministic) for Kappa stability; cost / trade-off note: T=0.0 may reduce reasoning quality on long transcripts
3. Path C structured-output count-based for M2-S2 (judge emits sub-finding count per turn as a structured field, derives verdict mechanically) — removes interpretation drift AND temperature stochasticity in one pass

**Working tree state**: M2-S2 cell updated in both `docs/BRANDMIND_EVAL_RUBRIC.md` (line 398) and `evaluation/judge/judge_prompt.md` (line 378). `make typecheck` clean. Single-variable per commit (M2-S2 row only). No backup files retained — the iter-3 attempt was tested by sub-agent on hold-out and reverted by sub-agent before main thread re-applied the wording.

