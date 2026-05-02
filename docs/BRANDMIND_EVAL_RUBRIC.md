# BrandMind AI — Evaluation Rubric v1.0

> **Purpose**: Concrete, evidence-based rubric for evaluating BrandMind's brand strategy agent across Quality, Mentoring, and Personalization. Designed to predict real-world user experience — not just benchmark performance.
>
> **Last Updated**: 2026-03-30
> **Status**: v1.0 — Ready for Claude-as-Judge evaluation
> **Research Base**: `docs/BRANDMIND_EVAL_RESEARCH.md`

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [Evaluation Scope & Input](#2-evaluation-scope--input)
3. [Scoring Mechanics](#3-scoring-mechanics)
4. [Dimension 1: Strategy Quality (50%)](#4-dimension-1-strategy-quality-50)
5. [Dimension 2: Mentoring Quality (30%)](#5-dimension-2-mentoring-quality-30)
6. [Dimension 3: Personalization Quality (20%)](#6-dimension-3-personalization-quality-20)
7. [Anti-Patterns (Negative Criteria)](#7-anti-patterns-negative-criteria)
8. [Evaluation Procedure](#8-evaluation-procedure)
9. [Score Interpretation](#9-score-interpretation)
10. [Criterion Summary](#10-criterion-summary)

---

## 1. Design Principles

### 1.1 Core Philosophy

This rubric exists to answer one question: **"If this agent passes, would a real user get brand strategy equivalent to what a junior brand manager (with senior review) would produce?"**

### 1.2 Anti-Gaming Design

The biggest risk is an eval that looks great on paper but fails in practice. Every criterion is designed to resist gaming:

| Risk | How Criteria Resist It |
|------|----------------------|
| **Generic output passes** | Criteria require business-specific evidence. Specificity test: "Would this advice work unchanged if we swapped the brand name?" — if yes, it fails. |
| **Fabricated research** | Criteria check whether research output is specific, detailed, and verifiable. Vague or unverifiable claims = UNMET. |
| **Framework name-dropping** | Criteria evaluate APPLICATION of frameworks to user's business, not mere mention of Keller/Kotler/Sharp. |
| **Length = quality bias** | No criterion rewards verbosity. Anti-pattern AP-6 penalizes information overload. |
| **Sycophantic scoring** | Anti-patterns are explicit deductions. Every judgment requires evidence citation. UNMET examples provided for calibration. |
| **Halo effect across phases** | Each phase evaluated independently. Cross-phase coherence is a SEPARATE criterion group. |

### 1.3 Criterion Design Rules

Every criterion follows these rules:
- **Binary**: MET / UNMET / CANNOT_ASSESS — no partial credit (CheckEval finding: binary decomposition has highest inter-judge consistency)
- **Evidence-required**: Judge MUST cite specific transcript quote as evidence
- **Failure-defined**: Every criterion includes "Common Failure" — what UNMET looks like in practice
- **Specificity-tested**: Criteria that a generic chatbot could satisfy are too weak

---

## 2. Evaluation Scope & Input

### 2.1 What Gets Evaluated

| Input | Purpose |
|-------|---------|
| Full session transcript (user messages + agent responses) | Evaluate behavior, teaching, decision process, personalization, strategy quality |

**Why transcript only (no workspace files)?** The rubric evaluates what the user EXPERIENCES, not what the agent records internally. If the agent personalizes well, it shows in the conversation. If the strategy is coherent, it shows in cross-phase references. Workspace files are implementation details — evaluating them would be unfair to systems that don't have workspace (baselines) and would test internal process rather than user-facing output. All criteria have been rewritten to assess behavior from the transcript.

### 2.2 Evaluation Unit

One complete or partial brand strategy session (Phase 0 through last completed phase).

- **Partial sessions**: Score only assessed phases; normalize to assessed criteria count
- **Phase 0.5**: Only scored for rebrand sessions; CANNOT_ASSESS for new_brand scope
- **Sub-agent work**: Evaluate the output the main agent PRESENTS, not sub-agent internals (user cares about results, not process)

---

## 3. Scoring Mechanics

### 3.1 Criterion Types

| Symbol | Type | Meaning |
|--------|------|---------|
| `GATE` | Gate | MUST be MET for dimension score > 5.0. Any gate failure = dimension capped. |
| `STD` | Standard | Each MET criterion contributes to score in 6.0–8.0 range. |
| `EXCEL` | Excellence | Required for 9.0–10.0. Represents "experienced brand manager" level. |

### 3.2 Dimension Score Formula

```
1. gates_met = count of MET gate criteria
   gates_total = count of assessed gate criteria (CANNOT_ASSESS excluded)

2. IF gates_met < gates_total:
     dimension_score = (gates_met / gates_total) × 5.0
     // Capped at 5.0 — fundamentals are broken

3. IF gates_met == gates_total (all gates pass):
     standard_ratio = standard_met / standard_assessed  (0 if none)
     excellence_ratio = excellence_met / excellence_assessed  (0 if none)
     dimension_score = 6.0 + (standard_ratio × 2.0) + (excellence_ratio × 2.0)
     // Range: 6.0 (gates only) → 8.0 (all standard) → 10.0 (all excel)

4. anti_pattern_deductions = instances × 0.5  (max 2.0 per dimension)
   final_score = max(0, dimension_score - anti_pattern_deductions)
```

### 3.3 Overall Score

```
overall = Quality × 0.50 + Mentor × 0.30 + Personalization × 0.20

QUALITY GATE: If Quality < 7.0 → overall capped at 6.0
  (Quality is the foundation — without it, mentor and personalization are meaningless)

PASS THRESHOLD: 8.0 / 10.0
```

### 3.4 Score Calibration

| Scenario | Expected Score | Interpretation |
|----------|---------------|----------------|
| All gates pass, 0 standard, 0 excellence | 6.0 | Basic competence only |
| All gates pass, 50% standard, 0 excellence | 7.0 | Good but inconsistent |
| All gates pass, 100% standard, 0 excellence | 8.0 | Solid professional quality (TARGET) |
| All gates pass, 100% standard, 50% excellence | 9.0 | Strong — exceeds expectations |
| All gates pass, 100% standard, 100% excellence | 10.0 | Exceptional — consultant level |
| 1 gate fails, everything else perfect | ≤ 5.0 | Fundamental flaw blocks quality |

---

## 4. Dimension 1: Strategy Quality (50%)

*Evaluates: Does the strategy output solve the user's actual business problem? Are recommendations actionable, evidence-based, and specific? Would a marketing manager approve this?*

### 4.1 Phase 0 — Business Problem Diagnosis

#### GATE Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q0-G1 | Problem statement references ≥2 specific business details (location, competition, current state, revenue pattern, customer behavior, etc.) | Quote the problem statement; identify the specific details | Generic "increase brand awareness" or "grow customer base" without business context |
| Q0-G2 | Scope classification includes explicit reasoning — not just a label | Find where agent explains WHY this scope (new_brand/refresh/repositioning/rebrand) applies to this specific case | Agent outputs "Scope: NEW_BRAND" without justification |
| Q0-G3 | User's actual business constraints captured and documented (budget, timeline, team size, market conditions) | Check against user's stated information; verify all key constraints present in diagnosis | Missing budget tier or location or key competitive constraint |

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q0-S1 | Agent asks ≥2 probing follow-up questions beyond initial template (5W1H) questions | Identify questions that dig deeper into initial answers — not just collecting next item on checklist | Agent runs through question list without follow-up on surprising or incomplete answers |
| Q0-S2 | Business problem is framed as strategic opportunity/gap — not user's complaint restated | Compare user's initial description vs agent's problem formulation; agent must add analytical value | Agent parrots user's exact words as the "problem statement" |
| Q0-S3 | Phase 0 synthesis connects business details to strategic implications | Find where agent draws insights from collected information (not just organizing it) | Raw information dump without analysis or "so what" |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q0-E1 | Agent identifies a strategic tension or paradox the user hadn't articulated (e.g., "casual name vs premium pricing" or "weekday traffic gap at premium location") | Find insight that is NOT in user's input — must be agent's original observation | Agent only reflects back what user explicitly said |
| Q0-E2 | Problem framing accounts for external market dynamics (not just internal business state) | Check for competitive landscape, market trends, or category dynamics in diagnosis | Problem defined purely from internal perspective: "We need more customers" |

---

### 4.2 Phase 0.5 — Brand Equity Audit (Rebrand Only)

*CANNOT_ASSESS for new_brand scope sessions.*

#### GATE Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q05-G1 | Brand inventory covers all 3 audit dimensions: visual, verbal, AND experiential | Check for explicit coverage of each dimension | Only visual audit (logo, colors); verbal (name, tagline) and experiential (service, ambiance) missing |
| Q05-G2 | Preserve-Discard Matrix has clear justification for each decision | Check reasoning per element in the matrix | "Keep logo ✓ / Discard tagline ✗" without explaining WHY |

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q05-S1 | Perception assessment presents specific, verifiable data (real review quotes, social media metrics, named sources) — not agent assumptions | Check whether agent cites specific data points, platforms, or sources when discussing brand perception | "Customers likely perceive the brand as..." with no specific review quotes, metrics, or named sources |
| Q05-S2 | Equity sources identified distinguish between brand equity and category equity | Check if agent separates what's unique to THIS brand vs generic category expectation | "Customers love the food quality" listed as brand equity (it's table-stakes for the category) |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q05-E1 | Audit reveals strategic tension between current equity and desired direction | Find where agent identifies what must change vs what must be preserved, and the tension between them | Audit is purely descriptive inventory without strategic implications |

---

### 4.3 Phase 1 — Market Intelligence & Research

#### GATE Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q1-G1 | ≥3 competitors profiled are REAL, verifiable businesses — not fictional or placeholder | Competitor names should be specific, real businesses in the user's stated location and category. Judge uses own knowledge to assess plausibility. | Made-up competitor names, "Competitor A/B/C", or businesses from wrong location |
| Q1-G2 | Target audience definition includes BOTH demographic AND psychographic/behavioral attributes | Find audience definition; verify both types present and connected | Demographics only: "25-40, income level B+" without motivations, behaviors, or decision drivers |
| Q1-G3 | ≥1 customer insight is non-obvious — not a truism anyone could state without research | Evaluate: would you know this insight WITHOUT doing research? If yes → too generic | "Customers want good food at reasonable prices" or "People prefer convenient locations" |
| Q1-G4 | Research covers user's specific geographic market — not generic national/global data | Check location specificity: district-level or city-level, not just "Vietnam" | Generic "Vietnam F&B market is growing" without local market specifics |

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q1-S1 | SWOT entries are specific to THIS business — would NOT apply unchanged to a random competitor | Substitution test: replace brand name with competitor → if entry still holds, it's too generic | "Strength: Good product quality" / "Threat: Economic downturn" (applies to everyone) |
| Q1-S2 | Perceptual map uses dimensions relevant to user's actual competitive dynamics — not default axes | Check if map axes reflect real differentiators in this market | Default "Price vs. Quality" axes without justification for why these dimensions matter |
| Q1-S3 | Competitive analysis identifies specific strategic gaps/opportunities (white space) | Find explicit gap identification with reasoning | Describes competitors but concludes with "there are opportunities" without specifying what or where |
| Q1-S4 | Research output is specific, detailed, and verifiable — not vague assertions presented as findings | Check whether research claims include specific data: named sources, concrete numbers, real business names, verifiable details. Vague "research shows..." without specifics = likely fabricated. | Agent presents "According to research..." or "Market data shows..." followed by generic statements with no specific data, numbers, or named sources |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q1-E1 | Strategic synthesis connects ≥3 separate research findings into a coherent narrative (not just bullet list) | Find synthesis section; check cross-referencing between findings | Disconnected bullet points: "Finding 1... Finding 2... Finding 3..." without narrative thread |
| Q1-E2 | Research uncovers information the user didn't already know or provide | Identify at least one finding absent from user's initial input | Research only confirms and elaborates what user already said |

---

### 4.4 Phase 2 — Brand Positioning

#### GATE Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q2-G1 | Positioning statement references ≥2 specific findings from Phase 1 research (traceable link) | Trace positioning elements back to Phase 1 evidence by citation or direct reference | Positioning created from scratch as if Phase 1 didn't happen |
| Q2-G2 | Point of Difference (POD) is genuinely differentiating — not table-stakes for the category | Evaluate: do major competitors in this market already offer this? If yes → it's a POP, not POD | "Fresh ingredients" / "Friendly service" / "Good ambiance" as differentiator in premium dining |
| Q2-G3 | Stress test addresses ≥3 of 5 criteria (Deliverability, Relevance, Differentiation, Credibility, Sustainability) with specific reasoning — not just a checklist | Check each stress test answer for specific evidence or reasoning | "Deliverable: Yes ✓" without explaining HOW the brand can deliver this |

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q2-S1 | Value ladder connects all 4 levels: product attributes → functional benefits → emotional benefits → outcome/self-expressive benefits | Check for all 4 levels AND logical connections between them | Missing emotional or outcome level; or levels present but not logically connected |
| Q2-S2 | Brand essence/mantra is ≤5 words and captures the positioning distinctly | Check length and uniqueness — could this essence belong to a competitor? | Too long (a sentence, not a mantra) or too generic ("Quality Dining Experience") |
| Q2-S3 | Positioning is implementable within user's stated budget tier | Check if positioning requirements match budget reality | Premium experiential positioning requiring multi-million marketing spend for a 50-80M VND/month budget |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q2-E1 | Agent challenges or refines user's initial positioning preference with evidence-based reasoning | Find where agent pushes back or improves on user's idea (not just validates) | Agent accepts user's first positioning suggestion without testing or alternative |
| Q2-E2 | Positioning accounts for different usage occasions or audience segments within the brand | Check for occasion-based or segment-based nuance (e.g., weekday business lunch vs. weekend family dining) | One-size-fits-all positioning that ignores distinct usage contexts |

---

### 4.5 Phase 3 — Brand Identity & Expression

#### GATE Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q3-G1 | Brand personality aligns with Phase 2 positioning — not contradictory | Cross-check: does personality reinforce or undermine the positioning? | Playful, irreverent personality for a brand positioned on prestige and trust — without explicit justification for the contrast |
| Q3-G2 | Voice guidelines include specific do/don't examples grounded in this brand's context | Check for concrete example phrases (not abstract adjectives) | "Voice should be warm, professional, and approachable" without showing what that sounds like |
| Q3-G3 | Visual direction is specific enough to brief a designer — includes color direction, typography style, and imagery mood | Check for actionable specifications a designer could execute | "Modern and elegant design" without specifying color palette direction, type style, or imagery references |

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q3-S1 | Brand archetype selection includes reasoning tied to user's business context and positioning | Check justification connects archetype → positioning → business reality | Archetype assigned because "it sounds right" or pure personality quiz without strategic rationale |
| Q3-S2 | Generated mood board/concept images align with the stated identity direction | Compare image aesthetics vs written identity brief — do they match? | Premium brand identity brief but casual/generic stock-photo-style images generated |
| Q3-S3 | Distinctive Brand Assets (DBA) strategy identifies ≥3 potential assets beyond just the logo | Count DBA candidates (color ownable, sonic, shape, character, pattern, etc.) | Only logo discussed; other sensory/visual assets ignored |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q3-E1 | Identity elements account for cultural/local context (Vietnamese market, dining culture, language nuances) | Check for culturally-informed decisions, not Western defaults | Western-centric identity system (e.g., English-primary naming) for a Vietnamese-market brand |
| Q3-E2 | Naming analysis evaluates multiple dimensions: meaning, sound, memorability, cultural connotation, URL/social availability | Check naming discussion for multi-dimensional evaluation | Name selected based on meaning alone, ignoring phonetics or cultural associations |

---

### 4.6 Phase 4 — Communication Framework

#### GATE Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q4-G1 | Value proposition directly flows from Phase 2 positioning — traceable link, not reinvented | Trace value prop elements to positioning statement; should be a natural extension | Value proposition created fresh, ignoring or contradicting the positioning established in Phase 2 |
| Q4-G2 | Channel strategy reflects where the target audience actually IS — with evidence or reasoning | Check for audience-channel matching with data from research or logical reasoning from Phase 1 audience profile | Default "Use TikTok, Instagram, Facebook" without explaining WHY these channels for THIS audience |
| Q4-G3 | Content pillars are specific to THIS brand — would NOT work unchanged for a competitor | Substitution test: swap brand name → do pillars still work? If yes → too generic | Universal pillars: "Behind the Scenes" / "Customer Stories" / "Tips & Tricks" / "Promotions" |

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q4-S1 | Messaging hierarchy has clear structure: primary message, secondary messages, and proof points | Check for explicit layered structure, not a flat list of messages | Flat list of 10 messages without hierarchy or priority |
| Q4-S2 | ≥2 Cialdini principles applied with specific implementation examples for this brand | Find principle + concrete brand-specific application (not just naming the principle) | "Use Social Proof" without specifying HOW (what type, what channel, what content format) |
| Q4-S3 | AIDA flow has distinct messages per stage — each stage serves a different communication purpose | Compare messages across Attention/Interest/Desire/Action — must be meaningfully different | Same core message slightly reworded per stage; or only 1-2 stages developed |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q4-E1 | Communication framework includes ≥2 specific content/campaign examples (not just strategy-level description) | Find concrete content examples: actual post concepts, campaign ideas, or messaging scripts | Pure strategic framework without any execution-level examples |
| Q4-E2 | Channel strategy includes operational details: frequency, format types, and resource requirements | Check for "what, how often, what format, who creates it" per channel | "Post regularly on Instagram" without frequency, format, or resource planning |

---

### 4.7 Phase 5 — Strategy Plan & Deliverables

#### GATE Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q5-G1 | Brand Key one-pager is internally consistent — all elements (Root Strength, Target, Insight, Benefits, POD, Essence) align with each other and with prior phases | Cross-check Brand Key fields for contradictions with each other and with Phase 2-4 decisions | Brand Key contains elements from different strategic directions (e.g., Phase 2 positioning ≠ Brand Key discriminator) |
| Q5-G2 | ≥5 KPIs defined with BOTH measurement method AND baseline/target — not just metric names | Check each KPI: is there a way to measure it? What's the starting point? What's the goal? | "Brand Awareness" / "Customer Satisfaction" listed without measurement method or targets |
| Q5-G3 | Implementation roadmap is explicitly tied to user's budget tier — activities match financial reality | Check if roadmap spending aligns with stated budget constraints | Enterprise-level roadmap (influencer campaigns, PR agency, event series) for starter budget without acknowledging constraint |

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q5-S1 | Roadmap items are explicitly prioritized: Must Do vs Nice to Have (or equivalent) | Check for priority labels or tiering | Flat list of 20 action items without prioritization — user doesn't know where to start |
| Q5-S2 | Strategy document covers all completed phases coherently — not just Phase 5 content | Check document for Phase 0 problem, Phase 1 research, Phase 2 positioning, Phase 3 identity, Phase 4 communication | Document only contains final-phase deliverables; earlier strategic foundation missing |
| Q5-S3 | Measurement plan includes review cadence — WHEN and HOW OFTEN to check KPIs | Check for temporal structure: weekly/monthly/quarterly review plan | KPIs defined but "measure regularly" without schedule |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| Q5-E1 | Roadmap includes risk considerations or contingency thinking | Check for "what if" scenarios or risk-aware planning | Linear plan assuming 100% execution — no acknowledgment of potential obstacles |
| Q5-E2 | Deliverables are stakeholder-ready — could be presented to a boss/investor without heavy editing | Assess presentation quality: structure, clarity, professional tone | Raw strategy notes that need significant reformatting before showing to stakeholders |

---

### 4.8 Cross-Phase Coherence

*Evaluated across all completed phases.*

#### GATE Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| QX-G1 | **Golden Thread**: Can trace a logical chain from Phase 0 problem → through each phase → to final solution without contradiction | Walk the chain: problem → research → positioning → identity → communication → plan. Each link must follow from the previous. | Strategy pivots at Phase 3 without acknowledging the change, or Phase 5 deliverables don't address Phase 0 problem |
| QX-G2 | No unresolved contradictions between phases | Search for conflicting recommendations across phases | Phase 3 brand personality contradicts Phase 2 positioning archetype; or Phase 4 messaging doesn't reflect Phase 3 voice |

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| QX-S1 | Each phase explicitly builds on previous phase's outputs — references or cites earlier decisions | Check for cross-phase references (e.g., "Building on our positioning from Phase 2...") | Each phase feels like a fresh start; no backward references |
| QX-S2 | Progressive depth: later phases are more specific/tactical than earlier strategic phases | Compare abstraction level: Phase 0 (strategic) → Phase 5 (tactical) gradient | Phase 5 is as abstract and high-level as Phase 0; no concretization through phases |
| QX-S3 | Agent maintains strategically consistent narrative — decisions referenced in later phases match what was actually discussed and agreed in earlier phases | Check: when agent references a prior decision (e.g., "our positioning from Phase 2"), does it match what actually happened in Phase 2? | Agent references a decision that was never made, or misquotes an earlier agreement — strategic narrative drifts from actual conversation |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| QX-E1 | Agent proactively surfaces connections between non-adjacent phases (e.g., Phase 1 insight → Phase 4 campaign; Phase 0 constraint → Phase 5 roadmap) | Find cross-phase connections that skip at least one intermediate phase | Only references Phase N-1, never reaches back to earlier phases |
| QX-E2 | Overall strategy narrative is compelling enough to present to stakeholders as a coherent story | Holistic assessment: does the strategy tell a story from problem to solution? | Strategy is technically correct but reads as disconnected checklist items, not a persuasive narrative |

---

## 5. Dimension 2: Mentoring Quality (30%)

*Evaluates: Does the agent teach the user brand strategy thinking — not just hand them a document? Would the user be able to explain and defend the strategy to their boss?*

*Key research finding: Expertise-Pedagogy Gap (MathTutorBench) — being good at strategy ≠ being good at teaching strategy. This dimension catches that gap.*

### 5.1 Teaching Effectiveness (Per-Turn Patterns)

#### GATE Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| M1-G1 | Agent explains underlying concepts BEFORE presenting strategic decisions — Explain → Do, not just Do | Check ordering: does explanation precede recommendation? In ≥80% of major decisions. | Jumps to "Your positioning should be X" without first teaching what positioning is and why it matters |
| M1-G2 | Agent does NOT use marketing jargon without explanation — or adapts terminology to user's demonstrated level | Search for unexplained technical terms. 1-2 instances acceptable if minor; pattern of unexplained jargon = UNMET. | "We need to establish POPs and PODs in the consideration set" to a user who hasn't encountered these terms |

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| M1-S1 | Agent uses relevant real-world examples or analogies when explaining concepts (not pure textbook definition) | Find ≥3 concrete examples across the session | Every explanation is Wikipedia-style: "Positioning is defined as the act of designing a company's offering..." |
| M1-S2 | Agent asks substantive understanding-check questions — not just "Does that make sense?" | Find verification questions that test comprehension (e.g., "Given what we discussed, which of these directions do you think fits your situation better?") | Only asks "Do you understand?" / "Shall I continue?" / "Any questions?" — rhetorical checks |
| M1-S3 | Agent explains "WHY" behind strategic decisions — rationale accompanies every major recommendation | Check major decisions for reasoning: the recommendation + the logic behind it | "I recommend X" without "because Y" — user follows blindly without understanding |
| M1-S4 | Explanations use user's language and context — Vietnamese terms, local market references, user's industry | Check for language adaptation and contextual examples from user's world | Purely Western MBA language and US market examples for a Vietnamese F&B user |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| M1-E1 | Agent elicits user's thinking BEFORE revealing its own analysis — asks user to reason first | Find ≥2 instances where agent prompts user to think before giving the answer | Agent always leads: presents analysis first, asks for agreement second |
| M1-E2 | Agent makes its strategic reasoning visible when teaching — shows the path from observation to conclusion, not only the conclusion (Cognitive Apprenticeship "Modeling": Collins, Brown & Holum 1991) | Find ≥2 instances where agent externalises the thinking steps — "I look at X → notice Y → this suggests Z because…" — so the user can see HOW the conclusion was reached, not just WHAT it is. For users beyond the beginner level, ≥1 instance of genuine inquiry (agent does not know the answer in advance and explores with the user) also satisfies (Socratic Partnership: Neenan 2008). | Agent presents only polished conclusions ("I recommend Z because Y") with the reasoning trail hidden — user cannot replicate the thinking. **Sophist-trap pattern fails this criterion**: a chain of leading questions walking the user toward a conclusion the agent already had in mind is not authentic Socratic and does not count as Modeling. |

---

### 5.2 Scaffolding (Per-Phase Patterns)

#### GATE Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| M2-G1 | Every completed phase includes ≥1 meaningful teaching moment (concept explanation, framework walkthrough, or strategic reasoning) | Find the teaching moment per phase — must add to user's understanding, not just inform | Agent executes work and presents results efficiently but user learns nothing about the process |
| M2-G2 | Agent briefs user on upcoming work BEFORE doing heavy research/analysis — pacing rule followed | Check: does agent explain what's coming next, THEN wait for confirmation, THEN execute? In ≥60% of phases. | Agent launches 15-minute sub-agent research without telling user what's being researched or why |

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| M2-S1 | Agent involves user in key strategic decisions — presents options and asks for input on ≥3 decisions across the session | Find decision points where user has meaningful choice (not just "approve my recommendation") | Agent makes all strategic decisions unilaterally; user's only role is "yes/no" to finished work |
| M2-S2 | Agent presents complex findings incrementally — not all research results in one massive response | Check if research findings are broken into digestible segments with space for user to process | Single 2000-word response with all Phase 1 research findings at once |
| M2-S3 | Agent connects current phase work to the overall strategy journey — user knows where they are and why | Find references to "how this phase fits into the bigger picture" per phase | Each phase feels like an isolated task; user loses sight of the journey |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| M2-E1 | Agent adjusts scaffolding depth based on user's demonstrated competence — less hand-holding as user shows understanding | Compare early vs late phase explanations: is there adaptive simplification as user shows competence? | Identical explanation depth in Phase 5 as Phase 0 despite user clearly understanding by then |
| M2-E2 | Agent teaches transferable skills — principles user can apply beyond this specific project | Find ≥1 instance where agent explains a principle generalizable to future brand decisions | All teaching is project-specific; user can't apply learnings to their next brand challenge |

---

### 5.3 Learning Outcomes (Session-Level)

*No gate criteria — learning outcomes are aspirational standards that build on teaching + scaffolding foundations.*

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| M3-S1 | User's responses show increasing strategic sophistication over the session — from tactical (Phase 0) to strategic (later phases) | Compare user's language and thinking at start vs end of session | User's communication style and strategic depth are unchanged from Phase 0 to Phase 5 |
| M3-S2 | Agent does NOT create dependency — user demonstrates understanding, not just agreement | Find ≥2 instances where user explains back, adds own reasoning, or applies concepts independently | User only ever says "yes", "sounds good", "let's do that" — passive agreement throughout |
| M3-S3 | Agent does NOT overwhelm with frameworks — introduces ≤2 major frameworks per phase, uses them, then moves on | Count frameworks introduced per response/phase; check if they're used or just named | 5+ framework names dropped in one response; user can't track or apply any of them |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| M3-E1 | User proactively contributes strategic ideas by later phases — not just answering questions | Find user-initiated strategic contributions (ideas, connections, objections based on new understanding) | User remains passive recipient from start to finish; never initiates strategic thinking |
| M3-E2 | Agent prepares user for post-session independence — explicitly discusses how to implement and iterate without the agent | Check Phase 5 for implementation guidance that assumes user will be working alone | Session ends abruptly; user has a document but no idea how to actually execute or adapt the strategy |

---

## 6. Dimension 3: Personalization Quality (20%)

*Evaluates: Does the agent adapt to THIS user's specific business, constraints, and context? And does it understand the USER as a person — their learning style, thinking patterns, and working preferences? Or could the same conversation have happened with any user?*

*Key research findings: (1) Perceived personalization drives satisfaction more than actual personalization (Tran 2015) — agent must make personalization VISIBLE. (2) Multi-dimensional personalization (thesis RQ3) requires adapting to trình độ, cách học, cách làm việc, AND business context — not just one dimension.*

### 6.1 Context Utilization

#### GATE Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| P1-G1 | Agent uses user's specific business details in recommendations — ≥5 distinct instances across the session where advice is business-specific | Find instances where recommendation references: user's brand name, specific competitors, location details, menu items, target customers, or budget tier | Generic "restaurants should..." / "F&B brands need to..." advice that works for any business |
| P1-G2 | No recommendation exceeds user's stated constraints without explicitly flagging the stretch | Check if any tactic/activity is beyond stated budget, team capacity, or timeline — and if so, whether agent acknowledges this | Recommending influencer partnerships costing 100M VND for a 50-80M VND total budget without noting the conflict |

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| P1-S1 | Competitive analysis uses user's actual competitors — businesses in their real market | Cross-check competitor names against user's location and category | Generic "top F&B brands" or competitors from a different city/segment |
| P1-S2 | Channel and tactic recommendations match user's market reality (country, city, audience behavior) | Check for Vietnam/HCMC-appropriate channels and tactics; Vietnamese consumer behavior considered | US-centric recommendations (Yelp, Google Ads, LinkedIn) for a Vietnamese F&B audience |
| P1-S3 | Examples and analogies drawn from user's industry context (F&B, dining, restaurant) | Check if illustrative examples relate to food, dining, or hospitality — not random industries | Tech startup or fashion brand analogies for a restaurant brand without bridging the contexts |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| P1-E1 | Agent proactively synthesizes different user-provided details into new insights (not just using them individually) | Find where agent connects two+ user details to create an observation the user didn't make | Uses brand name and location as labels but never synthesizes (e.g., "Your IFC location + premium positioning + weekday traffic gap suggests a corporate lunch strategy") |

---

### 6.2 Adaptive Behavior

#### GATE Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| P2-G1 | Agent's communication complexity matches user's demonstrated level — not too technical for juniors, not too basic for experts | Compare agent's vocabulary and conceptual depth to user's demonstrated marketing knowledge | PhD-level brand theory for a junior marketing executive; or dumbed-down basics for an experienced CMO |

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| P2-S1 | Agent integrates user's tangential or new information rather than ignoring it to maintain workflow | Find ≥1 instance where user introduces unexpected info and agent incorporates it meaningfully | Agent dismisses tangent: "Let's focus on Phase 2" without addressing user's point |
| P2-S2 | When research data is sparse, agent acknowledges gaps honestly — does not fabricate to fill template | Find ≥1 instance where agent says "I couldn't find data on X" or "this area needs more research" | Agent presents confident claims for data it never found — no gap acknowledgment |
| P2-S3 | Agent adjusts recommendations when user reveals new constraints or preferences mid-session | Find mid-session pivot where agent updates approach based on new user input | Agent sticks to initial plan despite user revealing budget cut or new competitor information |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| P2-E1 | Agent anticipates user needs before explicit articulation — proactive personalization | Find where agent preemptively addresses what user likely needs next, based on observed patterns | Purely reactive — only responds to explicit user requests, never anticipates |

---

### 6.3 Visible Personalization

*No gate criteria — visibility is a quality amplifier, not a gate.*

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| P3-S1 | Agent explicitly references earlier user input when making later decisions — makes the connection visible | Find callback references: "Based on what you mentioned earlier about X..." or "Since your budget is Y, we should..." | Recommendations appear without linking to user's earlier input — personalization is invisible |
| P3-S2 | Agent demonstrates accurate recall of user's characteristics in its responses — correctly references user's role, constraints, preferences, and prior statements | Find instances where agent says things like "Với budget 50-80 triệu của bạn..." or "Vì bạn là junior marketer..." — and these match what user actually said | Agent misremembers user details, or never references user's specific characteristics in its responses |
| P3-S3 | Agent shows awareness of user's behavioral patterns in conversation — references how user communicates, learns, or works when adjusting its approach | Find instances where agent acknowledges user patterns: "Tôi thấy bạn thường quan tâm đến chi phí trước..." or adjusts approach with visible reasoning tied to user behavior | Agent never acknowledges or references user's communication style, learning patterns, or working preferences in its responses |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| P3-E1 | Agent creates sense of being "known" — references patterns observed across multiple interactions or phases | Find pattern-based observations like "I notice you tend to think tactically first — let me show you the strategic frame..." | Each phase interaction feels like meeting a stranger; no accumulated understanding of user |

---

### 6.4 User Understanding & Adaptation

*Evaluates: Does the agent understand the USER as a person — not just their business? Does that understanding translate into adapted behavior? This section addresses the thesis's multi-dimensional personalization claim (Contribution #4): "adapt theo user's level, learning style, working patterns."*

*Theoretical basis: Thesis Section 4.2 defines 3 personalization levels — Strategy (6.1 covers), Mentoring (partially covered in 5.2), and Interaction (this section). RQ3 asks: "adapt theo trình độ, cách học, cách làm việc?" — these criteria evaluate exactly that.*

*Key distinction from 6.1–6.3: Those sections evaluate business-context personalization (competitors, budget, market). This section evaluates USER-context personalization (how the person thinks, learns, and works).*

#### GATE Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| P4-G1 | Agent demonstrates awareness of ≥3 distinct user dimensions through its behavior — must show adaptation across learning preferences, communication style, thinking patterns, knowledge level, or working style (not just name/role) | Find ≥3 distinct adaptation types in transcript: e.g., (1) simplifies language for beginner, (2) leads with examples for example-driven learner, (3) bridges to tactics for tactical thinker | Agent shows at most 1 dimension of adaptation (e.g., uses simple language) but doesn't differentiate across learning style, thinking pattern, or other dimensions |
| P4-G2 | Agent's behavior demonstrably changes based on observed user characteristics — ≥2 clear instances where agent adapts approach in response to USER signals (not business info) | Find moments where agent adjusts explanation style, depth, pacing, or presentation format in response to user signals; must be user-driven, not phase-driven | Agent treats every user identically: same explanation depth, same pacing, same presentation style regardless of demonstrated level or preferences |

#### STD Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| P4-S1 | Agent identifies user's learning preference (example-driven vs theory-first? visual vs verbal? fast absorber vs needs repetition?) and adapts teaching approach accordingly | Find ≥1 instance where agent's teaching method matches user's demonstrated preference — e.g., leading with examples for an example-driven user, or providing more structured summaries for a detail-oriented user | Agent uses the same teaching approach for all concepts regardless of how user has shown they learn best |
| P4-S2 | Agent recognizes user's thinking pattern (tactical vs strategic, detail-oriented vs big-picture) and adjusts how information is presented | Find evidence: (1) agent observes thinking pattern, (2) agent adjusts presentation — e.g., starting with tactical implementation for a tactical thinker, or leading with strategic frame for a strategic thinker | User consistently thinks tactically (asks "how do I do X?") but agent keeps presenting strategic frameworks first without bridging to tactics |
| P4-S3 | Agent explicitly links adaptation decisions to user observations — makes the "observe → adapt" chain visible to the user | Find ≥1 instance where agent verbalizes the link: "I noticed you pick up concepts quickly, so I'll focus on the key decisions rather than detailed explanations" or equivalent | Agent adapts silently — user doesn't know why communication style changed, so perceived personalization is zero (Tran 2015: perceived > actual) |
| P4-S4 | Agent's adaptation to user becomes more nuanced over the session — early phases show basic adaptation, later phases show refined understanding of user's specific patterns | Compare agent's adaptation in Phase 0-1 (generic: "I'll explain simply") vs Phase 3-4 (specific: "Since you prefer seeing concrete numbers before strategy, let me start with the data") | Agent's adaptation stays at the same generic level throughout — no evidence of learning about user's specific patterns over time |

#### EXCEL Criteria

| ID | Criterion | Evidence Required | Common Failure |
|----|-----------|-------------------|----------------|
| P4-E1 | Agent identifies user's knowledge gaps or blind spots and proactively addresses them WITHOUT user explicitly asking or showing confusion | Find where agent notices a likely gap (based on user's background/responses) and preemptively explains before user encounters the concept | Agent only responds to explicit confusion ("I don't understand X"); never anticipates what user might struggle with based on their profile |
| P4-E2 | Agent's responses reveal progressively deeper understanding of user across phases — later phases show nuanced, specific adaptation that couldn't happen without accumulated observation | Compare agent behavior: Phase 0 adaptation is generic (adjusts language level), but Phase 3-4 adaptation is specific (anticipates user's likely concern based on pattern: "Tôi biết bạn sẽ hỏi về chi phí, nên để tôi nói trước...") | Agent's understanding of user stays surface-level from Phase 0 to Phase 4 — same generic adaptation, no evidence of accumulated insight about this specific user |

---

## 7. Anti-Patterns (Negative Criteria)

Each confirmed occurrence deducts **0.5 points** from the affected dimension(s). Maximum deduction: **2.0 per dimension.**

Judge must cite specific evidence for each anti-pattern instance.

| ID | Anti-Pattern | Dimension(s) | How to Detect |
|----|-------------|---------------|---------------|
| AP-1 | **Sycophantic agreement**: Agent validates a clearly suboptimal or risky user choice without noting concerns | Quality, Mentor | User suggests something problematic; agent says "Great idea!" without caveats |
| AP-2 | **Fabricated research**: Agent presents vague, unverifiable claims as "research findings" — no specific data, sources, or numbers to back them up | Quality | Statements like "Research shows..." or "According to market data..." followed by generic assertions with no specific numbers, named sources, or verifiable details |
| AP-3 | **Generic advice**: Agent gives recommendations that work for any business in any market — no specificity | Quality, Personalization | Substitution test: swap brand name and location → advice unchanged |
| AP-4 | **Answer before teaching**: Agent reveals strategic decision before explaining the underlying concept | Mentor | "Your brand archetype is The Creator" before explaining what archetypes are |
| AP-5 | **Unverified knowledge claims**: Agent states marketing theory or data as fact without citing specific sources or acknowledging uncertainty | Quality | Bold claims like "Keller's research proves..." or "Statistics show 70% of..." without citing where this comes from or hedging with "based on..." |
| AP-6 | **Framework overload**: Agent introduces 4+ marketing frameworks in a single response without prioritization | Mentor | Response names Keller, Aaker, Kapferer, Sharp, Porter, Cialdini in one message |
| AP-7 | **Premature phase advance**: Agent calls report_progress(advance=True) with quality gates visibly incomplete | Quality | Gate criteria from phase reference file clearly not met when advance called |
| AP-8 | **Parrot strategy**: Agent copies user's exact words back as "strategic insight" without adding analytical value | Quality, Mentor | User says "we want more customers on weekdays" → Agent's problem statement is "increase weekday customers" verbatim |
| AP-9 | **Workflow rigidity**: Agent dismisses or ignores user's legitimate question/concern to maintain planned flow | Mentor, Personalization | User asks relevant question; agent responds "Let's stay focused on Phase X" without addressing it |
| AP-10 | **Visual-verbal mismatch**: Generated images contradict the brand identity or positioning direction | Quality | Premium brand visual brief but images show casual/budget/irrelevant aesthetics |

---

## 8. Evaluation Procedure

### 8.1 Overview: 2-Tier Evaluation Design

| Tier | Method | Purpose |
|------|--------|---------|
| **Tier 1: Quantitative** | Simulated user + 3 SOTA model judges | Scalable, reproducible comparison across systems |
| **Tier 2: Qualitative** | Real user case study (if available) | Validate perceived experience matches rubric scores |

### 8.2 Systems Under Evaluation (5 dòng)

| # | System | Mục đích so sánh |
|---|--------|-----------------|
| 1 | **Full system** (BrandMind) | Main evaluation target |
| 2 | System **không mentor** (ablation) | Chứng minh giá trị của mentoring component |
| 3 | System **không personalize** (ablation) | Chứng minh giá trị của personalization component |
| 4 | **ChatGPT vanilla** (external baseline) | Đại diện cách phổ biến nhất SME dùng AI hiện tại |
| 5 | **Gemini vanilla** (external baseline) | Tương tự — vanilla LLM, không trang bị thêm gì |

### 8.3 Tier 1: Quantitative — Simulation

#### 8.3.1 Simulated User (Claude Code)

- Đóng vai junior marketer với **persona cực kỳ chi tiết**: tên, tuổi, background, level kiến thức, cách nói chuyện, mức độ hiểu biết marketing
- Tương tác trực tiếp với cả 5 system (BrandMind + ablation variants + ChatGPT + Gemini) qua interface (Playwright cho web, API cho API-accessible systems)
- Chạy **3–5 persona đa dạng** (beginner mở quán mới, người muốn rebrand, người có chút kiến thức...), mỗi persona 2–3 lần → có variance
- Sau mỗi session, simulated user tự đánh giá **perceived personalization** và **mentor experience** từ góc first-person — vì chỉ user trực tiếp trải nghiệm mới đánh giá được

#### 8.3.2 Third-Person Judges: 3 SOTA Models

**Models**: 3 SOTA models từ 3 providers độc lập (e.g., Claude Sonnet 4.6, Gemini 3.1 Pro, GPT 5.4)

**Why 3 judges, not 1 custom judge agent:**
- Cross-provider validation → eliminates single-model bias
- Inter-rater agreement (Fleiss' Kappa / Krippendorff's Alpha) → statistical reliability metric
- No training/distillation overhead — rubric is the standardization mechanism
- Reproducible: anyone can replicate with same rubric + same models
- Disagreement between judges = diagnostic signal → reveals ambiguous criteria to refine

**Input**: Full session transcript + workspace files + generated deliverables (same for all judges)

**Judge Instructions** (provided as system prompt to each judge):

```
You are evaluating a brand strategy AI agent session. Use the rubric below
to judge each criterion as MET / UNMET / CANNOT_ASSESS.

RULES:
- Evaluate ONE criterion at a time (do NOT batch-evaluate)
- For each criterion: state it → search evidence → quote evidence → judge → explain
- You MUST cite specific transcript quotes or artifact content as evidence
- When uncertain between MET and UNMET, re-read the "Common Failure" column —
  if output matches failure description more than success, it's UNMET
- Actively search for evidence AGAINST MET before confirming (anti-confirmation bias)
- Score each phase independently — do NOT let a strong Phase 0 inflate Phase 3
- Long responses are NOT inherently better — judge content quality, not length

[Full rubric attached]
```

**Evaluation Process** (each judge follows independently):

```
Step 1: Read entire transcript sequentially. Note key events, decisions, outputs.

Step 2: For each criterion (in order: Quality → Mentor → Personalization):
  a. State the criterion
  b. Search transcript/artifacts for relevant evidence
  c. Quote the specific evidence found (or note absence)
  d. Judge: MET / UNMET / CANNOT_ASSESS
  e. Write 1-2 sentence explanation citing the evidence

Step 3: Scan full transcript for anti-pattern instances:
  a. For each anti-pattern, search for occurrences
  b. Quote evidence for each instance found
  c. Note affected dimension(s)

Step 4: Calculate scores:
  a. Per-dimension scores using formula from Section 3.2
  b. Apply anti-pattern deductions
  c. Calculate overall score with quality gate check

Step 5: Write evaluation summary:
  - Top 3 strengths (with evidence)
  - Top 3 weaknesses (with evidence)
  - Specific improvement recommendations (actionable)
  - Overall assessment: pass/fail against 8.0 threshold
```

#### 8.3.3 Judge Calibration & Bias Mitigation

| Bias | Mitigation |
|------|-----------|
| **Position bias** | Evaluate criteria in fixed order, not by "impressiveness" of transcript section |
| **Verbosity bias** | Long responses are NOT inherently better. Judge content quality, not length. |
| **Halo effect** | Score each phase independently. Don't let a strong Phase 0 inflate Phase 3 scores. |
| **Leniency bias** | When uncertain, re-read "Common Failure" column. If output matches failure more than success → UNMET. |
| **Confirmation bias** | Actively search for evidence AGAINST MET before confirming. |
| **Single-model bias** | 3 judges from 3 providers cross-validate. Disagreements flagged for analysis. |

#### 8.3.4 Inter-Rater Agreement Analysis

- Compute **Fleiss' Kappa** (or Krippendorff's Alpha) across 3 judges for each criterion
- Criteria with **high agreement** (κ ≥ 0.6): rubric is clear, criterion is reliable
- Criteria with **low agreement** (κ < 0.4): rubric is ambiguous → refine criterion definition, add examples, clarify "Common Failure"
- Report per-dimension and overall agreement scores
- **Disagreement patterns** are findings themselves — discuss in thesis what aspects of brand strategy evaluation are inherently subjective

#### 8.3.5 Scoring Across Systems

Final output: comparison table across all 5 systems × 3 dimensions:

```
| System              | Quality | Mentor | Personal. | Overall | Judges agree? |
|---------------------|---------|--------|-----------|---------|---------------|
| Full system         |   ?     |   ?    |     ?     |    ?    |    κ = ?      |
| No mentor (ablation)|   ?     |   ?    |     ?     |    ?    |    κ = ?      |
| No personal (abl.)  |   ?     |   ?    |     ?     |    ?    |    κ = ?      |
| ChatGPT vanilla     |   ?     |   ?    |     ?     |    ?    |    κ = ?      |
| Gemini vanilla      |   ?     |   ?    |     ?     |    ?    |    κ = ?      |
```

#### 8.3.6 Reproducibility Requirements

- Record **exact model IDs** and versions for all models (agent, simulated user, judges)
- Record **date of test** (model behavior changes over time)
- Set **temperature = 0** for all judge evaluations
- Use **API** where possible to control parameters (avoid web interface variance)
- Persona definitions and scenario briefs must be **fixed before** running experiments
- Check **Terms of Service** of OpenAI/Google if using Playwright for web interface interaction

### 8.4 Tier 2: Qualitative — Real User Case Study

*Optional but strongly recommended. Having real users validates that rubric scores predict actual user experience.*

#### 8.4.1 Participants

- **Participant A**: Junior marketer — ít kinh nghiệm brand strategy, đại diện target user chính
- **Participant B**: Assistant brand manager hoặc có nền tảng marketing — test khả năng personalization adapt theo level
- 2 người khác level → chứng minh system mentor khác nhau giữa 2 người

#### 8.4.2 Protocol

1. Cả hai dùng **full system** (BrandMind) với cùng brief (phát triển brand strategy cho một quán F&B giả định)
2. Quan sát quá trình tương tác: system mentor khác nhau thế nào giữa 2 người
3. Phỏng vấn sâu **20–30 phút** sau khi dùng xong
4. Danh tính ẩn danh hoàn toàn — mô tả profile đủ để hiểu level
5. Consent form đơn giản (đồng ý tham gia, dữ liệu ẩn danh)

#### 8.4.3 Post-Session Survey (10 câu)

| # | Question | Scale |
|---|----------|-------|
| 1 | Is the brand strategy actionable — could you implement this? | 1-5 |
| 2 | Are the recommendations specific to this business (not generic)? | 1-5 |
| 3 | Would you present this strategy to your management? (with minor edits) | 1-5 |
| 4 | Did the agent help you UNDERSTAND brand strategy concepts? | 1-5 |
| 5 | Did the agent adapt to your level and context? | 1-5 |
| 6 | Is the competitive analysis accurate and useful? | 1-5 |
| 7 | Is the positioning genuinely differentiating? | 1-5 |
| 8 | Are the communication recommendations practical for your budget? | 1-5 |
| 9 | Do you feel more confident about brand strategy after this session? | 1-5 |
| 10 | Would you use this tool again for future brand decisions? | 1-5 |

Plus open-ended:
- "What would a professional brand consultant do differently?"
- "What was the most valuable insight from the session?"
- "What was the most frustrating or unhelpful part?"

#### 8.4.4 What to Prove

- Participant A (junior) → system mentor nhiều hơn, giải thích kỹ, dẫn dắt từng bước
- Participant B (có nền tảng) → system adapt, ít giải thích cơ bản, đi sâu hơn
- → Bằng chứng sống cho personalization

#### 8.4.5 Validation Metric

**Pearson correlation** between rubric score (from Tier 1 judges) and human survey mean. Target: **r ≥ 0.7** (strong positive correlation = rubric predicts real-world experience).

#### 8.4.6 If Real Users Unavailable

- Simulation-only vẫn đủ cho master's thesis ứng dụng
- Acknowledge trong phần Limitation: future work sẽ validate với real user
- Có real user nâng từ "tốt" lên "rất tốt" — không có thì không rớt

### 8.5 Justification for Thesis Committee

> "Vì chưa có work nào giải quyết đồng thời cả 3 khía cạnh (multi-agent + mentoring + personalization cho brand strategy), baselines được thiết kế bằng cách degrade từng khía cạnh (bỏ mentoring, bỏ personalization) kết hợp với vanilla LLM baselines đại diện cho cách tiếp cận phổ biến nhất hiện tại của SME."

> "Evaluation sử dụng simulated user cho quantitative comparison ở quy mô lớn, cross-validated bởi 3 SOTA models từ 3 providers độc lập, bổ sung bởi exploratory case study với real users để validate perceived experience."

---

## 9. Score Interpretation

| Overall Score | Level | Real-World Equivalent |
|---------------|-------|----------------------|
| 9.0 – 10.0 | **Exceptional** | Equivalent to experienced brand consultant output. User could present directly to C-suite. |
| 8.0 – 8.9 | **Strong** (TARGET) | Junior brand manager with senior review would approve. Actionable, specific, well-reasoned. User understands the "why." |
| 7.0 – 7.9 | **Good** | Useful starting point but needs professional refinement. Some generic areas. Teaching moments present but inconsistent. |
| 6.0 – 6.9 | **Adequate** | Frameworks applied but output is largely generic. Limited practical value without heavy human rework. Mentoring is lecture-style. |
| 5.0 – 5.9 | **Weak** | Significant gaps in strategy logic, research quality, or coherence. Would not pass professional review. |
| < 5.0 | **Unacceptable** | Fundamental failures: fabricated research, contradictory strategy, no teaching, or actively misleading. Worse than no strategy. |

### 9.1 What 8.0 Looks Like in Practice

The target score (8.0) means:
- **All gate criteria pass** — fundamentals are solid across all dimensions
- **All standard criteria pass** — consistent professional quality
- **Excellence criteria are bonus** — not required, but distinguish "good" from "exceptional"

Concretely, at 8.0:
- A marketing manager reviews the strategy document and says "This is solid work. I'd approve this with minor adjustments."
- The user can explain the positioning and reasoning to their boss without the agent present.
- Recommendations are specific enough to execute within the stated budget.
- Research is based on real data, not assumptions.
- The strategy is coherent from problem diagnosis to implementation plan.

### 9.2 What 8.0 Does NOT Look Like

- A document that reads well but contains generic advice applicable to any restaurant
- Beautiful frameworks with no connection to the user's actual business constraints
- Perfect process completion (all phases done, all gates checked) but shallow content
- High scores because the agent was polite and verbose, not because the strategy was good

---

## 10. Criterion Summary

| Dimension | Gate | Standard | Excellence | Total |
|-----------|------|----------|------------|-------|
| Quality: Phase 0 | 3 | 3 | 2 | 8 |
| Quality: Phase 0.5 | 2 | 2 | 1 | 5 |
| Quality: Phase 1 | 4 | 4 | 2 | 10 |
| Quality: Phase 2 | 3 | 3 | 2 | 8 |
| Quality: Phase 3 | 3 | 3 | 2 | 8 |
| Quality: Phase 4 | 3 | 3 | 2 | 8 |
| Quality: Phase 5 | 3 | 3 | 2 | 8 |
| Quality: Cross-Phase | 2 | 3 | 2 | 7 |
| **Quality Subtotal** | **23** | **24** | **15** | **62** |
| Mentor: Teaching | 2 | 4 | 2 | 8 |
| Mentor: Scaffolding | 2 | 3 | 2 | 7 |
| Mentor: Learning Outcomes | 0 | 3 | 2 | 5 |
| **Mentor Subtotal** | **4** | **10** | **6** | **20** |
| Personalization: Context | 2 | 3 | 1 | 6 |
| Personalization: Adaptive | 1 | 3 | 1 | 5 |
| Personalization: Visible | 0 | 3 | 1 | 4 |
| Personalization: User Understanding | 2 | 4 | 2 | 8 |
| **Personalization Subtotal** | **5** | **13** | **5** | **23** |
| **GRAND TOTAL** | **32** | **47** | **25** | **104** |
| Anti-Patterns | — | — | — | **10** |

**Total evaluation points: 104 criteria + 10 anti-patterns = 114 checkpoints**

---

## Appendix A: Quick Reference for Judge

### Evaluation Checklist

```
□ Read full transcript
□ Score Quality gate criteria (23 items) — any fail → Quality ≤ 5.0
□ Score Quality standard criteria (24 items)
□ Score Quality excellence criteria (15 items)
□ Score Mentor gate criteria (4 items)
□ Score Mentor standard + excellence (16 items)
□ Score Personalization gate criteria (5 items)
□ Score Personalization standard + excellence (18 items)
□ Scan for anti-patterns (10 types)
□ Calculate dimension scores
□ Check quality gate: Quality ≥ 7.0?
□ Calculate overall score
□ Write top 3 strengths + top 3 weaknesses
□ Write improvement recommendations
□ Final verdict: PASS (≥8.0) or FAIL (<8.0)
```

### Critical Questions (Sanity Check)

Before finalizing the score, the judge should ask:

1. **"Would I hire the person who wrote this strategy?"** — If no → score should be < 8.0
2. **"Could the user defend this strategy in a meeting?"** — If no → Mentor should be < 7.0
3. **"Would this strategy work for a different restaurant in the same market?"** — If yes, unchanged → Personalization should be < 7.0
4. **"Did the agent do real work, or just organize what the user already knew?"** — If the latter → Quality should be < 7.0
