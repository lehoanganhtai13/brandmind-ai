"""CLI runner for the 3-way knowledge-search answer-flow benchmark."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from evaluation.hipporag_comparison.benchmark_schema import BenchmarkItem
from evaluation.knowledge_search_comparison.agents import (
    AgentRunnerConfig,
    run_brandmind_agent,
    run_direct_tool_answer_flow,
    run_hipporag_agent,
    run_hybrid_search_agent,
)
from evaluation.knowledge_search_comparison.dataset import (
    DEFAULT_DATASET_PATH,
    load_benchmark_dataset,
    select_benchmark_items,
)
from evaluation.knowledge_search_comparison.judge import (
    AnswerJudge,
    AnswerKeyFactJudge,
    GeminiAnswerJudge,
)
from evaluation.knowledge_search_comparison.report import build_report_lines
from evaluation.knowledge_search_comparison.schemas import (
    AnswerFlowRecord,
    ComparisonRunConfig,
    ComparisonRunResult,
    ComparisonSystem,
)
from evaluation.knowledge_search_comparison.source_mapping import (
    load_source_mapping,
)
from evaluation.knowledge_search_comparison.tools import (
    HippoRagSubprocessSearchTool,
)

DEFAULT_OUTPUT_DIR = Path(".codex/benchmarks/hipporag/results")


class FixtureSearchTool:
    """Offline fixture search tool for CLI smoke tests."""

    def __init__(self, *, item: BenchmarkItem, system: ComparisonSystem) -> None:
        """Store item-specific source IDs for deterministic fixture context."""

        self.item = item
        self.system = system

    async def __call__(self, *, query: str, top_k: int) -> str:
        """Return deterministic context containing required source IDs."""

        sources = ", ".join(self.item.required_sources)
        return (
            f"System={self.system.value}; query={query}; top_k={top_k}; "
            f"sources={sources}"
        )


class FixtureAnswerClient:
    """Offline fixture answer client for runner smoke tests."""

    def __init__(self, *, item: BenchmarkItem) -> None:
        """Store item answer-key facts for deterministic fixture answers."""

        self.item = item

    async def answer(
        self,
        *,
        question: str,
        context: str,
        system_prompt: str,
    ) -> str:
        """Return an answer containing all answer-key facts."""

        del question, context, system_prompt
        return " ".join(self.item.answer_key_facts)


async def run_comparison(config: ComparisonRunConfig) -> ComparisonRunResult:
    """Run selected systems over the configured benchmark item slice."""

    dataset = load_benchmark_dataset(config.dataset_path)
    items = select_benchmark_items(
        dataset,
        limit=config.limit,
        offset=config.offset,
    )
    agent_config = AgentRunnerConfig(
        answer_model=config.answer_model,
        top_k=config.top_k,
        candidate_top_k=config.candidate_top_k,
        max_tool_calls=config.max_tool_calls,
        recursion_limit=config.recursion_limit,
    )
    if config.dry_run_fixture:
        source_mapping = None
        hipporag_search = None
        judge: AnswerJudge = AnswerKeyFactJudge()
    else:
        source_mapping = load_source_mapping()
        hipporag_search = HippoRagSubprocessSearchTool()
        judge = GeminiAnswerJudge(model=config.judge_model)

    records: list[AnswerFlowRecord] = []
    for item in items:
        for system in config.systems:
            if config.dry_run_fixture:
                record = await run_fixture_system(
                    item=item,
                    system=system,
                    agent_config=agent_config,
                    judge=judge,
                )
            else:
                if hipporag_search is None or source_mapping is None:
                    raise RuntimeError("Live comparison dependencies were not loaded.")
                record = await run_system(
                    item=item,
                    system=system,
                    agent_config=agent_config,
                    judge=judge,
                    hipporag_search=hipporag_search,
                    source_mapping=source_mapping,
                )
            records.append(record)

    return ComparisonRunResult(
        dataset_id=dataset.dataset_id,
        dataset_version=dataset.dataset_version,
        config=config,
        records=records,
    )


async def run_fixture_system(
    *,
    item: BenchmarkItem,
    system: ComparisonSystem,
    agent_config: AgentRunnerConfig,
    judge: AnswerJudge,
) -> AnswerFlowRecord:
    """Run one offline fixture system for CLI structure verification."""

    search_tool = FixtureSearchTool(item=item, system=system)
    answer_client = FixtureAnswerClient(item=item)
    record = await run_direct_tool_answer_flow(
        item=item,
        system=system,
        search_tool=search_tool,
        answer_client=answer_client,
        config=agent_config,
    )
    record.judge = await judge.judge(
        item=item,
        candidate_answer=record.final_answer,
    )
    return record


async def run_system(
    *,
    item: BenchmarkItem,
    system: ComparisonSystem,
    agent_config: AgentRunnerConfig,
    judge: AnswerJudge,
    hipporag_search: HippoRagSubprocessSearchTool,
    source_mapping: object,
) -> AnswerFlowRecord:
    """Run one system for one item and attach the judge result."""

    if system is ComparisonSystem.BRANDMIND_AGENT:
        record = await run_brandmind_agent(
            item=item,
            config=agent_config,
            source_mapping=source_mapping,  # type: ignore[arg-type]
        )
    elif system is ComparisonSystem.HYBRID_SEARCH_AGENT:
        record = await run_hybrid_search_agent(
            item=item,
            config=agent_config,
            source_mapping=source_mapping,  # type: ignore[arg-type]
        )
    elif system is ComparisonSystem.HIPPORAG_AGENT:
        record = await run_hipporag_agent(
            item=item,
            config=agent_config,
            hipporag_search=hipporag_search,
            source_mapping=source_mapping,  # type: ignore[arg-type]
        )
    else:
        raise ValueError(f"Unsupported comparison system: {system}")

    if record.error:
        return record

    record.judge = await judge.judge(
        item=item,
        candidate_answer=record.final_answer,
    )
    return record


def parse_systems(raw_systems: str) -> list[ComparisonSystem]:
    """Parse comma-separated system names from the CLI."""

    if raw_systems.strip().lower() == "all":
        return list(ComparisonSystem)
    return [
        ComparisonSystem(system.strip())
        for system in raw_systems.split(",")
        if system.strip()
    ]


def build_output_path(output_dir: Path) -> Path:
    """Build the default ignored output path for comparison artifacts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / "knowledge_search_comparison_results.json"


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for pilot and full benchmark runs."""

    parser = argparse.ArgumentParser(
        description="Run BrandMind vs hybrid search vs HippoRAG answer-flow eval."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--systems", default="all")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--answer-model", default="gemini-2.5-flash-lite")
    parser.add_argument("--judge-model", default="gemini-2.5-flash")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--candidate-top-k", type=int, default=10)
    parser.add_argument("--max-tool-calls", type=int, default=4)
    parser.add_argument("--recursion-limit", type=int, default=60)
    parser.add_argument(
        "--dry-run-fixture",
        action="store_true",
        help="Run deterministic fake systems without live services.",
    )
    return parser


def main() -> None:
    """Run the comparison CLI and write a structured JSON artifact."""

    args = build_parser().parse_args()
    output_path = args.output or build_output_path(args.output_dir)
    config = ComparisonRunConfig(
        dataset_path=args.dataset,
        output_path=output_path,
        systems=parse_systems(args.systems),
        answer_model=args.answer_model,
        judge_model=args.judge_model,
        top_k=args.top_k,
        candidate_top_k=args.candidate_top_k,
        max_tool_calls=args.max_tool_calls,
        recursion_limit=args.recursion_limit,
        limit=args.limit,
        offset=args.offset,
        dry_run_fixture=args.dry_run_fixture,
    )
    result = asyncio.run(run_comparison(config))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("\n".join(build_report_lines(result)))
    print(f"Saved results to {output_path}")


if __name__ == "__main__":
    main()
