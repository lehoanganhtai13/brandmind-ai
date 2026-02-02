# BrandMind AI - Complete Vision & Architecture Document

> **Purpose**: This document captures the complete vision, architecture, and design decisions for BrandMind AI. It serves as a reference for any AI agent working on this project to understand the full context without needing to ask the user again.

**Last Updated**: 2026-02-03
**Status**: Baseline approved, ready for implementation

---

## 1. Project Overview

### 1.1 What is BrandMind?

BrandMind AI is an **AI Brand Manager who also acts as a Mentor**. The main agent operates as a professional Brand Manager with real expertise and execution capabilities, while simultaneously mentoring/teaching the user through the process.

**Key distinction:**

- ❌ NOT "mentor for brand managers" (teaching brand managers)
- ✅ IS "Brand Manager + Mentor" (an expert who teaches while executing)

Unlike traditional AI assistants that just generate outputs, BrandMind is designed to:

1. **TEACH** users the branding process (like a mentor training a junior employee)
2. **GUIDE** through each phase with explanations
3. **EXECUTE** the actual work with professional quality
4. **ITERATE** based on user feedback until the strategy is complete

### 1.2 Target Users

- Junior marketers who lack branding expertise
- Small business owners without marketing background
- Startup founders who need branding strategy
- Marketing students learning professional processes

### 1.3 Core Philosophy: "Mentor-Execute Loop"

BrandMind operates in a **Dual-Mode Loop per Phase**:

```
For each phase in Branding Strategy:
    ┌─────────────────────────────────────────┐
    │ MENTOR MODE                             │
    │ • Explain WHY this phase matters        │
    │ • Present WHAT we'll do                 │
    │ • Gather user context (if needed)       │
    │ • Ask clarifying questions              │
    └──────────────────┬──────────────────────┘
                       ▼
    ┌─────────────────────────────────────────┐
    │ EXECUTOR MODE                           │
    │ • Research using KG + Web tools         │
    │ • Analyze and synthesize findings       │
    │ • Generate output for this phase        │
    │ • Present with explanation              │
    └──────────────────┬──────────────────────┘
                       ▼
    ┌─────────────────────────────────────────┐
    │ FEEDBACK LOOP                           │
    │ • User reviews output                   │
    │ • Collects feedback/corrections         │
    │ • Refine until approved                 │
    └──────────────────┬──────────────────────┘
                       ▼
              [Move to next phase]
```

**Key Insight**: This is NOT "explain everything first, then execute all at once". Each phase has its own mentor-execute cycle.

---

## 2. Agent Architecture

### 2.1 Architecture Philosophy

BrandMind follows a **Custom Planner-Executor Pattern** inspired by Claude Code:

**Key Difference from Traditional Planner-Executor:**

