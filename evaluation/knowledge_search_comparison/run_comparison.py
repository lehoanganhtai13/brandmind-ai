"""CLI runner for the 3-way knowledge-search answer-flow benchmark."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Literal, cast

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
    create_answer_judge,
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
RecordKey = tuple[str, ComparisonSystem]


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
        answer_provider=cast(Literal["gemini", "litellm"], config.answer_provider),
        answer_model=config.answer_model,
        top_k=config.top_k,
        candidate_top_k=config.candidate_top_k,
        max_tool_calls=config.max_tool_calls,
        recursion_limit=config.recursion_limit,
        temperature=config.answer_temperature,
        thinking_budget=config.answer_thinking_budget,
        thinking_level=config.answer_thinking_level,
        brandmind_evidence_recovery=config.brandmind_evidence_recovery,
    )
    if config.dry_run_fixture:
        source_mapping = None
        hipporag_search = None
        judge: AnswerJudge = AnswerKeyFactJudge()
    else:
        source_mapping = load_source_mapping()
        hipporag_search = HippoRagSubprocessSearchTool()
        judge = create_answer_judge(
            provider=cast(Literal["gemini", "litellm"], config.judge_provider),
            model=config.judge_model,
            temperature=config.judge_temperature,
            thinking_budget=config.judge_thinking_budget,
            thinking_level=config.judge_thinking_level,
        )

    checkpoint_records = (
        load_checkpoint_records(config.checkpoint_path)
        if config.resume and config.checkpoint_path is not None
        else []
    )
    records_by_key = {
        record_key(record.item_id, record.system): record
        for record in checkpoint_records
    }
    work_items = [
        (item, system)
        for item in items
        for system in config.systems
        if record_key(item.id, system) not in records_by_key
    ]
    total_records = len(items) * len(config.systems)
    completed_records = len(records_by_key)
    if completed_records and config.progress_interval:
        print(
            f"Resuming from checkpoint: {completed_records}/{total_records} "
            "records already complete.",
            flush=True,
        )

    semaphore = asyncio.Semaphore(config.concurrency)
    checkpoint_lock = asyncio.Lock()
    result_lock = asyncio.Lock()

    async def run_one(item: BenchmarkItem, system: ComparisonSystem) -> None:
        nonlocal completed_records
        async with semaphore:
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
            if config.checkpoint_path is not None:
                await append_checkpoint_record(
                    path=config.checkpoint_path,
                    record=record,
                    lock=checkpoint_lock,
                )
            async with result_lock:
                records_by_key[record_key(record.item_id, record.system)] = record
                completed_records += 1
                should_print_progress = config.progress_interval > 0 and (
                    completed_records == total_records
                    or completed_records % config.progress_interval == 0
                )
                if should_print_progress:
                    print(
                        f"Progress: {completed_records}/{total_records} records "
                        f"({item.id} / {system.value}).",
                        flush=True,
                    )

    if config.concurrency == 1:
        for item, system in work_items:
            await run_one(item, system)
    else:
        await asyncio.gather(*(run_one(item, system) for item, system in work_items))

    records = order_records(
        records_by_key=records_by_key,
        items=items,
        systems=config.systems,
    )

    return ComparisonRunResult(
        dataset_id=dataset.dataset_id,
        dataset_version=dataset.dataset_version,
        config=config,
        records=records,
    )


def record_key(item_id: str, system: ComparisonSystem) -> RecordKey:
    """Return the stable identity for one benchmark item/system pair."""

    return (item_id, system)


def load_checkpoint_records(path: Path | None) -> list[AnswerFlowRecord]:
    """Load deduplicated answer-flow records from a JSONL checkpoint."""

    if path is None or not path.exists():
        return []

    records_by_key: dict[RecordKey, AnswerFlowRecord] = {}
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        try:
            record = AnswerFlowRecord.model_validate_json(line)
        except ValueError as exc:
            raise ValueError(
                f"Invalid checkpoint record in {path} at line {line_number}."
            ) from exc
        records_by_key[record_key(record.item_id, record.system)] = record
    return list(records_by_key.values())


async def append_checkpoint_record(
    *,
    path: Path,
    record: AnswerFlowRecord,
    lock: asyncio.Lock,
) -> None:
    """Append one completed answer-flow record to a JSONL checkpoint."""

    async with lock:
        await asyncio.to_thread(write_checkpoint_line, path, record)


def write_checkpoint_line(path: Path, record: AnswerFlowRecord) -> None:
    """Write one checkpoint line and flush it to disk."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(record.model_dump(mode="json"), ensure_ascii=False)
    with path.open("a", encoding="utf-8") as file_handle:
        file_handle.write(f"{payload}\n")
        file_handle.flush()
        os.fsync(file_handle.fileno())


def order_records(
    *,
    records_by_key: dict[RecordKey, AnswerFlowRecord],
    items: list[BenchmarkItem],
    systems: list[ComparisonSystem],
) -> list[AnswerFlowRecord]:
    """Return records in deterministic dataset/system order."""

    return [
        records_by_key[key]
        for item in items
        for system in systems
        if (key := record_key(item.id, system)) in records_by_key
    ]


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
    attach_item_metadata(record, item)
    return await attach_judge_result(record=record, item=item, judge=judge)


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
        attach_item_metadata(record, item)
        return record

    attach_item_metadata(record, item)
    return await attach_judge_result(record=record, item=item, judge=judge)


