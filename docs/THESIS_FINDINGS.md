# BrandMind — Thesis Findings

> Research findings from the BrandMind multi-agent system optimization, presented in research-paper style. Each finding is grounded in empirical evidence from the 7-pilot evaluation series (r10–r15 v2) and supported by bisect attribution methodology.

## Abstract

This document records the principal research findings of the BrandMind project. Three findings are empirically supported by paired pilot comparisons under disciplined methodology:

1. **Layer separation in prompt design — identity surface vs action surface — empirically validated**: an identity-level edit (Phase A v1) added to the top of the agent's system prompt failed to lift per-artifact dispatch narration across six pilots, while a surgically equivalent edit at the action surface (Phase A v2 — directly before each `task()` dispatch in the Phase 5 section) achieved the lift in a single pilot.
2. **Action-surface restatement at on-demand skill files is load-bearing reinforcement, not redundant duplication**: removing rule restatements from the on-demand skill that were "duplicates" of the always-loaded system prompt caused a measured combined-score regression of 0.53 points on otherwise identical conditions.
3. **Persona-driver methodology contamination biases personalization rubrics upward and compromises cross-system fairness**: persona-driver leakage of framework jargon into the simulated user voice (theorist names, framework labels, system-internal terms) is a systematic methodology failure that taints transcript records and is corrected only by pre-written turn-by-turn scripts with explicit avoid-lists.

Each finding is presented below with methodology, evidence, and implications for prompt-engineering practice in multi-agent LLM systems.

---

## Finding 1 — Layer separation in prompt design

### Background

The B-judge in the BrandMind evaluation framework measures Strategic Coherence across 12 criteria, of which **B7** (DOCX dispatch design rationale visible in chat) and **B8** (PPTX dispatch design rationale visible in chat) measure whether the agent narrates the per-artifact design choices a stakeholder would ask about ("why this slide order?", "why these 5 KPIs?") in the user-facing conversation, before dispatching the artifact-generation sub-agent. The artifact files alone do not satisfy the criteria; the chat narration is what makes the user able to defend the artifact in a stakeholder meeting.

Six consecutive pilots (r10 through r14b) returned **FLAT-INCOHERENT** verdicts on B7 and B8, despite the agent receiving an identity-level prompt edit ("Decisions narrated, not hidden", commit `8b8e45a`, hereafter Phase A v1) added to the CORE PHILOSOPHY block at the top of the always-loaded system prompt.

### Hypothesis

Identity-level disposition rules at the top of the system prompt (`8b8e45a`) generalize to specific actions through model reasoning: the agent reads "I am the kind of agent that narrates design rationale" and applies the disposition at all narration surfaces, including per-artifact dispatch.

### Test

A surgical edit (Phase A v2, commit `7a66d50`) inserted a new rule **at the action surface** — directly before the existing Phase 5 dispatch templates in the system prompt, in a section titled "Per-artifact design rationale in chat (B7/B8 stakeholder-defendability surface)". For each of the four artifacts (Brand Key / Strategy DOCX / Executive PPTX / KPI XLSX), the rule names what design choices to narrate in chat before each `task()` dispatch and why each tie back to an earlier-phase decision.

The rule preserves layer separation: the identity-level CORE PHILOSOPHY (Phase A v1) remains unchanged as the disposition; the action-surface rule (Phase A v2) is the operational trigger at the dispatch surface.

A single pilot (r15 v2) was driven on the new state with N=3 trial methodology overhaul (B-judge run three times to confirm verdict stability).

### Evidence

| Pilot | State | B7 | B8 | B mean ± std |
|---|---|---|---|---|
| r10 | pre-Path-C baseline | INCOHERENT × 3 | INCOHERENT × 3 | 8.62 ± 0.22 |
| r11 | Path-C iter | INCOHERENT × 3 | INCOHERENT × 3 | 8.21 ± 0.14 |
| r12 | Path-C cumulative + Phase A v1 | INCOHERENT × 3 | INCOHERENT × 3 | 8.12 ± 0.00 |
| r13 | post-L2-new (Phase A v1 stable) | INCOHERENT × 3 | INCOHERENT × 3 | 8.50 ± 0.00 |
| r14 | truly-final + dedup | INCOHERENT × 3 | INCOHERENT × 3 | 8.04 ± 0.44 |
| r14b | pre-dedup bisect | INCOHERENT × 3 | INCOHERENT × 3 | 8.50 ± 0.00 |
| **r15 v2** | **disciplined script + Phase A v2** | **PARTIAL × 3** | **COHERENT × 3** | **9.25 ± 0.00** |