| Aspect          | Traditional Pattern                                 | BrandMind Pattern                                   |
| --------------- | --------------------------------------------------- | --------------------------------------------------- |
| Main Agent Role | Planner/Manager only (coordinates, doesn't execute) | Brand Manager (CAN do everything itself)            |
| Execution       | Sub-agents do ALL execution                         | Main agent executes directly, delegates selectively |
| Delegation      | Mandatory (planner can't execute)                   | Optional (for context efficiency)                   |
| Similar to      | Manager → Workers hierarchy                        | Claude Code (self-sufficient but delegates)         |

```
┌───────────────────────────────────────────────────────────────────┐
│                         MAIN AGENT                                │
│  "Brand Manager" - Gemini 2.5 Flash (or higher)                   │
│  • CAN execute everything directly (self-sufficient)              │
│  • Plans AND executes (not just coordinator)                      │
│  • Delegates SELECTIVELY to keep main context clean               │
└───────────────────────────────────────────────────────────────────┘
          │
          │ Delegates via "Task" tool
          ▼
┌───────────────────────────────────────────────────────────────────┐
│                       SUB-AGENTS                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │ Specialized     │  │ Specialized     │  │ General         │    │
│  │ Sub-Agent 1     │  │ Sub-Agent 2     │  │ Sub-Agent       │    │
│  │ (e.g., Market   │  │ (e.g., Visual   │  │ (Clone of main  │    │
│  │  Research)      │  │  Identity)      │  │  agent, limited)│    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
└───────────────────────────────────────────────────────────────────┘
```

**Why delegate if main agent CAN do everything?**

Same reason Claude Code delegates to `general_agent` even though it could do the task itself:

1. **Context Window Efficiency** - Sub-agent runs in isolated context, keeps main agent's context clean for high-level reasoning
2. **Known/Repetitive Tasks** - Tasks that follow predictable patterns (e.g., "search web for competitor X", "summarize these documents") don't need main agent's full reasoning
3. **Specialized Processing** - Some tasks benefit from focused prompts (e.g., visual identity generation with specialized system prompt)

**Delegation Decision Rule:**

```
IF task is:
  - Known pattern / repetitive workflow
  - OR requires specialized sub-agent capability
  - OR would pollute main context with unnecessary details
THEN: Delegate to sub-agent
ELSE: Main agent executes directly
```

### 2.3 Tool Distribution Strategy

**APPROVED APPROACH**: Hybrid with ToolSearch (Option C)

Main agent retains CAPABILITY to use all tools (true to "manager can do everything") but uses **ToolSearch** to load specialized tools on-demand rather than having all tools in context.

**Why not give main agent ALL tools directly?**

| Approach                                           | Pros                      | Cons                                                        |
| -------------------------------------------------- | ------------------------- | ----------------------------------------------------------- |
| **A: All tools always loaded**               | Simple, always capable    | Context bloat (~200-500 tokens/tool), slower reasoning      |
| **B: Specialized tools only for sub-agents** | Lean context              | Main agent CAN'T do specialized tasks (violates philosophy) |
| **C: ToolSearch (Chosen)**                   | Lean + capable + flexible | Slightly more complex                                       |

**Tool Categories:**

```yaml
Main Agent:
  core_tools:                    # Always available
    - search_kg                  # Knowledge Graph search
    - search_docs                # Document library search
    - search_web                 # Internet search
    - fetch_url                  # Web page scraping
    - task                       # Delegate to sub-agents
    - tool_search                # Find & load specialized tools
    - load_skill                 # Load skill instructions
  
  loadable_tools:                # Available via tool_search
    - generate_image             # Visual asset creation
    - get_trending_keywords      # SEO/keyword research
    - analyze_competitors        # Competition analysis
    - create_color_palette       # Brand colors
    - search_fonts               # Typography research
    - ... (extensible)

Specialized Sub-Agents:
  visual_identity_agent:
    tools:                       # Pre-loaded (optimized context)
      - generate_image
      - create_color_palette
      - search_fonts
      - create_moodboard
  
  market_research_agent:
    tools:
      - get_trending_keywords
      - analyze_competitors
      - search_web
      - fetch_url
```

**Flow when main agent needs specialized tool:**

```
Main Agent needs to create visual asset
         │
         ▼
┌────────────────────────────────────────┐
│ tool_search("visual asset creation")   │
│ → Returns: ["generate_image", ...]     │
└────────────────────────────────────────┘
         │
         ├─── Simple task → Load tool, use directly
         │    (e.g., single image for presentation)
         │
         └─── Complex task → Delegate to visual_identity_agent
              (e.g., full brand visual system)
```

**Decision Logic (pseudocode):**

```python
if task.is_simple and task.type in loadable_tools:
    tool = tool_search(task.type)
    result = execute(tool, task)
elif task.is_complex or task.requires_specialized_context:
    result = delegate_to_subagent(task)
```

**Human Analogy**: Real managers *know* they can learn any tool if needed, but *choose* to delegate based on complexity and time efficiency. BrandMind works the same way.

### 2.4 Context Engineering Components

The main agent is enhanced with several context engineering techniques:

| Component                        | Purpose                                                                         |
| -------------------------------- | ------------------------------------------------------------------------------- |
| **Skills**                 | Procedural knowledge for specific workflows (phases, checklists, quality gates) |
| **Knowledge Graph Search** | Domain expertise from marketing textbooks (Kotler, etc.)                        |
| **Document Search**        | Search through indexed documents for reference                                  |
| **Web Search + Fetch**     | Real-time information from the internet                                         |
| **ToolSearch**             | Find & load specialized tools on-demand (context efficient)                     |
| **Context Editing**        | Manage context window efficiently                                               |

---

## 3. Knowledge Graph System

### 3.1 Overview

The Knowledge Graph is a critical component that provides **domain expertise** to the agent. It's built from professional marketing textbooks and resources.

### 3.2 5-Stage Pipeline

```
Stage 1: Document Mapping (The Cartographer)
         PDF → Markdown → Structure Map (chapters, sections, line numbers)
     
Stage 2: Chunking
         Structure Map → Semantic Chunks (respecting section boundaries)
     
Stage 3: Entity/Relation Extraction
         Chunks → Entities + Relationships → FalkorDB Graph
     
Stage 4: Indexing
         Entities/Relations → Milvus Vector Embeddings
     
Stage 5: Retrieval (The Retriever)
         Query → PPR + Dijkstra → Relevant Knowledge Paths
```

### 3.3 Data Sources (Planned)

| Document                                 | Status     | Purpose                     |
| ---------------------------------------- | ---------- | --------------------------- |
| Principles of Marketing 17th Ed (Kotler) | ✅ Indexed | Core marketing fundamentals |
| TBD: Brand Strategy Book                 | 🔄 Planned | Deep branding knowledge     |
| TBD: Visual Identity Guide               | 🔄 Planned | Design principles           |
| TBD: Case Studies Collection             | 🔄 Planned | Real-world examples         |

### 3.4 Current KG Stats

- **EntityDescriptions**: ~25,000+ embeddings
- **RelationDescriptions**: ~23,000+ embeddings
- **Graph Database**: FalkorDB with entity nodes + relationship edges

---

## 4. Hybrid Skills + KG Approach

### 4.1 The Decision

**APPROVED APPROACH**: Hybrid Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                  HYBRID ARCHITECTURE                              │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│   SKILL LAYER (Process Skeleton)              KG LAYER            │
│   ─────────────────────────────              ─────────            │
│   • WHAT phases to execute          ◄───►    • HOW to do it       │
│   • WHEN to move forward                     • WHY it works       │
│   • Quality gates/checklists                 • Domain depth       │
│   • Required inputs/outputs                  • Expert reasoning   │
│                                                                   │
│   ┌─────────────────────┐                   ┌───────────────────┐ │
│   │ branding-strategy   │     Search        │ Marketing KG      │ │
│   │ Skill (skeleton)    │ ◄──────────────── │ 25K+ entities     │ │
│   └─────────────────────┘                   └───────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### 4.2 What Skills Contain (Skeleton Only)

Skills define **WHAT** not **HOW**:

```markdown
# Phase 2: Brand Positioning

## Required Inputs (from Phase 1)
- Business context
- Target audience profile  
- Competitive landscape

## Required Outputs
- [ ] Competitive alternatives list
- [ ] Unique attributes (3-5 items)
- [ ] Value mapping (attribute → benefit → outcome)
- [ ] Category positioning statement

## Search KG For (HOW)
1. "positioning framework methodology"
2. "competitive differentiation strategies"
3. "value proposition development"

## Quality Criteria
- [ ] Differentiation is clear and defensible
- [ ] Aligns with target audience pain points
- [ ] Feasible given business resources
```

### 4.3 What KG Provides (Domain Knowledge)

When agent needs specific knowledge:

```python
# Agent searches KG for methodology
kg_results = await search_kg("April Dunford positioning framework")

# Returns structured knowledge:
# - 5-step positioning process
# - Examples from real brands
# - Common pitfalls to avoid
# - How to identify unique attributes

# Agent applies this knowledge to user's specific situation
```

### 4.4 Why Hybrid Works

| Benefit                | Explanation                                               |
| ---------------------- | --------------------------------------------------------- |
| **Consistency**  | Skills ensure same phases, same checkpoints every project |
| **Flexibility**  | KG allows agent to adapt approach to situation            |
| **Evaluability** | Can test output quality at each phase checkpoint          |
| **Depth**        | 25K+ entities provide rich domain expertise               |
| **Efficiency**   | Skills loaded on-demand, KG queried as needed             |

---

## 5. Branding Strategy Workflow

### 5.1 High-Level Phases

Based on professional brand management practices:

```
Phase 1: Discovery & Research
         ├── Business context gathering
         ├── Target audience analysis
         └── Competitive landscape assessment

Phase 2: Brand Positioning
         ├── Identify competitive alternatives
         ├── Define unique attributes
         ├── Map value to outcomes
         └── Category positioning

Phase 3: Brand Messaging
         ├── Value proposition (one-liner)
         ├── Key benefits hierarchy
         ├── Feature-benefit-outcome mapping
         ├── Proof points

Phase 4: Visual Identity Direction
         ├── Brand personality definition
         ├── Visual style guidelines
         ├── Color/typography recommendations
         └── Mood board/references

Phase 5: Brand Guidelines & Implementation
         ├── Compile all brand elements
         ├── Create brand guidelines document
         ├── Implementation roadmap
         └── Measurement plan
```

### 5.2 User Experience Flow

**Scenario**: SME owner wants branding for new coffee shop

```
USER: I want to create a brand for my cafe

BRANDMIND (Mentor Mode):
"Chào bạn! Tôi sẽ hướng dẫn bạn qua quy trình phát triển thương hiệu 
chuyên nghiệp gồm 5 giai đoạn. Đầu tiên, chúng ta cần hiểu rõ về 
doanh nghiệp của bạn. 

Bạn có thể cho tôi biết về quán cafe của bạn không? 
- Vị trí ở đâu?
- Phục vụ ai là chính?
- Có gì đặc biệt so với các quán khác?"

USER: [Provides info...]

BRANDMIND (Mentor Mode):
"Tuyệt vời! Bước tiếp theo tôi sẽ phân tích đối thủ cạnh tranh 
xung quanh để hiểu rõ thị trường..."

BRANDMIND (Executor Mode):
[Searches web for nearby cafes, analyzes competitive landscape]
[Presents findings with clear explanations]

USER: [Reviews, gives feedback]

[Loop continues through all phases...]
```

**Workflow Demo:**

![BrandMind Chat Demo](/Users/lehoanganhtai/projects/brandmind-ai/media/workflow_demo.png)

### 5.3 Mentor Style Clarification

The "mentor" style is NOT lecturing theory:

❌ **Bad (Textbook style)**:

> "Positioning là việc xác định vị trí thương hiệu trong tâm trí khách hàng. Theo Philip Kotler, nó bao gồm 3 bước..."

✅ **Good (Team lead presenting to team)**:

> "Để cạnh tranh được với các quán cafe xung quanh, chúng ta cần xác định được điểm khác biệt của quán bạn. Việc này sẽ giúp khách hàng nhớ đến quán bạn khi họ nghĩ đến cafe. Tôi sẽ phân tích thị trường và đề xuất một số hướng đi..."

---

## 6. Evaluation Framework

### 6.1 Two-Track Evaluation

```
Track 1: E2E Autonomous Test
         └── Main agent runs alone (no human in loop)
         └── Tests: Can agent complete full workflow?
         └── Establishes agent "credibility" as an expert

Track 2: Simulated User Test
         └── AI user simulates real human interactions
         └── Tests: Can agent MENTOR effectively?
         └── Tests learning/teaching quality
```

### 6.2 Evaluation Layers

| Layer                           | What It Measures                        | Weight |
| ------------------------------- | --------------------------------------- | ------ |
| **Output Quality (OQ)**   | Final strategy correctness              | 30-40% |
| **Process Quality (PQ)**  | Workflow execution                      | 25-30% |
| **Learning Quality (LQ)** | Mentorship effectiveness (Track 2 only) | 20-30% |
| **Robustness Score (RS)** | Edge case handling                      | 10-15% |

### 6.3 Test Scenarios

Three types of brands to test:

1. **New Business** - Start from scratch, collect info on-the-fly
2. **Existing Brand** - Has history, needs refreshing
3. **Rebranding** - Major transformation

---

## 7. Technical Infrastructure

### 7.1 Current Tech Stack

| Component       | Technology                                      |
| --------------- | ----------------------------------------------- |
| Package Manager | uv                                              |
| LLM             | Gemini 2.5 Flash Lite / Pro                     |
| Vector DB       | Milvus                                          |
| Graph DB        | FalkorDB                                        |
| Web Search      | SearXNG (self-hosted), Perplexity, Tavily, Bing |
| Web Crawling    | Crawl4AI                                        |
| PDF Parsing     | LlamaParse                                      |
| Agent Framework | LangChain + DeepAgents                          |

### 7.2 Project Structure

```
brandmind-ai/
├── src/
│   ├── core/           # Core business logic
│   │   ├── knowledge_graph/   # KG building pipeline
│   │   └── retrieval/         # Search components
│   ├── shared/         # Shared utilities
│   │   ├── agent_tools/       # Tools for agents
│   │   ├── database_clients/  # DB connections
│   │   └── model_clients/     # LLM/Embedder clients
│   ├── cli/            # CLI commands
│   ├── prompts/        # System prompts
│   └── config/         # Configuration
├── tasks/              # Development task specifications
├── docs/               # Documentation
├── data/               # Data files
│   ├── documents/      # Source documents
│   └── parsed_documents/  # Processed documents
└── evaluation/         # Evaluation framework
```

### 7.3 CLI Commands

| Command                      | Purpose                                                                     |
| ---------------------------- | --------------------------------------------------------------------------- |
| `parse-docs`               | PDF → Markdown processing                                                  |
| `build-kg --stage <stage>` | Build knowledge graph (mapping, chunking, extraction, validation, indexing) |
| `brandmind`                | Interactive TUI interface                                                   |
| `brandmind ask`            | One-shot Q&A mode                                                           |
| `brandmind search-kg`      | Direct KG search                                                            |
| `brandmind search-docs`    | Document library search                                                     |

---

## 8. Next Steps & Roadmap

### 8.1 Immediate Next Steps

1. **Complete KG** - Add 3-4 more marketing documents
2. **Build `branding-strategy` skill** - Skeleton with phases, quality gates
3. **Implement main agent** - With hybrid Skills + KG approach
4. **Run evaluation** - Using defined evaluation framework

### 8.2 Future Enhancements

- [ ] Visual asset generation integration
- [ ] Multi-language support (Vietnamese primary)
- [ ] Brand guidelines document generation
- [ ] Real-time web research integration
- [ ] Collaboration features (multiple stakeholders)

---

## 9. Key Design Decisions Log

| Decision           | Choice                                  | Rationale                                     |
| ------------------ | --------------------------------------- | --------------------------------------------- |
| Agent architecture | Claude Code pattern (Main + Sub-agents) | Proven in production, maintains clean context |
| Skills vs KG       | Hybrid approach                         | Best of both: consistency + flexibility       |
| Tool distribution  | ToolSearch hybrid (Option C)            | Main can do all, but loads tools on-demand    |
| Mentor style       | Team lead presenting to team            | More practical than academic lecturing        |
| Evaluation         | Two-track (E2E + Simulated User)        | Tests both execution AND mentorship quality   |
| KG data source     | Marketing textbooks (Kotler, etc.)      | Authoritative, comprehensive foundation       |

---

## 10. References

- **Evaluation Plan**: `/evaluation/evaluation_plan.md`
- **Task Specifications**: `/tasks/task_*.md`
- **Marketing Skills**: `.gemini/antigravity/skills/marketing-*`
- **KG Documentation**: `/docs/brainstorm/`

---

*This document should be updated as the project evolves. Any AI agent working on BrandMind should read this first to understand the full context.*
