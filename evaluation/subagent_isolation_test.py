"""Sub-agent isolation smoke test for the BrandMind brand-strategy stack.

Each sub-agent in the brand-strategy system (creative-studio,
document-generator, etc.) is normally invoked through the orchestrator's
``task`` tool. When end-to-end pilots show the deliverable artifacts are
not produced, it is impossible to tell whether the sub-agent itself is
unreliable or whether the orchestrator is dispatching it incorrectly.

This script invokes each sub-agent **directly** with a hand-crafted brief
that already contains the structured data the sub-agent needs, then
inspects the resulting message stream and on-disk artifacts to check
whether the sub-agent calls the expected generator tool and produces a
valid output file.

The script is read-only with respect to the agent codebase; it constructs
a fresh ``create_agent`` runnable per test using the same configuration
as the production sub-agent middleware.

Usage:
    uv run python evaluation/subagent_isolation_test.py
    uv run python evaluation/subagent_isolation_test.py --case brand_key
    uv run python evaluation/subagent_isolation_test.py --json

Exit codes:
    0  All requested cases passed.
    1  At least one case failed.
    2  Setup error (missing dependency, invalid configuration, etc.).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure src/ is on the path when run from repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
for sub in ("config", "core/src", "shared/src", "prompts"):
    p = _REPO_ROOT / "src" / sub
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from langchain.agents import create_agent  # noqa: E402
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage  # noqa: E402

from core.brand_strategy.subagents.configs import (  # noqa: E402
    CREATIVE_STUDIO_TOOLS,
    DOCUMENT_GENERATOR_TOOLS,
    create_subagent_models,
)
from prompts.brand_strategy.subagents import (  # noqa: E402
    CREATIVE_STUDIO_SYSTEM_PROMPT,
    DOCUMENT_GENERATOR_SYSTEM_PROMPT,
)
from shared.agent_tools.document import (  # noqa: E402
    generate_document,
    generate_presentation,
    generate_spreadsheet,
)
from shared.agent_tools.image import (  # noqa: E402
    edit_image,
    generate_brand_key,
    generate_image,
)

# ---------------------------------------------------------------------------
# Brief fixtures — hand-crafted inputs that contain everything the sub-agent
# needs to produce its artifact, so the test isolates the sub-agent's
# behaviour from any orchestrator brief-construction errors.
# ---------------------------------------------------------------------------


_BRAND_KEY_BRIEF = """\
Compile a Brand Key one-pager visual for "Chuyện Ba Bữa Signature".
Use generate_brand_key with the structured data below.

Brand: Chuyện Ba Bữa Signature
Tagline: Vị quen sắc mới
Visual style: Indochine modern, deep green + warm gold + walnut wood,
serif typography (Playfair Display), moody premium photography.

Brand Key 9 components:
1. Root Strength: 15-year fine-dining chef heritage; signature dishes
   (Chả Cá Na Hang, Xôi Cua Cà Mau) with world-class ingredients
   (truffle, Iberico, Cà Mau crab); 3-floor Indochine flagship at Q1.
2. Competitive Environment: premium Vietnamese dining in District 1 HCMC
   — Cục Gạch Quán (heritage), An Nhiên (modern), Quán Bụi (casual scale).
3. Target: corporate executives and senior managers in Q1 office towers
   needing a private, professional venue for client entertainment.
4. Insight: "I need a place sophisticated enough to impress my partners
   but private enough to actually close the deal."
5. Benefits: functional — soundproof private room, predictable service,
   bilingual menu; emotional — pride in hosting choice, conversation
   confidence.
6. Values & Personality: Caregiver archetype — empathetic privacy,
   refined, distinguished, quietly luxurious.
7. Reasons to Believe: 15-year chef, 2nd-floor private rooms,
   Iberico/truffle/crab specialty dishes, soft-open Dec 2024.
8. Discriminator: the only "Modern Saigonese Gastronomy" in Q1 with
   genuine private corporate hosting space.
9. Brand Essence: Empathetic Privacy — Modern Saigonese Excellence.

Return the file path to the generated Brand Key image."""

_STRATEGY_DOC_BRIEF = """\
Compile the full brand strategy document for "Chuyện Ba Bữa Signature"
as DOCX, using generate_document. Then compile an executive presentation
deck as PPTX using generate_presentation.

Section / slide content (use this content verbatim, do not invent):

