# Task 49: Workspace Notes — System Prompt & Context Restoration (Phase B)

## 📌 Metadata

- **Epic**: Brand Strategy — Persistent Memory (Tier 3)
- **Priority**: High
- **Status**: Done
- **Estimated Effort**: 1.5 days
- **Team**: Backend
- **Related Tasks**: Task 46 (System Prompt — original creation), Task 48 (Storage Layer — prerequisite)
- **Blocking**: Task 50 (Enforcement Hooks)
- **Blocked by**: Task 48 (workspace must be accessible before agent can be instructed to use it)

### ✅ Progress Checklist

- [x] 🤖 [Agent Protocol](#-agent-protocol) — Read and confirm before starting
- [x] 🎯 [Context & Goals](#-context--goals) — Problem definition and success metrics
- [x] 🛠 [Solution Design](#-solution-design) — Architecture and technical approach
- [x] 🔬 [Pre-Implementation Research](#-pre-implementation-research) — Findings logged before coding
- [x] 🔄 [Implementation Plan](#-implementation-plan) — Phased execution plan confirmed with user
- [x] 📋 [Implementation Detail](#-implementation-detail) — Component-level specs with test cases
    - [x] ✅ [Component 1: Workspace Notes System Prompt Section](#component-1-workspace-notes-system-prompt-section) — Done
    - [x] ✅ [Component 2: Session Resume Awareness](#component-2-session-resume-awareness) — Done
- [x] 🧪 [Test Execution Log](#-test-execution-log) — All tests run and results recorded
- [x] 📊 [Decision Log](#-decision-log) — Key decisions documented
- [x] 📝 [Task Summary](#-task-summary) — Final implementation summary completed

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards (see Agent Protocol section)
- **Prompt Standards**: `tasks/prompt_engineering_standards.md` — MANDATORY for this task
- **Blueprint Reference**: `docs/BRANDMIND_WORKSPACE_NOTES_RESEARCH.md` — Section 7 (File Architecture: "Thinking Tool" Design)
- **Existing System Prompt**: `src/prompts/brand_strategy/system_prompt.py` — match style exactly
- **Existing SKILL.md**: `src/shared/src/shared/agent_skills/brand_strategy/brand-strategy-orchestrator/SKILL.md` — reference for Phase Transition Protocol integration
- **Claude Code memory instructions**: Reference for how production systems guide agents on persistent note-taking (instruction density, structure, when-to-read/write patterns)

------------------------------------------------------------------------

## 🤖 Agent Protocol

> **MANDATORY**: Read this section in full before starting any implementation work.

### Rule 1 — Research Before Coding
(Same as Task 48)

### Rule 2 — Ask, Don't Guess
(Same as Task 48)

### Rule 3 — Update Progress As You Go
(Same as Task 48)

### Rule 4 — Production-Grade Code Standards
(Same as Task 48)

### Rule 5 — Prompt Engineering Standards

**This task is primarily prompt engineering.** The system prompt section MUST follow `tasks/prompt_engineering_standards.md`:
- Structure with Markdown headings
- Imperative mood — direct commands, no hedging
- Every conditional has an explicit "otherwise" branch
- Define what the agent must **never** do
- Output format specified as template, not description
- Controlled flexibility — define boundaries, let agent determine specifics

**Additional prompt design principles for workspace notes**:
- Instructions must be **specific enough** to guide structured note-taking (SOAP, Golden Thread) but **flexible enough** that agent can adapt to different project types
- Reference existing prompt patterns: the "Mentor Cycle" (explain → do → present → check) and "Workflow Discipline" (DRIVER, not passenger) sections already establish the tone
- Match the **concise, imperious style** of the existing CRITICAL RULES section
- Do NOT over-specify content — the templates in the workspace files guide structure. The prompt guides WHEN and HOW, not WHAT.

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Task 48 enables the agent to read/write workspace files — but the agent doesn't know they exist
- System prompt currently has no references to workspace notes, filesystem, or persistent memory
- Agent needs clear instructions on: what workspace notes are, when to read them, when to write them, how to write them
- Instructions must match the existing system prompt's tone and structure (tested and optimized over 6+ phases of development)
- Key insight from research: workspace notes are a **THINKING TOOL** — the prompt must enforce deliberate synthesis, not data dumping

### Mục tiêu

1. Add `# WORKSPACE NOTES` section to system prompt that teaches the agent about persistent workspace files
2. Add session resume awareness — when resuming, agent reads workspace files FIRST before responding
3. Keep prompt addition under ~60 lines to avoid context bloat
4. Agent correctly reads workspace at session start, writes notes at phase transitions

### Success Metrics / Acceptance Criteria

- **Prompt quality**: Instructions follow prompt engineering standards (imperative mood, specific conditions, explicit otherwise branches)
- **Agent behavior**: Agent reads workspace files within first 2 turns of session start
- **Note quality**: Agent writes SOAP-structured notes, not raw transcripts
- **Context budget**: New prompt section ≤ 1500 tokens
- **Resume works**: On session resume, agent restores context from workspace files before proceeding

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**System prompt section + session-aware addendum**: Add a new `# WORKSPACE NOTES` section to the system prompt between `# INTERACTION STYLE` and `# CONTEXT MANAGEMENT`. For session resume, dynamically append an addendum to the system prompt in `agent_config.py`.

### Placement Rationale

The workspace notes section goes between INTERACTION STYLE and CONTEXT MANAGEMENT because:
- INTERACTION STYLE defines HOW the agent communicates (mentor cycle, pacing)
- WORKSPACE NOTES defines HOW the agent persists thinking (note-taking discipline)
- CONTEXT MANAGEMENT defines HOW skills/tools are loaded (technical context)

This ordering creates a natural flow: interact → persist → manage context.

### Issues & Solutions

1. **Agent might ignore workspace instructions** → Instructions placed in high-visibility system prompt (not buried in skill files). Phase transition hooks (Task 50) provide enforcement.
2. **Agent might write raw transcripts** → Prompt explicitly says "THINKING TOOL, not data capture tool" and references SOAP template structure.
3. **Session resume detection** → Check `session.completed_phases` — if non-empty, session was resumed.

------------------------------------------------------------------------

## 🔬 Pre-Implementation Research

### Prompt Design Research

**How Claude Code handles memory instructions** (observed from own system prompt):
- Clear structure: types → when_to_save → how_to_use → examples
- Explicit "What NOT to save" section
- Two-step process (write file, then update index)
- Rules about when to access memories
- Warnings about stale data verification

**Key patterns to adopt**:
- Be specific about WHEN (triggers): "At session start", "At every phase transition", "When system reminds you"
- Be specific about HOW (format): "APPEND only", "EDIT specific sections", "Never rewrite entire files"
- Include the "otherwise" branch: "If file is already current, skip it"
- Include what NOT to do: "Do NOT dump raw conversation"

**Key patterns to avoid** (from prompt engineering standards):
- Over-specification that removes agent judgment
- Generic instructions ("update your notes") instead of specific ones ("update the current phase's S/O/A/P sections")
- Missing error handling ("If workspace files are not accessible, proceed without them")

### Research Status

- [x] All referenced documentation read
- [x] Existing system prompt style analyzed
- [x] Prompt engineering standards reviewed
- [x] No unresolved ambiguities remain → Ready to implement

------------------------------------------------------------------------

## 🔄 Implementation Plan

### Phase 1: System Prompt Section — 1 day

1. **Write workspace notes section** in `system_prompt.py`
   - Match existing style (markdown headers, imperative mood, tables)
   - Cover: what, when to read, when to write, how to write, what NOT to do
   - *Checkpoint: Section ≤ 1500 tokens, follows prompt engineering standards*

### Phase 2: Session Resume Awareness — 0.5 day

1. **Add session-aware prompt addendum** in `agent_config.py`
   - Detect resumed session via `completed_phases`
   - Append SESSION RESUME instructions to system prompt
   - *Checkpoint: Resumed agent reads workspace files in first turn*

### Rollback Plan

Remove the workspace notes section from `system_prompt.py` (single string deletion). Remove addendum logic from `agent_config.py`. No infrastructure changes.

------------------------------------------------------------------------

## 📋 Implementation Detail

### Component 1: Workspace Notes System Prompt Section

> Status: ✅ Done

#### Requirement 1 — Add WORKSPACE NOTES section to system prompt

- **Requirement**: Add a new top-level section to the brand strategy system prompt that teaches the agent about persistent workspace files, when to read/write them, and how to write notes effectively. Must match existing prompt style and follow prompt engineering standards.

- **Test Specification**:
  ```python
  # Test case 1: Section present in system prompt
  # Input: Read BRAND_STRATEGY_SYSTEM_PROMPT
  # Expected: Contains "# WORKSPACE NOTES" section

  # Test case 2: Token budget
  # Input: Count tokens in workspace notes section
  # Expected: ≤ 1500 tokens

  # Test case 3: Agent reads workspace at session start
  # Input: Start new session, observe agent's first tool calls
  # Expected: Agent calls read_file("/workspace/brand_brief.md") within first 2 turns

  # Test case 4: Agent writes SOAP notes at phase transition
  # Input: Complete Phase 0, trigger phase advance
  # Expected: brand_brief.md contains S/O/A/P sections for Phase 0

  # Test case 5: Agent does NOT dump raw conversation
  # Input: Complete Phase 0 with 10+ exchanges
  # Expected: brand_brief.md contains synthesized notes, not copy-pasted conversation
  ```

- **Implementation**:
  - `src/prompts/brand_strategy/system_prompt.py` (modify — insert new section)

  Insert the following section AFTER the `# INTERACTION STYLE` section (after line 277 `---`) and BEFORE `# CONTEXT MANAGEMENT` (line 280):

  ```python
  # In the BRAND_STRATEGY_SYSTEM_PROMPT string, add between INTERACTION STYLE and CONTEXT MANAGEMENT:

  """
  ---

  # WORKSPACE NOTES — YOUR PERSISTENT MEMORY

  You have 4 persistent files that survive context compression and session boundaries. They are your "external brain" — use them to preserve strategic thinking across long conversations.

  ## Files

  | Path | Purpose | Thinking Mode |
  |------|---------|---------------|
  | `/workspace/brand_brief.md` | Cumulative strategy document. SOAP structure per phase. Executive Summary + Golden Thread at top. | Build on previous, synthesize |
  | `/workspace/working_notes.md` | Scratchpad. Inbox for unprocessed items, user patterns, pending questions, ideas, session reflections. | Capture everything, filter later |
  | `/workspace/quality_gates.md` | Phase gate checklist. Thread Check (does output connect to Phase 0 and next phase?). Readiness assessment. | Evaluate, verify connections |
  | `/user/profile.md` | Global user profile (persists across projects). Identity, communication preferences, constraints, working style. | Understand the human |

  ## When to Read

  **At session start**: Read `brand_brief.md` first (Executive Summary restores 80% of context), then `working_notes.md` (pending items), then `quality_gates.md` (current gate status). Read `user/profile.md` once for user preferences.

  **Before major decisions**: Re-read the Golden Thread in `brand_brief.md` to verify your current work connects to the foundational problem.

  **If workspace files are empty or missing**: This is a new session — proceed normally. Files will be populated as you work through phases.

  ## When to Write

  **At phase transitions** (before calling `report_progress(advance=True)`): Comprehensive update — this is your primary save point.
  1. `brand_brief.md` — Write full SOAP for the phase you just completed. Compress the phase before it to a 3-4 bullet summary. Update Executive Summary and Golden Thread.
  2. `working_notes.md` — Process inbox items (act on, defer, or discard). Add session reflection. Clear resolved pending questions.
  3. `quality_gates.md` — Mark completed gates. Write Thread Check for current phase. Add gate checklist for the next phase.
  4. `user/profile.md` — Any new stable preferences or constraints learned?

  **Mid-phase, when significant**: Append new observations or findings to `working_notes.md` inbox. Do NOT update brand_brief mid-phase — wait for phase transition.

  **When user reveals stable personal info**: Update `user/profile.md` (e.g., "User prefers Vietnamese communication", "User is a junior marketer"). Only stable facts — not session-specific reactions.

  **When system reminds you** (pre-compact): Follow the system reminder's specific instructions for incremental save.

  ## How to Write

  **APPEND or EDIT sections — never rewrite entire files.** Use `edit_file` for targeted section updates. Use `write_file` only if creating a new section.

  **brand_brief.md structure per phase (SOAP)**:
  - **S** (Subjective): What user told us — goals, constraints, opinions
  - **O** (Objective): What research found — data, metrics, evidence tagged [O1], [O2]
  - **A** (Assessment): What we concluded — cite evidence, include alternatives rejected
  - **P** (Plan): What's next — immediate steps, pending decisions

  **Progressive Summarization**: Current phase at full SOAP detail. Previous phases compressed to 3-4 key bullets + 1-line decision summary + link to next phase.

  **Golden Thread**: One chain linking all major decisions: Problem → [P0 insight] → [P1 finding] → [P2 choice] → ...

  **Keep `user/profile.md` under ~2000 characters** — only the most important, stable facts.

  ## What NOT to Do

  - **Do NOT** copy-paste conversation into workspace files. Write synthesized notes.
  - **Do NOT** rewrite files from scratch. Edit specific sections that changed.
  - **Do NOT** store raw research data. Store insights derived from research. Raw data can be re-fetched.
  - **Do NOT** update brand_brief.md mid-phase (except via inbox in working_notes.md). Wait for phase transition.
  - **Do NOT** skip workspace updates at phase transitions. This is mandatory, like quality gates.

  ---
  """
  ```

- **Acceptance Criteria**:
  - [x] Section inserted between INTERACTION STYLE and CONTEXT MANAGEMENT
  - [x] Follows prompt engineering standards (imperative mood, explicit conditions, otherwise branches)
  - [x] ≤ 1500 tokens
  - [x] Covers: files (table), when to read, when to write, how to write (SOAP, Progressive Summarization, Golden Thread), what NOT to do
  - [x] Matches existing system prompt style (markdown headers, bold emphasis, tables)
  - [ ] Agent reads workspace at session start *(deferred to manual E2E testing)*
  - [ ] Agent writes structured notes at phase transitions *(deferred to manual E2E testing)*

---

### Component 2: Session Resume Awareness

> Status: ✅ Done

#### Requirement 1 — Dynamic session resume addendum

- **Requirement**: When a session is resumed (has completed phases), append a SESSION RESUME instruction to the system prompt that tells the agent to read workspace files immediately before responding to the user.

- **Test Specification**:
  ```python
  # Test case 1: New session → no addendum
  # Input: Create agent with fresh BrandStrategySession (no completed_phases)
  # Expected: System prompt is standard, no SESSION RESUME text

  # Test case 2: Resumed session → addendum present
  # Input: Create agent with session that has completed_phases=["phase_0"]
  # Expected: System prompt ends with SESSION RESUME instructions

  # Test case 3: Resumed agent reads workspace first
  # Input: Resume session at Phase 1, send "continue"
  # Expected: Agent's first actions are read_file calls to workspace files
  ```

- **Implementation**:
  - `src/core/src/core/brand_strategy/agent_config.py` (modify — in create_brand_strategy_agent)

  Add after the workspace initialization block (from Task 48) and before the agent assembly:

  ```python
  # Session-aware system prompt (Task 49)
  system_prompt = BRAND_STRATEGY_SYSTEM_PROMPT
  if session is not None and session.completed_phases:
      # Resumed session — instruct agent to restore context from workspace
      resume_addendum = (
          "\n\n# SESSION RESUME\n\n"
          "This is a **RESUMED session**. You have completed phases: "
          f"{', '.join(p.replace('phase_', 'Phase ') for p in session.completed_phases)}. "
          f"Current phase: **{session.current_phase.replace('phase_', 'Phase ')}**.\n\n"
          "**BEFORE responding to the user**, read your workspace notes to restore context:\n"
          "1. `read_file(\"/workspace/brand_brief.md\")` — Executive Summary + Golden Thread\n"
          "2. `read_file(\"/workspace/working_notes.md\")` — Pending items + observations\n"
          "3. `read_file(\"/workspace/quality_gates.md\")` — Current gate status\n"
          "4. `read_file(\"/user/profile.md\")` — User preferences\n\n"
          "After reading, briefly acknowledge to the user where you left off and what comes next. "
          "Do NOT ask the user to repeat information that is already in your workspace notes."
      )
      system_prompt = system_prompt + resume_addendum

  # Then use system_prompt instead of BRAND_STRATEGY_SYSTEM_PROMPT in create_agent():
  agent = create_agent(
      model=model,
      tools=tools,
      system_prompt=system_prompt,  # <-- changed from BRAND_STRATEGY_SYSTEM_PROMPT
      middleware=[...],
  )
  ```

- **Acceptance Criteria**:
  - [x] New session → standard system prompt (no addendum)
  - [x] Resumed session → system prompt includes SESSION RESUME section
  - [x] Resume addendum lists correct completed phases and current phase
  - [ ] Agent reads all 4 workspace files before first response on resume *(deferred to manual E2E)*
  - [ ] Agent does NOT ask user to repeat info already in workspace notes *(deferred to manual E2E)*
  - [x] `create_agent()` uses `system_prompt` variable (not hardcoded constant)

------------------------------------------------------------------------

## 🧪 Test Execution Log

### Test 1: System Prompt Contains Workspace Section

- **Purpose**: Verify the workspace notes section is present and well-formatted
- **Steps**:
  1. Import `BRAND_STRATEGY_SYSTEM_PROMPT` from system_prompt.py
  2. Check `"# WORKSPACE NOTES"` is in the string
  3. Check it appears between `"# INTERACTION STYLE"` and `"# CONTEXT MANAGEMENT"`
  4. Count tokens (approximate: len / 4)
- **Expected Result**: Section present, correctly placed, ≤ 1500 tokens
- **Actual Result**: `"# WORKSPACE NOTES"` present in prompt. Appears between INTERACTION STYLE and CONTEXT MANAGEMENT. Contains files table, SOAP instructions, Golden Thread, What NOT to Do. ~1400 tokens estimated.
- **Status**: ✅ Pass

### Test 2: New Session — No Resume Addendum

- **Purpose**: Verify new sessions don't get resume instructions
- **Steps**:
  1. Create fresh `BrandStrategySession()` with empty `completed_phases`
  2. Simulate addendum logic: `if session.completed_phases:` → False
- **Expected Result**: No `"# SESSION RESUME"` in system prompt
- **Actual Result**: Condition correctly evaluates to False for new session. No addendum appended.
- **Status**: ✅ Pass

### Test 3: Resumed Session — Resume Addendum Present

- **Purpose**: Verify resumed sessions get context restoration instructions
- **Steps**:
  1. Create `BrandStrategySession()` with `completed_phases=["phase_0"]`, `current_phase="phase_1"`
  2. Simulate addendum construction
  3. Verify completed phases and current phase format correctly
- **Expected Result**: Contains `"# SESSION RESUME"` with "Phase 0" in completed and "Phase 1" as current
- **Actual Result**: Addendum correctly formats: "completed: Phase 0, current: Phase 1". Lists all 4 read_file calls with correct paths.
- **Status**: ✅ Pass

### Test 4: Agent Reads Workspace at Session Start (E2E)

- **Purpose**: Verify agent actually reads workspace files in first turns
- **Steps**:
  1. Ran full E2E: `BrandStrategySession()` → `set_active_session()` → `create_brand_strategy_agent()`
  2. Verified agent creation succeeds with workspace CompositeBackend
  3. Verified system prompt contains WORKSPACE NOTES instructions including "At session start: Read brand_brief.md first"
  4. Verified resumed session gets SESSION RESUME addendum with explicit `read_file()` calls
- **Expected Result**: Agent reads at least brand_brief.md within first 2 turns
- **Actual Result**: Infrastructure verified. Agent has instructions + workspace access. Behavioral verification (does agent actually call read_file on first turn?) requires live LLM session — deferred to manual test by user.
- **Status**: ✅ Pass (infrastructure) / ⏳ Deferred (behavioral, requires live LLM)

### Test 5: Agent Writes SOAP Notes at Phase Transition (E2E)

- **Purpose**: Verify agent writes structured notes when completing a phase
- **Steps**:
  1. Verified system prompt WORKSPACE NOTES section has SOAP instructions
  2. Verified report_progress(advance=True) returns workspace update hint
  3. Verified workspace files writable via edit_file (CompositeBackend routing)
- **Expected Result**: brand_brief.md contains Phase 0 SOAP notes (not raw conversation)
- **Actual Result**: Infrastructure verified (prompt instructions + hook + writable workspace). Behavioral verification requires live LLM session — deferred to manual test by user.
- **Status**: ✅ Pass (infrastructure) / ⏳ Deferred (behavioral, requires live LLM)

------------------------------------------------------------------------

## 📊 Decision Log

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | Prompt placement | After CONTEXT MANAGEMENT vs between INTERACTION STYLE and CONTEXT MANAGEMENT | Between INTERACTION STYLE and CONTEXT MANAGEMENT | Natural flow: interact → persist → manage context. Also higher visibility than post-CONTEXT MANAGEMENT. |
| 2 | Session resume mechanism | Inject workspace content into system prompt vs instruct agent to read files | Instruct agent to read files | Injecting content wastes context (permanent). Agent reading on-demand is more flexible and files might be large. |
| 3 | Workspace read instruction style | List specific file paths vs generic "read your workspace" | List specific file paths with read_file() calls | Agent follows specific instructions more reliably than generic ones. Explicit tool calls leave no ambiguity. |
| 4 | Prompt length target | ~30 lines (minimal) vs ~60 lines (comprehensive) | ~55 lines (~1500 tokens) | Needs enough detail to guide SOAP structure and when-to-write triggers, but not so much that it bloats context. Comparable to INTERACTION STYLE section length. |
| 5 | What NOT to do section | Omit (rely on positive instructions) vs include explicitly | Include explicitly | Prompt engineering best practice: negative constraints are as important as positive ones. Prevents common failure modes (data dumping, full rewrites). |

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation.

### What Was Implemented

**Components Completed**:
- [x] [Component 1]: Workspace Notes system prompt section (~55 lines, ~1400 tokens)
- [x] [Component 2]: Session resume awareness (dynamic prompt addendum)

**Files Created / Modified**:
```
src/prompts/brand_strategy/
└── system_prompt.py                     # MODIFIED: Added WORKSPACE NOTES section

src/core/src/core/brand_strategy/
└── agent_config.py                      # MODIFIED: Session resume addendum + system_prompt variable
```

------------------------------------------------------------------------
