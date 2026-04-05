# BrandMind AI — Evaluation Research & Findings

> **Purpose**: Comprehensive research for building an evaluation framework for BrandMind's brand strategy agent. Covers brand strategy quality, mentoring quality, personalization quality, and LLM judge methodologies.
>
> **Last Updated**: 2026-03-30
> **Status**: Research complete, rubric design pending

---

## Table of Contents

1. [Brand Strategy Quality Evaluation](#1-brand-strategy-quality-evaluation)
2. [Mentoring & Coaching Quality Evaluation](#2-mentoring--coaching-quality-evaluation)
3. [Personalization Quality Evaluation](#3-personalization-quality-evaluation)
4. [LLM Judge & Agent Evaluation Methodologies](#4-llm-judge--agent-evaluation-methodologies)
5. [References](#5-references)

---

## 1. Brand Strategy Quality Evaluation

### 1.1 Consulting Firm Standards

**McKinsey BrandMatics**: 250 tangible/intangible brand attributes, three sources of brand power (Science, Art, Craft), brand funnel analytics (awareness → consideration → preference → purchase → loyalty).

**BCG**: Four-step framework — quantitatively link brand ladder to strategy, translate via consumer insight, ensure consistent delivery via "brand drivers", measure via focused brand scorecard.

**Bain NPS**: Net Promoter Score (0-10), Promoters (9-10) minus Detractors (0-6), strong correlation with organic growth.

**Interbrand Brand Strength (BSS)**: 10 factors out of 100 across 3 pillars:
- Internal: Clarity, Commitment, Governance, Responsiveness
- External: Authenticity, Relevance, Differentiation, Consistency, Presence, Engagement

**Brand Finance BSI**: 0-100 score (AAA+ to D rating) across Marketing Investment, Stakeholder Equity, Business Performance.

### 1.2 Academic Frameworks

**Keller's Brand Report Card (HBR 2000)** — Most directly applicable rubric:
- 10 traits, 1-10 scale each, max 100
- 80+ = strong brand, <50 = significant issues
- Traits: delivers desired benefits, stays relevant, proper pricing, properly positioned, consistent, portfolio makes sense, coordinated marketing, managers understand brand, sustained support, monitors equity sources

**Keller's CBBE Pyramid**: 4 levels (Identity → Meaning → Response → Resonance), 6 building blocks (Salience, Performance, Imagery, Judgments, Feelings, Resonance).

**Aaker's Brand Equity**: 5 dimensions — Loyalty, Awareness, Perceived Quality, Associations, Proprietary Assets.

**Kapferer's Brand Identity Prism**: 6 facets (Physique, Personality, Culture, Relationship, Reflection, Self-Image). Diagnostic tool — assess coherence across facets.

**Sharp's "How Brands Grow"**: Mental Availability (Category Entry Points, Distinctive Asset Grid) + Physical Availability. Double Jeopardy Law.

**BAV (Young & Rubicam)**: 4 pillars — Differentiation, Relevance (= Brand Vitality), Esteem, Knowledge (= Brand Stature). Power Grid plotting.

### 1.3 Industry Standards & Awards

**ISO 20671**: Only formal international standard for brand evaluation. Input/output framework with quantifiable brand strength indicators.

**Effie Awards**: Challenge/Context/Objectives 23.3%, Insights/Strategy 23.3%, Execution 23.3%, **Results 30%**.

**Cannes Lions Creative Effectiveness**: Idea 25%, Strategy 25%, **Results 50%**.

**IPA Effectiveness Awards**: Creativity most effective when distinctive, emotional, novel, well-branded, has longevity.

### 1.4 7 Universal Dimensions (Synthesized)

| # | Dimension | Key Sources |
|---|-----------|-------------|
| 1 | Strategic Clarity | McKinsey, BCG, Interbrand (Clarity), Keller Trait 4 |
| 2 | Differentiation | Aaker, BAV, Interbrand, Sharp |
| 3 | Relevance | BAV, Keller Trait 2, Effie |
| 4 | Credibility | Positioning theory, Interbrand (Authenticity) |
| 5 | Consistency | Keller Trait 5, Kapferer, IPA/WARC |
| 6 | Emotional Resonance | Keller Level 3-4, Aaker, Cannes |
| 7 | Measurable Impact | Effie 30%, Cannes 50%, Bain NPS |

### 1.5 Quality Score Levels

| Score | Level | Characteristics |
|-------|-------|-----------------|
| 9-10 | Exceptional | Clear undeniable differentiation, deep consumer insight, all Kapferer facets aligned, Keller Resonance achieved |
| 7-8 | Strong | Clear/relevant/differentiated positioning, consistent execution, some emotional connection |
| 5-6 | Adequate | Generic positioning, functional benefits only, inconsistent, limited measurement |
| 3-4 | Weak | No differentiation, claims without proof, fragmented identity |
| 1-2 | Damaging | No strategy, confuses customers, negative associations |

---

## 2. Mentoring & Coaching Quality Evaluation

### 2.1 Core Frameworks

**Bloom's Taxonomy**: 6 levels (Remember → Understand → Apply → Analyze → Evaluate → Create). Mentor effectiveness = which cognitive levels they elicit. AI defaults to lowest levels without deliberate design.

**Kirkpatrick's 4 Levels**: Reaction (engagement) → Learning (knowledge acquired) → Behavior (applied on job) → Results (business outcome). Plan from Level 4 down. Ultimate measure = quality of brand strategy produced.

**GROW Model**: Goal → Reality → Options → Will. Each brand strategy phase = a GROW cycle. Quality indicators: SMART goals, multiple data sources, options breadth, commitment strength.

**ICF Core Competencies (2025)**: 8 competencies across 4 domains — Foundation (ethics, mindset), Co-Creating (agreements, trust), Communicating (presence, listening, evoking awareness), Cultivating Growth (facilitating growth).

### 2.2 AI Tutoring Benchmarks

**AI Tutor Evaluation Taxonomy (NAACL 2025)**: 8 dimensions — Mistake Identification, Mistake Location, Revealing Answer (should be NO), Providing Guidance, Actionability, Coherence, Tone, Human-likeness. Metric: DAMR. Critical: LLM-based eval showed negative correlation with human judgment for pedagogy.

**MathTutorBench (EMNLP 2025)**: Revealed Expertise-Pedagogy Gap — being good at a subject ≠ being good at teaching it. Qwen2.5-Math: 88% problem-solving but only 6% scaffolding.

**KMP-Bench**: 6 pedagogical principles (Challenge, Explanation, Modelling, Practice, Questioning, Feedback), 22 criteria. Found: flawed scaffolding 32.5% of errors, evasion by substitution 25.8%.

**GuideEval**: 3-phase framework — Perception (identifying learner state), Orchestration (adapting to ZPD), Elicitation (stimulating reflection). Found: asymmetric feedback bias (affirm correct well, vague on errors), near-zero elicitation adaptivity.

### 2.3 Good vs Bad Mentoring (UCSF Research)

**Good**: Altruistic, active listener, accessible, opens doors, honest/trustworthy, emotionally supportive.
**Bad**: Poor communication, lack of commitment, personality clashes, competition, conflicts of interest.

### 2.4 Critical Findings for AI Mentors

1. **Expertise-Pedagogy Gap**: Domain knowledge ≠ teaching ability. Must optimize for pedagogy explicitly.
2. **Asymmetric Feedback**: LLMs affirm correct answers well but are vague on errors. Must design clear error correction.
3. **Scaffold Fading**: Without it, users become dependent. Support must decrease as competence grows.
4. **Verify Understanding**: Mentor-mentee perception gaps documented. Must ask verification questions.
5. **Over-reliance Risk**: AI dependency linked to procrastination, cognitive errors, lower critical thinking. GPA deficit 0.41.

### 2.5 Recommended Eval Tiers

**Per-Turn**: Does NOT reveal answer (binary), provides guidance (3-point), actionability (binary), coherence (binary), Bloom's level elicited (1-6), tone (encouraging/neutral/negative).

**Per-Phase**: GROW coverage (4-point checklist), scaffolding appropriateness, knowledge transfer (quality gate pass), phase deliverable quality.

**Session-Level**: Autonomy development (decreasing hints), scaffold fading, overall learning gain, engagement trajectory, strategy quality, over-reliance check, user satisfaction.

---

## 3. Personalization Quality Evaluation

### 3.1 Production System Metrics

**Netflix**: Take-rate, engagement, retention (North Star, saves $1B/yr), discovery rate. Causal measurement: removing personalization = -4% to -12% engagement.

**Spotify**: Impression-to-stream ratio, diversity metrics (intra/inter-list), serendipity. Trained satisfaction prediction model.

**Amazon**: MAE, Recall, MRR, Coverage. ~35% of sales from recommendations.

**Beyond-Accuracy Dimensions**: Relevance, Diversity, Novelty, Serendipity, Coverage, Fairness.

**HBR Personalization Index (0-100)**: Empower Me (50pts), Know Me (10), Reach Me (10), Show Me (10), Delight Me (10), Be Accountable (10). Every 10-point increase ≈ 7-point NPS rise.

### 3.2 Memory Benchmarks

| Benchmark | Venue | Focus | Best Score |
|-----------|-------|-------|------------|
| LoCoMo | ACL 2024 | Long-term conversational memory | 87.9 F1 (human) |
| LongMemEval | ICLR 2025 | 5 memory abilities | 70% (with optimizations) |
| PrefEval | ICLR 2025 | Preference following | <10% at 10 turns (zero-shot) |
| PersonaLens | ACL 2025 | Task-oriented personalization | ~2.59/4 (with history) |
| MemoryCD | Mar 2026 | Cross-domain user memory | Memory design > model scale |

**Zep vs Mem0**: Zep 75.14% vs Mem0 66.9% on LoCoMo. Zep 300ms vs Mem0 1.44s latency.

### 3.3 Perceived vs Actual Personalization

Critical distinction (Tran 2015): Perceived personalization drives favorable effects, not actual personalization. AI must make personalization VISIBLE ("Based on what you told me about X...").

### 3.4 PersonaLens 4-Point Scale

| Score | Description |
|-------|-------------|
| 1 | No personalization — generic responses |
| 2 | Minimal — occasional reference to user context |
| 3 | Moderate — consistent use of preferences and history |
| 4 | Full — deeply tailored to profile, history, situation |

### 3.5 Quality Score Levels (Synthesized)

**6/10**: Uses name/basic profile, adjusts vocabulary, recalls current session, generic scaffolding.

**8/10**: Recalls past sessions unprompted, adapts based on observed (not stated) patterns, calibrates challenge dynamically (ZPD), makes proactive connections, visibly demonstrates personalization.

**10/10**: Predicts needs before articulation, adapts strategy (not just content), handles contradictions, transfers across domains, creates sense of being "known".

---

## 4. LLM Judge & Agent Evaluation Methodologies

### 4.1 LLM-as-Judge

**MT-Bench**: GPT-4 judge achieves 80%+ agreement with humans. Key paper: Zheng et al. 2023.

**Known Biases**: Position (65% consistency on swap), Verbosity (91% failure rate for Claude/GPT-3.5), Self-Enhancement (~10% GPT-4, ~25% Claude), Authority, Moderation.

**Mitigation**: Swap test (position), penalize redundancy (verbosity), different model family as judge (self-enhancement), majority voting, reference-guided evaluation.

**Best Scoring**: CheckEval binary decomposition > Likert scales. Chain-of-thought before score. Split criteria into independent evaluations. Pairwise comparison most reliable for subjective eval.

### 4.2 Agent-as-a-Judge (ICML 2025)

- Agent-as-a-Judge: **90.44%** alignment with human consensus
- LLM-as-a-Judge: **60.38%** alignment
- Cost: ~97% reduction ($1,297 → $31)
- Uses 8 modular components (Graph, Locate, Read, Search, Retrieve, Ask, Memory, Planning)

### 4.3 Judge Agent Design Best Practices

- Rubric-based > open-ended evaluation
- Analytic rubrics with independent criteria (binary MET/UNMET most reliable)
- Mandatory natural language explanation (audit trail)
- Negative criteria combat sycophancy
- `CANNOT_ASSESS` option for inapplicability
- Few-shot with verdict balancing (equal MET/UNMET examples)
- Different model family than agent being evaluated

### 4.4 Distillation Approaches

- **Constitutional AI**: Define principles → AI feedback (RLAIF) → train preference model
- **Inverse Constitutional AI (ICLR 2025)**: Extract constitution from preference data
- **Self-Taught Evaluator (Meta)**: Self-improvement loop, 75.4 → 88.3 on RewardBench without human labels
- **Expert-to-AI Transfer**: Expert annotation (30-50) → rubric extraction → few-shot calibration → iterative refinement → optional fine-tuning

### 4.5 Production Pipeline Best Practices

- Start with 20-50 tasks from real failures
- Pin model versions and seeds for reproducibility
- Multiple trials (3-5+ per task), use pass@k and pass^k
- Swiss Cheese Model: automated evals + production monitoring + A/B testing + user feedback + manual review
- Version control eval definitions as code artifacts

---

## 5. References

### Brand Strategy Quality
- McKinsey BrandMatics, BCG Brand-Centric Transformation, Bain NPS
- Interbrand Brand Strength framework (10 factors/100)
- Brand Finance BSI (0-100, AAA+ to D)
- Keller's Brand Report Card (HBR 2000) — 10 traits, 1-10 scale
- Keller's CBBE Model, Aaker's Brand Equity, Kapferer's Prism, BAV, Sharp's How Brands Grow
- ISO 20671 — International standard for brand evaluation
- Effie Awards, Cannes Lions, D&AD, IPA Effectiveness Awards criteria

### Mentoring & Coaching
- Bloom's Revised Taxonomy (Anderson & Krathwohl 2001)
- Kirkpatrick's 4 Levels (New World Model)
- GROW Model (Whitmore), ICF Core Competencies 2025
- UCSF Mentoring Research (PMC3665769)
- AI Tutor Taxonomy (NAACL 2025), MathTutorBench (EMNLP 2025), KMP-Bench, GuideEval
- Bloom's 2-Sigma Problem, Khanmigo/Duolingo evaluations

### Personalization
- Netflix causal measurement (arXiv 2511.07280), Spotify RecSys 2025, Amazon recommendations
- HBR Personalization Index (Nov 2024)
- LoCoMo (ACL 2024), LongMemEval (ICLR 2025), PrefEval (ICLR 2025), PersonaLens (ACL 2025), MemoryCD (2026)
- Zep vs Mem0 benchmarks, PerSEval, PerQ
- Tran 2015 — Perceived vs Actual Personalization

### LLM Judge
- MT-Bench (Zheng et al. 2023), Agent-as-a-Judge (Zhuge et al. ICML 2025)
- CheckEval (EMNLP 2025), Autorubric (2025), EvalPlanner (Meta 2025)
- Self-Taught Evaluator (Meta), Constitutional AI (Anthropic), Inverse Constitutional AI (ICLR 2025)
- Prometheus, JudgeLM judge models
- Anthropic "Demystifying Evals for AI Agents", LangChain AgentEvals/OpenEvals
