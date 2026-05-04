"""Methodology overhaul re-scoring orchestration (Phase D-1 #6).

Re-scores BrandMind pilot transcripts under the post-calibration eval
methodology layer: calibrated chat rubric (Q + M + P + AP from Step
4-bis Phases 1-4 + M2-S2 iter 3) plus B (Strategic Coherence) judge
plus C (Strategic Problem-Solving) judge plus self-eval triangulation.
The combined score formula per `eval_methodology_overhaul_plan_2026_05_03.md`
is 0.30 * chat_process_avg + 0.30 * B_score + 0.30 * C_score + 0.10 *
self_eval_avg.

The script preserves the pre-calibration chat-rubric result (renaming
the existing ``evaluation_results.json`` to ``evaluation_results_pre_calibration.json``
on first run) before invoking the calibrated chat-rubric pipeline, so
the pre/post comparison stays auditable. B and C judges run with N
independent trials per pilot to surface variance from temperature 1.0
sampling; the trials' mean is used in the combined score and the
standard deviation is recorded as a stability signal.

Usage:
    uv run --env-file environments/.env python evaluation/judge/run_methodology_overhaul.py \\
        --pilots brandmind_linh_r10_20260430 brandmind_linh_r11_20260502 \\
                 brandmind_linh_r12_20260502 brandmind_linh_r13_20260503

Output: evaluation/judge/methodology_overhaul_summary.json — structured
summary of per-pilot scores plus aggregate stability / cluster diagnostics.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Repo paths.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
for sub in ("config", "core/src", "shared/src"):
    p = _REPO_ROOT / "src" / sub
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Allow importing sibling modules from evaluation/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from judge.coherence_judge import (  # type: ignore  # noqa: E402
    score_coherence,
)
from judge.problem_solving_judge import (  # type: ignore  # noqa: E402
    score_problem_solving,
)


_OUTPUT_ROOT = Path(__file__).resolve().parent.parent.parent / "brandmind-output" / "eval"
_RUN_JUDGES_SCRIPT = Path(__file__).resolve().parent / "run_judges.py"
_DEFAULT_JUDGE_MODEL = "gemini-3.1-pro-preview"


@dataclass
class TrialScore:
    """One judge trial result."""

    trial: int
    score: float
    n_criteria: int
    error: str = ""


@dataclass
class JudgeStability:
    """Aggregate of N trials for one judge on one pilot."""

    n_trials: int
    scores: list[float]
    mean: float
    std: float
    min: float
    max: float
    errors: list[str] = field(default_factory=list)


@dataclass
class PilotSummary:
    """Per-pilot summary under the methodology overhaul framework."""

    pilot_id: str
    pilot_dir: str
    chat_process_avg: float
    chat_process_pre_calibration: float
    coherence: JudgeStability
    problem_solving: JudgeStability
    self_eval_avg: float
    combined_score: float
    notes: list[str] = field(default_factory=list)


@dataclass
class OverhaulReport:
    """Aggregate report across all re-scored pilots."""

    pilots: list[PilotSummary] = field(default_factory=list)
    coherence_cluster_spread: float = 0.0
    problem_solving_cluster_spread: float = 0.0
    coherence_mean_std: float = 0.0
    problem_solving_mean_std: float = 0.0
    decision_gate_passed: bool = False
    decision_notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pre-calibration backup discipline
# ---------------------------------------------------------------------------


def _backup_pre_calibration_chat_result(session_dir: Path) -> tuple[float, str]:
    """Preserve the pre-calibration chat-rubric result before a calibrated re-run overwrites it.

    Maintains the audit comparison surface for pre vs post calibration verdicts on the same
    transcript. Idempotent across re-invocations on the same pilot directory.

    Args:
        session_dir (Path): Pilot session directory.

    Returns:
        result (tuple[float, str]): ``(pre_calibration_overall, status_note)`` — the overall
            score from the preserved pre-calibration result, or 0.0 with an explanatory note.
    """
    src = session_dir / "evaluation_results.json"
    backup = session_dir / "evaluation_results_pre_calibration.json"
    if backup.is_file():
        data = json.loads(backup.read_text(encoding="utf-8"))
        return _extract_chat_overall(data), "pre-calibration backup already in place"
    if not src.is_file():
        return 0.0, "no pre-calibration evaluation_results.json found"
    data = json.loads(src.read_text(encoding="utf-8"))
    backup.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return _extract_chat_overall(data), "pre-calibration result preserved as backup"


def _extract_chat_overall(data: dict[str, Any]) -> float:
    """Return the cross-judge overall score from a chat-rubric result file."""
    aggregate = data.get("aggregate", {}) or {}
    overall = aggregate.get("cross_judge_overall")
    if isinstance(overall, (int, float)):
        return float(overall)
    judges = data.get("judges", {}) or {}
    overalls: list[float] = []
    for judge_data in judges.values():
        scores = (judge_data or {}).get("scores", {}) or {}
        if "overall" in scores and isinstance(scores["overall"], (int, float)):
            overalls.append(float(scores["overall"]))
    return sum(overalls) / len(overalls) if overalls else 0.0


# ---------------------------------------------------------------------------
# Calibrated chat rubric runner
# ---------------------------------------------------------------------------


def _invalidate_chat_judge_cache(session_dir: Path) -> list[str]:
    """Clear the chat-rubric runner's cached output so the next invocation re-judges from scratch.

    The runner reuses checkpoint state when present, which is desirable for resumability but
    defeats re-runs that intend to apply an updated judge prompt. Caller is responsible for
    backing up any prior result needed for audit before invoking this helper.

    Args:
        session_dir (Path): Pilot session directory containing the runner's output files.

    Returns:
        deleted (list[str]): Names of files removed from the session directory, for the
            orchestration audit trail.
    """
    deleted: list[str] = []
    target_names = [
        "evaluation_results.json",
        "judge_openai-claude-sonnet-4_6.json",
        "judge_openai-claude-sonnet-4_6_checkpoint.json",
        "judge_gemini-gemini-3_1-pro-preview.json",
        "judge_gemini-gemini-3_1-pro-preview_checkpoint.json",
        "judge_openai-gpt-5_4.json",
        "judge_openai-gpt-5_4_checkpoint.json",
    ]
    for name in target_names:
        candidate = session_dir / name
        if candidate.is_file():
            candidate.unlink()
            deleted.append(name)
    return deleted


def _run_calibrated_chat_rubric(
    session_dir: Path, env_file: Path | None
) -> tuple[float, str]:
    """Invoke ``run_judges.py`` with the calibrated chat-rubric prompt.

    The chat-rubric runner is kept as a subprocess so its scoring
    logic stays single-sourced. Before invoking it, this function
    invalidates the pilot's cached judge files so the calibrated
    prompt is actually evaluated end-to-end rather than short-
    circuited via the runner's resume-from-checkpoint behaviour.
    The calibrated verdicts land at
    ``<session_dir>/evaluation_results.json`` and the per-judge
    intermediates are recreated alongside.

    Args:
        session_dir (Path): Pilot session directory the chat rubric
            should re-score.
        env_file (Path | None): Optional ``.env`` path forwarded to
            ``uv run --env-file`` so the subprocess inherits the
            same model API credentials as the orchestrator.

    Returns:
        result (tuple[float, str]): ``(overall_score, status_note)``
            where ``overall_score`` is the calibrated cross-judge
            overall and ``status_note`` summarises the invocation
            outcome for the orchestrator audit trail.
    """
    deleted = _invalidate_chat_judge_cache(session_dir)
    cmd: list[str] = ["uv", "run"]
    if env_file is not None:
        cmd.extend(["--env-file", str(env_file)])
    cmd.extend(
        [
            "python",
            str(_RUN_JUDGES_SCRIPT),
            "--session-dir",
            str(session_dir),
        ]
    )
    try:
        result = subprocess.run(
            cmd,
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=1800,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 0.0, "chat rubric subprocess timed out (30 min)"
    if result.returncode != 0:
        return (
            0.0,
            f"chat rubric subprocess failed rc={result.returncode}: "
            f"{result.stderr[-400:]}",
        )
    fresh_path = session_dir / "evaluation_results.json"
    if not fresh_path.is_file():
        return 0.0, "chat rubric subprocess succeeded but no result file"
    data = json.loads(fresh_path.read_text(encoding="utf-8"))
    cache_note = (
        f" (invalidated cache: {', '.join(deleted)})" if deleted else ""
    )
    return (
        _extract_chat_overall(data),
        f"calibrated chat rubric run completed{cache_note}",
    )


# ---------------------------------------------------------------------------
# B / C judge N-trial runners
# ---------------------------------------------------------------------------


async def _run_judge_n_trials(
    session_dir: Path,
    judge_model: str,
    n_trials: int,
    judge_kind: str,
) -> JudgeStability:
    """Run B or C judge N times and aggregate stability statistics.

    Args:
        session_dir: Pilot session directory.
        judge_model: Gemini model id used for both B and C.
        n_trials: Number of independent trials per judge.
        judge_kind: ``"coherence"`` or ``"problem_solving"``.

    Returns:
        :class:`JudgeStability` with per-trial scores plus mean / std /
        min / max + any per-trial errors.
    """
    scorer = (
        score_coherence
        if judge_kind == "coherence"
        else score_problem_solving
    )
    trial_scores: list[float] = []
    errors: list[str] = []
    for trial in range(1, n_trials + 1):
        result = await scorer(
            transcript_path=session_dir,
            judge_model=judge_model,
        )
        if result.error:
            errors.append(f"trial {trial}: {result.error}")
            continue
        score = float(result.verdict.get("score", 0.0))
        trial_scores.append(score)
        # Persist each trial individually so the audit trail covers every call.
        out_dir = session_dir / "methodology_overhaul"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{judge_kind}_trial_{trial}.json").write_text(
            json.dumps(asdict(result), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    if not trial_scores:
        return JudgeStability(
            n_trials=n_trials,
            scores=[],
            mean=0.0,
            std=0.0,
            min=0.0,
            max=0.0,
            errors=errors,
        )
    mean = statistics.mean(trial_scores)
    std = statistics.stdev(trial_scores) if len(trial_scores) > 1 else 0.0
    return JudgeStability(
        n_trials=n_trials,
        scores=trial_scores,
        mean=mean,
        std=std,
        min=min(trial_scores),
        max=max(trial_scores),
        errors=errors,
    )


# ---------------------------------------------------------------------------
# Self-eval loader
# ---------------------------------------------------------------------------


def _load_self_eval_avg(session_dir: Path) -> tuple[float, str]:
    """Return the self-eval average that contributes the 0.10 weight in the combined formula.

    Accepts three input schemas so legacy and canonical pilot output both score: the
    ``scores_1_to_10`` dimension dict documented in ``evaluation/self_eval.md``, an ``overall``
    + ``dimensions`` shape, and a per-question ``score`` shape. Pilots missing the file or
    holding no readable score fields contribute 0.0 to the formula.

    Args:
        session_dir (Path): Pilot session directory possibly holding a ``self_eval.json``.

    Returns:
        result (tuple[float, str]): ``(self_eval_avg, status_note)`` where ``self_eval_avg`` is
            0.0 when no usable scores were found and ``status_note`` records which schema
            branch matched (or why none did).
    """
    path = session_dir / "self_eval.json"
    if not path.is_file():
        return 0.0, "no self_eval.json present"
    data = json.loads(path.read_text(encoding="utf-8"))
    candidates: list[float] = []
    branches_matched: list[str] = []

    scores_1_to_10 = data.get("scores_1_to_10", {}) or {}
    if isinstance(scores_1_to_10, dict):
        for value in scores_1_to_10.values():
            if isinstance(value, (int, float)):
                candidates.append(float(value))
        if scores_1_to_10:
            branches_matched.append("scores_1_to_10")

    overall_node = data.get("overall")
    if isinstance(overall_node, dict):
        score = overall_node.get("score")
        if isinstance(score, (int, float)):
            candidates.append(float(score))
            branches_matched.append("overall.score")
    elif isinstance(overall_node, (int, float)):
        candidates.append(float(overall_node))
        branches_matched.append("overall")

    dims = data.get("dimensions", {}) or {}
    if isinstance(dims, dict):
        for dim in dims.values():
            if isinstance(dim, dict) and isinstance(dim.get("score"), (int, float)):
                candidates.append(float(dim["score"]))
        if dims:
            branches_matched.append("dimensions")

    if not candidates:
        return 0.0, "self_eval.json present but no usable score field found"
    averaged = sum(candidates) / len(candidates)
    return averaged, f"self-eval averaged across fields ({'+'.join(branches_matched)})"


# ---------------------------------------------------------------------------
# Combined score computation
# ---------------------------------------------------------------------------


def _compute_combined_score(
    chat_avg: float, b_mean: float, c_mean: float, self_eval_avg: float
) -> float:
    """Return the methodology-overhaul combined score for one pilot."""
    return 0.30 * chat_avg + 0.30 * b_mean + 0.30 * c_mean + 0.10 * self_eval_avg


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


async def re_score_pilot(
    pilot_dir: Path,
    judge_model: str,
    n_trials: int,
    env_file: Path | None,
    skip_chat_rubric: bool,
) -> PilotSummary:
    """Re-score one pilot under the methodology-overhaul framework.

    Args:
        pilot_dir: Pilot session directory under ``brandmind-output/eval/``.
        judge_model: Gemini model id used for B + C judges.
        n_trials: B / C trial count per pilot.
        env_file: Optional ``.env`` for the chat-rubric subprocess.
        skip_chat_rubric: When True, reuse the existing
            ``evaluation_results.json`` instead of re-running the
            calibrated chat-rubric pipeline. Useful for fast iteration
            on B / C portions.

    Returns:
        :class:`PilotSummary` with all computed fields populated.
    """
    notes: list[str] = []
    pre_overall, backup_note = _backup_pre_calibration_chat_result(pilot_dir)
    notes.append(backup_note)

    if skip_chat_rubric:
        existing = pilot_dir / "evaluation_results.json"
        if existing.is_file():
            data = json.loads(existing.read_text(encoding="utf-8"))
            chat_avg = _extract_chat_overall(data)
            notes.append("chat rubric reuse (skip-chat-rubric flag)")
        else:
            chat_avg = 0.0
            notes.append("skip-chat-rubric set but no existing result")
    else:
        chat_avg, chat_note = _run_calibrated_chat_rubric(pilot_dir, env_file)
        notes.append(chat_note)

    coherence_stability = await _run_judge_n_trials(
        session_dir=pilot_dir,
        judge_model=judge_model,
        n_trials=n_trials,
        judge_kind="coherence",
    )
    problem_solving_stability = await _run_judge_n_trials(
        session_dir=pilot_dir,
        judge_model=judge_model,
        n_trials=n_trials,
        judge_kind="problem_solving",
    )

    self_eval_avg, self_eval_note = _load_self_eval_avg(pilot_dir)
    notes.append(self_eval_note)

    combined = _compute_combined_score(
        chat_avg=chat_avg,
        b_mean=coherence_stability.mean,
        c_mean=problem_solving_stability.mean,
        self_eval_avg=self_eval_avg,
    )

    return PilotSummary(
        pilot_id=pilot_dir.name,
        pilot_dir=str(pilot_dir),
        chat_process_avg=chat_avg,
        chat_process_pre_calibration=pre_overall,
        coherence=coherence_stability,
        problem_solving=problem_solving_stability,
        self_eval_avg=self_eval_avg,
        combined_score=combined,
        notes=notes,
    )


def _evaluate_decision_gate(report: OverhaulReport) -> None:
    """Decide whether the methodology framework is reliable enough to use downstream.

    The gate exists so a script run is the source of truth for
    "framework cleared for D-1 #7 / D-2" without forcing the next
    maintainer to re-derive criteria from narrative analysis. It
    encodes only objective reliability properties — within-pilot
    determinism and reasonable absolute scoring scale — because
    those properties have a single right answer that an automated
    check can decide. Cross-pilot variation is computed and reported
    here for transparency, but it is interpretive (a wide spread can
    mean genuine system-state differentiation OR judge scatter,
    depending on within-pilot stability and criterion-level pattern)
    so its signal-vs-noise call belongs in narrative analysis where
    context can be evaluated, not in a boolean threshold.

    Args:
        report (OverhaulReport): Assembled per-pilot summaries; this
            function mutates the report in place to populate the
            cluster-spread, mean-std, decision_gate_passed, and
            decision_notes fields.

    Returns:
        None: Mutation-only contract; downstream code reads the
            updated report fields directly.
    """
    if not report.pilots:
        report.decision_notes.append("no pilots evaluated")
        return
    coh_means = [p.coherence.mean for p in report.pilots]
    ps_means = [p.problem_solving.mean for p in report.pilots]
    coh_stds = [p.coherence.std for p in report.pilots]
    ps_stds = [p.problem_solving.std for p in report.pilots]
    combined = [p.combined_score for p in report.pilots]

    report.coherence_cluster_spread = max(coh_means) - min(coh_means)
    report.problem_solving_cluster_spread = max(ps_means) - min(ps_means)
    report.coherence_mean_std = sum(coh_stds) / len(coh_stds)
    report.problem_solving_mean_std = sum(ps_stds) / len(ps_stds)

    # Bounds match the combined formula's realistic span: ~5.3 for a mediocre system,
    # ~8.3 for a strong one (rounded to 5.0-8.5 with buffer).
    range_ok = all(5.0 <= c <= 8.5 for c in combined)
    stability_ok = (
        report.coherence_mean_std <= 0.5
        and report.problem_solving_mean_std <= 0.5
    )

    report.decision_notes.append(
        f"B mean trial std {report.coherence_mean_std:.2f}, "
        f"C mean trial std {report.problem_solving_mean_std:.2f} "
        f"(stability_ok={stability_ok})"
    )
    report.decision_notes.append(
        f"combined score range {min(combined):.2f}-{max(combined):.2f} "
        f"(range_ok={range_ok})"
    )
    report.decision_notes.append(
        f"B cluster spread {report.coherence_cluster_spread:.2f}, "
        f"C cluster spread {report.problem_solving_cluster_spread:.2f} "
        f"(informational only — cross-pilot variation is interpretive; "
        f"trace to system-commit history in narrative analysis to "
        f"distinguish signal from noise)"
    )
    report.decision_gate_passed = stability_ok and range_ok


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pilots",
        nargs="+",
        required=True,
        help="Pilot session directory names under brandmind-output/eval/.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=_OUTPUT_ROOT,
        help="Root directory containing pilot sessions.",
    )
    parser.add_argument(
        "--judge-model",
        default=_DEFAULT_JUDGE_MODEL,
        help="Gemini model id used for B and C judges.",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=3,
        help="Number of B / C trial runs per pilot (default 3).",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Optional .env path passed to the chat-rubric subprocess.",
    )
    parser.add_argument(
        "--skip-chat-rubric",
        action="store_true",
        help="Skip re-running the calibrated chat rubric and reuse "
        "the existing evaluation_results.json (faster iteration).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "methodology_overhaul_summary.json",
        help="Path to write the aggregate summary JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    report = OverhaulReport()
    for pilot_name in args.pilots:
        pilot_dir = args.output_root / pilot_name
        if not pilot_dir.is_dir():
            print(f"warn: pilot dir missing: {pilot_dir}", file=sys.stderr)
            continue
        print(f"=== Re-scoring {pilot_name} ===", flush=True)
        summary = asyncio.run(
            re_score_pilot(
                pilot_dir=pilot_dir,
                judge_model=args.judge_model,
                n_trials=args.n_trials,
                env_file=args.env_file,
                skip_chat_rubric=args.skip_chat_rubric,
            )
        )
        report.pilots.append(summary)
        print(
            f"  chat={summary.chat_process_avg:.2f} "
            f"B={summary.coherence.mean:.2f}±{summary.coherence.std:.2f} "
            f"C={summary.problem_solving.mean:.2f}±{summary.problem_solving.std:.2f} "
            f"self={summary.self_eval_avg:.2f} "
            f"combined={summary.combined_score:.2f}",
            flush=True,
        )

    _evaluate_decision_gate(report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    status = "PASS" if report.decision_gate_passed else "FAIL"
    print()
    print(f"Decision gate: {status}")
    for note in report.decision_notes:
        print(f"  - {note}")
    return 0 if report.decision_gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
