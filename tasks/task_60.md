# Task 60: 3-Way Knowledge Search Answer-Flow Benchmark

## Metadata

- **Epic**: Marketing KG Evaluation — HippoRAG comparison
- **Priority**: High
- **Status**: Implementation In Progress
- **Team**: Backend / Evaluation
- **Related Tasks**: `tasks/task_57.md`, `tasks/task_58.md`, `tasks/task_59.md`
- **Active Package**: `evaluation/knowledge_search_comparison/`

## Progress Checklist

- [x] Agent Protocol — Read and follow `tasks/task_template.md`
- [x] Context & Goals — Refined from retrieval-component eval to answer-flow eval
- [x] Solution Design — 3-way answer-flow benchmark design approved
- [x] Canonical Dataset — Copied into `evaluation/knowledge_search_comparison/datasets/`
- [x] Core Package — Dataset loader, schemas, source mapping, prompts, judge, agents, CLI, report
- [x] Offline Unit Tests — Fake-tool tests and schema/mapping/dataset tests pass
- [x] Offline CLI Pilot — `--dry-run-fixture --limit 2 --systems all` pass
- [ ] Legacy Cleanup — Delete old baseline files after final targeted verification
- [ ] Live Pilot — Run 5-10 questions with live BrandMind/Hybrid/HippoRAG tools
- [ ] Task Summary — Final implementation and verification summary

## Context & Goal

The accepted comparison should follow the spirit of the earlier baseline
comparison: run a full tool-using answer flow, then judge the final answer
against ground truth. It must not become a retrieval-only/component benchmark.

The supporting thesis claim is narrow:

> BrandMind's dual KG/docs interface is a better agent-facing domain search
> interface than replacing the knowledge tool with one bundled SOTA RAG search
> system such as HippoRAG.

Primary measurement is final answer quality against the committed
`gold_answer` and `answer_key_facts` in the 150-item five-book benchmark.
Retrieval/source metrics are diagnostics for failure analysis, not the main
score.

## Final Comparison Design

Compare the same 150 benchmark items across three answer-flow systems:

1. **BrandMind agent** — autonomous access to `search_knowledge_graph` and
   `search_document_library`; no forced KG-plus-docs sequence.
2. **Hybrid search agent** — same answer behavior and shared prompt style, but
   with one hybrid document-search tool.
3. **HippoRAG agent** — same answer behavior and shared prompt style, but with
   one `search_hipporag` tool exposing native HippoRAG retriever output.

HippoRAG is used as a retriever/search tool only. The runner must not call
HippoRAG `rag_qa()`, because that would compare HippoRAG's full QA pipeline
against BrandMind's agent-facing search interface.

## Implemented Files

- `evaluation/knowledge_search_comparison/__init__.py`
- `evaluation/knowledge_search_comparison/dataset.py`
- `evaluation/knowledge_search_comparison/schemas.py`
- `evaluation/knowledge_search_comparison/source_mapping.py`
- `evaluation/knowledge_search_comparison/prompts.py`
- `evaluation/knowledge_search_comparison/judge.py`
- `evaluation/knowledge_search_comparison/agents.py`
- `evaluation/knowledge_search_comparison/hipporag_worker.py`
- `evaluation/knowledge_search_comparison/tools.py`
- `evaluation/knowledge_search_comparison/run_comparison.py`
- `evaluation/knowledge_search_comparison/report.py`
- `evaluation/knowledge_search_comparison/datasets/marketing_5books_benchmark_v1.json`
- `tests/unit/test_knowledge_search_comparison_dataset.py`
- `tests/unit/test_knowledge_search_comparison_source_mapping.py`
- `tests/unit/test_knowledge_search_comparison_schemas.py`
- `tests/unit/test_knowledge_search_comparison_fake_flows.py`

## Implementation Detail

### Dataset Loader

`dataset.py` loads the canonical `BenchmarkDataset` schema from the new package
dataset path and supports deterministic `limit`/`offset` slicing for pilots.

