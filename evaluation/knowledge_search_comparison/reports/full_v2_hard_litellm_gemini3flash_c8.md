# Full V2-Hard Benchmark Report

## Summary

This report documents the latest full run of the BrandMind knowledge-search comparison benchmark on the 150-item v2-hard dataset. It compares BrandMind dual knowledge search, Hybrid document search, and HippoRAG native retriever output in the same answer-flow harness.

The result is close: BrandMind led on raw accuracy and mean fact coverage, HippoRAG was slightly behind on quality and much slower, and Hybrid remained competitive because it uses BrandMind's cleaned document chunks and document-search index.

## Research Question

When a marketing-domain agent must answer hard questions from distributed textbook evidence, does BrandMind's dual knowledge-search interface provide better answer-flow performance than a strong hybrid document-search baseline or HippoRAG-style graph-based retrieval?

## Dataset

| Field | Value |
| --- | --- |
| Dataset path | `evaluation/knowledge_search_comparison/datasets/marketing_5books_multihop_hard_v2.json` |
| Dataset ID | `brandmind_marketing_5books_multihop_hard_v2` |
| Dataset version | `1.0.0` |
| Items | 150 |
| Difficulty | 150 hard |
| Question types | 30 each of `mechanism`, `compare_contrast`, `application`, `synthesis`, `diagnosis` |
| Required sources | 20 with 2 sources, 60 with 3 sources, 50 with 4 sources, 20 with 5 sources |
| Scope | 90 cross-book, 60 intra-book distributed across chapters or sections |
| Definition questions | 0 |

The dataset is source-grounded. Each item includes a gold answer, answer-key facts, required sources, and v2-hard metadata such as reasoning type and fact-source mappings.

## Systems

| System | Search surface | Notes |
| --- | --- | --- |
| BrandMind | `search_knowledge_graph` plus `search_document_library` | Dual-tool, autonomous tool choice, evidence recovery enabled |
| Hybrid | One hybrid document-search tool | Uses BrandMind's document chunks and document-search index |
| HippoRAG | One `search_hipporag` tool | Returns native retriever output; does not call `rag_qa()` |

## Run Configuration

| Field | Value |
| --- | --- |
| Result artifact | `.codex/benchmarks/hipporag/results/full_v2_hard_litellm_gemini3flash_c8.json` |
| Checkpoint artifact | `.codex/benchmarks/hipporag/results/full_v2_hard_litellm_gemini3flash_c8.records.jsonl` |
| Run ID | `5f4b5904cf164edca8c02a81ca8cd629` |
| Created at | `2026-05-13T15:08:30.112580+00:00` |
| Records | 450, equal to 150 items x 3 systems |
| Checkpoint lines | 450 |
| Answer provider | LiteLLM |
| Answer model | `gemini/gemini-3-flash-preview` |
| Answer temperature | `1.0` |
| Answer reasoning effort | `medium` |
| Judge provider | Gemini |
| Judge model | `gemini-2.5-flash` |
| Judge temperature | `0.0` |
| Judge thinking budget | 2000 |
| `top_k` | 5 |
| Candidate `top_k` | 10 |
| Max tool calls | 4 |
| Recursion limit | 60 |
| Concurrency | 8 |
| BrandMind evidence recovery | enabled |

## Primary Results

| System | Accuracy | Mean fact coverage | Errors | Avg tool calls | Avg latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| BrandMind | 59.3% | 83.9% | 0 | 3.01 | 59.2s |
| HippoRAG | 56.7% | 83.1% | 0 | 2.63 | 100.4s |
| Hybrid | 57.3% | 82.3% | 1 | 2.33 | 42.9s |

BrandMind had the best overall answer-quality profile in this run, but the lead is narrow. The most operationally visible gap is latency: HippoRAG averaged about 100.4 seconds per answer-flow record despite fewer outer tool calls than BrandMind.

## Deterministic Evaluator Views

These views are derived from existing judge fields. They do not replace the primary judge score.

| System | Raw correct | Fact complete | Strict supported | Judged |
| --- | ---: | ---: | ---: | ---: |
| BrandMind | 59.3% | 50.0% | 48.0% | 150 |
| HippoRAG | 56.7% | 46.7% | 44.7% | 150 |
| Hybrid | 57.7% | 48.3% | 47.7% | 149 |

`fact_complete` means all answer-key facts were covered. `strict_supported` additionally requires no unsupported claims. Hybrid has 149 judged records because one record hit a transport error.

## Breakdown By Reasoning Type

| Reasoning type | BrandMind acc/fc | HippoRAG acc/fc | Hybrid acc/fc |
| --- | ---: | ---: | ---: |
| `distributed_diagnosis` | 26.7% / 72.1% | 43.3% / 75.6% | 40.0% / 74.5% |
| `failure_mode_analysis` | 56.7% / 84.1% | 60.0% / 87.8% | 60.0% / 83.7% |
| `mechanism_bridge` | 90.0% / 93.3% | 76.7% / 91.2% | 73.3% / 90.4% |
| `strategy_synthesis` | 60.0% / 85.1% | 50.0% / 82.0% | 56.7% / 82.0% |
| `tension_resolution` | 63.3% / 84.7% | 53.3% / 78.8% | 58.6% / 81.0% |

BrandMind was strongest on `mechanism_bridge`, `strategy_synthesis`, and `tension_resolution`. HippoRAG and Hybrid were stronger on `distributed_diagnosis` and `failure_mode_analysis` in this run.

