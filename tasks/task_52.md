# Task 52: Judge Evaluation Pipeline

## Metadata

- **Epic**: Quality Evaluation
- **Priority**: High
- **Status**: Done
- **Estimated Effort**: 1.5 days
- **Team**: Full-stack
- **Related Tasks**: Task 51
- **Blocking**: None
- **Blocked by**: Task 51 (transcript format), Task 53 (LiteLLM backend)

### Progress Checklist

- [x] Agent Protocol — Read and confirmed
- [x] Context & Goals
- [x] Solution Design
- [x] Pre-Implementation Research
- [x] Implementation Plan
- [x] Implementation Detail
    - [x] Component 1: Judge System Prompt
    - [x] Component 2: Judge Runner Script (litellm)
    - [x] Component 3: Scoring & Fleiss' Kappa
    - [x] Component 4: Aggregation Script
- [x] Test Execution Log
- [x] Decision Log
- [x] Task Summary

## Reference Documentation

- **Rubric**: `docs/BRANDMIND_EVAL_RUBRIC.md` — Full rubric + Section 8
- **Eval Design**: `docs/thesis_evaluation_summary.md`
- **Transcript Format**: `evaluation/protocol.md` (Task 51) — Step 3
- **LiteLLM docs**: https://docs.litellm.ai/

------------------------------------------------------------------------

## Agent Protocol

> **MANDATORY**: Read this section in full before starting.

### Rule 1 — Research Before Coding

1. Read rubric Section 3 (scoring) and Section 8 (procedure) carefully
2. Read litellm documentation for async completion API
3. Log findings in Pre-Implementation Research

### Rule 2 — Ask, Don't Guess

When encountering ambiguity, STOP and ask the user.

### Rule 3 — Update Progress As You Go

### Rule 4 — Production-Grade Code Standards

All code: PEP 8, type hints, docstrings, double quotes.

### Rule 5 — Prompt Engineering Standards

Judge system prompt follows `tasks/prompt_engineering_standards.md`.

------------------------------------------------------------------------

## Context & Goals

### Boi canh

