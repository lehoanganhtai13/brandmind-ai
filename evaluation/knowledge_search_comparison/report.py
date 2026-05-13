"""Report helpers for knowledge-search comparison result artifacts."""

from __future__ import annotations

from collections.abc import Callable

from evaluation.knowledge_search_comparison.schemas import (
    AnswerFlowRecord,
    ComparisonRunResult,
    ComparisonSystem,
    SystemSummary,
    summarize_records,
)

FULL_COVERAGE_THRESHOLD = 0.999
DEFAULT_MAX_DIAGNOSTIC_ITEMS = 5


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
    lines.extend(build_evaluator_v2_report_lines(run_result.records))
    lines.extend(build_stratified_report_lines(run_result.records))
    lines.extend(build_diagnostic_report_lines(run_result.records))
    return lines


def summarize_by_system(
    records: list[AnswerFlowRecord],
) -> dict[ComparisonSystem, SystemSummary]:
    """Return run summaries keyed by comparison system."""

    return {summary.system: summary for summary in summarize_records(records)}


def build_evaluator_v2_report_lines(
    records: list[AnswerFlowRecord],
) -> list[str]:
    """Build deterministic score views from existing judge fields."""

    if not records:
        return []

    lines = ["", "Deterministic evaluator v2 views:"]
    for system in sorted(
        {record.system for record in records}, key=lambda item: item.value
    ):
        system_records = [
            record for record in records if record.system is system and record.judge
        ]
        judged_count = len(system_records)
        raw_correct_count = sum(
            1 for record in system_records if record.judge and record.judge.is_correct
        )
        fact_complete_count = sum(
            1
            for record in system_records
            if record.judge and record.judge.fact_coverage >= FULL_COVERAGE_THRESHOLD
        )
        strict_supported_count = sum(
            1
            for record in system_records
            if record.judge
            and record.judge.fact_coverage >= FULL_COVERAGE_THRESHOLD
            and not record.judge.unsupported_claims
        )
        lines.append(
            (
                f"- {system.value}: raw_correct="
                f"{_format_rate(raw_correct_count, judged_count)}, "
                f"fact_complete={_format_rate(fact_complete_count, judged_count)}, "
                f"strict_supported="
                f"{_format_rate(strict_supported_count, judged_count)}, "
                f"judged={judged_count}"
            )
        )
    return lines


def build_stratified_report_lines(records: list[AnswerFlowRecord]) -> list[str]:
    """Build v2-hard stratified score summaries when metadata is present."""

    if not any(
        record.reasoning_type or record.required_source_count for record in records
    ):
        return []

    lines = ["", "Stratified diagnostics:"]
    lines.extend(
        build_dimension_report_lines(
            records,
            title="reasoning_type",
            value_getter=lambda record: record.reasoning_type,
        )
    )
    lines.extend(
        build_dimension_report_lines(
            records,
            title="required_source_count",
            value_getter=lambda record: (
                str(record.required_source_count)
                if record.required_source_count is not None
                else None
            ),
        )
    )
    lines.extend(
        build_dimension_report_lines(
            records,
            title="book_scope",
            value_getter=lambda record: record.book_scope,
        )
    )
    return lines


def build_dimension_report_lines(
    records: list[AnswerFlowRecord],
    *,
    title: str,
    value_getter: Callable[[AnswerFlowRecord], str | None],
) -> list[str]:
    """Build per-system fact coverage by one record metadata dimension."""

    values = sorted(
        {value_getter(record) for record in records if value_getter(record)}
    )
    if not values:
        return []

    lines = [f"- {title}:"]
    for value in values:
        value_records = [record for record in records if value_getter(record) == value]
        fragments = []
        for system in sorted(
            {record.system for record in value_records},
            key=lambda item: item.value,
        ):
            system_records = [
                record
                for record in value_records
                if record.system is system and record.judge is not None
            ]
            fact_coverages = [
                record.judge.fact_coverage
                for record in system_records
                if record.judge is not None
            ]
            correct_count = sum(
                1
                for record in system_records
                if record.judge is not None and record.judge.is_correct
            )
            fragments.append(
                (
                    f"{system.value} "
                    f"acc={_format_rate(correct_count, len(system_records))} "
                    f"fc={_format_float_rate(_mean_float(fact_coverages))}"
                )
            )
        lines.append(f"  - {value}: " + "; ".join(fragments))
    return lines


