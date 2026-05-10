"""Report helpers for knowledge-search comparison result artifacts."""

from __future__ import annotations

from evaluation.knowledge_search_comparison.schemas import (
    AnswerFlowRecord,
    ComparisonRunResult,
    ComparisonSystem,
    SystemSummary,
    summarize_records,
)


def build_report_lines(run_result: ComparisonRunResult) -> list[str]:
    """Build a compact text report from a comparison run result."""

    lines = [
        f"Run ID: {run_result.run_id}",
        f"Dataset: {run_result.dataset_id} v{run_result.dataset_version}",
        "",
        "System summaries:",
    ]
    for summary in sorted(
        run_result.summaries,
        key=lambda item: item.system.value,
    ):
        accuracy = (
            summary.correct_items / summary.total_items if summary.total_items else 0.0
        )
        lines.append(
            (
                f"- {summary.system.value}: accuracy={accuracy:.1%}, "
                f"fact_coverage={summary.mean_fact_coverage:.1%}, "
                f"errors={summary.error_items}, "
                f"avg_tools={summary.mean_tool_calls:.2f}, "
                f"avg_latency_ms={summary.mean_latency_ms:.0f}"
            )
        )
    return lines


def summarize_by_system(
    records: list[AnswerFlowRecord],
) -> dict[ComparisonSystem, SystemSummary]:
    """Return run summaries keyed by comparison system."""

    return {summary.system: summary for summary in summarize_records(records)}