async def attach_judge_result(
    *,
    record: AnswerFlowRecord,
    item: BenchmarkItem,
    judge: AnswerJudge,
) -> AnswerFlowRecord:
    """Attach a judge result without letting judge failures crash the run."""

    try:
        record.judge = await judge.judge(
            item=item,
            candidate_answer=record.final_answer,
        )
    except Exception as exc:
        record.error = merge_record_error(record.error, f"Judge failed: {exc}")
    return record


def merge_record_error(existing_error: str | None, new_error: str) -> str:
    """Combine record-level errors without dropping earlier failure context."""

    if not existing_error:
        return new_error
    return f"{existing_error} | {new_error}"


def attach_item_metadata(record: AnswerFlowRecord, item: BenchmarkItem) -> None:
    """Attach benchmark stratification metadata to one result record."""

    record.book_scope = item.book_scope.value
    record.question_type = item.question_type.value
    record.difficulty = item.difficulty.value
    record.reasoning_type = item.reasoning_type.value if item.reasoning_type else None
    record.required_source_count = len(item.required_sources)


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


def build_default_checkpoint_path(output_path: Path) -> Path:
    """Build the JSONL checkpoint path paired with an output artifact."""

    return output_path.with_name(f"{output_path.stem}.records.jsonl")


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for pilot and full benchmark runs."""

    parser = argparse.ArgumentParser(
        description="Run BrandMind vs hybrid search vs HippoRAG answer-flow eval."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--checkpoint-path",
        type=Path,
        default=None,
        help="JSONL checkpoint path. Defaults to <output stem>.records.jsonl.",
    )
    parser.add_argument(
        "--no-checkpoint",
        action="store_true",
        help="Disable incremental JSONL checkpoint writes.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip item/system records already present in the checkpoint.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Maximum number of item/system answer flows to run concurrently.",
    )
    parser.add_argument(
        "--progress-interval",
        type=int,
        default=10,
        help="Print progress every N completed records; use 0 to disable.",
    )
    parser.add_argument("--systems", default="all")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument(
        "--answer-provider",
        choices=["auto", "gemini", "litellm"],
        default="auto",
        help=(
            "Answer model provider. Auto uses Gemini for gemini-* IDs and "
            "LiteLLM/OpenAI-compatible routing for other model IDs."
        ),
    )
    parser.add_argument("--answer-model", default="gemini-2.5-flash-lite")
    parser.add_argument(
        "--judge-provider",
        choices=["auto", "gemini", "litellm"],
        default="auto",
        help=(
            "Judge model provider. Auto uses Gemini for gemini-* IDs and "
            "LiteLLM/OpenAI-compatible routing for other model IDs."
        ),
    )
    parser.add_argument("--judge-model", default="gemini-2.5-flash")
    parser.add_argument("--judge-temperature", type=float, default=0.0)
    parser.add_argument("--judge-thinking-budget", type=int, default=2000)
    parser.add_argument(
        "--judge-thinking-level",
        "--judge-reasoning-effort",
        dest="judge_thinking_level",
        choices=["minimal", "low", "medium", "high"],
        default=None,
        help="LiteLLM/OpenAI-compatible reasoning effort for the judge model.",
    )
    parser.add_argument("--answer-temperature", type=float, default=0.1)
    parser.add_argument("--answer-thinking-budget", type=int, default=2000)
    parser.add_argument(
        "--answer-thinking-level",
        "--answer-reasoning-effort",
        dest="answer_thinking_level",
        choices=["minimal", "low", "medium", "high"],
        default=None,
        help="Gemini 3 thinking level; alias accepts reasoning-effort wording.",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--candidate-top-k", type=int, default=10)
    parser.add_argument("--max-tool-calls", type=int, default=4)
    parser.add_argument("--recursion-limit", type=int, default=60)
    parser.add_argument(
        "--brandmind-evidence-recovery",
        action="store_true",
        help="Let BrandMind run one document recovery pass after KG-only answers.",
    )
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
    checkpoint_path = (
        None
        if args.no_checkpoint
        else args.checkpoint_path or build_default_checkpoint_path(output_path)
    )
    config = ComparisonRunConfig(
        dataset_path=args.dataset,
        output_path=output_path,
        checkpoint_path=checkpoint_path,
        resume=args.resume,
        concurrency=args.concurrency,
        progress_interval=args.progress_interval,
        systems=parse_systems(args.systems),
        answer_provider=args.answer_provider,
        answer_model=args.answer_model,
        judge_provider=args.judge_provider,
        judge_model=args.judge_model,
        judge_temperature=args.judge_temperature,
        judge_thinking_budget=args.judge_thinking_budget,
        judge_thinking_level=args.judge_thinking_level,
        answer_temperature=args.answer_temperature,
        answer_thinking_budget=args.answer_thinking_budget,
        answer_thinking_level=args.answer_thinking_level,
        top_k=args.top_k,
        candidate_top_k=args.candidate_top_k,
        max_tool_calls=args.max_tool_calls,
        recursion_limit=args.recursion_limit,
        brandmind_evidence_recovery=args.brandmind_evidence_recovery,
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
