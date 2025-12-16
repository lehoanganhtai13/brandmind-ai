# Task 23: Inference CLI for Marketing Knowledge Base

## 📌 Metadata

- **Epic**: Marketing AI Assistant
- **Priority**: High
- **Estimated Effort**: 1 week
- **Team**: Backend
- **Related Tasks**: Task 22 (Baseline Comparison)
- **Blocking**: []
- **Blocked by**: @suneox

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [x] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [x] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] ✅ [Component 1](#component-1-prompts-module) - Prompts Module (Q&A Agent system prompt)
    - [x] ✅ [Component 2](#component-2-cli-structure--argument-parsing) - CLI Structure & Argument Parsing
    - [x] ✅ [Component 3](#component-3-pyprojecttoml-entry-point) - pyproject.toml Entry Point
    - [x] ✅ [Component 4](#component-4-ask-mode) - Ask Mode (Q&A Agent)
    - [x] ✅ [Component 5](#component-5-kg-search-mode) - KG Search Mode
    - [x] ✅ [Component 6](#component-6-document-search-mode) - Document Search Mode
- [/] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation
- [/] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **Existing CLIs**: `src/cli/parse_documents.py`, `src/cli/build_knowledge_graph.py`
- **Deep Agent Reference**: `evaluation/kg_tools_search_baseline_comparison.py`
- **Agent Tools**: `src/shared/src/shared/agent_tools/retrieval/`
- **Prompts Pattern**: `src/prompts/knowledge_graph/cartographer_system_prompt.py`

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Đã implement thành công Deep Agent với 2 tools (search_knowledge_graph, search_document_library) trong evaluation framework
- Cần có CLI dễ sử dụng để run inference: hỏi đáp, search KG, search document library
- Các CLIs hiện tại (parse_documents.py, build_knowledge_graph.py) dùng argparse với pattern đã proven
- **Prompts** được organize trong `src/prompts/` với pattern: `*_system_prompt.py`, `*_task_prompt.py`
- **Future Plan**: TUI mode giống Claude Code/Gemini CLI với branding "BRANDMIND AI" (sau khi hoàn thành backup/restore database theo docs/brainstorm/stage_4.md)

### Mục tiêu

Tạo CLI `src/cli/inference.py` để chạy inference với 3 modes:
1. **ask**: Deep Agent trả lời câu hỏi marketing (agentic reasoning)
2. **search-kg**: Trực tiếp search Knowledge Graph
3. **search-docs**: Trực tiếp search Document Library với đầy đủ filters

### Success Metrics / Acceptance Criteria

- **Usability**: CLI có help text rõ ràng, dễ sử dụng
- **Output**: User-friendly formatting với rich Console (panels, colors, markdown)
- **Functionality**: Cả 3 modes hoạt động đúng như expected
- **Consistency**: Follow same patterns như existing CLIs (argparse, async_main, loguru)
- **Extensibility**: Dễ dàng thêm modes mới (chat TUI trong tương lai)

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Multi-mode CLI**: Single entry point với subcommands cho mỗi mode
- Reuse code từ `evaluation/kg_tools_search_baseline_comparison.py`
- Extract Q&A Agent prompt vào `src/prompts/inference/qa_agent_system_prompt.py`
- User-friendly output với rich Console
- User-friendly output với rich Console

### Stack công nghệ

- **argparse**: Argument parsing với subparsers cho modes (consistent với existing CLIs)
- **asyncio**: Async execution cho database operations
- **loguru**: Logging (existing pattern)
- **rich**: Console formatting cho pretty output (panels, markdown, syntax highlighting)
- **langchain agents**: Deep Agent implementation (từ evaluation)

### Architecture

```
src/
├── prompts/
│   └── inference/                     # NEW: Inference prompts
│       ├── __init__.py
│       └── qa_agent_system_prompt.py  # Q&A Agent instruction
│
└── cli/
    └── inference.py                   # NEW: Main CLI với 3 modes
        ├── Mode: ask (Q&A Agent)
        │   ├── Input: --question "Marketing question"
        │   ├── Processing: create_qa_agent() + ainvoke()
        │   └── Output: Rich formatted answer with panels
        │
        ├── Mode: search-kg
        │   ├── Input: --query "concept query" [--max-results N]
        │   ├── Processing: search_knowledge_graph()
        │   └── Output: Entities, relationships, sources

# pyproject.toml entry:  brandmind = "cli.inference:main"
        │
        └── Mode: search-docs
            ├── Input: --query "text" [--book X] [--chapter Y] [--author Z] [--top-k N]
            ├── Processing: search_document_library()
            └── Output: Passages with sources
```

### Future TUI Design (Reference)

> **Note**: TUI sẽ implement sau khi hoàn thành database backup/restore (Stage 4)

Dựa trên Claude Code và Gemini CLI:

1. **ASCII Art Branding**: Large "BRANDMIND AI" banner khi khởi động
2. **Interactive Chat**: Real-time streaming responses
3. **Status Indicators**: Thinking, searching, generating
4. **Slash Commands**: `/help`, `/clear`, `/context`, `/cost`, etc.
5. **Tool Visualization**: Show tool calls and results inline
6. **Libraries**: textual, rich cho TUI implementation

### Issues & Solutions

1. **Code Duplication** → Extract prompt to `src/prompts/inference/`, reuse agent code
2. **Long Agent Output** → Use rich Console với Markdown rendering và panels
3. **Error Handling** → Graceful error messages for DB connection issues

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Prompts Module**

1. **Create Prompts Structure**
   - Create `src/prompts/inference/__init__.py`
   - Create `qa_agent_system_prompt.py` với QA_AGENT_SYSTEM_PROMPT từ evaluation

### **Phase 2: Core CLI Implementation**

1. **Create CLI Structure**
   - Create `src/cli/inference.py` với argparse subcommands
   - Setup 3 modes: ask, search-kg, search-docs
   - Add proper help text và argument validation

2. **Implement Q&A Agent Mode (ask)**
   - Reuse `create_qa_agent()` logic từ evaluation
   - Import prompt từ `src/prompts/inference/`
   - Wire lên CLI với `--question` argument
   - Format output với rich Console panels

3. **Add pyproject.toml Entry**
   - Add `brandmind = "cli.inference:main"` to `[project.scripts]`
   - Reinstall package: `uv pip install -e .`

3. **Implement KG Search Mode (search-kg)**
   - Direct call to `search_knowledge_graph()` tool
   - Arguments: `--query`, `--max-results`
   - Pretty output với entities và relationships

4. **Implement Document Search Mode (search-docs)**
   - Direct call to `search_document_library()` tool  
   - Arguments: `--query`, `--book`, `--chapter`, `--author`, `--top-k`
   - Clean output với passage previews

### **Phase 3: Output Formatting**

1. **Rich Console Integration**
   - Panels với headers cho mỗi mode
   - Markdown rendering cho agent responses
   - Color coding cho sources và metadata

2. **Error Handling**
   - Database connection errors
   - API key validation
   - Empty results handling

------------------------------------------------------------------------

## 📋 Implementation Detail

### Component 1: Prompts Module

#### Requirement 1 - Q&A Agent System Prompt
- **Requirement**: Extract prompt từ evaluation vào src/prompts structure
- **Implementation**:
  - `src/prompts/inference/qa_agent_system_prompt.py`
  ```python
  """
  System prompt for Q&A Marketing Agent.
  This prompt guides the agent to use Knowledge Graph and Document Library
  tools for research-first, evidence-based marketing knowledge retrieval.
  """
  
  QA_AGENT_SYSTEM_PROMPT = """# ROLE & OBJECTIVE
  You are **The Marketing Knowledge Expert**...
  [Full prompt from evaluation/kg_tools_search_baseline_comparison.py]
  """
  ```
  - `src/prompts/inference/__init__.py`
  ```python
  """Inference-related prompts for CLI and agents."""
  
  from .qa_agent_system_prompt import QA_AGENT_SYSTEM_PROMPT
  
  __all__ = ["QA_AGENT_SYSTEM_PROMPT"]
  ```
- **Acceptance Criteria**:
  - [ ] Prompt importable: `from prompts.inference import QA_AGENT_SYSTEM_PROMPT`
  - [ ] Same content as evaluation file's DEEP_AGENT_INSTRUCTION

---

### Component 2: CLI Structure & Argument Parsing

#### Requirement 1 - CLI Entry Point with Rich Output
- **Requirement**: Create CLI với subcommands pattern và user-friendly output
- **Implementation**:
  - `src/cli/inference.py`
  ```python
  """
  CLI for running inference on the Marketing Knowledge Base.
  
  Modes:
      ask        - Ask marketing questions using Deep Agent (agentic reasoning)
      search-kg  - Search Knowledge Graph for concepts and relationships
      search-docs - Search Document Library for text passages
  
  Examples:
      brandmind ask -q "What is Marketing Myopia?"
      brandmind search-kg -q "customer value" -n 5
      brandmind search-docs -q "pricing" --chapter "Chapter 10"
  """
  
  import argparse
  import asyncio
  
  from loguru import logger
  from rich.console import Console
  from rich.markdown import Markdown
  from rich.panel import Panel
  
  console = Console()
  
  async def async_main() -> None:
      """Main CLI entry point for inference operations."""
      parser = argparse.ArgumentParser(
          description="Query the Marketing Knowledge Base.",
          formatter_class=argparse.RawDescriptionHelpFormatter,
          epilog="""
  Examples:
    brandmind ask -q "What is Marketing Myopia?"
    brandmind search-kg -q "customer value" -n 10
    brandmind search-docs -q "pricing strategy" --chapter "Chapter 10"
          """
      )
      
      subparsers = parser.add_subparsers(dest="mode", help="Inference mode")
      
      # Mode: ask
      ask_parser = subparsers.add_parser(
          "ask", 
          help="Ask a marketing question using Deep Agent"
      )
      ask_parser.add_argument(
          "--question", "-q", required=True,
          help="Marketing question to answer"
      )
      ask_parser.add_argument(
          "--verbose", "-v", action="store_true",
          help="Show agent thinking and tool calls"
      )
      
      # Mode: search-kg
      kg_parser = subparsers.add_parser(
          "search-kg", help="Search Knowledge Graph"
      )
      kg_parser.add_argument(
          "--query", "-q", required=True,
          help="Conceptual query about marketing"
      )
      kg_parser.add_argument(
          "--max-results", "-n", type=int, default=10,
          help="Maximum results (default: 10)"
      )
      
      # Mode: search-docs 
      docs_parser = subparsers.add_parser(
          "search-docs", help="Search Document Library"
      )
      docs_parser.add_argument(
          "--query", "-q", required=True,
          help="Text to search for"
      )
      docs_parser.add_argument("--book", "-b", help="Filter by book (exact)")
      docs_parser.add_argument("--chapter", "-c", help="Filter by chapter (partial)")
      docs_parser.add_argument("--author", "-a", help="Filter by author (exact)")
      docs_parser.add_argument(
          "--top-k", "-k", type=int, default=10,
          help="Number of results (default: 10)"
      )
      
      args = parser.parse_args()
      
      if args.mode is None:
          parser.print_help()
          return
      
      # Dispatch to handlers
      if args.mode == "ask":
          await run_ask_mode(args.question, verbose=args.verbose)
      elif args.mode == "search-kg":
          await run_kg_search_mode(args.query, args.max_results)
      elif args.mode == "search-docs":
          await run_docs_search_mode(
              args.query, args.book, args.chapter, args.author, args.top_k
          )
  
  def main() -> None:
      """Synchronous entry point."""
      asyncio.run(async_main())
  
  if __name__ == "__main__":
      main()
  ```
- **Acceptance Criteria**:
  - [ ] `python src/cli/inference.py --help` shows all 3 modes
  - [ ] Each mode has proper help text

---

### Component 3: pyproject.toml Entry Point

#### Requirement 1 - CLI Alias Registration
- **Requirement**: Add `brandmind` alias to project scripts
- **Implementation**:
  - `pyproject.toml`
  ```toml
  [project.scripts]
  parse-docs = "cli.parse_documents:main"
  build-kg = "cli.build_knowledge_graph:main"
  brandmind = "cli.inference:main"  # NEW
  ```
- **Acceptance Criteria**:
  - [ ] `brandmind --help` works after reinstall
  - [ ] All 3 modes accessible via `brandmind ask/search-kg/search-docs`

---

### Component 4: Ask Mode (Q&A Agent)

#### Requirement 1 - Ask Mode with Rich Output
- **Requirement**: Port Q&A Agent từ evaluation với beautiful output
- **Implementation**:
  ```python
  async def run_ask_mode(question: str, verbose: bool = False) -> None:
      """Run Q&A Agent mode to answer marketing questions."""
      from prompts.inference import QA_AGENT_SYSTEM_PROMPT
      
      console.print(Panel(
          f"[bold cyan]{question}[/bold cyan]",
          title="🎯 Question",
          border_style="cyan"
      ))
      
      with console.status("[bold green]Thinking...", spinner="dots"):
          try:
              answer = await qa_agent_answer(question)
              
              # Render answer as markdown
              console.print()
              console.print(Panel(
                  Markdown(answer),
                  title="📝 Answer",
                  border_style="green",
                  padding=(1, 2)
              ))
          except Exception as e:
              console.print(Panel(
                  f"[red]{e}[/red]",
                  title="❌ Error",
                  border_style="red"
              ))
              logger.exception("Q&A Agent failed")
  ```
- **Acceptance Criteria**:
  - [ ] Question displayed in cyan panel
  - [ ] Answer rendered as markdown in green panel
  - [ ] Spinner shown during processing

---

### Component 5: KG Search Mode

#### Requirement 1 - KG Search with Pretty Output
- **Requirement**: Direct search với formatted results
- **Implementation**:
  ```python
  async def run_kg_search_mode(query: str, max_results: int = 10) -> None:
      """Run Knowledge Graph search mode."""
      from shared.agent_tools.retrieval import search_knowledge_graph
      
      console.print(Panel(
          f"[bold magenta]{query}[/bold magenta]\n"
          f"[dim]Max Results: {max_results}[/dim]",
          title="🔍 Knowledge Graph Search",
          border_style="magenta"
      ))
      
      with console.status("[bold magenta]Searching...", spinner="dots"):
          try:
              results = await search_knowledge_graph(
                  query=query, max_results=max_results
              )
              console.print()
              console.print(Markdown(results))
          except Exception as e:
              console.print(f"[red]Error: {e}[/red]")
  ```
- **Acceptance Criteria**:
  - [ ] Query displayed in magenta panel
  - [ ] Results rendered as markdown

---

### Component 6: Document Search Mode

#### Requirement 1 - Document Search with Filters Display
- **Requirement**: Search với đầy đủ filters và clean output
- **Implementation**:
  ```python
  async def run_docs_search_mode(
      query: str,
      book: str = None,
      chapter: str = None,
      author: str = None,
      top_k: int = 10
  ) -> None:
      """Run Document Library search mode."""
      from shared.agent_tools.retrieval import search_document_library
      
      # Build filter display
      filters = []
      if book: filters.append(f"Book: {book}")
      if chapter: filters.append(f"Chapter: {chapter}")
      if author: filters.append(f"Author: {author}")
      filter_text = " | ".join(filters) if filters else "None"
      
      console.print(Panel(
          f"[bold blue]{query}[/bold blue]\n"
          f"[dim]Filters: {filter_text}[/dim]\n"
          f"[dim]Top K: {top_k}[/dim]",
          title="📚 Document Library Search",
          border_style="blue"
      ))
      
      with console.status("[bold blue]Searching...", spinner="dots"):
          try:
              results = await search_document_library(
                  query=query,
                  filter_by_book=book,
                  filter_by_chapter=chapter,
                  filter_by_author=author,
                  top_k=top_k
              )
              console.print()
              console.print(results)
          except Exception as e:
              console.print(f"[red]Error: {e}[/red]")
  ```
- **Acceptance Criteria**:
  - [ ] Query and filters displayed in blue panel
  - [ ] All filters work correctly

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: CLI Help Display
- **Purpose**: Verify CLI structure và help text
- **Steps**:
  1. Run `brandmind --help`
  2. Run `brandmind ask --help`
  3. Run `brandmind search-kg --help`
  4. Run `brandmind search-docs --help`
- **Expected Result**: All commands show proper help với arguments
- **Status**: ⏳ Pending

### Test Case 2: Q&A Agent Ask Mode
- **Purpose**: Verify agentic Q&A works end-to-end
- **Steps**:
  1. Ensure database connections (Milvus, FalkorDB) are running
  2. Run: `brandmind ask -q "What is Marketing Myopia?"`
  3. Observe output formatting
- **Expected Result**: 
  - Question in cyan panel
  - Spinner during processing
  - Answer in green panel với markdown formatting
- **Status**: ⏳ Pending

### Test Case 3: KG Search Mode
- **Purpose**: Verify KG search functionality
- **Steps**:
  1. Run: `brandmind search-kg -q "customer value" -n 5`
  2. Check output for entities và relationships
- **Expected Result**: 
  - Query in magenta panel
  - Results với entities, relationships, sources
- **Status**: ⏳ Pending

### Test Case 4: Document Search with Filters
- **Purpose**: Verify document search với các filters
- **Steps**:
  1. Run: `brandmind search-docs -q "pricing" -k 3`
  2. Run: `brandmind search-docs -q "pricing" -c "Chapter 10" -k 3`
- **Expected Result**: 
  - Filters displayed correctly
  - Second command returns only Chapter 10 passages
- **Status**: ⏳ Pending

### Test Case 5: Error Handling
- **Purpose**: Verify graceful error handling
- **Steps**:
  1. Stop Milvus temporarily
  2. Run any inference command
  3. Observe error message
- **Expected Result**: Clear error in red panel (not stack trace)
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

### What Was Implemented

**Components Completed**:
- [x] [Component 1]: Prompts module với qa_agent_system_prompt.py
- [x] [Component 2]: CLI structure với argparse subcommands
- [x] [Component 3]: pyproject.toml entry point (`brandmind` alias)
- [x] [Component 4]: Q&A Agent ask mode
- [x] [Component 5]: KG search mode
- [x] [Component 6]: Document search mode

**Files Created/Modified**:
```
src/
├── prompts/
│   └── inference/
│       ├── __init__.py                    # Exports prompts
│       └── qa_agent_system_prompt.py      # Q&A Agent instruction
│
└── cli/
    └── inference.py                        # Main CLI với 3 modes

pyproject.toml                               # Added brandmind entry point
```

**Key Features Delivered**:
1. **Ask Mode**: Q&A Agent với agentic reasoning using langchain, middlewares, and dual tools
2. **KG Search Mode**: Direct Knowledge Graph search với formatted markdown results
3. **Document Search Mode**: Passage search với book/chapter/author filters and clean display
4. **CLI Alias**: `brandmind` command registered and tested successfully
5. **Rich Output**: Beautiful console formatting with panels, colors, spinners, and markdown rendering

### Implementation Notes

**Code Quality**:
- ✅ All code passes typecheck (`make typecheck`)
- ✅ No mypy errors, ruff checks passed
- ✅ Security scan passed (bandit)
- ✅ Proper type hints and docstrings throughout

**Implementation Details**:
- Q&A Agent uses same middleware stack as evaluation (context editing, summarization, retry, etc.)
- Properly extracts agent responses from langchain message format
- Rich Console integration with color-coded panels per mode:
  - Cyan for questions (ask mode)
  - Magenta for KG searches 
  - Blue for document searches
- Spinner animations during async operations
- Markdown rendering for formatted outputs

### Technical Highlights

**Architecture Decisions**:
- Prompts extracted to `src/prompts/inference/` for reusability
- Rich Console cho user-friendly output
- Argparse subparsers giống existing CLIs

**Future TUI Notes**:
- Branding: "BRANDMIND AI" 
- Style: Claude Code / Gemini CLI interface
- Libraries: textual, rich
- Prerequisites: Database backup/restore (Stage 4) must be completed first

------------------------------------------------------------------------

