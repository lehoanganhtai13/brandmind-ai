# Task 41: Sub-Agent Infrastructure & Brand Strategy Sub-Agents

## 📌 Metadata

- **Epic**: Brand Strategy — Sub-Agents
- **Priority**: Medium-High (P2 — Market Research Agent, Creative Studio Agent; P3 — Social Media Analyst, Document Generator)
- **Estimated Effort**: 1.5 weeks
- **Team**: Backend
- **Related Tasks**: Task 36-40 (tools used by sub-agents), Task 35 (skills system)
- **Blocking**: Task 46 (E2E Integration — needs sub-agents for full workflow)
- **Blocked by**: Task 36 (search_places), Task 37 (deep_research), Task 38 (generate_image), Task 39 (Document Gen), Task 40 (Analysis Tools)

### ✅ Progress Checklist

- [x] 🎯 [Context &amp; Goals](#🎯-context--goals)
- [x] 🛠 [Solution Design](#🛠-solution-design)
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan)
- [x] 📋 [Implementation Detail](#📋-implementation-detail)
  - [x] ✅ [Component 1: Sub-Agent System Prompts](#component-1-sub-agent-system-prompts)
  - [x] ✅ [Component 2: Sub-Agent Configs &amp; Builder Function](#component-2-sub-agent-configs--builder-function)
  - [x] ✅ [Component 3: Market Research Agent](#component-3-market-research-agent)
  - [x] ✅ [Component 4: Social Media Analyst Agent](#component-4-social-media-analyst-agent)
  - [x] ✅ [Component 5: Creative Studio Agent](#component-5-creative-studio-agent)
  - [x] ✅ [Component 6: Document Generator Agent](#component-6-document-generator-agent)
- [x] ✅ 🧪 [Test Cases](#🧪-test-cases)
- [x] ✅ 📝 [Task Summary](#📝-task-summary)

## 🔗 Reference Documentation

- **Blueprint Reference**: `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — Section 6 (Sub-Agents & Delegation Strategy)
- **Existing SubAgent Pattern**: `src/core/src/core/knowledge_graph/cartographer/agent_config.py` — uses `deepagents.middleware.subagents.SubAgentMiddleware` (old single-agent API)
- **DeepAgents SubAgentMiddleware**: Supports `subagents` parameter — a list of named sub-agents with `{name, description, system_prompt, model, tools}`. Main agent gets `task()` tool and the LLM naturally selects which sub-agent to delegate to based on name/description.
- **Blueprint Delegation Matrix**: Section 6.6 — what to delegate vs keep in main agent (guidance in system prompt, NOT coded logic)

---

## 🎯 Context & Goals

### Bối cảnh

- Blueprint Section 6 định nghĩa 4 sub-agents: Market Research, Social Media Analyst, Creative Studio, Document Generator
- Main agent giữ strategic reasoning, mentor interaction, KG search — chỉ delegate data-heavy, repetitive, specialized tasks
- DeepAgents SubAgentMiddleware ĐÃ CÓ trong codebase — đang dùng cho cartographer agent (API cũ: single general-purpose sub-agent)
- **API mới (named sub-agents)**: `SubAgentMiddleware(subagents=[{name, description, system_prompt, model, tools}])` → mỗi sub-agent có tên riêng, description riêng → main agent LLM tự chọn sub-agent thông qua `task()` tool dựa trên name/description
- `model` field accepts `str` hoặc `BaseChatModel` instance → dùng `RetryChatGoogleGenerativeAI` (có retry 503/429) thay vì string, để config đúng params per model generation (Gemini 2.5: `thinking_budget`, `temperature=0.1`; Gemini 3: `thinking_level`, `temperature=1.0`)
- Mỗi sub-agent cần: own model instance (configured đúng per generation), own tools (subset of actual tool instances), own system prompt
- `SubAgent` TypedDict cũng hỗ trợ `middleware` field (optional) → có thể gắn `PatchToolCallsMiddleware`, `SummarizationMiddleware` per sub-agent
- **`task()` tool parameter**: Sub-agent được chọn qua `task(description="...", subagent_type="market-research")` — parameter tên là `subagent_type`, KHÔNG phải `agent`
- **`backend` parameter**: `SubAgentMiddleware(backend=...)` là **REQUIRED** khi dùng new API (truyền `subagents=`). Nếu không có `backend` và không có `default_model`, sẽ raise `ValueError`. Dùng factory pattern: `backend=lambda rt: StateBackend(rt)` để tạo `StateBackend` lazily khi `ToolRuntime` có sẵn.
- **KHÔNG cần** custom routing logic hay keyword matching — LLM tự quyết định delegate cho sub-agent nào

### Hiện trạng codebase

```python
# OLD pattern from cartographer/agent_config.py (single unnamed sub-agent):
subagent_middleware = SubAgentMiddleware(
    default_model=model,
    default_tools=[line_search_wrapper],
    default_middleware=[ctx_edit, summarization, todo, fs, patch, log, retry, stop],
    general_purpose_agent=True,
)

# NEW pattern — named sub-agents (what we'll use):
from deepagents.middleware.subagents import SubAgentMiddleware

subagent_middleware = SubAgentMiddleware(
    subagents=[
        {
            "name": "market-research",
            "description": "Research agent for competitor analysis, market mapping, trends",
            "system_prompt": MARKET_RESEARCH_SYSTEM_PROMPT,
            "model": "google_genai:gemini-2.5-flash-lite",
            "tools": [search_web, scrape_web_content, search_places, ...],
        },
        {
            "name": "social-media-analyst",
            "description": "Analyzes F&B brand social media presence",
            "system_prompt": SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT,
            "model": "google_genai:gemini-3-flash-preview",
            "tools": [browse_and_research, analyze_social_profile],
        },
        # ... more sub-agents
    ],
)
# → Main agent gets `task(description, subagent_type="market-research")` tool
# → LLM reads each sub-agent's name+description to decide which to use
```

### Mục tiêu

1. Builder function tạo `SubAgentMiddleware` với 4 named sub-agents cho brand strategy
2. Mỗi sub-agent có riêng: name, description, model instance (`RetryChatGoogleGenerativeAI`), tool set, system prompt
3. Model instances configured đúng per generation: Gemini 2.5 → `thinking_budget` + `temperature=0.1`; Gemini 3 → `thinking_level` + `temperature=1.0`
4. Main agent LLM tự quyết delegate thông qua `task()` tool — không cần custom routing logic
5. Prompts breakdown theo business function: `src/prompts/brand_strategy/subagents/{market_research,social_media,creative_studio,document_generator}.py`
6. `__init__.py` chỉ re-export, logic nằm trong `middleware.py` (clean module structure)
7. Integration seamless: task_46 import function, truyền `tools_registry` dict, nhận lại `SubAgentMiddleware`

### Success Metrics / Acceptance Criteria

- **Functionality**: Main agent có thể delegate tasks tới sub-agents thông qua `task` tool
- **Specialization**: Mỗi sub-agent chạy đúng model + đúng tools
- **Context efficiency**: Sub-agent giữ kết quả gọn, trả summary cho main agent
- **Error handling**: Sub-agent failure không crash main agent flow

---

## 🛠 Solution Design

### Giải pháp đề xuất

**Named Sub-Agents via SubAgentMiddleware**: Tạo `SubAgentMiddleware(subagents=[...])` với 4 named sub-agents. Main agent LLM tự chọn sub-agent nào qua `task()` tool dựa trên name/description — không cần custom routing, Factory class, hay DelegationDecision logic. Chỉ cần 1 builder function: `create_brand_strategy_subagent_middleware(tools_registry)` trả về configured `SubAgentMiddleware`.

### Architecture

```
Main Agent (Brand Manager)
    │
    ├── SubAgentMiddleware(subagents=[4 named agents]) → `task` tool
    │       │
    │       ├── LLM reads sub-agent names + descriptions
    │       └── LLM decides which to delegate via task(description, subagent_type="..."):
    │           ├── "market-research"    → search_web, scrape_web_content, search_places, ...
    │           ├── "social-media-analyst" → browse_and_research, analyze_social_profile
    │           ├── "creative-studio"    → generate_image, generate_brand_key
    │           └── "document-generator" → generate_document, generate_presentation, ...
    │
    └── (still has own tools: KG search, doc search, todo, etc.)
```

### Existing Components (Reuse)

| Component                | Location                                   | Reuse                     |
| ------------------------ | ------------------------------------------ | ------------------------- |
| SubAgentMiddleware       | `deepagents.middleware.subagents`        | Core sub-agent delegation |
| PatchToolCallsMiddleware | `deepagents.middleware.patch_tool_calls` | Fix tool call format      |
| SummarizationMiddleware  | `langchain.agents.middleware`            | Context management        |
| ContextEditingMiddleware | `langchain.agents.middleware`            | Context editing           |

### New Components

| Component         | Location                                                     | Purpose                                                             |
| ----------------- | ------------------------------------------------------------ | ------------------------------------------------------------------- |
| Builder function  | `src/core/src/core/brand_strategy/subagents/middleware.py` | `create_brand_strategy_subagent_middleware(tools_registry)`       |
| Re-exports        | `src/core/src/core/brand_strategy/subagents/__init__.py`   | Clean re-exports only                                               |
| Agent configs     | `src/core/src/core/brand_strategy/subagents/configs.py`    | Model instances (`RetryChatGoogleGenerativeAI`) + tool name lists |
| Sub-agent prompts | `src/prompts/brand_strategy/subagents/`                    | 4 prompt files — one per sub-agent business function               |

### Issues & Solutions

1. **Tool resolution** → Builder function receives `tools_registry: dict[str, BaseTool]` (name→tool mapping), resolves tool name strings to actual tool instances per sub-agent
2. **Tool dependencies across agents** → tools_registry built once in agent factory (task_46), shared across all sub-agents
3. **Sub-agent context overflow** → SubAgentMiddleware spawns ephemeral agents — context resets per task delegation
4. **Cost control** → Market Research + Document Generator use Flash Lite ($0.00); Creative Studio uses Flash Image (minimal cost); Social Media uses Flash 3 (for vision)

---

## 🔄 Implementation Plan

### **Phase 1: Sub-Agent System Prompts**

1. `src/prompts/brand_strategy/subagents/` — 4 prompt files, one per sub-agent business function
2. Mỗi prompt định nghĩa rõ role, specialties, output format, constraints
3. `__init__.py` re-exports all 4 prompt constants

### **Phase 2: Sub-Agent Configs**

1. `src/core/src/core/brand_strategy/subagents/configs.py` — model instances (`RetryChatGoogleGenerativeAI`) + tool name lists
2. `create_subagent_models()` function returns dict of configured model instances per agent type
3. Gemini 2.5 models: `thinking_budget=2000`, `temperature=0.1`; Gemini 3 models: `thinking_level="medium"`, `temperature=1.0`
4. Market Research Agent config (tools: search_web, scrape_web_content, search_places, deep_research, analyze_reviews, get_search_autocomplete)
5. Social Media Analyst config (tools: browse_and_research, analyze_social_profile)
6. Creative Studio config (tools: generate_image, generate_brand_key)
7. Document Generator config (tools: generate_document, generate_presentation, generate_spreadsheet, export_to_markdown)

### **Phase 3: Builder Function**

1. `create_brand_strategy_subagent_middleware(tools_registry)` in `subagents/middleware.py`
2. `subagents/__init__.py` re-exports only
3. Resolves tool names → actual tool instances from tools_registry
4. Creates model instances via `create_subagent_models()`
5. Returns `SubAgentMiddleware(subagents=[4 named sub-agent dicts])`

### **Phase 4: Integration & Testing**

1. Task 46 imports builder function, passes tools_registry, receives SubAgentMiddleware
2. Test: middleware has 4 sub-agents, tools resolved correctly

---

## 📋 Implementation Detail

> **📝 Coding Standards**: Enterprise-level Python, comprehensive docstrings, type hints.

### Component 1: Sub-Agent System Prompts

#### Requirement 1 - System Prompts Broken Down by Business Function

- **Requirement**: Sub-agent system prompts stored in `src/prompts/brand_strategy/subagents/` — one file per sub-agent business function (theo project convention: prompts luôn ở `src/prompts/`, breakdown theo chức năng để dễ quản lý)
- **Implementation**:

  - `src/prompts/brand_strategy/subagents/__init__.py` — re-exports all prompt constants

  ```python
  """Sub-agent system prompts for Brand Strategy.

  Each sub-agent has its own prompt file organized by business function.
  """

  from prompts.brand_strategy.subagents.market_research import (
      MARKET_RESEARCH_SYSTEM_PROMPT,
  )
  from prompts.brand_strategy.subagents.social_media import (
      SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT,
  )
  from prompts.brand_strategy.subagents.creative_studio import (
      CREATIVE_STUDIO_SYSTEM_PROMPT,
  )
  from prompts.brand_strategy.subagents.document_generator import (
      DOCUMENT_GENERATOR_SYSTEM_PROMPT,
  )

  __all__ = [
      "MARKET_RESEARCH_SYSTEM_PROMPT",
      "SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT",
      "CREATIVE_STUDIO_SYSTEM_PROMPT",
      "DOCUMENT_GENERATOR_SYSTEM_PROMPT",
  ]
  ```

  - `src/prompts/brand_strategy/subagents/market_research.py` — Market Research Agent prompt
  - `src/prompts/brand_strategy/subagents/social_media.py` — Social Media Analyst prompt
  - `src/prompts/brand_strategy/subagents/creative_studio.py` — Creative Studio Agent prompt
  - `src/prompts/brand_strategy/subagents/document_generator.py` — Document Generator Agent prompt

  *(Full prompt content defined in Components 3-6 below)*
- **Acceptance Criteria**:

  - [ ] 4 separate prompt files in `src/prompts/brand_strategy/subagents/` — one per business function
  - [ ] `__init__.py` cleanly re-exports all 4 prompt constants
  - [ ] Each prompt clearly defines role, specialties, output format, constraints
  - [ ] No prompts stored in `src/core/` (prompts belong in `src/prompts/`)

### Component 2: Sub-Agent Configs & Builder Function

#### Requirement 1 - Agent Configs (Model Instances + Tool Names)

- **Requirement**: Per-agent-type configs storing model instances (`RetryChatGoogleGenerativeAI`) with correct params per generation, and tool name lists. String-based model names (`"provider:model_name"`) không đủ vì mỗi model generation cần config khác — Gemini 2.5 dùng `thinking_budget` + `temperature=0.1`, Gemini 3 dùng `thinking_level` + `temperature=1.0`.
- **Implementation**:

  - `src/core/src/core/brand_strategy/subagents/configs.py`

  ```python
  """Configuration for Brand Strategy sub-agents.

  Defines model instances and tool assignments per sub-agent type.
  Uses RetryChatGoogleGenerativeAI (with built-in 503/429 retry) instead of
  string model names, because each model generation requires different configs:
  - Gemini 2.5 models: thinking_budget (int), temperature=0.1
  - Gemini 3 models: thinking_level (str), temperature=1.0

  System prompts are imported from src/prompts/brand_strategy/subagents/.
  """

  from config.system_config import SETTINGS
  from shared.agent_models import RetryChatGoogleGenerativeAI

  # Tool name lists per sub-agent (resolved to actual tools at build time)
  MARKET_RESEARCH_TOOLS = [
      "search_web", "scrape_web_content", "search_places",
      "get_search_autocomplete", "deep_research",
      "analyze_reviews",
  ]

  SOCIAL_MEDIA_TOOLS = [
      "browse_and_research", "analyze_social_profile",
  ]

  CREATIVE_STUDIO_TOOLS = [
      "generate_image", "generate_brand_key",
  ]

  DOCUMENT_GENERATOR_TOOLS = [
      "generate_document", "generate_presentation",
      "generate_spreadsheet", "export_to_markdown",
  ]


  def create_subagent_models() -> dict[str, RetryChatGoogleGenerativeAI]:
      """Create model instances for each sub-agent type.

      Returns:
          Dict mapping sub-agent name → configured model instance.
      """
      return {
          # Market Research: Gemini 2.5 Flash Lite — cheap, fast, good at data gathering
          "market-research": RetryChatGoogleGenerativeAI(
              google_api_key=SETTINGS.GEMINI_API_KEY,
              model="gemini-2.5-flash-lite",
              temperature=0.1,
              thinking_budget=2000,
              max_output_tokens=8000,
              include_thoughts=False,     # Sub-agents don't need to expose thinking
          ),
          # Social Media Analyst: Gemini 3 Flash — vision capable for social images
          "social-media-analyst": RetryChatGoogleGenerativeAI(
              google_api_key=SETTINGS.GEMINI_API_KEY,
              model="gemini-3-flash-preview",
              temperature=1.0,
              thinking_level="medium",
              max_output_tokens=8000,
              include_thoughts=False,
          ),
          # Creative Studio: Gemini 2.5 Flash Lite — cheap, crafts image prompts + orchestrates tools
          "creative-studio": RetryChatGoogleGenerativeAI(
              google_api_key=SETTINGS.GEMINI_API_KEY,
              model="gemini-2.5-flash-lite",
              temperature=0.1,
              thinking_budget=2000,
              max_output_tokens=5000,
              include_thoughts=False,
          ),
          # Document Generator: Gemini 2.5 Flash Lite — cheap, structured output
          "document-generator": RetryChatGoogleGenerativeAI(
              google_api_key=SETTINGS.GEMINI_API_KEY,
              model="gemini-2.5-flash-lite",
              temperature=0.1,
              thinking_budget=2000,
              max_output_tokens=10000,    # Longer for document generation
              include_thoughts=False,
          ),
      }
  ```

#### Requirement 2 - Builder Function

- **Requirement**: Single function that builds `SubAgentMiddleware` with 4 named sub-agents. Called by task_46's agent factory with a `tools_registry` dict. Logic lives in `middleware.py`, `__init__.py` only re-exports.
- **Implementation**:

  - `src/core/src/core/brand_strategy/subagents/__init__.py` — **re-exports only**

  ```python
  """Brand Strategy Sub-Agent Infrastructure.

  Re-exports the builder function for creating SubAgentMiddleware
  with 4 named brand strategy sub-agents.
  """

  from core.brand_strategy.subagents.middleware import (
      create_brand_strategy_subagent_middleware,
  )

  __all__ = ["create_brand_strategy_subagent_middleware"]
  ```

  - `src/core/src/core/brand_strategy/subagents/middleware.py` — **actual builder logic**

  ```python
  """Builder function for Brand Strategy SubAgentMiddleware.

  Creates a SubAgentMiddleware with 4 named sub-agents for brand strategy.
  Each sub-agent has its own model instance, tool set, and system prompt.
  """

  from loguru import logger
  from langchain_core.tools import BaseTool
  from deepagents.middleware.subagents import SubAgentMiddleware
  from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware

  from prompts.brand_strategy.subagents import (
      MARKET_RESEARCH_SYSTEM_PROMPT,
      SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT,
      CREATIVE_STUDIO_SYSTEM_PROMPT,
      DOCUMENT_GENERATOR_SYSTEM_PROMPT,
  )
  from .configs import (
      MARKET_RESEARCH_TOOLS,
      SOCIAL_MEDIA_TOOLS,
      CREATIVE_STUDIO_TOOLS,
      DOCUMENT_GENERATOR_TOOLS,
      create_subagent_models,
  )

  # Each sub-agent gets PatchToolCallsMiddleware to fix Gemini tool call
  # format issues. SummarizationMiddleware is NOT needed since sub-agents
  # are ephemeral (context resets per task delegation).
  _SUBAGENT_MIDDLEWARE = [PatchToolCallsMiddleware()]


  def _resolve_tools(
      tool_names: list[str],
      tools_registry: dict[str, BaseTool],
  ) -> list[BaseTool]:
      """Resolve tool name strings to actual tool instances.

      Args:
          tool_names: List of tool names (e.g. ["search_web", "scrape_web_content"])
          tools_registry: Mapping of tool name → tool instance

      Returns:
          List of resolved tool instances (skips missing tools with warning)
      """
      resolved = []
      for name in tool_names:
          if name in tools_registry:
              resolved.append(tools_registry[name])
          else:
              logger.warning(f"Tool '{name}' not found in registry, skipping")
      return resolved


  def create_brand_strategy_subagent_middleware(
      tools_registry: dict[str, BaseTool],
  ) -> SubAgentMiddleware:
      """Create SubAgentMiddleware with 4 named brand strategy sub-agents.

      Each sub-agent has its own name, description, system prompt, model
      instance (RetryChatGoogleGenerativeAI), and tool set. The main
      agent LLM naturally selects which sub-agent to delegate to via
      the task() tool based on name/description.

      Args:
          tools_registry: Mapping of tool name → tool instance.
              Built in the agent factory (task_46) as:
              {tool.name: tool for tool in all_tools}

      Returns:
          Configured SubAgentMiddleware ready for agent middleware stack.

      Usage (in agent factory — task_46):
          tools_registry = {tool.name: tool for tool in tools}
          sub_agent_mw = create_brand_strategy_subagent_middleware(tools_registry)
      """
      models = create_subagent_models()

      subagents = [
          {
              "name": "market-research",
              "description": (
                  "Research agent for competitor analysis, local market mapping "
                  "via search_places, deep market research, review sentiment "
                  "analysis, and search trend discovery. Use for data-heavy "
                  "research tasks requiring multiple tool calls."
              ),
              "system_prompt": MARKET_RESEARCH_SYSTEM_PROMPT,
              "model": models["market-research"],
              "tools": _resolve_tools(MARKET_RESEARCH_TOOLS, tools_registry),
              "middleware": _SUBAGENT_MIDDLEWARE,
          },
          {
              "name": "social-media-analyst",
              "description": (
                  "Analyzes F&B brand social media presence on Instagram, "
                  "Facebook, TikTok. Performs profile analysis, content audits, "
                  "brand voice assessment, and competitive social benchmarking."
              ),
              "system_prompt": SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT,
              "model": models["social-media-analyst"],
              "tools": _resolve_tools(SOCIAL_MEDIA_TOOLS, tools_registry),
              "middleware": _SUBAGENT_MIDDLEWARE,
          },
          {
              "name": "creative-studio",
              "description": (
                  "Generates brand visual assets — mood boards, logo concept "
                  "directions, color palette visualizations, packaging mockups, "
                  "and Brand Key one-pager visuals. Images are direction drafts."
              ),
              "system_prompt": CREATIVE_STUDIO_SYSTEM_PROMPT,
              "model": models["creative-studio"],
              "tools": _resolve_tools(CREATIVE_STUDIO_TOOLS, tools_registry),
              "middleware": _SUBAGENT_MIDDLEWARE,
          },
          {
              "name": "document-generator",
              "description": (
                  "Compiles brand strategy data into professional deliverables: "
                  "PDF/DOCX strategy documents, PPTX pitch decks, XLSX spreadsheets, "
                  "Markdown exports, and Brand Key one-pager compilation."
              ),
              "system_prompt": DOCUMENT_GENERATOR_SYSTEM_PROMPT,
              "model": models["document-generator"],
              "tools": _resolve_tools(DOCUMENT_GENERATOR_TOOLS, tools_registry),
              "middleware": _SUBAGENT_MIDDLEWARE,
          },
      ]

      # BackendFactory: StateBackend for ephemeral sub-agent state.
      # The factory receives ToolRuntime at agent build time.
      # The task() tool parameter for selecting a sub-agent is
      # `subagent_type` (e.g., task(description="...", subagent_type="market-research"))
      def _backend_factory(runtime: ToolRuntime) -> StateBackend:
          return StateBackend(runtime)

      return SubAgentMiddleware(
          backend=_backend_factory,
          subagents=subagents,
      )
  ```
- **Acceptance Criteria**:

  - [ ] Returns `SubAgentMiddleware` with exactly 4 named sub-agents
  - [ ] Each sub-agent has correct: name, description, system_prompt, model (RetryChatGoogleGenerativeAI instance), tools, middleware
  - [ ] Model instances use correct params: Gemini 2.5 → `thinking_budget` + `temperature=0.1`; Gemini 3 → `thinking_level` + `temperature=1.0`
  - [ ] Model names follow convention: `gemini-2.5-flash-lite` (stable, no suffix), `gemini-3-flash-preview` (preview)
  - [ ] Each sub-agent has `PatchToolCallsMiddleware` in `middleware` list
  - [ ] Tool resolution handles missing tools gracefully (warning, not crash)
  - [ ] `task()` tool uses `subagent_type` parameter (NOT `agent`)
  - [ ] No custom routing/keyword matching — LLM decides naturally
  - [ ] `__init__.py` only re-exports; logic in `middleware.py`

### Component 3: Market Research Agent

#### Requirement 1 - Market Research Agent Prompt

- **Requirement**: Sub-agent specialized in data gathering and analysis (Blueprint Section 6.2)
- **Implementation**:

  - `src/prompts/brand_strategy/subagents/market_research.py`
  - Tools configured in `src/core/src/core/brand_strategy/subagents/configs.py` → `MARKET_RESEARCH_TOOLS`

  ```python
  MARKET_RESEARCH_SYSTEM_PROMPT = """# ROLE & OBJECTIVE
You are **The Market Research Agent**, a data-gathering specialist for BrandMind AI's F&B brand strategy workflow.
Your mission is to collect, organize, and return comprehensive market data as instructed by the main Brand Manager agent.

**CORE PRINCIPLE: DATA, NOT STRATEGY**
You are the researcher — the main agent is the strategist. Your job ends at presenting well-structured findings. You may highlight patterns you observe (e.g., "4 of 6 competitors price below 60k VND"), but you do NOT recommend what the brand should do about it.

# YOUR TOOLBOX
1. `search_places` — **The Scout.** Discovers local businesses by location. Returns ratings, review counts, addresses, categories. *Start here* for any location-based competitive mapping.
2. `search_web` — **The Researcher.** General market info, industry reports, news, brand background. Use for market sizing, trends, regulations, or any topic not tied to a physical location.
3. `scrape_web_content` — **The Deep-Diver.** Extracts content from a specific URL. Use *after* search_places or search_web surfaces interesting URLs — menus, pricing pages, about pages, job postings (growth signals).
4. `deep_research` — **The Synthesizer.** Multi-step research pipeline on a complex topic. Use when you need 5+ searches synthesized into a coherent analysis (category trends, consumer behavior shifts, market reports).
5. `analyze_reviews` — **The Listener.** Extracts sentiment themes from customer reviews. Surfaces what customers praise, complain about, and wish for.
6. `get_search_autocomplete` — **The Demand Sensor.** Shows what people actually search for. Reveals consumer language, demand signals, and trending queries in a category.

## Tool Chaining
Tools work best in combination. A natural flow for competitor research:
`search_places` (discover) → `scrape_web_content` (deep-dive top results) → `analyze_reviews` (customer perception)

But not every task needs every tool. Match tools to the task — a trend research task may only need `deep_research` + `search_web`. Use judgment.

# DATA COLLECTION GUIDELINES
These are *lenses*, not rigid checklists. Adapt to what's actually available and relevant.

**When profiling competitors**, useful data points include:
- Identity: name, location, concept, positioning cues
- Performance: rating, review volume, price range, foot traffic signals
- Differentiation: menu highlights, unique selling points, ambiance/experience
- Digital presence: website quality, social links, online ordering
- Customer voice: most-praised aspects, recurring complaints, unmet wishes

**When mapping markets/trends:**
- Scale: market size indicators, growth trajectory, key players
- Demand: consumer search patterns, unmet needs, spending behavior
- Dynamics: emerging formats, declining ones, regulatory landscape

**When researching audiences:**
- Observed demographics: age groups, visit occasions, spending patterns
- Behavioral signals: search queries, review language, content engagement
- Psychographic hints: values, lifestyle cues, community affiliations

Some data will be unavailable — note the gap explicitly and move on. Do not fabricate or assume.

# OUTPUT CONTRACT
* **Structure:** Use headers, tables, and bullet points. Group by entity (per competitor) or by theme (per trend) — whichever fits.
* **Sources:** Cite origin (URL, platform, search query) for every data point.
* **Gaps:** Call out missing data explicitly: *"Price data not publicly available for X."*
* **Length:** Comprehensive but concise. Target <2000 words. Prefer tables over prose for comparative data.
* **Boundary:** Findings and observed patterns only. No strategic recommendations.
  """
  ```
- **When to Delegate** (from Blueprint Section 6.2):

  - Competitor deep-dive analysis (multiple businesses)
  - Local market mapping with search_places
  - Trend research requiring multiple web searches
- **Acceptance Criteria**:

  - [ ] Handles multi-business competitor analysis
  - [ ] Returns structured data with sources
  - [ ] Stays within data gathering scope (no strategy)

### Component 4: Social Media Analyst Agent

#### Requirement 1 - Social Media Analyst Prompt

- **Requirement**: Sub-agent for browser-based social media research (Blueprint Section 6.3)
- **Implementation**:

  - `src/prompts/brand_strategy/subagents/social_media.py`
  - Tools configured in `src/core/src/core/brand_strategy/subagents/configs.py` → `SOCIAL_MEDIA_TOOLS`

  ```python
  SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT = """# ROLE & OBJECTIVE
You are **The Social Media Analyst**, a browser-based social intelligence agent for BrandMind AI.
Your mission is to observe, analyze, and report on F&B brand social media presence — what they're doing, how they're doing it, and what signals their activity reveals.

**CORE PRINCIPLE: OBSERVE & REPORT**
You are the eyes — the main agent is the strategist. Describe what you see with specificity. Note patterns. The main agent decides what it means for the brand strategy.

# YOUR TOOLBOX
1. `browse_and_research` — **The Observer.** Navigates any web page or social profile autonomously. Provide a task description like "Visit instagram.com/brand_name and analyze their recent 12 posts, bio, and visual grid". The tool handles browser automation, anti-detection, and data extraction. Use this to *look* at what a brand is doing on social.
2. `analyze_social_profile` — **The Auditor.** Returns a structured profile-level analysis (content themes, posting patterns, engagement metrics). Use this for a systematic overview.

For multi-profile tasks: analyze each profile individually first, then deliver a cross-comparison at the end.

# OBSERVATION LENSES
These are *what to notice*, not mandatory checklists. Focus on what's actually observable and noteworthy for each profile.

**Profile Signals:**
- Bio copy: how does the brand describe itself? Keywords, CTA, link destination.
- Visual grid (IG): color consistency, photo style, content variety visible at a glance.
- Follower scale and ratio as rough credibility/growth signals.

**Content Strategy Signals:**
- Content pillars: what recurring themes appear? (product shots, lifestyle, behind-the-scenes, UGC, promos, educational)
- Format mix: photos vs reels/videos vs carousels vs stories.
- Posting rhythm: frequency, consistency, any notable gaps.
- Caption voice: tone (casual/professional/playful), length, hashtag strategy.

**Engagement Signals:**
- Quality over quantity — are comments genuine conversations or generic emojis?
- Which content types drive the strongest response?
- Brand responsiveness: do they reply? What tone? How fast?

**Positioning Signals** (read between the lines):
- Price tier cues: product styling, photography quality, venue aesthetics.
- Audience cues: who appears in photos, what language tone is used, what lifestyle is portrayed.
- Differentiation: what does this brand emphasize that others in the same category don't?

**Platform-Specific Awareness:**
- **Instagram:** Grid aesthetic coherence. Check the recent 9-12 posts as a "storefront." Reels strategy.
- **Facebook:** Community engagement (comments, shares), page reviews, events, group presence.
- **TikTok:** Trend participation speed, production level, virality signals, audio/trend usage.

# OUTPUT CONTRACT
* **Per-profile sections** with a consistent structure so profiles are easily comparable.
* **Specificity:** Name actual content examples you observed ("their Jan 15 reel featuring latte art got 2.3K likes"). Vague summaries are low-value.
* **Cross-comparison** (when multiple profiles): what's shared across all? Where do they meaningfully diverge?
* **Candid gaps:** If a profile is private, barely active, or lacks sufficient data, say so directly. Do not pad thin data.
* **Boundary:** Observations and patterns only. No strategic recommendations.
  """
  ```
- **When to Delegate** (from Blueprint Section 6.3):

  - Analyzing competitor social media profiles
  - Mining customer conversations on social platforms
  - Gathering social trend data
- **Acceptance Criteria**:

  - [ ] Browses social profiles via browse_and_research
  - [ ] Returns structured brand assessment
  - [ ] Handles multiple profile analysis in one task

### Component 5: Creative Studio Agent

#### Requirement 1 - Creative Studio Agent Prompt

- **Requirement**: Sub-agent for batch image generation (Blueprint Section 6.4)
- **Implementation**:

  - `src/prompts/brand_strategy/subagents/creative_studio.py`
  - Tools configured in `src/core/src/core/brand_strategy/subagents/configs.py` → `CREATIVE_STUDIO_TOOLS`

  ```python
  CREATIVE_STUDIO_SYSTEM_PROMPT = """# ROLE & OBJECTIVE
You are **The Creative Studio**, a visual asset generator for BrandMind AI.
Your mission is to translate brand direction briefs into AI-generated visual assets that communicate the intended brand feel, style, and personality.

**CORE PRINCIPLE: TRANSLATE, DON'T INVENT**
The main agent provides the creative direction (positioning, personality, color sense, mood). You bring it to life visually. Stay faithful to the brief — add creative richness, but don't override the strategic intent.

# YOUR TOOLBOX
1. `generate_image` — **The Canvas.** Creates images from text prompts. Output quality depends directly on prompt quality. This is your primary tool.
2. `generate_brand_key` — **The Compiler.** Generates a Brand Key one-pager visual from structured brand data. Use when the task specifically requests a Brand Key.

# PROMPT CRAFTING
The gap between a mediocre and excellent output is almost entirely in the prompt. Write image prompts that specify:
- **Subject:** What's in the image — be concrete ("a specialty coffee cup on a marble counter" not "coffee").
- **Style:** Art direction — photography style, illustration technique, design movement ("editorial food photography with natural lighting" or "minimalist flat vector illustration").
- **Mood:** The emotional tone ("warm and inviting", "bold and energetic", "serene and premium").
- **Color:** Key palette cues when relevant ("earth tones with terracotta accents", "monochrome with gold details").
- **Composition:** Framing, perspective, spatial arrangement when it matters.

*Bad prompt:* "a nice café logo"
*Good prompt:* "Minimalist wordmark logo concept for a Vietnamese specialty coffee brand, clean geometric sans-serif, warm earth-tone palette with a terracotta accent, modern yet approachable, displayed on a textured paper background"

# ASSET TYPE THINKING

**Mood boards** — Capture the brand's *desired world*. Think: if this brand were a place and a moment, what would you see and feel? Generate images across facets: venue atmosphere, product styling, customer lifestyle, texture/material feel.

**Logo concept directions** — These are *directional*, not final logos. Show contrasting stylistic paths (e.g., minimalist vs. organic vs. bold typographic). Focus on communicating personality and feel, not pixel precision.

**Color palette visualizations** — Colors in *context*, not swatches. Show how the palette feels applied to real surfaces — a painted wall, a printed menu, packaging, a storefront. Context reveals whether colors actually work.

**Packaging/interior concepts** — The brand applied to physical F&B touchpoints: cups, bags, menu boards, storefront signage, table settings, uniform details. Make it tangible.

**Brand Key visual** — Use `generate_brand_key` with the structured data from the main agent's brief.

# CRITICAL FRAMING
All generated images are **DIRECTION DRAFTS**. They show creative direction, not production-ready assets. A professional designer uses these as starting references. State this in your output.

# OUTPUT CONTRACT
For each generated image, return:
1. File path (from `generate_image`)
2. What it represents and how it connects to the brand direction (1-2 sentences)

At the end: a brief synthesis of how the full set of visuals works together to express the brand.
  """
  ```
- **When to Delegate** (from Blueprint Section 6.4):

  - Generating mood boards (multiple images)
  - Creating logo concept variations
  - Color palette visualization
  - Brand Key visual generation
- **Acceptance Criteria**:

  - [ ] Generates batch images matching brand direction
  - [ ] Returns file paths + descriptions
  - [ ] Handles 4+ images in single task

### Component 6: Document Generator Agent

#### Requirement 1 - Document Generator Agent Prompt

- **Requirement**: Sub-agent for deliverable assembly (Blueprint Section 6.5)
- **Implementation**:

  - `src/prompts/brand_strategy/subagents/document_generator.py`
  - Tools configured in `src/core/src/core/brand_strategy/subagents/configs.py` → `DOCUMENT_GENERATOR_TOOLS`

  ```python
  DOCUMENT_GENERATOR_SYSTEM_PROMPT = """# ROLE & OBJECTIVE
You are **The Document Generator**, a professional deliverable assembler for BrandMind AI.
Your mission is to compile brand strategy data into polished, well-structured PDF, DOCX, PPTX, or Markdown documents.

**CORE PRINCIPLE: SHAPE, DON'T REWRITE**
The main agent provides the strategic content — positioning statements, competitor data, identity decisions, metric targets. Your job is to *structure and present* this content professionally. Preserve specifics faithfully. Add narrative flow and visual hierarchy, not new strategic ideas.

# YOUR TOOLBOX
1. `generate_document` — **The Report Builder.** Creates PDF or DOCX. Use for comprehensive strategy documents, brand guidelines, detailed reports.
2. `generate_presentation` — **The Deck Builder.** Creates PPTX. Use for executive presentations, pitch decks, stakeholder summaries.
3. `export_to_markdown` — **The Quick Exporter.** Clean markdown output. Use for shareable text formats, wiki/notion exports, lightweight reference docs.

When the task doesn't specify format: PDF for formal deliverables, PPTX for presentations, Markdown for quick/shareable outputs.

# ASSEMBLY THINKING
A good deliverable *tells a story* — it flows from context → insight → action. Don't dump sections sequentially; connect them with narrative purpose.

**Strategy document flow** (adapt as needed):
1. Executive summary — the punchline first, so a busy stakeholder gets the core in 1 page
2. Business context & challenge — why we're here
3. Market landscape — what the world looks like (competition, trends, audience)
4. Strategic positioning — where we play and how we win
5. Brand identity — personality, visual system, verbal system
6. Communication framework — messaging hierarchy, channel strategy
7. Implementation roadmap — what to do, when, at what investment
8. Measurement framework — how we'll know it's working

**Pitch deck flow:**
- One key idea per slide. Build the argument: situation → insight → strategy → action.
- Fewer words, more impact. If a slide needs a paragraph, it's two slides.

These are *patterns*. Adapt section count, ordering, and emphasis to match what's actually provided. If the input only covers positioning + identity, build those sections beautifully — don't invent market research you don't have.

# CONTENT QUALITY
* **Preserve specifics.** If the main agent provides exact positioning statements, verbatim customer quotes, or precise metric targets — use them as-is. Don't paraphrase away the precision.
* **Handle gaps honestly.** If expected data is missing, include the section header with a clear placeholder: *"[Pending: competitive analysis data]"*. Never silently skip sections.
* **Professional tone.** Clean, confident, consultant-quality prose. No filler, no hedging words ("perhaps", "might", "it seems"). Write like a strategy document from a top-tier firm.
* **Scannable layout.** Headings, subheadings, bullet points, tables. Wall-of-text is never acceptable. The reader should be able to skim-read and still grasp the strategy.

# OUTPUT CONTRACT
* File path to the generated document.
* Brief table of contents or slide list (what was included).
* Any sections that used placeholder data or were incomplete.
* Total page count (document) or slide count (deck).
  """
  ```
- **When to Delegate** (from Blueprint Section 6.5):

  - Generating the final brand strategy PDF/DOCX
  - Creating the pitch deck presentation
  - Compiling the Brand Key one-pager
- **Acceptance Criteria**:

  - [ ] Compiles all phase outputs into professional document
  - [ ] Creates pitch deck with correct slide count
  - [ ] Reports missing data gracefully

---

## 🧪 Test Cases

### Test Case 1: Market Research Delegation

- **Purpose**: Verify competitor research delegates to Market Research Agent
- **Steps**:
  1. Main agent receives: "Research top 5 specialty coffee competitors in District 1"
  2. Should delegate to Market Research Agent
  3. Agent runs search_places + scrape_web_content + analyze_reviews
  4. Returns structured competitor analysis
- **Expected Result**: 5 competitor profiles with ratings, reviews, locations
- **Status**: ⏳ Pending

### Test Case 2: Creative Studio Delegation

- **Purpose**: Verify batch image generation delegates to Creative Studio
- **Steps**:
  1. Main agent receives: "Generate 4 mood board images for a modern café brand"
  2. Should delegate to Creative Studio Agent
  3. Agent generates 4 images
  4. Returns file paths + descriptions
- **Expected Result**: 4 images generated, paths returned
- **Status**: ⏳ Pending

### Test Case 3: SubAgentMiddleware Has 4 Named Sub-Agents

- **Purpose**: Verify middleware is configured with exactly 4 named sub-agents
- **Steps**:
  1. Call `create_brand_strategy_subagent_middleware(tools_registry)`
  2. Inspect returned SubAgentMiddleware's subagents list
  3. Verify names: "market-research", "social-media-analyst", "creative-studio", "document-generator"
  4. Verify each has: name, description, system_prompt, model, tools
- **Expected Result**: 4 sub-agents with correct configs
- **Status**: ⏳ Pending

### Test Case 4: Tool Resolution Per Sub-Agent

- **Purpose**: Verify tools_registry resolves tool names correctly
- **Steps**:
  1. Build tools_registry with known tools
  2. Call builder function → inspect each sub-agent's tools list
  3. Market Research should have 6 tools, Social Media 2, Creative Studio 2, Document Generator 4
  4. Test with missing tool → should warn but not crash
- **Expected Result**: Correct tool count per sub-agent, graceful missing tool handling
- **Status**: ⏳ Pending

---

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation.

### What Was Implemented

**Components Completed**:

- [x] ✅ [Component 1]: Sub-Agent System Prompts (4 files in `src/prompts/brand_strategy/subagents/`)
- [x] ✅ [Component 2]: Sub-Agent Configs & Builder Function (`configs.py` + `middleware.py`)
- [x] ✅ [Component 3]: Market Research Agent prompt
- [x] ✅ [Component 4]: Social Media Analyst Agent prompt
- [x] ✅ [Component 5]: Creative Studio Agent prompt
- [x] ✅ [Component 6]: Document Generator Agent prompt

**Files Created/Modified**:

```
src/core/src/core/brand_strategy/
├── __init__.py
└── subagents/
    ├── __init__.py                # Re-exports only
    ├── middleware.py              # create_brand_strategy_subagent_middleware()
    └── configs.py                 # Model instances (RetryChatGoogleGenerativeAI) + tool name lists

src/prompts/brand_strategy/
├── __init__.py
└── subagents/
    ├── __init__.py                # Re-exports all 4 prompt constants
    ├── market_research.py         # MARKET_RESEARCH_SYSTEM_PROMPT
    ├── social_media.py            # SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT
    ├── creative_studio.py         # CREATIVE_STUDIO_SYSTEM_PROMPT
    └── document_generator.py      # DOCUMENT_GENERATOR_SYSTEM_PROMPT
```

### Bug Fixes Found During Testing

1. **`crawl_web` → `scrape_web_content`**: The actual tool name registered in `agent_tools.crawler.crawl_web` module is `scrape_web_content`, not `crawl_web`. Fixed in `configs.py` `MARKET_RESEARCH_TOOLS`.

2. **`SubAgentMiddleware` requires `backend` parameter**: The new API (passing `subagents=`) requires `backend` to be non-None. Without it: `ValueError: SubAgentMiddleware requires either 'backend' (new API) or 'default_model' (deprecated API)`. Fixed by using a factory pattern: `backend=lambda rt: StateBackend(rt)`.

3. **`StateBackend` requires `ToolRuntime` argument**: `StateBackend()` cannot be instantiated without a `ToolRuntime` instance. Must use a factory callable that receives `ToolRuntime` at agent build time.

---