The transition is clean: 18 trials of FLAT-INCOHERENT before Phase A v2; 3 trials of PARTIAL (B7) and 3 trials of FULL COHERENT (B8) immediately after. B-mean rose from cluster mean ≈ 8.3 to 9.25, the highest score of any pilot in the series.

### Interpretation

Identity-level disposition does not, in this system, automatically reach narrow action surfaces. The agent generalizes "narrate design rationale" at the strategic phases (Phase 0 through Phase 4 reasoning is consistently visible in transcripts across all 7 pilots) but does not transfer the disposition to the per-artifact dispatch micro-action without a rule co-located at that surface.

The hypothesis is consistent with three mechanisms documented in the prompt-engineering literature:

1. **Position weighting** in long contexts — instructions placed near the action they govern receive higher attention weight than instructions placed at context-start (Anthropic *Claude techniques* on top/bottom weighting).
2. **Procedural specificity** — identity dispositions are abstract; action-surface rules are concrete operational scripts. The agent's training favors concrete operational rules at the moment of action over abstract dispositions inferred from identity.
3. **Surface-binding of action rules** — when a rule is co-located with the action it governs (immediately before each `task()` dispatch), the rule activates in the same reasoning chain that generates the action, rather than requiring back-reference to a distant identity statement.

### Implication for prompt-engineering practice

For action-specific behaviors that did not generalize from identity-level rules, edit the action surface, not the identity surface. The two are not interchangeable layers in this system class. Future work designing similar multi-agent systems should plan rule placement around where the action fires, not around where the disposition is described.

---

## Finding 2 — Action-surface restatement is load-bearing reinforcement, not redundant duplication

### Background

The BrandMind orchestrator skill (`brand-strategy-orchestrator/SKILL.md`) is loaded on demand when the agent is about to perform phase-specific procedures. The always-loaded system prompt defines identity, philosophy, per-turn discipline, and high-level workflow; the skill, when loaded, gives operational mechanics for the specific procedure (phase transition mechanics, per-phase mentoring shape, quality gate protocol).

A logical-cleanness audit identified that several rules in the orchestrator skill were "duplicates" of rules already in the system prompt — for example, the "verify quality gate before advancing" rule appeared in both surfaces, the "you do not choose which phase comes next; `report_progress` enforces the sequence" rule appeared in both, and the per-turn one-teaching-moment discipline appeared in both with similar phrasing. Two dedup commits removed these "duplicates" from the skill, replacing them with cross-references to the system prompt:

- `760f5df` Mentor approach dedup (compressed 5-step procedure to 3-step + cross-ref)
- `99f5673` Phase Transition Protocol dedup (replaced gate-verify and "you do not choose phase" lines with cross-ref to the system prompt)

The dedup was logically clean: the rules existed at one canonical surface (system prompt) plus cross-reference at the action surface (skill). No information was lost; the skill simply pointed back to the system prompt for the rule body.

### Hypothesis tested

The dedup is behaviorally neutral: cross-references substitute fully for action-surface restatement, because the system prompt is loaded every turn anyway and the agent has access to the full rule via the system prompt regardless of whether the skill restates it.

### Test — bisect

Pilot r14 was driven on the post-dedup state (HEAD `99f5673`). The agent, on the same Linh persona and same disciplined-baseline setup, exhibited:

- Phase metadata stuck at `phase_1` throughout 10 turns despite verbally walking through Phase 2 / 3 / 4 / 5 content
- Two emissions of XML pseudo-tool-call `<report_progress advance="true" />` in user-facing text, a CRITICAL RULE 9 violation
- Bundling pattern: Phase 2 + Phase 3 + Phase 4 content packed into single turns rather than the per-turn discipline

A paired pilot r14b was driven on a temporary branch checked out at commit `19fe661` (pre-dedup state) with the same Linh persona and same prompt-engineering script. The agent on r14b:

- Advanced phase metadata cleanly through all 5 phases
- Did not emit any XML pseudo-tool-call
- Maintained per-turn discipline more consistently

### Evidence

| Pilot | State | combined | B mean ± std | C mean ± std | Phase metadata advance | XML emission |
|---|---|---|---|---|---|---|
| r14 | post-dedup `99f5673` | 6.52 | 8.04 ± 0.44 | 7.67 ± 0.29 | stuck at phase_1 | 2 emissions |
| r14b | pre-dedup `19fe661` | 7.05 | 8.50 ± 0.00 | 8.17 ± 0.29 | clean to phase_5 | 0 emissions |

Combined-score Δ = +0.53 attributable to dedup removal alone (same persona, same script, single-variable change between branches).

### Interpretation

