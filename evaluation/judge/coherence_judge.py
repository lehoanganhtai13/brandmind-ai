"""B (Strategic Coherence) judge for BrandMind sessions.

Reads a chat transcript and scores 12 strategic-coherence criteria
spanning the problem to positioning to identity to communication to
KPI chain (Tier 1), the artifact-design rationale visibility window
that Phase A "decisions narrated, not hidden" identity edit targets
(Tier 2), and cross-cutting alignment (Integration tier). The judge
operates on chat-only transcripts so the same calibrated rubric is
fair across BrandMind, ChatGPT vanilla, and Gemini vanilla baselines
in Phase D-2 cross-system comparison.

The judge is a single LLM (Gemini 3.1 Pro) calling through the same
``GoogleAIClientLLM`` client the production content-check middleware
uses. Single-judge per dimension is the design choice for B/C: the
deliverable of a coherence verdict is one auditable reasoning chain,
not an averaged vote — averaging would dilute the synthesis. Judge
reliability is established via golden-alignment isolation testing
(see ``coherence_test_set/``) rather than cross-judge Kappa.

Usage:
    uv run python evaluation/judge/coherence_judge.py \\
        --session-dir brandmind-output/eval/<pilot>
    uv run python evaluation/judge/coherence_judge.py \\
        --test-set evaluation/judge/coherence_test_set/
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# Repo paths.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
for sub in ("config", "core/src", "shared/src"):
    p = _REPO_ROOT / "src" / sub
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from config.system_config import SETTINGS  # noqa: E402
from shared.model_clients.llm.google import (  # noqa: E402
    GoogleAIClientLLM,
    GoogleAIClientLLMConfig,
)

_RUBRIC_PATH = Path(__file__).resolve().parent / "coherence_rubric.md"

# Criterion identifiers in tier order. The rubric and the judge prompt
# reference these in the same sequence so the JSON output is stable.
_TIER_1_IDS = ("B1", "B2", "B3", "B4", "B5")
_TIER_2_IDS = ("B6", "B7", "B8", "B9")
_INTEGRATION_IDS = ("B10", "B11", "B12")
_ALL_CRITERIA_IDS = _TIER_1_IDS + _TIER_2_IDS + _INTEGRATION_IDS

_VALID_VERDICTS = ("COHERENT", "PARTIAL", "INCOHERENT")


# ---------------------------------------------------------------------------
# Verdict schema (returned by the LLM judge)
# ---------------------------------------------------------------------------


class CoherenceCriterionVerdict(BaseModel):
    """One judge verdict for a single B-criterion."""

    id: str = Field(..., description="Criterion identifier, e.g. 'B1'.")
    verdict: str = Field(
        ...,
        description="One of: COHERENT, PARTIAL, INCOHERENT.",
    )
    evidence: str = Field(
        ...,
        description=(
            "Short verbatim or near-verbatim quote from the transcript "
            "supporting the verdict. Use 'no evidence in transcript' "
            "when the criterion fails for absence of evidence."
        ),
    )
    explanation: str = Field(
        ...,
        description=(
            "One sentence explaining the verdict, grounded in the "
            "evidence and the criterion definition."
        ),
    )


class TierSummary(BaseModel):
    """Aggregate counts of verdicts within a tier."""

    coherent: int = Field(0, description="Count of COHERENT verdicts.")
    partial: int = Field(0, description="Count of PARTIAL verdicts.")
    incoherent: int = Field(0, description="Count of INCOHERENT verdicts.")


class CoherenceVerdict(BaseModel):
    """Full judge verdict over all 12 B-criteria for one transcript."""

    criteria: list[CoherenceCriterionVerdict] = Field(
        default_factory=list,
        description="Per-criterion verdicts in B1 through B12 order.",
    )
    tier1_summary: TierSummary = Field(
        default_factory=TierSummary,
        description="Summary counts for B1-B5.",
    )
    tier2_summary: TierSummary = Field(
        default_factory=TierSummary,
        description="Summary counts for B6-B9.",
    )
    integration_summary: TierSummary = Field(
        default_factory=TierSummary,
        description="Summary counts for B10-B12.",
    )
    score: float = Field(
        0.0,
        description=(
            "Weighted score 0-10 per rubric: 0.5*tier1 + 0.3*tier2 + "
            "0.2*integration where each tier is coherent fraction with "
            "PARTIAL counted as 0.5."
        ),
    )


# ---------------------------------------------------------------------------
# Result dataclasses (serialised to JSON for downstream tooling)
# ---------------------------------------------------------------------------


@dataclass
class CoherenceResult:
    """Coherence judge result for one transcript."""

    transcript_id: str
    transcript_path: str
    judge_model: str
    verdict: dict[str, Any] = field(default_factory=dict)
    error: str = ""


@dataclass
class AlignmentRow:
    """One row of the alignment table for the isolation test."""

    sample_id: str
    criterion_id: str
    expected: str
    actual: str
    aligned: bool


@dataclass
class AlignmentReport:
    """Aggregate alignment report from running the judge over the test set."""

    judge_model: str
    rubric_path: str
    samples_evaluated: int
    total_verdicts: int
    aligned_verdicts: int
    alignment_pct: float
    pass_threshold: float
    passed: bool
    per_sample: dict[str, dict[str, str]] = field(default_factory=dict)
    rows: list[AlignmentRow] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Transcript loading and formatting
# ---------------------------------------------------------------------------


def _load_transcript_data(path: Path) -> tuple[str, list[dict[str, Any]]]:
    """Return (transcript_id, turns_list) for a real pilot or synthetic sample.

    Real pilot directories store the chat at ``<session>/transcript.json``
    with shape ``{"turns": [{"turn": int, "user": str, "agent": str}, ...]}``.
    Synthetic samples in ``coherence_test_set/`` follow the same shape at
    the file root with an additional ``id`` field. This helper handles
    both inputs uniformly so callers do not need to branch.

    Args:
        path: Either a session directory containing ``transcript.json`` or
            a synthetic sample JSON file.

    Returns:
        ``(transcript_id, turns)`` where ``turns`` is a list of dicts with
        ``turn``, ``user``, ``agent`` keys. ``transcript_id`` is the
        sample id when present, otherwise the parent directory name.

    Raises:
        FileNotFoundError: When neither a sample file nor a transcript
            file is present at ``path``.
    """
    if path.is_dir():
        transcript_path = path / "transcript.json"
        if not transcript_path.is_file():
            raise FileNotFoundError(
                f"No transcript.json under {path}"
            )
        data = json.loads(transcript_path.read_text(encoding="utf-8"))
        return path.name, data.get("turns", [])
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        sample_id = data.get("id", path.stem)
        return sample_id, data.get("turns", [])
    raise FileNotFoundError(f"{path} is neither a directory nor a file")


def _format_transcript_for_judge(turns: list[dict[str, Any]]) -> str:
    """Return turn-by-turn text the judge reads as the source of truth."""
    chunks: list[str] = []
    for turn in turns:
        chunks.append(
            f"--- Turn {turn.get('turn', '?')} ---\n"
            f"USER: {turn.get('user', '').strip()}\n\n"
            f"AGENT: {turn.get('agent', '').strip()}"
        )
    return "\n\n".join(chunks)


# ---------------------------------------------------------------------------
# Judge invocation
# ---------------------------------------------------------------------------


_SYSTEM_PROMPT_TEMPLATE = """You are a Senior Brand Strategy peer reviewer evaluating Strategic Coherence in a Vietnamese F&B brand-strategy session. You read the full chat transcript between a junior marketer and the BrandMind agent, then assess whether the strategy hangs together as an integrated thing across phases. You evaluate REASONABLENESS, not optimality — a strategy can be COHERENT even if you would personally make different choices, as long as its parts align with each other and address the diagnosed problem.