### Shared Schemas

`schemas.py` defines:

- `ComparisonSystem`: `brandmind_agent`, `hybrid_search_agent`, `hipporag_agent`
- `ToolTrace`: tool name, query, output preview, source IDs, latency, error
- `AnswerJudgeResult`: correctness, reasoning, covered/missing facts,
  unsupported claims, computed fact coverage
- `AnswerFlowRecord`: final answer, judge result, tool traces, latency/cost
- `ComparisonRunConfig` and `ComparisonRunResult` for reproducible artifacts
- `SystemSummary` for accuracy, fact coverage, tool-call, latency, and error
  diagnostics

### Source Mapping

`source_mapping.py` maps HippoRAG raw retriever passages back to stable
`book_slug::chunk_id` source IDs using exact text first, then whitespace-normalized
text. It also maps worker documents by title/index and can extract source IDs
already present in formatted tool output.

### Agents And Tools

`agents.py` contains:

- a shared `ANSWER_AGENT_SYSTEM_PROMPT`
- `run_brandmind_agent()` with autonomous KG/docs tools
- `run_hybrid_search_agent()` with one hybrid search tool
- `run_hipporag_agent()` with one `search_hipporag` tool
- `run_direct_tool_answer_flow()` for offline fixture and simple single-tool
  smoke tests

`tools.py` calls HippoRAG through the isolated conda environment by invoking
`evaluation.knowledge_search_comparison.hipporag_worker` in a subprocess.

`hipporag_worker.py` supports `index` and `retrieve`. Retrieval uses
`hipporag.retrieve(...)` and maps returned docs to source IDs. It does not call
`rag_qa()`.

### Judge And Runner

`judge.py` implements `GeminiAnswerJudge` for live structured judging and
`AnswerKeyFactJudge` for deterministic fixture tests.

`run_comparison.py` runs selected systems, attaches judge results, writes JSON
artifacts under `.codex/benchmarks/hipporag/results/`, and supports
`--dry-run-fixture` for offline structural verification.

## Test Execution Log

- `uv run pytest tests/unit/test_knowledge_search_comparison_*.py -q`
  - Result: `13 passed`
- `uv run ruff format evaluation/knowledge_search_comparison tests/unit/test_knowledge_search_comparison_*.py`
  - Result: formatted/no pending changes after fix
- `uv run ruff check evaluation/knowledge_search_comparison tests/unit/test_knowledge_search_comparison_*.py`
  - Result: pass
- `uv run mypy evaluation/knowledge_search_comparison --ignore-missing-imports`
  - Result: pass
- `make typecheck`
  - Result: pass for project `src/` typecheck/ruff/bandit target
- `uv run python -m evaluation.knowledge_search_comparison.run_comparison --dry-run-fixture --limit 2 --systems all`
  - Result: pass; wrote ignored artifact to
    `.codex/benchmarks/hipporag/results/knowledge_search_comparison_results.json`

## Legacy Cleanup Gate

Once the new package remains green after targeted verification, delete the old
baseline path immediately to avoid misleading future work:

- `evaluation/kg_tools_search_baseline_comparison.py`
- `evaluation/test_questions.py`
- `evaluation/test_questions_extended.py`
- `evaluation/result/baseline_comparison_basic_results.json`
- `evaluation/result/baseline_comparison_extended_results.json`
- `evaluation/result/` if empty

Before final completion, run GitNexus change detection and rerun the targeted
tests/ruff checks after cleanup.

## Decision Log

- 2026-05-10: Use answer-flow eval as the main comparison shape; retrieval/source
  metrics are diagnostics only.
- 2026-05-10: Keep BrandMind's KG/docs tool choice autonomous; do not force one KG
  call plus one docs call for every question.
- 2026-05-10: HippoRAG tool returns native retriever output and never calls
  `rag_qa()`.
- 2026-05-10: Canonical runtime benchmark dataset moved under
  `evaluation/knowledge_search_comparison/datasets/`.