def build_diagnostic_report_lines(
    records: list[AnswerFlowRecord],
    *,
    max_items: int = DEFAULT_MAX_DIAGNOSTIC_ITEMS,
) -> list[str]:
    """Build judge and per-item delta diagnostics without changing scores."""

    if not records:
        return []

    lines = ["", "Judge diagnostics:"]
    for system in sorted(
        {record.system for record in records}, key=lambda item: item.value
    ):
        system_records = [
            record for record in records if record.system is system and record.judge
        ]
        full_coverage_false = [
            record.item_id
            for record in system_records
            if record.judge
            and not record.judge.is_correct
            and record.judge.fact_coverage >= FULL_COVERAGE_THRESHOLD
        ]
        correct_with_missing = [
            record.item_id
            for record in system_records
            if record.judge
            and record.judge.is_correct
            and record.judge.fact_coverage < FULL_COVERAGE_THRESHOLD
        ]
        unsupported_accepted = [
            record.item_id
            for record in system_records
            if record.judge
            and record.judge.is_correct
            and record.judge.unsupported_claims
        ]
        unsupported_rejected = [
            record.item_id
            for record in system_records
            if record.judge
            and not record.judge.is_correct
            and record.judge.unsupported_claims
        ]
        lines.append(
            (
                f"- {system.value}: coverage_1_false={len(full_coverage_false)} "
                f"[{_format_ids(full_coverage_false, max_items)}], "
                f"correct_with_missing={len(correct_with_missing)} "
                f"[{_format_ids(correct_with_missing, max_items)}], "
                f"unsupported_accepted={len(unsupported_accepted)} "
                f"[{_format_ids(unsupported_accepted, max_items)}], "
                f"unsupported_rejected={len(unsupported_rejected)} "
                f"[{_format_ids(unsupported_rejected, max_items)}]"
            )
        )

    delta_lines = build_top_coverage_delta_lines(records, max_items=max_items)
    if delta_lines:
        lines.extend(["", "Top fact-coverage deltas:", *delta_lines])
    return lines


def build_top_coverage_delta_lines(
    records: list[AnswerFlowRecord],
    *,
    max_items: int = DEFAULT_MAX_DIAGNOSTIC_ITEMS,
) -> list[str]:
    """Show items where compared systems diverge most on fact coverage."""

    coverages_by_item: dict[str, dict[ComparisonSystem, float]] = {}
    for record in records:
        if record.judge is None:
            continue
        coverages_by_item.setdefault(record.item_id, {})[record.system] = (
            record.judge.fact_coverage
        )

    deltas: list[tuple[float, str, dict[ComparisonSystem, float]]] = []
    for item_id, coverages in coverages_by_item.items():
        if len(coverages) < 2:
            continue
        values = list(coverages.values())
        deltas.append((max(values) - min(values), item_id, coverages))

    lines: list[str] = []
    for delta, item_id, coverages in sorted(deltas, reverse=True)[:max_items]:
        if delta <= 0:
            continue
        highest = max(coverages.values())
        lowest = min(coverages.values())
        leaders = [
            system.value
            for system, coverage in sorted(
                coverages.items(), key=lambda item: item[0].value
            )
            if coverage == highest
        ]
        trailers = [
            system.value
            for system, coverage in sorted(
                coverages.items(), key=lambda item: item[0].value
            )
            if coverage == lowest
        ]
        lines.append(
            (
                f"- {item_id}: delta={delta:.1%}, "
                f"leaders={','.join(leaders)}({highest:.1%}), "
                f"trailers={','.join(trailers)}({lowest:.1%})"
            )
        )
    return lines


def _format_ids(item_ids: list[str], limit: int) -> str:
    """Format a bounded item-ID list for compact terminal reports."""

    if not item_ids:
        return "-"
    visible_ids = item_ids[:limit]
    suffix = f", +{len(item_ids) - limit} more" if len(item_ids) > limit else ""
    return ", ".join(visible_ids) + suffix


def _format_rate(numerator: int, denominator: int) -> str:
    """Format a percentage while avoiding division by zero."""

    if denominator == 0:
        return "0.0%"
    return f"{numerator / denominator:.1%}"


def _mean_float(values: list[float]) -> float:
    """Return the arithmetic mean for a possibly empty float list."""

    return sum(values) / len(values) if values else 0.0


def _format_float_rate(value: float) -> str:
    """Format a float ratio as a percentage."""

    return f"{value:.1%}"