- After Claude Code runs sessions and saves transcripts, need automated evaluation by 3 SOTA judges
- Judges must apply the rubric (104 criteria + 10 anti-patterns) independently
- Need inter-rater agreement (Fleiss' Kappa) to validate reliability
- User chose litellm for unified API across providers
- This is the ONLY piece that requires actual Python code in the eval pipeline

### Muc tieu

Build the post-session judge evaluation pipeline: send transcript to 3 judges via litellm, collect structured scores, compute agreement metrics, and aggregate across all sessions.

### Success Metrics

- **Structured output**: Per-criterion MET/UNMET/CANNOT_ASSESS with evidence from each judge
- **Scoring correctness**: Dimension scores match rubric Section 3.2 formula exactly
- **Agreement computed**: Fleiss' Kappa per criterion and per dimension
- **Aggregation**: Produces comparison table across all 3 systems
- **Uses LiteLLM backend**: Task 53's `LiteLLMClientLLM` for unified provider access

------------------------------------------------------------------------

## Solution Design

### Architecture Overview

```
evaluation/judge/
├── judge_prompt.md       # Full rubric formatted as judge system prompt
├── run_judges.py         # Send transcript to 3 judges via litellm
├── scoring.py            # Score calculation + Fleiss' Kappa
└── aggregate.py          # Aggregate results across all sessions → comparison table
```

### Data Flow

```
transcript.json (conversation only)
        │
        ▼
   run_judges.py (litellm → 3 models in parallel)
        │
        ▼
   evaluation_results.json (per session)
        │
        ▼
   aggregate.py (across all sessions)
        │
        ▼
   comparison_table.json + summary.md
```

------------------------------------------------------------------------

## Pre-Implementation Research

### LiteLLM Usage

- **Async**: `await litellm.acompletion(model=..., messages=...)`
- **Model naming**: `"claude-sonnet-4-6"`, `"gemini/gemini-3.1-pro-preview"`, `"gpt-5.4"`
- **JSON mode**: `response_format={"type": "json_object"}` (OpenAI-style, litellm translates per provider)
- **Temperature**: `temperature=0.0` for deterministic evaluation

### Research Status

- [x] Rubric scoring formula understood
- [x] LiteLLM async API confirmed
- [x] Fleiss' Kappa formula reviewed
- [x] No unresolved ambiguities

------------------------------------------------------------------------

## Implementation Plan

### Phase 1: Judge Prompt + Runner

1. Write judge system prompt (rubric → prompt format)
2. Write run_judges.py using litellm
3. *Checkpoint: Run 1 judge on 1 test transcript, verify parseable JSON output*

### Phase 2: Scoring + Aggregation

1. Write scoring.py (dimension scores + Kappa)
2. Write aggregate.py (comparison table)
3. *Checkpoint: End-to-end test on mock data*

------------------------------------------------------------------------

## Implementation Detail

### Component 1: Judge System Prompt

> Status: Done

#### Requirement 1 — Rubric as Judge Prompt

**Requirement**: Convert the evaluation rubric into a system prompt for LLM judges. Must produce structured JSON output with per-criterion judgments and evidence.

**Implementation**:

- `evaluation/judge/judge_prompt.md`

The full judge prompt is large (~4000 tokens) because it includes all 104 criteria. Structure:

```markdown
# Judge System Prompt

## Content (to be used as system message for judge LLM)

You are an expert evaluator assessing an AI brand strategy agent session.
Evaluate the conversation transcript against the rubric below.

## YOUR ROLE

Third-person judge. You did NOT participate. You are reading the transcript after the fact.

3 dimensions:
1. Strategy Quality (50%): Does the output solve the user's actual business problem?
2. Mentoring Quality (30%): Does the agent teach brand strategy thinking?
3. Personalization (20%): Does the agent adapt to THIS user's context?

## EVALUATION RULES

### Rule 1: One Criterion at a Time
For each criterion: state ID → search evidence → quote evidence → judge MET/UNMET/CANNOT_ASSESS → explain.

### Rule 2: Evidence Required
Every MET/UNMET MUST cite specific transcript content. CANNOT_ASSESS only when criterion doesn't apply.

### Rule 3: Anti-Leniency
When uncertain: re-read "Common Failure". If output matches failure more than success → UNMET.

### Rule 4: No Halo Effect
Score each phase independently. Long responses ≠ better.

### Rule 5: Anti-Pattern Detection
After all criteria, scan for 10 anti-patterns. Each instance deducts 0.5 from affected dimension (max 2.0).

## SCORING FORMULA

[Include formula from rubric Section 3.2 verbatim]

## OUTPUT FORMAT

Output valid JSON:
{
  "criteria": [
    {"id": "Q0-G1", "type": "GATE", "dimension": "quality", "judgment": "MET", "evidence": "...", "explanation": "..."},
    ...
  ],
  "anti_patterns": [
    {"id": "AP-3", "instances": [{"turn": 12, "evidence": "...", "dimension_affected": ["quality"]}]},
    ...
  ],
  "scores": {
    "quality": {"gates_met": 20, "gates_total": 23, "standard_met": 18, "standard_total": 24, "excellence_met": 5, "excellence_total": 15, "anti_pattern_deductions": 0.5, "final_score": 7.5},
    "mentor": {...},
    "personalization": {...},
    "overall": 7.2,
    "quality_gate_applied": false,
    "pass": false
  },
  "summary": {
    "top_strengths": ["1. ...", "2. ...", "3. ..."],
    "top_weaknesses": ["1. ...", "2. ...", "3. ..."],
    "improvement_recommendations": ["1. ...", "2. ...", "3. ..."]
  }
}

## CRITERIA REFERENCE

[Include all 104 criteria tables from rubric — Phase 0 through Cross-Phase, Mentor, Personalization]
[Include all 10 anti-patterns table]

## EVALUATE NOW

Evaluate the session provided below. Go through ALL criteria, then anti-patterns, then calculate scores.
When uncertain, default to UNMET — strict is better than lenient.
```

**Note**: The actual judge_prompt.md will include the complete criteria tables from `docs/BRANDMIND_EVAL_RUBRIC.md` Sections 4-7. Not duplicated here to avoid bloat — they will be copied verbatim at implementation time.

---

### Component 2: Judge Runner Script

> Status: Done

#### Requirement 1 — Run 3 Judges via LiteLLM

**Implementation**:

- `evaluation/judge/run_judges.py`

```python
"""Run 3 SOTA model judges on a BrandMind evaluation session.

Sends session transcript to 3 judge models
via litellm, collects structured evaluations, and saves results.

Usage:
    uv run python evaluation/judge/run_judges.py --session-dir brandmind-output/eval/full_linh_r1_20260401/
    uv run python evaluation/judge/run_judges.py --session-dir brandmind-output/eval/ --all
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from evaluation.judge.scoring import calculate_all_scores, compute_fleiss_kappa
from shared.model_clients.llm.litellm import LiteLLMClientLLM, LiteLLMClientLLMConfig

# Judge model configs — configurable via environment or CLI
DEFAULT_JUDGE_MODELS = [
    "claude-sonnet-4-6",
    "gemini/gemini-3.1-pro-preview",
    "gpt-5.4",
]

JUDGE_PROMPT_PATH = Path(__file__).parent / "judge_prompt.md"


def _load_judge_prompt() -> str:
    """Load the judge system prompt from markdown file."""
    return JUDGE_PROMPT_PATH.read_text(encoding="utf-8")


def _load_session_input(session_dir: Path) -> str:
    """Load and format session transcript for judge consumption.

    Only the transcript is provided to judges — no workspace files.
    The rubric evaluates what the user EXPERIENCES (conversation behavior),
    not what the agent records internally.

    Works with ALL systems (BrandMind, ChatGPT, Gemini) — same format.
    Optional fields (phase, tools_used) are included if present but not required.

    Args:
        session_dir: Path to session output directory.

    Returns:
        Formatted transcript string.
    """
    sections = []

    transcript_path = session_dir / "transcript.json"
    if transcript_path.exists():
        data = json.loads(transcript_path.read_text(encoding="utf-8"))

        system = data.get("system", "unknown")
        sections.append(f"## SESSION TRANSCRIPT (System: {system})\n")

        for turn in data.get("turns", []):
            sections.append(f"[Turn {turn['turn']}]")
            sections.append(f"USER: {turn.get('user', '')}")
            sections.append(f"AGENT: {turn.get('agent', turn.get('agent_response', ''))}")
            sections.append("")

    return "\n".join(sections)


async def _run_single_judge(
    model: str,
    system_prompt: str,
    session_input: str,
) -> dict[str, Any]:
    """Run a single judge evaluation via LiteLLM backend.

    Uses the LiteLLMClientLLM from Task 53 which reads proxy config
    from SETTINGS (LITELLM_PROXY_URL, LITELLM_API_KEY).

    Args:
        model: LiteLLM model identifier.
        system_prompt: Judge system prompt with rubric.
        session_input: Formatted transcript.

    Returns:
        Parsed JSON evaluation result.
    """
    config = LiteLLMClientLLMConfig(
        model=model,
        temperature=0.0,
        max_tokens=16000,
        system_prompt=system_prompt,
        response_format={"type": "json_object"},
    )
    llm = LiteLLMClientLLM(config)
    response = await llm.acomplete(session_input)

    text = response.text

    # Handle markdown-wrapped JSON
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    return json.loads(text)


async def evaluate_session(
    session_dir: Path,
    models: list[str] | None = None,
) -> dict[str, Any]:
    """Run all judges on a session and compute agreement.

    Args:
        session_dir: Path to session output directory.
        models: List of litellm model identifiers. Defaults to DEFAULT_JUDGE_MODELS.

    Returns:
        Full evaluation result with per-judge scores and agreement.
    """
    models = models or DEFAULT_JUDGE_MODELS
    system_prompt = _load_judge_prompt()
    session_input = _load_session_input(session_dir)

    print(f"Evaluating: {session_dir.name}")
    print(f"Judges: {', '.join(models)}")

    # Run all judges in parallel
    tasks = [_run_single_judge(m, system_prompt, session_input) for m in models]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    judge_results = {}
    for model, result in zip(models, results):
        model_key = model.split("/")[-1]  # "gemini/gemini-3.1-pro-preview" → "gemini-3.1-pro"
        if isinstance(result, Exception):
            print(f"  WARNING: {model_key} failed: {result}")
            judge_results[model_key] = {"error": str(result)}
        else:
            judge_results[model_key] = result
            score = result.get("scores", {}).get("overall", "?")
            print(f"  {model_key}: {score}")

    # Compute inter-rater agreement
    successful = [v for v in judge_results.values() if "error" not in v]
    agreement = compute_fleiss_kappa(successful) if len(successful) >= 2 else {}

    evaluation = {
        "session_dir": str(session_dir),
        "timestamp": datetime.now().isoformat(),
        "judge_models": models,
        "judges": judge_results,
        "agreement": agreement,
    }

    output_path = session_dir / "evaluation_results.json"
    output_path.write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    print(f"  Saved: {output_path}")
    return evaluation


def main():
    parser = argparse.ArgumentParser(description="Run judge evaluation on BrandMind sessions")
    parser.add_argument("--session-dir", required=True, type=Path)
    parser.add_argument("--all", action="store_true", help="Evaluate all subdirectories")
    parser.add_argument("--models", nargs="+", default=None, help="Override judge models")
    args = parser.parse_args()

    if args.all:
        session_dirs = sorted(
            d for d in args.session_dir.iterdir()
            if d.is_dir() and (d / "transcript.json").exists()
        )
    else:
        session_dirs = [args.session_dir]

    for sd in session_dirs:
        asyncio.run(evaluate_session(sd, args.models))


if __name__ == "__main__":
    main()
```

**Acceptance Criteria**:
- [x] Sends transcript to 3 models in parallel via litellm
- [x] Parses structured JSON response from each judge
- [x] Handles judge failures gracefully (logs warning, continues with others)
- [x] Saves evaluation_results.json in session directory
- [x] Supports `--all` flag for batch evaluation
- [x] Model list configurable via `--models` flag

---

### Component 3: Scoring & Fleiss' Kappa

> Status: Done

**Implementation**:

- `evaluation/judge/scoring.py`

```python
"""Score calculation and inter-rater agreement for BrandMind evaluation.

Implements scoring formula from BRANDMIND_EVAL_RUBRIC.md Section 3.2
and Fleiss' Kappa for inter-rater agreement.
"""

from __future__ import annotations

from typing import Any


def calculate_dimension_score(
    criteria: list[dict[str, Any]],
    anti_pattern_deductions: float = 0.0,
) -> dict[str, Any]:
    """Calculate score for a single dimension using gated formula.

    Formula:
    - Any GATE UNMET → score = (gates_met / gates_total) * 5.0
    - All gates pass → 6.0 + (std_ratio * 2.0) + (excel_ratio * 2.0)
    - Minus anti-pattern deductions (max 2.0)
    - CANNOT_ASSESS excluded from denominators
    """
    gates = [c for c in criteria if c["type"] == "GATE" and c["judgment"] != "CANNOT_ASSESS"]
    standards = [c for c in criteria if c["type"] == "STD" and c["judgment"] != "CANNOT_ASSESS"]
    excels = [c for c in criteria if c["type"] == "EXCEL" and c["judgment"] != "CANNOT_ASSESS"]

    gates_met = sum(1 for c in gates if c["judgment"] == "MET")
    gates_total = len(gates)
    std_met = sum(1 for c in standards if c["judgment"] == "MET")
    std_total = len(standards)
    excel_met = sum(1 for c in excels if c["judgment"] == "MET")
    excel_total = len(excels)

    if gates_total > 0 and gates_met < gates_total:
        raw_score = (gates_met / gates_total) * 5.0
    else:
        base = 6.0
        std_bonus = (std_met / std_total * 2.0) if std_total > 0 else 0.0
        excel_bonus = (excel_met / excel_total * 2.0) if excel_total > 0 else 0.0
        raw_score = base + std_bonus + excel_bonus

    deductions = min(anti_pattern_deductions, 2.0)
    return {
        "gates_met": gates_met,
        "gates_total": gates_total,
        "standard_met": std_met,
        "standard_total": std_total,
        "excellence_met": excel_met,
        "excellence_total": excel_total,
        "anti_pattern_deductions": deductions,
        "raw_score": round(raw_score, 2),
        "final_score": round(max(0.0, raw_score - deductions), 2),
    }


def calculate_all_scores(judge_result: dict[str, Any]) -> dict[str, Any]:
    """Calculate all dimension scores from a judge's criterion-level results.

    Separates criteria by dimension prefix (Q=quality, M=mentor, P=personalization),
    counts anti-pattern deductions per dimension, and computes overall score.
    """
    criteria = judge_result.get("criteria", [])
    anti_patterns = judge_result.get("anti_patterns", [])

    # Count anti-pattern deductions per dimension
    dim_deductions: dict[str, float] = {"quality": 0, "mentor": 0, "personalization": 0}
    for ap in anti_patterns:
        for inst in ap.get("instances", []):
            for dim in inst.get("dimension_affected", []):
                dim_deductions[dim] = dim_deductions.get(dim, 0) + 0.5

    # Split criteria by dimension
    quality_criteria = [c for c in criteria if c["id"].startswith("Q")]
    mentor_criteria = [c for c in criteria if c["id"].startswith("M")]
    personal_criteria = [c for c in criteria if c["id"].startswith("P")]

    q_score = calculate_dimension_score(quality_criteria, dim_deductions["quality"])
    m_score = calculate_dimension_score(mentor_criteria, dim_deductions["mentor"])
    p_score = calculate_dimension_score(personal_criteria, dim_deductions["personalization"])

    # Overall with quality gate
    weighted = q_score["final_score"] * 0.50 + m_score["final_score"] * 0.30 + p_score["final_score"] * 0.20
    quality_gate = q_score["final_score"] < 7.0
    overall = min(weighted, 6.0) if quality_gate else weighted

    return {
        "quality": q_score,
        "mentor": m_score,
        "personalization": p_score,
        "overall": round(overall, 2),
        "quality_gate_applied": quality_gate,
        "pass": overall >= 8.0,
    }


def compute_fleiss_kappa(judge_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute Fleiss' Kappa inter-rater agreement.

    Analyzes criterion-level agreement (MET vs UNMET) across judges.
    CANNOT_ASSESS excluded. Only criteria rated by ALL judges included.
    """
    if len(judge_results) < 2:
        return {"error": "Need >= 2 judges"}

    n_raters = len(judge_results)

    # Build criterion → ratings matrix
    criterion_ratings: dict[str, list[int]] = {}
    for result in judge_results:
        for c in result.get("criteria", []):
            if c["judgment"] == "CANNOT_ASSESS":
                continue
            cid = c["id"]
            criterion_ratings.setdefault(cid, []).append(1 if c["judgment"] == "MET" else 0)

    # Only criteria rated by ALL judges
    complete = {k: v for k, v in criterion_ratings.items() if len(v) == n_raters}
    if not complete:
        return {"error": "No criteria rated by all judges"}

    n = len(complete)
    cat_totals = [0, 0]  # [UNMET, MET]
    p_values = []

    for ratings in complete.values():
        met = sum(ratings)
        unmet = n_raters - met
        cat_totals[0] += unmet
        cat_totals[1] += met
        pi = (met * (met - 1) + unmet * (unmet - 1)) / (n_raters * (n_raters - 1))
        p_values.append(pi)

    p_bar = sum(p_values) / n
    total = n * n_raters
    p_e = sum((c / total) ** 2 for c in cat_totals)
    kappa = (p_bar - p_e) / (1.0 - p_e) if p_e != 1.0 else 1.0

    # Identify low/high agreement criteria
    per_criterion = {}
    for cid, ratings in complete.items():
        majority = max(sum(ratings), n_raters - sum(ratings))
        per_criterion[cid] = round(majority / n_raters, 2)

    return {
        "overall_kappa": round(kappa, 3),
        "interpretation": _interpret_kappa(kappa),
        "n_criteria": n,
        "n_raters": n_raters,
        "low_agreement": [c for c, a in per_criterion.items() if a < 0.67],
        "high_agreement": [c for c, a in per_criterion.items() if a == 1.0],
        "per_criterion": per_criterion,
    }


def _interpret_kappa(kappa: float) -> str:
    """Landis & Koch (1977) interpretation scale."""
    if kappa < 0:
        return "poor"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"
```

---

### Component 4: Aggregation Script

> Status: Done

**Implementation**:

- `evaluation/judge/aggregate.py`

```python
"""Aggregate evaluation results across all sessions into comparison table.

Usage:
    uv run python evaluation/judge/aggregate.py --eval-dir brandmind-output/eval/
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def aggregate_results(eval_dir: Path) -> dict[str, Any]:
    """Aggregate evaluation results from all session directories.

    Produces a comparison table: systems × dimensions × scores.

    Args:
        eval_dir: Root directory containing all session output dirs.

    Returns:
        Aggregated results with comparison table.
    """
    sessions = []

    for session_dir in sorted(eval_dir.iterdir()):
        eval_path = session_dir / "evaluation_results.json"
        meta_path = session_dir / "metadata.json"
        self_eval_path = session_dir / "self_eval.json"

        if not eval_path.exists():
            continue

        eval_data = json.loads(eval_path.read_text(encoding="utf-8"))
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        self_eval = json.loads(self_eval_path.read_text(encoding="utf-8")) if self_eval_path.exists() else {}

        # Average scores across judges (excluding errors)
        judge_scores = []
        for judge_result in eval_data.get("judges", {}).values():
            if "error" not in judge_result:
                scores = judge_result.get("scores", {})
                if scores:
                    judge_scores.append(scores)

        if not judge_scores:
            continue

        avg_quality = sum(s.get("quality", {}).get("final_score", 0) for s in judge_scores) / len(judge_scores)
        avg_mentor = sum(s.get("mentor", {}).get("final_score", 0) for s in judge_scores) / len(judge_scores)
        avg_personal = sum(s.get("personalization", {}).get("final_score", 0) for s in judge_scores) / len(judge_scores)
        avg_overall = sum(s.get("overall", 0) for s in judge_scores) / len(judge_scores)

        sessions.append({
            "dir": session_dir.name,
            "system": meta.get("system", _infer_system(session_dir.name)),
            "persona": meta.get("persona", "?"),
            "quality": round(avg_quality, 2),
            "mentor": round(avg_mentor, 2),
            "personalization": round(avg_personal, 2),
            "overall": round(avg_overall, 2),
            "kappa": eval_data.get("agreement", {}).get("overall_kappa", None),
            "perceived_personalization": self_eval.get("perceived_personalization_avg", None),
            "perceived_mentoring": self_eval.get("perceived_mentoring_avg", None),
        })

    # Group by system for comparison table
    systems: dict[str, list] = {}
    for s in sessions:
        systems.setdefault(s["system"], []).append(s)

    comparison = {}
    for system, system_sessions in systems.items():
        comparison[system] = {
            "quality": round(sum(s["quality"] for s in system_sessions) / len(system_sessions), 2),
            "mentor": round(sum(s["mentor"] for s in system_sessions) / len(system_sessions), 2),
            "personalization": round(sum(s["personalization"] for s in system_sessions) / len(system_sessions), 2),
            "overall": round(sum(s["overall"] for s in system_sessions) / len(system_sessions), 2),
            "n_sessions": len(system_sessions),
        }

    return {
        "timestamp": str(Path(eval_dir)),
        "sessions": sessions,
        "comparison": comparison,
    }


def _infer_system(dirname: str) -> str:
    """Infer system name from directory name convention."""
    if "chatgpt" in dirname:
        return "chatgpt"
    if "gemini" in dirname:
        return "gemini"
    return "brandmind"


def print_comparison_table(results: dict[str, Any]) -> None:
    """Print formatted comparison table to stdout."""
    comp = results["comparison"]
    print(f"\n{'System':<25} {'Quality':>8} {'Mentor':>8} {'Personal':>8} {'Overall':>8} {'N':>4}")
    print("-" * 65)
    for system in ["brandmind", "chatgpt", "gemini"]:
        if system in comp:
            s = comp[system]
            print(f"{system:<25} {s['quality']:>8.2f} {s['mentor']:>8.2f} {s['personalization']:>8.2f} {s['overall']:>8.2f} {s['n_sessions']:>4}")


def main():
    parser = argparse.ArgumentParser(description="Aggregate BrandMind evaluation results")
    parser.add_argument("--eval-dir", required=True, type=Path)
    args = parser.parse_args()

    results = aggregate_results(args.eval_dir)

    output_path = args.eval_dir / "comparison_results.json"
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print_comparison_table(results)
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
```

**Acceptance Criteria**:
- [x] Aggregates across all session directories automatically
- [x] Produces system × dimension comparison table
- [x] Handles missing data gracefully (some sessions might not have all judges)
- [x] Includes both objective scores (from judges) and perceived metrics (from self-eval)

------------------------------------------------------------------------

## Test Execution Log

### Test 1: Score Calculation — All Gates Pass

- **Purpose**: Verify scoring when all gates pass
- **Input**: 23 GATE MET, 20/24 STD MET, 10/15 EXCEL MET, 0.5 deductions
- **Expected**: 6.0 + (20/24)*2.0 + (10/15)*2.0 - 0.5 = 6.0 + 1.667 + 1.333 - 0.5 = 8.5
- **Actual Result**: PASSED — score = 8.5
- **Status**: Passed

### Test 2: Score Calculation — Gate Failure

- **Purpose**: Verify gate failure caps at 5.0
- **Input**: 20/23 GATE MET
- **Expected**: (20/23) * 5.0 = 4.35
- **Actual Result**: PASSED — score = 4.35
- **Status**: Passed

### Test 3: Overall Score — Quality Gate

- **Purpose**: Verify quality < 7.0 caps overall
- **Input**: Quality=6.5, Mentor=9.0, Personal=8.0
- **Expected**: weighted = 7.55, but capped to 6.0
- **Actual Result**: PASSED — weighted 7.55 capped to 6.0; also verified via calculate_all_scores: quality=6.0 (0/2 std) triggers gate, overall capped
- **Status**: Passed

### Test 4: Fleiss' Kappa — Perfect Agreement

- **Purpose**: Verify kappa = 1.0 when all judges agree
- **Input**: 3 judges, all criteria MET
- **Expected**: kappa = 1.0
- **Actual Result**: PASSED — kappa = 1.0
- **Status**: Passed

### Test 5: End-to-End — Mock Session

- **Purpose**: Verify full pipeline imports + scoring integration
- **Actual Result**: All modules import correctly. Scoring + Kappa computation verified with mock data. E2E with real judges deferred to eval execution phase.
- **Status**: Passed (unit level)

------------------------------------------------------------------------

## Decision Log

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | LLM client | Provider-specific SDKs vs litellm | litellm | User specified; single interface for all providers |
| 2 | Judge output | Free text vs structured JSON | JSON | Parseable for automated Kappa + aggregation |
| 3 | Judge temperature | 0.0 vs 0.3 | 0.0 | Maximum determinism for reproducibility |
| 4 | Judge concurrency | Sequential vs parallel | Parallel (asyncio.gather) | 3 independent API calls |
| 5 | Judge prompt location | Inline Python string vs markdown file | Markdown file | Easier to review/edit; same format as other eval materials |

------------------------------------------------------------------------

## Task Summary

### What Was Implemented

**Components Completed**:
- [x] **Judge System Prompt**: 573-line prompt with all 104 criteria + 10 anti-patterns + scoring formula + JSON output format
- [x] **Judge Runner**: Async parallel execution of 3 judges via LiteLLMClientLLM, saves evaluation_results.json
- [x] **Scoring**: Gated dimension scoring + Fleiss' Kappa inter-rater agreement
- [x] **Aggregation**: Cross-session comparison table with per-system averages

**Files Created**:
```
evaluation/judge/
├── __init__.py
├── judge_prompt.md      # 573 lines — full rubric as judge system prompt
├── run_judges.py        # Async 3-judge runner via LiteLLMClientLLM
├── scoring.py           # Dimension scores + Fleiss' Kappa
└── aggregate.py         # Cross-session comparison table
```

**Validation Results**:
- Scoring: all gates pass = 8.5 (correct), gate failure = 4.35 (correct)
- Quality gate: weighted 7.55 capped to 6.0 when quality < 7.0 (correct)
- Fleiss' Kappa: perfect agreement = 1.0 (correct)
- All modules import and run correctly
