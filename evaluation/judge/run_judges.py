"""Run 3 SOTA model judges on a BrandMind evaluation session.

Uses dimension-level batching (4 batches per judge: Quality, Mentor,
Personalization, Anti-Patterns) to fit within proxy upstream timeout
while preserving cross-phase context within each dimension.

Output: evaluation_results.json — backward-compatible with aggregate.py,
containing per-judge criteria + scores (via scoring.py) + Fleiss' Kappa.

Usage:
    uv run python evaluation/judge/run_judges.py --session-dir brandmind-output/eval/brandmind_linh_r1_20260409/
    uv run python evaluation/judge/run_judges.py --session-dir brandmind-output/eval/ --all
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from json_repair import repair_json

# Allow running as script from project root
_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from evaluation.judge.scoring import (  # noqa: E402
    calculate_all_scores,
    compute_fleiss_kappa,
)
from shared.model_clients.llm.litellm import (  # noqa: E402
    LiteLLMClientLLM,
    LiteLLMClientLLMConfig,
)

# Judge model configs — prefix determines routing:
# - "openai/..." → LiteLLM proxy (OpenAI-compatible). Use for Claude/GPT.
# - "gemini/..." → direct Google API via GEMINI_API_KEY. Use for Gemini (proxy
#   routing through openai/ prefix causes criteria truncation in output).
DEFAULT_JUDGE_MODELS = [
    "openai/claude-sonnet-4.6",
    "gemini/gemini-3.1-pro-preview",
    "openai/gpt-5.4",
]

JUDGE_PROMPT_PATH = Path(__file__).parent / "judge_prompt.md"

# Batch definitions: (batch_id, label, section_key, is_ap)
BATCHES: list[tuple[str, str, str, bool]] = [
    ("quality", "Strategy Quality", "quality", False),
    ("mentor", "Mentoring Quality", "mentor", False),
    ("personalization", "Personalization", "personalization", False),
    ("antipatterns", "Anti-Patterns", "antipatterns", True),
]


# ============================================================
# Rubric parsing
# ============================================================

def _parse_rubric_sections(rubric: str) -> dict[str, list[str]]:
    """Parse rubric into header / dimension sections / antipatterns / footer.

    Header: everything before "### Dimension 1:" (ROLE, RULES, SCORING, FORMAT).
    Dimension sections: criteria tables for Quality/Mentor/Personalization.
    Antipatterns: the 10 anti-patterns table.
    Footer: EVALUATION PROCEDURE onwards (sanity checks, "evaluate now").
    """
    lines = rubric.split("\n")
    sections: dict[str, list[str]] = {
        "header": [],
        "quality": [],
        "mentor": [],
        "personalization": [],
        "antipatterns": [],
        "footer": [],
    }

    cur = "header"
    for line in lines:
        if "### Dimension 1:" in line:
            cur = "quality"
        elif "### Dimension 2:" in line:
            cur = "mentor"
        elif "### Dimension 3:" in line:
            cur = "personalization"
        elif "### Anti-Patterns" in line:
            cur = "antipatterns"
        elif "## EVALUATION PROCEDURE" in line:
            cur = "footer"

        sections[cur].append(line)

    return sections


# ============================================================
# Session input loading
# ============================================================

def _load_session_input(session_dir: Path) -> str:
    """Load and format session transcript + scope context for judge consumption.

    Prepends session metadata (scope, completed_phases) to help judges correctly
    mark Phase 0.5 and skipped phases as CANNOT_ASSESS per rubric rules.

    Works with all systems (BrandMind/ChatGPT/Gemini) via the same format.
    """
    sections: list[str] = []

    # Prepend metadata context if available
    meta_path = session_dir / "metadata.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        session_meta = meta.get("session_metadata", {})
        scope = session_meta.get("scope", "unknown")
        completed = session_meta.get("completed_phases", [])
        system = meta.get("system", "unknown")

        sections.append("## SESSION CONTEXT")
        sections.append(f"- System: {system}")
        sections.append(f"- Scope: {scope}")
        sections.append(f"- Completed phases: {', '.join(completed) if completed else 'none'}")
        sections.append("")
        sections.append("**Rubric scope rules:**")
        sections.append("- Phase 0.5 (Q05-*) applies only to refresh/repositioning/full_rebrand scopes")
        sections.append("- For new_brand scope → mark Q05-* as CANNOT_ASSESS")
        sections.append("- Phase sequences by scope:")
        sections.append("  - new_brand: 0 → 1 → 2 → 3 → 4 → 5 (skip 0.5)")
        sections.append("  - refresh: 0 → 0.5 → 1 → 3 → 4 → 5 (skip Phase 2 → Q2-* = CANNOT_ASSESS)")
        sections.append("  - repositioning: 0 → 0.5 → 1 → 2 → 3 → 4 → 5")
        sections.append("  - full_rebrand: 0 → 0.5 → 1 → 2 → 3 → 4 → 5")
        sections.append("")

    # Transcript
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


# ============================================================
# Batch prompt building
# ============================================================

def _build_batch_prompt(
    batch_id: str,
    batch_label: str,
    section_content: str,
    is_ap: bool,
    header: str,
    footer: str,
) -> str:
    """Build judge system prompt for one dimension batch."""
    # JSON enforcement (especially needed for Claude)
    json_rule = (
        "\n\n## CRITICAL OUTPUT RULE\n"
        "Your ENTIRE response MUST be a single valid JSON object.\n"
        "- NO markdown fences (no ```json or ```)\n"
        "- NO narrative outside JSON\n"
        "- Start with { and end with }\n"
        f"- Evaluate ONLY the criteria in THIS batch ({batch_label}), not others\n"
    )

    if is_ap:
        format_example = (
            '{\n'
            '  "anti_patterns": [\n'
            '    {"id": "AP-1", "triggered": false, "instances": []},\n'
            '    {"id": "AP-2", "triggered": true, "instances": [\n'
            '      {"turn": 4, "evidence": "quoted text", "dimension_affected": ["quality"]}\n'
            '    ]}\n'
            '  ]\n'
            '}'
        )
    else:
        # Map batch to dimension key used in criteria "dimension" field
        dim_key = batch_id  # quality, mentor, personalization
        format_example = (
            '{\n'
            '  "criteria": [\n'
            '    {"id": "Q0-G1", "type": "GATE", '
            f'"dimension": "{dim_key}", '
            '"judgment": "MET", '
            '"evidence": "Turn X: quoted text from transcript", '
            '"explanation": "Why this judgment"}\n'
            '  ]\n'
            '}'
        )

    return (
        f"{header}\n\n"
        f"## EVALUATION BATCH: {batch_label}\n\n"
        f"You are evaluating ONLY the {batch_label} section of the rubric below. "
        f"Other dimensions/sections are evaluated separately.\n\n"
        f"{section_content}\n"
        f"{json_rule}\n"
        f"## REQUIRED JSON FORMAT\n"
        f"{format_example}\n\n"
        f"{footer}"
    )


# ============================================================
# Batch execution
# ============================================================

async def _run_batch(
    model: str,
    system_prompt: str,
    session_input: str,
    max_retries: int = 2,
) -> dict[str, Any]:
    """Run a single batch with streaming + JSON repair + retries.

    Returns dict with "criteria" and/or "anti_patterns" keys.
    On total failure, returns {}.
    """
    config = LiteLLMClientLLMConfig(
        model=model,
        temperature=1.0,  # deliberate — rubric 8.3.6 says 0, but Google/OpenAI/
        # Anthropic all recommend 1.0 for their thinking/reasoning models
        max_tokens=16000,  # batch output typically 1-6K tokens; headroom for Quality
        system_prompt=system_prompt,
        response_format={"type": "json_object"},
    )
    llm = LiteLLMClientLLM(config)

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        chunks: list[str] = []
        try:
            async for chunk in llm.astream_complete(session_input):
                chunks.append(chunk.delta or "")
            raw = "".join(chunks)
        except Exception as e:  # noqa: BLE001
            raw = "".join(chunks)
            last_error = e

        if not raw.strip():
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)
                continue
            return {}

        # Try parse → repair → extract-and-repair
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        try:
            repaired = repair_json(raw, return_objects=False)
            return json.loads(repaired)
        except Exception:  # noqa: BLE001
            pass

        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                repaired = repair_json(raw[start:end], return_objects=False)
                return json.loads(repaired)
            except Exception:  # noqa: BLE001
                pass

        last_error = ValueError(f"JSON parse failed on {len(raw)} chars")
        if attempt < max_retries:
            await asyncio.sleep(2 ** attempt)

    if last_error:
        print(f"    Batch failed after {max_retries + 1} attempts: {last_error}")
    return {}


async def _run_judge_batched(
    model: str,
    session_input: str,
    rubric_sections: dict[str, list[str]],
    checkpoint_file: Path | None = None,
) -> dict[str, Any]:
    """Run one judge across all 4 dimension batches. Resume from checkpoint."""
    header = "\n".join(rubric_sections["header"])
    footer = "\n".join(rubric_sections["footer"])
    tag = model.split("/")[-1][:24]  # short model name for log prefix

    combined: dict[str, Any] = {
        "criteria": [],
        "anti_patterns": [],
        "batches_done": [],
    }

    if checkpoint_file and checkpoint_file.exists():
        combined = json.loads(checkpoint_file.read_text(encoding="utf-8"))
        print(f"  [{tag}] Resumed from checkpoint: {len(combined['batches_done'])} batches done")

    for batch_id, batch_label, section_key, is_ap in BATCHES:
        if batch_id in combined["batches_done"]:
            print(f"  [{tag}] {batch_id} SKIP (already done)")
            continue

        section_content = "\n".join(rubric_sections.get(section_key, []))
        if not section_content.strip():
            print(f"  [{tag}] {batch_id} SKIP (empty section)")
            combined["batches_done"].append(batch_id)
            continue

        prompt = _build_batch_prompt(
            batch_id, batch_label, section_content, is_ap, header, footer
        )

        ts = time.strftime("%H:%M:%S")
        print(f"  [{tag}] {batch_id} START {ts} ({batch_label}, input={len(session_input) + len(prompt):,} chars)", flush=True)
        start_t = time.time()
        result = await _run_batch(model, prompt, session_input)
        elapsed = time.time() - start_t

        criteria = result.get("criteria", [])
        ap = result.get("anti_patterns", [])

        if not criteria and not ap:
            print(f"  [{tag}] {batch_id} FAIL ({elapsed:.0f}s)", flush=True)
        else:
            print(f"  [{tag}] {batch_id} OK ({elapsed:.0f}s) — {len(criteria)} crit, {len(ap)} AP", flush=True)

        combined["criteria"].extend(criteria)
        combined["anti_patterns"].extend(ap)
        combined["batches_done"].append(batch_id)

        if checkpoint_file:
            checkpoint_file.write_text(
                json.dumps(combined, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        # Pause between batches to avoid overloading proxy
        await asyncio.sleep(2)

    # Deduplicate criteria by ID (keep last — retry result)
    # Also filter out incomplete entries (judges sometimes return id-only stubs).
    required_fields = {"id", "type", "dimension", "judgment"}
    seen: dict[str, dict[str, Any]] = {}
    dropped_incomplete = 0
    for c in combined["criteria"]:
        cid = c.get("id", "")
        if not cid:
            continue
        if not required_fields.issubset(c.keys()):
            dropped_incomplete += 1
            continue
        seen[cid] = c
    combined["criteria"] = list(seen.values())
    if dropped_incomplete:
        print(f"    ⚠ Dropped {dropped_incomplete} incomplete criterion entries (missing required fields)")

    # Deduplicate anti-patterns by ID
    ap_seen: dict[str, dict[str, Any]] = {}
    for ap in combined["anti_patterns"]:
        aid = ap.get("id", "")
        if aid:
            ap_seen[aid] = ap
    combined["anti_patterns"] = list(ap_seen.values())

    return combined


# ============================================================
# Transcript validation
# ============================================================

def _validate_transcript(session_dir: Path) -> list[str]:
    """Check transcript completeness. Returns list of warnings (empty = OK)."""
    warnings: list[str] = []

    transcript_path = session_dir / "transcript.json"
    if not transcript_path.exists():
        warnings.append("No transcript.json found")
        return warnings

    data = json.loads(transcript_path.read_text(encoding="utf-8"))
    turns = data.get("turns", [])
    if not turns:
        warnings.append("Transcript has no turns")
        return warnings

    # Check for empty agent responses
    empty_count = sum(1 for t in turns if not t.get("agent", "").strip())
    if empty_count > 0:
        warnings.append(f"{empty_count} turn(s) with empty agent response")

    # Check turn numbering is sequential
    for i, t in enumerate(turns, start=1):
        if t.get("turn") != i:
            warnings.append(f"Turn numbering non-sequential at position {i}: got {t.get('turn')}")
            break

    return warnings


# ============================================================
# Main evaluation
# ============================================================

async def evaluate_session(
    session_dir: Path,
    models: list[str] | None = None,
) -> dict[str, Any]:
    """Run all judges on a session → produce evaluation_results.json.

    Pipeline:
    1. Validate transcript → warn on issues
    2. Parse rubric into 4 dimension sections
    3. For each judge: run 4 batches (checkpoint-resumable)
    4. Compute scores via scoring.calculate_all_scores
    5. Compute inter-rater agreement via scoring.compute_fleiss_kappa
    6. Save evaluation_results.json (backward-compatible with aggregate.py)
    """
    models = models or DEFAULT_JUDGE_MODELS

    # Step 1: Validate transcript
    warnings = _validate_transcript(session_dir)
    if warnings:
        print(f"⚠ Transcript warnings for {session_dir.name}:")
        for w in warnings:
            print(f"  - {w}")

    # Step 2: Parse rubric
    rubric = JUDGE_PROMPT_PATH.read_text(encoding="utf-8")
    rubric_sections = _parse_rubric_sections(rubric)

    # Step 3: Load session input (with scope context)
    session_input = _load_session_input(session_dir)

    print(f"\nEvaluating: {session_dir.name}")
    print(f"Judges: {', '.join(models)}")
    print(f"Batches per judge: {len(BATCHES)} (Quality, Mentor, Personal, AP)\n")

    # Step 4: Run judges in parallel (independent per judge; batches within
    # each judge stay sequential for checkpoint resume).
    judge_results: dict[str, Any] = {}
    start_total = time.time()

    async def _run_one_judge(model: str) -> tuple[str, dict[str, Any]]:
        safe = model.replace("/", "-").replace(".", "_")
        checkpoint_file = session_dir / f"judge_{safe}_checkpoint.json"
        model_key = model.split("/")[-1]
        judge_start = time.time()
        try:
            combined = await _run_judge_batched(
                model, session_input, rubric_sections, checkpoint_file,
            )
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ Judge {model_key} crashed: {e}")
            return model_key, {"error": str(e)}

        judge_elapsed = time.time() - judge_start
        scores = calculate_all_scores(combined)
        result = {
            "criteria": combined["criteria"],
            "anti_patterns": combined["anti_patterns"],
            "scores": scores,
            "elapsed_seconds": round(judge_elapsed, 1),
        }

        # Save per-judge file (human-readable inspection)
        judge_file = session_dir / f"judge_{safe}.json"
        judge_file.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Concise per-judge summary
        q = scores["quality"]
        m = scores["mentor"]
        p = scores["personalization"]
        print(
            f"  ✓ {model_key}: Overall={scores['overall']}, "
            f"Q={q['final_score']} (G={q['gates_met']}/{q['gates_total']}), "
            f"M={m['final_score']}, P={p['final_score']} — "
            f"{len(combined['criteria'])} crit, {len(combined['anti_patterns'])} AP, "
            f"{judge_elapsed:.0f}s"
        )
        return model_key, result

    # Launch all 3 judges concurrently
    pairs = await asyncio.gather(
        *[_run_one_judge(m) for m in models],
        return_exceptions=False,
    )
    for model_key, result in pairs:
        judge_results[model_key] = result

    total_elapsed = time.time() - start_total

    # Step 5: Inter-rater agreement
    successful = [v for v in judge_results.values() if "error" not in v]
    agreement = compute_fleiss_kappa(successful) if len(successful) >= 2 else {}

    # Step 6: Final output (backward-compatible format)
    evaluation = {
        "session_dir": str(session_dir),
        "timestamp": datetime.now().isoformat(),
        "judge_models": models,
        "judges": judge_results,
        "agreement": agreement,
        "total_elapsed_seconds": round(total_elapsed, 1),
        "transcript_warnings": warnings,
    }

    output_path = session_dir / "evaluation_results.json"
    output_path.write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Summary
    print(f"{'='*60}")
    print(f"TOTAL: {total_elapsed:.0f}s ({total_elapsed/60:.1f}min)")
    print(f"{'='*60}")
    print("\n=== SCORE SUMMARY ===")
    for name, r in judge_results.items():
        if "error" in r:
            print(f"  {name}: ERROR — {r['error']}")
        else:
            s = r["scores"]
            print(f"  {name}: Overall={s['overall']}, "
                  f"Q={s['quality']['final_score']}, "
                  f"M={s['mentor']['final_score']}, "
                  f"P={s['personalization']['final_score']}")
    if agreement:
        print(f"\n=== INTER-RATER AGREEMENT ===")
        print(f"  Fleiss' Kappa: {agreement.get('overall_kappa', '?')} "
              f"({agreement.get('interpretation', '?')})")
        print(f"  Criteria rated by all: {agreement.get('n_criteria', 0)}")
        print(f"  Low-agreement (<0.67): {len(agreement.get('low_agreement', []))}")
    print(f"\nSaved: {output_path}")

    return evaluation


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run multi-judge evaluation on BrandMind sessions",
    )
    parser.add_argument("--session-dir", required=True, type=Path)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Treat --session-dir as root; evaluate all subdirs with transcript.json",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="Override judge model IDs (default: 3 SOTA judges)",
    )
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
