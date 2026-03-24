# Task 37: deep_research Tool — Multi-Step Research Pipeline

## 📌 Metadata

- **Epic**: Brand Strategy — Tools
- **Priority**: High
- **Estimated Effort**: 3-4 days
- **Team**: Backend
- **Related Tasks**: Task 29 (Search Orchestration), Task 36 (search_places)
- **Blocking**: Task 43 (Market Research Skill uses deep_research for trend analysis)
- **Blocked by**: None

### ✅ Progress Checklist

- [x] 🤖 [Agent Protocol](#-agent-protocol) — Read and confirm before starting
- [x] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [x] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [x] 🔬 [Pre-Implementation Research](#-pre-implementation-research) — Findings logged before coding
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [x] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] ✅ [Component 1: Research Prompts](#component-1-research-prompts) - Query generation + synthesis prompts
    - [x] ✅ [Component 2: deep_research Function](#component-2-deep_research-function) - Pipeline orchestration
- [ ] 🧪 [Test Execution Log](#-test-execution-log) — All tests run and results recorded
- [ ] 📊 [Decision Log](#-decision-log) — Key decisions documented
- [ ] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards (see Agent Protocol section)
- **Prompt Engineering Standards**: `tasks/prompt_engineering_standards.md`
- **Blueprint Reference**: `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — Section 5.3, Tool 9
- **Existing search_web**: `src/shared/src/shared/agent_tools/search/search_web.py` — multi-provider search with auto-fallback (SearXNG → Perplexity → Tavily → Bing)
- **Existing scrape_web_content**: `src/shared/src/shared/agent_tools/crawler/crawl_web.py` — 3 modes: clean, summary, relevant (LLM-filtered)
- **GoogleAIClientLLM pattern**: `src/shared/src/shared/agent_tools/crawler/crawl4ai_client.py` — internal LLM calls for tool-level processing
- **Prompt convention**: `src/prompts/{domain}/` — module-level string constants, `{{variable}}` template syntax

------------------------------------------------------------------------

## 🤖 Agent Protocol

> **MANDATORY**: Read this section in full before starting any implementation work.

### Rule 1 — Research Before Coding

Before writing any code for a component:
1. Read all files referenced in "Reference Documentation" above
2. Read existing code in `src/shared/src/shared/agent_tools/search/` and `src/shared/src/shared/agent_tools/crawler/` to understand current patterns
3. Read `src/prompts/` to understand prompt file conventions
4. Log your findings in [Pre-Implementation Research](#-pre-implementation-research) before proceeding
5. **Do NOT assume or invent** behavior — verify against actual source

### Rule 2 — Ask, Don't Guess

When encountering any of the following, **STOP and ask the user** before proceeding:

- A requirement is ambiguous or contradictory
- Two valid implementation approaches exist with non-trivial trade-offs
- An existing interface, API, or behavior conflicts with the spec
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

Applies to `GENERATE_QUERIES_PROMPT` and `SYNTHESIZE_RESEARCH_PROMPT` in this task.

**Line length**: Prompt strings are **exempt from the 100-character rule**. Break lines at semantic boundaries (end of a rule, end of a clause), not at character count.

**Full standards**: `tasks/prompt_engineering_standards.md`

Key requirements:
- Structure with Markdown headings (`##`, `###`) to separate role, process, rules, output format
- Use imperative mood — direct commands, no hedging
- Every conditional must have an explicit "otherwise" branch
- Define what the agent must **never** do (Hard Constraints section)
- Output format specified as a template, not a description
- Self-verification step for the synthesis prompt (critical output)
- Review using the checklist at the end of `prompt_engineering_standards.md` before finalizing

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Brand strategy Phase 1 cần **deep research** cho F&B industry trends, market analysis, consumer behavior — những câu hỏi phức tạp cần tổng hợp nhiều nguồn
- Hiện tại `search_web` chỉ trả về search results (snippets) — không đủ sâu cho phân tích market trends hay competitive landscape tổng quan
- `scrape_web_content` extract nội dung 1 trang — nhưng deep research cần tổng hợp 5-10+ nguồn rồi synthesize thành analysis có cấu trúc
- **Giải pháp**: Xây pipeline kết hợp 2 tools đã có (`search_web` + `scrape_web_content`) + LLM synthesis → **không cần thêm external API dependency** (không Perplexity Sonar key)
- `scrape_web_content` đã có mode `relevant` (LLM filter content theo query) → 70% bước "extract relevant info" đã built-in
- `search_web` đã có provider chain tự fallback → reliability cao

### Thiết kế đã đánh giá & loại bỏ

| Approach | Lý do loại bỏ |
|----------|---------------|
| **Perplexity Sonar API** | Ép user phải có API key — không acceptable cho tool required ở mọi use case |
| **Sub-agent (5th agent)** | Sub-agent không thể gọi sub-agent khác → market-research sub-agent (consumer chính) mất khả năng dùng deep_research. Blueprint define deep_research là **tool** trong tool list của market-research agent |
| **Skill (SKILL.md)** | Overlap với task_43 (Market Research Skill đã chứa research methodology). Không encapsulated — agent phải tự manage multi-step research, unreliable |

### Mục tiêu

Xây dựng `deep_research` tool cho phép agent:

1. Thực hiện nghiên cứu sâu về một chủ đề với nhiều cấp độ (quick/standard/comprehensive)
2. Nhận kết quả tổng hợp có structured analysis + citations thay vì raw search results
3. Không cần external API key — sử dụng hoàn toàn `search_web` + `scrape_web_content` + LLM synthesis
4. Phù hợp cho research tasks trong Phase 1 (market trends, industry analysis, consumer behavior)

### Success Metrics / Acceptance Criteria

- **Quality**: Kết quả deep research phải có depth tương đương đọc 5-10 bài viết, có citations
- **No external dependency**: Hoạt động hoàn toàn với existing tools + Gemini API (đã required cho toàn bộ system)
- **Speed**: Standard depth ≤ 45 giây; Quick ≤ 20 giây; Comprehensive ≤ 90 giây
- **Integration**: Agent gọi `deep_research("F&B market trends Vietnam 2026")` và nhận analysis có cấu trúc
- **Convention compliance**: Plain function (no `@tool`), prompts in `src/prompts/research/`

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Multi-Step Research Pipeline**: Pipeline cố định 4 bước — (1) LLM generate targeted search queries, (2) `search_web` batch search, (3) `scrape_web_content(mode="relevant")` crawl top pages filtered by query, (4) LLM synthesize tất cả thành structured research summary với citations. Depth parameter control số queries + số pages crawl.

### Pipeline Flow

```
deep_research(topic, context, depth)
    │
    ├─ Step 1: Query Generation
    │   └─ GoogleAIClientLLM + GENERATE_QUERIES_PROMPT
    │   └─ Input: topic + context → Output: list[str] (2-5 queries)
    │
    ├─ Step 2: Web Search
    │   └─ search_web(queries) → search results with snippets + URLs
    │   └─ Existing provider chain handles reliability
    │
    ├─ Step 3: Content Crawling
    │   └─ Deduplicate URLs, rank by snippet relevance
    │   └─ scrape_web_content(url, mode="relevant", query=topic) × top N
    │   └─ ThreadPoolExecutor for concurrent crawling
    │   └─ Skip failed URLs gracefully
    │
    └─ Step 4: Research Synthesis
        └─ GoogleAIClientLLM + SYNTHESIZE_RESEARCH_PROMPT
        └─ Input: topic + context + all crawled content + search snippets
        └─ Output: structured markdown summary with citations
```

### Existing Components (Reuse)

| Component | Location | Reuse |
|-----------|----------|-------|
| search_web | `src/shared/src/shared/agent_tools/search/search_web.py` | Step 2: batch search with auto-fallback |
| scrape_web_content | `src/shared/src/shared/agent_tools/crawler/crawl_web.py` | Step 3: crawl + LLM-filter relevant content |
| GoogleAIClientLLM | `src/shared/src/shared/model_clients/llm/google/` | Steps 1 & 4: query generation + synthesis |
| SETTINGS | `src/config/src/config/system_config.py` | GEMINI_API_KEY for LLM client |

### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Query generation prompt | `src/prompts/research/generate_queries.py` | LLM prompt to generate search queries from topic |
| Synthesis prompt | `src/prompts/research/synthesize_research.py` | LLM prompt to synthesize crawled content into research summary |
| deep_research function | `src/shared/src/shared/agent_tools/research/deep_research.py` | Pipeline orchestration |

### Depth Configuration

| Depth | Queries | Crawl Top N | Use Case |
|-------|---------|-------------|----------|
| `quick` | 2 | 2 | Fast overview, simple topic |
| `standard` | 4 | 4 | Balanced, default for most research |
| `comprehensive` | 5 | 6 | Deep analysis, complex market research |

> **⚠️ Note**: `search_web` enforces `MAX_QUERIES=5` (see `search_web.py:43`). The `comprehensive` depth generates 5 queries (not 6) to stay within this limit. Crawl count remains 6 because URL crawling is independent of query count — top 6 URLs are selected from the combined results of all queries.

### Issues & Solutions

1. **Crawl failures** → Skip failed URLs, proceed with remaining. Log warning. Minimum 1 successful crawl required for synthesis
2. **Content too long for synthesis** → `scrape_web_content(mode="relevant")` already LLM-filters content per query → manageable token size. Additional truncation at `max_chars_per_page` as safety net
3. **Query quality** → Prompt instructs LLM to generate diverse, specific queries (not just rephrasings). Include context like region, time period, segment
4. **Concurrent crawling latency** → ThreadPoolExecutor with max_workers=3 for parallel crawling. Still sequential search_web calls (respects rate limits)
5. **Search result ranking** → Sort by relevance heuristic: snippet contains topic keywords → higher priority. Deduplicate by domain to get diverse sources
6. **Synthesis token limits** → `scrape_web_content(mode="relevant")` already filters content, but comprehensive depth (6 pages × 8000 chars) could produce ~48K chars of crawled content. `GoogleAIClientLLM` with `gemini-2.5-flash-lite` supports 1M token context — sufficient. However, add `max_chars_per_page` as safety net and log total chars before synthesis call

------------------------------------------------------------------------

## 🔬 Pre-Implementation Research

> **Agent**: Complete this section BEFORE writing any implementation code.
> Log your findings here so the user can verify your understanding is correct.
> If anything contradicts the spec above, flag it immediately.

### Codebase Audit

- **Files read**: [List existing files reviewed — search_web.py, crawl_web.py, crawl4ai_client.py, existing prompts/]
- **Relevant patterns found**: [Describe patterns in existing tools — plain functions, error handling, logging, config access]
- **Potential conflicts**: [Any existing interface or behavior that may conflict with the spec]

### External Library / API Research

- **Library/API**: google-genai (GoogleAIClientLLM wrapper) — for Steps 1 & 4
- **Documentation source**: Existing `src/shared/src/shared/model_clients/llm/google/` implementation
- **Key findings**: [How GoogleAIClientLLMConfig works, response_mime_type options, thinking_budget behavior]
- **Interface confirmed**: `llm.complete(prompt, temperature=X).text` returns string

### Unknown / Risks Identified

- [ ] Verify search_web return structure matches `_rank_and_deduplicate_urls` expectations
- [ ] Confirm scrape_web_content(mode="relevant") returns `.content` attribute
- [ ] Test LLM JSON output reliability with response_mime_type="application/json"

### Research Status

- [ ] All referenced documentation read
- [ ] Existing codebase patterns understood
- [ ] External dependencies verified
- [ ] No unresolved ambiguities remain → Ready to implement

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Research Prompts** (Day 1)
1. `src/prompts/research/__init__.py` — re-exports prompt constants
2. `src/prompts/research/generate_queries.py` — `GENERATE_QUERIES_PROMPT`
   - Input: topic, context, num_queries
   - Output instruction: JSON list of search query strings
3. `src/prompts/research/synthesize_research.py` — `SYNTHESIZE_RESEARCH_PROMPT`
   - Input: topic, context, search snippets, crawled content with source URLs
   - Output instruction: structured markdown with citations

### **Phase 2: Pipeline Function** (Day 2-3)
1. `src/shared/src/shared/agent_tools/research/deep_research.py`
   - `deep_research(topic, context, depth)` → `str`
   - Internal: query gen → search → crawl → synthesize
   - Uses GoogleAIClientLLM for Steps 1 & 4
   - Uses search_web and scrape_web_content for Steps 2 & 3
   - ThreadPoolExecutor for concurrent crawling
2. `src/shared/src/shared/agent_tools/research/__init__.py` — re-export
3. Update `src/shared/src/shared/agent_tools/__init__.py` — add deep_research export

### **Phase 3: Testing** (Day 3-4)
1. Manual test with various topics and depth levels
2. Verify citations map to real sources
3. Test error handling (crawl failures, empty results)

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards Reminder**: Apply the standards from Agent Protocol Rule 4 to every file.
> Prompt strings follow Rule 5. Test specifications are written BEFORE implementation — follow TDD order within each requirement.

### Component 1: Research Prompts

#### Requirement 1 - Query Generation Prompt
- **Requirement**: Prompt that instructs LLM to generate diverse, targeted search queries from a research topic
- **Implementation**:
  - `src/prompts/research/generate_queries.py`
  ```python
  GENERATE_QUERIES_PROMPT = """
  ## Role
  You are a market intelligence research strategist specializing in brand strategy, consumer behavior, and competitive analysis.

  ## Task
  Generate exactly {{num_queries}} targeted search queries to research the given topic comprehensively for brand strategy decision-making.

  ## Research Topic
  {{topic}}

  ## Additional Context
  {{context}}

  ## Query Generation Rules
  1. Each query MUST target a DIFFERENT aspect or angle of the topic. Never generate overlapping queries.
  2. Include specific qualifiers where relevant: geographic region, time period (prefer current year: 2025-2026), industry segment, demographic group.
  3. Mix query types for comprehensive coverage:
     - 1-2 broad market overview queries (market size, growth trends, industry reports)
     - 1-2 specific segment or niche queries (target demographic behavior, sub-category trends)
     - 1-2 competitive or strategic queries (key players, market positioning, competitive gaps)
  4. Optimize for web search engines: concise, keyword-rich, 5-12 words each.
  5. Prefer queries that surface data-rich pages: industry reports, market research, government statistics, trade publications.

  ## Hard Constraints
  - NEVER generate duplicate or near-duplicate queries.
  - NEVER include generic filler queries like "what is [topic]" or "[topic] definition".
  - NEVER exceed {{num_queries}} queries.

  ## Output Format
  Return a JSON array of exactly {{num_queries}} strings. No other text, no explanation, no markdown code blocks.

  ## Example
  Topic: "specialty coffee market trends in Vietnam"
  Context: "Focus on Ho Chi Minh City, premium segment"

  ["specialty coffee market size Vietnam 2024 2025 growth forecast",
   "premium third wave coffee shops Ho Chi Minh City consumer trends",
   "Gen Z specialty coffee consumption behavior Vietnam urban demographics",
   "specialty coffee competitive landscape Vietnam key players market share"]
  """
  ```
- **Acceptance Criteria**:
  - [ ] Prompt produces diverse, non-overlapping queries
  - [ ] Respects `num_queries` parameter
  - [ ] Output parseable as JSON list of strings
  - [ ] Queries are specific enough for good search results

#### Requirement 2 - Research Synthesis Prompt
- **Requirement**: Prompt that instructs LLM to synthesize crawled content into a structured research summary with citations
- **Implementation**:
  - `src/prompts/research/synthesize_research.py`
  ```python
  SYNTHESIZE_RESEARCH_PROMPT = """
  ## Role
  You are a senior market research analyst producing executive-quality research briefs for brand strategy decision-makers.

  ## Task
  Synthesize the provided web research into a structured, actionable analysis with cited sources.

  ## Research Topic
  {{topic}}

  ## Research Context
  {{context}}

  ## Source Material

  ### Search Result Snippets
  {{search_snippets}}

  ### Crawled Full-Page Content
  {{crawled_content}}

  ---

  ## Analysis Process
  Work through these steps before writing your output:

  1. **Scan all sources** — identify the most authoritative, recent, and data-rich materials.
  2. **Extract key data points** — statistics, market figures, consumer insights, competitive moves.
  3. **Cross-reference** — note where multiple sources agree (consensus) and where they disagree (contradictions).
  4. **Identify patterns** — connect isolated facts into strategic themes relevant to brand strategy.
  5. **Assess gaps** — note what the sources do NOT cover that would be valuable for brand positioning, market entry, or competitive advantage.

  ## Synthesis Rules
  - **Synthesize, do not summarize.** Connect findings across sources into coherent insights. Do not write source-by-source summaries.
  - **Prioritize** recent data (2024-2025) over older data, quantitative evidence over anecdotal claims, authoritative sources (industry reports, government data, trade publications) over opinion pieces.
  - **Cite every factual claim** using [N] notation mapped to the Sources section.
  - **Write for a business decision-maker** — focus on strategic implications ("so what?"), not academic detail.
  - If sources are contradictory, present both perspectives with their respective citations and note the disagreement.

  ## Hard Constraints
  - NEVER fabricate data, statistics, market figures, or citations.
  - NEVER cite a source that is not in the provided source material.
  - NEVER create a theme section that has no supporting data from the sources.
  - If sources are insufficient for comprehensive analysis, state explicitly what information is missing and why it matters.

  ## Output Format
  Return EXACTLY this markdown structure:

  ```markdown
  ## Research: [Topic Title]

  ### Executive Summary
  [2-3 sentences. Lead with the single most actionable insight for brand strategy. Include the most impactful data point.]

  ### Key Findings
  - [Finding with specific data/evidence] [1]
  - [Finding with specific data/evidence] [2][3]
  - [Finding with specific data/evidence] [4]
  [4-8 findings maximum. Each MUST include a specific data point, percentage, or concrete evidence — not vague observations.]

  ### Detailed Analysis

  #### [Theme 1 — e.g., Market Size & Growth]
  [Analysis paragraph connecting findings across multiple sources] [1][2]

  #### [Theme 2 — e.g., Consumer Behavior Shifts]
  [Analysis paragraph connecting findings across multiple sources] [3][4]

  #### [Theme 3 — e.g., Competitive Landscape]
  [Analysis paragraph connecting findings across multiple sources] [5][6]

  [2-5 themes based on available content. Do not pad with thin analysis.]

  ### Strategic Implications
  - [Actionable implication for brand strategy — specific opportunity or threat]
  - [Actionable implication for brand strategy — specific opportunity or threat]
  - [Actionable implication for brand strategy — specific opportunity or threat]
  [Each implication must be specific enough to inform a brand positioning or market entry decision.]

  ### Information Gaps
  [List specific data points or topics NOT adequately covered by sources but valuable for brand strategy decisions. If coverage is adequate, state: "Sources provided adequate coverage for the research scope."]

  ### Sources
  [1] [Page Title](URL)
  [2] [Page Title](URL)
  [Only sources actually cited in the analysis. Do not list uncited sources.]
  ```

  ## Self-Verification
  Before returning your output, verify ALL of the following:
  - [ ] Every [N] citation maps to a real source listed in the Sources section
  - [ ] No data point or statistic is stated without a citation
  - [ ] Executive Summary leads with the single most actionable insight
  - [ ] Key Findings contain specific data points, not vague observations
  - [ ] Strategic Implications are specific enough to inform a brand strategy decision
  - [ ] No fabricated data or citations appear anywhere in the output

  If any check fails, revise before responding.
  """
  ```
- **Acceptance Criteria**:
  - [ ] Output follows structured markdown format
  - [ ] Citations map to actual source URLs
  - [ ] Synthesis connects findings, not just lists them
  - [ ] Executive summary captures key takeaways

#### Requirement 3 - Prompt Package Init
- **Requirement**: `__init__.py` re-exports prompt constants
- **Implementation**:
  - `src/prompts/research/__init__.py`
  ```python
  from prompts.research.generate_queries import GENERATE_QUERIES_PROMPT
  from prompts.research.synthesize_research import SYNTHESIZE_RESEARCH_PROMPT

  __all__ = [
      "GENERATE_QUERIES_PROMPT",
      "SYNTHESIZE_RESEARCH_PROMPT",
  ]
  ```
- **Acceptance Criteria**:
  - [ ] Both prompts importable from `prompts.research`

### Component 2: deep_research Function

#### Requirement 1 - Pipeline Orchestration
- **Requirement**: Plain function (no `@tool` decorator) that orchestrates the 4-step research pipeline. Follows codebase convention — `search_web` and `scrape_web_content` are both plain functions, `deep_research` follows the same pattern.
- **Implementation**:
  - `src/shared/src/shared/agent_tools/research/deep_research.py`
  ```python
  import json
  import traceback
  from concurrent.futures import ThreadPoolExecutor
  from typing import Any, Dict, List, Optional
  from urllib.parse import urlparse

  from loguru import logger

  from config.system_config import SETTINGS
  from prompts.research.generate_queries import GENERATE_QUERIES_PROMPT
  from prompts.research.synthesize_research import SYNTHESIZE_RESEARCH_PROMPT
  from shared.agent_tools.crawler.crawl_web import scrape_web_content
  from shared.agent_tools.search.search_web import search_web
  from shared.model_clients.llm.google import GoogleAIClientLLM, GoogleAIClientLLMConfig


  # =========================================================================
  # Depth Configuration
  # =========================================================================

  DEPTH_CONFIG = {
      "quick": {"num_queries": 2, "crawl_top_n": 2, "max_chars_per_page": 4000},
      "standard": {"num_queries": 4, "crawl_top_n": 4, "max_chars_per_page": 6000},
      "comprehensive": {
          "num_queries": 5,  # MAX: search_web enforces MAX_QUERIES=5
          "crawl_top_n": 6,
          "max_chars_per_page": 8000,
      },
  }

  MAX_CRAWL_WORKERS = 3  # Concurrent crawling threads


  # =========================================================================
  # Main Function
  # =========================================================================


  def deep_research(
      topic: str,
      context: Optional[str] = None,
      depth: str = "standard",
  ) -> str:
      """
      Conduct deep research on a topic by searching the web,
      crawling top results, and synthesizing findings.

      This function orchestrates a 4-step pipeline:
          1. LLM generates targeted search queries from the topic
          2. search_web executes queries across multiple providers
          3. scrape_web_content crawls top URLs with relevance filtering
          4. LLM synthesizes all content into structured research

      Use for complex research questions that require synthesis from
      multiple sources — market trends, industry analysis, consumer
      behavior, competitive landscape.

      For simple factual queries, use search_web instead.

      Args:
          topic: Research question or topic
              (e.g., "F&B market trends Vietnam 2026")
          context: Additional context to guide research
              (e.g., "Focus on specialty coffee segment in HCMC")
          depth: Research depth level:
              - "quick": 2 queries, 2 pages (fast overview)
              - "standard": 4 queries, 4 pages (balanced, default)
              - "comprehensive": 5 queries, 6 pages (thorough)

      Returns:
          Structured markdown research summary with key findings,
          detailed analysis, implications, and source citations.
          Returns error message string if pipeline fails entirely.
      """
      logger.info(
          f"Starting deep research: topic='{topic}', "
          f"depth='{depth}'"
      )

      config = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["standard"])

      try:
          # Step 1: Generate targeted search queries
          queries = _generate_search_queries(
              topic=topic,
              context=context,
              num_queries=config["num_queries"],
          )
          logger.info(f"Generated {len(queries)} search queries")

          # Step 2: Execute web search
          search_results = search_web(
              queries=queries,
              number_of_results=10,
          )
          logger.info("Web search completed")

          # Step 3: Crawl top pages with relevance filtering
          ranked_urls = _rank_and_deduplicate_urls(
              search_results=search_results,
              topic=topic,
              top_n=config["crawl_top_n"],
          )
          crawled_pages = _crawl_pages_concurrent(
              urls=ranked_urls,
              topic=topic,
              max_chars=config["max_chars_per_page"],
          )
          logger.info(
              f"Crawled {len(crawled_pages)} pages "
              f"(of {len(ranked_urls)} attempted)"
          )

          if not crawled_pages:
              logger.warning(
                  "No pages crawled successfully, "
                  "synthesizing from search snippets only"
              )

          # Step 4: Synthesize into research summary
          result = _synthesize_research(
              topic=topic,
              context=context,
              search_results=search_results,
              crawled_pages=crawled_pages,
          )
          logger.info(
              f"Deep research completed: "
              f"{len(result)} characters"
          )
          return result

      except Exception as e:
          logger.error(f"Deep research failed: {e}")
          logger.error(traceback.format_exc())
          return (
              f"Deep research failed for topic '{topic}': {e}. "
              f"Try using search_web for a simpler search."
          )


  # =========================================================================
  # Step 1: Query Generation
  # =========================================================================


  def _generate_search_queries(
      topic: str,
      context: Optional[str],
      num_queries: int,
  ) -> List[str]:
      """
      Use LLM to generate diverse search queries from the topic.

      Falls back to the original topic as a single query if LLM
      call or JSON parsing fails.

      Args:
          topic: Research topic.
          context: Additional context.
          num_queries: Number of queries to generate.

      Returns:
          List of search query strings.
      """
      try:
          llm = GoogleAIClientLLM(
              config=GoogleAIClientLLMConfig(
                  model="gemini-3-flash-preview",
                  api_key=SETTINGS.GEMINI_API_KEY,
                  thinking_level="medium",
                  response_mime_type="application/json",
              )
          )

          prompt = (
              GENERATE_QUERIES_PROMPT
              .replace("{{topic}}", topic)
              .replace("{{context}}", context or "No additional context")
              .replace("{{num_queries}}", str(num_queries))
          )

          result = llm.complete(prompt, temperature=0.3).text
          queries = json.loads(result.strip())

          if isinstance(queries, list) and queries and all(
              isinstance(q, str) for q in queries
          ):
              return queries[:num_queries]

          logger.warning(
              f"LLM returned invalid format: {type(queries)}, "
              f"falling back to topic as query"
          )
          return [topic]

      except Exception as e:
          logger.warning(
              f"Query generation failed: {e}, "
              f"using topic as query"
          )
          return [topic]


  # =========================================================================
  # Step 2 Helper: URL Ranking & Deduplication
  # =========================================================================


  def _rank_and_deduplicate_urls(
      search_results: Dict[str, Any],
      topic: str,
      top_n: int,
  ) -> List[Dict[str, str]]:
      """
      Extract, deduplicate, and rank URLs from search results.

      Deduplicates by domain (keeps first occurrence) and ranks by
      a simple relevance heuristic: snippet keyword match count.

      Args:
          search_results: Raw output from search_web().
          topic: Research topic for relevance scoring.
          top_n: Maximum number of URLs to return.

      Returns:
          List of dicts with "url", "title", "snippet" keys,
          ranked by relevance.
      """
      seen_domains: set = set()
      candidates: List[Dict[str, Any]] = []
      # Filter short stop words to avoid inflating scores
      topic_words = {w for w in topic.lower().split() if len(w) > 3}

      queries_data = search_results.get("queries", {})
      for query_key, query_data in queries_data.items():
          results = query_data.get("results", [])
          for r in results:
              url = r.url if hasattr(r, "url") else r.get("url", "")
              title = r.title if hasattr(r, "title") else r.get("title", "")
              snippet = (
                  r.snippet if hasattr(r, "snippet")
                  else r.get("snippet", "")
              )

              if not url:
                  continue

              # Deduplicate by domain
              domain = urlparse(url).netloc
              if domain in seen_domains:
                  continue
              seen_domains.add(domain)

              # Relevance score: count topic keyword matches in snippet
              snippet_lower = snippet.lower()
              score = sum(
                  1 for w in topic_words if w in snippet_lower
              )

              candidates.append({
                  "url": url,
                  "title": title,
                  "snippet": snippet,
                  "score": score,
              })

      # Sort by relevance score descending
      candidates.sort(key=lambda x: x["score"], reverse=True)

      return [
          {"url": c["url"], "title": c["title"], "snippet": c["snippet"]}
          for c in candidates[:top_n]
      ]


  # =========================================================================
  # Step 3: Concurrent Crawling
  # =========================================================================


  def _crawl_pages_concurrent(
      urls: List[Dict[str, str]],
      topic: str,
      max_chars: int,
  ) -> List[Dict[str, str]]:
      """
      Crawl multiple URLs concurrently using scrape_web_content
      with relevant mode for query-filtered content extraction.

      Args:
          urls: List of URL dicts with "url", "title", "snippet".
          topic: Research topic (used as query for relevant filtering).
          max_chars: Maximum characters per page (safety truncation).

      Returns:
          List of dicts with "url", "title", "content" for
          successfully crawled pages.
      """
      if not urls:
          return []

      crawled: List[Dict[str, str]] = []

      def _crawl_single(url_info: Dict[str, str]) -> Optional[Dict[str, str]]:
          try:
              result = scrape_web_content(
                  web_url=url_info["url"],
                  mode="relevant",
                  query=topic,
              )
              content = result.content.strip()
              if not content:
                  return None

              # Safety truncation
              if len(content) > max_chars:
                  content = content[:max_chars] + "\n\n[Content truncated]"

              return {
                  "url": url_info["url"],
                  "title": url_info["title"],
                  "content": content,
              }
          except Exception as e:
              logger.warning(
                  f"Failed to crawl {url_info['url']}: {e}"
              )
              return None

      with ThreadPoolExecutor(max_workers=MAX_CRAWL_WORKERS) as executor:
          # Submit in ranked order and collect in same order to preserve relevance ranking
          futures = [executor.submit(_crawl_single, url_info) for url_info in urls]
          for future in futures:
              result = future.result()
              if result is not None:
                  crawled.append(result)

      return crawled


  # =========================================================================
  # Step 4: Research Synthesis
  # =========================================================================


  def _synthesize_research(
      topic: str,
      context: Optional[str],
      search_results: Dict[str, Any],
      crawled_pages: List[Dict[str, str]],
  ) -> str:
      """
      Synthesize search results and crawled content into a structured
      research summary using LLM.

      Args:
          topic: Research topic.
          context: Additional context.
          search_results: Raw output from search_web().
          crawled_pages: List of crawled page dicts with
              "url", "title", "content".

      Returns:
          Structured markdown research summary with citations.
      """
      # Format search snippets
      snippets_text = _format_search_snippets(search_results)

      # Format crawled content
      crawled_text = _format_crawled_content(crawled_pages)

      llm = GoogleAIClientLLM(
          config=GoogleAIClientLLMConfig(
              model="gemini-2.5-flash-lite",
              api_key=SETTINGS.GEMINI_API_KEY,
              thinking_budget=2000,
              response_mime_type="text/plain",
          )
      )

      prompt = (
          SYNTHESIZE_RESEARCH_PROMPT
          .replace("{{topic}}", topic)
          .replace("{{context}}", context or "No additional context")
          .replace("{{search_snippets}}", snippets_text)
          .replace("{{crawled_content}}", crawled_text)
      )

      result = llm.complete(prompt, temperature=0.2).text
      return result.strip()


  def _format_search_snippets(
      search_results: Dict[str, Any],
  ) -> str:
      """Format search results into readable text for synthesis prompt."""
      lines: List[str] = []
      queries_data = search_results.get("queries", {})
      for query_key, query_data in queries_data.items():
          lines.append(f"### Query: {query_key}")
          results = query_data.get("results", [])
          for r in results:
              title = (
                  r.title if hasattr(r, "title") else r.get("title", "")
              )
              url = r.url if hasattr(r, "url") else r.get("url", "")
              snippet = (
                  r.snippet if hasattr(r, "snippet")
                  else r.get("snippet", "")
              )
              lines.append(f"- [{title}]({url}): {snippet}")
          lines.append("")
      return "\n".join(lines)


  def _format_crawled_content(
      crawled_pages: List[Dict[str, str]],
  ) -> str:
      """Format crawled pages into labeled sections for synthesis prompt."""
      if not crawled_pages:
          return "(No pages were crawled successfully)"
      sections: List[str] = []
      for i, page in enumerate(crawled_pages, 1):
          sections.append(
              f"--- Source [{i}]: {page['title']} ---\n"
              f"URL: {page['url']}\n\n"
              f"{page['content']}\n"
          )
      return "\n".join(sections)
  ```
- **Acceptance Criteria**:
  - [ ] Function signature: `deep_research(topic, context, depth) -> str`
  - [ ] No `@tool` decorator — plain function matching codebase convention
  - [ ] Step 1: Generates diverse search queries via LLM (falls back to topic if fails)
  - [ ] Step 2: Uses `search_web()` for batch search
  - [ ] Step 3: Concurrent crawling via `scrape_web_content(mode="relevant")`
  - [ ] Step 4: LLM synthesis with `thinking_budget=2000` for deeper reasoning
  - [ ] URL deduplication by domain + relevance ranking
  - [ ] Graceful error handling at every step (no crash, always returns string)
  - [ ] Logging at each step via loguru

#### Requirement 2 - Package Exports
- **Requirement**: Re-export from package `__init__.py` and update agent_tools root
- **Implementation**:
  - `src/shared/src/shared/agent_tools/research/__init__.py`
  ```python
  from shared.agent_tools.research.deep_research import deep_research

  __all__ = ["deep_research"]
  ```
  - Update `src/shared/src/shared/agent_tools/__init__.py` — add:
  ```python
  from shared.agent_tools.research.deep_research import deep_research
  ```
- **Acceptance Criteria**:
  - [ ] `from shared.agent_tools import deep_research` works
  - [ ] `from shared.agent_tools.research import deep_research` works

------------------------------------------------------------------------

## 🧪 Test Execution Log

> **Agent**: Record actual test results here as you run them.
> Do not mark a test as Passed until you have run it and seen the output.

### Test 1: Standard Depth Research
- **Purpose**: Verify full pipeline produces quality structured research
- **Steps**:
  1. Call `deep_research("specialty coffee market trends Vietnam 2026")`
  2. Verify result is structured markdown with all required sections
  3. Verify result has Key Findings + Detailed Analysis + Sources sections
  4. Verify citations [N] map to real URLs in Sources section
- **Expected Result**: 500+ word summary with 3+ source citations, structured markdown following output template
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 2: Quick Depth (Fast Overview)
- **Purpose**: Verify quick depth produces concise result faster
- **Steps**:
  1. Call `deep_research("Gen Z coffee consumption Vietnam", depth="quick")`
  2. Measure execution time
  3. Verify result is shorter but still structured
- **Expected Result**: Complete within 20s, 200+ word summary with 2+ citations
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 3: Comprehensive Depth (Thorough Analysis)
- **Purpose**: Verify comprehensive depth produces detailed analysis
- **Steps**:
  1. Call `deep_research("F&B consumer behavior trends Southeast Asia 2025-2026", depth="comprehensive")`
  2. Verify more sources and deeper analysis
- **Expected Result**: 800+ word summary with 5+ citations, multiple analysis sections
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 4: Context-Guided Research
- **Purpose**: Verify context parameter meaningfully shapes results
- **Steps**:
  1. Call with context: `deep_research("F&B market trends Vietnam", context="Focus on bubble tea and healthy drinks segment in Ho Chi Minh City")`
  2. Verify results are filtered toward the context
- **Expected Result**: Research focused on bubble tea/healthy drinks in HCMC, not generic F&B
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 5: Error Handling — All Crawls Fail
- **Purpose**: Verify graceful degradation when pages can't be crawled
- **Steps**:
  1. Simulate scenario where all URLs fail to crawl (e.g., Crawl4AI service down)
  2. Verify function still returns synthesis from search snippets
- **Expected Result**: Returns summary based on search snippets with warning, does not crash
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 6: Query Generation Fallback
- **Purpose**: Verify fallback when LLM query generation fails
- **Steps**:
  1. Simulate LLM failure for query generation
  2. Verify function falls back to using topic as single query
- **Expected Result**: Pipeline continues with topic as query, still produces result
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📊 Decision Log

> **Agent**: Document every significant decision made during implementation.
> Include the options considered, the trade-off, and the final choice.

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | LLM model for query gen | gemini-3-flash-preview vs gemini-2.5-flash | gemini-3-flash-preview | JSON output reliability critical for query gen; newer model with `response_mime_type="application/json"` + `thinking_level="medium"` ensures valid JSON array output |
| 1b | LLM model for synthesis | gemini-2.5-flash-lite vs gemini-2.5-flash | gemini-2.5-flash-lite | Faster, cheaper for synthesis; `thinking_budget=2000` provides sufficient reasoning for research synthesis without premium model cost |
| 2 | Concurrency approach | asyncio vs ThreadPoolExecutor | ThreadPoolExecutor | scrape_web_content is sync; ThreadPoolExecutor wraps sync calls cleanly without async complexity |
| 3 | URL deduplication strategy | By exact URL vs by domain | By domain | Dedup by domain gets diverse sources; exact URL dedup still allows multiple pages from same site |
| 4 | Crawl failure handling | Fail entire pipeline vs degrade gracefully | Degrade gracefully | Even with 0 crawled pages, search snippets can produce useful (if shallow) synthesis |
| 5 | Prompt approach (no Perplexity) | Perplexity Sonar API vs search+crawl+LLM pipeline | search+crawl+LLM pipeline | No additional API key dependency; reuses existing tools; user gets full control |

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation and all tests pass.

### What Was Implemented

**Components Completed**:
- [ ] [Component 1]: Research Prompts (query generation + synthesis)
- [ ] [Component 2]: deep_research pipeline function

**Files Created/Modified**:
```
# New files
src/prompts/research/
├── __init__.py                    # Re-exports prompt constants
├── generate_queries.py            # GENERATE_QUERIES_PROMPT
└── synthesize_research.py         # SYNTHESIZE_RESEARCH_PROMPT

src/shared/src/shared/agent_tools/research/
├── __init__.py                    # Re-exports deep_research
└── deep_research.py               # Pipeline orchestration

# Modified files
src/shared/src/shared/agent_tools/__init__.py    # Add deep_research export
```

**Key Features Delivered**:
1. **Multi-depth research pipeline**: quick/standard/comprehensive with configurable query count and crawl depth
2. **Structured synthesis with citations**: Executive summary → Key findings → Detailed analysis → Strategic implications → Sources

### Technical Highlights

**Architecture Decisions** (see Decision Log for details):
- Plain function (no @tool), ThreadPoolExecutor for concurrency, domain-level URL dedup

**Performance / Quality Results**:
- [Quick depth latency]: [Observed result — target: <20s]
- [Standard depth latency]: [Observed result — target: <45s]
- [Comprehensive depth latency]: [Observed result — target: <90s]

**Documentation Checklist**:
- [ ] All functions have comprehensive docstrings (purpose, args, returns)
- [ ] Complex business logic has inline comments
- [ ] Module-level docstrings explain purpose and usage
- [ ] Type hints complete and accurate

### Validation Results

**Test Results**:
- [ ] All tests in Test Execution Log: ✅ Passed
- [ ] Edge cases and error scenarios covered (crawl failures, LLM failures)
- [ ] No regressions in search_web or scrape_web_content

**Deployment Notes**:
- No new dependencies — uses existing google-genai, search_web, scrape_web_content
- Requires GEMINI_API_KEY in environment (already required system-wide)
- New prompt files in `src/prompts/research/` must be committed

------------------------------------------------------------------------
