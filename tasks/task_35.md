# Task 35: Agent Skills Configuration & Directory Setup

## 📌 Metadata

- **Epic**: Brand Strategy — Foundation
- **Priority**: High
- **Estimated Effort**: 2 days
- **Team**: Backend
- **Related Tasks**: Task 34 (Browser Tool — existing tool pattern reference)
- **Blocking**: Task 42, 43, 44, 45 (all skill implementations depend on this)
- **Blocked by**: None

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [x] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [x] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] ✅ [Component 1: Skills Directory Structure](#component-1-skills-directory-structure) - 4 SKILL.md placeholder files created
    - [x] ✅ [Component 2: SkillsMiddleware Configuration](#component-2-skillsmiddleware-configuration) - Factory function + re-exports
- [ ] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation (deferred to Task 42-45)
- [ ] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards with comprehensive documentation
- **Blueprint Reference**: `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — Section 4 (Skills Architecture), Section 7.3 (Context Window Management)
- **DeepAgents SkillsMiddleware**: Built-in middleware from `deepagents.middleware.skills` — progressive disclosure pattern
- **DeepAgents FilesystemBackend**: `deepagents.backends.filesystem.FilesystemBackend` — local file access
- **Agent Skills Spec**: https://agentskills.io/specification — SKILL.md format with YAML frontmatter
- **Existing Pattern**: `.agent/skills/` — current skill format in workspace (same `SKILL.md` + YAML frontmatter convention)

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Thư mục `src/shared/src/shared/agent_skills/` hiện tại **hoàn toàn trống** — chỉ có `__init__.py` placeholder
- Blueprint Brand Strategy định nghĩa **4 skills** cần implement: orchestrator, market-research, brand-positioning-identity, brand-communication-planning
- Mỗi skill là file `SKILL.md` trong thư mục riêng, chứa YAML frontmatter + **procedural instructions** — giống "playbook" cho từng phase
- **DeepAgents đã có sẵn `SkillsMiddleware`** — built-in middleware (697 lines) xử lý:
  - Skill discovery từ backend sources (`_list_skills()` / `_alist_skills()`)
  - YAML frontmatter parsing (`_parse_skill_metadata()`)
  - Progressive disclosure: agent thấy name + description trong system prompt, đọc full SKILL.md on-demand
  - System prompt injection tự động (`modify_request()` + `SKILLS_SYSTEM_PROMPT` template)
  - Source layering: multiple sources, later overrides earlier (last wins)
- **KHÔNG CẦN build from scratch**: models, loader, registry, context manager, skill_search — tất cả đã có sẵn trong DeepAgents package
- Chỉ cần: (1) tạo directory structure đúng Agent Skills spec, (2) configure SkillsMiddleware + FilesystemBackend

### Approach: Progressive Disclosure (Option A)

Thay vì build custom phase-based skill loading (inject skill content vào system prompt theo phase), ta dùng **progressive disclosure** của built-in SkillsMiddleware:

1. **System prompt chỉ chứa skill listing** (~300 tokens): name + description + path cho 4 skills
2. **Agent tự đọc SKILL.md** on-demand khi cần (qua read_file tool của FilesystemMiddleware)
3. **Skill content đi vào message history** — tự bị summarize khi context đầy
4. **Orchestrator skill instruct agent re-read** SKILL.md tương ứng khi chuyển phase

**Lý do chọn progressive disclosure thay vì phase-based injection**:

| Tiêu chí | Phase-based (build custom) | Progressive Disclosure (built-in) |
|-----------|---------------------------|-----------------------------------|
| Context cost | ~4300 tokens cố định (300 listing + 4000 skill) | ~300 tokens cố định (listing only) |
| Per-phase cost | Swap: remove old + inject new | Agent re-read: ~4000 tokens 1 lần vào history |
| After summarization | Skill vẫn trong system prompt | History bị summarize → tokens giải phóng |
| Build effort | 1.5 tuần (5 custom components) | 2 ngày (directory + config) |
| Maintenance | Custom code cần maintain | 100% upstream DeepAgents |

### Mục tiêu

1. Tạo directory structure theo đúng Agent Skills spec (`skill-name/SKILL.md`)
2. Configure `SkillsMiddleware` + `FilesystemBackend` cho brand strategy agent
3. Đảm bảo SkillsMiddleware discover đúng 4 skills
4. Validate progressive disclosure hoạt động (agent thấy listing, đọc on-demand)
5. Cung cấp helper function cho task_46 integration

### Success Metrics / Acceptance Criteria

- **Discovery**: `SkillsMiddleware.before_agent()` scan sources → trả về 4 `SkillMetadata`
- **System Prompt**: Agent thấy 4 skills listing trong system prompt (~300 tokens)
- **On-Demand Read**: Agent có thể đọc full SKILL.md qua FilesystemMiddleware
- **YAML Compliance**: Frontmatter conform Agent Skills spec (name, description, optional: license, metadata, allowed-tools)
- **Extensibility**: Thêm skill mới = tạo thư mục + SKILL.md → auto-discovered

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Built-in SkillsMiddleware + FilesystemBackend + Directory Structure**: Tận dụng 100% DeepAgents built-in. Chỉ cần setup directory structure và config.

### Built-in Components (từ DeepAgents — KHÔNG build)

| Component | Module | What it does |
|-----------|--------|-------------|
| `SkillsMiddleware` | `deepagents.middleware.skills` | Scan sources, parse YAML, inject listing into system prompt |
| `SkillMetadata` | `deepagents.middleware.skills` | TypedDict: name, description, path, license, compatibility, metadata, allowed_tools |
| `FilesystemBackend` | `deepagents.backends.filesystem` | Read files from local filesystem |
| `_parse_skill_metadata()` | `deepagents.middleware.skills` | Parse SKILL.md YAML frontmatter |
| `_list_skills()` / `_alist_skills()` | `deepagents.middleware.skills` | Scan source directories for skill subdirs |
| `SKILLS_SYSTEM_PROMPT` | `deepagents.middleware.skills` | Template for system prompt injection |

### New Components (chỉ cần tạo)

| Component | Location | Purpose |
|-----------|----------|---------|
| Skills directory structure | `src/shared/src/shared/agent_skills/brand_strategy/` | Directory tree với 4 skill subdirectories |
| Skills config helper | `src/shared/src/shared/agent_skills/config.py` | Helper function tạo SkillsMiddleware instance |
| Updated `__init__.py` | `src/shared/src/shared/agent_skills/__init__.py` | Re-export config helper |

### Directory Structure (Agent Skills Spec)

```
src/shared/src/shared/agent_skills/
├── __init__.py                                        # Re-exports
├── config.py                                          # SkillsMiddleware factory
└── brand_strategy/
    ├── brand-strategy-orchestrator/
    │   └── SKILL.md                                   # Task 42
    ├── market-research/
    │   └── SKILL.md                                   # Task 43
    ├── brand-positioning-identity/
    │   └── SKILL.md                                   # Task 44
    └── brand-communication-planning/
        └── SKILL.md                                   # Task 45
```

### YAML Frontmatter Format (Agent Skills Spec compliance)

Mỗi SKILL.md phải có YAML frontmatter conform Agent Skills spec. Các fields:

- **Required**: `name` (max 64 chars, lowercase alphanumeric + hyphens), `description` (max 1024 chars)
- **Optional**: `license`, `compatibility`
- **Note**: Per skill-creator best practices, chỉ dùng `name` + `description` trong frontmatter. Không dùng `metadata` hay `allowed-tools` — description là PRIMARY triggering mechanism, phải comprehensive (bao gồm cả "when to use").

```yaml
---
name: brand-strategy-orchestrator
description: >-
  Master workflow orchestrating 6-phase F&B brand strategy development.
  Covers new brand creation, refresh, repositioning, and full rebrand.
  Manages phase sequencing, quality gates, mentor-mode conversations,
  rebrand scope diagnosis, and proactive loop-back triggers.
  Use when user asks to build a brand strategy, create a brand,
  rebrand an existing business, or develop brand positioning.
  Always load this skill first — it delegates to sub-skills per phase.
---

# Brand Strategy Orchestrator
[Full skill content here — filled by Task 42]
```

**Note**: `name` PHẢI match directory name (e.g., directory `brand-strategy-orchestrator/` → name `brand-strategy-orchestrator`). Đây là requirement của `_validate_skill_name()` trong SkillsMiddleware.

### How Progressive Disclosure Works

```
┌──────────────────────────────────────────────────────┐
│                   System Prompt                       │
│                                                       │
│  ## Skills System                                     │
│                                                       │
│  **Available Skills:**                                │
│  - **brand-strategy-orchestrator**: Master workflow... │
│    -> Read `.../brand-strategy-orchestrator/SKILL.md` │
│  - **market-research**: F&B market research...        │
│    -> Read `.../market-research/SKILL.md`             │
│  - **brand-positioning-identity**: Phases 2-3...      │
│    -> Read `.../brand-positioning-identity/SKILL.md`  │
│  - **brand-communication-planning**: Phases 4-5...    │
│    -> Read `.../brand-communication-planning/SKILL.md`│
│                              ~300 tokens              │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼ Agent reads SKILL.md on-demand
┌──────────────────────────────────────────────────────┐
│                  Message History                      │
│                                                       │
│  [Tool Result] Content of orchestrator/SKILL.md       │
│    ~3000-5000 tokens (vào history, KHÔNG system prmpt)│
│  ...                                                  │
│  [Tool Result] Content of market-research/SKILL.md    │
│    ~3000-5000 tokens                                  │
│  ...                                                  │
│  → SummarizationMiddleware summarizes old content     │
│  → Agent performs re-read nếu cần (1 tool call)       │
│  → Tokens tự giải phóng                               │
└──────────────────────────────────────────────────────┘
```

### Issues & Solutions

1. **Agent "quên" skill sau summarization** → Orchestrator SKILL.md có "Phase Transition Protocol" section instruct agent re-read khi chuyển phase
2. **Agent không biết đọc skill nào** → System prompt listing + description đủ rõ; orchestrator skill map phases → skills explicitly
3. **Custom metadata fields** → Đặt vào `metadata` dict (compliant với spec); agent đọc full SKILL.md nên đây chỉ là nice-to-have
4. **Thêm skill mới trong tương lai** → Chỉ cần tạo thư mục + SKILL.md → auto-discovered ở lần before_agent() kế tiếp

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Directory Structure (Day 1)**
1. Tạo directory tree theo Agent Skills spec
2. Tạo placeholder SKILL.md files cho 4 skills (frontmatter + placeholder body, Task 42-45 sẽ fill content)
3. Validate: `SkillsMiddleware._list_skills()` scan → phát hiện 4 skills

### **Phase 2: Configuration & Integration (Day 2)**
1. Tạo `config.py` với factory function `create_brand_strategy_skills_middleware()`
2. Update `__init__.py` re-exports
3. Integration test: agent thấy skill listing trong system prompt
4. E2E test: agent đọc SKILL.md on-demand qua FilesystemMiddleware

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards & Documentation Requirements**
>
> All code implementations **MUST** follow **enterprise-level Python standards**:
>
> - **Comprehensive Docstrings**: Every module, class, and function must have detailed docstrings in English
> - **Detailed Comments**: Add inline comments explaining complex logic
> - **Consistent String Quoting**: Use double quotes `"` consistently
> - **Type Hints**: Use Python type hints for all function signatures
> - **Line Length**: Max 100 characters
> - **Language**: All code, comments, and docstrings must be in **English only**

### Component 1: Skills Directory Structure

#### Requirement 1 - Create Directory Tree
- **Requirement**: Create skill directories conforming to Agent Skills spec (`skill-name/SKILL.md` pattern), including `references/` subdirectories for progressive disclosure
- **Implementation**:
  - Create directories:
    ```
    src/shared/src/shared/agent_skills/brand_strategy/
    ├── brand-strategy-orchestrator/
    │   ├── SKILL.md       # Placeholder — content filled by Task 42
    │   └── references/    # Phase-specific details — filled by Task 42
    ├── market-research/
    │   ├── SKILL.md       # Placeholder — content filled by Task 43
    │   └── references/    # Output templates — filled by Task 43
    ├── brand-positioning-identity/
    │   ├── SKILL.md       # Placeholder — content filled by Task 44
    │   └── references/    # Naming process, identity transition — filled by Task 44
    └── brand-communication-planning/
        ├── SKILL.md       # Placeholder — content filled by Task 45
        └── references/    # Transition plan, deliverable assembly — filled by Task 45
    ```

  - Placeholder SKILL.md template (each skill has this, Task 42-45 fill real content):

  **brand-strategy-orchestrator/SKILL.md**:
  ```markdown
  ---
  name: brand-strategy-orchestrator
  description: >-
    Master workflow orchestrating 6-phase F&B brand strategy development.
    Covers new brand creation, refresh, repositioning, and full rebrand.
    Manages phase sequencing, quality gates, mentor-mode conversations,
    rebrand scope diagnosis, and proactive loop-back triggers.
    Use when user asks to build a brand strategy, create a brand,
    rebrand an existing business, or develop brand positioning.
    Always load this skill first — it delegates to sub-skills per phase.
  ---

  # Brand Strategy Orchestrator

  > ⚠️ Placeholder — full content will be implemented in Task 42.
  ```

  **market-research/SKILL.md**:
  ```markdown
  ---
  name: market-research
  description: >-
    Systematic 8-step F&B market research methodology for Phase 1.
    Covers industry scan, local competitor mapping, competitor brand analysis,
    target audience research, customer insight mining, trend scanning,
    current brand position research (rebrand only), and strategic synthesis
    (SWOT, perceptual map, strategic sweet spot, insight prioritization).
    Use when the orchestrator enters Phase 1 or when the user asks
    to research a market, analyze competitors, or gather customer insights.
  ---

  # Market Research Skill

  > ⚠️ Placeholder — full content will be implemented in Task 43.
  ```

  **brand-positioning-identity/SKILL.md**:
  ```markdown
  ---
  name: brand-positioning-identity
  description: >-
    Brand positioning and identity expression frameworks for Phases 2-3.
    Phase 2: competitive frame of reference, POPs/PODs, value ladder,
    positioning statement, brand essence/mantra, product-brand alignment,
    and positioning stress test with loop-back triggers.
    Phase 3: brand personality (Aaker), voice spectrum, visual identity
    direction, distinctive brand assets (Sharp), sensory identity, and
    brand naming (Keller's 6 criteria).
    Use when the orchestrator enters Phase 2 or Phase 3, or when the user
    asks about positioning, brand identity, naming, or visual direction.
  ---

  # Brand Positioning & Identity Skill

  > ⚠️ Placeholder — full content will be implemented in Task 44.
  ```

  **brand-communication-planning/SKILL.md**:
  ```markdown
  ---
  name: brand-communication-planning
  description: >-
    Messaging architecture, channel strategy, deliverable assembly, and
    implementation planning for Phases 4-5. Phase 4: value proposition,
    messaging hierarchy, Cialdini persuasion principles for F&B, AIDA
    mapping, channel strategy, content pillars, and brand storytelling.
    Phase 5: strategy document assembly, Brand Key one-pager, KPI
    framework, implementation roadmap with budget-tier modifiers, and
    transition/change management planning (rebrand scopes only).
    Use when the orchestrator enters Phase 4 or Phase 5, or when the user
    asks about messaging, communication strategy, brand deliverables,
    implementation planning, or rebrand transition.
  ---

  # Brand Communication & Planning Skill

  > ⚠️ Placeholder — full content will be implemented in Task 45.
  ```

- **Acceptance Criteria**:
  - [ ] 4 skill directories created with correct naming (lowercase, hyphens)
  - [ ] Each has `SKILL.md` with valid YAML frontmatter
  - [ ] `name` matches directory name (Agent Skills spec requirement validated by `_validate_skill_name()`)
  - [ ] `description` ≤ 1024 characters
  - [ ] `SkillsMiddleware._list_skills()` discovers all 4 skills

### Component 2: SkillsMiddleware Configuration

#### Requirement 1 - Configuration Helper Function
- **Requirement**: Factory function that creates a configured SkillsMiddleware ready for brand strategy agent
- **Implementation**:
  - `src/shared/src/shared/agent_skills/config.py`
  ```python
  """Configuration for Agent Skills using DeepAgents built-in SkillsMiddleware.

  Provides factory functions to create pre-configured SkillsMiddleware
  instances for different agent domains. Uses progressive disclosure pattern:
  agent sees skill name + description in system prompt, reads full SKILL.md
  on-demand via FilesystemMiddleware.

  Architecture:
      SkillsMiddleware (built-in from DeepAgents)
      └── FilesystemBackend (local filesystem access)
          └── sources: ["/"]
              ├── brand-strategy-orchestrator/SKILL.md
              ├── market-research/SKILL.md
              ├── brand-positioning-identity/SKILL.md
              └── brand-communication-planning/SKILL.md

  Usage:
      from shared.agent_skills import create_brand_strategy_skills_middleware

      skills_middleware = create_brand_strategy_skills_middleware()
      agent = create_agent(
          model=model,
          middleware=[skills_middleware, ...],
      )
  """
  from pathlib import Path

  from deepagents.backends.filesystem import FilesystemBackend
  from deepagents.middleware.skills import SkillsMiddleware
  from loguru import logger


  # Base path for all agent skills
  _AGENT_SKILLS_DIR = Path(__file__).parent

  # Brand strategy skills source path
  _BRAND_STRATEGY_SKILLS_DIR = _AGENT_SKILLS_DIR / "brand_strategy"


  def create_brand_strategy_skills_middleware() -> SkillsMiddleware:
      """Create SkillsMiddleware pre-configured for brand strategy skills.

      Sets up FilesystemBackend pointing to the brand strategy skills
      directory and configures SkillsMiddleware with a single source.

      The middleware uses progressive disclosure:
      - System prompt shows skill name + description (~300 tokens)
      - Agent reads full SKILL.md on-demand via FilesystemMiddleware
      - Orchestrator skill instructs agent to re-read when changing phases

      Returns:
          Configured SkillsMiddleware instance ready for agent middleware chain.

      Raises:
          FileNotFoundError: If brand strategy skills directory does not exist.

      Example:
          >>> middleware = create_brand_strategy_skills_middleware()
          >>> # Use in agent creation
          >>> agent = create_agent(model=model, middleware=[middleware])
      """
      if not _BRAND_STRATEGY_SKILLS_DIR.exists():
          raise FileNotFoundError(
              f"Brand strategy skills directory not found: "
              f"{_BRAND_STRATEGY_SKILLS_DIR}"
          )

      # FilesystemBackend with virtual_mode=True for safe read-only access
      backend = FilesystemBackend(
          root_dir=str(_BRAND_STRATEGY_SKILLS_DIR),
          virtual_mode=True,
      )

      # Single source — all brand strategy skills under one directory
      # SkillsMiddleware scans for subdirectories containing SKILL.md
      # sources=["/"] means scan from the root of the FilesystemBackend
      # (i.e., the brand_strategy directory itself). The "/" is a
      # virtual path within the backend, not the system root.
      skills_middleware = SkillsMiddleware(
          backend=backend,
          sources=["/"],  # Root of brand_strategy directory (virtual path)
      )

      logger.info(
          "Brand strategy SkillsMiddleware configured. "
          f"Skills dir: {_BRAND_STRATEGY_SKILLS_DIR}"
      )

      return skills_middleware
  ```

#### Requirement 2 - Updated __init__.py
- **Requirement**: Re-export the factory function for clean imports
- **Implementation**:
  - `src/shared/src/shared/agent_skills/__init__.py`
  ```python
  """Agent Skills configuration and setup.

  Provides factory functions for creating SkillsMiddleware instances
  that leverage DeepAgents' built-in progressive disclosure pattern.

  Skills are organized as directories containing SKILL.md files with
  YAML frontmatter (per Agent Skills spec: https://agentskills.io).
  """
  from shared.agent_skills.config import (
      create_brand_strategy_skills_middleware,
  )

  __all__ = [
      "create_brand_strategy_skills_middleware",
  ]
  ```

- **Acceptance Criteria**:
  - [ ] `create_brand_strategy_skills_middleware()` returns configured SkillsMiddleware
  - [ ] FilesystemBackend points to correct directory
  - [ ] `from shared.agent_skills import create_brand_strategy_skills_middleware` works
  - [ ] SkillsMiddleware.before_agent() discovers 4 skills with correct SkillMetadata
  - [ ] System prompt contains skill listing with paths to each SKILL.md

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Skill Discovery
- **Purpose**: Verify SkillsMiddleware discovers all 4 skills from directory
- **Steps**:
  1. Create SkillsMiddleware via `create_brand_strategy_skills_middleware()`
  2. Call internal `_list_skills()` on the backend with source `"/"`
  3. Verify 4 `SkillMetadata` returned
  4. Verify names: brand-strategy-orchestrator, market-research, brand-positioning-identity, brand-communication-planning
- **Expected Result**: 4 skills discovered with correct names and descriptions
- **Status**: ⏳ Pending

### Test Case 2: YAML Frontmatter Validation
- **Purpose**: Verify SKILL.md frontmatter conforms to Agent Skills spec
- **Steps**:
  1. Read each SKILL.md file
  2. Parse YAML frontmatter via `_parse_skill_metadata()`
  3. Verify `name` matches directory name
  4. Verify `description` is non-empty and ≤ 1024 chars
  5. Verify `name` format: lowercase alphanumeric + hyphens, no start/end hyphen
- **Expected Result**: All 4 frontmatters valid per spec
- **Status**: ⏳ Pending

### Test Case 3: System Prompt Injection
- **Purpose**: Verify skills listing appears in system prompt
- **Steps**:
  1. Create middleware via factory function
  2. Simulate `before_agent()` → get `SkillsState` with `skills_metadata`
  3. Simulate `modify_request()` → check system message
  4. Verify contains all 4 skill names + descriptions + paths
- **Expected Result**: System prompt contains skill listing (~300 tokens)
- **Status**: ⏳ Pending

### Test Case 4: On-Demand Skill Read
- **Purpose**: Verify agent can read full SKILL.md content via FilesystemBackend
- **Steps**:
  1. Setup FilesystemBackend with brand_strategy directory
  2. Read `/brand-strategy-orchestrator/SKILL.md` via backend
  3. Verify content includes full YAML frontmatter + markdown body
- **Expected Result**: Complete SKILL.md content returned
- **Status**: ⏳ Pending

### Test Case 5: New Skill Auto-Discovery
- **Purpose**: Verify adding a new skill directory is auto-discovered
- **Steps**:
  1. Create new directory `test-skill/` with valid `SKILL.md`
  2. Re-run `_list_skills()` scan
  3. Verify new skill appears in results
  4. Clean up test directory
- **Expected Result**: 5 skills discovered (4 original + 1 new)
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation.

### What Was Implemented

**Components Completed**:
- [ ] [Component 1]: Skills Directory Structure (4 skill subdirectories with placeholder SKILL.md)
- [ ] [Component 2]: SkillsMiddleware Configuration (factory function + `__init__.py` re-exports)

**Files Created/Modified**:
```
src/shared/src/shared/agent_skills/
├── __init__.py                                           # Updated: re-export factory
├── config.py                                             # NEW: SkillsMiddleware factory
└── brand_strategy/
    ├── brand-strategy-orchestrator/
    │   └── SKILL.md                                      # Placeholder (Task 42 fills)
    ├── market-research/
    │   └── SKILL.md                                      # Placeholder (Task 43 fills)
    ├── brand-positioning-identity/
    │   └── SKILL.md                                      # Placeholder (Task 44 fills)
    └── brand-communication-planning/
        └── SKILL.md                                      # Placeholder (Task 45 fills)
```

### Key Design Decisions

1. **Progressive Disclosure (Option A)**: Dùng built-in SkillsMiddleware thay vì build custom phase-based loading
2. **No custom models/loader/registry**: Tận dụng 100% DeepAgents built-in (`SkillMetadata` TypedDict, `_parse_skill_metadata`, `_list_skills`)
3. **Orchestrator drives re-reads**: Phase transition protocol in orchestrator SKILL.md instructs agent to re-read relevant skill khi chuyển phase
4. **Context efficiency**: Skill content nằm trong message history (bị summarize tự nhiên) thay vì cố định trong system prompt

------------------------------------------------------------------------
