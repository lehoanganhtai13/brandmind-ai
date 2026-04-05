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
