# Knowledge Search Comparison Benchmark

This package runs the BrandMind knowledge-search benchmark against three answer-flow systems:

- `brandmind_agent`: BrandMind dual knowledge search with autonomous KG and document-library tool use.
- `hybrid_search_agent`: one hybrid document-search tool over BrandMind's document index.
- `hipporag_agent`: one `search_hipporag` tool returning native HippoRAG retriever output. It does not call HippoRAG `rag_qa()`.

Use this README as the clean runbook. Detailed run interpretation lives in the linked reports.

## Current Benchmark

| Item | Value |
| --- | --- |
| Primary dataset | `datasets/marketing_5books_multihop_hard_v2.json` |
| Supplementary dataset | `datasets/marketing_5books_benchmark_v1.json` |
| Corpus | Five canonical marketing books from `data/parsed_documents/` |
| Primary score | Final answer quality against `gold_answer` and `answer_key_facts` |
| Diagnostics | Fact coverage, strict support, tool traces, source IDs, latency, errors |
| Latest report | [`reports/full_v2_hard_litellm_gemini3flash_c8.md`](reports/full_v2_hard_litellm_gemini3flash_c8.md) |

The v2-hard dataset has 150 hard multi-hop questions. Every item requires 2 to 5 sources, and the distribution is designed to stress cross-source reasoning rather than one-chunk lookup.

## Design Boundaries

The benchmark is answer-flow based, not retriever-only. This matters because BrandMind's knowledge search is designed as an agent-facing dual-tool interface.

Fairness rules:

- Same question set for all systems.
- Same answer model and judge model for all systems in a run.
- Same answer-prompt family and scoring rubric for all systems.
- Same `top_k`, candidate fetch budget, tool-call budget, and recursion limit.
- Native retrieval shape is preserved for each system.

System-specific retrieval behavior is intentionally not flattened:

- BrandMind keeps two tools because dual-tool use is the architecture under test.
- Hybrid keeps one document-search tool.
- HippoRAG keeps one native retriever-output tool.

## Files

| Path | Purpose |
| --- | --- |
| `run_comparison.py` | Main benchmark runner CLI |
| `rejudge_results.py` | Re-score an existing result artifact with another judge |
| `agents.py` | Answer-flow wrappers for BrandMind, Hybrid, and HippoRAG |
| `tools.py` | Tool adapters and telemetry capture |
| `hipporag_worker.py` | Isolated HippoRAG subprocess entrypoint |
| `judge.py` | Reference-based answer judge |
| `report.py` | Compact reporting and diagnostics |
| `datasets/` | Tracked benchmark datasets |
| `reports/` | Tracked benchmark interpretation reports |

## Prerequisites

Install the main workspace:

```bash
make install-all
```

Start and restore the BrandMind infrastructure:

```bash
make services-up
make restore-package
```

Load environment values without printing secrets:

```bash
set -a
source environments/.env
set +a
```

Verify the local services used by BrandMind retrieval:

```bash
nc -z localhost 19530  # Milvus
nc -z localhost 6380   # FalkorDB
```

For the latest run profile, LiteLLM must be reachable at port `4000`:

```bash
curl http://localhost:4000/health/readiness
```

When using Gemini through LiteLLM, keep the provider prefix:

```text
gemini/gemini-3-flash-preview
```

## HippoRAG Runtime

HippoRAG is isolated from the main `uv` workspace.

Expected local contract:

```text
conda env: brandmind-hipporag
python: 3.10
litellm: 1.83.14 inside the conda env
```

Smoke check:

```bash
conda run -n brandmind-hipporag python -c "import hipporag, litellm; print('hipporag ok')"
conda run -n brandmind-hipporag python -m evaluation.knowledge_search_comparison.hipporag_worker --help
```

The HippoRAG index is persistent but ignored by git:

```text
.codex/benchmarks/hipporag/index/marketing_5books
```

If the corpus has not changed and this folder still exists, reindexing is not required.

## Corpus And Index

Export the five-book corpus:

```bash
uv run python -m evaluation.hipporag_comparison.export_corpus \
  --parsed-root data/parsed_documents \
  --corpus-output .codex/benchmarks/hipporag/corpus/marketing_5books_corpus.json \
  --metadata-output .codex/benchmarks/hipporag/corpus/marketing_5books_metadata.json
```

The current expected corpus size is 3,185 records. If this changes, confirm whether `data/parsed_documents/` or the export pipeline changed before comparing against older reports.

Build the HippoRAG index:

```bash
conda run -n brandmind-hipporag python -m evaluation.knowledge_search_comparison.hipporag_worker index \
  --save-dir .codex/benchmarks/hipporag/index/marketing_5books \
  --corpus-path .codex/benchmarks/hipporag/corpus/marketing_5books_corpus.json
```

Smoke test HippoRAG retrieval:

```bash
conda run -n brandmind-hipporag python -m evaluation.knowledge_search_comparison.hipporag_worker retrieve \
  --query "mental availability brand growth" \
  --top-k 2 \
  --save-dir .codex/benchmarks/hipporag/index/marketing_5books \
  --corpus-path .codex/benchmarks/hipporag/corpus/marketing_5books_corpus.json \
  --metadata-path .codex/benchmarks/hipporag/corpus/marketing_5books_metadata.json
```

## Validation

Validate the v2-hard dataset against the metadata sidecar:

```bash
uv run python -m evaluation.hipporag_comparison.validate_benchmark_dataset \
  --dataset evaluation/knowledge_search_comparison/datasets/marketing_5books_multihop_hard_v2.json \
  --metadata .codex/benchmarks/hipporag/corpus/marketing_5books_metadata.json
```

Run a no-cost fixture before spending model calls:

```bash
uv run python -m evaluation.knowledge_search_comparison.run_comparison \
  --dataset evaluation/knowledge_search_comparison/datasets/marketing_5books_multihop_hard_v2.json \
  --limit 2 \
  --systems all \
  --dry-run-fixture
```

## Pilot Run

Use a pilot after changing prompts, tools, providers, retrieval services, or index state:

```bash
uv run python -m evaluation.knowledge_search_comparison.run_comparison \
  --dataset evaluation/knowledge_search_comparison/datasets/marketing_5books_multihop_hard_v2.json \
  --limit 15 \
  --systems all \
  --answer-provider litellm \
  --answer-model gemini/gemini-3-flash-preview \
  --answer-temperature 1.0 \
  --answer-reasoning-effort medium \
  --judge-provider gemini \
  --judge-model gemini-2.5-flash \
  --concurrency 8 \
  --progress-interval 5 \
  --brandmind-evidence-recovery \
  --resume \
  --output .codex/benchmarks/hipporag/results/pilot_v2_hard_litellm_gemini3flash_c8.json
```

Inspect the JSON output, checkpoint JSONL, system summaries, tool traces, judge diagnostics, and transport errors before running the full benchmark.

## Full Run

Command used for the latest full report:

```bash
uv run python -m evaluation.knowledge_search_comparison.run_comparison \
  --dataset evaluation/knowledge_search_comparison/datasets/marketing_5books_multihop_hard_v2.json \
  --limit 150 \
  --systems all \
  --answer-provider litellm \
  --answer-model gemini/gemini-3-flash-preview \
  --answer-temperature 1.0 \
  --answer-reasoning-effort medium \
  --judge-provider gemini \
  --judge-model gemini-2.5-flash \
  --concurrency 8 \
  --progress-interval 5 \
  --brandmind-evidence-recovery \
  --resume \
  --output .codex/benchmarks/hipporag/results/full_v2_hard_litellm_gemini3flash_c8.json
```

The runner writes a checkpoint beside the output:

```text
.codex/benchmarks/hipporag/results/full_v2_hard_litellm_gemini3flash_c8.records.jsonl
```

If a run stops unexpectedly, rerun the same command with `--resume` and the same output path. Do not change dataset, systems, model settings, or output path when resuming one artifact.

## Re-Judging

Use re-judging to test judge sensitivity without rerunning retrieval or answer generation:

```bash
uv run python -m evaluation.knowledge_search_comparison.rejudge_results \
  --input .codex/benchmarks/hipporag/results/full_v2_hard_litellm_gemini3flash_c8.json \
  --output .codex/benchmarks/hipporag/results/full_v2_hard_litellm_gemini3flash_c8_sonnet46judge.json \
  --dataset evaluation/knowledge_search_comparison/datasets/marketing_5books_multihop_hard_v2.json \
  --judge-provider litellm \
  --judge-model claude-sonnet-4.6 \
  --judge-temperature 1.0 \
  --judge-reasoning-effort medium
```

Keep re-judge artifacts separately labeled. They change the evaluator lane, not the retrieved evidence or generated answers.

## Result Summary

Latest full run:

| System | Accuracy | Mean fact coverage | Errors | Avg latency |
| --- | ---: | ---: | ---: | ---: |
| BrandMind | 59.3% | 83.9% | 0 | 59.2s |
| HippoRAG | 56.7% | 83.1% | 0 | 100.4s |
| Hybrid | 57.3% | 82.3% | 1 | 42.9s |

Read the full interpretation before citing this result:

```text
evaluation/knowledge_search_comparison/reports/full_v2_hard_litellm_gemini3flash_c8.md
```

The headline margin is narrow. Report binary accuracy together with fact coverage, strict support, judge diagnostics, transport errors, and latency.

## Artifact Policy

Tracked:

- Benchmark code in `evaluation/knowledge_search_comparison/`
- Dataset JSON files in `evaluation/knowledge_search_comparison/datasets/`
- Interpretation reports in `evaluation/knowledge_search_comparison/reports/`

Ignored:

- `.codex/benchmarks/hipporag/corpus/`
- `.codex/benchmarks/hipporag/index/`
- `.codex/benchmarks/hipporag/results/`
- Intermediate generation, curation, pilot, and audit artifacts

If a benchmark result is used in a thesis, paper, or release note, promote the exact result artifact or at least record its hash intentionally.