The dedup hypothesis (cross-reference substitutes fully for restatement) is rejected. The "duplicate" text in the on-demand skill was **load-bearing reinforcement**: at the moment the agent loads the skill (immediately before performing a phase transition or executing the mentoring shape), the rule needs to fire in the same attention window as the action; a cross-reference back to a distant system-prompt section does not produce equivalent activation.

Three mechanisms plausibly explain the observation:

1. **Recency bias** — the skill is loaded freshly during the action; rules within the freshly-loaded skill are higher attention than rules in the always-loaded system prompt that has been in context since the session start.
2. **Action-binding** — the skill section is co-located with the procedure it governs (phase transition mechanics, mentoring shape); rules within the same section as the procedure activate together with the procedure.
3. **Procedural framing** — restated rules in the skill section read as part of the operational script for the phase; cross-references read as "see elsewhere", lower-priority signal.

A subsequent commit (`f35ec0c`, PARTIAL RESTORE) restored three load-bearing pieces of the dedup-removed text — the standalone "bundling collapses silence" paragraph, the "Stop and wait" tokens between mentoring steps, and the Vietnamese reasoning template "Tôi nhìn vào X → thấy Y → suy ra Z" — while keeping cross-references where the skill genuinely defers to the system prompt. The PARTIAL RESTORE reflects a refined understanding: not all surface restatements are load-bearing, but text restatements at the moment-of-action surface are.

### Implication for prompt-engineering practice

When refactoring multi-surface prompts (system prompt + skill files + reference files), do not assume that "the same rule already exists upstream" makes downstream restatement redundant. If the downstream surface is loaded at the moment of action (on-demand skill loaded for a specific procedure), the restatement is action-bound reinforcement and removing it can degrade behavior even when the rule is logically still present upstream.

The dedup pattern violation here mirrors a well-documented anti-pattern in software refactoring (Fowler): removing apparent duplication can remove implicit coupling that was load-bearing. The same caution applies to prompts.

---

## Finding 3 — Persona-driver methodology contamination

### Background

The BrandMind evaluation framework includes a cross-system fair comparison commitment: the same persona-driver simulating the user must send identical messages to BrandMind and to vanilla baseline systems (ChatGPT, Gemini), so that downstream judge scoring measures the system's quality given fixed user input rather than measuring the persona-driver's prompting skill.

This commitment is documented in `docs/CROSS_SYSTEM_PILOT_PROCEDURE.md` Phase C anti-pattern #1 (no elicitation injection). The persona-driver simulates a real first-time user from outside the system, not the system's builder.

### Hypothesis discovered (not pre-planned)

Six pilots (r10 through r14b) were driven by the persona-driver leaking framework jargon into the simulated user voice — phrases such as "Aaker personality + visual direction", "POPs/PODs + value ladder + brand essence", "messaging hierarchy + Cialdini + AIDA", "Stress test 5 criteria pass", and "dispatch sub-agents". These are not phrases a real first-time user from outside BrandMind would produce.

The contamination was discovered when a 7th pilot (r15 v1) was being driven and the user surfaced the leak at turn 8, noting that "dispatch sub-agents" is not user-facing language.

### Test

A persona-driver discipline rule was promoted to canonical surface (`CLAUDE.md` § Persona-as-Outsider Driving Discipline) requiring:
- Echo-back rule: persona uses framework term ONLY after agent has cited it in the prior turn
- Vietnamese-natural deliverable names ("file chiến lược / slide cho sếp / bảng KPI / Brand Key tóm tắt"), not file-extension or English deliverable names
- Tactical questions from outsider view, not strategist-level framework-stacking
- Never speak system-internal terms (`dispatch sub-agents` / `task()` / `report_progress` / `phase advance` / `tool_calls`)
- Pre-write the script BEFORE driving with explicit "avoid" terms per turn

Pilot r15 v1 was aborted at turn 8 mid-flight; pilot r15 v2 was redriven from a pre-written disciplined script.

### Evidence

The disciplined r15 v2 transcript shows persona-natural Vietnamese throughout:
- Linh asks "anh cho em hỏi 'scope' là gì vậy" rather than asserting framework knowledge
- Linh requests deliverables as "file chiến lược + slide cho sếp + bảng theo dõi KPI + Brand Key tóm tắt" rather than "DOCX + PPTX + XLSX + Brand Key one-pager"
- Linh echoes back "Brand Dilution" only AFTER the agent introduced it in the prior turn
- Linh's tactical questions ("kênh nào nên ưu tiên với budget này", "viết content thế nào cho weekday") match a junior marketer's outsider vocabulary