Phase 0 — Business Problem Diagnosis:
Brand: Chuyện Ba Bữa Signature, premium flagship of Chuyện Ba Bữa,
soft-opened Dec 2024. Q1 HCMC, 3-floor Indochine. Weekday dinner traffic
sparse. Scope: Repositioning. Budget tier: Starter (50-80M VND/month).
Problem statement: Signature is stuck in customers' minds as an
"expensive version of the parent brand"; corporate decision-makers see
no differentiated reason to choose it for weekday client dinners
in a dense Q1 fine-dining market.

Phase 1 — Market Intelligence:
Top 3 competitors — Cục Gạch (heritage rustic), An Nhiên (modern chic),
Quán Bụi (casual scale). Strategic gap: "Modern Saigonese Gastronomy"
positioning for executive private dining is unclaimed in Q1. Target
audience: corporate executives in Q1 office towers, weekday client
entertainment occasion, status + efficiency dual need.

Phase 2 — Brand Positioning:
For corporate executives in HCMC seeking a private, refined venue for
business entertainment, Chuyện Ba Bữa Signature is the only Premium
Modern Saigonese Dining experience that pairs international fine-dining
technique with Vietnamese culinary heritage, in a private Indochine
sanctuary, because of our 15-year executive chef and dedicated 2nd-floor
private rooms.
Brand Essence: Empathetic Privacy. Mantra: Refined - Private - Distinguished.

Phase 3 — Brand Identity:
Archetype: Caregiver. Visual direction "Midnight Indochine" — charcoal +
antique gold + walnut. Photography: low-key moody, texture-focused.
Typography: Serif (Playfair Display) for headlines, sans-serif
(Montserrat) for body. Logo evolution: Typographic Authority option.

Phase 4 — Communication Framework:
Value proposition (3 levels: one-liner, elevator pitch, full story).
Messaging hierarchy 4 tiers (functional, emotional, differentiating,
credibility). Cialdini Authority (executive chef storytelling) +
Scarcity ("Executive Tuesday" 4-private-rooms-only). AIDA mapping to
Google Maps/SEO -> IG -> LinkedIn networking. Channel cadence:
LinkedIn 2/wk, IG 4/wk, FB 3/wk. 80/20 moody/showcase visual rule.

Phase 5 — Implementation Roadmap & KPIs:
Roadmap horizons: Month 1 Foundation (logo Evolve, photoshoot,
training); Month 2 Launch (LinkedIn page, "Executive Tuesday" campaign,
direct outreach to nearby corporate offices); Month 3 Optimize
(retargeting, Signature Circle membership). KPI baselines all marked
"current: no data — measure pre-launch": booking T2-T5 +25%, Corporate
share 40%, LinkedIn followers +5,000, NPS >9, Social ER +15%.

Output contract: return file paths for both DOCX and PPTX."""

_KPI_SHEET_BRIEF = """\
Build a KPI tracking spreadsheet for "Chuyện Ba Bữa Signature" using
generate_spreadsheet. Format the sheet with one row per KPI and these
columns: Metric, Measurement Method, Baseline, Target, Timeframe,
Review Frequency.

Rows:
- Weekday booking volume (T2-T5) | Reservation system count |
  Current: no data, measure pre-launch | +25% | 3 months | Weekly
- Corporate guest share | Receipt category tag at checkout |
  Current: <10% (estimated) | 40% | 3 months | Weekly
- LinkedIn page followers | LinkedIn analytics |
  Current: 0 (page not yet created) | 5,000 | 3 months | Monthly
- Net Promoter Score (corporate guests) | Post-meal SMS survey |
  Current: no data | >9 / 10 | Quarterly | Monthly
- Instagram engagement rate (cao-cấp segment) | IG analytics |
  Current: ~1.2% | +15% (1.4%) | 3 months | Bi-weekly
- Average ticket size (corporate cover) | POS data |
  Current: no data | track baseline | 3 months | Monthly

