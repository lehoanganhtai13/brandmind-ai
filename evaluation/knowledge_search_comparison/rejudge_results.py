"""Re-judge existing knowledge-search comparison artifacts."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Literal, cast

from evaluation.hipporag_comparison.benchmark_schema import (
    BenchmarkDataset,
    BenchmarkItem,
)
from evaluation.knowledge_search_comparison.dataset import (
    DEFAULT_DATASET_PATH,
    load_benchmark_dataset,
)
from evaluation.knowledge_search_comparison.judge import (
    AnswerJudge,
    create_answer_judge,
)
from evaluation.knowledge_search_comparison.report import build_report_lines
from evaluation.knowledge_search_comparison.schemas import (
    AnswerFlowRecord,
    ComparisonRunConfig,
    ComparisonRunResult,
)


def resolve_dataset_path(
    *,
    run_result: ComparisonRunResult,
    override_path: Path | None,
) -> Path:
    """Resolve the dataset path for an existing result artifact.

    Args:
        run_result: Existing answer-flow result artifact.
        override_path: Optional caller-supplied dataset path.

    Returns:
        The dataset path to load for item labels.
    """

    if override_path is not None:
        return override_path
    if run_result.config.dataset_path.exists():
        return run_result.config.dataset_path
    return DEFAULT_DATASET_PATH


async def rejudge_records(
    *,
    records: list[AnswerFlowRecord],
    dataset: BenchmarkDataset,
    judge: AnswerJudge,
) -> list[AnswerFlowRecord]:
    """Replace judge results on answered records using the supplied judge.

    Args:
        records: Existing answer-flow records.
        dataset: Benchmark dataset containing answer-key labels.
        judge: Judge implementation to apply.

    Returns:
        Records with fresh judge results and original answer/tool diagnostics.

    Raises:
        ValueError: If a record references an item absent from the dataset.
    """

    items_by_id: dict[str, BenchmarkItem] = {item.id: item for item in dataset.items}
    rejudged_records: list[AnswerFlowRecord] = []
    for record in records:
        updated_record = record.model_copy(deep=True)
        if updated_record.error or not updated_record.final_answer.strip():
            updated_record.judge = None
            rejudged_records.append(updated_record)
            continue

        item = items_by_id.get(updated_record.item_id)
        if item is None:
            raise ValueError(f"Dataset does not contain item: {updated_record.item_id}")

        updated_record.judge = await judge.judge(
            item=item,
            candidate_answer=updated_record.final_answer,
        )
        rejudged_records.append(updated_record)
    return rejudged_records


def build_rejudge_config(
    *,
    original_config: ComparisonRunConfig,
    dataset_path: Path,
    output_path: Path,
    judge_provider: str,
    judge_model: str,
    judge_temperature: float,
    judge_thinking_budget: int | None,
    judge_thinking_level: str | None,
) -> ComparisonRunConfig:
    """Build a validated config for a re-judged output artifact."""

    config_payload = original_config.model_dump()
    config_payload.update(
        {
            "dataset_path": dataset_path,
            "output_path": output_path,
            "judge_provider": judge_provider,
            "judge_model": judge_model,
            "judge_temperature": judge_temperature,
            "judge_thinking_budget": judge_thinking_budget,
            "judge_thinking_level": judge_thinking_level,
        }
    )
    return ComparisonRunConfig.model_validate(config_payload)


async def rejudge_artifact(
    *,
    input_path: Path,
    output_path: Path,
    dataset_path: Path | None,
    judge_provider: str,
    judge_model: str,
    judge_temperature: float,
    judge_thinking_budget: int | None,
    judge_thinking_level: str | None,
) -> ComparisonRunResult:
    """Load, re-judge, and return one comparison result artifact."""

    run_result = ComparisonRunResult.model_validate_json(
        input_path.read_text(encoding="utf-8")
    )
    resolved_dataset_path = resolve_dataset_path(
        run_result=run_result,
        override_path=dataset_path,
    )
    dataset = load_benchmark_dataset(resolved_dataset_path)
    config = build_rejudge_config(
        original_config=run_result.config,
        dataset_path=resolved_dataset_path,
        output_path=output_path,
        judge_provider=judge_provider,
        judge_model=judge_model,
        judge_temperature=judge_temperature,
        judge_thinking_budget=judge_thinking_budget,
        judge_thinking_level=judge_thinking_level,
    )
    judge = create_answer_judge(
        provider=cast(Literal["gemini", "litellm"], config.judge_provider),
        model=config.judge_model,
        temperature=config.judge_temperature,
        thinking_budget=config.judge_thinking_budget,
        thinking_level=config.judge_thinking_level,
    )
    records = await rejudge_records(
        records=run_result.records,
        dataset=dataset,
        judge=judge,
    )
    return ComparisonRunResult(
        dataset_id=run_result.dataset_id,
        dataset_version=run_result.dataset_version,
        config=config,
        records=records,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for artifact re-judging."""

    parser = argparse.ArgumentParser(
        description="Re-judge an existing knowledge-search comparison artifact."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=None)
    parser.add_argument(
        "--judge-provider",
        choices=["auto", "gemini", "litellm"],
        default="auto",
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
    )
    return parser


def main() -> None:
    """Run the artifact re-judge CLI."""

    args = build_parser().parse_args()
    result = asyncio.run(
        rejudge_artifact(
            input_path=args.input,
            output_path=args.output,
            dataset_path=args.dataset,
            judge_provider=args.judge_provider,
            judge_model=args.judge_model,
            judge_temperature=args.judge_temperature,
            judge_thinking_budget=args.judge_thinking_budget,
            judge_thinking_level=args.judge_thinking_level,
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("\n".join(build_report_lines(result)))
    print(f"Saved re-judged results to {args.output}")


if __name__ == "__main__":
    main()