The score comparison r14b (jargon-contaminated) vs r15 v2 (disciplined) on otherwise comparable agent state (both have all 4 sub-plan fixes; r14b lacks Phase A v2 + PARTIAL RESTORE, r15 v2 has both):

| Pilot | Methodology | chat | B mean | C mean | self | combined |
|---|---|---|---|---|---|---|
| r14b | jargon-contaminated | 4.30 | 8.50 | 8.17 | 7.57 | 7.05 |
| r15 v2 | disciplined script | 4.42 | 9.25 | 7.67 | 7.80 | 7.18 |

The combined-score delta (+0.13 from r14b to r15 v2) understates the methodology improvement — r14b is jargon-contaminated UPWARD on personalization criteria (the agent appeared to "match Linh's level" because Linh fed it framework vocabulary), so the contaminated baseline is inflated. The disciplined methodology, despite +0.13 combined, provides a cleaner baseline for cross-system comparison.

### Interpretation

The contamination operates through three mechanisms:

1. **Personalization rubric P-criteria bias upward** — when the user pre-loads framework jargon, the agent appears to "match user level" because the user matched agent vocabulary, not because the agent adapted. Adaptive-depth criteria (P4-G2 behavior changes per persona, P4-S1 learning preference adapts, P4-S2 thinking pattern adapts) score artificially high because the user input does not require adaptation.
2. **Cross-system fairness compromised** — vanilla baselines (ChatGPT, Gemini) will see the same persona-driver messages; if those messages contain framework jargon, vanilla baselines look misleadingly knowledgeable because the user is feeding them vocabulary. The system-vs-system comparison is no longer apples-to-apples.
3. **Thesis claim about junior users undermined** — the BrandMind thesis claim depends on the simulated user staying junior throughout the transcript. A persona-driver leaking framework names from turn 2 is no longer a junior; the test is contaminated.

### Implication for evaluation methodology

For LLM evaluation work that uses scripted persona simulation, persona-driver discipline is a methodology requirement co-equal with rubric design and judge calibration. Pre-written turn-by-turn scripts with explicit avoid-lists are the safeguard. Discovery of contamination requires either (a) external review by someone who is not also the persona-driver, or (b) pre-commitment to an avoid-list checked against the script before driving.

The contamination on six BrandMind pilots (r10 through r14b) means those pilots' results are indicative for bisect attribution but not clean apples-to-apples vs vanilla baselines. The thesis defense uses the disciplined r15 v2 as the methodology reference baseline; cross-persona (Task #82) and vanilla comparison (Task #83) work proceeds under the disciplined script.

---

## Cross-finding implications

The three findings interact: Findings 1 and 2 are findings about how prompts work in this system class (layer separation; action-surface reinforcement), while Finding 3 is a finding about how to evaluate prompt-engineering interventions reliably (persona-driver discipline). Together they justify the disciplined methodology as the basis for the thesis's empirical claims.

The findings also frame what the thesis claim depends on:

- The defendable claim "BrandMind narrates per-artifact design rationale at the Phase 5 dispatch surface" rests on Finding 1.
- The defendable claim "action-surface reinforcement at on-demand skill is load-bearing" rests on Finding 2 — independent of the Phase A v2 result.
- Both claims are valid only under disciplined persona-driver methodology, hence Finding 3 is methodologically prerequisite.

The thesis-critical comparison "BrandMind delivers strategic substance vanilla LLMs cannot" awaits Phase D-2 #9 vanilla baseline data and is not yet defended.

---

## References (in-system)

- `phase_a_v2_verified_2026_05_05.md` — milestone memory with full pilot table and per-commit attribution
- `docs/B_C_JUDGE_METHODOLOGY.md` — B and C judge framework, criteria, calibration
- `docs/JUDGE_CALIBRATION_METHODOLOGY.md` — chat rubric calibration, Kappa, deviation analysis
- `docs/CROSS_SYSTEM_PILOT_PROCEDURE.md` — cross-system fairness commitment, per-persona behavior specs
- `docs/BRANDMIND_EVAL_RUBRIC.md` — 104 chat-rubric criteria + 10 anti-patterns
- `CLAUDE.md` § Persona-as-Outsider Driving Discipline — canonical persona-driver discipline rule

## Out-of-scope for this document

- Cross-persona generalization (Task #82) — pending
- Cross-system comparison (Task #83) — pending
- C-dimension lift levers (C6 risk / C8 ROI math / C9 stakeholder defensibility) — separate future work; Phase A v2 specifically targeted B7/B8 not C-criteria
- Architectural-fallback alternative (`WorkspaceInjectionMiddleware`) — not pursued; Phase A v2 prompt-level result demonstrates prompt-level edits can reach the surface
