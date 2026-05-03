"""Compute judge deviation against golden labels for Step 4-bis Phase 2.

Loads ``evaluation/judge/golden_labels.json`` (the 4th-expert-reviewer
ground truth) and the per-transcript ``evaluation_results.json`` for each
production judge, then renders a per-judge per-criterion alignment matrix
plus systematic-pattern aggregates. Output is human-readable Markdown at
``evaluation/judge/calibration_deviation_report.md`` so Phase 3 can target
prompt adjustments at concrete deviations.

The script does not call any LLM — verdicts come from cached evaluation
results and golden labels. Hold-out transcripts are excluded from the
aggregate to keep them unseen for Phase 4 validation.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

GOLDEN_PATH = Path("evaluation/judge/golden_labels.json")
EVAL_BASE = Path("brandmind-output/eval")
REPORT_PATH = Path("evaluation/judge/calibration_deviation_report.md")


def _load_golden() -> dict[str, Any]:
    """Load the golden label set produced by the 4th-expert reviewer."""
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def _load_judge_verdicts(transcript_id: str) -> dict[str, dict[str, str]]:
    """Return ``{judge_name: {criterion_id: verdict}}`` for one transcript.

    The verdict source is the cached ``evaluation_results.json`` written by
    ``run_judges.py``. ``judgment`` may be ``MET`` / ``UNMET`` /
    ``CANNOT_ASSESS`` (or an unexpected value, which we keep verbatim).

    Args:
        transcript_id (str): Pilot directory name under ``brandmind-output/eval``.

    Returns:
        verdicts (dict[str, dict[str, str]]): Outer key = judge model name,
            inner key = criterion ID, value = verdict string.
    """
    path = EVAL_BASE / transcript_id / "evaluation_results.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict[str, str]] = {}
    for judge_name, judge_data in data["judges"].items():
        per_judge: dict[str, str] = {}
        for crit in judge_data.get("criteria", []):
            cid = crit.get("id")
            if cid:
                per_judge[cid] = crit.get("judgment", "UNKNOWN")
        out[judge_name] = per_judge
    return out


def _confusion_row(judge_verdict: str, golden_verdict: str) -> str:
    """Classify a single (judge, golden) pair into a deviation bucket.

    The classifier turns the per-label outcome into one of five strings used
    by the report's aggregate counts. Any unknown verdict on either side is
    bucketed as ``"unknown"`` so it is visible in the totals instead of
    silently dropped.

    Args:
        judge_verdict (str): The judgment a production judge produced.
        golden_verdict (str): The 4th-expert-reviewer's golden judgment.

    Returns:
        bucket (str): One of ``aligned``, ``judge_lenient``,
            ``judge_strict``, ``cannot_assess_split``, or ``unknown``.
    """
    if judge_verdict == golden_verdict:
        return "aligned"
    if golden_verdict == "UNMET" and judge_verdict == "MET":
        return "judge_lenient"
    if golden_verdict == "MET" and judge_verdict == "UNMET":
        return "judge_strict"
    if "CANNOT_ASSESS" in {judge_verdict, golden_verdict}:
        return "cannot_assess_split"
    return "unknown"


def _aggregate_deviations(
    golden: dict[str, Any],
    transcripts: list[str],
) -> dict[str, dict[str, dict[str, int]]]:
    """Walk every (judge, criterion, transcript) tuple and tally buckets.

    Returns a nested map ``{judge: {criterion: {bucket: count}}}`` so the
    report can render per-criterion alignment as well as per-judge family
    aggregates.

    Args:
        golden (dict[str, Any]): The golden label set.
        transcripts (list[str]): Training transcript IDs to include.

    Returns:
        agg (dict): Nested counts keyed by judge → criterion → bucket.
    """
    agg: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )
    for crit_id, per_transcript in golden["criteria"].items():
        for transcript_id in transcripts:
            golden_verdict = per_transcript.get(transcript_id, {}).get("verdict")
            if not golden_verdict:
                continue
            judge_verdicts = _load_judge_verdicts(transcript_id)
            for judge_name, verdicts in judge_verdicts.items():
                judge_v = verdicts.get(crit_id, "MISSING")
                bucket = _confusion_row(judge_v, golden_verdict)
                agg[judge_name][crit_id][bucket] += 1
    return agg


def _alignment_rate(per_criterion: dict[str, dict[str, int]]) -> float:
    """Compute the per-judge alignment rate across all training labels."""
    total = sum(sum(buckets.values()) for buckets in per_criterion.values())
    aligned = sum(buckets.get("aligned", 0) for buckets in per_criterion.values())
    return aligned / total if total else 0.0


def _render_per_judge_section(
    judge_name: str,
    per_criterion: dict[str, dict[str, int]],
) -> str:
    """Produce the Markdown section for one judge's alignment matrix."""
    lines = [f"### Judge: `{judge_name}`", ""]
    rate = _alignment_rate(per_criterion)
    lines.append(
        f"**Aggregate alignment with golden across training labels: "
        f"{rate * 100:.1f}%**"
    )
    lines.append("")
    lines.append("| Criterion | aligned | judge lenient (MET when golden=UNMET) | "
                 "judge strict (UNMET when golden=MET) | other |")
    lines.append("|-----------|---------|---------------------------------------|"
                 "-------------------------------------|-------|")
    for crit_id in sorted(per_criterion.keys()):
        buckets = per_criterion[crit_id]
        aligned = buckets.get("aligned", 0)
        lenient = buckets.get("judge_lenient", 0)
        strict = buckets.get("judge_strict", 0)
        other = (
            buckets.get("cannot_assess_split", 0)
            + buckets.get("unknown", 0)
        )
        lines.append(
            f"| {crit_id} | {aligned} | {lenient} | {strict} | {other} |"
        )
    lines.append("")
    # Family-level patterns
    lenient_total = sum(b.get("judge_lenient", 0) for b in per_criterion.values())
    strict_total = sum(b.get("judge_strict", 0) for b in per_criterion.values())
    lines.append(
        f"**Pattern**: total lenient = {lenient_total}, total strict = "
        f"{strict_total}, dominant deviation = "
        f"{'lenient' if lenient_total > strict_total else 'strict'}"
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Render the calibration deviation report for the training set."""
    golden = _load_golden()
    training = golden["training_transcripts"]
    agg = _aggregate_deviations(golden, training)

    sections = [
        "# Calibration Deviation Report — Step 4-bis Phase 2",
        "",
        f"**Golden labels source**: `{GOLDEN_PATH}` (labeled by "
        f"`{golden.get('labeler')}` on {golden.get('labeled_at')})",
        f"**Training transcripts** (used for calibration): "
        f"{', '.join(training)}",
        f"**Hold-out transcripts** (held back for Phase 4): "
        f"{', '.join(golden.get('holdout_transcripts', []))}",
        "",
        "Each cell counts (criterion × transcript) tuples where the "
        "production judge's verdict differs from golden in the named "
        "direction. ``aligned`` means agreement; the remaining columns "
        "name the disagreement kind.",
        "",
    ]

    for judge_name in sorted(agg.keys()):
        sections.append(
            _render_per_judge_section(judge_name, agg[judge_name])
        )

    # Cross-judge family pattern summary
    sections.append("## Cross-judge family pattern summary")
    sections.append("")
    sections.append(
        "| Criterion | claude lenient/strict | gemini lenient/strict "
        "| gpt lenient/strict |"
    )
    sections.append(
        "|-----------|----------------------|---------------------|---|"
    )
    for crit_id in sorted(golden["criteria"].keys()):
        cells = []
        for jname in sorted(agg.keys()):
            buckets = agg[jname].get(crit_id, {})
            cells.append(
                f"{buckets.get('judge_lenient', 0)}/"
                f"{buckets.get('judge_strict', 0)}"
            )
        cells_str = " | ".join(cells)
        sections.append(f"| {crit_id} | {cells_str} |")
    sections.append("")

    # Phase 3 targeting hints
    sections.append("## Phase 3 prompt-adjustment targeting hints")
    sections.append("")
    for jname in sorted(agg.keys()):
        per = agg[jname]
        lenient_top = sorted(
            per.items(),
            key=lambda x: x[1].get("judge_lenient", 0),
            reverse=True,
        )[:3]
        strict_top = sorted(
            per.items(),
            key=lambda x: x[1].get("judge_strict", 0),
            reverse=True,
        )[:3]
        sections.append(f"### `{jname}`")
        sections.append("")
        sections.append("Top lenient deviations (judge MET, golden UNMET):")
        for crit_id, buckets in lenient_top:
            count = buckets.get("judge_lenient", 0)
            if count > 0:
                sections.append(f"- `{crit_id}`: {count} lenient labels")
        sections.append("")
        sections.append("Top strict deviations (judge UNMET, golden MET):")
        for crit_id, buckets in strict_top:
            count = buckets.get("judge_strict", 0)
            if count > 0:
                sections.append(f"- `{crit_id}`: {count} strict labels")
        sections.append("")

    REPORT_PATH.write_text("\n".join(sections), encoding="utf-8")
    print(f"Report written: {REPORT_PATH}")


if __name__ == "__main__":
    main()
