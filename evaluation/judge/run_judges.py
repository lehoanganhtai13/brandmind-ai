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
        reasoning_effort="medium",
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

    judge_results: dict[str, Any] = {}
    for model, result in zip(models, results):
        model_key = model.split("/")[-1]  # "gemini/gemini-3.1-pro-preview" → "gemini-3.1-pro"
        if isinstance(result, BaseException):
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
