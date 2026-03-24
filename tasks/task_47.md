# Task 47: ToolSearch Middleware — Dynamic Tool Loading for Brand Strategy Agent

## 📌 Metadata

- **Epic**: Brand Strategy — Agent Infrastructure
- **Priority**: High (P1 — Agent has 18+ tools, exceeds Anthropic's 10-tool threshold for defer_loading)
- **Estimated Effort**: 3 days
- **Team**: Backend
- **Related Tasks**: Task 36-40 (tools discovered by ToolSearch), Task 41 (SubAgentMiddleware — similar middleware pattern), Task 35 (SkillsMiddleware — similar progressive disclosure pattern)
- **Blocking**: Task 46 (Agent assembly — needs ToolSearchMiddleware for context-efficient tool binding)
- **Blocked by**: None (infrastructure task; tools can be registered at any time)

### ✅ Progress Checklist

> **Agent**: Update checkboxes as each section is completed. Do NOT mark a section done until it is fully verified.

- [x] 🤖 [Agent Protocol](#-agent-protocol) — Read and confirm before starting
- [x] 🎯 [Context & Goals](#-context--goals) — Problem definition and success metrics
- [x] 🛠 [Solution Design](#-solution-design) — Architecture and technical approach
- [x] 🔬 [Pre-Implementation Research](#-pre-implementation-research) — Findings logged before coding
- [x] 🔄 [Implementation Plan](#-implementation-plan) — Phased execution plan confirmed with user
- [x] 📋 [Implementation Detail](#-implementation-detail) — Component-level specs with test cases
    - [x] ✅ [Component 1: ToolRegistry](#component-1-toolregistry) — Tool metadata storage + search
    - [x] ✅ [Component 2: tool_search Tool](#component-2-tool_search-tool) — Agent-callable discovery tool
    - [x] ✅ [Component 3: ToolSearchMiddleware](#component-3-toolsearchmiddleware) — LangChain middleware
    - [x] ✅ [Component 4: Factory Function & Tool Catalog](#component-4-factory-function--tool-catalog) — create_tool_search_middleware() + brand strategy tool catalog
- [ ] 🧪 [Test Execution Log](#-test-execution-log) — All tests run and results recorded (deferred to integration)
- [ ] 📊 [Decision Log](#-decision-log) — Key decisions documented
- [ ] 📝 [Task Summary](#-task-summary) — Final implementation summary completed

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards (see Agent Protocol section)
- **Blueprint Reference**: `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — Section 5.1 (Tool #7 `tool_search`), Section 6.1 (Core vs Loadable tools diagram)
- **Research Document**: `docs/langchain/tool_search_langchain.md` — Analysis of Claude Code defer_loading + LangChain middleware approach
- **LangChain Middleware Docs**: `https://docs.langchain.com/oss/python/langchain/middleware/custom` — `AgentMiddleware`, `wrap_model_call`, `wrap_tool_call`, `request.override(tools=[...])`
- **LangChain Dynamic Tools**: `https://docs.langchain.com/oss/python/langchain/agents` — "Register and Execute Dynamic Tools at Runtime" pattern
- **Anthropic defer_loading**: `https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/tool-search` — `tool_search_tool_regex` / `tool_search_tool_bm25` reference
- **Existing Middleware Patterns**:
  - `src/shared/src/shared/agent_middlewares/` — `EnsureTasksFinishedMiddleware`, `LogModelMessageMiddleware`
  - `src/shared/src/shared/agent_tools/todo/todo_write_middleware.py` — `TodoWriteMiddleware` (middleware providing a tool)
  - `deepagents.middleware.subagents.SubAgentMiddleware` — provides `task()` tool (same pattern)
- **Prompt Engineering Standards**: `tasks/prompt_engineering_standards.md`

------------------------------------------------------------------------

## 🤖 Agent Protocol

> **MANDATORY**: Read this section in full before starting any implementation work.

### Rule 1 — Research Before Coding

Before writing any code for a component:
1. Read all files referenced in "Reference Documentation" above
2. Read existing code in `src/shared/src/shared/agent_middlewares/` to understand current patterns
3. Read `src/shared/src/shared/agent_tools/todo/todo_write_middleware.py` — it's the closest pattern (middleware that provides a tool)
4. Verify LangChain's `AgentMiddleware` API: `wrap_model_call(request, handler)`, `wrap_tool_call(request, handler)`, `tools` class var
5. Log findings in [Pre-Implementation Research](#-pre-implementation-research) before proceeding
6. **Do NOT assume or invent** behavior — verify against actual LangChain source

### Rule 2 — Ask, Don't Guess

When encountering any of the following, **STOP and ask the user** before proceeding:

- Whether a specific tool should be "core" (always visible) or "loadable" (via tool_search)
- How to handle the case where `request.state` doesn't persist across model calls (verify first)
- Whether `wrap_tool_call` can modify state (verify with LangChain source)
- If the ToolRegistry search algorithm should be upgraded from keyword-based to embedding-based

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

### Rule 5 — Tool Search Specific Standards

Applies to the `tool_search` tool definition and the catalog descriptions that are injected into the system prompt.

- **Tool description**: Must clearly communicate WHEN to use tool_search (agent doesn't see loadable tools initially)
- **Catalog summary**: Must be concise (< 500 tokens) — category names + tool counts, not full descriptions
- **Search results**: Must include tool name, description, and category — enough for the agent to decide
- **3-tool inventory pattern**: `tool_search` (browse catalog) + `load_tools` (equip) + `unload_tools` (unequip). Agent thinks first, decides what to load, and cleans up when done.
- **State management**: Use `request.state["loaded_tools"]` set — middleware intercepts `load_tools`/`unload_tools` calls to add/remove tools from state. Bidirectional: agent can both load AND unload.
- **ToolRuntime access**: `load_tools` and `unload_tools` use `ToolRuntime` (auto-injected, invisible to LLM) to read current loaded state for validation and informative messages.

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Brand Strategy Agent có **18 tools** (7 existing + 10 new + 1 `generate_spreadsheet`) — vượt xa ngưỡng 10 tools mà Anthropic khuyến nghị cho defer_loading
- Khi tất cả 18 tools được bind vào model cùng lúc: **context bloat** (~5K-10K tokens cho tool definitions) + **tool selection accuracy** giảm (model bị overwhelm)
- Claude Code giải quyết vấn đề này bằng `defer_loading` flag: chỉ critical tools hiện trong context, còn lại tìm qua `tool_search_tool_regex`
- LangChain `create_agent` yêu cầu register tất cả tools upfront — nhưng middleware có thể **filter** tools nào visible cho model qua `request.override(tools=[...])`
- Blueprint Section 6.1 đã define sẵn "Core Tools" vs "Loadable Tools" split nhưng chưa có implementation
- File research `docs/langchain/tool_search_langchain.md` đã phân tích pattern và đề xuất middleware approach — cần refine thành production code

### Hiện trạng codebase

```python
# CURRENT (task_46): Register ALL tools upfront — model sees everything
tools = [
    search_knowledge_graph,   # Core: every phase
    search_document_library,  # Core: every phase
    search_web,               # Core: most phases
    scrape_web_content,                # Core: used with search_web
    browse_and_research,      # Loadable: Phase 0.5, 1, 3, 4
    search_places,            # Loadable: Phase 1
    deep_research,            # Core: Phase 1, 4
    analyze_reviews,          # Loadable: Phase 0.5, 1
    analyze_social_profile,   # Loadable: Phase 1
    get_search_autocomplete,  # Loadable: Phase 1, 4
    generate_image,           # Loadable: Phase 3, 5
    generate_brand_key,       # Loadable: Phase 5
    generate_document,        # Loadable: Phase 5
    generate_presentation,    # Loadable: Phase 5
    generate_spreadsheet,     # Loadable: Phase 5
    export_to_markdown,       # Loadable: Phase 0-5 (utility)
]
# Model sees 16 tool definitions + todo_write + task = 18 tools → NOisy

# TARGET: Model initially sees only 10 tools
# Core: search_knowledge_graph, search_document_library, search_web,
#        scrape_web_content, deep_research (5 tools)
# + Middleware tools: tool_search, load_tools, unload_tools,
#                     todo_write, task (5 tools)
# = 10 tools visible initially (44% reduction)
# Remaining 11 tools loaded/unloaded on-demand by the agent
# Agent can also UNLOAD tools when done → keeps context clean
```

### Mục tiêu

1. **ToolRegistry** class lưu trữ metadata cho tất cả tools với search capability
2. **3 meta tools** cho agent quản lý tool inventory:
   - `tool_search(query)` — browse catalog, tìm tools phù hợp (read-only, không tự load)
   - `load_tools(tool_names)` — agent chủ động load tools nó cần (1 hoặc nhiều)
   - `unload_tools(tool_names)` — agent cất tools đi khi dùng xong, giảm context
3. **ToolSearchMiddleware** implements `wrap_model_call` (filter tools) + `wrap_tool_call` (intercept load/unload → update state)
4. **Factory function** `create_tool_search_middleware(all_tools, core_tool_names)` → returns configured middleware
5. **Tool catalog** pre-defined cho BrandMind brand strategy: 5 categories × 11 loadable tools, each with metadata
6. Integration-ready: task_46 imports factory function, passes tools, gets back middleware

### Success Metrics / Acceptance Criteria

- **Context Reduction**: Model initially sees 10 tools instead of 18+ (44%+ reduction in tool definitions)
- **Discovery Accuracy**: `tool_search("generate image")` returns `generate_image` + `generate_brand_key` in top results
- **Explicit Load**: `load_tools(["generate_image"])` → tool appears in next model call's visible tools
- **Explicit Unload**: `unload_tools(["generate_image"])` → tool removed from next model call's visible tools
- **Agent Autonomy**: Agent decides WHAT to load and WHEN to unload — no auto-loading from search results
- **No Lost Capability**: Every tool is still accessible — requires search → load steps for loadable tools
- **Bidirectional State**: Tools can be loaded AND unloaded; state reflects current agent needs, not just accumulation
- **Performance**: ToolRegistry.search < 1ms (in-memory keyword matching, 11 tools)

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**ToolSearchMiddleware with 3-Tool Inventory Pattern**: A LangChain `AgentMiddleware` that provides 3 meta tools (`tool_search`, `load_tools`, `unload_tools`) enabling the agent to manage its own tool inventory — like a game character managing equipment from a warehouse. The middleware filters tool visibility (via `wrap_model_call`) and manages load/unload state (via `wrap_tool_call`). Follows LangChain's `SkillsMiddleware` pattern (progressive disclosure) and `ToolRuntime` for state-aware tool functions.

### Stack công nghệ

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| LangChain `AgentMiddleware` | Base class for middleware | Official API, supports `wrap_model_call` + `wrap_tool_call` + `tools` class var |
| `request.override(tools=[...])` | Filter visible tools per model call | LangChain's native mechanism for dynamic tool selection |
| `request.state` | Persist loaded_tools set across model calls | Built-in agent state management |
| `@tool` decorator | Define tool_search, load_tools, unload_tools | Standard LangChain tool pattern |
| `ToolRuntime` | Access state from within tool functions | Auto-injected, invisible to LLM, lets tools read current loaded state |

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│          create_agent(tools=ALL_TOOLS, middleware=[...])         │
│    All 18 tools registered upfront (LangChain requirement)       │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                   ToolSearchMiddleware                           │
│                                                                  │
│  tools = [tool_search, load_tools, unload_tools]                 │
│           ↑ always available to agent (inventory management)     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  wrap_model_call(request, handler):                        │  │
│  │    loaded = request.state.get("loaded_tools", set())       │  │
│  │    visible = core_tools + [t for t in all                  │  │
│  │              if t.name in loaded]                          │  │
│  │    if first call: inject catalog summary into system       │  │
│  │    return handler(request.override(tools=visible))         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  wrap_tool_call(request, handler):                         │  │
│  │    result = handler(request)  ← execute tool first         │  │
│  │                                                            │  │
│  │    if "load_tools":                                        │  │
│  │      names = request.tool_call["args"]["tool_names"]       │  │
│  │      request.state["loaded_tools"] |= valid_names          │  │
│  │                                                            │  │
│  │    elif "unload_tools":                                    │  │
│  │      names = request.tool_call["args"]["tool_names"]       │  │
│  │      request.state["loaded_tools"] -= names                │  │
│  │                                                            │  │
│  │    return result  ← tool_search passes through (no state)  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ToolRegistry:  (warehouse — all 11 loadable tools)              │
│    ┌───────────────────┬─────────────────────────────────────┐   │
│    │ local_market      │ search_places                       │   │
│    │ social_media      │ browse_and_research,                │   │
│    │                   │ analyze_social_profile              │   │
│    │ customer_analysis │ analyze_reviews,                    │   │
│    │                   │ get_search_autocomplete             │   │
│    │ image_generation  │ generate_image,                     │   │
│    │                   │ generate_brand_key                  │   │
│    │ document_export   │ generate_document,                  │   │
│    │                   │ generate_presentation,              │   │
│    │                   │ generate_spreadsheet,               │   │
│    │                   │ export_to_markdown                  │   │
│    └───────────────────┴─────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Agent Flow Example                          │
│                                                                  │
│  Turn 1: Model sees 10 tools (5 core + 3 meta + todo + task)     │
│    System prompt includes: "## Tool Warehouse" catalog summary   │
│    → Agent uses search_web, search_knowledge_graph (core tools)  │
│                                                                  │
│  Turn N: Agent needs to generate visuals                         │
│    → tool_search("generate image mood board")                    │
│    → Returns: generate_image, generate_brand_key (with desc)     │
│    → Agent THINKS: "I need both for Phase 5"                     │
│    → load_tools(["generate_image", "generate_brand_key"])        │
│    → State: loaded_tools = {generate_image, generate_brand_key}  │
│                                                                  │
│  Turn N+1: Model sees 12 tools (10 + 2 loaded)                   │
│    → Agent uses generate_image(...), generate_brand_key(...)     │
│                                                                  │
│  Turn N+2: Agent done with visuals, needs documents next         │
│    → unload_tools(["generate_image", "generate_brand_key"])      │
│    → State: loaded_tools = {} (cleaned up)                       │
│    → tool_search("create PDF report document")                   │
│    → load_tools(["generate_document"])                           │
│    → Agent uses generate_document(...)                           │
│                                                                  │
│  Turn N+3: Model sees 11 tools (10 + 1 loaded)                   │
│    → Context stays lean — only active tools visible              │
└──────────────────────────────────────────────────────────────────┘
```

### Issues & Solutions

1. **Tools registered upfront but hidden** → `request.override(tools=filtered)` passes only visible tools to model; all tools remain executable by middleware
2. **State persistence across model calls** → LangChain `request.state` dict persists within a conversation thread (backed by checkpointer). Middleware's `wrap_tool_call` mutates this dict directly.
3. **Agent autonomy in tool selection** → Agent explicitly calls `load_tools` and `unload_tools` — no automatic loading from search results. Agent must THINK about what it needs, then act. Mirrors game inventory: player decides what to equip.
4. **Bidirectional state management** → `unload_tools` removes tools from `loaded_tools` set, reducing visible tools on next model call. Keeps context lean when agent switches between workflow phases.
5. **Catalog summary bloating system prompt** → Keep summary ultra-compact: 5 category lines × ~15 words = ~75 words ≈ 100 tokens
6. **State access from tool functions** → `load_tools` and `unload_tools` use `ToolRuntime` (auto-injected, invisible to LLM) to read current loaded state for validation and user-friendly confirmation messages

------------------------------------------------------------------------

## 🔬 Pre-Implementation Research

> **Agent**: Complete this section BEFORE writing any implementation code.

### Codebase Audit

- **Files to read**:
  - `src/shared/src/shared/agent_middlewares/` — all files, understand existing middleware patterns
  - `src/shared/src/shared/agent_tools/todo/todo_write_middleware.py` — middleware providing a tool (closest pattern)
  - `src/shared/src/shared/agent_tools/__init__.py` — current tool exports
  - `src/cli/inference.py` → `create_qa_agent()` — how agent is assembled with middlewares
  - `src/core/src/core/knowledge_graph/cartographer/agent_config.py` — SubAgentMiddleware usage
- **Relevant patterns found**: [To be filled by implementing agent]
- **Potential conflicts**: [To be filled by implementing agent]

### External Library / API Research

- **LangChain AgentMiddleware API** (verified via context7):
  - `AgentMiddleware` base class with `wrap_model_call` + `wrap_tool_call` hooks
  - `tools` class variable: list of tools that middleware provides (auto-added to agent)
  - `ModelRequest` fields: `.state` (dict), `.tools` (list), `.system_message`, `.messages`
  - `request.override(tools=[...])` — replaces tool list for current model call
  - `request.override(system_message=...)` — replaces system message
  - `ToolCallRequest` fields: `.tool_call` (dict with `name`, `args`, `id`), `.state`
  - State is a shared dict persisted across model calls within a thread
- **Anthropic defer_loading** (reference):
  - `tool_search_tool_regex`: Model sends regex pattern, matching tool definitions returned and become available
  - `tool_search_tool_bm25`: Model sends natural language query, BM25 search returns matching tools
  - Both: searched tools automatically become available for the next model call — no separate "load" step
  - Threshold: Anthropic recommends defer_loading when agent has > 10 tools

### Unknown / Risks Identified

- [ ] **Risk**: `request.state` may not persist if `SummarizationMiddleware` or `ContextEditingMiddleware` resets it → Verify that state dict survives middleware chain. Mitigation: state is separate from messages, should persist.
- [ ] **Risk**: `wrap_tool_call` may execute AFTER tool execution (vs before) → Verify hook timing. If post-execution: parse `tool_search` return value to extract found tool names.
- [ ] **Risk**: System prompt injection via `request.override(system_message=...)` may conflict with SkillsMiddleware's own system prompt modification → Verify middleware ordering. Ensure ToolSearchMiddleware runs BEFORE SkillsMiddleware in the chain.
- [ ] **Unknown**: Does `request.override(tools=[...])` fully replace tools or merge? → LangChain docs show replacement (`override` = replace). Confirmed.

### Research Status

- [x] All referenced documentation read (LangChain middleware docs, Anthropic defer_loading docs)
- [x] Existing codebase patterns understood (QA agent assembly, TodoWriteMiddleware)
- [x] External dependencies verified (LangChain AgentMiddleware API)
- [ ] No unresolved ambiguities remain → [state persistence and wrap_tool_call timing need runtime verification]

------------------------------------------------------------------------

## 🔄 Implementation Plan

### Phase 1: Core Infrastructure — 1.5 days

1. **ToolRegistry + ToolMetadata** (Component 1)
   - Dataclasses for tool metadata storage
   - Keyword-based search with scoring
   - Category-aware catalog summary generation
   - *Checkpoint: Unit tests pass for search accuracy*

2. **tool_search Tool** (Component 2)
   - LangChain `@tool` definition
   - Clear docstring with usage examples
   - Formatted output with tool names and descriptions
   - *Checkpoint: Tool callable independently, returns formatted results*

3. **ToolSearchMiddleware** (Component 3)
   - `wrap_model_call`: filter tools based on state
   - `wrap_tool_call`: intercept tool_search, update state
   - System prompt catalog injection on first call
   - *Checkpoint: Middleware filters tools correctly in isolated test*

### Phase 2: Integration — 1 day

4. **Factory Function & Catalog** (Component 4)
   - `create_tool_search_middleware(all_tools, core_tool_names)` factory
   - Brand Strategy tool catalog (5 categories × 11 tools)
   - *Checkpoint: Factory produces working middleware*

5. **task_46 Integration** (separate task update)
   - Update `create_brand_strategy_agent()` to use ToolSearchMiddleware
   - *Checkpoint: Agent creates successfully with ToolSearchMiddleware in chain*

### Phase 3: Verification — 0.5 days

6. **Integration testing**
   - Verify tool_search → auto-load → tool usage flow
   - Verify core tools always visible
   - Verify state persistence across model calls
   - *Checkpoint: All Test Execution Log entries pass*

### Rollback Plan

Remove `ToolSearchMiddleware` from middleware chain in `create_brand_strategy_agent()` and pass all tools directly (revert to current task_46 behavior). No database or config changes to revert.

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards Reminder**: Apply the standards from Agent Protocol Rule 4 to every file.
> Test specifications are written BEFORE implementation — follow TDD order within each requirement.

### Component 1: ToolRegistry

> Status: ⏳ Pending

#### Requirement 1 — ToolMetadata Dataclass

- **Requirement**: Immutable metadata record for each tool in the registry. Stores name, description, category, keywords, and the phases where it's used.

- **Test Specification**:
  ```python
  # Test: ToolMetadata creation with all fields
  # Input: ToolMetadata(name="search_places", description="Search local businesses...",
  #         category="local_market", keywords=["google places", "nearby", "competitors"],
  #         phases=["1"])
  # Expected: All fields accessible, frozen dataclass (immutable)

  # Test: ToolMetadata from_tool class method
  # Input: A LangChain @tool function with name and description attributes
  # Expected: ToolMetadata created with name and description extracted from tool
  ```

- **Implementation**:
  - `src/shared/src/shared/agent_middlewares/tool_search/__init__.py`
  ```python
  """Dynamic tool loading middleware — inventory pattern for LangChain.

  Implements a game-like tool inventory system using LangChain middleware:
  - tool_search: Browse the warehouse catalog
  - load_tools: Equip tools the agent needs
  - unload_tools: Put tools back when done
  - Only equipped tools (core + loaded) are visible in model context

  Usage:
      from shared.agent_middlewares.tool_search import create_tool_search_middleware

      middleware = create_tool_search_middleware(
          all_tools=tools,
          core_tool_names={"search_web", "scrape_web_content", ...},
          tool_catalog=BRAND_STRATEGY_TOOL_CATALOG,
      )
  """

  from .middleware import ToolSearchMiddleware, create_tool_search_middleware
  from .registry import ToolMetadata, ToolRegistry

  __all__ = [
      "ToolSearchMiddleware",
      "ToolRegistry",
      "ToolMetadata",
      "create_tool_search_middleware",
  ]
  ```

  - `src/shared/src/shared/agent_middlewares/tool_search/registry.py`
  ```python
  """Tool registry for dynamic tool loading.

  Stores metadata for all loadable tools and provides keyword-based search
  with scoring. Designed for small catalogs (10-50 tools) where in-memory
  keyword matching is faster than embedding-based search.
  """
  from __future__ import annotations

  from dataclasses import dataclass, field


  @dataclass(frozen=True)
  class ToolMetadata:
      """Immutable metadata for a tool: name, description, category, keywords, phases."""

      name: str
      description: str
      category: str
      keywords: tuple[str, ...] = ()
      phases: tuple[str, ...] = ()

      def __post_init__(self) -> None:
          """Coerce lists to tuples for true immutability."""
          if isinstance(self.keywords, list):
              object.__setattr__(self, "keywords", tuple(self.keywords))
          if isinstance(self.phases, list):
              object.__setattr__(self, "phases", tuple(self.phases))
  ```

- **Acceptance Criteria**:
  - [ ] `ToolMetadata` is frozen dataclass (immutable after creation)
  - [ ] All fields typed and documented
  - [ ] `keywords` and `phases` default to empty tuple; lists auto-coerced via `__post_init__`

#### Requirement 2 — ToolRegistry Search Engine

- **Requirement**: In-memory registry that stores ToolMetadata entries grouped by category and provides keyword-based search with relevance scoring. Must support multi-word queries, partial matching, and return results sorted by score.

- **Test Specification**:
  ```python
  # Test: Exact name match (highest score)
  # Setup: Registry with "generate_image" tool
  # Input: registry.search("generate_image")
  # Expected: "generate_image" in results with highest score

  # Test: Keyword match
  # Setup: Registry with tools having keywords ["mood board", "logo", "visual"]
  # Input: registry.search("mood board")
  # Expected: Tools with "mood board" keyword returned

  # Test: Category match
  # Setup: Registry with "image_generation" category
  # Input: registry.search("image")
  # Expected: All tools in image_generation category returned

  # Test: Multi-word query
  # Input: registry.search("generate document report")
  # Expected: document_export category tools ranked higher than others

  # Test: No results
  # Input: registry.search("blockchain")
  # Expected: Empty list

  # Test: get_summary returns compact catalog
  # Expected: String with category names, tool counts, and short descriptions
  #           Total length < 500 tokens (~375 words)
  ```

- **Implementation**:
  - `src/shared/src/shared/agent_middlewares/tool_search/registry.py` (continued)
  ```python
  class ToolRegistry:
      """Registry for loadable tools with keyword-based search.

      Stores tools grouped by category. Search uses multi-signal scoring:
      - Exact name match: +10 points
      - Name contains query word: +5 points
      - Description contains query word: +3 points
      - Category contains query word: +4 points
      - Keyword exact match: +6 points
      - Keyword contains query word: +2 points

      Designed for small catalogs (10-50 tools). For larger catalogs,
      consider upgrading to embedding-based search.
      """

      def __init__(self) -> None:
          """Initialize empty registry."""
          self._tools: dict[str, ToolMetadata] = {}
          self._categories: dict[str, list[str]] = {}

      def register(self, metadata: ToolMetadata) -> None:
          """Register a tool. Raises ValueError on duplicate name."""
          if metadata.name in self._tools:
              raise ValueError(
                  f"Tool '{metadata.name}' already registered. "
                  f"Use update() to modify existing entries."
              )
          self._tools[metadata.name] = metadata

          # Index by category
          if metadata.category not in self._categories:
              self._categories[metadata.category] = []
          self._categories[metadata.category].append(metadata.name)

      def register_many(self, metadata_list: list[ToolMetadata]) -> None:
          """Register multiple tools at once."""
          for metadata in metadata_list:
              self.register(metadata)

      def search(self, query: str, top_k: int = 5) -> list[ToolMetadata]:
          """Search tools by natural language query with relevance scoring.

          Args:
              query: Search query (e.g., "generate image", "social media analysis").
              top_k: Maximum results to return.

          Returns:
              List of ToolMetadata sorted by relevance, up to top_k items.
          """
          if not query or not query.strip():
              return []

          query_words = query.lower().split()
          scored_results: list[tuple[int, ToolMetadata]] = []

          for meta in self._tools.values():
              score = self._score_tool(meta, query_words)
              if score > 0:
                  scored_results.append((score, meta))

          # Sort by score descending, then by name for stable ordering
          scored_results.sort(key=lambda x: (-x[0], x[1].name))
          return [meta for _, meta in scored_results[:top_k]]

      def get_tools_in_category(self, category: str) -> list[ToolMetadata]:
          """Get all tools in a category. Returns empty list if not found."""
          tool_names = self._categories.get(category, [])
          return [self._tools[name] for name in tool_names if name in self._tools]

      def get_category_for_tool(self, tool_name: str) -> str | None:
          """Get the category for a tool, or None if not found."""
          meta = self._tools.get(tool_name)
          return meta.category if meta else None

      def get_all_tool_names_in_category(self, category: str) -> set[str]:
          """Get all tool names in a category as a set."""
          return set(self._categories.get(category, []))

      def has_tool(self, tool_name: str) -> bool:
          """Check if a tool exists in the registry."""
          return tool_name in self._tools

      def get_category_names(self) -> list[str]:
          """Get sorted list of all category names."""
          return sorted(self._categories.keys())

      def get_summary(self) -> str:
          """Generate compact catalog summary (< 500 tokens) for system prompt."""
          lines: list[str] = []
          for category, tool_names in sorted(self._categories.items()):
              tools = [self._tools[n] for n in tool_names if n in self._tools]
              if not tools:
                  continue
              tool_list = ", ".join(t.name for t in tools)
              count = len(tools)
              category_label = category.replace("_", " ").title()
              lines.append(
                  f"- **{category_label}** ({count} tool{'s' if count > 1 else ''}): "
                  f"{tool_list}"
              )
          return "\n".join(lines)

      @staticmethod
      def _score_tool(meta: ToolMetadata, query_words: list[str]) -> int:
          """Score a tool against lowercased query words. Returns 0 if no match."""
          score = 0
          name_lower = meta.name.lower()
          desc_lower = meta.description.lower()
          cat_lower = meta.category.lower()
          keywords_lower = [kw.lower() for kw in meta.keywords]

          for word in query_words:
              # Exact name match (full query word matches tool name)
              if word == name_lower:
                  score += 10
              elif word in name_lower:
                  score += 5

              # Description match
              if word in desc_lower:
                  score += 3

              # Category match
              if word in cat_lower:
                  score += 4

              # Keyword matching
              for kw in keywords_lower:
                  if word == kw:
                      score += 6
                  elif word in kw or kw in word:
                      score += 2

          return score
  ```

- **Acceptance Criteria**:
  - [ ] `register()` stores metadata and indexes by category
  - [ ] `register()` raises `ValueError` on duplicate name
  - [ ] `search()` returns results sorted by relevance score
  - [ ] `search()` handles multi-word queries (each word scored independently)
  - [ ] `search("")` returns empty list (no crash)
  - [ ] `get_summary()` returns compact string < 500 tokens
  - [ ] `get_all_tool_names_in_category()` returns full set for category tools
  - [ ] `has_tool()` returns True for registered tools, False otherwise

---

### Component 2: Tool Inventory Tools (tool_search, load_tools, unload_tools)

> Status: ⏳ Pending

#### Requirement 1 — tool_search Tool (Browse Catalog)

- **Requirement**: A read-only LangChain `@tool` function that searches the ToolRegistry and returns formatted results. Does NOT load tools — agent must explicitly call `load_tools` afterwards. The docstring must clearly explain the search→load→use→unload workflow.

- **Test Specification**:
  ```python
  # Test: Search with matching query
  # Input: tool_search("generate image mood board")
  # Expected: Formatted string with generate_image and generate_brand_key entries
  #           Includes tool name, category, description
  #           Does NOT say "tools are now loaded" (read-only search)

  # Test: Search with no matches
  # Input: tool_search("cryptocurrency trading")
  # Expected: "No matching tools found" message with category hints

  # Test: Search shows related tools in same category
  # Input: tool_search("social media")
  # Expected: browse_and_research AND analyze_social_profile listed
  ```

#### Requirement 2 — load_tools Tool (Equip Items)

- **Requirement**: A LangChain `@tool` function that the agent calls to explicitly load specific tools into its context. Uses `ToolRuntime` to read current loaded state for validation. Returns confirmation listing what was loaded.

- **Test Specification**:
  ```python
  # Test: Load valid tools
  # Input: load_tools(["generate_image", "generate_brand_key"])
  # Expected: "Loaded 2 tools: generate_image, generate_brand_key"

  # Test: Load with already-loaded tools
  # Setup: generate_image already in loaded_tools
  # Input: load_tools(["generate_image", "generate_brand_key"])
  # Expected: "Loaded 1 new tool: generate_brand_key. Already loaded: generate_image"

  # Test: Load with invalid tool name
  # Input: load_tools(["nonexistent_tool"])
  # Expected: "Not found in catalog: nonexistent_tool"
  ```

#### Requirement 3 — unload_tools Tool (Unequip Items)

- **Requirement**: A LangChain `@tool` function that the agent calls to remove tools from its context. Uses `ToolRuntime` to check what's currently loaded. Returns confirmation listing what was unloaded.

- **Test Specification**:
  ```python
  # Test: Unload loaded tools
  # Setup: generate_image, generate_brand_key in loaded_tools
  # Input: unload_tools(["generate_image", "generate_brand_key"])
  # Expected: "Unloaded 2 tools: generate_image, generate_brand_key"

  # Test: Unload tool not currently loaded
  # Input: unload_tools(["generate_image"])
  # Expected: "Not currently loaded: generate_image"

  # Test: Mixed unload (some loaded, some not)
  # Setup: generate_image loaded, generate_brand_key not loaded
  # Input: unload_tools(["generate_image", "generate_brand_key"])
  # Expected: "Unloaded: generate_image. Not currently loaded: generate_brand_key"
  ```

- **Implementation** (all 3 tools):
  - `src/shared/src/shared/agent_middlewares/tool_search/middleware.py`
  ```python
  """ToolSearch middleware — dynamic tool loading for LangChain agents.

  Provides tool_search/load_tools/unload_tools inventory pattern.
  Filters model context to core + loaded tools only.
  Place BEFORE SkillsMiddleware in the middleware chain.
  """
  from __future__ import annotations

  from typing import Callable

  from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
  from langchain.messages import SystemMessage, ToolMessage
  from langchain.tools import tool, ToolRuntime
  from langchain.tools.tool_node import ToolCallRequest
  from langgraph.types import Command
  from loguru import logger

  from .registry import ToolRegistry

  # Set once by factory function; read-only after init.
  # Per-request mutable state lives in request.state, not here.
  _registry: ToolRegistry | None = None


  @tool
  def tool_search(query: str) -> str:
      """Search the tool warehouse for specialized capabilities.

      You start with core tools only. This BROWSES the catalog (does NOT load).
      After reviewing results, use load_tools() to equip what you need.

      Searchable: image generation, document creation (PDF/DOCX/PPTX/XLSX),
      local market (Google Places), social media analysis, customer reviews.

      Args:
          query: Capability description. Examples: "generate image",
                "social media analysis", "create PDF document"
      """
      if _registry is None:
          return "Tool registry not initialized. Contact system administrator."

      results = _registry.search(query, top_k=8)

      if not results:
          return (
              f"No matching tools found for '{query}'. "
              f"Try different search terms. Available categories: "
              f"{', '.join(_registry.get_category_names())}"
          )

      lines = [f"Found {len(results)} tool(s) matching '{query}':\n"]
      seen_categories: set[str] = set()

      for meta in results:
          lines.append(f"**{meta.name}**")
          lines.append(f"  Category: {meta.category}")
          lines.append(f"  Description: {meta.description}")
          if meta.phases:
              lines.append(f"  Typical phases: {', '.join(meta.phases)}")
          lines.append("")
          seen_categories.add(meta.category)

      # Show related tools in same categories that weren't in top results
      related: list[str] = []
      for cat in seen_categories:
          cat_tools = _registry.get_all_tool_names_in_category(cat)
          result_names = {m.name for m in results}
          additional = cat_tools - result_names
          if additional:
              related.extend(additional)

      if related:
          lines.append(
              f"Other tools in same categories: {', '.join(sorted(related))}"
          )

      lines.append(
          "\nTo use these tools, call load_tools() with the tool names you need."
      )

      return "\n".join(lines)


  @tool
  def load_tools(tool_names: list[str], runtime: ToolRuntime) -> str:
      """Load (equip) tools into your active set so you can use them.

      After tool_search(), call this with the tool names you want.
      Loaded tools appear in your tool list on the next action.

      Args:
          tool_names: Tool names from catalog. Example: ["generate_image"]
      """
      if _registry is None:
          return "Tool registry not initialized. Contact system administrator."

      loaded = runtime.state.get("loaded_tools", set())
      newly_loaded: list[str] = []
      already_loaded: list[str] = []
      not_found: list[str] = []

      for name in tool_names:
          if not _registry.has_tool(name):
              not_found.append(name)
          elif name in loaded:
              already_loaded.append(name)
          else:
              newly_loaded.append(name)

      parts: list[str] = []
      if newly_loaded:
          parts.append(
              f"Loaded {len(newly_loaded)} tool(s): {', '.join(newly_loaded)}"
          )
      if already_loaded:
          parts.append(f"Already loaded: {', '.join(already_loaded)}")
      if not_found:
          parts.append(
              f"Not found in catalog: {', '.join(not_found)}. "
              f"Use tool_search() to find valid tool names."
          )

      if newly_loaded:
          parts.append("These tools are now available for use.")

      return "\n".join(parts) if parts else "No tools specified."


  @tool
  def unload_tools(tool_names: list[str], runtime: ToolRuntime) -> str:
      """Unload (unequip) tools from your active set to keep context lean.

      Call when done with tools. You can always load them again later.

      Args:
          tool_names: Tool names to unload. Example: ["generate_image"]
      """
      loaded = runtime.state.get("loaded_tools", set())
      unloaded: list[str] = []
      not_loaded: list[str] = []

      for name in tool_names:
          if name in loaded:
              unloaded.append(name)
          else:
              not_loaded.append(name)

      parts: list[str] = []
      if unloaded:
          parts.append(f"Unloaded {len(unloaded)} tool(s): {', '.join(unloaded)}")
      if not_loaded:
          parts.append(f"Not currently loaded: {', '.join(not_loaded)}")

      if unloaded:
          parts.append("These tools are no longer in your active set.")

      return "\n".join(parts) if parts else "No tools specified."
  ```

- **Acceptance Criteria**:
  - [ ] `tool_search` is read-only — does NOT modify state or load tools
  - [ ] `tool_search` returns formatted results with name, category, description
  - [ ] `tool_search` shows related category tools for awareness
  - [ ] `tool_search` returns friendly message with category hints when no results found
  - [ ] `load_tools` uses `ToolRuntime` to check current loaded state
  - [ ] `load_tools` validates tool names against registry
  - [ ] `load_tools` reports newly loaded, already loaded, and not found separately
  - [ ] `unload_tools` uses `ToolRuntime` to check current loaded state
  - [ ] `unload_tools` reports unloaded and not-currently-loaded separately
  - [ ] All 3 tools have clear docstrings explaining the inventory workflow
  - [ ] `ToolRuntime` parameter is invisible to the LLM (auto-injected)

---

### Component 3: ToolSearchMiddleware

> Status: ⏳ Pending

#### Requirement 1 — Middleware Class with wrap_model_call

- **Requirement**: LangChain `AgentMiddleware` subclass that filters tool visibility based on loaded state. On first model call, injects a compact tool catalog summary into the system prompt. On subsequent calls, shows core tools + any tools loaded via `load_tools`. After `unload_tools`, previously visible tools are removed.

- **Test Specification**:
  ```python
  # Test: First model call sees only core tools + 3 meta tools
  # Setup: Middleware with 5 core tools and 11 loadable tools
  # Input: ModelRequest with all 16 tools, empty state
  # Expected: handler called with request.override(tools=[5 core + tool_search
  #           + load_tools + unload_tools])
  #           System message includes tool catalog summary

  # Test: After load_tools, model sees core + loaded tools
  # Setup: state["loaded_tools"] = {"generate_image", "generate_brand_key"}
  # Input: ModelRequest with all tools
  # Expected: handler called with tools=[5 core + 3 meta + generate_image
  #           + generate_brand_key]

  # Test: After unload_tools, model no longer sees unloaded tools
  # Setup: state["loaded_tools"] = {} (after unloading)
  # Input: ModelRequest with all tools
  # Expected: handler called with tools=[5 core + 3 meta] (back to initial)

  # Test: System prompt injection only on first call
  # Input: Two consecutive ModelRequests
  # Expected: Catalog injected on first call only
  ```

#### Requirement 2 — Middleware Class with wrap_tool_call

- **Requirement**: Intercepts `load_tools` and `unload_tools` calls to update `request.state["loaded_tools"]`. `tool_search` passes through without state modification. State changes take effect on the next `wrap_model_call`.

- **Test Specification**:
  ```python
  # Test: load_tools intercept — adds to state
  # Input: tool_call is load_tools(["generate_image"])
  # Expected: After handler, state["loaded_tools"] == {"generate_image"}

  # Test: unload_tools intercept — removes from state
  # Setup: state["loaded_tools"] = {"generate_image", "generate_brand_key"}
  # Input: tool_call is unload_tools(["generate_image"])
  # Expected: state["loaded_tools"] == {"generate_brand_key"}

  # Test: tool_search passes through — no state change
  # Input: tool_call is tool_search("image")
  # Expected: state unchanged, result returned as-is

  # Test: load then unload then load again
  # Expected: State correctly tracks all transitions
  ```

- **Implementation**:
  - `src/shared/src/shared/agent_middlewares/tool_search/middleware.py` (continued)
  ```python
  class ToolSearchMiddleware(AgentMiddleware):
      """Filters tool visibility and manages load/unload state for LangChain agents.

      Provides 3 inventory tools (tool_search, load_tools, unload_tools) and
      filters model context to only show core + currently loaded tools.
      Place BEFORE SkillsMiddleware in the middleware chain.
      """

      # 3 inventory tools — always available to the agent
      tools = [tool_search, load_tools, unload_tools]

      # Names of the meta tools (used for filtering logic)
      _META_TOOL_NAMES = {"tool_search", "load_tools", "unload_tools"}

      def __init__(
          self,
          registry: ToolRegistry,
          core_tool_names: set[str],
      ) -> None:
          """Initialize middleware.

          Args:
              registry: ToolRegistry with metadata for all loadable tools.
              core_tool_names: Tool names always visible to the model.
                  Meta tools are auto-included.
          """
          self.registry = registry
          self.core_tool_names = core_tool_names | self._META_TOOL_NAMES

          # Set module-level registry for tool functions
          global _registry
          _registry = registry

      def wrap_model_call(
          self,
          request: ModelRequest,
          handler: Callable[[ModelRequest], ModelResponse],
      ) -> ModelResponse:
          """Filter visible tools to core + loaded; inject catalog on first call."""
          loaded_names: set[str] = request.state.get("loaded_tools", set())

          # Filter tools: core + meta + currently loaded
          visible_tools = [
              t for t in request.tools
              if t.name in self.core_tool_names or t.name in loaded_names
          ]

          # Inject tool catalog into system prompt on first call
          catalog_injected = request.state.get("_tool_catalog_injected", False)

          if not catalog_injected:
              catalog_summary = self.registry.get_summary()
              addendum = (
                  "\n\n## Tool Warehouse\n\n"
                  "You currently see only core tools. Specialized tools are in "
                  "the warehouse. Use the inventory workflow:\n"
                  "1. `tool_search(query)` — browse catalog, find tools\n"
                  "2. `load_tools([names])` — equip tools you need\n"
                  "3. Use the loaded tools\n"
                  "4. `unload_tools([names])` — unequip when done\n\n"
                  f"Available in warehouse:\n{catalog_summary}\n"
              )

              if request.system_message:
                  current_content = request.system_message.content
                  if isinstance(current_content, str):
                      new_content = current_content + addendum
                  elif isinstance(current_content, list):
                      new_content = list(current_content) + [
                          {"type": "text", "text": addendum}
                      ]
                  else:
                      new_content = str(current_content) + addendum
                  new_system = SystemMessage(content=new_content)
              else:
                  # No system message — create one with just the catalog
                  new_system = SystemMessage(content=addendum)

              request.state["_tool_catalog_injected"] = True
              return handler(request.override(
                  system_message=new_system,
                  tools=visible_tools,
              ))

          return handler(request.override(tools=visible_tools))

      def wrap_tool_call(
          self,
          request: ToolCallRequest,
          handler: Callable[[ToolCallRequest], ToolMessage | Command],
      ) -> ToolMessage | Command:
          """Intercept load/unload calls to update state["loaded_tools"].

          State mutation happens HERE, not in tool functions. Tool functions
          only read state (via ToolRuntime) for validation messages.
          tool_search and all other tools pass through unchanged.
          """
          tool_name = request.tool_call["name"]

          # Execute the tool first — get the result
          result = handler(request)

          # Update state based on which meta tool was called
          if tool_name == "load_tools":
              names_to_load = request.tool_call["args"].get("tool_names", [])
              loaded = request.state.get("loaded_tools", set())
              # Only add names that exist in the registry
              valid_names = {
                  n for n in names_to_load if self.registry.has_tool(n)
              }
              request.state["loaded_tools"] = loaded | valid_names

          elif tool_name == "unload_tools":
              names_to_unload = request.tool_call["args"].get("tool_names", [])
              loaded = request.state.get("loaded_tools", set())
              request.state["loaded_tools"] = loaded - set(names_to_unload)

          # tool_search and all other tools: no state change

          return result
  ```

- **Acceptance Criteria**:
  - [ ] `tools = [tool_search, load_tools, unload_tools]` — all 3 meta tools provided
  - [ ] `wrap_model_call` filters tools to core + meta + currently loaded only
  - [ ] First call injects catalog summary with inventory workflow instructions
  - [ ] Catalog injection happens only once (state flag `_tool_catalog_injected`)
  - [ ] Handles both string and list system message content formats
  - [ ] `wrap_tool_call` intercepts `load_tools` → adds valid names to state
  - [ ] `wrap_tool_call` intercepts `unload_tools` → removes names from state
  - [ ] `wrap_tool_call` passes `tool_search` through (read-only, no state change)
  - [ ] State is bidirectional: tools can be added AND removed
  - [ ] After unload, tools disappear from next model call
  - [ ] Global `_registry` set correctly for tool functions

---

### Component 4: Factory Function & Tool Catalog

> Status: ⏳ Pending

#### Requirement 1 — Brand Strategy Tool Catalog

- **Requirement**: Pre-defined tool metadata catalog for all 11 loadable tools in BrandMind brand strategy, organized into 5 categories. Each entry has name, description, category, keywords, and typical phases.

- **Implementation**:
  - `src/shared/src/shared/agent_middlewares/tool_search/middleware.py` (continued, or separate `catalog.py`)
  ```python
  # ---- Brand Strategy Tool Catalog ----
  # Defines metadata for all loadable tools (11 tools in 5 categories).
  # Core tools (search_knowledge_graph, search_document_library, search_web,
  # scrape_web_content, deep_research) are NOT in this catalog — they are always visible.

  BRAND_STRATEGY_TOOL_CATALOG: list[ToolMetadata] = [
      # ---- Category: local_market ----
      ToolMetadata(
          name="search_places",
          description=(
              "Search local businesses using Google Places API. "
              "Find competitors, map the competitive landscape in a specific area."
          ),
          category="local_market",
          keywords=[
              "google places", "nearby", "local", "competitors",
              "location", "restaurant", "cafe", "F&B", "map",
              "district", "area", "radius",
          ],
          phases=["1"],
      ),

      # ---- Category: social_media ----
      ToolMetadata(
          name="browse_and_research",
          description=(
              "Browse and research social media profiles using automated browser. "
              "Analyze competitor content strategy, engagement, and brand presence."
          ),
          category="social_media",
          keywords=[
              "instagram", "facebook", "tiktok", "social", "followers",
              "engagement", "content", "posts", "stories", "reels",
              "social media", "browse", "profile",
          ],
          phases=["0.5", "1", "3", "4"],
      ),
      ToolMetadata(
          name="analyze_social_profile",
          description=(
              "Analyze a social media profile's brand strategy — "
              "content themes, engagement patterns, posting frequency, audience."
          ),
          category="social_media",
          keywords=[
              "social profile", "brand analysis", "content strategy",
              "engagement rate", "social analysis", "competitor social",
          ],
          phases=["1"],
      ),

      # ---- Category: customer_analysis ----
      ToolMetadata(
          name="analyze_reviews",
          description=(
              "Aggregate and analyze customer reviews from Google Maps and social media. "
              "Extract sentiment patterns, recurring themes, and perception insights."
          ),
          category="customer_analysis",
          keywords=[
              "reviews", "sentiment", "customer perception", "google reviews",
              "rating", "feedback", "complaints", "praise", "opinions",
          ],
          phases=["0.5", "1"],
      ),
      ToolMetadata(
          name="get_search_autocomplete",
          description=(
              "Get Google search autocomplete suggestions for keyword and topic research. "
              "Discover what consumers are searching for related to your brand/category."
          ),
          category="customer_analysis",
          keywords=[
              "autocomplete", "search trends", "keyword research",
              "google suggest", "consumer search", "search behavior",
          ],
          phases=["1", "4"],
      ),

      # ---- Category: image_generation ----
      ToolMetadata(
          name="generate_image",
          description=(
              "Generate visual brand assets using Gemini 3.1 Flash Image Preview — "
              "mood boards, logo concepts, color palette visualizations, social media mockups."
          ),
          category="image_generation",
          keywords=[
              "image", "visual", "mood board", "logo", "color palette",
              "design", "mockup", "brand visual", "illustration",
              "generate image", "create image",
          ],
          phases=["3", "5"],
      ),
      ToolMetadata(
          name="generate_brand_key",
          description=(
              "Generate Brand Key one-pager visual — the summary infographic of the "
              "complete brand strategy (positioning, personality, values, target audience)."
          ),
          category="image_generation",
          keywords=[
              "brand key", "one-pager", "infographic", "brand summary",
              "visual summary", "brand key visual",
          ],
          phases=["5"],
      ),

      # ---- Category: document_export ----
      ToolMetadata(
          name="generate_document",
          description=(
              "Generate brand strategy documents in PDF or DOCX format. "
              "Professional formatting with cover page, table of contents, and sections."
          ),
          category="document_export",
          keywords=[
              "document", "PDF", "DOCX", "report", "strategy document",
              "brand book", "generate document", "create document",
          ],
          phases=["5"],
      ),
      ToolMetadata(
          name="generate_presentation",
          description=(
              "Generate brand strategy presentations in PPTX format. "
              "Executive pitch decks with branded slides."
          ),
          category="document_export",
          keywords=[
              "presentation", "PPTX", "PowerPoint", "pitch deck",
              "slides", "executive summary", "generate presentation",
          ],
          phases=["5"],
      ),
      ToolMetadata(
          name="generate_spreadsheet",
          description=(
              "Generate brand strategy spreadsheets in XLSX format — "
              "competitor analysis matrix, brand audit scorecard, content calendar, "
              "KPI dashboard, budget plan. Formula-driven with auto-calculations."
          ),
          category="document_export",
          keywords=[
              "spreadsheet", "XLSX", "Excel", "matrix", "scorecard",
              "calendar", "dashboard", "budget", "table", "data",
          ],
          phases=["5"],
      ),
      ToolMetadata(
          name="export_to_markdown",
          description=(
              "Export brand strategy content to well-formatted Markdown. "
              "Clean text export for documentation, README files, or wikis."
          ),
          category="document_export",
          keywords=[
              "markdown", "export", "text", "format", "documentation",
              "MD", "plain text",
          ],
          phases=["0", "1", "2", "3", "4", "5"],
      ),
  ]
  ```

- **Acceptance Criteria**:
  - [ ] 11 loadable tools defined across 5 categories
  - [ ] Each entry has name, description, category, keywords (8+ per tool), and phases
  - [ ] Tool names match exactly the names from tool implementations (tasks 36-40)
  - [ ] Keywords cover both English and common search variations
  - [ ] Categories are logical groupings: `local_market`, `social_media`, `customer_analysis`, `image_generation`, `document_export`

#### Requirement 2 — Factory Function

- **Requirement**: Factory function that takes a list of all tool instances and core tool names, builds the ToolRegistry from the catalog, and returns a configured ToolSearchMiddleware. This is what task_46's agent factory calls.

- **Test Specification**:
  ```python
  # Test: Factory returns configured middleware
  # Input: all_tools=[...16 tools...], core_tool_names={"search_web", ...}
  # Expected: ToolSearchMiddleware instance with registry populated (11 loadable tools)

  # Test: Core tools not in registry
  # Input: core_tool_names includes "search_web"
  # Expected: "search_web" not in registry (only loadable tools in registry)

  # Test: Missing tool warning
  # Input: Catalog has "search_places" but all_tools doesn't include it
  # Expected: Warning logged, tool still in registry (will be available when added)
  ```

- **Implementation**:
  - `src/shared/src/shared/agent_middlewares/tool_search/middleware.py` (continued)
  ```python
  # ---- Core Tool Names for Brand Strategy ----
  # These tools are always visible to the model — no tool_search needed.
  # They are the fundamental research+planning tools used across ALL phases.
  BRAND_STRATEGY_CORE_TOOLS: set[str] = {
      "search_knowledge_graph",   # KG search — every phase
      "search_document_library",  # Doc library — every phase
      "search_web",               # Web search — most phases
      "scrape_web_content",                # Web crawling — used with search_web
      "deep_research",            # Multi-step research — Phase 1, 4
  }


  def create_tool_search_middleware(
      all_tools: list | None = None,
      core_tool_names: set[str] | None = None,
      tool_catalog: list[ToolMetadata] | None = None,
  ) -> ToolSearchMiddleware:
      """Build ToolRegistry from catalog and return configured middleware.

      Args:
          all_tools: All tool instances for validation. None skips validation.
          core_tool_names: Always-visible tools. Defaults to BRAND_STRATEGY_CORE_TOOLS.
          tool_catalog: Loadable tool metadata. Defaults to BRAND_STRATEGY_TOOL_CATALOG.

      Returns:
          Configured ToolSearchMiddleware for the middleware chain.
      """
      catalog = tool_catalog or BRAND_STRATEGY_TOOL_CATALOG
      core = core_tool_names or BRAND_STRATEGY_CORE_TOOLS

      # Build registry from catalog
      registry = ToolRegistry()
      registry.register_many(catalog)

      # Validate: check that catalog tool names exist in all_tools
      if all_tools is not None:
          actual_names = {
              getattr(t, "name", None) or getattr(t, "__name__", str(t))
              for t in all_tools
          }
          catalog_names = {meta.name for meta in catalog}
          missing = catalog_names - actual_names
          if missing:
              logger.warning(
                  f"ToolSearch catalog references tools not in all_tools: "
                  f"{missing}. These tools will appear in search results "
                  f"but won't be executable until registered."
              )

      logger.info(
          f"ToolSearchMiddleware initialized: "
          f"{len(core)} core tools always visible, "
          f"3 inventory tools (tool_search, load_tools, unload_tools), "
          f"{len(catalog)} loadable tools in {len(registry._categories)} categories"
      )

      return ToolSearchMiddleware(
          registry=registry,
          core_tool_names=core,
      )
  ```

- **Acceptance Criteria**:
  - [ ] Factory returns configured `ToolSearchMiddleware` with populated registry
  - [ ] Defaults to `BRAND_STRATEGY_TOOL_CATALOG` and `BRAND_STRATEGY_CORE_TOOLS` when not specified
  - [ ] Validates catalog against actual tool list (logs warnings for missing tools)
  - [ ] Logs initialization summary (count of core, loadable, categories)
  - [ ] `all_tools=None` skips validation (useful for testing without actual tool instances)

------------------------------------------------------------------------

## 🧪 Test Execution Log

> **Agent**: Record actual test results here as you run them.

### Test 1: ToolRegistry Search Accuracy

- **Purpose**: Verify search returns relevant tools for various query patterns
- **Steps**:
  1. Create ToolRegistry, register all 11 BRAND_STRATEGY_TOOL_CATALOG entries
  2. Search "generate image" → expect generate_image, generate_brand_key
  3. Search "social media" → expect browse_and_research, analyze_social_profile
  4. Search "document PDF report" → expect generate_document (+ category siblings)
  5. Search "blockchain" → expect empty list
  6. Search "" → expect empty list
- **Expected Result**: All queries return correct tools; scoring prioritizes exact matches
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 2: ToolSearchMiddleware — First Call Tool Filtering

- **Purpose**: Verify first model call sees only core tools + 3 meta tools, with catalog injected
- **Steps**:
  1. Create middleware with 5 core tools and 11 loadable tools
  2. Create mock ModelRequest with all 16+ tools, empty state
  3. Call wrap_model_call
  4. Verify handler called with filtered tools (5 core + tool_search + load_tools + unload_tools = 8)
  5. Verify system message includes "## Tool Warehouse" catalog with inventory workflow
- **Expected Result**: Only 8 tools visible (5 core + 3 meta), system message includes catalog + 4-step workflow
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 3: load_tools — Explicit Tool Loading

- **Purpose**: Verify load_tools adds tools to state and they become visible on next model call
- **Steps**:
  1. Set up middleware, call tool_search("generate image") first (read-only, no state change)
  2. Verify state["loaded_tools"] is still empty after tool_search
  3. Call wrap_tool_call with load_tools(["generate_image", "generate_brand_key"])
  4. Verify state["loaded_tools"] == {"generate_image", "generate_brand_key"}
  5. Call wrap_model_call again
  6. Verify generate_image and generate_brand_key now visible alongside core + meta tools
- **Expected Result**: Explicit load required — tool_search alone does NOT load. load_tools updates state correctly.
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 4: Bidirectional State — Load Then Unload

- **Purpose**: Verify unload_tools removes tools from state and they disappear from next model call
- **Steps**:
  1. Load tools: load_tools(["generate_image", "generate_brand_key"])
  2. Verify state["loaded_tools"] == {"generate_image", "generate_brand_key"}
  3. Unload tools: unload_tools(["generate_image"])
  4. Verify state["loaded_tools"] == {"generate_brand_key"}
  5. Call wrap_model_call — verify generate_image gone, generate_brand_key still visible
  6. Unload remaining: unload_tools(["generate_brand_key"])
  7. Verify state["loaded_tools"] == {} (empty, back to initial)
  8. Call wrap_model_call — verify only core + meta tools visible (same as initial)
- **Expected Result**: State is fully bidirectional — tools can be added AND removed. Empty state returns to initial tool set.
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 5: Factory Function with Default Catalog

- **Purpose**: Verify factory creates middleware with correct defaults
- **Steps**:
  1. Call `create_tool_search_middleware()` with no arguments
  2. Verify returned ToolSearchMiddleware has registry with 11 tools in 5 categories
  3. Verify core_tool_names is BRAND_STRATEGY_CORE_TOOLS
- **Expected Result**: Defaults applied correctly, middleware functional
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 6: Tool Catalog Completeness

- **Purpose**: Verify BRAND_STRATEGY_TOOL_CATALOG covers all loadable tools from blueprint
- **Steps**:
  1. Compare catalog tool names against blueprint Section 5.1 + 5.2 tools
  2. Verify core tools NOT in catalog (they don't need discovery)
  3. Verify all 11 loadable tools have entries with keywords and phases
- **Expected Result**: 11/11 loadable tools covered; 0 core tools in catalog
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 7: Integration — End-to-End Inventory Workflow

- **Purpose**: Verify complete flow: agent starts → searches → thinks → loads → uses → unloads
- **Steps**:
  1. Create agent with ToolSearchMiddleware using mock tools
  2. Send message requiring image generation
  3. Agent should call tool_search("generate image") (read-only browse)
  4. Agent reviews results, decides what to load
  5. Agent calls load_tools(["generate_image"]) (explicit equip)
  6. Agent calls generate_image (now visible and usable)
  7. Agent finishes image work, calls unload_tools(["generate_image"]) (unequip)
  8. Verify generate_image no longer visible on next model call
- **Expected Result**: Full search → load → use → unload cycle works. Agent has autonomy at each step.
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 8: unload_tools Edge Cases

- **Purpose**: Verify unload handles edge cases gracefully
- **Steps**:
  1. Unload a tool that was never loaded → "Not currently loaded: X"
  2. Unload a mix of loaded and not-loaded tools → correct split reporting
  3. Unload with empty list → "No tools specified."
  4. Load, unload, re-load same tool → state correctly tracks all transitions
- **Expected Result**: All edge cases handled without errors, with informative messages
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📊 Decision Log

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | Tool count: 1 vs 2 vs 3 tools | **A**: `tool_search` only (auto-load on search — Claude Code pattern) **B**: `tool_search` + `load_tools` (user's original 2-tool research) **C**: `tool_search` + `load_tools` + `unload_tools` (game inventory pattern) | **C**: 3-tool inventory pattern | Agent needs full autonomy: browse catalog (search), explicitly decide what to equip (load), and put items back when done (unload). Auto-load removes agent's ability to think before loading. Unload is critical for context management in long multi-phase conversations. User's exact metaphor: "giống như trong game, mở kho lên lấy đúng cái đó ra, dùng xong cất lại vào kho." |
| 2 | Loading granularity | **A**: Load exact matching tools only **B**: Load entire category when any tool matches | **A**: Individual tool loading by agent choice | Agent explicitly decides which tools to equip. Category auto-loading was removed because: (1) agent may not need all tools in a category, (2) defeats the purpose of agent autonomy, (3) unload becomes confusing if some tools were auto-loaded. Agent can always load more tools individually. |
| 3 | Search algorithm | **A**: Substring matching (user's doc) **B**: Multi-word scored matching **C**: Embedding-based | **B**: Multi-word scored matching | Exact substring misses partial matches. Embeddings overkill for 11 tools. Multi-word scoring balances accuracy and simplicity. Can upgrade to C later. |
| 4 | Catalog injection timing | **A**: Always inject catalog into system prompt **B**: Inject only on first call (flag in state) | **B**: First call only | Avoids repeated injection that wastes tokens. After first call, agent knows about tool_search. Catalog is redundant on subsequent calls. |
| 5 | State key for loaded tools | **A**: Custom state class **B**: Plain dict key in request.state | **B**: `request.state["loaded_tools"]` (set) | Simpler, compatible with all middleware chains. Set type prevents duplicates naturally. LangChain state is a plain dict. |
| 6 | Middleware ordering | **A**: ToolSearch before Skills **B**: ToolSearch after Skills | **A**: ToolSearch BEFORE SkillsMiddleware | Tool catalog injection should occur before skill descriptions in system prompt. Tool discovery is more fundamental than skill loading. |
| 7 | Unload capability | **A**: Accumulation-only (tools persist forever once loaded) **B**: Bidirectional state (load AND unload) | **B**: Bidirectional state | Long multi-phase conversations need context cleanup. Phase 1 tools (search_places, analyze_reviews) are useless in Phase 3-5. Without unload, loaded tools accumulate and re-bloat context — defeating the middleware's purpose. |
| 8 | State access from tool functions | **A**: Module-level `_registry` global only **B**: `ToolRuntime` for state + module-level for registry | **B**: ToolRuntime + module-level | `load_tools` and `unload_tools` need to read current loaded state for validation (already loaded? not loaded?). `ToolRuntime` is auto-injected by LangChain, invisible to LLM, and provides `runtime.state` access. Registry uses module-level because it's immutable config, not per-request state. |

------------------------------------------------------------------------

## 📝 Task Summary

> **Agent**: Complete this section AFTER the task is fully implemented and all tests pass.

### What Was Implemented

**Components Planned**:
- [ ] Component 1: ToolRegistry — Tool metadata storage with keyword-based search + `has_tool()` validation
- [ ] Component 2: 3 Inventory Tools — `tool_search` (browse), `load_tools` (equip), `unload_tools` (unequip)
- [ ] Component 3: ToolSearchMiddleware — LangChain middleware with wrap_model_call (filter) + wrap_tool_call (load/unload state)
- [ ] Component 4: Factory function + BRAND_STRATEGY_TOOL_CATALOG

**Files Created / Modified**:
```
src/shared/src/shared/agent_middlewares/tool_search/
├── __init__.py                          # Module exports (inventory pattern)
├── registry.py                          # ToolMetadata + ToolRegistry + has_tool()
└── middleware.py                        # ToolSearchMiddleware + 3 inventory tools
                                         #   (tool_search, load_tools, unload_tools)
                                         #   + BRAND_STRATEGY_TOOL_CATALOG
                                         #   + BRAND_STRATEGY_CORE_TOOLS
                                         #   + create_tool_search_middleware()
```

**Key Features Delivered**:
1. **3-tool inventory pattern**: tool_search (browse catalog) → load_tools (equip) → use → unload_tools (unequip)
2. **Agent autonomy**: Agent decides what to load/unload — no auto-loading from search
3. **Bidirectional state**: Tools can be loaded AND unloaded, keeping context lean across phases
4. **ToolRuntime integration**: load_tools/unload_tools use LangChain ToolRuntime for state validation (invisible to LLM)
5. **Category-aware search**: 5 categories × 11 tools with keyword scoring
6. **Zero-loss accessibility**: Every tool still accessible; loadable tools just need search + load steps first

### Technical Highlights

**Architecture Decisions** (see Decision Log for details):
- 3 inventory tools: tool_search (read-only), load_tools (equip), unload_tools (unequip)
- Individual tool loading by agent choice (not category auto-loading)
- Bidirectional state via `request.state["loaded_tools"]` (set)
- ToolRuntime for state access from within tool functions
- First-call catalog injection into system prompt with inventory workflow instructions

**Performance / Quality Results**:
- Context reduction: 18+ tools → 10 initial (44% fewer tool definitions in context)
  - 5 core research tools (always visible)
  - 3 inventory meta tools (tool_search, load_tools, unload_tools)
  - 2 other middleware tools (todo_write, task)
- Search latency: < 1ms (in-memory keyword matching over 11 tools)

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
- No new dependencies (uses LangChain AgentMiddleware + ToolRuntime already in project)
- No config changes or environment variables
- task_46 must be updated to use `create_tool_search_middleware()` in agent factory
- task_46 system prompt must describe 3-tool inventory workflow (not auto-load)
- Middleware ordering: `tool_search_middleware` → `skills_middleware` → `sub_agent_middleware` → other middlewares