You read ONLY the chat transcript provided. You do not see workspace files, rendered artifacts, or sub-agent internal output. Your judgment is grounded only in what the agent stated in the user-facing chat — that is what the user sees and must defend to her boss.

Apply the rubric below. Return verdicts in order B1 through B12, do not skip any criterion, and do not invent new criteria. Each verdict carries an evidence quote (short, taken verbatim or near-verbatim from the transcript) and a one-sentence explanation grounded in the evidence and the criterion definition. When a criterion fails for absence of evidence, the verdict is INCOHERENT with evidence "no evidence in transcript" — that is a valid verdict.

# RUBRIC

{rubric}
"""


_USER_PROMPT_TEMPLATE = """Score the 12 B-criteria against this transcript.

Required criteria (in order, score every one): {criteria_list}

=== TRANSCRIPT ===
{transcript_text}
=== END TRANSCRIPT ===

Return the JSON verdict per the schema. Score every criterion B1 through B12, do not skip any, and ensure each evidence quote is taken from the transcript above (not invented). The score field is computed as 0.5 * (tier1_coherent_count + 0.5 * tier1_partial_count) / 5 + 0.3 * (tier2_coherent_count + 0.5 * tier2_partial_count) / 4 + 0.2 * (integration_coherent_count + 0.5 * integration_partial_count) / 3, scaled to 0-10.
"""


def _build_llm(model_id: str) -> GoogleAIClientLLM:
    """Construct the judge LLM client lazily."""
    return GoogleAIClientLLM(
        config=GoogleAIClientLLMConfig(
            model=model_id,
            api_key=SETTINGS.GEMINI_API_KEY,
            temperature=1.0,
            thinking_level="medium",
            max_tokens=8000,
            response_mime_type="application/json",
            response_schema=CoherenceVerdict,
        )
    )


async def _judge_one_transcript(
    llm: GoogleAIClientLLM,
    transcript_id: str,
    turns: list[dict[str, Any]],
    rubric: str,
) -> tuple[CoherenceVerdict | None, str]:
    """Call the judge and return ``(verdict, error)``; one of them is empty."""
    transcript_text = _format_transcript_for_judge(turns)
    if not transcript_text.strip():
        return None, "empty transcript"

    criteria_list = ", ".join(_ALL_CRITERIA_IDS)
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(rubric=rubric)
    user_prompt = _USER_PROMPT_TEMPLATE.format(
        criteria_list=criteria_list,
        transcript_text=transcript_text,
    )
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    try:
        response = await llm.acomplete(full_prompt)
    except Exception as exc:  # noqa: BLE001
        return None, f"judge call failed: {exc}"

    parsed = _coerce_verdict(response.text)
    if parsed is None:
        return None, "verdict could not be parsed as JSON schema"
    return parsed, ""


def _coerce_verdict(raw: Any) -> CoherenceVerdict | None:
    """Best-effort coercion when the LLM returns dict / string / object."""
    if isinstance(raw, CoherenceVerdict):
        return raw
    if isinstance(raw, dict):
        try:
            return CoherenceVerdict(**raw)
        except Exception:  # noqa: BLE001
            return None
    if isinstance(raw, str):
        try:
            return CoherenceVerdict(**json.loads(raw))
        except Exception:  # noqa: BLE001
            return None
    return None


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


async def score_coherence(
    transcript_path: Path,
    judge_model: str = "gemini-3.1-pro-preview",
) -> CoherenceResult:
    """Run the B coherence judge over one transcript.

    Args:
        transcript_path: Either a session directory containing
            ``transcript.json`` or a synthetic sample JSON file.
        judge_model: Gemini model id used by the judge.

    Returns:
        :class:`CoherenceResult` with the parsed verdict (when the call
        succeeded) or an ``error`` string explaining why it did not.
    """
    rubric = _RUBRIC_PATH.read_text(encoding="utf-8")
    transcript_id, turns = _load_transcript_data(transcript_path)
    llm = _build_llm(judge_model)
    verdict, error = await _judge_one_transcript(
        llm=llm,
        transcript_id=transcript_id,
        turns=turns,
        rubric=rubric,
    )
    return CoherenceResult(
        transcript_id=transcript_id,
        transcript_path=str(transcript_path),
        judge_model=judge_model,
        verdict=verdict.model_dump() if verdict else {},
        error=error,
    )


async def score_test_set(
    test_set_dir: Path,
    judge_model: str = "gemini-3.1-pro-preview",
    pass_threshold: float = 0.80,
) -> AlignmentReport:
    """Run the judge over the synthetic isolation test set + measure alignment.

    Args:
        test_set_dir: Directory containing sample ``*.json`` files plus
            ``expected_verdicts.json``.
        judge_model: Gemini model id used by the judge.
        pass_threshold: Minimum alignment fraction required to pass the
            kill gate (default 0.80 per Phase B Step 2 plan).

    Returns:
        :class:`AlignmentReport` summarising per-sample alignment plus
        the aggregate pass / fail decision against ``pass_threshold``.
    """
    expected_path = test_set_dir / "expected_verdicts.json"
    if not expected_path.is_file():
        raise FileNotFoundError(
            f"expected_verdicts.json missing under {test_set_dir}"
        )
    expected_all = json.loads(expected_path.read_text(encoding="utf-8"))
    expected_all.pop("_metadata", None)

    rubric = _RUBRIC_PATH.read_text(encoding="utf-8")
    llm = _build_llm(judge_model)

    rows: list[AlignmentRow] = []
    per_sample: dict[str, dict[str, str]] = {}
    aligned = 0
    total = 0

    for sample_path in sorted(test_set_dir.glob("*.json")):
        if sample_path.name == "expected_verdicts.json":
            continue
        sample_id = sample_path.stem
        if sample_id not in expected_all:
            continue
        _, turns = _load_transcript_data(sample_path)
        verdict, error = await _judge_one_transcript(
            llm=llm,
            transcript_id=sample_id,
            turns=turns,
            rubric=rubric,
        )
        if verdict is None:
            per_sample[sample_id] = {"_error": error}
            for criterion_id in _ALL_CRITERIA_IDS:
                rows.append(
                    AlignmentRow(
                        sample_id=sample_id,
                        criterion_id=criterion_id,
                        expected=expected_all[sample_id]
                        .get(criterion_id, {})
                        .get("verdict", ""),
                        actual="",
                        aligned=False,
                    )
                )
                total += 1
            continue
        actual_by_id = {c.id: c.verdict for c in verdict.criteria}
        per_sample[sample_id] = actual_by_id
        for criterion_id in _ALL_CRITERIA_IDS:
            expected = (
                expected_all[sample_id].get(criterion_id, {}).get("verdict", "")
            )
            actual = actual_by_id.get(criterion_id, "")
            is_aligned = expected == actual and expected in _VALID_VERDICTS
            rows.append(
                AlignmentRow(
                    sample_id=sample_id,
                    criterion_id=criterion_id,
                    expected=expected,
                    actual=actual,
                    aligned=is_aligned,
                )
            )
            total += 1
            if is_aligned:
                aligned += 1

    alignment_pct = aligned / total if total > 0 else 0.0
    return AlignmentReport(
        judge_model=judge_model,
        rubric_path=str(_RUBRIC_PATH),
        samples_evaluated=len(per_sample),
        total_verdicts=total,
        aligned_verdicts=aligned,
        alignment_pct=alignment_pct,
        pass_threshold=pass_threshold,
        passed=alignment_pct >= pass_threshold,
        per_sample=per_sample,
        rows=rows,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _format_alignment_summary(report: AlignmentReport) -> str:
    """Render a compact alignment table for terminal output."""
    lines: list[str] = []
    lines.append(f"Judge: {report.judge_model}")
    lines.append(
        f"Alignment: {report.aligned_verdicts}/{report.total_verdicts} "
        f"= {report.alignment_pct:.1%} (threshold {report.pass_threshold:.0%})"
    )
    status = "PASS" if report.passed else "FAIL"
    lines.append(f"Kill gate: {status}")
    lines.append("")
    by_sample: dict[str, list[AlignmentRow]] = {}
    for row in report.rows:
        by_sample.setdefault(row.sample_id, []).append(row)
    for sample_id, sample_rows in by_sample.items():
        sample_aligned = sum(1 for r in sample_rows if r.aligned)
        lines.append(f"--- {sample_id} ({sample_aligned}/{len(sample_rows)}) ---")
        for r in sample_rows:
            mark = "OK" if r.aligned else "X "
            lines.append(
                f"  [{mark}] {r.criterion_id}: expected={r.expected:<11} "
                f"actual={r.actual:<11}"
            )
    return "\n".join(lines)


def _format_single_summary(result: CoherenceResult) -> str:
    """Render a compact per-criterion table for one transcript."""
    lines: list[str] = []
    lines.append(f"Transcript: {result.transcript_id}")
    lines.append(f"Judge: {result.judge_model}")
    if result.error:
        lines.append(f"Error: {result.error}")
        return "\n".join(lines)
    verdict_data = result.verdict
    score = verdict_data.get("score", 0.0)
    lines.append(f"Score: {score:.2f} / 10")
    for tier_name, tier_key in (
        ("Tier 1 (B1-B5)", "tier1_summary"),
        ("Tier 2 (B6-B9)", "tier2_summary"),
        ("Integration (B10-B12)", "integration_summary"),
    ):
        summary = verdict_data.get(tier_key, {})
        lines.append(
            f"  {tier_name}: COHERENT={summary.get('coherent', 0)} "
            f"PARTIAL={summary.get('partial', 0)} "
            f"INCOHERENT={summary.get('incoherent', 0)}"
        )
    lines.append("")
    for criterion in verdict_data.get("criteria", []):
        lines.append(
            f"  {criterion.get('id', '?')}: {criterion.get('verdict', '?')} "
            f"— {criterion.get('explanation', '')}"
        )
    return "\n".join(lines)


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--session-dir",
        type=Path,
        help="Pilot session directory under brandmind-output/eval/.",
    )
    mode.add_argument(
        "--test-set",
        type=Path,
        help="Path to coherence_test_set/ for synthetic isolation test.",
    )
    parser.add_argument(
        "--judge-model",
        default="gemini-3.1-pro-preview",
        help="Gemini model id used by the coherence judge.",
    )
    parser.add_argument(
        "--pass-threshold",
        type=float,
        default=0.80,
        help="Alignment threshold for isolation test pass (default 0.80).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Path to write the JSON report (defaults to a sibling of input).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the raw report as JSON on stdout in addition to the summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    if not SETTINGS.GEMINI_API_KEY:
        print(
            "error: GEMINI_API_KEY is required (set env or load environments/.env)",
            file=sys.stderr,
        )
        return 2

    if args.test_set is not None:
        report = asyncio.run(
            score_test_set(
                test_set_dir=args.test_set,
                judge_model=args.judge_model,
                pass_threshold=args.pass_threshold,
            )
        )
        out_path = args.out or args.test_set / "isolation_test_report.json"
        out_path.write_text(
            json.dumps(asdict(report), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if args.json:
            print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
        else:
            print(_format_alignment_summary(report))
        return 0 if report.passed else 1

    result = asyncio.run(
        score_coherence(
            transcript_path=args.session_dir,
            judge_model=args.judge_model,
        )
    )
    out_path = args.out or args.session_dir / "coherence_judge.json"
    out_path.write_text(
        json.dumps(asdict(result), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print(_format_single_summary(result))
    return 0 if not result.error else 1


if __name__ == "__main__":
    raise SystemExit(main())
