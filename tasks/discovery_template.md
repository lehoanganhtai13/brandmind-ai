# Discovery: [Feature / Initiative Name]

> **Purpose of this document**: This is a living document for the pre-planning phase.
> Use it to brainstorm, research, and make decisions BEFORE creating task files.
> The output of this phase is a confirmed `summary.md` that feeds directly into the task breakdown.
>
> **Typical flow**:
> 1. User describes the idea (can be rough/incomplete)
> 2. Agent asks clarifying questions, then researches
> 3. Agent presents findings + options → User makes decisions
> 4. Both confirm the final summary → Agent creates the task file list

## 📌 Metadata

- **Date Started**: [YYYY-MM-DD]
- **Initiated by**: [User / Team]
- **Status**: 🔍 Exploring / 💬 Discussing / ✅ Decided / 📋 Tasks Created
- **Related Epic**: [Epic or product area]
- **Output**: [Link to summary.md when finalized]

### Discovery Checklist

- [ ] 🎯 [Problem Definition](#-problem-definition) — Confirmed with user
- [ ] ❓ [Clarifying Questions](#-clarifying-questions) — All answered
- [ ] 🔍 [Research & Analysis](#-research--analysis) — Agent research complete
- [ ] ⚖️ [Options Analysis](#-options-analysis) — Options presented to user
- [ ] ✅ [Decision](#-decision) — User has confirmed the approach
- [ ] 📋 [Task Breakdown](#-task-breakdown) — Tasks created and linked

------------------------------------------------------------------------

## 🎯 Problem Definition

> **Agent**: Before asking questions, write down your initial understanding of the problem.
> Then identify gaps and ask the user to fill them in.

### Initial Understanding

[Agent writes their initial interpretation of what the user wants to build and why]

### Problem Statement

> *Fill this in collaboratively with the user before proceeding*

**The problem**: [Describe the current situation and pain point]

**Who is affected**: [Users, systems, or teams impacted]

**Why now**: [What makes this important or urgent]

**Definition of done**: [In 1–2 sentences, what does success look like?]

### Scope Boundary

| In Scope | Out of Scope |
|----------|--------------|
| [What this initiative WILL address] | [What it will NOT address] |
| [Feature / behavior included] | [Adjacent feature explicitly excluded] |

------------------------------------------------------------------------

## ❓ Clarifying Questions

> **Agent**: List all questions needed to fully understand the requirements.
> Ask them all at once — do not ask one at a time. Wait for user answers before proceeding.

### Questions for User

- [ ] **Q1**: [Question about requirements, constraints, or priorities]
- [ ] **Q2**: [Question about expected behavior or edge cases]
- [ ] **Q3**: [Question about integration with existing systems]
- [ ] **Q4**: [Question about non-functional requirements — performance, scale, security]
- [ ] **Q5**: [Question about timeline or phasing preferences]

### User Answers

> *Record answers here as the user responds*

- **Q1**: [Answer]
- **Q2**: [Answer]
- **Q3**: [Answer]
- **Q4**: [Answer]
- **Q5**: [Answer]

------------------------------------------------------------------------

## 🔍 Research & Analysis

> **Agent**: Run this research phase autonomously. Use web search, context7 docs,
> and codebase exploration. Log findings here before presenting them to the user.

### Codebase Audit

**Goal**: Understand existing patterns, adjacent features, and potential integration points.

- **Files / modules reviewed**:
  - `[path/to/file.py]` — [What it does and what's relevant]
  - `[path/to/file.py]` — [What it does and what's relevant]

- **Existing patterns to follow**: [Describe conventions, base classes, middleware patterns, etc.]

- **Technical debt or gotchas**: [Anything that might complicate implementation]

- **Conflicts or overlaps**: [Any existing code that does something similar or conflicts]

### Technology / Library Research

| Library / Tool | Version | Purpose | Key Findings |
|---------------|---------|---------|--------------|
| [Name] | [version] | [Why relevant] | [API behavior, limitations, gotchas] |
| [Name] | [version] | [Why relevant] | [API behavior, limitations, gotchas] |

### Competitive / Industry Reference

> *Fill if relevant — e.g., how do other products solve this problem?*

- **[Reference 1]**: [What they do and what we can learn]
- **[Reference 2]**: [What they do and what we can learn]

### Key Constraints Identified

- **Technical**: [Hard technical limits — e.g., "library X doesn't support Y"]
- **Performance**: [Bottlenecks or scaling concerns discovered]
- **Security**: [Auth, data privacy, or injection risks to address]
- **Dependency**: [External services, APIs, or other tasks this depends on]

------------------------------------------------------------------------

## ⚖️ Options Analysis

> **Agent**: Present 2–3 concrete implementation options with honest trade-offs.
> Do NOT advocate for one option — present them neutrally and let the user decide.
> If one option is clearly inferior, you may note that, but still present it.

### Option A: [Option Name]

**Summary**: [1–2 sentence description]

**How it works**:
[Brief technical explanation — what gets built, how components interact]

**Pros**:
- [Advantage 1]
- [Advantage 2]

**Cons**:
- [Disadvantage 1]
- [Disadvantage 2]

**Effort estimate**: [X days / X weeks]
**Risk level**: Low / Medium / High — [brief reason]

---

### Option B: [Option Name]

**Summary**: [1–2 sentence description]

**How it works**:
[Brief technical explanation]

**Pros**:
- [Advantage 1]
- [Advantage 2]

**Cons**:
- [Disadvantage 1]
- [Disadvantage 2]

**Effort estimate**: [X days / X weeks]
**Risk level**: Low / Medium / High — [brief reason]

---

### Option C: [Option Name] *(if applicable)*

**Summary**: [1–2 sentence description]

**Pros**: [Advantages]
**Cons**: [Disadvantages]
**Effort estimate**: [X days]
**Risk level**: Low / Medium / High

---

### Comparison Matrix

| Criteria | Option A | Option B | Option C |
|----------|----------|----------|----------|
| Development effort | [Low/Med/High] | [Low/Med/High] | [Low/Med/High] |
| Maintainability | [Low/Med/High] | [Low/Med/High] | [Low/Med/High] |
| Performance | [Low/Med/High] | [Low/Med/High] | [Low/Med/High] |
| Risk | [Low/Med/High] | [Low/Med/High] | [Low/Med/High] |
| Aligns with existing patterns | Yes / No / Partial | Yes / No / Partial | Yes / No / Partial |

------------------------------------------------------------------------

## ✅ Decision

> *This section is filled in after the user reviews the Options Analysis.*
> *The user decides; the agent documents and confirms.*

### Chosen Approach

**Decision**: Option [X] — [Option Name]

**Decided by**: [User / Team]
**Date**: [YYYY-MM-DD]

**Rationale** *(in user's own words or paraphrased)*:
[Why this option was chosen — what factors mattered most]

### Adjustments / Hybrid

[If the chosen approach has modifications from the original option, document them here]

### Deferred Items

[Features or sub-problems that are explicitly deferred to a later task or phase]

- **[Item]**: Deferred because [reason]. Will revisit in [timeframe / trigger condition].

------------------------------------------------------------------------

## 📋 Task Breakdown

> **Agent**: Based on the confirmed decision, break the work into discrete task files.
> Each task should be independently implementable by the coding agent.
> Create the task files using `task_template.md` and link them below.

### Proposed Tasks

| Task # | Title | Effort | Blocking | Blocked By | Priority |
|--------|-------|--------|----------|------------|----------|
| Task XX | [Title] | [X days] | [Task YY, ZZ] | [Task AA] | High |
| Task YY | [Title] | [X days] | [Task ZZ] | [Task XX] | High |
| Task ZZ | [Title] | [X days] | [] | [Task YY] | Medium |

### Dependency Graph

```
Task XX (Foundation)
└── Task YY (depends on XX)
    └── Task ZZ (depends on YY)

Task AA (Independent)
```

### Implementation Order

1. **Task XX** — [Why this goes first]
2. **Task YY** — [Why this comes second]
3. **Task ZZ** — [Why this comes last]

### Task Files Created

- [ ] `tasks/task_XX.md` — [Title]
- [ ] `tasks/task_YY.md` — [Title]
- [ ] `tasks/task_ZZ.md` — [Title]

------------------------------------------------------------------------

## 📄 Summary

> **Purpose**: This section is the canonical output of the Discovery phase.
> It should be self-contained enough that anyone (or any agent) can read this
> section alone and understand what was decided and why.
> Save this as `docs/[feature]-summary.md` if it needs to persist beyond the task files.

### What We're Building

[2–4 sentences describing what will be built, for what purpose, and how it fits into the product]

### Why This Approach

[2–3 sentences explaining the key rationale behind the chosen solution]

### What's Explicitly Not Included

[List items that were considered and rejected or deferred]

### Key Constraints and Risks

- [Constraint / Risk 1 and mitigation]
- [Constraint / Risk 2 and mitigation]

### Definition of Done

- [ ] [Verifiable outcome 1]
- [ ] [Verifiable outcome 2]
- [ ] [Verifiable outcome 3]

------------------------------------------------------------------------
