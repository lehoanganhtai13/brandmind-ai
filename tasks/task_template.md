# Task XX: [Task Title]

## 📌 Metadata

- **Epic**: [Epic Name]
- **Priority**: High / Medium / Low
- **Status**: Backlog / In Progress / Done / Blocked
- **Estimated Effort**: X days / X weeks
- **Team**: Backend / Mobile / Full-stack
- **Related Tasks**: [Task XX — description]
- **Blocking**: [Task XX, YY]
- **Blocked by**: [Task XX, or @person]

### ✅ Progress Checklist

> **Agent**: Update checkboxes as each section is completed. Do NOT mark a section done until it is fully verified.

- [ ] 🤖 [Agent Protocol](#-agent-protocol) — Read and confirm before starting
- [ ] 🎯 [Context & Goals](#-context--goals) — Problem definition and success metrics
- [ ] 🛠 [Solution Design](#-solution-design) — Architecture and technical approach
- [ ] 🔬 [Pre-Implementation Research](#-pre-implementation-research) — Findings logged before coding
- [ ] 🔄 [Implementation Plan](#-implementation-plan) — Phased execution plan confirmed with user
- [ ] 📋 [Implementation Detail](#-implementation-detail) — Component-level specs with test cases
    - [ ] ⏳ [Component 1](#component-1) — Pending
    - [ ] ⏳ [Component 2](#component-2) — Pending
- [ ] 🧪 [Test Execution Log](#-test-execution-log) — All tests run and results recorded
- [ ] 📊 [Decision Log](#-decision-log) — Key decisions documented
- [ ] 📝 [Task Summary](#-task-summary) — Final implementation summary completed

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards (see Agent Protocol section)
- **Blueprint Reference**: `docs/[RELEVANT_DOC].md` — Section [X]
- **External Spec**: [URL or path to relevant spec/API docs]
- **Related Pattern**: [Path to existing code that follows the same pattern]

------------------------------------------------------------------------

## 🤖 Agent Protocol

> **MANDATORY**: Read this section in full before starting any implementation work.

### Rule 1 — Research Before Coding

Before writing any code for a component:
1. Read all files referenced in "Reference Documentation" above
2. Read existing code in the relevant module to understand current patterns
3. If an external library or API is involved, fetch its documentation (use web search or context7)
4. Log your findings in [Pre-Implementation Research](#-pre-implementation-research) before proceeding
5. **Do NOT assume or invent** behavior — verify against actual source

### Rule 2 — Ask, Don't Guess

When encountering any of the following, **STOP and ask the user** before proceeding:

- A requirement is ambiguous or contradictory
- Two valid implementation approaches exist with non-trivial trade-offs
- An existing interface, API, or behavior conflicts with the spec
- A dependency behaves differently than documented
- The scope of a change is larger than anticipated

Format: State the issue clearly, present your options with pros/cons, and ask for a decision.

### Rule 3 — Update Progress As You Go

After completing each component or sub-task:
1. Check off the corresponding item in the Progress Checklist
2. Update the component status emoji: ⏳ Pending → 🚧 In Progress → ✅ Done
3. Fill in the Test Execution Log with actual results as tests run
4. Log any significant decisions in the Decision Log

### Rule 4 — Production-Grade Code Standards

All code MUST meet these standards (no exceptions):

| Standard | Requirement |
|----------|-------------|
| **Docstrings** | Every module, class, and function — purpose, args, returns, business context |
| **Comments** | Inline comments for complex logic, business rules, non-obvious decisions |
| **String quotes** | Double quotes `"` consistently throughout |
| **Type hints** | All function signatures — no `Any` unless truly unavoidable |
| **Naming** | PEP 8 — `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE` constants |
| **Line length** | Max 100 characters — **exception: prompt strings** (see Rule 5) |
| **Language** | English only — all code, comments, docstrings |
| **Modularity** | Single responsibility — break large functions into focused, reusable units |

### Rule 5 — Prompt Engineering Standards

Applies whenever this task involves writing or modifying **any prompt string** passed to an LLM
(system prompts, agent instructions, skill content, persona definitions, workflow directives).

**Line length**: Prompt strings are **exempt from the 100-character rule**. Break lines at
semantic boundaries (end of a rule, end of a clause), not at character count.

**Full standards**: `tasks/prompt_engineering_standards.md`

Key requirements:
- Structure with Markdown headings (`##`, `###`) to separate role, process, rules, output format
- Use imperative mood — direct commands, no hedging (`"Always X"`, not `"try to X"`)
- Every conditional must have an explicit "otherwise" branch — no undefined edge cases
- Define what the agent must **never** do, not just what it should do
- Multi-phase workflows require explicit **phase transition rules** and **user confirmation gates**
- Output format must be specified as a template, not a description
- Review using the checklist at the end of `prompt_engineering_standards.md` before finalizing

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- [Current problem or situation — what exists today]
- [Pain point or impact — why this needs to be solved]

### Mục tiêu

[Clear objective statement — what this task will achieve and what changes for the better]

### Success Metrics / Acceptance Criteria

- **Performance**: [Measurable target — e.g., "API response < 200ms at p95"]
- **Scale**: [User/data volume requirements]
- **Reliability**: [Uptime, error rate, or resilience requirement]
- **Business**: [User-facing impact or business outcome]

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**[Approach Name]**: [1–2 sentence description of the chosen approach and why it was selected over alternatives]

### Stack công nghệ

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| [Library/Framework] | [What it does in this context] | [Rationale] |
| [Library/Framework] | [What it does in this context] | [Rationale] |

### Architecture Overview

```
[ASCII diagram or description of how components fit together]
```

### Issues & Solutions

1. **[Anticipated Challenge]** → [How it will be addressed]
2. **[Anticipated Challenge]** → [How it will be addressed]

------------------------------------------------------------------------

## 🔬 Pre-Implementation Research

> **Agent**: Complete this section BEFORE writing any implementation code.
> Log your findings here so the user can verify your understanding is correct.
> If anything contradicts the spec above, flag it immediately.

### Codebase Audit

- **Files read**: [List of existing files reviewed]
- **Relevant patterns found**: [Describe patterns in existing code that this task should follow]
- **Potential conflicts**: [Any existing code, interface, or behavior that may conflict with the spec]

### External Library / API Research

- **Library/API**: [Name and version]
- **Documentation source**: [URL or local path]
- **Key findings**: [Relevant behaviors, limitations, or gotchas discovered]
- **Interface confirmed**: [The specific function/class/method signatures you will use]

### Unknown / Risks Identified

> List any items that are still unclear after research. These must be resolved (via user Q&A or further research) before implementation begins.

- [ ] [Unknown item — will ask user / will research further]
- [ ] [Risk — mitigation approach]

### Research Status

- [ ] All referenced documentation read
- [ ] Existing codebase patterns understood
- [ ] External dependencies verified
- [ ] No unresolved ambiguities remain → Ready to implement

------------------------------------------------------------------------

## 🔄 Implementation Plan

> **Agent**: Present this plan to the user before beginning implementation.
> Do not start coding until the user confirms the plan is correct.

### Phase 1: [Phase Name] — [Estimated time]

1. **[Task]**
   - [Sub-task or key consideration]
   - [Sub-task or key consideration]
   - *Checkpoint: [What to verify before moving on]*

2. **[Task]**
   - [Sub-task]
   - *Checkpoint: [What to verify before moving on]*

### Phase 2: [Phase Name] — [Estimated time]

1. **[Task]**
   - [Sub-task]
   - *Checkpoint: [Integration or validation step]*

### Rollback Plan

[How to safely undo this change if something goes wrong — e.g., "revert file X, remove migration Y"]

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards Reminder**: Apply the standards from Agent Protocol Rule 4 to every file.
> Test specifications are written BEFORE implementation — follow TDD order within each requirement.

### Component 1: [Component Name]

> Status: ⏳ Pending / 🚧 In Progress / ✅ Done

#### Requirement 1 — [Title]

- **Requirement**: [What needs to be built — business purpose and behavior]

- **Test Specification** *(define before implementing)*:
  ```python
  # Test case 1: [What is being validated]
  # Input: [describe input]
  # Expected: [describe expected output or behavior]

  # Test case 2: [Edge case or error condition]
  # Input: [describe input]
  # Expected: [describe expected output or behavior]
  ```

- **Implementation**:
  - `path/to/file.py`
  ```python
  def example_function(param: ParamType) -> ReturnType:
      """
      [One-line summary of what this function does.]

      [Longer description of business purpose, data transformations,
      and how this fits into the overall workflow.]

      Args:
          param (ParamType): [Description of the parameter]

      Returns:
          result (ReturnType): [Description of the return value]

      Raises:
          ValueError: [When and why this is raised]
      """
      pass
  ```

- **Acceptance Criteria**:
  - [ ] [Measurable outcome — e.g., "function returns X given input Y"]
  - [ ] [Measurable outcome — e.g., "raises ValueError when Z"]
  - [ ] [Code standard — e.g., "mypy passes with no errors"]

#### Requirement 2 — [Title]

- **Requirement**: [What needs to be built]

- **Test Specification** *(define before implementing)*:
  ```python
  # Test case 1: [Normal path]
  # Test case 2: [Error path]
  ```

- **Implementation**:
  - `path/to/file.py`
  - [Brief description of approach — focus on business logic, not code syntax]

- **Acceptance Criteria**:
  - [ ] [Measurable outcome 1]
  - [ ] [Measurable outcome 2]

### Component 2: [Component Name]

> Status: ⏳ Pending / 🚧 In Progress / ✅ Done

#### Requirement 1 — [Title]

- **Requirement**: [What needs to be built]

- **Test Specification** *(define before implementing)*:
  ```python
  # Test case 1: [Normal path]
  # Test case 2: [Error path]
  ```

- **Implementation**:
  - `path/to/file.py`
  - [Brief description of approach]

- **Acceptance Criteria**:
  - [ ] [Measurable outcome 1]
  - [ ] [Measurable outcome 2]

------------------------------------------------------------------------

## 🧪 Test Execution Log

> **Agent**: Record actual test results here as you run them.
> Do not mark a test as Passed until you have run it and seen the output.

### Test 1: [Test Name]

- **Purpose**: [What this test validates]
- **Steps**:
  1. [Step 1]
  2. [Step 2]
  3. [Step 3]
- **Expected Result**: [What success looks like]
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending / 🚧 Running / ✅ Passed / ❌ Failed

### Test 2: [Test Name]

- **Purpose**: [What this test validates]
- **Steps**:
  1. [Step 1]
  2. [Step 2]
- **Expected Result**: [What success looks like]
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending / 🚧 Running / ✅ Passed / ❌ Failed

### Test 3: Error / Edge Case — [Scenario Name]

- **Purpose**: Verify correct behavior when [error condition occurs]
- **Steps**:
  1. [Setup error condition]
  2. [Trigger the code path]
- **Expected Result**: [Expected error, fallback, or rejection]
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending / 🚧 Running / ✅ Passed / ❌ Failed

------------------------------------------------------------------------

## 📊 Decision Log

> **Agent**: Document every significant decision made during implementation.
> Include the options considered, the trade-off, and the final choice.
> This section is what transforms a task file into institutional knowledge.

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | [What decision was made] | [Option A vs Option B] | [Option chosen] | [Why] |
| 2 | [What decision was made] | [Option A vs Option B] | [Option chosen] | [Why] |

------------------------------------------------------------------------

## 📝 Task Summary

> **Agent**: Complete this section AFTER the task is fully implemented and all tests pass.
> This is the permanent record of what was built and how it works.

### What Was Implemented

**Components Completed**:
- [ ] [Component 1]: [What was actually built — 1–2 sentences]
- [ ] [Component 2]: [What was actually built — 1–2 sentences]

**Files Created / Modified**:
```
[module]/
├── path/to/new_file.py           # [Purpose]
├── path/to/modified_file.py      # [What changed and why]
└── path/to/another_file.py       # [Purpose]
```

**Key Features Delivered**:
1. **[Feature Name]**: [Business functionality and impact]
2. **[Feature Name]**: [Business functionality and impact]

### Technical Highlights

**Architecture Decisions** (see Decision Log for details):
- [Decision 1]: [One-line rationale]
- [Decision 2]: [One-line rationale]

**Performance / Quality Results**:
- [Metric]: [Observed result — e.g., "p95 latency: 120ms (target: <200ms) ✅"]

**Documentation Checklist**:
- [ ] All functions have comprehensive docstrings (purpose, args, returns)
- [ ] Complex business logic has inline comments
- [ ] Module-level docstrings explain purpose and usage
- [ ] Type hints complete and accurate
- [ ] `mypy` / `make typecheck` passes with 0 errors

### Validation Results

**Test Results**:
- [ ] All test cases in Test Execution Log: ✅ Passed
- [ ] Edge cases and error scenarios covered
- [ ] No regressions in related functionality

**Deployment Notes**:
- [New dependencies added, if any]
- [Config changes or environment variables required]
- [Database migrations or one-time setup steps]
- [Anything the next developer needs to know]

------------------------------------------------------------------------