## Breakdown By Required Source Count

| Required sources | BrandMind acc/fc | HippoRAG acc/fc | Hybrid acc/fc |
| --- | ---: | ---: | ---: |
| 2 | 70.0% / 89.2% | 65.0% / 88.9% | 70.0% / 87.4% |
| 3 | 73.3% / 91.0% | 63.3% / 86.7% | 61.7% / 85.8% |
| 4 | 48.0% / 76.7% | 52.0% / 80.1% | 59.2% / 81.5% |
| 5 | 35.0% / 75.0% | 40.0% / 73.6% | 30.0% / 68.8% |

BrandMind led most clearly on three-source items. Hybrid led the four-source slice. HippoRAG led binary accuracy on five-source items, while BrandMind retained slightly higher fact coverage there.

## Breakdown By Scope

| Scope | BrandMind acc/fc | HippoRAG acc/fc | Hybrid acc/fc |
| --- | ---: | ---: | ---: |
| `cross_book` | 57.8% / 82.1% | 54.4% / 80.6% | 53.3% / 79.6% |
| `how_brands_grow_what_marketers_dont_know` | 80.0% / 89.6% | 65.0% / 87.4% | 65.0% / 88.7% |
| `influence_new_and_expanded_the_psychology_of_persuasion` | 50.0% / 89.3% | 100.0% / 100.0% | 100.0% / 100.0% |
| `kotler_and_armstrong_principles_of_marketing` | 20.0% / 70.0% | 40.0% / 84.8% | 60.0% / 84.8% |
| `positioning_the_battle_for_your_mind` | 69.2% / 89.4% | 57.7% / 86.9% | 69.2% / 87.5% |
| `strategic_brand_management` | 0.0% / 72.9% | 40.0% / 75.7% | 20.0% / 67.1% |

The cross-book row is the most important scope row because it contains 90 items. The smaller intra-book slices should be interpreted cautiously.

## Judge Diagnostics

| System | Coverage 1.0 but false | Correct with missing facts | Unsupported accepted | Unsupported rejected |
| --- | ---: | ---: | ---: | ---: |
| BrandMind | 0 | 14 | 4 | 17 |
| HippoRAG | 1 | 16 | 4 | 18 |
| Hybrid | 0 | 14 | 3 | 21 |

These diagnostics are why the benchmark should not be cited from binary accuracy alone. Some accepted answers missed answer-key facts, and some answers were accepted despite unsupported claims.

## Largest Fact-Coverage Deltas

| Item | Delta | Leader | Trailer |
| --- | ---: | --- | --- |
| `BM5B-HARD-052` | 83.3% | BrandMind 100.0% | HippoRAG 16.7% |
| `BM5B-HARD-054` | 71.4% | BrandMind 100.0% | HippoRAG and Hybrid 28.6% |
| `BM5B-HARD-428` | 66.7% | Hybrid 100.0% | BrandMind and HippoRAG 33.3% |
| `BM5B-HARD-509` | 57.1% | Hybrid 100.0% | BrandMind and HippoRAG 42.9% |
| `BM5B-HARD-445` | 57.1% | HippoRAG 100.0% | BrandMind 42.9% |

These items are the best candidates for manual qualitative review because they show where the systems diverged most.

## Interpretation

The strongest defensible claims from this run are:

1. BrandMind produced the best overall answer-quality profile on v2-hard, but the margin is narrow.
2. HippoRAG was the slowest system in this setup, with about 100.4 seconds average answer-flow latency.
3. Hybrid remained strong because it uses BrandMind's cleaned document chunks and document index. This does not make KG search useless; it shows that document search can be highly competitive when evidence is concentrated in retrievable chunks.
4. V2-hard is more appropriate than v1 for the BrandMind vs HippoRAG question because it requires multiple evidence sources and cross-source synthesis.
5. Accuracy, fact coverage, strict support, judge diagnostics, transport errors, and latency should be reported together.

## Threats To Validity

- **Judge sensitivity:** Gemini and Sonnet judge variants can differ. Evaluator-lane labels must stay explicit.
- **Model variance:** Gemini 3 answer runs used `temperature=1.0` and can vary across runs.
- **Single-run result:** The full result is one 150-item run, not a repeated-run confidence interval.
- **One transport error:** Hybrid had one server disconnect. Publication-grade reporting should either preserve `149 judged + 1 transport error` or rerun only that failed record with a clearly labeled repair artifact.
- **Outer tool traces only:** `ToolTrace` records outer agent tool calls, previews, source IDs, latency, and errors. It does not expose all internal retriever steps.
- **Ignored result artifact:** The JSON result file is under `.codex/` and is not tracked by git. For archival use, promote the exact artifact or record its hash.
- **Service state:** BrandMind's KG and vector DB must match the expected restored five-book state. Different backups, embeddings, or chunking can change outcomes.

## Reproducibility Notes

Use the runbook in [`../README.md`](../README.md) to reproduce the result. The important frozen settings are:

- Dataset: `marketing_5books_multihop_hard_v2.json`
- Systems: `brandmind_agent`, `hybrid_search_agent`, `hipporag_agent`
- Answer provider/model: LiteLLM `gemini/gemini-3-flash-preview`
- Answer temperature/reasoning: `1.0`, `medium`
- Judge provider/model: Gemini `gemini-2.5-flash`
- Concurrency: `8`
- BrandMind evidence recovery: enabled
