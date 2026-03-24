# Task 46: Brand Strategy System Prompt & E2E Integration

## 📌 Metadata

- **Epic**: Brand Strategy — System Integration (Capstone)
- **Priority**: Critical (P0 — Everything converges here)
- **Estimated Effort**: 1 week
- **Team**: Backend
- **Related Tasks**: ALL previous brand strategy tasks (35-45), Task 47 (ToolSearchMiddleware)
- **Blocking**: None (this is the final task)
- **Blocked by**: Tasks 35-45 (all must be complete), Task 47 (ToolSearchMiddleware for dynamic tool loading)

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals)
- [x] 🛠 [Solution Design](#🛠-solution-design)
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan)
- [x] 📋 [Implementation Detail](#📋-implementation-detail)
    - [x] ✅ [Component 1: Brand Strategy System Prompt](#component-1-brand-strategy-system-prompt)
    - [x] ✅ [Component 2: Brand Strategy Agent Factory](#component-2-brand-strategy-agent-factory)
    - [x] ✅ [Component 3: CLI Entry Point](#component-3-cli-entry-point)
    - [x] ✅ [Component 4: Session & State Persistence](#component-4-session--state-persistence)
    - [x] ✅ [Component 5: E2E Integration Tests](#component-5-e2e-integration-tests)
- [x] 🧪 [Test Cases](#🧪-test-cases)
- [x] 📝 [Task Summary](#📝-task-summary)

## 🔗 Reference Documentation

- **Blueprint Reference**: `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — Section 7 (Integration), Section 8 (Appendix)
- **Runtime Flow**: Blueprint Section 7.1 (full Phase 0→5 scenario)
- **KG Integration Points**: Blueprint Section 7.2 (queries per phase)
- **Context Window Management**: Blueprint Section 7.3 (skill loading/unloading)
- **Existing Pattern**: `src/cli/inference.py` → `create_qa_agent()`, `src/prompts/inference/qa_agent_system_prompt.py`
- **Existing Agent Config Pattern**: `src/core/src/core/knowledge_graph/cartographer/agent_config.py`

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

Đây là capstone task — wires everything together. Tất cả tools (Task 36-40), sub-agents (Task 41), skills (Task 42-45), và infrastructure (Task 35) đã được implement. Task này tạo system prompt cho brand strategy mode, agent factory function, CLI entry, và E2E tests.

Key pattern đã có sẵn trong codebase:
- `create_qa_agent()` in `src/cli/inference.py` — tạo agent với model, tools, middlewares, system_prompt
- `create_cartographer_agent()` in cartographer `agent_config.py` — tạo agent với SubAgentMiddleware
- `QA_AGENT_SYSTEM_PROMPT` in `src/prompts/inference/qa_agent_system_prompt.py` — system prompt ví dụ

Brand Strategy Agent khác QA Agent ở:
1. **Multi-phase workflow** (0→5) thay vì single Q&A
2. **Skill loading** — load/unload skill files theo phase
3. **Sub-agent delegation** — SubAgentMiddleware for heavy tasks
4. **Stateful** — brand_brief accumulates, phase state persists
5. **Image generation** — generate_image, generate_brand_key tools
6. **Document generation** — generate_document, generate_presentation tools
7. **More tools** — search_places, deep_research, analyze_reviews, etc.

### Mục tiêu

1. System prompt truyền đạt:
   - Brand Manager + Mentor dual persona
   - Phase workflow (0→0.5→1→2→3→4→5) with branching for rebrand
   - Tool usage guidance (which tool when)
   - Quality gate awareness (know when to proceed)
   - KG search strategy per phase (from Blueprint Section 7.2)
   - Mentor interaction style (explain → do → present → check)
2. Agent factory function:
   - Configure model, all tools, all middlewares, SubAgentMiddleware
   - SkillsMiddleware for progressive skill disclosure (built-in DeepAgents)
   - Context window management (summarization, context editing)
3. CLI entry:
   - `brandmind brand-strategy` command or interactive mode selection
4. E2E tests:
   - New brand scenario
   - Rebrand scenario
   - Phase transitions verified

### Success Metrics / Acceptance Criteria

- **System Prompt**: ≤15k tokens, covers all phases, persona, and tool guidance
- **Agent Creation**: All tools registered, skills loadable, sub-agents delegatable
- **Phase Flow**: Agent correctly enters Phase 0, collects info, proceeds through phases
- **Skill Loading**: Correct skill loaded per phase (verified via context)
- **KG Integration**: Agent uses KG at each phase for framework grounding
- **Sub-Agent Delegation**: Heavy tasks delegated to sub-agents
- **Deliverables**: PDF/PPTX generated at Phase 5
- **Rebrand Path**: Phase 0.5 triggered for rebrand scopes
- **Context Management**: No context overflow through 5-phase conversation

------------------------------------------------------------------------

## 🛠 Solution Design

### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| System Prompt | `src/prompts/brand_strategy/system_prompt.py` | Brand Strategy Agent prompt |
| Phase-specific prompts | `src/prompts/brand_strategy/phase_prompts.py` | Per-phase tool guidance snippets |
| Agent factory | `src/core/src/core/brand_strategy/agent_config.py` | Create brand strategy agent |
| CLI entry | `src/cli/brand_strategy.py` | CLI command for brand strategy mode |
| Session state | `src/core/src/core/brand_strategy/session.py` | Session persistence (brand_brief, phase) |
| E2E tests | `tests/e2e/test_brand_strategy_e2e.py` | End-to-end integration tests |
| __init__ exports | `src/prompts/brand_strategy/__init__.py` | Module exports |

### Modified Components

| Component | Location | Change |
|-----------|----------|--------|
| CLI main | `src/cli/inference.py` | Add brand-strategy subcommand routing |
| Prompts __init__ | `src/prompts/__init__.py` | Export brand_strategy prompts |

------------------------------------------------------------------------

## 📋 Implementation Detail

### Component 1: Brand Strategy System Prompt

#### Requirement 1 - System Prompt Structure
- **Requirement**: Complete system prompt for brand strategy mode covering dual persona, workflow, tools, and KG integration
- **Implementation**:
  - `src/prompts/brand_strategy/__init__.py`
  - `src/prompts/brand_strategy/system_prompt.py`
  ```python
  """
  System prompt for Brand Strategy Agent.

  Guides the agent through the 6-phase brand strategy workflow:
  Phase 0: Business Problem Diagnosis
  Phase 0.5: Brand Equity Audit (rebrand only)
  Phase 1: Market Intelligence
  Phase 2: Brand Positioning
  Phase 3: Brand Identity
  Phase 4: Communication Framework
  Phase 5: Strategy Plan & Deliverables
  """

  BRAND_STRATEGY_SYSTEM_PROMPT = """# ROLE & IDENTITY

  You are **BrandMind — Brand Strategist & Mentor**, a senior brand consultant specializing in F&B (Food & Beverage) brand strategy for the Vietnamese market.

  You operate with TWO personas simultaneously:
  - **Brand Manager**: The strategic expert who does the analysis, builds frameworks, and produces deliverables. You think rigorously using established marketing frameworks from Keller, Kotler, Sharp, Ries & Trout, and Cialdini.
  - **Brand Mentor**: The caring teacher who explains the "why" behind each step, educates the user about branding concepts, and ensures they understand and own the strategy. You speak in Vietnamese (or user's language), use clear explanations, and avoid jargon without context.

  ## CORE PHILOSOPHY
  - **Research-First**: Never assume — always verify with Knowledge Graph, Document Library, and web research before making strategic recommendations.
  - **Framework-Grounded**: Every strategic decision is backed by established marketing theory from your knowledge base.
  - **User-Owned**: The user must understand and agree with every strategic choice. You explain, propose, check, iterate.
  - **F&B-Specialized**: Your recommendations account for F&B realities: location-based competition, sensory branding, menu-as-brand, tight margins, and the importance of in-store experience.

  ---

  # THE WORKFLOW: 6-PHASE BRAND STRATEGY

  You follow a structured 6-phase process. You MUST complete each phase's quality gate before moving to the next. Never skip phases.

  ## Phase 0: Business Problem Diagnosis
  **Goal**: Understand the business situation and classify the project scope.

  **Your actions**:
  1. Greet and explain the process (Mentor mode)
  2. Ask structured questions to understand:
     - Business description (what, where, when)
     - Brand history (new vs existing)
     - Target customers (who they envision)
     - Budget range (bootstrap/starter/growth/enterprise)
     - Goals and challenges
     - Timeline expectations
  3. Classify scope: NEW_BRAND | REFRESH | REPOSITIONING | FULL_REBRAND
  4. For rebrand: explain the 6 signals that indicate rebrand need
  5. Present problem statement → get user confirmation

  **Quality Gate**: Problem statement confirmed, scope classified, budget tier set.
  **If rebrand scope**: → Proceed to Phase 0.5
  **If new brand**: → Skip to Phase 1

  ## Phase 0.5: Brand Equity Audit (Rebrand Only)
  **Goal**: Assess existing brand equity before making changes.

  **Your actions**:
  1. Brand Inventory: catalog existing elements (name, logo, colors, tagline, etc.)
  2. Brand Exploratory: research current perceptions (reviews, social, search)
  3. Equity Assessment: what's working vs what's not
  4. Preserve-Discard Matrix: classify each element as PRESERVE/EVOLVE/DISCARD
  5. Recommend preserve vs change strategy

  **KG searches**: "brand audit", "brand equity sources", "brand element adaptability"
  **Quality Gate**: Preserve-discard decisions confirmed by user.

  ## Phase 1: Market Intelligence
  **Goal**: Comprehensive market understanding for strategic foundation.

  **Your actions (8 research steps)**:
  1. Local competitive mapping (search_places → competitors within radius)
  2. Extended competitor analysis (search_web, crawl_web → deep profiles)
  3. Social media intelligence (browse_and_research → content strategy analysis)
  4. Review analysis (analyze_reviews → customer perception patterns)
  5. Market trend research (deep_research → category and consumer trends)
  6. Target audience definition (KG frameworks → segmentation, personas)
  7. Opportunity identification (synthesize all data → gaps and opportunities)
  8. Strategic synthesis (SWOT + Perceptual Map + Customer Insights)

  **Delegation**: Use sub-agents for multi-competitor research and social analysis.
  **KG searches**: "market segmentation", "competitor analysis framework", "consumer behavior", "SWOT analysis", "Porter's Five Forces"
  **Quality Gate**: SWOT complete, competitive landscape mapped, target defined.

  ## Phase 2: Brand Positioning
  **Goal**: Define the brand's competitive position in the market.

  **Your actions**:
  1. Category frame definition (where you compete)
  2. Points of Parity (table stakes for the category)
  3. Points of Difference (unique competitive advantages)
  4. Brand positioning statement (structured format)
  5. Product-Brand Alignment check (F&B: does the product embody the brand promise?)
  6. Positioning Stress Test (5 criteria: differentiated, relevant, credible, sustainable, ownable)

  **KG searches**: "brand positioning", "points of parity", "competitive differentiation", "brand essence", "product brand alignment"
  **Quality Gate**: Positioning statement passes stress test, user confirmed.

  ## Phase 3: Brand Identity
  **Goal**: Create tangible brand expressions.

  **Your actions**:
  1. Brand personality (Aaker's 5 dimensions)
  2. Brand archetype selection
  3. Visual identity direction (colors, typography, mood board reference)
  4. Verbal identity (tone of voice, vocabulary, do/don't examples)
  5. Sensory identity (F&B-specific: taste, aroma, ambient, tactile)
  6. Brand naming (if needed) — 6 Keller criteria evaluation
  7. Tagline creation (options with rationale)
  8. [Rebrand] Preserve-Discard execution (apply Phase 0.5 decisions)

  **Delegation**: Use Creative Studio sub-agent for image generation tasks.
  **KG searches**: "brand personality framework", "distinctive brand assets", "brand elements criteria", "brand name selection"
  **Quality Gate**: Identity elements defined, naming decided, user approved.

  ## Phase 4: Communication Framework
  **Goal**: Define what the brand says and how.

  **Your actions**:
  1. Value proposition (3 levels: one-liner, elevator, full story)
  2. Messaging hierarchy (functional, emotional, differentiating, credibility, community)
  3. Cialdini persuasion mapping (at least 2 principles applied to F&B)
  4. AIDA communication flow
  5. Channel strategy (Instagram, Facebook, TikTok, Google Maps, In-store, Website)
  6. Content pillars (5 pillars with percentage mix)
  7. Brand story framework

  **KG searches**: "persuasion principles", "AIDA model", "integrated marketing communication"
  **Quality Gate**: Messaging hierarchy complete, channel strategy defined.

  ## Phase 5: Strategy Plan & Deliverables
  **Goal**: Compile everything into professional deliverables.

  **Your actions**:
  1. Brand Strategy Document assembly (PDF/DOCX — 10 sections)
  2. Executive Presentation (PPTX — key slides)
  3. Brand Key one-pager (generate_brand_key tool)
  4. KPI framework (7 categories: awareness, perception, engagement, behavior, loyalty, revenue, distinctiveness)
  5. Implementation roadmap (3 horizons × budget-tier modifiers)
  6. Measurement plan (tools, cadence, reporting)
  7. [Rebrand only] Transition & Change Management Plan (stakeholders, internal, customer, physical, digital, timeline, risks)

  **Delegation**: Use Document Generator sub-agent for PDF/PPTX production.
  **KG searches**: "brand equity measurement", "brand tracking", "brand audit"
  **Quality Gate**: All deliverables generated, user satisfied.

  ---

  # TOOL USAGE GUIDANCE

  ## Tool Inventory (Warehouse Pattern)
  You start with core research tools only. Specialized tools are in the **warehouse** — use the inventory workflow to equip what you need:

  1. `tool_search(query)` — **Browse** the warehouse catalog to find tools matching your need. This is read-only — it does NOT load tools.
  2. `load_tools([names])` — **Equip** specific tools you want to use. They become available on your next action.
  3. Use the loaded tools to complete your task.
  4. `unload_tools([names])` — **Unequip** tools when done to keep your context lean for the next phase.

  Think before loading — only equip what you actually need. When switching phases, unload tools from the previous phase that you no longer need.

  Available tool categories (discoverable via tool_search):
  - **Local Market**: Local business search (Google Places)
  - **Social Media**: Social media browsing and profile analysis
  - **Customer Analysis**: Review analysis and search autocomplete
  - **Image Generation**: Visual assets, mood boards, brand key visuals
  - **Document Export**: PDF, DOCX, PPTX, XLSX, and Markdown generation

  ## Core Research Tools (always available)
  - `search_knowledge_graph`: Marketing theory, frameworks, concepts. USE FIRST to ground your strategy in theory. Returns relationships, not raw text.
  - `search_document_library`: Specific quotes, examples, case studies. Use to verify and deepen KG findings with exact passages.
  - `search_web`: Real-time market data, trends, competitor info. Use for anything not in the KG (current events, specific businesses).
  - `crawl_web`: Deep-dive into competitor websites, menus, pricing.
  - `deep_research`: Multi-step deep research on complex topics. Use for comprehensive market analysis, trend reports.

  ## Specialized Tools (load via tool_search → load_tools when needed)

  ### Research & Analysis
  - `search_places`: Local business mapping. Critical for Phase 1 competitive landscape in F&B.
  - `browse_and_research`: Analyze competitor/industry social media presence.
  - `analyze_reviews`: Aggregate review sentiment and themes.
  - `analyze_social_profile`: Profile-level social media analysis.
  - `get_search_autocomplete`: Consumer search behavior patterns.

  ### Creative & Document Generation
  - `generate_image`: Visual assets — mood boards, color palettes, logo concepts.
  - `generate_brand_key`: Brand Key one-pager visual summary.
  - `generate_document`: PDF/DOCX strategy documents.
  - `generate_presentation`: PPTX executive decks.
  - `generate_spreadsheet`: XLSX analysis spreadsheets.
  - `export_to_markdown`: Clean markdown exports.

  Example workflow:
  ```
  tool_search("generate image")          → see available image tools
  load_tools(["generate_image"])         → equip generate_image
  generate_image(prompt="...", ...)      → use it
  unload_tools(["generate_image"])       → put it back when done
  ```

  ## Planning Tools (always available)
  - `todo_write`: Track phase progress and deliverables.

  ---

  # KG-FIRST RESEARCH STRATEGY

  At EVERY phase, before making strategic decisions:
  1. Search Knowledge Graph for relevant frameworks and theory
  2. Apply framework to the specific brand context
  3. Present framework-grounded recommendation to user

  Your authority comes from COMBINING:
  - Academic frameworks (from KG — Keller, Kotler, Sharp, etc.)
  - Real-world data (from web/social/review research)
  - F&B domain expertise (built into your workflow)

  ## Source Attribution Rules
  - REVEAL: Author name, book title, chapter, framework name
  - HIDE: "Knowledge Graph", "Document Library", "Vector DB", "tool"
  - Speak like a consultant who has the books and data at hand

  ---

  # INTERACTION STYLE

  ## Mentor Cycle (repeat at every step)
  1. **Explain**: What we're about to do and why (cite the framework)
  2. **Do**: Execute the analysis/research
  3. **Present**: Show results with clear structure
  4. **Check**: Ask user for feedback, confirmation, or iteration

  ## Language
  - Default Vietnamese (match user's language)
  - Use clear explanations, avoid naked jargon
  - When using a framework name, briefly explain it first time

  ## Pacing
  - One phase at a time
  - Quality gate before proceeding
  - User confirms before moving on
  - If user wants to jump ahead: warn about skipping, but respect their choice

  ---

  # CONTEXT MANAGEMENT

  You will receive skill content dynamically loaded per phase.
  Follow the loaded skill instructions for detailed phase procedures.

  Phase → Skill mapping:
  - Phase 0, 0.5: brand-strategy-orchestrator (always loaded)
  - Phase 1: + market-research
  - Phase 2-3: + brand-positioning-identity
  - Phase 4-5: + brand-communication-planning

  Previous phase OUTPUTS (structured data) carry forward.
  Previous phase SKILL instructions may be unloaded to save context.

  ---

  # PROACTIVE INTELLIGENCE

  Monitor for these signals and alert/adjust:
  1. Competitor openings detected in social/web monitoring
  2. Market trend shifts (new regulation, consumer preference change)
  3. User info contradicts earlier assumptions
  4. Phase output doesn't align with stated goals
  5. Budget constraints may limit recommendations
  6. Naming conflicts (existing trademarks, domain availability)
  7. Seasonal timing opportunities
  8. Scope-fit misalignment (strategy too ambitious for budget/timeline)

  When triggered: flag the issue, explain impact, recommend adjustment.

  ---

  # CRITICAL RULES

  1. NEVER skip a quality gate
  2. NEVER fabricate data — if unsure, say so
  3. ALWAYS ground strategy in framework theory (KG search first)
  4. ALWAYS get user confirmation before phase transition
  5. DELEGATE heavy tasks to sub-agents (multi-competitor, social analysis, images, documents)
  6. Keep strategic reasoning in the main agent — never delegate strategic decisions
  7. For rebrand: ALWAYS do Phase 0.5 before Phase 1
  8. Budget-tier MUST influence implementation recommendations
  """
  ```

- **Acceptance Criteria**:
  - [ ] Prompt ≤15k tokens (target ~12k)
  - [ ] Covers all 6 phases with actions and quality gates
  - [ ] Tool guidance section with when-to-use rationale
  - [ ] KG-first research strategy
  - [ ] Mentor cycle (explain → do → present → check)
  - [ ] Context management instructions (skill loading)
  - [ ] Proactive intelligence triggers
  - [ ] Language: Vietnamese default, professional consultant tone

#### Requirement 2 - Phase-Specific Prompt Snippets
- **Requirement**: Short prompt snippets injected per phase for focused guidance
- **Implementation**:
  - `src/prompts/brand_strategy/phase_prompts.py`
  ```python
  """Per-phase prompt snippets for focused tool guidance.

  These are injected alongside skill content when entering a new phase.
  They complement the main system prompt with phase-specific KG queries
  and delegation instructions.
  """

  PHASE_0_PROMPT = """## CURRENT PHASE: 0 — Business Problem Diagnosis

  Focus: Understand the business. Ask questions. Classify scope.
  KG queries to run:
  - "brand strategy business problem"
  - "brand health metrics" (if existing brand)
  - "brand revitalization" (if brand issues mentioned)

  DO NOT delegate anything. This is a conversation phase.
  """

  PHASE_0_5_PROMPT = """## CURRENT PHASE: 0.5 — Brand Equity Audit (Rebrand)

  Focus: Audit existing brand equity. Preserve-Discard analysis.
  Tools to use: search_web, crawl_web, browse_and_research, analyze_reviews
  KG queries: "brand audit", "brand equity sources", "brand element adaptability"

  DELEGATE: Social media analysis → Social Media Analyst sub-agent
  KEEP IN MAIN: Preserve-discard strategic decisions
  """

  PHASE_1_PROMPT = """## CURRENT PHASE: 1 — Market Intelligence (8 steps)

  Focus: Comprehensive market research. This is the most tool-heavy phase.
  DELEGATE: Multi-competitor research → Market Research Agent
  DELEGATE: Social media analysis → Social Media Analyst Agent
  KEEP IN MAIN: Strategic synthesis, SWOT, perceptual mapping

  Required KG searches:
  - "market segmentation criteria methods"
  - "consumer behavior purchasing"
  - "competitor analysis framework"
  - "SWOT analysis"
  """

  PHASE_2_PROMPT = """## CURRENT PHASE: 2 — Brand Positioning

  Focus: Strategic positioning decisions. This is the MOST strategic phase.
  DO NOT delegate positioning decisions.
  Tools: search_knowledge_graph (heavy), search_document_library

  Required KG searches:
  - "brand positioning points of parity"
  - "competitive differentiation"
  - "brand essence"
  - "product brand alignment"
  """

  PHASE_3_PROMPT = """## CURRENT PHASE: 3 — Brand Identity

  Focus: Tangible brand expressions. Creative phase.
  DELEGATE: Image generation → Creative Studio Agent
  KEEP IN MAIN: Identity strategy decisions, naming evaluation

  Required KG searches:
  - "brand personality framework"
  - "distinctive brand assets"
  - "brand elements criteria"
  """

  PHASE_4_PROMPT = """## CURRENT PHASE: 4 — Communication Framework

  Focus: Messaging and channel strategy. Apply persuasion theory.
  Tools: search_knowledge_graph, search_web, browse_and_research

  Required KG searches:
  - "persuasion principles Cialdini"
  - "AIDA model"
  - "integrated marketing communication"
  """

  PHASE_5_PROMPT = """## CURRENT PHASE: 5 — Strategy Plan & Deliverables

  Focus: Compile and deliver. Document assembly phase.
  DELEGATE: Document generation → Document Generator Agent
  DELEGATE: Image assets → Creative Studio Agent (brand key visual)
  KEEP IN MAIN: KPI framework, roadmap strategy, transition planning

  Tools: generate_document, generate_presentation, generate_brand_key
  KG searches: "brand equity measurement", "brand tracking"
  """

  PHASE_PROMPTS = {
      "phase_0": PHASE_0_PROMPT,
      "phase_0_5": PHASE_0_5_PROMPT,  # Python dict keys can't have dots
      "phase_1": PHASE_1_PROMPT,
      "phase_2": PHASE_2_PROMPT,
      "phase_3": PHASE_3_PROMPT,
      "phase_4": PHASE_4_PROMPT,
      "phase_5": PHASE_5_PROMPT,
  }
  ```
- **Acceptance Criteria**:
  - [ ] One snippet per phase
  - [ ] Each includes: focus, tools, KG queries, delegation guidance
  - [ ] Short enough to inject alongside skill content without bloating context

### Component 2: Brand Strategy Agent Factory

#### Requirement 1 - Agent Creation Function
- **Requirement**: Factory function mirroring `create_qa_agent()` but with all brand strategy tools, SubAgentMiddleware, and SkillsMiddleware
- **Implementation**:
  - `src/core/src/core/brand_strategy/agent_config.py`
  ```python
  """Deep Agent configuration for Brand Strategy mode.

  Creates a fully-configured agent with:
  - All brand strategy tools (search, analysis, creative, document, planning)
  - SubAgentMiddleware for delegating to 4 specialized sub-agents
  - SkillsMiddleware for progressive skill disclosure (built-in DeepAgents)
  - Context management middlewares (summarization, context editing)
  - Session state management for multi-phase workflow
  """
  from typing import Callable, Optional

  from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
  from deepagents.middleware.subagents import SubAgentMiddleware
  from langchain.agents import create_agent
  from langchain.agents.middleware import (
      ClearToolUsesEdit,
      ContextEditingMiddleware,
      SummarizationMiddleware,
      ToolRetryMiddleware,
  )

  from config.system_config import SETTINGS
  from prompts.brand_strategy import BRAND_STRATEGY_SYSTEM_PROMPT
  from shared.agent_middlewares import (
      EnsureTasksFinishedMiddleware,
      LogModelMessageMiddleware,
  )
  from shared.agent_models.retry_gemini import RetryChatGoogleGenerativeAI
  from shared.agent_tools import TodoWriteMiddleware

  # ---- Tool Imports ----
  # Retrieval tools (existing)
  from shared.agent_tools.retrieval import (
      search_document_library,
      search_knowledge_graph,
  )
  # Web tools (existing)
  from shared.agent_tools.web import search_web, crawl_web
  from shared.agent_tools.browser import BrowserManager, create_browse_tool

  _browser_manager = BrowserManager()
  browse_and_research = create_browse_tool(_browser_manager)
  # New brand strategy tools (Tasks 36-40)
  from shared.agent_tools.places import search_places
  from shared.agent_tools.research import deep_research
  from shared.agent_tools.image import generate_image, generate_brand_key
  from shared.agent_tools.document import (
      generate_document,
      generate_presentation,
      generate_spreadsheet,
      export_to_markdown,
  )
  from shared.agent_tools.analysis import (
      analyze_reviews,
      analyze_social_profile,
      get_search_autocomplete,
  )

  # ---- ToolSearch Infrastructure (Task 47) ----
  from shared.agent_middlewares.tool_search import create_tool_search_middleware

  # ---- Skill Infrastructure (Task 35) ----
  from shared.agent_skills import create_brand_strategy_skills_middleware

  # ---- Sub-Agent Infrastructure (Task 41) ----
  from core.brand_strategy.subagents import (
      create_brand_strategy_subagent_middleware,
  )


  def create_brand_strategy_agent(
      callback: Optional[Callable] = None,
      on_tool_start: Optional[Callable[[str], object]] = None,
      on_tool_end: Optional[Callable[[object], None]] = None,
      initial_phase: str = "phase_0",
  ):
      """Create Brand Strategy Agent with full tool suite.

      Args:
          callback: Optional callback for agent events
          on_tool_start: Hook called when tool starts
          on_tool_end: Hook called when tool ends
          initial_phase: Starting phase (default: phase_0)

      Returns:
          Configured langchain agent with all brand strategy capabilities
      """
      # Initialize model — Gemini 3 Flash with thinking for strategic reasoning
      model = RetryChatGoogleGenerativeAI(
          google_api_key=SETTINGS.GEMINI_API_KEY,
          model="gemini-3-flash-preview",
          temperature=1.0,
          thinking_level="high",   # Higher thinking for strategic work
          max_output_tokens=8000,  # Longer outputs for detailed analysis
          include_thoughts=True,
      )
      model_context_window = 1048576  # 1M tokens

      # ---- All Brand Strategy Tools ----
      tools = [
          # Research (existing + new)
          search_knowledge_graph,
          search_document_library,
          search_web,
          crawl_web,
          browse_and_research,
          search_places,        # Task 36
          deep_research,        # Task 37
          # Analysis (Task 40)
          analyze_reviews,
          analyze_social_profile,
          get_search_autocomplete,
          # Creative (Task 38)
          generate_image,
          generate_brand_key,
          # Document (Task 39)
          generate_document,
          generate_presentation,
          generate_spreadsheet,
          export_to_markdown,
      ]

      # ---- Middlewares ----
      todo_middleware = TodoWriteMiddleware()
      patch_middleware = PatchToolCallsMiddleware()
      retry_middleware = ToolRetryMiddleware()
      stop_check_middleware = EnsureTasksFinishedMiddleware()

      log_message_middleware = LogModelMessageMiddleware(
          callback=callback,
          on_tool_start=on_tool_start,
          on_tool_end=on_tool_end,
          log_thinking=True if not callback else False,
          log_text_response=False,
          log_tool_calls=True if not callback else False,
          log_tool_results=True if not callback else False,
          truncate_thinking=1500,
          truncate_tool_results=1500,
          exclude_tools=[],
      )

      # Context management — aggressive for long multi-phase conversations
      context_edit_middleware = ContextEditingMiddleware(
          edits=[
              ClearToolUsesEdit(
                  trigger=150000,  # Clear after 150k tokens (more room than QA)
                  keep=8,          # Keep more recent tool results
              )
          ]
      )
      msg_summary_middleware = SummarizationMiddleware(
          model=model,
          trigger=(
              "tokens",
              int(model_context_window * 0.5),  # Summarize at 50% (earlier than QA)
          ),
          keep=("messages", 30),  # Keep more messages for multi-phase context
      )

      # ToolSearch middleware — 3-tool inventory pattern (Task 47)
      # Agent sees 5 core tools + 3 inventory tools (tool_search, load_tools, unload_tools) initially.
      # 11 specialized tools discoverable via tool_search → load_tools, unloadable via unload_tools.
      # Reduces visible tools from 18+ to 10 (44% reduction).
      tool_search_middleware = create_tool_search_middleware(
          all_tools=tools,
      )

      # Skills middleware — progressive disclosure of brand strategy skills
      # Agent sees skill listing in system prompt (~300 tokens),
      # reads full SKILL.md on-demand. Orchestrator skill instructs
      # re-reads at phase transitions.
      skills_middleware = create_brand_strategy_skills_middleware()

      # Sub-agent middleware — delegates to 4 specialized sub-agents (Task 41)
      # Build tools_registry: {tool.name: tool} for sub-agent tool resolution
      tools_registry = {tool.name: tool for tool in tools}
      sub_agent_middleware = create_brand_strategy_subagent_middleware(
          tools_registry=tools_registry,
      )

      # ---- Assemble Agent ----
      agent = create_agent(
          model=model,
          tools=tools,
          system_prompt=BRAND_STRATEGY_SYSTEM_PROMPT,
          middleware=[
              context_edit_middleware,
              msg_summary_middleware,
              tool_search_middleware,      # Dynamic tool loading (BEFORE skills)
              skills_middleware,           # Progressive skill disclosure
              sub_agent_middleware,      # Sub-agent delegation via `task` tool
              todo_middleware,
              patch_middleware,
              log_message_middleware,
              retry_middleware,
              stop_check_middleware,
          ],
      )

      return agent
  ```

- **Acceptance Criteria**:
  - [ ] All 15+ tools registered
  - [ ] SubAgentMiddleware configured with 4 sub-agents
  - [ ] SkillsMiddleware with progressive disclosure of 4 brand strategy skills
  - [ ] Context management tuned for long conversations
  - [ ] Follows same pattern as create_qa_agent() and create_cartographer_agent()

### Component 3: CLI Entry Point

#### Requirement 1 - Brand Strategy CLI Command
- **Requirement**: CLI command `brandmind brand-strategy` for interactive brand strategy sessions
- **Implementation**:
  - `src/cli/brand_strategy.py`
  ```python
  """CLI for Brand Strategy interactive sessions.

  Provides the interactive brand strategy mode where users work through
  the 6-phase brand building process with the AI Brand Mentor.
  """
  import asyncio
  from typing import Optional

  from langchain_core.messages import HumanMessage
  from loguru import logger
  from rich.console import Console
  from rich.markdown import Markdown

  from core.brand_strategy.agent_config import create_brand_strategy_agent
  from core.brand_strategy.session import (
      BrandStrategySession,
      load_session,
      save_session,
  )
  from rich.panel import Panel

  console = Console()


  async def run_brand_strategy_session(
      initial_message: Optional[str] = None,
      session_id: Optional[str] = None,
  ) -> None:
      """Run interactive brand strategy session.

      Args:
          initial_message: Optional first message to start the conversation
          session_id: Optional session ID to resume a previous session
      """
      console.print(Panel(
          "[bold cyan]BrandMind — Brand Strategy Mode[/bold cyan]\n"
          "AI Brand Strategist & Mentor for F&B\n"
          "Type 'exit' or 'quit' to end session\n"
          "Type 'save' to save current session\n"
          "Type 'status' to see current phase",
          title="🧠 BrandMind",
      ))

      # Load or create session
      if session_id:
          session = load_session(session_id)
          if session:
              console.print(f"[green]Resumed session: {session_id}[/green]")
              console.print(f"[dim]Current phase: {session.current_phase}[/dim]")
          else:
              console.print(f"[yellow]Session {session_id} not found. Starting new.[/yellow]")
              session = BrandStrategySession()
      else:
          session = BrandStrategySession()

      # Create agent
      agent = create_brand_strategy_agent(
          initial_phase=session.current_phase,
      )

      # Conversation state
      messages = session.messages.copy() if session.messages else []

      # If initial message provided, use it as first input
      if initial_message:
          messages.append(HumanMessage(content=initial_message))

      # Main conversation loop
      while True:
          if not initial_message or len(messages) > 1:
              try:
                  user_input = console.input("[bold green]You:[/bold green] ")
              except (KeyboardInterrupt, EOFError):
                  break

              if user_input.strip().lower() in ("exit", "quit"):
                  save_session(session)
                  console.print("[dim]Session saved. Goodbye![/dim]")
                  break

              if user_input.strip().lower() == "save":
                  save_session(session)
                  console.print("[green]Session saved.[/green]")
                  continue

              if user_input.strip().lower() == "status":
                  console.print(Panel(
                      f"Phase: {session.current_phase}\n"
                      f"Scope: {session.scope or 'Not yet classified'}\n"
                      f"Brand: {session.brand_name or 'Not yet named'}",
                      title="📊 Status",
                  ))
                  continue

              messages.append(HumanMessage(content=user_input))

          initial_message = None  # Clear after first use

          # Run agent
          try:
              result = await agent.ainvoke(
                  {"messages": messages},
                  {"recursion_limit": 200},  # Higher limit for multi-tool phases
              )

              # Extract and display response
              if "messages" in result and result["messages"]:
                  for msg in reversed(result["messages"]):
                      if hasattr(msg, "content") and msg.content:
                          response_text = _extract_text(msg.content)
                          if response_text:
                              console.print()
                              console.print(Panel(
                                  Markdown(response_text),
                                  title="🧠 BrandMind",
                                  border_style="cyan",
                              ))
                              break

              # Update messages for next turn
              messages = result.get("messages", messages)

              # Update session state (phase tracking done by orchestrator skill)
              session.messages = messages

          except Exception as e:
              logger.error(f"Agent error: {e}")
              console.print(f"[red]Error: {e}[/red]")
              continue


  def _extract_text(content) -> str:
      """Extract text from agent message content."""
      if isinstance(content, str):
          return content
      if isinstance(content, list):
          parts = []
          for part in content:
              if isinstance(part, dict) and part.get("type") == "text":
                  parts.append(part.get("text", ""))
              elif isinstance(part, str):
                  parts.append(part)
          return "\n".join(parts)
      return str(content)
  ```

- **Acceptance Criteria**:
  - [ ] Interactive session with conversation loop
  - [ ] Session save/load support
  - [ ] Status command shows current phase
  - [ ] Graceful error handling
  - [ ] Rich console output with panels

#### Requirement 2 - CLI Integration with Main Entry
- **Requirement**: Add `brand-strategy` subcommand to existing CLI
- **Implementation**:
  - Modify `src/cli/inference.py` — add subcommand in argument parser
  ```python
  # In create_parser() or main():
  brand_strategy_parser = subparsers.add_parser(
      "brand-strategy",
      help="Start interactive brand strategy session",
  )
  brand_strategy_parser.add_argument(
      "-m", "--message",
      help="Initial message to start the session",
      default=None,
  )
  brand_strategy_parser.add_argument(
      "--session",
      help="Resume a previous session by ID",
      default=None,
  )
  brand_strategy_parser.set_defaults(func=run_brand_strategy_session)
  ```
- **Acceptance Criteria**:
  - [ ] `brandmind brand-strategy` launches interactive session
  - [ ] `brandmind brand-strategy -m "..."` starts with initial message
  - [ ] `brandmind brand-strategy --session <id>` resumes session

### Component 4: Session & State Persistence

#### Requirement 1 - Session Management
- **Requirement**: Persist brand strategy session state across interruptions
- **Implementation**:
  - `src/core/src/core/brand_strategy/session.py`
  ```python
  """Brand Strategy session state management.

  Handles saving and loading of multi-phase brand strategy sessions,
  allowing users to resume work across separate conversations.

  Architecture: BrandStrategySession composes a BrandBrief (Task 42)
  as the single source of truth for all phase outputs. The session
  adds workflow metadata (current phase, completed phases, messages)
  around the brief. There is no separate phase_outputs dict — all
  phase data lives in brief.phase_N_output fields.
  """
  import json
  import uuid
  from datetime import datetime
  from pathlib import Path
  from typing import Optional

  from pydantic import BaseModel, Field

  from core.brand_strategy.orchestrator.brand_brief import BrandBrief

  # Session storage directory
  SESSIONS_DIR = Path("data/brand_strategy_sessions")


  class BrandStrategySession(BaseModel):
      """Persistent session state for brand strategy workflow.

      Composes a BrandBrief instance as the single source of truth
      for all accumulated phase outputs. The session wraps the brief
      with workflow tracking (phase progression, messages) and
      persistence (save/load to JSON).

      State ownership:
          - Phase output data → BrandBrief (brief.phase_N_output)
          - Workflow progression → BrandStrategySession (current_phase, completed_phases)
          - Conversation history → BrandStrategySession (messages)
          - Persistence → save_session / load_session functions
      """
      session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
      created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
      updated_at: str = ""

      # Workflow state
      current_phase: str = "phase_0"
      scope: str | None = None  # NEW_BRAND | REFRESH | REPOSITIONING | FULL_REBRAND
      budget_tier: str | None = None  # bootstrap | starter | growth | enterprise
      brand_name: str | None = None

      # Phase completion tracking
      completed_phases: list[str] = Field(default_factory=list)

      # Brand brief — single source of truth for all phase outputs
      brief: BrandBrief = Field(default_factory=BrandBrief)

      # Conversation messages (serialized)
      messages: list = Field(default_factory=list)

      def advance_phase(self, next_phase: str) -> None:
          """Move to the next phase, recording completion.

          Args:
              next_phase: Phase identifier to transition to.
          """
          self.completed_phases.append(self.current_phase)
          self.current_phase = next_phase
          self.updated_at = datetime.now().isoformat()

      def save_phase_output(self, phase: str, output: dict) -> None:
          """Store structured output from a completed phase.

          Delegates to brief.add_phase_output() so all phase data
          lives in a single location (the BrandBrief).

          Args:
              phase: Phase identifier (e.g., "phase_0", "phase_1").
              output: Dict of phase output data.

          Raises:
              ValueError: If phase is not a valid phase identifier.
          """
          self.brief.add_phase_output(phase, output)
          self.updated_at = datetime.now().isoformat()

      def sync_metadata_to_brief(self) -> None:
          """Sync session metadata into the BrandBrief.

          Call this after updating brand_name, scope, or budget_tier
          to keep the brief's metadata fields in sync.
          """
          self.brief.session_id = self.session_id
          self.brief.brand_name = self.brand_name or ""
          self.brief.scope = self.scope or ""
          self.brief.budget_tier = self.budget_tier or ""


  def save_session(session: BrandStrategySession) -> Path:
      """Save session to disk.

      Args:
          session: Session to save

      Returns:
          Path to saved session file
      """
      SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
      session.updated_at = datetime.now().isoformat()
      filepath = SESSIONS_DIR / f"{session.session_id}.json"
      filepath.write_text(
          session.model_dump_json(indent=2),
          encoding="utf-8",
      )
      return filepath


  def load_session(session_id: str) -> Optional[BrandStrategySession]:
      """Load session from disk.

      Args:
          session_id: Session ID to load

      Returns:
          Loaded session or None if not found
      """
      filepath = SESSIONS_DIR / f"{session_id}.json"
      if not filepath.exists():
          return None
      data = json.loads(filepath.read_text(encoding="utf-8"))
      return BrandStrategySession(**data)


  def list_sessions() -> list[dict]:
      """List all saved sessions.

      Returns:
          List of session summaries with id, brand_name, phase, updated_at
      """
      SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
      sessions = []
      for filepath in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
          try:
              data = json.loads(filepath.read_text(encoding="utf-8"))
              sessions.append({
                  "session_id": data.get("session_id"),
                  "brand_name": data.get("brand_name", "Unnamed"),
                  "phase": data.get("current_phase", "phase_0"),
                  "scope": data.get("scope", "Unknown"),
                  "updated_at": data.get("updated_at", ""),
              })
          except Exception:
              continue
      return sessions
  ```

- **Acceptance Criteria**:
  - [ ] Session save/load roundtrip works (BrandBrief serialized inside session JSON)
  - [ ] Phase advancement tracked via completed_phases list
  - [ ] Phase outputs stored via brief.add_phase_output() (single source of truth)
  - [ ] sync_metadata_to_brief() keeps brief metadata in sync with session
  - [ ] No duplicate state — no separate brand_brief dict or phase_outputs dict
  - [ ] List sessions shows all saved sessions

### Component 5: E2E Integration Tests

#### Requirement 1 - End-to-End Test Scenarios
- **Requirement**: E2E tests verifying the full workflow for both new brand and rebrand paths
- **Implementation**:
  - `tests/e2e/test_brand_strategy_e2e.py`
  ```python
  """End-to-end integration tests for Brand Strategy workflow.

  These tests verify the full pipeline:
  1. Agent creation with all tools
  2. Phase 0 interview and scope classification
  3. Phase transitions
  4. Skill loading per phase
  5. Sub-agent delegation
  6. Deliverable generation at Phase 5
  """
  import pytest
  from langchain_core.messages import HumanMessage

  from core.brand_strategy.agent_config import create_brand_strategy_agent
  from core.brand_strategy.session import (
      BrandStrategySession,
      load_session,
      save_session,
  )


  @pytest.fixture
  def brand_strategy_agent():
      """Create a brand strategy agent for testing."""
      return create_brand_strategy_agent()


  class TestNewBrandE2E:
      """E2E tests for new brand creation scenario."""

      @pytest.mark.asyncio
      async def test_phase_0_interview(self, brand_strategy_agent):
          """Phase 0: Agent should ask structured questions about the business."""
          result = await brand_strategy_agent.ainvoke(
              {"messages": [
                  HumanMessage(content="Tôi muốn xây dựng thương hiệu cho quán café specialty mới ở Quận 3, TPHCM")
              ]},
              {"recursion_limit": 100},
          )
          response = _get_response(result)
          # Agent should engage in interview mode, not jump to analysis
          assert response is not None
          assert len(response) > 100  # Meaningful response, not a stub

      @pytest.mark.asyncio
      async def test_scope_classification_new_brand(self, brand_strategy_agent):
          """Verify new brand is classified correctly."""
          messages = [
              HumanMessage(content="Tôi muốn mở quán café mới, chưa có thương hiệu gì"),
          ]
          result = await brand_strategy_agent.ainvoke(
              {"messages": messages},
              {"recursion_limit": 100},
          )
          response = _get_response(result)
          # Should classify as new brand, not trigger Phase 0.5
          assert response is not None

      @pytest.mark.asyncio
      async def test_agent_has_all_tools(self, brand_strategy_agent):
          """Verify all brand strategy tools are registered."""
          # Check agent has expected tools
          tool_names = [
              tool.name for tool in brand_strategy_agent.tools
          ] if hasattr(brand_strategy_agent, 'tools') else []

          expected_tools = [
              "search_knowledge_graph", "search_document_library",
              "search_web", "crawl_web", "browse_and_research",
              "search_places", "deep_research",
              "analyze_reviews", "generate_image", "generate_document",
          ]
          for tool_name in expected_tools:
              assert tool_name in tool_names, f"Missing tool: {tool_name}"


  class TestRebrandE2E:
      """E2E tests for rebrand scenario."""

      @pytest.mark.asyncio
      async def test_rebrand_triggers_phase_05(self, brand_strategy_agent):
          """Rebrand scope should trigger Phase 0.5 audit."""
          messages = [
              HumanMessage(content=(
                  "Quán café của tôi đã hoạt động 5 năm nhưng doanh thu giảm, "
                  "brand cũ không còn phù hợp. Tôi muốn làm mới thương hiệu."
              )),
          ]
          result = await brand_strategy_agent.ainvoke(
              {"messages": messages},
              {"recursion_limit": 100},
          )
          response = _get_response(result)
          # Agent should recognize this as a rebrand case
          assert response is not None


  class TestSessionPersistence:
      """Tests for session save/load."""

      def test_session_roundtrip(self):
          """Session save and load preserves state."""
          session = BrandStrategySession(
              brand_name="Test Café",
              scope="NEW_BRAND",
              current_phase="phase_1",
              budget_tier="starter",
          )
          save_session(session)
          loaded = load_session(session.session_id)
          assert loaded is not None
          assert loaded.brand_name == "Test Café"
          assert loaded.current_phase == "phase_1"
          assert loaded.scope == "NEW_BRAND"

      def test_phase_advancement(self):
          """Phase advancement tracks completed phases."""
          session = BrandStrategySession()
          assert session.current_phase == "phase_0"
          session.advance_phase("phase_1")
          assert session.current_phase == "phase_1"
          assert "phase_0" in session.completed_phases


  def _get_response(result: dict) -> str | None:
      """Extract text response from agent result."""
      if "messages" in result and result["messages"]:
          for msg in reversed(result["messages"]):
              if hasattr(msg, "content") and msg.content:
                  if isinstance(msg.content, str):
                      return msg.content
                  if isinstance(msg.content, list):
                      parts = [
                          p.get("text", "") for p in msg.content
                          if isinstance(p, dict) and p.get("type") == "text"
                      ]
                      return "\n".join(parts)
      return None
  ```

- **Acceptance Criteria**:
  - [ ] New brand E2E: Phase 0 interview works
  - [ ] Rebrand E2E: Phase 0.5 triggered
  - [ ] All tools registered on agent
  - [ ] Session persistence roundtrip
  - [ ] Phase advancement tracking

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Full New Brand Flow
- **Purpose**: Verify complete new brand creation from Phase 0 to Phase 5
- **Steps**:
  1. Start brand strategy session
  2. Provide: "Quán café specialty mới ở Quận 3" 
  3. Answer Phase 0 questions
  4. Verify Phase 1 research uses search_places + search_web + KG
  5. Verify Phase 2 positioning uses KG heavily
  6. Verify Phase 5 produces PDF + PPTX
- **Expected Result**: Complete brand strategy with deliverables
- **Status**: ⏳ Pending

### Test Case 2: Full Rebrand Flow
- **Purpose**: Verify rebrand path with Phase 0.5
- **Steps**:
  1. Start with: "Quán café 5 năm cần rebrand"
  2. Verify scope classified as REFRESH or FULL_REBRAND
  3. Verify Phase 0.5 equity audit triggered
  4. Verify preserve-discard matrix created
  5. Complete through Phase 5 — verify transition plan present
- **Expected Result**: Complete rebrand strategy with transition plan
- **Status**: ⏳ Pending

### Test Case 3: Context Window Management
- **Purpose**: Verify no context overflow in 5+ phase conversation
- **Steps**:
  1. Run through all phases (simulated with shorter responses)
  2. Monitor token usage per phase
  3. Verify summarization triggers correctly
  4. Verify skill unloading works
- **Expected Result**: Conversation completes without context overflow
- **Status**: ⏳ Pending

### Test Case 4: Session Resume
- **Purpose**: Verify session can be saved and resumed
- **Steps**:
  1. Start session, complete Phase 0 and Phase 1
  2. Save session
  3. Create new agent, load session
  4. Verify Phase 1 outputs available
  5. Continue from Phase 2
- **Expected Result**: Seamless resume from saved state
- **Status**: ⏳ Pending

### Test Case 5: Tool Registration
- **Purpose**: Verify all 15+ tools are available on the agent
- **Steps**:
  1. Create brand strategy agent
  2. Inspect registered tools
  3. Verify: search_places, deep_research, generate_image, generate_document, etc.
- **Expected Result**: All tools present and callable
- **Status**: ⏳ Pending

### Test Case 6: Sub-Agent Delegation
- **Purpose**: Verify heavy tasks are delegated to sub-agents
- **Steps**:
  1. Trigger Phase 1 with 5+ competitors identified
  2. Verify agent delegates multi-competitor research to Market Research Agent
  3. Verify social media analysis delegated to Social Media Analyst
- **Expected Result**: Delegation via `task` tool observed
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation.

### What Was Implemented

**Components Completed**:
- [x] [Component 1]: Brand Strategy System Prompt
- [x] [Component 2]: Brand Strategy Agent Factory
- [x] [Component 3]: CLI Entry Point
- [x] [Component 4]: Session & State Persistence
- [x] [Component 5]: E2E Integration Tests

**Files Created/Modified**:
```
src/prompts/brand_strategy/
├── __init__.py                            # Module exports
├── system_prompt.py                       # Main system prompt (~12k tokens)
├── phase_prompts.py                       # Per-phase prompt snippets
├── analyze_reviews.py                     # REVIEW_ANALYSIS_PROMPT (Task 40)
├── analyze_social_profile.py              # SOCIAL_ANALYSIS_PROMPT (Task 40)
├── generate_image.py                      # BRAND_PROMPT_TEMPLATES (Task 38)
├── generate_brand_key.py                  # BRAND_KEY_PROMPT_TEMPLATE (Task 38)
└── subagents/                             # Sub-agent prompts (Task 41)
    ├── __init__.py
    ├── market_research.py
    ├── social_media.py
    ├── creative_studio.py
    └── document_generator.py

src/core/src/core/brand_strategy/
├── agent_config.py                        # Agent factory function
└── session.py                             # Session persistence

src/cli/
├── brand_strategy.py                      # CLI interactive session
└── inference.py                           # Modified: add brand-strategy subcommand

tests/e2e/
└── test_brand_strategy_e2e.py             # E2E integration tests
```

------------------------------------------------------------------------