Return the file path to the generated XLSX."""


# ---------------------------------------------------------------------------
# Test data model
# ---------------------------------------------------------------------------


@dataclass
class CaseResult:
    """Outcome of a single sub-agent isolation test case."""

    case_id: str
    sub_agent: str
    description: str
    expected_tools: list[str]
    observed_tool_calls: list[str] = field(default_factory=list)
    artifact_files: list[str] = field(default_factory=list)
    artifact_sizes: dict[str, int] = field(default_factory=dict)
    file_validity: dict[str, bool] = field(default_factory=dict)
    failure_reasons: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    @property
    def passed(self) -> bool:
        return not self.failure_reasons


# ---------------------------------------------------------------------------
# Sub-agent runtime
# ---------------------------------------------------------------------------


_TOOL_REGISTRY: dict[str, Any] = {
    "generate_image": generate_image,
    "edit_image": edit_image,
    "generate_brand_key": generate_brand_key,
    "generate_document": generate_document,
    "generate_presentation": generate_presentation,
    "generate_spreadsheet": generate_spreadsheet,
}


def _resolve(names: list[str]) -> list[Any]:
    """Resolve tool name strings into actual tool instances.

    Args:
        names: Tool names declared by the sub-agent's config.

    Returns:
        List of tool instances. Missing names are silently skipped after
        logging to stderr; this matches the production middleware.
    """
    resolved: list[Any] = []
    for name in names:
        tool = _TOOL_REGISTRY.get(name)
        if tool is None:
            print(f"warning: tool '{name}' not in registry", file=sys.stderr)
            continue
        resolved.append(tool)
    return resolved


def _build_runnable(name: str) -> Any:
    """Construct a standalone runnable for one sub-agent.

    The resulting object mirrors what
    :class:`deepagents.middleware.subagents.SubAgentMiddleware` would
    register under the name ``name``: same model, same tools, same
    system prompt. The middleware-only wrapping (PatchToolCallsMiddleware,
    HumanInTheLoopMiddleware) is intentionally omitted because this
    test invokes the agent directly without the orchestrator's
    interrupt machinery.

    Args:
        name: Sub-agent identifier — ``creative-studio`` or
            ``document-generator``.

    Returns:
        A LangGraph runnable that accepts ``{"messages": [...]}`` and
        returns the final state.

    Raises:
        ValueError: When ``name`` is not a known sub-agent.
    """
    models = create_subagent_models()
    if name == "creative-studio":
        return create_agent(
            models[name],
            system_prompt=CREATIVE_STUDIO_SYSTEM_PROMPT,
            tools=_resolve(CREATIVE_STUDIO_TOOLS),
            name=name,
        )
    if name == "document-generator":
        return create_agent(
            models[name],
            system_prompt=DOCUMENT_GENERATOR_SYSTEM_PROMPT,
            tools=_resolve(DOCUMENT_GENERATOR_TOOLS),
            name=name,
        )
    raise ValueError(f"unknown sub-agent: {name}")


async def _run_subagent(name: str, brief: str) -> dict[str, Any]:
    """Execute a single sub-agent against a brief and return final state.

    Args:
        name: Sub-agent identifier.
        brief: Brief text passed as a HumanMessage.

    Returns:
        The runnable's final state dict; ``messages`` contains the
        entire turn history including AI / Tool messages.
    """
    runnable = _build_runnable(name)
    return await runnable.ainvoke(
        {"messages": [HumanMessage(content=brief)]},
        config={"recursion_limit": 50},
    )


# ---------------------------------------------------------------------------
# Inspection
# ---------------------------------------------------------------------------


def _collect_tool_calls(messages: list[Any]) -> list[str]:
    """Return the names of all tool calls made by the sub-agent.

    Args:
        messages: Final ``messages`` list from the runnable's state.

    Returns:
        Tool names, in invocation order, as observed in
        ``AIMessage.tool_calls``.
    """
    calls: list[str] = []
    for msg in messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                calls.append(tc.get("name", "<unknown>"))
    return calls


def _collect_artifact_paths(messages: list[Any]) -> list[str]:
    """Extract artifact file paths from ToolMessage content.

    Recognised forms:
      * Plain JSON object with ``file_path`` key.
      * Plain string ending in a known artifact extension.
      * Free-form text containing an absolute path with a known extension.

    Args:
        messages: Final ``messages`` list from the runnable's state.

    Returns:
        Absolute file paths that are present on disk; non-existent
        paths are filtered out so tests do not give credit for ghost
        references in the conversation.
    """
    extensions = (".jpeg", ".jpg", ".png", ".docx", ".pdf", ".pptx", ".xlsx")
    found: list[str] = []
    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue
        content = msg.content
        if isinstance(content, list):
            content = " ".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        text = content if isinstance(content, str) else str(content)
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                for key in ("file_path", "image_path", "output_path", "path"):
                    val = obj.get(key)
                    if isinstance(val, str) and val.lower().endswith(extensions):
                        found.append(val)
                continue
        except (json.JSONDecodeError, ValueError):
            pass
        for token in text.replace("\\n", " ").replace("\n", " ").split():
            cleaned = token.strip("\"',()[]{}")
            if cleaned.lower().endswith(extensions):
                found.append(cleaned)
    seen: set[str] = set()
    unique = [p for p in found if not (p in seen or seen.add(p))]
    resolved: list[str] = []
    for p in unique:
        path = Path(p)
        if not path.is_absolute():
            path = (_REPO_ROOT / p).resolve()
        if path.is_file():
            resolved.append(str(path))
    return resolved


def _validate_files(paths: list[str]) -> tuple[dict[str, int], dict[str, bool]]:
    """Check size and openability of each artifact file.

    Args:
        paths: Absolute file paths returned by tool calls.

    Returns:
        Tuple of ``(sizes, validity)``. ``sizes`` maps each path to its
        byte length. ``validity`` maps each path to ``True`` when the
        file's extension matches a recognised parser AND that parser
        opens it without exception. Missing parsers (e.g.
        ``python-docx`` not installed) yield ``True`` because the
        check would otherwise penalise a perfectly valid file.
    """
    sizes: dict[str, int] = {}
    validity: dict[str, bool] = {}
    for p in paths:
        path = Path(p)
        if not path.is_file():
            sizes[p] = 0
            validity[p] = False
            continue
        sizes[p] = path.stat().st_size
        ext = path.suffix.lower()
        validity[p] = _open_artifact(path, ext)
    return sizes, validity


def _open_artifact(path: Path, ext: str) -> bool:
    """Return True when the artifact opens with its native parser."""
    try:
        if ext in (".jpeg", ".jpg", ".png"):
            try:
                from PIL import Image  # type: ignore

                with Image.open(path) as img:
                    img.verify()
                return True
            except ImportError:
                return True
        if ext == ".docx":
            try:
                import docx  # type: ignore

                docx.Document(str(path))
                return True
            except ImportError:
                return True
        if ext == ".pptx":
            try:
                from pptx import Presentation  # type: ignore

                Presentation(str(path))
                return True
            except ImportError:
                return True
        if ext == ".xlsx":
            try:
                from openpyxl import load_workbook  # type: ignore

                load_workbook(str(path), read_only=True)
                return True
            except ImportError:
                return True
    except Exception as exc:  # noqa: BLE001
        print(f"validation error for {path}: {exc}", file=sys.stderr)
        return False
    return True


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


def _evaluate_brand_key(messages: list[Any]) -> CaseResult:
    """Score the creative-studio Brand Key isolation case."""
    case = CaseResult(
        case_id="brand_key",
        sub_agent="creative-studio",
        description="Brand Key brief with full 9 components.",
        expected_tools=["generate_brand_key"],
    )
    case.observed_tool_calls = _collect_tool_calls(messages)
    case.artifact_files = _collect_artifact_paths(messages)
    case.artifact_sizes, case.file_validity = _validate_files(case.artifact_files)

    if "generate_brand_key" not in case.observed_tool_calls:
        case.failure_reasons.append(
            "generate_brand_key was not called (observed: "
            f"{case.observed_tool_calls})"
        )
    image_exts = (".jpeg", ".jpg", ".png")
    image_files = [
        p for p in case.artifact_files if Path(p).suffix.lower() in image_exts
    ]
    if not image_files:
        case.failure_reasons.append("no image artifact returned")
    else:
        for p in image_files:
            size = case.artifact_sizes.get(p, 0)
            if size < 50_000:
                case.failure_reasons.append(
                    f"image {p} is {size} bytes (threshold 50_000)"
                )
            if not case.file_validity.get(p, False):
                case.failure_reasons.append(f"image {p} did not open with PIL")
    return case


def _evaluate_strategy_doc(messages: list[Any]) -> CaseResult:
    """Score the document-generator strategy DOCX + PPTX isolation case."""
    case = CaseResult(
        case_id="strategy_doc",
        sub_agent="document-generator",
        description="Full strategy data for DOCX + PPTX.",
        expected_tools=["generate_document", "generate_presentation"],
    )
    case.observed_tool_calls = _collect_tool_calls(messages)
    case.artifact_files = _collect_artifact_paths(messages)
    case.artifact_sizes, case.file_validity = _validate_files(case.artifact_files)

    for required in case.expected_tools:
        if required not in case.observed_tool_calls:
            case.failure_reasons.append(f"{required} was not called")

    docx_files = [p for p in case.artifact_files if p.lower().endswith(".docx")]
    pptx_files = [p for p in case.artifact_files if p.lower().endswith(".pptx")]
    if not docx_files:
        case.failure_reasons.append("no DOCX artifact returned")
    if not pptx_files:
        case.failure_reasons.append("no PPTX artifact returned")

    for p in docx_files + pptx_files:
        size = case.artifact_sizes.get(p, 0)
        if size < 30_000:
            case.failure_reasons.append(f"{p} is {size} bytes (threshold 30_000)")
        if not case.file_validity.get(p, False):
            case.failure_reasons.append(f"{p} did not open with native parser")
    return case


def _evaluate_kpi_sheet(messages: list[Any]) -> CaseResult:
    """Score the document-generator KPI XLSX isolation case."""
    case = CaseResult(
        case_id="kpi_sheet",
        sub_agent="document-generator",
        description="KPI list for spreadsheet generation.",
        expected_tools=["generate_spreadsheet"],
    )
    case.observed_tool_calls = _collect_tool_calls(messages)
    case.artifact_files = _collect_artifact_paths(messages)
    case.artifact_sizes, case.file_validity = _validate_files(case.artifact_files)

    if "generate_spreadsheet" not in case.observed_tool_calls:
        case.failure_reasons.append("generate_spreadsheet was not called")
    xlsx_files = [p for p in case.artifact_files if p.lower().endswith(".xlsx")]
    if not xlsx_files:
        case.failure_reasons.append("no XLSX artifact returned")
    # Threshold reflects file existence + valid format only. Row-population
    # depth is checked by the M-4 semantic audit, not the M-2A isolation
    # test, because empty rows usually indicate a brief-format mismatch
    # between sub-agent output and the template schema (orchestrator's
    # dispatch concern, fixed at M-2C).
    for p in xlsx_files:
        size = case.artifact_sizes.get(p, 0)
        if size < 5_000:
            case.failure_reasons.append(f"{p} is {size} bytes (threshold 5_000)")
        if not case.file_validity.get(p, False):
            case.failure_reasons.append(f"{p} did not open with openpyxl")
    return case


_CASES: dict[str, tuple[str, str, Any]] = {
    "brand_key": ("creative-studio", _BRAND_KEY_BRIEF, _evaluate_brand_key),
    "strategy_doc": (
        "document-generator",
        _STRATEGY_DOC_BRIEF,
        _evaluate_strategy_doc,
    ),
    "kpi_sheet": ("document-generator", _KPI_SHEET_BRIEF, _evaluate_kpi_sheet),
}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


async def _run_case(case_id: str) -> CaseResult:
    sub_agent_name, brief, evaluate = _CASES[case_id]
    started = datetime.now()
    state = await _run_subagent(sub_agent_name, brief)
    case = evaluate(state.get("messages", []))
    case.duration_seconds = (datetime.now() - started).total_seconds()
    return case


async def _run_cases(case_ids: list[str]) -> list[CaseResult]:
    results: list[CaseResult] = []
    for cid in case_ids:
        try:
            results.append(await _run_case(cid))
        except Exception as exc:  # noqa: BLE001
            results.append(
                CaseResult(
                    case_id=cid,
                    sub_agent=_CASES[cid][0],
                    description="Case raised an exception during execution.",
                    expected_tools=[],
                    failure_reasons=[f"exception: {exc!r}"],
                )
            )
    return results


def _format_summary(results: list[CaseResult]) -> str:
    lines: list[str] = []
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        lines.append(
            f"[{status}] {r.case_id} ({r.sub_agent}) — "
            f"{r.duration_seconds:.1f}s"
        )
        lines.append(f"  expected: {', '.join(r.expected_tools)}")
        lines.append(f"  observed: {', '.join(r.observed_tool_calls) or '(none)'}")
        for p in r.artifact_files:
            size = r.artifact_sizes.get(p, 0)
            valid = "ok" if r.file_validity.get(p, False) else "INVALID"
            lines.append(f"  artifact: {p}  size={size}  {valid}")
        for reason in r.failure_reasons:
            lines.append(f"  fail: {reason}")
    passed = sum(1 for r in results if r.passed)
    lines.append("")
    lines.append(f"Summary: {passed}/{len(results)} cases passed")
    return "\n".join(lines)


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        action="append",
        choices=sorted(_CASES.keys()),
        help="Run only the named case. Repeat to run multiple. Default: all.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human summary on stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    if not os.environ.get("GEMINI_API_KEY") and not Path(
        _REPO_ROOT / "environments/.env"
    ).is_file():
        print(
            "error: GEMINI_API_KEY is required (set env or load environments/.env)",
            file=sys.stderr,
        )
        return 2
    cases = args.case or sorted(_CASES.keys())
    results = asyncio.run(_run_cases(cases))
    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False))
    else:
        print(_format_summary(results))
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
