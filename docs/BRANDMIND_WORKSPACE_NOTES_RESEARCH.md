# BrandMind AI - Workspace Notes: Research & Design

> **Purpose**: Comprehensive research document covering the design rationale behind BrandMind's Workspace Notes system (Tier 3 Memory). Synthesizes insights from human knowledge management practices, AI agent memory systems, and PKM methodologies into a unified architecture for persistent agent workspace notes.

**Last Updated**: 2026-03-28
**Version**: 3.1 (Post-Discussion Update)
**Status**: Ready for Implementation
**Relationship**: This document designs the **Virtual Filesystem workspace layer** referenced in `BRANDMIND_MEMORY_ARCHITECTURE.md` Section 3.1.
**Changelog**: v3.1 adds Zep deep dive (Section 4.4), post-research discussion decisions (Section 8 v3.1), and revised scalability path (Section 10).

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Research: How Humans Organize Knowledge](#2-research-how-humans-organize-knowledge)
   - 2.1 [Students](#21-students)
   - 2.2 [Researchers & Academics](#22-researchers--academics)
   - 2.3 [Doctors & Medical Professionals](#23-doctors--medical-professionals)
   - 2.4 [Therapists & Coaches](#24-therapists--coaches)
   - 2.5 [Journalists & Investigators](#25-journalists--investigators)
   - 2.6 [Chess Players & Strategic Thinkers](#26-chess-players--strategic-thinkers)
3. [Research: Personal Knowledge Management (PKM) Methodologies](#3-research-personal-knowledge-management-pkm-methodologies)
   - 3.1 [Zettelkasten (Luhmann's Slip-Box)](#31-zettelkasten-luhmanns-slip-box)
   - 3.2 [Building a Second Brain — PARA + CODE (Tiago Forte)](#32-building-a-second-brain--para--code-tiago-forte)
   - 3.3 [Getting Things Done — GTD (David Allen)](#33-getting-things-done--gtd-david-allen)
   - 3.4 [Bloom's Taxonomy Applied to Agent Learning](#34-blooms-taxonomy-applied-to-agent-learning)
   - 3.5 [Spaced Repetition & Active Recall](#35-spaced-repetition--active-recall)
   - 3.6 [Reflective Practice (Kolb, Schon, Argyris)](#36-reflective-practice-kolb-schon-argyris)
4. [Research: AI Agent Memory Systems](#4-research-ai-agent-memory-systems)
   - 4.1 [Production Systems (ChatGPT, Claude, Gemini, Copilot)](#41-production-systems-chatgpt-claude-gemini-copilot)
   - 4.2 [Research Frameworks (MemGPT, Generative Agents, Voyager, Reflexion, A-MEM)](#42-research-frameworks-memgpt-generative-agents-voyager-reflexion-a-mem)
   - 4.3 [Emerging Architectures (Mem0, Memoria, MemoryOS)](#43-emerging-architectures-mem0-memoria-memoryos)
   - 4.4 [Zep — Temporal Knowledge Graph for Agent Memory](#44-zep--temporal-knowledge-graph-for-agent-memory) *(v3.1)*
5. [Synthesis: 6 Universal Patterns](#5-synthesis-6-universal-patterns)
6. [Storage Architecture](#6-storage-architecture)
   - 6.1 [Why `~/.brandmind/` (Home Directory)](#61-why-brandmind-home-directory)
   - 6.2 [Three-Layer Scoping](#62-three-layer-scoping)
   - 6.3 [Directory Structure](#63-directory-structure)
7. [File Architecture: The "Thinking Tool" Design](#7-file-architecture-the-thinking-tool-design)
   - 7.1 [brand_brief.md — Cumulative Thinking (SOAP + Progressive Summarization + Golden Thread)](#71-brand_briefmd--cumulative-thinking)
   - 7.2 [working_notes.md — Expansive Thinking (GTD Inbox + Zettelkasten Fleeting Notes + Kolb Reflection)](#72-working_notesmd--expansive-thinking)
   - 7.3 [quality_gates.md — Critical Thinking (Golden Thread Verification + Chess Post-Mortem)](#73-quality_gatesmd--critical-thinking)
   - 7.4 [user/profile.md — User Understanding (Cross-Project)](#74-userprofilemd--user-understanding)
8. [Design Evolution: v1 → v2 → v3 → v3.1](#8-design-evolution-v1--v2--v3)
   - [v3.1: Post-Research Discussion Decisions](#v31-post-research-discussion-decisions) *(v3.1)*
     - Decision 1: Explicit Memory Sufficient for Current Stage
     - Decision 2: No Consolidation Agent
     - Decision 3: Pre-Compact Hook (Merged into Tier 3)
     - Decision 4: Architecture Diagram Alignment
9. [Implementation: DeepAgents API Mapping](#9-implementation-deepagents-api-mapping)
10. [Scalability Path](#10-scalability-path)
    - [Revised Scalability Path (v3.1)](#revised-scalability-path-v31) *(v3.1)*
11. [References](#11-references)

---

## 1. Problem Statement

BrandMind's brand strategy agent conducts multi-phase sessions (6-7 phases) that span long conversations — often exceeding the LLM context window. Three critical problems emerge:

1. **Context decay**: As conversation grows, early phases get compressed or evicted. By Phase 4, the agent loses Phase 1 research details, Phase 0 problem framing, and the reasoning chain connecting all decisions.

2. **No cross-session continuity**: When a session resumes after days/weeks, or when context window compresses, the agent starts "fresh" with no awareness of what happened before. User preferences, strategic decisions, and research findings are lost.

3. **No meta-learning**: The agent completes sessions without reflecting on what worked or didn't. Each project starts from zero expertise. A human consultant accumulates wisdom across clients — BrandMind doesn't.

The workspace notes system solves these by giving the agent a persistent "external brain" — structured files it reads at session start and writes to during work, surviving context compression and session boundaries.

---

## 2. Research: How Humans Organize Knowledge

### 2.1 Students

#### Core Systems

**Cornell Method** (Walter Pauk, Cornell University, 1950s)

Divides each page into three functional zones:
- **Right column** (2/3 width): Detailed notes captured during lectures — raw information
- **Left column** (1/3 width): Cue questions and keywords written AFTER the lecture — synthesized triggers
- **Bottom section**: Summary of the entire page — compressed understanding

The system integrates three learning stages: capture, refine, consolidate. The "5 Rs" workflow: Record → Reduce (distill into cue column) → Recite (cover notes, answer from cues) → Reflect (think about implications) → Review (regular spaced review).

**What it solves**: Passive note-taking (just recording) produces poor retention. Cornell forces transformation at three levels: raw capture → question generation → summarization. Each level requires deeper cognitive processing.

**What it doesn't solve**: Notes are siloed per-lecture, per-course. No mechanism for cross-course connections. The structure is rigid — works for lecture content, not for research or creative work.

**Feynman Technique** (Richard Feynman)

Four-step comprehension test:
1. Choose a concept
2. Explain it in simple language as if teaching a child
3. Identify gaps where your explanation breaks down
4. Return to source material and simplify again

**What it solves**: Reveals hidden comprehension gaps. Complexity and jargon mask lack of understanding. Forces genuine understanding rather than surface familiarity.

**What it doesn't solve**: It's a verification tool, not an organization system. Doesn't persist knowledge. No longitudinal tracking.

**Spaced Repetition** (Ebbinghaus, 1885; modern: Anki, SuperMemo)

Algorithmically scheduled retrieval practice. Anki's FSRS algorithm optimizes review intervals based on individual performance data.

Key research:
- A 2024 study found 86.2% of US medical students use Anki, with 66.5% using it daily
- Meta-analyses (Dunlosky 2013, Karpicke 2017) show active recall + spaced repetition achieves **90-95% retention after 30 days** versus **15-20% for passive rereading**

**What it solves**: The forgetting curve. Without reinforcement, ~70% of new information is forgotten within 24 hours. Spaced repetition makes retention nearly permanent with minimal review time.

**What it doesn't solve**: Works for factual recall, not for creative synthesis or decision-making. No mechanism for connecting ideas across domains.

#### BrandMind Application

- **Cornell's three-zone principle** → brand_brief.md structure: raw findings (O) → synthesized insights (A) → executive summary (top)
- **Feynman's simplification test** → Agent should be able to explain any strategic decision in 1-2 simple sentences. If it can't, the decision isn't well-understood.
- **Spaced repetition's importance scoring** → Not all workspace content is equally important. Strategic decisions (high importance) should persist permanently. Transient research data (low importance) can be re-fetched.

---

### 2.2 Researchers & Academics

#### Core Systems

**Lab Notebooks**

The primary record of scientific work. A proper entry includes: date, title, hypothesis/objective, materials and methods, experimental observations, analysis, conclusions, and next steps.

Critical rules:
- Written in permanent ink AS experiments progress (not retrospectively)
- Errors are struck through with a single line, dated, initialed, and explained — **NEVER erased**
- Maintains clear distinction between raw data and interpretation

**What it solves**: Reproducibility (someone else can replicate the work) and interpretive layering (the researcher's analysis sits alongside the raw data, creating a thinking trail).

**What it doesn't solve**: Lab notebooks are chronological — hard to find specific information later. Cross-project connections require separate indexing systems.

**Literature Management (Zotero + Obsidian workflow)**

Modern two-tool pipeline:
1. Collect papers in Zotero via browser connector
2. Read and annotate PDFs within Zotero
3. Import annotations into Obsidian as structured literature notes
4. Create links between notes from different papers using backlinks
5. Use graph visualization to discover cross-paper connections

**What it solves**: Cross-referencing across papers and research projects. The graph view reveals clusters of connected ideas spanning different research questions.

**What it doesn't solve**: Time investment is high. Many researchers report their cross-referencing systems are aspirational rather than consistently maintained.

#### BrandMind Application

- **Lab notebook's "never erase" principle** → brand_brief.md preserves decision history. Previous phases are compressed but never deleted. "Alternatives rejected" section captures what was NOT chosen and why.
- **Observation vs interpretation separation** → SOAP structure (S/O = observations, A/P = interpretations) prevents mixing facts with judgments.
- **Cross-referencing** → Golden Thread at the top of brand_brief.md links decisions across phases, like Obsidian backlinks connecting notes.

---

### 2.3 Doctors & Medical Professionals

#### Core Systems

**SOAP Notes** (Dr. Lawrence Weed, 1964-1968)

Four sections:
- **S (Subjective)**: Patient's reported symptoms, history, concerns — what the patient tells you
- **O (Objective)**: Measurable findings — vitals, lab results, physical examination findings
- **A (Assessment)**: The clinician's interpretation — diagnosis, differential diagnosis, clinical reasoning
- **P (Plan)**: What to do next — tests to order, medications, referrals, follow-up schedule

**What it solves**: Forces separation of observation from interpretation. A doctor cannot jump from "patient says they feel tired" (S) to "prescribe iron supplements" (P) without explicitly documenting what they measured (O) and what they concluded (A). This prevents diagnostic shortcuts and creates an audit trail for other doctors.

**What it doesn't solve**: SOAP is per-visit. For chronic conditions across many visits, you need additional structure (see POMR below).

**Problem-Oriented Medical Record (POMR)**

Organizes ALL documentation around individual patient problems rather than chronological encounters. Each problem gets its own contained SOAP section, creating "a note within a note."

By 1973, 73% of US medical schools taught POMR. Research found that encounter-oriented alternatives "muddle the course of individual conditions and perhaps cause inattention to critical concerns."

**What it solves**: Longitudinal tracking of each problem across visits. A three-column interface displays: (1) visit diagnoses list, (2) overview and current assessment/plan for the selected diagnosis, (3) problem-relevant data. Previous A/P documentation is accessible via hyperlinks, showing the trajectory of each problem.

**What it doesn't solve**: Per-patient only. No mechanism for cross-patient learning (e.g., "patients with these symptoms often respond well to treatment X").

**Continuity of Care Documents (CCD)**

Standardized documents for handoffs between providers. Ensure every new provider has the requisite knowledge to maintain treatment quality.

Research finding on handoffs: **41% of handoff phrases contained knowledge (interpretation, clinical reasoning)** rather than bare facts. The distinction: "potassium is 3.2" is information; "potassium is 3.2, trending down despite supplementation, likely related to the diuretic, watch for arrhythmias" is knowledge.

**What it solves**: Context restoration when the original provider is unavailable. This is EXACTLY the workspace notes use case — restoring agent context after compression or session resume.

#### BrandMind Application — SOAP as Core Structure

SOAP maps directly to the brand strategy agent's needs:

| SOAP | Brand Strategy | Example |
|------|---------------|---------|
| **S** (Subjective) | What the user told us | "Muon rebrand, target Gen Z, budget mid-range" |
| **O** (Objective) | What research found | "73% Gen Z VN willing to pay premium for craft. Competitor A: 60% market share mid-tier" |
| **A** (Assessment) | What agent concluded | "Positioning territory: Modern Vietnamese Craft. Gap exists between mass-market and luxury import" |
| **P** (Plan) | What comes next | "Phase 3: Develop identity system. Pending: user confirm brand name finalists" |

The POMR principle (organize by problem, not chronology) maps to organizing brand_brief.md by phase rather than by date — each phase is a "problem" with its own SOAP section.

The CCD principle (handoff documents must contain KNOWLEDGE not just information) is the design standard for workspace notes — they must contain the agent's interpretive reasoning, not just raw data.

---

### 2.4 Therapists & Coaches

#### Core Systems

**The Golden Thread**

The central organizing principle of therapy documentation: "the consistent clinical connection between your assessment (what brings the client to therapy), treatment plan (what goals and interventions you've set), and progress notes (how the client responds over time)."

The flow: Intake Assessment (identifies problems, diagnosis) → Treatment Plan (goals with specific interventions) → Progress Notes (each session connects back to the plan) → Discharge (outcomes against initial goals).

Example:
- Goal: "Reduce panic attacks from daily to once per week within 8 weeks"
- Objective: "Client will practice three coping strategies"
- Intervention: "CBT focusing on cognitive restructuring"
- Measurement: "Self-report and GAD-7 reassessment every four weeks"

**What it solves**: Traceability. EVERY progress note connects backward to the treatment plan (goals) AND forward to the next step. If anyone asks "why are we doing this?", trace the thread back to the initial assessment. If anyone asks "is this working?", trace forward to measurable outcomes.

**What it doesn't solve**: Limited to per-client context. No cross-client learning mechanism built into the documentation structure.

**Coaching Self-Assessment**

Coaches maintain separate notes evaluating their OWN effectiveness:
- Which techniques worked for which client types
- Where the coach felt uncertain
- Patterns in their own coaching style

**What it solves**: Meta-learning. The practitioner gets better over time by reflecting on their own practice, not just the client's progress.

**What it doesn't solve**: Self-assessment is subjective. Without external validation, blind spots persist.

#### BrandMind Application — Golden Thread as Traceability Chain

The Golden Thread is the MOST directly applicable pattern for BrandMind's multi-phase workflow:

```
Phase 0: Problem identified → "Brand perceived as outdated for Gen Z"
    ↓ (thread)
Phase 1: Research confirmed → "Gen Z VN prefers authentic, craft aesthetics"
    ↓ (thread)
Phase 2: Positioning chosen → "Modern Vietnamese Craft" territory
    ↓ (thread)
Phase 3: Identity designed → "Earth tones, hand-drawn elements, artisan typography"
    ↓ (thread)
Phase 4: Communication planned → "Instagram-first, UGC-heavy, craft-story content"
    ↓ (thread)
Phase 5: Deliverables → Brand book + social media templates + launch plan
```

Every decision traces back to the Phase 0 problem and forward to downstream implications. If the user asks in Phase 4 "why minimalist identity?", the agent traces: minimalist ← "modern craft" positioning ← Gen Z research ← "outdated brand" problem.

quality_gates.md implements Golden Thread verification: before advancing, the agent checks that the current phase's output CONNECTS to both the foundational problem and the upcoming phases.

The coaching self-assessment pattern maps to session reflections — the agent evaluates its own effectiveness after each session.

---

### 2.5 Journalists & Investigators

#### Core Systems

**Evidence Chain & Source Management**

Journalists maintain rigorous attribution for every factual claim. Two approaches:
1. Footnotes after each statement citing its source
2. Spreadsheets with one column per factual claim and subsequent columns for sourcing (links, filenames, audio timecodes)

The "five pillars of verification": provenance, source, date, location, and motivation.

**What it solves**: Every fact is traceable to its source. This enables fact-checking, legal defense, and collaborative investigation. The distinction: a notebook that says "the mayor approved the contract" is recording; one that says "Mayor Smith approved the contract [Source: City Council minutes 2024-03-15, page 42; confirmed by Deputy Mayor Jones, phone interview 2024-03-20]" is knowledge management.

**What it doesn't solve**: Evidence chains are time-consuming to maintain. Most journalists admit their systems are personal and idiosyncratic.

**Source Networks as Cross-Story Assets**

Journalists build source relationship databases that persist across stories. Contact databases, institutional knowledge, and "string" (saved fragments of potentially useful information) create serendipitous connections across investigations.

**What it solves**: Cross-context transfer. A source developed for one story provides leads for another. Beat expertise accumulates.

**What it doesn't solve**: Personal and idiosyncratic — institutional knowledge transfer is difficult when reporters change beats.

#### BrandMind Application

- **Evidence chain** → brand_brief.md A (Assessment) sections should cite sources: "Positioning based on: [O1] consumer survey data, [O2] competitive gap analysis, [O3] social listening trends." When the user challenges a decision, the agent can point to specific evidence.
- **Source networks as cross-project assets** → The `learnings/` directory accumulates domain expertise across projects, like a journalist's beat knowledge. "Vietnamese F&B brands that succeed at repositioning typically [pattern learned from prior projects]."

---

### 2.6 Chess Players & Strategic Thinkers

#### Core Systems

**Post-Game Analysis (Post-Mortem)**

The recommended process:
1. **Human analysis first** — replay the game from memory, capturing mental state, confidence levels, confusion points
2. **Locate the earliest turning point** — not the final blunder, but the first moment the position shifted
3. **Classify the mistake category** — tactical, conceptual, psychological, or time-management
4. **Engine verification last** — use Stockfish/Lc0 to check analysis, not replace it
5. **Extract one actionable lesson** — write it in a "Chess Diary"

**What it solves**: The "one-lesson rule" creates compound learning. One lesson per game × hundreds of games = mastery. Error classification reveals patterns: "I keep making conceptual mistakes in endgames" → targeted study.

The critical distinction: **human analysis before engine analysis**. Using an engine immediately tells you what was wrong but not WHY you made the mistake. Players who review with human-first analysis learn THINKING corrections (transferable). Players who only use engine analysis learn MOVE corrections (position-specific).

**What it doesn't solve**: Requires discipline. Many players skip the human analysis step and jump to engine verification, losing the meta-learning benefit.

**Pattern Libraries**

Expert chess players store approximately 50,000-100,000 position patterns (chunks). Expertise manifests as faster and more accurate pattern matching. Cross-context transfer happens when a tactical theme from one opening appears in a different opening's middlegame.

**What it solves**: Transfer learning. Abstract patterns (forks, pins, pawn structures) apply across many specific positions.

#### BrandMind Application

- **One-lesson rule** → Each session reflection ends with ONE actionable lesson. This prevents reflection from becoming an unfocused data dump. Compound effect: 50 sessions × 1 lesson = significant expertise.
- **Error classification** → When things go wrong (research returns poor results, user rejects recommendation), classify WHY:
  - **Data gap**: KG/doc missing information
  - **Tool failure**: Search engine down, browser blocked
  - **Conceptual mismatch**: Agent's recommendation didn't fit user's context
  - **User preference**: User has strong opinion overriding analysis

  This feeds into both session reflection AND cross-project learning.
- **Human-first analysis** → The agent should reflect on its OWN reasoning before checking external validation. "Why did I recommend this positioning?" before "Does the research support this positioning?"
- **Pattern libraries** → The `learnings/` directory IS the pattern library. Abstract strategic patterns ("Vietnamese F&B consumers show X behavior") transfer across projects.

---

## 3. Research: Personal Knowledge Management (PKM) Methodologies

### 3.1 Zettelkasten (Luhmann's Slip-Box)

**Creator**: Niklas Luhmann (German sociologist, 1927-1998)
**Scale**: ~90,000 interlinked cards → 50 books + 600 articles across 40 years

#### Core Principles

**Three types of notes:**
- **Fleeting notes**: Quick, temporary captures — a sentence, keyword, or question. Meant to be discarded after being recast into permanent notes.
- **Literature notes**: Source references with selective annotations in your own words. Short, focused on what you don't want to forget.
- **Permanent notes**: Self-contained, atomic notes that are interconnected. Written in your own words, always understandable without external context.

**Atomic notes + cross-links**: Each note captures ONE idea. Notes link to other notes based on semantic relationships, not hierarchical categories. Structure emerges bottom-up through connections, not top-down through pre-defined folders.

**What it solves**: Emergent knowledge. By forcing atomic granularity and explicit linking, the system surfaces unexpected connections between ideas from completely different domains. Luhmann described his Zettelkasten as a "communication partner" that surprised him with connections he hadn't planned.

**What it doesn't solve**: High overhead for initial setup. Requires discipline to maintain atomic granularity. Doesn't scale well without digital tooling for large collections.

#### A-MEM (NeurIPS 2025): Zettelkasten for AI Agents

The A-MEM paper directly applies Zettelkasten to AI agent memory:

1. **Note Construction**: New memory → LLM generates structured note with contextual descriptions, keywords, tags, embedding vectors
2. **Link Generation**: Retrieve relevant historical memories → LLM decides whether connections should be established
3. **Memory Evolution**: New memories trigger updates to existing notes' contextual representations and attributes

Performance: 2x better multi-hop reasoning vs MemGPT while using only 1,200-2,500 tokens vs 16,900 tokens.

#### BrandMind Application

- **Three note types map to workspace content lifecycle**: User's raw inputs = fleeting notes → Agent's research findings = literature notes → Validated strategic decisions = permanent notes. The agent knows what to trust and what to discard.
- **Fleeting → Permanent pipeline**: `working_notes.md` inbox = fleeting notes. Processed insights move to `brand_brief.md` = permanent notes. Phase transition = the processing step.
- **Future evolution (Tier 4/5)**: Full atomic linked notes graph (A-MEM style) replacing monolithic files. Each strategic decision becomes a node linked to evidence, phase, and related decisions.

---

### 3.2 Building a Second Brain — PARA + CODE (Tiago Forte)

#### PARA Method

Organizes ALL information by actionability:
- **Projects**: Short-term efforts with a clear goal and deadline
- **Areas**: Ongoing responsibilities with standards to maintain
- **Resources**: Topics of ongoing interest for future reference
- **Archives**: Inactive items from the other three categories

#### CODE Workflow

- **Capture**: Save anything that resonates, is surprising, or is useful
- **Organize**: Move captured items to the right PARA category. Key question: "In which project will this be most useful?"
- **Distill**: Progressive summarization
- **Express**: Use notes to create something — notes exist to be used, not hoarded

#### Progressive Summarization

The distillation engine, 5 layers:
- Layer 0: Original full source text
- Layer 1: Content brought into the note system
- Layer 2: Bold the best passages (keywords, key phrases, core ideas)
- Layer 3: Highlight the "best of the best" from Layer 2
- Layer 4: Write your own executive summary at the top
- Layer 5: Remix into original work

Critical insight: **distillation is opportunistic and incremental**. You don't summarize everything at once. Each time you revisit a note, you compress it one layer further.

**What it solves**: The "discoverable at a glance" problem. The executive summary (Layer 4) lets you do a flyby scan. Previous layers preserved for deep dives. Nothing is lost.

**What it doesn't solve**: PARA is per-person, not per-team. Progressive summarization requires revisitation discipline.

#### BrandMind Application

| PARA Category | BrandMind Equivalent |
|---|---|
| **Projects** | Current brand strategy session (active workspace) |
| **Areas** | Domain knowledge (F&B, fashion, Vietnamese market) |
| **Resources** | Knowledge Graph + Document Library + Skills |
| **Archives** | Completed brand strategy projects |

**Progressive Summarization in brand_brief.md**: Executive summary at top (Layer 4), updated each phase. Current phase at full detail (Layer 1-2). Previous phases compressed (Layer 3). The agent reads the summary for instant context restoration, dives into full detail only when needed.

**CODE maps to agent workflow**: Capture (research tools gather data) → Organize (file into workspace by phase) → Distill (summarize at phase transitions) → Express (create deliverables).

---

### 3.3 Getting Things Done — GTD (David Allen)

#### Core Insight

"Your mind is for having ideas, not holding them." The "open loops" occupying working memory (unfinished tasks, commitments, concerns) create cognitive overhead. The solution: a "trusted external system" that captures everything.

#### Five Phases

1. **Capture**: Get everything out of your head into an inbox
2. **Clarify**: Decide what each item means and what action it requires
3. **Organize**: Next Actions, Waiting For, Someday/Maybe, Reference, Calendar, Projects
4. **Reflect**: The Weekly Review — look at all lists, update, regain perspective
5. **Engage**: Choose actions based on context, time, energy, priority

#### The Weekly Review

The keystone habit:
- Process all inboxes to zero
- Review all project lists
- Get current and complete
- Be creative about what comes next

**What it solves**: Cognitive overhead from trying to hold everything in working memory. Once captured in a trusted system, the mind can focus on execution rather than remembering.

**What it doesn't solve**: GTD is an organization system, not a thinking system. It tells you WHAT to do next but not HOW to think about it.

#### BrandMind Application

| GTD Concept | Agent Equivalent |
|---|---|
| **Inbox** | Unprocessed user inputs, research findings pending synthesis |
| **Next Actions** | Current phase step, immediate to-dos |
| **Waiting For** | Questions posed to user awaiting response |
| **Someday/Maybe** | Ideas user mentioned for future consideration |
| **Weekly Review** | **Phase Transition Review** — process inbox, verify quality gates, update brand brief |

The agent's conversation memory is unreliable (subject to compression/decay). The workspace filesystem IS the "trusted external system."

**Inbox in working_notes.md**: Every unprocessed item goes here. User says "maybe we should do a loyalty program" during Phase 1 → into inbox. Phase transition = GTD's Weekly Review: process all inbox items (act on, defer to relevant phase, or discard).

---

### 3.4 Bloom's Taxonomy Applied to Agent Learning

#### Revised Bloom's Taxonomy (Anderson & Krathwohl, 2001)

Cognitive levels from simple to complex:
1. **Remember**: Retrieve relevant knowledge
2. **Understand**: Construct meaning from information
3. **Apply**: Use a procedure in a given situation
4. **Analyze**: Break material into parts, determine relationships
5. **Evaluate**: Make judgments based on criteria
6. **Create**: Put elements together to form a novel whole

#### How Agent Knowledge Evolves Through Phases

| Phase | Bloom's Level | What the agent does | Memory implication |
|---|---|---|---|
| Phase 0 (Diagnosis) | Remember + Understand | Collect facts, understand business context | Store factual data → can be re-fetched later |
| Phase 1 (Research) | Understand + Analyze | Construct meaning from market data, analyze competitive dynamics | Store INSIGHTS, not raw data |
| Phase 2 (Positioning) | Analyze + Evaluate | Evaluate positioning territories, judge which is defensible | Store JUDGMENTS + RATIONALE |
| Phase 3 (Identity) | Create | Synthesize brand personality, visual direction | Store CREATIVE DECISIONS + intent |
| Phase 4 (Communication) | Apply + Create | Apply strategy to channels, create content framework | Store FRAMEWORKS + guidelines |
| Phase 5 (Deliverables) | Create + Apply | Produce tangible outputs | Store REFERENCES to deliverables |

**What it solves**: Clarifies what the agent should persist in workspace notes vs. re-fetch on demand. Raw facts (Bloom 1-2) can be re-fetched from KG/web. Higher-order outputs — insights, judgments, decisions, creative choices (Bloom 3-6) — are expensive to recreate and MUST persist.

#### BrandMind Application

- **brand_brief.md stores Bloom Level 4-6 outputs**: Analysis conclusions, evaluation rationale, creative decisions. NOT raw facts.
- **Quality gates escalate in cognitive complexity**: Phase 0 gate = "Can the agent recall the business facts?" Phase 2 gate = "Can the agent justify which positioning territory to choose?"
- **Progressive summarization aligns with Bloom**: Executive summary = Level 6 synthesis. Detailed sections = Level 3-4 analysis. Raw data in KG = Level 1-2 facts.

---

### 3.5 Spaced Repetition & Active Recall

#### Ebbinghaus Forgetting Curve

Memory retention decays exponentially without reinforcement. After 24 hours, ~70% of new information is forgotten. Spaced retrieval at increasing intervals (1 day, 3 days, 7 days, 14 days...) combats this decay.

#### AI Agent Memory Systems Implementation

State-of-the-art (2025-2026) uses multi-factor scoring:

- **Importance scoring**: LLM-generated importance (0.0-1.0). Critical memories get high scores.
- **Recency decay**: Score decreases over time. Every retrieval resets the clock (this IS spaced repetition).
- **FadeMem** (2025): Intelligent forgetting — retains what matters, 45% less storage by pruning noise.
- **SAGE framework**: Uses Ebbinghaus curve explicitly — dynamically prioritizes high-value information.

#### What to "Remember" vs "Look Up"

Research converges on a clear heuristic:

| Always persist (high importance) | Look up on demand (low importance) |
|---|---|
| User preferences and constraints | Competitor pricing details |
| Key strategic decisions + rationale | Specific market statistics |
| Phase outputs and quality gate results | Social media follower counts |
| Brand positioning choices | Current trend data (changes frequently) |
| User's knowledge level | Transient research findings |

**The deciding principle**: If the information shapes HOW the agent behaves (strategic context), persist it. If it's raw DATA the agent uses (factual content), let it be retrieved on demand.

#### BrandMind Application

- **brand_brief.md = Long-Term Memory (LTM)**: Strategic decisions, positioning rationale, creative direction. Never decays. Gets richer each phase.
- **working_notes.md = Short-Term Memory (STM)**: Current discussion, pending questions, session-specific context. Refreshed each session.
- **user/profile.md = Highest importance LTM**: User preferences persist across ALL projects.
- **Research findings = volatile**: Don't store raw competitor data in workspace. Store the INSIGHT derived from it.

---

### 3.6 Reflective Practice (Kolb, Schon, Argyris)

#### Kolb's Experiential Learning Cycle

Four stages in a continuous loop:
1. **Concrete Experience**: Do something (agent completes Phase 1 research)
2. **Reflective Observation**: Reflect on what happened (what went well? what was missed?)
3. **Abstract Conceptualization**: Form theories/principles ("Vietnamese F&B competitor data is more reliable from social media than review sites")
4. **Active Experimentation**: Test the theory (in next Phase 1, prioritize social media research)

**What it solves**: Without explicit reflection, experience doesn't translate to expertise. The cycle ensures each experience produces an abstract, transferable lesson.

#### Schon's Reflection-in-Action vs Reflection-on-Action

- **Reflection-in-action**: Real-time adjustment during the task. Agent notices search results are irrelevant → changes strategy mid-phase.
- **Reflection-on-action**: Deliberate post-task analysis. After completing session, agent reviews: which phases went smoothly, where user seemed confused, which tools failed.

Practitioners develop "repertoires" through repeated reflection. They don't apply rules mechanically — they recognize situations and draw from experience.

#### Argyris & Schon: Single-Loop vs Double-Loop Learning

- **Single-loop**: Detect error → correct action → keep same assumptions. (Search query failed → try different query.)
- **Double-loop**: Detect error → question the governing assumptions. (Search query failed → question whether web search is even the right approach. Maybe the KG has better information for this class of question.)

**What it solves**: Single-loop keeps you running on the same track. Double-loop changes the track itself. For BrandMind: instead of just "retry search with different keywords," the agent learns "for Vietnamese market data, social listening tools outperform traditional web search."

#### BrandMind Application

- **Session reflection in working_notes.md**: After each session, agent writes: what worked, what didn't, user patterns, one actionable lesson (Kolb Step 2-3).
- **Phase transition = reflection checkpoint**: Not just quality gate verification, but genuine reflection: "Is this positioning well-supported, or am I relying on incomplete data?"
- **Accumulated reflections → learnings/**: Over time, session reflections distill into abstract principles (Kolb Step 3) that transfer to new projects (Kolb Step 4). This is the bridge from per-session notes to cross-project expertise.

---

## 4. Research: AI Agent Memory Systems

### 4.1 Production Systems (ChatGPT, Claude, Gemini, Copilot)

#### ChatGPT (OpenAI)

**Architecture**: Four-layer memory injected directly into context window (NO RAG):

| Layer | Persistence | Contents |
|---|---|---|
| Session Metadata | Ephemeral | Device, browser, location, timezone, subscription tier |
| User Memory | Permanent | ~33 explicit facts via "Remember that..." or confirmed detections |
| Recent Conversations | Rolling (~15 chats) | Pre-computed summaries of user statements only |
| Current Session | Ephemeral | Full transcript, oldest drops first |

Key decisions: No RAG (pre-computed summaries for latency), explicit memory storage (no behavioral inference), all layers compete for fixed context budget.

**OpenAI Agents SDK Cookbook** — State-based long-term memory with four lifecycle phases:
1. **Injection**: State rendered as YAML frontmatter + Markdown, injected via XML blocks
2. **Distillation**: `save_memory_note()` captures high-signal info during interaction
3. **Trimming**: Maintains last N turns; on trim, session memories reinject into system instructions
4. **Consolidation**: End-of-session LLM-powered merge with dedup and conflict resolution

**What works**: State-based injection (not RAG) for deterministic professional agents. LLM-driven consolidation prevents unbounded growth.
**What doesn't**: Automatic injection is noisier than on-demand retrieval. No cross-conversation semantic search.

#### Claude (Anthropic)

**Architecture**: Tool-based on-demand retrieval (NOT automatic injection).

Memory stored in XML format (`<userMemories>` tags). Categories: identity, professional background, learning style, project history, preferences. Project-based compartmentalization.

Retrieval tools: `conversation_search` (topic/keyword, 1-10 results), `recent_chats` (time-based, 1-20 results). Non-deterministic — Claude decides whether to invoke.

**What works**: On-demand depth over automatic breadth. Project compartmentalization prevents cross-context bleed. User control (tool calls visible).
**What doesn't**: If Claude doesn't think to look, relevant context stays buried.

#### Gemini (Google)

**Architecture**: Single `user_context` document — typed outline with factual bullets in fixed sections. Each memory includes rationale linking to source conversation + date.

Memory access is opt-in — model only accesses when queries contain explicit trigger phrases.

Despite Google's data ecosystem (Gmail, Drive, Calendar), `user_context` remains isolated to chat — significant underutilization.

**What works**: Explicit triggers avoid irrelevant context surfacing. Simple single-document approach.
**What doesn't**: Sacrifices serendipitous personalization. Doesn't leverage Google's data ecosystem.

#### Microsoft Copilot

**Architecture**: Memories stored in user's **Exchange mailbox** (hidden `CopilotMemory` folder). Types: Saved Memories (persistent), Chat History Details (dynamic, LLM-inferred), Custom Instructions.

Cross-app: memory persists across Teams, Outlook, Word. Communication Memory creates unified views across collaboration tools.

**What works**: Cross-app persistence leveraging existing infrastructure. Enterprise security inheritance.
**What doesn't**: No admin controls for what information enters memory. Auto-deleted on feature disable.

#### Comparative Analysis

| Aspect | ChatGPT | Claude | Gemini | Copilot |
|---|---|---|---|---|
| Injection | Automatic (always-on) | On-demand (tool-based) | Trigger-based (opt-in) | Automatic |
| Storage | Proprietary | Proprietary (XML) | Single document | Exchange mailbox |
| Cross-session | Pre-computed summaries | Full conversation search | Summarized profile | Persistent memories |
| User control | View/delete | View/delete/search tools | View/delete | View/delete |
| Personalization depth | Medium | Deep (when invoked) | Shallow | Medium |

---

### 4.2 Research Frameworks

#### MemGPT / Letta (UC Berkeley, 2023-2025)

**Architecture**: OS-inspired virtual context management.

**Two-tier memory:**

| Tier | Component | Description |
|---|---|---|
| Main Context (Tier 1) | System Instructions | Read-only control flow |
| | Core Memory | Fixed-size, writeable persona/user facts (6 self-editing tools) |
| | Conversation History | FIFO queue + summary of evicted context |
| External Context (Tier 2) | Recall Storage | Complete uncompressed conversation history |
| | Archival Storage | "Infinite size" structured knowledge via embedding search |

**Key innovation**: The LLM manages its OWN context through function tools, deciding what to page in/out. Like an OS managing virtual memory.

**Benchmark finding**: A simple filesystem approach scored **74% on LoCoMo** — competitive with specialized memory systems. Blog title: "Is a Filesystem All You Need?"

**What works**: Self-editing core memory forces selective persistence. The agent becomes its own memory manager. Filesystem baseline surprisingly competitive.
**What doesn't**: 16,900 tokens for core memory is expensive. Self-editing can be unpredictable without constraints.

#### Generative Agents (Stanford, Park et al., 2023)

**Architecture**: Three-component system for believable human behavior:

1. **Memory Stream**: Complete record of experiences in natural language. Each observation: description, creation timestamp, last access timestamp, importance score (1-10, LLM-rated).
2. **Reflection**: Periodically synthesizes memories into higher-level conclusions. Triggered when sum of importance scores exceeds threshold. Generates abstract insights like "person X values Y."
3. **Planning**: Translates reasoning into high-level plans → hourly decomposition → 5-15 minute actions.

**Memory retrieval scored on three factors**: recency (exponential decay), importance (LLM-rated), relevance (embedding similarity to current context).

**Key finding through ablation**: ALL three components (observation, planning, reflection) are critical. Removing any one significantly degrades agent behavior.

**What works**: Reflection mechanism produces genuinely emergent behavior. Importance scoring prevents noise from dominating.
**What doesn't**: Computationally expensive. Importance scoring is LLM-dependent (quality varies).

#### Voyager (NVIDIA, 2023)

**Architecture**: First LLM-powered embodied lifelong learning agent (Minecraft).

Three components:
1. **Automatic Curriculum**: Proposes increasingly complex tasks
2. **Skill Library**: Ever-growing library of executable code — skills are compositional
3. **Iterative Prompting**: Incorporates environment feedback, execution errors, self-verification

**Key insight**: Skills stored as CODE alleviate catastrophic forgetting because knowledge is external to model weights. The skill library transfers to new worlds — Voyager solves novel tasks in unseen environments.

Performance: 3.3x more unique items, 2.3x longer distances, 15.3x faster tech tree milestones vs prior SOTA.

**What works**: Code-as-memory is the most effective anti-forgetting mechanism. Compositional skills compound.
**What doesn't**: Domain-specific (game environments). Skill extraction requires executable format.

#### Reflexion (NeurIPS 2023, Shinn et al.)

**Architecture**: Verbal reinforcement learning — no weight updates, only linguistic feedback.

Three components:
1. **Actor**: Generates actions
2. **Evaluator**: Scores trajectories with reward functions
3. **Self-Reflection**: LLM generates verbal reinforcement cues stored in episodic memory

After failed trials, the reflection model analyzes trajectory + reward to produce actionable feedback for future attempts.

**What works**: Lightweight (no fine-tuning), nuanced (verbal vs scalar), explicit and interpretable episodic memory.
**What doesn't**: Requires clear evaluation criteria. Doesn't generalize well across task types.

#### A-MEM (NeurIPS 2025)

**Architecture**: Zettelkasten-inspired agentic memory with autonomous organization.

Each memory = atomic note: (original content, timestamp, LLM-generated keywords, tags, contextual descriptions, embedding vectors, linked memory references).

**Dynamic linking**: New memory → cosine similarity against all existing → top-k neighbors → LLM analyzes candidates for meaningful connections. No predefined schemas.

**Memory evolution**: New memories trigger updates to existing ones. Higher-order patterns emerge organically.

Performance: 2x better multi-hop reasoning vs MemGPT using only 1,200-2,500 tokens vs 16,900 tokens.

**What works**: Dynamic linking outperforms fixed schemas. Emergent patterns. Token-efficient.
**What doesn't**: Requires LLM call for every new memory (latency). Link quality depends on LLM judgment.

---

### 4.3 Emerging Architectures

#### Mem0 (Production Memory Layer, 2025)

Two variants:
1. **Base**: Extract → Update → Store pipeline with tool-call mechanism for dedup/conflict resolution
2. **Graph-Enhanced (Mem0g)**: Adds knowledge graph layer with entity-relation triplets

Performance: 26% improvement over OpenAI approach. 91% lower p95 latency. 90%+ token cost savings.

#### Memoria (Dec 2025)

Four integrated modules: structured logging, dynamic user persona via KG, session summarization, semantic retrieval.

Recency-weighted prioritization: `w_i = e^(-a * x_i)` where a=0.02. Newer facts override older conflicting information.

Performance: 87.1% accuracy, 38.7% latency reduction.

#### MemoryOS (EMNLP 2025 Oral)

OS-inspired hierarchical storage: short-term → mid-term (FIFO) → long-term (segmented pages).

Performance: 49.11% F1 improvement, 46.18% BLEU-1 improvement over baselines.

### 4.4 Zep — Temporal Knowledge Graph for Agent Memory

> **Added in v3.1** — Deep dive from post-research discussion on Explicit vs Implicit memory.

#### Architecture: Built on Graphiti

Zep is built on top of **Graphiti** (Python library for temporal knowledge graphs), but adds a complete memory pipeline purpose-built for agent context engineering. While Graphiti provides the graph primitives, Zep builds the full ingestion → extraction → retrieval pipeline.

#### Ingestion Pipeline

When a message arrives, Zep processes it through a multi-stage pipeline:

```
Message → Episode Node (raw, immutable)
    → LLM extract entities (Person, Brand, Concept...)
    → Entity Resolution (exact match → fuzzy Levenshtein → LLM reasoning)
    → LLM extract facts/relationships ("User prefers premium positioning")
    → Edge Dedup + Contradiction Detection
    → Bi-temporal metadata (valid_at, invalid_at, created_at, expired_at)
    → Community Clustering (label propagation + LLM summarization)
    → Persist to Graph DB
```

Key features:
- **Bi-temporal tracking**: Every fact has two time axes — when it was TRUE in the real world (`valid_at`/`invalid_at`) and when it was RECORDED (`created_at`/`expired_at`). Enables point-in-time queries: "what did we know about competitor X as of last Tuesday?"
- **Contradiction detection**: When a new fact contradicts an existing one (e.g., user changes budget from "mid-range" to "premium"), the old fact is invalidated with `invalid_at` timestamp rather than deleted.
- **Community clustering**: Related entities are grouped via label propagation, then LLM-summarized. Creates high-level context ("this cluster is about Vietnamese F&B competitors").

#### Retrieval (Zero LLM Calls, P95 ~300ms)

```
Query → Cosine similarity + BM25 + Graph BFS traversal
    → Reranking (RRF / MMR)
    → ~1.6K tokens context injected
```

The retrieval path uses NO LLM calls — purely vector similarity, keyword matching, and graph traversal. This keeps latency low and costs predictable.

#### Benchmark Performance

- **~85% LoCoMo** — top performer among memory systems
- Compared to: Mem0 (~67%), MemGPT (~83%), full context (~73%)
- **Weakness**: -17.7% on "single-session-assistant" questions — details from conversation that weren't extracted as facts get LOST. This is precisely agent reasoning, assessments, and plans.

#### 3-Tier Graph Model

| Tier | Node Type | Content |
|---|---|---|
| **Episodes** | Raw conversation turns | Immutable, timestamped, source of truth |
| **Entities** | People, brands, concepts | Resolved, deduplicated, linked |
| **Communities** | Clusters of related entities | LLM-summarized, high-level context |

#### Complementary Analysis: Zep vs Workspace Notes

This analysis emerged from discussion on whether BrandMind needs implicit memory (Zep-like) in addition to explicit memory (workspace notes).

| Capability | Zep ✓/✗ | Workspace Notes ✓/✗ |
|---|---|---|
| Auto-extract entities/facts from conversation | **✓** | ✗ |
| Bi-temporal fact tracking (fact changes over time) | **✓** | ✗ |
| Contradiction detection & invalidation | **✓** | ✗ |
| Cross-session entity tracking | **✓** | ✗ |
| Community clustering (related entities) | **✓** | ✗ |
| Point-in-time queries ("last week what did we know?") | **✓** | ✗ |
| Evidence provenance (fact → source episode) | **✓** | ✗ |
| --- | --- | --- |
| Structured note-taking (SOAP, templates) | **✗** | **✓** |
| Decision reasoning (WHY, alternatives rejected) | **✗** | **✓** |
| Golden Thread (decision chain across phases) | **Partial** (provenance only) | **✓** |
| Progressive summarization | **✗** | **✓** |
| Session reflection / meta-learning | **✗** | **✓** |
| GTD inbox / pending items | **✗** | **✓** |
| Cross-project learning | **✗** (group_id isolation) | **✓** (learnings/) |
| Importance scoring | **✗** (all facts equal) | **✓** (Bloom level) |
| Agent-directed memory (agent chooses what to write) | **✗** (all automatic) | **✓** |

**Core insight**:

> **Zep handles "what happened" and "what's true now."**
> **Workspace notes handle "what do we think about it" and "what should we do next."**

Zep captures FACTS (who, what, when). Workspace notes capture REASONING (why, which alternatives, next steps). Zep's -17.7% weakness on single-session details is exactly the agent's own thinking — the thing workspace notes are designed to persist.

#### BrandMind Application

For current stage (single-user CLI, structured workflow): **workspace notes alone provide ~80% of personalization needs**. Zep-like implicit memory adds ~15% more (auto-detect user patterns, temporal queries, contradiction detection) but requires significant infrastructure (Graphiti + Memory Service + Redis Streams).

The structured workflow of BrandMind creates natural checkpoints (phase transitions) where the agent deliberately captures context — making explicit notes more reliable than auto-extraction for this specific use case. General chatbots without structured workflows benefit more from Zep's automatic extraction.

**Future integration**: Workspace notes serve as the **input interface** for implicit memory. Session reflections written to `working_notes.md` feed into Graphiti for cross-session entity extraction when the system scales to production.

---

#### Three-Layer Production Consensus

A pattern emerging across ALL production systems:

| Layer | Purpose | Implementation |
|---|---|---|
| **State Memory** | Current conditions, active workflows | Session state, workspace files |
| **Episodic Memory** | Immutable audit trail, time-travel | Append-only event store, timestamped |
| **Semantic Memory** | Shared knowledge, learned patterns | Embeddings, KGs, domain knowledge |

---

## 5. Synthesis: 6 Universal Patterns

Across ALL human groups (students, researchers, doctors, therapists, journalists, chess players) AND all AI systems (ChatGPT, MemGPT, Generative Agents, A-MEM, production systems), **six universal patterns** emerge:

### Pattern 1: Separation of Observation from Interpretation

Every effective system separates raw data from analysis:

| Group | Observation | Interpretation |
|---|---|---|
| Doctors | S (Subjective) + O (Objective) | A (Assessment) + P (Plan) |
| Researchers | Raw data in lab notebook | Conclusions and next experiments |
| Journalists | Source quotes with attribution | Story narrative |
| Chess players | Game moves | Post-mortem analysis |
| Students | Lecture notes (right column) | Cue questions (left column) |
| Therapists | Client statements (Data) | Clinical assessment |

**Why this matters**: Mixing observation and interpretation makes it impossible to revisit reasoning. Separating them enables re-evaluation when new information arrives without losing original evidence.

**BrandMind application**: SOAP structure in brand_brief.md. S/O = observations → A/P = interpretations. When new research contradicts a previous conclusion, the original evidence is preserved for re-analysis.

### Pattern 2: Forced Transformation (Not Just Storage)

Every effective system requires transforming information, not merely recording:

| Group | Transformation mechanism |
|---|---|
| Cornell | Summarize page, generate questions |
| Zettelkasten | Rewrite in own words, state connection reasons |
| Feynman | Simplify to a child's level |
| SOAP | Synthesize into Assessment |
| Golden Thread | Connect each note to treatment goals |
| Chess | Extract one actionable lesson per game |
| Progressive Summarization | Layer-by-layer distillation |

**The principle**: Systems that only store information (highlighting, copy-paste, bookmarking) produce dramatically lower retention and utility than systems that force cognitive processing.

**BrandMind application**: Phase transitions force transformation. Raw research (Phase 1) → compressed insights (brand_brief Phase 1 section) → executive summary update. The agent doesn't just "save findings" — it distills them.

### Pattern 3: The Golden Thread (Traceability)

Effective systems maintain a traceable chain from origin to outcome:

| Group | Thread |
|---|---|
| Therapists | Intake assessment → treatment plan → progress → discharge outcomes |
| Journalists | Source attribution for every factual claim |
| Doctors | Problem list → treatment → follow-up trajectory |
| Researchers | Hypothesis → experiment → conclusion |
| Chess players | Opening preparation → game → post-mortem lesson |

**BrandMind application**: Golden Thread in brand_brief.md and quality_gates.md. Every Phase N decision links backward to Phase 0 problem and forward to Phase N+1 implications. Thread Check before phase advance.

### Pattern 4: Structured Review Loop

Every group that improves over time has an explicit review mechanism:

| Group | Review mechanism | Frequency |
|---|---|---|
| Doctors | Follow-up visits, problem list review | Per visit |
| Therapists | Treatment plan review, outcome measurement | Monthly/quarterly |
| Chess players | Post-game analysis with error classification | Per game |
| Students | Spaced repetition review | Algorithmically scheduled |
| GTD | Weekly Review — process inboxes, update lists | Weekly |
| Researchers | Lab notebook review before new experiments | Per experiment |

**The key**: Systems without built-in review degrade into write-once archives. The review must be structured and focused on pattern extraction.

**BrandMind application**: Phase Transition Review = GTD Weekly Review. Process inbox, verify quality gates, verify Golden Thread, update executive summary, write session reflection. This prevents "workspace note rot."

### Pattern 5: Actionability (Every Note Leads to Action)

The most effective systems embed next-step thinking into note structure:

| Group | Actionability mechanism |
|---|---|
| SOAP | Plan section: "what to do next" |
| Golden Thread | Treatment plan with specific interventions and measurable outcomes |
| Chess | One-lesson rule: "what to practice next" |
| Journalism | Fact-check annotations: "what still needs verification" |
| GTD | Next Actions list: "what's the very next physical action?" |

**BrandMind application**: Every brand_brief.md phase section ends with P (Plan) — what comes next. quality_gates.md tracks specific actions needed before advancing. working_notes.md inbox items must be actionable or discardable.

### Pattern 6: Evidence Chain (Provenance)

Effective systems preserve how you know what you know:

| Group | Evidence mechanism |
|---|---|
| Journalists | Source, date, method of verification for every claim |
| Doctors | Objective findings backing Assessment |
| Researchers | Raw data underlying conclusions |
| Therapists | Client quotes supporting clinical assessment |
| Chess | Specific positions backing strategic conclusions |
| Zettelkasten | References on every permanent note |

**BrandMind application**: brand_brief.md A (Assessment) sections cite evidence from O (Objective): "Positioning based on: [O1] consumer survey data, [O2] competitive gap analysis." When user challenges a decision, agent traces evidence chain.

---

## 6. Storage Architecture

### 6.1 Why `~/.brandmind/` (Home Directory)

**Problem**: Current sessions store at `data/brand_strategy_sessions/` (relative to CWD). If user runs CLI from a different directory, data is lost or duplicated.

**Solution**: Home directory `~/.brandmind/`, matching industry standard:

| Tool | Storage location |
|---|---|
| Claude Code | `~/.claude/` |
| VS Code | `~/.vscode/` |
| npm | `~/.npm/` |
| Docker | `~/.docker/` |
| BrandMind | `~/.brandmind/` |

**Why not XDG** (`~/.local/share/brandmind/`): Simpler discoverability. `~/.brandmind/` is immediately obvious. XDG compliance can be added later via environment variable override.

**Why not project-local**: CLI runs from anywhere. Home directory guarantees consistency.

**Why not database**: Zero infrastructure requirement. Human-readable files. User can inspect/edit directly. MemGPT/Letta benchmark shows filesystem achieves 74% on LoCoMo — competitive with specialized systems.

### 6.2 Three-Layer Scoping

Three scoping layers solve the cross-project dedup problem:

| Layer | Scope | Lifetime | Example |
|---|---|---|---|
| **User** | Cross-project, global | Permanent | "User is junior marketer, prefers Vietnamese" |
| **Project** | Per-brand | Permanent | "Brand X positioned as modern craft" |
| **Session** | Per-conversation | Session lifetime | Message history, ephemeral context |

**Why 3 layers, not 2 or 4**:
- 2 layers (project + session) → user preferences duplicated per project, drift out of sync
- 4 layers (user + project + session + phase) → phase-level data lives naturally inside brand_brief.md sections, not in separate storage
- 3 layers: clean separation, each layer has distinct lifetime and scope

### 6.3 Directory Structure

```
~/.brandmind/
├── user/                              ← LAYER 1: User scope (global, cross-project)
│   └── profile.md                     ← Knowledge level, preferences, communication style
│
├── learnings/                         ← Cross-project knowledge (Tier 4/5 — empty placeholder)
│   └── (populated after project completion: abstract patterns, transferable insights)
│
├── projects/                          ← LAYER 2: Project scope (per-brand)
│   └── {project-slug}/
│       ├── project.json               ← Project metadata (brand name, scope, created_at)
│       ├── workspace/                 ← Agent-writable notes (3 files)
│       │   ├── brand_brief.md         ← Cumulative strategy document (SOAP + Progressive Summarization)
│       │   ├── working_notes.md       ← Scratchpad (Inbox + Observations + Ideas + Reflections)
│       │   └── quality_gates.md       ← Phase checklist + Golden Thread verification
│       └── sessions/                  ← LAYER 3: Session scope (per-conversation)
│           └── {session-id}.json      ← Session state + message history
│
└── index.json                         ← Project registry for discovery
```

---

## 7. File Architecture: The "Thinking Tool" Design

Every effective knowledge system (Zettelkasten, SOAP, Golden Thread, Cornell) doesn't just STORE information — it forces the practitioner to THINK in a specific way. **The structure IS the thinking process.**

Each workspace file enforces a distinct thinking mode:

| Thinking Mode | File | Enforces | Human Analog |
|---|---|---|---|
| **Cumulative** | brand_brief.md | Build on previous, synthesize, compress | Doctor POMR, researcher lab notebook |
| **Expansive** | working_notes.md | Capture everything, filter later, reflect | Journalist source list, Zettelkasten fleeting notes |
| **Critical** | quality_gates.md | Evaluate, verify connections, check completeness | Therapist Golden Thread, chess post-mortem |
| **Reflective** | working_notes.md (reflections section) | Learn from experience, extract patterns | Kolb cycle, coaching self-assessment |

### 7.1 brand_brief.md — Cumulative Thinking

**Combines**: SOAP (observation/interpretation separation) + Progressive Summarization (layered compression) + Golden Thread (decision traceability) + Bloom's Taxonomy (store high-order outputs)

**Template structure:**

```markdown
# Brand Brief: [Brand Name]

## Executive Summary (Progressive Summarization Layer 4)
[2-3 sentences capturing the entire strategy state. Updated EVERY phase transition.
This alone should restore 80% of context after compression or session resume.]

## Golden Thread (Decision Chain)
Problem → [Phase 0 insight] → Research confirms → [Phase 1 finding] →
Positioning → [Phase 2 choice] → Identity → [Phase 3 direction] → ...
[Single chain linking ALL major decisions back to the foundational problem.]

---

## Phase N: [Current Phase Name] (FULL DETAIL — Layer 1-2)

### S — What user told us
[User's goals, constraints, preferences, opinions for this phase]

### O — What we found
[Research data, metrics, competitive intelligence, social listening data]
[Each finding tagged: [O1], [O2], etc. for evidence chain]

### A — What we concluded
[Agent's analysis, insights, interpretations]
[Cite evidence: "Based on [O1] and [O3], we conclude..."]
[Include: Alternatives considered + why rejected]

### P — What's next
[Immediate next steps, pending decisions, open questions]

---

## Phase N-1: [Previous Phase] (COMPRESSED — Layer 3)
**Key findings**: [3-4 bullet points]
**Decision**: [What was decided + 1-line rationale]
**Linked to**: [Which later decisions depend on this phase's output]

## Phase N-2: [Earlier Phase] (COMPRESSED — Layer 3)
...
```

**Design rationale:**

| Feature | Source | What it solves |
|---|---|---|
| Executive Summary at top | Progressive Summarization Layer 4 | 5-second context restoration |
| Golden Thread | Therapist documentation | Decision traceability across phases |
| SOAP per phase | Medical POMR | Separates observation from interpretation |
| Evidence tags [O1], [O2] | Journalism evidence chain | Traceable source attribution |
| "Alternatives rejected" | Chess post-mortem | Records WHY options were eliminated |
| Previous phases compressed | Progressive Summarization Layer 2-3 | Prevents file bloat, saves context window |
| Current phase full detail | Bloom's Taxonomy | Higher-order outputs need full context |

### 7.2 working_notes.md — Expansive Thinking

**Combines**: GTD Inbox (capture everything) + Zettelkasten fleeting notes (temporary, to be processed) + Kolb Reflection (learn from experience) + Coaching self-assessment (evaluate own effectiveness) + Chess error classification (categorize failures)

**Template structure:**

```markdown
# Working Notes

## Inbox (GTD — process at phase transition)
- [Unprocessed item 1 — user mentioned X, needs triage]
- [Unprocessed item 2 — research finding, not yet synthesized]

## User Interaction Patterns (Per-project mentee context)
- [How user responds to different approaches]
- [Where user struggles, where they're confident]
- [Communication preferences specific to this project]

## Pending Questions (GTD Waiting For)
- [Question posed to user, awaiting response]
- [Decision that needs user input]

## Ideas & Hypotheses (Zettelkasten fleeting notes)
- [Creative ideas, potential directions, things to explore]
- [Parked ideas from user: "maybe we should also do X"]

## Session Reflections (Kolb + Chess one-lesson rule)
### Session [date]
- **What worked**: [tool/approach that produced good results]
- **What didn't**: [where things failed + error classification]
  - Data gap / Tool failure / Conceptual mismatch / User preference
- **User pattern**: [new observation about user interaction]
- **One lesson**: [Single transferable insight from this session]
```

**Design rationale:**

| Section | Source | What it solves |
|---|---|---|
| Inbox | GTD Capture + Clarify | Prevents "open loops" — everything captured, nothing forgotten |
| User Interaction Patterns | Coaching notes + therapist observation | Per-project mentee understanding (distinct from global profile) |
| Pending Questions | GTD Waiting For | Tracks what needs user response |
| Ideas & Hypotheses | Zettelkasten fleeting notes | Captures creative sparks without committing |
| Session Reflections | Kolb cycle Step 2-3 | Meta-learning: what worked, what didn't |
| Error classification | Chess post-mortem | Categorizes failures for pattern detection |
| One lesson | Chess one-lesson rule | Forces distillation: 1 session = 1 transferable insight |

### 7.3 quality_gates.md — Critical Thinking

**Combines**: Therapist Golden Thread verification + Chess post-mortem evaluation + Bloom's cognitive-level assessment

**Template structure:**

```markdown
# Quality Gates

## Phase N: [Current Phase]

### Gate Checklist
- [ ] [Specific deliverable or verification item]
- [ ] [Knowledge verified via KG/doc search, not just assumed]
- [ ] [User confirmed/approved key decisions]

### Thread Check (Golden Thread Verification)
- Does this phase's output SOLVE the Phase 0 problem? [Yes/No + evidence]
- Is it SUPPORTED by previous phases' research? [Yes/No + which findings]
- Will it GUIDE the next phase's work? [Yes/No + how]

### Readiness Assessment
- Confidence: [High/Medium/Low]
- Known gaps: [What's missing but acceptable to proceed]
- Risks: [What could go wrong in the next phase based on this output]
```

**Design rationale:**

| Feature | Source | What it solves |
|---|---|---|
| Gate checklist | Therapist treatment plan milestones | Prevents skipping steps |
| Thread Check | Golden Thread traceability | Ensures every phase connects to the whole |
| Readiness Assessment | Chess evaluation + Bloom's Evaluate level | Forces judgment, not just checklist completion |

### 7.4 user/profile.md — User Understanding

**Combines**: MemGPT's "Human" core memory block + Therapist intake assessment + Coaching discovery notes

**Template structure:**

```markdown
# User Profile

## Identity
- Role: [e.g., Junior marketing executive, 2 years experience]
- Industry expertise: [what they know well vs. learning]
- Language: [Vietnamese preferred, English technical terms OK]

## Communication Preferences
- [e.g., Prefers concise answers, asks "tai sao?" often]
- [e.g., Needs data support before accepting bold recommendations]
- [e.g., Visual learner — show examples, not just describe]

## Constraints
- [e.g., No in-house designer, outsources creative]
- [e.g., Budget sensitivity: mid-range, ROI-focused]
- [e.g., Boss wants ROI numbers in all proposals]

## Working Style
- [e.g., Detail-oriented in research phase, faster in creative]
- [e.g., Prefers to see 2-3 options before deciding]
```

**Why global (not per-project)**: These facts are stable across projects. "User prefers Vietnamese" doesn't change between brand strategy sessions. Per-project user observations (Phase 2 went smoothly, user struggled with competitive analysis) live in working_notes.md instead.

**Character budget**: ~2K characters. Following MemGPT's core memory block design — small enough to always fit in context, forces selectivity about what's truly important.

---

## 8. Design Evolution: v1 → v2 → v3

### v1: Initial Design (from memory/project_workspace_notes.md)

```
/workspace/
├── brand_brief.md       ← Free-form cumulative document
├── user_profile.md      ← User preferences (per-project)
├── session_context.md   ← Current session state
└── quality_gates.md     ← Phase checklist
```

**Limitations identified:**
- Storage at project-local directory (CWD-dependent)
- user_profile duplicated per-project (dedup problem)
- No cross-project learning mechanism
- Free-form brand_brief with no structure → unpredictable content
- session_context.md purpose unclear (overlaps with working notes)

### v2: Consultant-Mapped Design

```
~/.brandmind/
├── user/profile.md                  ← Global (cross-project dedup solved)
├── learnings/                       ← Cross-project (placeholder)
├── projects/{slug}/
│   ├── workspace/
│   │   ├── brand_brief.md           ← Template per phase + decision rationale
│   │   ├── working_notes.md         ← Flexible scratchpad (replaced research_notes.md)
│   │   └── quality_gates.md         ← Checklist
│   └── sessions/{id}.json
└── index.json
```

**Improvements over v1:**
- Home directory storage (location-independent)
- Three-layer scoping (user/project/session)
- research_notes.md → working_notes.md (more flexible)
- Decision rationale captured in brand_brief

**Remaining gaps:**
- No reflection mechanism (no meta-learning)
- No Golden Thread (no traceability across phases)
- brand_brief mixes observation with interpretation
- No progressive summarization (file grows unbounded)
- No inbox/pending tracking (GTD gap)

### v3: Final Design (Cross-Discipline + AI Systems Research)

```
~/.brandmind/
├── user/profile.md                  ← Global (MemGPT "Human" block)
├── learnings/                       ← Cross-project schemas (Kolb Step 3-4, future)
├── projects/{slug}/
│   ├── workspace/
│   │   ├── brand_brief.md           ← SOAP + Progressive Summarization + Golden Thread
│   │   ├── working_notes.md         ← GTD Inbox + Observations + Reflections (Kolb)
│   │   └── quality_gates.md         ← Checklist + Thread Check (Golden Thread verification)
│   └── sessions/{id}.json
└── index.json
```

**What v3 adds over v2:**

| Addition | Source inspiration | Solves |
|---|---|---|
| SOAP per phase in brand_brief | Doctors (POMR) | Observation/interpretation separation |
| Progressive summarization | BASB (Tiago Forte) | File bloat, context window efficiency |
| Golden Thread chain | Therapists | Decision traceability across phases |
| Evidence tags [O1], [O2] | Journalists | Source attribution for decisions |
| Inbox section | GTD (David Allen) | Unprocessed items don't get lost |
| Session reflections | Kolb/Schon + chess one-lesson rule | Meta-learning, getting better over time |
| Error classification | Chess post-mortem | Pattern detection in failures |
| Thread Check | Golden Thread verification | Quality assurance at phase transitions |
| User interaction patterns | Coaching notes | Per-project mentee understanding |
| Readiness Assessment | Bloom's Evaluate level | Confidence-aware phase advancement |

**File count**: 3 project files + 1 global file = 4 total. Same as MemGPT's "core memory blocks" count. Minimal cognitive overhead, maximum structure.

### v3.1: Post-Research Discussion Decisions

> **Added in v3.1** — Documents key architectural decisions made during discussion after v3 design was finalized.

#### Decision 1: Explicit Memory Sufficient for Current Stage

**Question**: Does BrandMind need implicit memory (Zep-like auto-extraction) in addition to explicit memory (workspace notes) for its "personalized mentor" goal?

**Analysis — mapping 6 personalization needs**:

| Need | Workspace Notes (Explicit) | Zep-like (Implicit) | Gap if Explicit only? |
|---|---|---|---|
| Remember user identity | `user/profile.md` — agent writes manually | Auto-extract from conversation | **Small** — info rarely changes, write once |
| Adapt teaching style | `working_notes.md` observations | Auto-detect patterns cross-sessions | **Medium** — agent must remember to note, but phase transitions are natural checkpoints |
| Remember project context | `brand_brief.md` SOAP — designed for this | Auto-extract facts + temporal tracking | **Very small** — brand_brief covers 95% |
| Track user growth | Session reflections in working_notes | Auto-pattern detection cross-sessions | **Medium** — manual observation vs automatic |
| Remember across sessions | brand_brief + working_notes | Temporal query: "last week discussed what?" | **Some gap** — casual remarks not captured in notes |
| Cross-project transfer | `learnings/` (manual) | Entity linking across group_ids | **Some gap** — depends on agent writing learnings |

**80/20 analysis**:

| Option | Effort | Personalization coverage | ROI |
|---|---|---|---|
| **Workspace Notes only** | ~1-2 weeks | ~80% needs | **Very high** |
| **+ Zep-like Implicit** | +4-8 weeks (Graphiti + Memory Service + Redis Streams + testing) | +15% (→ ~95%) | **Low for current stage** |

**Conclusion**: Workspace notes = sufficient for current stage because:
1. **Structured workflow** creates natural checkpoints (phase transitions) → agent knows WHEN and WHAT to capture
2. **4 files** cover 80% of personalization needs
3. **Phase transition hooks** enforce note discipline → more reliable than general chatbot
4. **Single user CLI** → auto-extraction scale not needed
5. **Infrastructure cost** of Graphiti + Memory Service + Redis Streams is disproportionate for 1 user

**When to add implicit memory**: Multi-user production, 50+ sessions needing cross-reference, cross-project transfer as real (not theoretical) need, infrastructure already running.

#### Decision 2: No Consolidation Agent

**Idea considered**: End-of-session LLM call to review conversation + workspace notes, identify gaps, auto-fix.

**Rejected for 3 reasons**:

1. **Complexity**: Not a single LLM call — needs to read session transcript → read each workspace file → compare → identify gaps → decide what to fix → fix precisely. This is deep agent work, not a prompt call.

2. **Quality risk (the core problem)**: Consolidation agent lacks the main agent's THINKING CONTEXT.

   ```
   Main agent during session:
     → User mentions TikTok strategy
     → Agent DELIBERATELY decides: "not relevant for Phase 1, don't note"
     → This is a correct JUDGMENT call

   Consolidation agent post-session:
     → Sees: user mentioned TikTok, workspace has nothing about it
     → Concludes: "gap, need to add"
     → Adds to working_notes → WRONG, main agent intentionally omitted
   ```

3. **False gap detection**: Consolidation agent would over-capture — any conversation content absent from notes appears as a "gap." But not everything users say needs recording. The main agent working WITH the user has the best judgment about what matters.

**Principle reaffirmed**: Workspace is a THINKING TOOL, not a DATA CAPTURE tool. Value lies in DELIBERATE synthesis. Adding a second agent to "fill gaps" transforms it from thinking tool into data dump — destroying the core value.

**Alternative chosen**: Make the main agent write notes BETTER (structured templates, phase transition hooks), not add a second agent to clean up after.

#### Decision 3: Pre-Compact Hook (Merged into Tier 3)

**Problem**: Phase transition hooks capture context at phase boundaries. But context window can fill up MID-PHASE (e.g., during long Phase 1 research). When summarization triggers, information is lost before any phase transition hook fires.

**Solution**: Pre-compact hook = "auto-save" safety net, complementary to phase transition hooks ("Save As").

```
Phase transition hooks = "Save As" (manual, deliberate, comprehensive)
Pre-compact hook       = "Auto-save" (automatic, safety net, incremental)
```

**Design**:

```python
# Pseudo-code
class PreCompactNotesMiddleware:
    trigger_threshold = 0.60-0.70  # 60-70% of context window
    # Must trigger BEFORE SummarizationMiddleware (80%)

    def before_model_call(self, messages, context):
        current_tokens = count_tokens(messages)
        if current_tokens > self.trigger_threshold * context_window:
            if not self._already_reminded_this_cycle:
                inject_system_reminder(messages, PRE_COMPACT_INSTRUCTION)
                self._already_reminded_this_cycle = True
        # Flag resets after summarization fires
```

**Critical rules**:

1. **APPEND/EDIT only, never rewrite** — agent edits specific sections that changed, never rewrites entire files. Prevents quality degradation and accidental overwrite of good content.

2. **Specific instructions, not generic**:
   ```
   ❌ Generic (invites sloppy notes):
   "Update your workspace notes before context compression."

   ✓ Specific (guided incremental save):
   "Context approaching limit. Quick incremental save:
   1. brand_brief.md — Is current phase S/O/A/P section up to date?
      If not, EDIT the specific section that changed. Do NOT rewrite other phases.
   2. working_notes.md — Any new inbox items or observations since last update?
      APPEND only. Do NOT rewrite existing content.
   3. quality_gates.md — Any gates newly completed? Mark them.
   Skip files that are already current."
   ```

3. **Trigger once per compact cycle** — flag resets after summarization fires. Prevents repeated nagging.

**Race condition mitigation**: Pre-compact triggers at ~60-70%, summarization at ~80%. Buffer of ~10-20% provides room for 3-4 tool calls (read + edit workspace files) before summarization kicks in.

**UX consideration**: Agent can handle transparently (update notes before responding to user) or acknowledged ("Let me save progress first" → update → continue). Both acceptable.

#### Decision 4: Architecture Diagram Alignment

The BrandMind architecture diagram (designed before research) aligns precisely with research findings:

| Diagram Component | Research Equivalent |
|---|---|
| **Explicit → Notes (Artifact) → Filesystem** | Workspace notes (Tier 3) = MemGPT "Core Memory" blocks |
| **Implicit → Procedural → Skills + Filesystem** | Agent Skills (read-only) — already implemented |
| **Implicit → Semantic → 2 KG layers** | Industry pattern: static domain knowledge + dynamic agent knowledge |
| **Implicit → Episodic → Temporal KG (Zep)** | Generative Agents' "Memory Stream" + reflection |
| **Hook/Middleware (4)** | Context Editing, Summarization, ToolSearch — already implemented |
| **(1) Planning → (2) Delegation** | TodoWrite + SubAgentMiddleware — already implemented |

**Key validation from research**: The Explicit/Implicit split in the diagram maps directly to the fundamental distinction found across ALL memory systems studied — agent-directed writing (explicit) vs system-automated extraction (implicit). Both are needed for full personalization, but explicit alone is sufficient for current stage.

**Workspace notes placement in the architecture**:

```
Persistent Memory (3)
├── Explicit
│   └── Notes (Artifact) ⭐          ← IMPLEMENTING NOW (Tier 3)
│       └── Filesystem
│           ├── /workspace/brand_brief.md      (SOAP + Progressive Summarization)
│           ├── /workspace/working_notes.md    (GTD Inbox + Reflections)
│           ├── /workspace/quality_gates.md    (Golden Thread)
│           └── /user/profile.md               (Cross-project)
│
├── Implicit
│   ├── Procedural → Skills (already implemented)
│   ├── Semantic → Domain KG (already implemented) + Temporal KG (Tier 4+)
│   └── Episodic → Temporal KG (Tier 4+)
│       ↑
│       Session reflections from working_notes.md FEED into here
```

**Flow between Explicit → Implicit (future)**:
1. Agent writes reflection in `working_notes.md` (Explicit, filesystem)
2. End-of-session → Memory Service picks up via Redis Stream (planned in MEMORY_ARCHITECTURE.md)
3. Graphiti extracts entities, events, patterns (Implicit, async)
4. Store in Temporal KG (Episodic + Semantic)
5. Next session → agent queries temporal KG for cross-session knowledge

Workspace notes = **input interface** for the entire memory pipeline. They don't replace implicit memory — they **feed** into it.

---

## 9. Implementation: DeepAgents API Mapping

### Backend Architecture

The DeepAgents framework provides exactly the primitives needed:

```python
from deepagents.backends.composite import CompositeBackend
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemMiddleware

# Read-only: skills
skills_backend = FilesystemBackend(
    root_dir=SKILLS_DIR,
    virtual_mode=True,
)

# Read-write: project workspace
workspace_backend = FilesystemBackend(
    root_dir=f"~/.brandmind/projects/{project_slug}/workspace/",
    virtual_mode=True,
)

# Read-write: user profile (global)
user_backend = FilesystemBackend(
    root_dir="~/.brandmind/user/",
    virtual_mode=True,
)

# Composite routes
composite = CompositeBackend(
    default=skills_backend,          # /skills/* (read-only)
    routes={
        "/workspace/": workspace_backend,  # /workspace/* (read-write, per-project)
        "/user/": user_backend,            # /user/* (read-write, global)
    },
)

# Single middleware exposes all three backends
fs_middleware = FilesystemMiddleware(backend=composite)
```

### Agent's Virtual View

```
/                                    ← Skills (read-only)
  brand-strategy-orchestrator/
    SKILL.md
    references/
  market-research/
    SKILL.md
  ...

/workspace/                          ← Project workspace (read-write)
  brand_brief.md
  working_notes.md
  quality_gates.md

/user/                               ← Global profile (read-write)
  profile.md
```

The agent doesn't know physical paths. CompositeBackend routes transparently. `read_file("/workspace/brand_brief.md")` resolves to `~/.brandmind/projects/{slug}/workspace/brand_brief.md` on disk.

### Key CompositeBackend Behaviors

- **Longest-prefix-first matching**: Routes sorted by prefix length. `/workspace/notes/` matches before `/workspace/` if both exist.
- **Path stripping**: Backend sees stripped path. `/workspace/brand_brief.md` → backend receives `/brand_brief.md`.
- **Aggregate ls**: At `/`, lists all backends' root contents. Agent can discover what's available.
- **Cross-backend grep**: At `/`, grep merges results from all backends.

---

## 10. Scalability Path

### Tier 3 (Now): Filesystem Workspace Notes

- Agent reads/writes markdown files via FilesystemMiddleware
- brand_brief.md loaded into context as MemGPT-style "core memory block"
- File-based, zero infrastructure, human-readable
- Sufficient for single-user CLI

### Tier 4 (Future): Episodic Memory + Cross-Project Learning

- `sessions/` directory gets indexed — search prior sessions: "last time we researched F&B competitors, what did we find?"
- Session reflections distill into `learnings/` — abstract patterns extracted (Kolb Step 3)
- Milvus (already in stack) embeds session summaries for semantic search
- **Agent interface unchanged** — still `read_file()` and `write_file()`

### Tier 5 (Future): Semantic Memory + Full Personalization

- Atomic linked notes (A-MEM/Zettelkasten style) replace monolithic files
- Knowledge graph stores agent-discovered patterns alongside curated marketing knowledge
- Importance scoring + recency decay for memory prioritization (spaced repetition)
- Double-loop learning: agent questions its own reasoning patterns
- Schema extraction for far transfer across industries
- **Agent interface unchanged** — backend switches from FilesystemBackend to StoreBackend/custom backend. Agent tools remain identical.

### The Core Architectural Principle

> **Separate the memory interface (what the agent reads/writes) from the storage backend (where it persists).**

Start with files. Graduate to database when concurrency, search, or scale demands it. The agent's tools NEVER change — only the backend behind them.

This matches the industry consensus: MemGPT, OpenAI Agents SDK, and Google Project Astra all converge on a "virtual filesystem" pattern where the agent sees a clean file interface while the storage backend can be anything.

### Revised Scalability Path (v3.1)

> **Added in v3.1** — Refined tier progression based on discussion about Explicit vs Implicit memory, consolidation agents, and pre-compact hooks. The original Tier 3/4/5 above remains the long-term vision. This revised path adds intermediate steps and clarifies what triggers each tier.

```
Tier 3 (Now):      Workspace Notes + Phase Transition Hooks + Pre-compact Hook
                    ├── Agent reads/writes 4 markdown files (filesystem)
                    ├── Phase transition hooks ÉP agent update notes before advancing
                    ├── Pre-compact hook auto-reminds at ~60-70% context window
                    └── Sufficient for single-user CLI, ~80% personalization

Tier 3.5 (Soon):   + End-of-session Validation
                    ├── Lightweight CHECK at session end (not fix)
                    ├── "brand_brief current phase filled? [✓/✗]"
                    ├── "working_notes inbox processed? [✓/✗]"
                    ├── "quality_gates current phase checked? [✓/✗]"
                    ├── "user/profile any new observations? [✓/✗]"
                    └── WARN user if gaps found, do NOT auto-fix

Tier 4 (When needed): + Zep-like Implicit Memory
                    ├── Graphiti + FalkorDB (already in stack)
                    ├── Memory Service via Redis Streams (planned in MEMORY_ARCHITECTURE.md)
                    ├── Auto-extract entities/facts from conversation
                    ├── Bi-temporal tracking, contradiction detection
                    └── Trigger: multi-user production, 50+ sessions, cross-project transfer needed
```

**What changed from original path**:
- Tier 3 now includes pre-compact hook (was not in original)
- Tier 3.5 added as intermediate step (validation without auto-fix)
- Tier 4 replaces both original Tier 4 AND 5 — Zep/Graphiti covers episodic + semantic in one system
- Consolidation agent explicitly excluded from all tiers (see Decision 2 in Section 8)

**Explicit → Implicit feed flow (Tier 3 → Tier 4)**:

```
DURING SESSION (Tier 3 — Explicit):
  Agent writes workspace notes deliberately
  ├── brand_brief.md: SOAP per phase, Golden Thread, Executive Summary
  ├── working_notes.md: Inbox items, observations, session reflections
  ├── quality_gates.md: Gate status, thread checks
  └── user/profile.md: User preferences, communication style

END OF SESSION (Tier 4 — bridge):
  Memory Service picks up session via Redis Stream
  ├── Graphiti extracts entities, events, facts from conversation
  ├── Session reflections from working_notes.md → extracted as episodic nodes
  ├── User patterns from profile.md → validated/enriched as semantic facts
  └── Bi-temporal metadata attached to all extracted knowledge

NEXT SESSION (Tier 4 — Implicit retrieval):
  Agent queries temporal KG for cross-session knowledge
  ├── "Last time we researched F&B competitors, what did we find?"
  ├── "Has user's budget preference changed over time?"
  └── Entity linking across projects for pattern detection
```

Workspace notes remain the **input interface** at all tiers. They don't get replaced — they get **augmented** by implicit memory's queryability and cross-session linking.

---

## 11. References

### Human Knowledge Management

- Pauk, W. (1962). *How to Study in College*. Cornell Note-Taking System.
- Ahrens, S. (2017). *How to Take Smart Notes*. Zettelkasten method.
- Forte, T. (2022). *Building a Second Brain*. PARA + CODE + Progressive Summarization.
- Allen, D. (2001). *Getting Things Done*. GTD methodology.
- Feynman, R. (1985). *Surely You're Joking, Mr. Feynman!* Feynman Technique.
- Ebbinghaus, H. (1885). *Uber das Gedachtnis*. Forgetting curve.
- Bloom, B. (1956). *Taxonomy of Educational Objectives*. Bloom's Taxonomy.
- Anderson, L. & Krathwohl, D. (2001). Revised Bloom's Taxonomy.
- Kolb, D. (1984). *Experiential Learning*. Learning cycle.
- Schon, D. (1983). *The Reflective Practitioner*. Reflection-in-action.
- Argyris, C. & Schon, D. (1978). *Organizational Learning*. Double-loop learning.
- Weed, L. (1968). "Medical records that guide and teach." *NEJM*. SOAP/POMR.
- Dunlosky, J. et al. (2013). "Improving Students' Learning With Effective Learning Techniques." *Psychological Science in the Public Interest*.

### AI Agent Memory Systems

- Packer, C. et al. (2023). "MemGPT: Towards LLMs as Operating Systems." [arXiv:2310.08560](https://arxiv.org/abs/2310.08560)
- Park, J.S. et al. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." [arXiv:2304.03442](https://arxiv.org/abs/2304.03442)
- Wang, G. et al. (2023). "Voyager: An Open-Ended Embodied Agent with Large Language Models." [arXiv:2305.16291](https://arxiv.org/abs/2305.16291)
- Shinn, N. et al. (2023). "Reflexion: Language Agents with Verbal Reinforcement Learning." NeurIPS 2023. [arXiv:2303.11366](https://arxiv.org/abs/2303.11366)
- Xu, W. et al. (2025). "A-MEM: Agentic Memory for LLM Agents." NeurIPS 2025. [arXiv:2502.12110](https://arxiv.org/abs/2502.12110)
- Chheda, T. et al. (2025). "Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory." [arXiv:2504.19413](https://arxiv.org/abs/2504.19413)
- Zhou, Y. et al. (2025). "Memoria: Structured User Personas for AI Memory." [arXiv:2512.12686](https://arxiv.org/abs/2512.12686)
- Jia, Z. et al. (2025). "MemoryOS: Hierarchical Storage for LLM Agents." EMNLP 2025 Oral. [arXiv:2506.06326](https://arxiv.org/abs/2506.06326)
- Zhou, Y. et al. (2026). "Memory in the Age of AI Agents: A Survey." [arXiv:2512.13564](https://arxiv.org/abs/2512.13564)
- Sun, Y. et al. (2025). "Lifelong Learning of LLM Agents: A Roadmap." IEEE TPAMI. [arXiv:2501.07278](https://arxiv.org/abs/2501.07278)
- Zhang, G. et al. (2025). "SAGE: Self-evolving Agents with Reflective and Memory-augmented Abilities." [arXiv:2409.00872](https://arxiv.org/abs/2409.00872)
- Zhou, H. et al. (2024). "Language Agent Tree Search (LATS)." ICML 2024. [arXiv:2310.04406](https://arxiv.org/abs/2310.04406)
- Salemi, A. & Zamani, H. (2025). "A Survey of Personalization of LLMs." [arXiv:2502.11528](https://arxiv.org/abs/2502.11528)
- OpenAI (2025). "Context Personalization with Agents SDK." [Cookbook](https://developers.openai.com/cookbook/examples/agents_sdk/context_personalization).
- Netflix (2025). "Foundation Model for Personalized Recommendation." [TechBlog](https://netflixtechblog.com/foundation-model-for-personalized-recommendation-1a0bd8e02d39).

### Production Systems Analysis

- Reverse Engineering ChatGPT Memory: [llmrefs.com](https://llmrefs.com/blog/reverse-engineering-chatgpt-memory)
- Reverse Engineering Claude Memory: [manthanguptaa.in](https://manthanguptaa.in/posts/claude_memory/)
- Gemini Memory Analysis: [shloked.com](https://www.shloked.com/writing/gemini-memory)
- Microsoft Copilot Memory: [learn.microsoft.com](https://learn.microsoft.com/en-us/copilot/microsoft-365/copilot-personalization-memory)
- Letta Benchmark ("Is a Filesystem All You Need?"): [letta.com](https://www.letta.com/blog/benchmarking-ai-agent-memory)
- Three-Layer Production Architecture: [tacnode.io](https://tacnode.io/post/ai-agent-memory-architecture-explained)
