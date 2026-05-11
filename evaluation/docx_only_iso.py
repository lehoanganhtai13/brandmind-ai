"""DOCX-only isolation test for document-generator dispatch reliability.

Goal: distinguish whether the failure was at
  Layer 2 — sub-agent reasoning: didn't call generate_document, or called it
             with malformed / non-JSON content argument.
  Layer 3 — tool execution: generate_document was called with valid JSON but
             the docx_builder raised an exception.

Usage:
    uv run python evaluation/docx_only_iso.py
    uv run python evaluation/docx_only_iso.py --fixture docx_iso_clean_fixture
    uv run python evaluation/docx_only_iso.py --json
    uv run python evaluation/docx_only_iso.py --log-level DEBUG

Do NOT modify comparison files or HippoRAG env/index. This script is
diagnosis-only; it writes no source code changes.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Path bootstrap — mirrors evaluation/subagent_isolation_test.py
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _sub in ("config", "core/src", "shared/src", "prompts"):
    _p = _REPO_ROOT / "src" / _sub
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# ---------------------------------------------------------------------------
# Imports — deferred until after path setup
# ---------------------------------------------------------------------------

from langchain.agents import create_agent  # noqa: E402
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage  # noqa: E402
from loguru import logger  # noqa: E402

from core.brand_strategy.subagents.configs import (  # noqa: E402
    DOCUMENT_GENERATOR_TOOLS,
    create_subagent_models,
)
from prompts.brand_strategy.subagents import (  # noqa: E402
    DOCUMENT_GENERATOR_SYSTEM_PROMPT,
)
from shared.agent_middlewares import WorkspaceInjectionMiddleware  # noqa: E402
from shared.agent_tools.document import (  # noqa: E402
    generate_document,
    generate_presentation,
    generate_spreadsheet,
)

# ---------------------------------------------------------------------------
# Fixture path — overridable via --fixture CLI argument
# ---------------------------------------------------------------------------

_DEFAULT_FIXTURE_SESSION_ID = "docx_iso_fixture"

# DOCX dispatch description — mirrors what the orchestrator generates at Phase 5
# for the "Đà Lạt Sương Sớm" session (new_brand, growth tier 80M/month).
_DOCX_DISPATCH = """\
Build the DOCX strategy document only. Do NOT call generate_presentation or generate_spreadsheet.

=== DOCX CONTENT (paragraph text per section) ===
cover: Đà Lạt Sương Sớm — Specialty Cafe & Brunch, Japandi Soul, Đà Lạt Highlands
executive_summary: New specialty cafe + brunch brand in Đà Lạt. Japandi-inspired space. \
Target: young professionals + remote workers + Hà Nội/HCM travelers. \
POD: serene "morning mist" rituals in an authentic highland setting. \
Budget Growth tier 80M/month. Launch August 2026.
phase_0_problem: Junior marketer briefed to build brand strategy for a new specialty cafe \
in Đà Lạt. New brand (no prior brand equity). Growth tier budget 80M/month. \
Sếp meeting in one week.
phase_1_output: SWOT — Strengths: unique Japandi concept, highland location advantage, \
Đà Lạt growing café scene. Weaknesses: new brand, no social proof. \
Opportunities: underserved aesthetic travelers, remote-work segment. \
Threats: competition from existing specialty cafes. Top 3 insights: \
(1) Aesthetic travelers seek "instagrammable morning rituals" not just coffee; \
(2) Remote workers want reliable peaceful workspace; \
(3) Weekend visitors plan via TikTok/Google Maps.
phase_2_output: Positioning: "For young professionals and aesthetic travelers \
who want a mindful highland morning, Đà Lạt Sương Sớm is the specialty cafe \
that transforms your coffee ritual into a sensory journey — because the best \
ideas emerge in stillness." POD: the "morning mist ritual" experience — \
a curated slow-morning sequence unavailable elsewhere in the Đà Lạt café market.
phase_3_output: Archetype: Sage × Creator. Brand personality: serene, intentional, quietly \
confident. Visual: muted earth tones (linen, sage, terracotta), Japanese typography, natural \
textures. Brand voice: soft, poetic, avoids hype language.
phase_4_output: Messaging pillars — Specialty (Functional): "Precision-brewed highland \
single origin"; Brunch (Emotional): "Slow mornings, clear afternoons"; \
Space (Differentiating): "Stillness as a feature, not an afterthought." \
Cialdini: Authority (craft credentials) + Scarcity ("Sunday Mist Table" pre-booking only) \
+ Social Proof (community building). 7 Cialdini principles mapped. \
Channels: IG 40%, FB 40%, TikTok 20%.
phase_5_output: {"roadmap": \
[{"Horizon": "Tháng 5-7/2026 (Pre-launch)", \
"Items": "Build digital presence, teasing content, staff training, space finalize", \
"Priority": "Must-do"}, \
{"Horizon": "Tháng 8-10/2026 (Grand Opening)", \
"Items": "Full launch campaign Sương Sớm First Look, KOC bookings, Meta ads", \
"Priority": "Must-do"}, \
{"Horizon": "Tháng 11/2026+ (Growth & Loyalty)", \
"Items": "Membership program, seasonal brunch menus, community workshops", \
"Priority": "Nice-to-have"}], \
"measurement": \
[{"KPI": "Brand Reach (Monthly Unique)", \
"Method": "Meta Business Suite Insights", \
"Current": "0 (new brand)", \
"Target": "150,000 users/month by Tháng 6/2026", "Cadence": "Monthly"}, \
{"KPI": "Social Engagement Rate", \
"Method": "Total Engagement / Reach (IG/FB)", "Current": "0", \
"Target": "4-6% stable by Tháng 4/2026", "Cadence": "Weekly"}, \
{"KPI": "Google Maps Intent Clicks", \
"Method": "Google Business Profile Directions", "Current": "0", \
"Target": "800 clicks/month by Tháng 3/2026", "Cadence": "Monthly"}, \
{"KPI": "Customer Satisfaction Score", \
"Method": "Google Maps & FB Review average", \
"Current": "no data — measure pre-launch", \
"Target": "4.8/5.0 (min 50 reviews) by Tháng 2/2026", "Cadence": "Monthly"}, \
{"KPI": "Revenue", "Method": "POS monthly report", \
"Current": "0 (new brand)", \
"Target": "600M VNĐ/month breakeven by Tháng 6/2026", "Cadence": "Monthly"}, \
{"KPI": "Media Efficiency (CPC)", \
"Method": "Meta Ads Manager", "Current": "no data", \
"Target": "< 3,000 VNĐ/click by end of Tháng 8/2026", "Cadence": "Weekly"}]}
"""


# ---------------------------------------------------------------------------
# Mock session for WorkspaceInjectionMiddleware
# ---------------------------------------------------------------------------

def _make_mock_session(session_id: str) -> Any:
    """Return a minimal mock BrandStrategySession that WorkspaceInjectionMiddleware can use."""
    mock = MagicMock()
    mock.session_id = session_id
    return mock


# ---------------------------------------------------------------------------
# Agent builder — WITH WorkspaceInjectionMiddleware (production-faithful)
# ---------------------------------------------------------------------------

_TOOL_REGISTRY: dict[str, Any] = {
    "generate_document": generate_document,
    "generate_presentation": generate_presentation,
    "generate_spreadsheet": generate_spreadsheet,
}


def _resolve(names: list[str]) -> list[Any]:
    resolved = []
    for name in names:
        tool = _TOOL_REGISTRY.get(name)
        if tool is not None:
            resolved.append(tool)
        else:
            print(f"warning: tool '{name}' not in registry", file=sys.stderr)
    return resolved


def _build_docgen_with_middleware() -> Any:
    """Build a document-generator agent that includes WorkspaceInjectionMiddleware."""
    models = create_subagent_models()
    # WorkspaceInjectionMiddleware wraps the model call, not the agent.
    # In production SubAgentMiddleware passes middleware to create_agent.
    # Here we replicate that by passing middlewares= directly.
    return create_agent(
        models["document-generator"],
        system_prompt=DOCUMENT_GENERATOR_SYSTEM_PROMPT,
        tools=_resolve(DOCUMENT_GENERATOR_TOOLS),
        name="document-generator",
        middleware=[WorkspaceInjectionMiddleware()],
    )


# ---------------------------------------------------------------------------
# Inspection helpers
# ---------------------------------------------------------------------------

@dataclass
class IsoResult:
    fixture_session_id: str
    fixture_workspace: str
    dispatch_len: int
    tool_calls_observed: list[str] = field(default_factory=list)
    generate_document_called: bool = False
    content_arg_preview: str = ""
    content_arg_valid_json: bool | None = None
    content_arg_parse_error: str = ""
    tool_result_preview: str = ""
    artifact_path: str = ""
    artifact_exists: bool = False
    artifact_size_bytes: int = 0
    manifest_entry_found: bool = False
    layer_2_failure: bool = False
    layer_3_failure: bool = False
    failure_detail: str = ""
    duration_seconds: float = 0.0


def _inspect_messages(messages: list[Any]) -> dict[str, Any]:
    """Extract tool call names, generate_document args, and tool results."""
    tool_calls: list[str] = []
    gen_doc_input: Any = ""
    gen_doc_result: str = ""
    generate_document_calls: dict[str, Any] = {}

    for msg in messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                name = tc.get("name", "<unknown>")
                tool_calls.append(name)
                if name == "generate_document":
                    args = tc.get("args", {})
                    tool_call_id = tc.get("id", "")
                    content_arg = args.get("content", "")
                    if tool_call_id:
                        generate_document_calls[tool_call_id] = content_arg
                    gen_doc_input = content_arg
        if isinstance(msg, ToolMessage):
            content = msg.content
            if isinstance(content, list):
                content = " ".join(
                    p.get("text", "") if isinstance(p, dict) else str(p)
                    for p in content
                )
            result_text = content if isinstance(content, str) else str(content)
            tool_call_id = getattr(msg, "tool_call_id", "")
            if tool_call_id in generate_document_calls:
                gen_doc_input = generate_document_calls[tool_call_id]
                gen_doc_result = result_text

    return {
        "tool_calls": tool_calls,
        "gen_doc_input": gen_doc_input,
        "gen_doc_result": gen_doc_result,
    }


def _content_preview(content: Any, limit: int = 500) -> str:
    """Render a stable preview for structured or legacy string content."""
    if isinstance(content, str):
        return content[:limit]
    try:
        rendered = json.dumps(content, ensure_ascii=False)
    except TypeError:
        rendered = repr(content)
    return rendered[:limit]


def _content_is_valid(content: Any) -> tuple[bool, str]:
    """Return whether generate_document content is a valid section object."""
    if isinstance(content, dict):
        return True, ""
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        return False, repr(exc)
    if not isinstance(parsed, dict):
        return False, f"expected object, got {type(parsed).__name__}"
    return True, ""


def _check_manifest(session_id: str) -> bool:
    """Check if the manifest has a 'documents' entry for this session."""
    manifest = _REPO_ROOT / "brandmind-output" / ".manifest.jsonl"
    if not manifest.is_file():
        return False
    with open(manifest, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("session_id") == session_id and entry.get("category") == "documents":
                    return True
            except json.JSONDecodeError:
                continue
    return False


# ---------------------------------------------------------------------------
# Main ISO runner
# ---------------------------------------------------------------------------

async def _run_iso(log_level: str, fixture_session_id: str) -> IsoResult:
    import time

    fixture_workspace = Path.home() / ".brandmind" / "projects" / fixture_session_id / "workspace"

    # Verify fixture workspace exists
    if not fixture_workspace.is_dir():
        print(f"ERROR: fixture workspace not found: {fixture_workspace}", file=sys.stderr)
        sys.exit(2)

    result = IsoResult(
        fixture_session_id=fixture_session_id,
        fixture_workspace=str(fixture_workspace),
        dispatch_len=len(_DOCX_DISPATCH),
    )

    mock_session = _make_mock_session(fixture_session_id)

    with patch(
        "core.brand_strategy.session.get_active_session",
        return_value=mock_session,
    ):
        runnable = _build_docgen_with_middleware()
        t0 = time.perf_counter()
        try:
            state = await runnable.ainvoke(
                {"messages": [HumanMessage(content=_DOCX_DISPATCH)]},
                config={"recursion_limit": 50},
            )
        except Exception as exc:
            result.failure_detail = f"Agent invocation raised: {exc!r}"
            result.layer_2_failure = True
            result.duration_seconds = time.perf_counter() - t0
            return result
        result.duration_seconds = time.perf_counter() - t0

    messages = state.get("messages", [])
    inspection = _inspect_messages(messages)

    result.tool_calls_observed = inspection["tool_calls"]
    gen_doc_input = inspection["gen_doc_input"]
    gen_doc_result = inspection["gen_doc_result"]

    result.generate_document_called = "generate_document" in result.tool_calls_observed

    # Capture final AI response text (to see what sub-agent said if no tool call)
    final_ai_text = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            final_ai_text = (
                msg.content if isinstance(msg.content, str) else str(msg.content)
            )
            break
    result.tool_result_preview = final_ai_text[:800]

    if not result.generate_document_called:
        result.layer_2_failure = True
        result.failure_detail = (
            f"Sub-agent did NOT call generate_document. "
            f"Tool calls observed: {result.tool_calls_observed or ['(none)']}. "
            f"Final agent text (first 800): {final_ai_text[:800]!r}"
        )
        return result

    # generate_document was called — inspect the content argument
    result.content_arg_preview = _content_preview(gen_doc_input)
    content_valid, content_error = _content_is_valid(gen_doc_input)
    result.content_arg_valid_json = content_valid
    if content_error:
        result.content_arg_parse_error = content_error
        result.layer_2_failure = True
        result.failure_detail = (
            f"generate_document called with invalid content: {content_error}"
        )
        return result

    # Valid JSON — inspect tool result
    result.tool_result_preview = gen_doc_result[:600]

    result_lower = gen_doc_result.lower()
    if "failed" in result_lower or "invalid" in result_lower or "error" in result_lower:
        result.layer_3_failure = True
        result.failure_detail = f"generate_document returned error: {gen_doc_result[:300]}"
        return result

    # Check for path in result
    extensions = (".docx", ".pdf")
    for token in gen_doc_result.replace("\n", " ").split():
        if any(token.lower().endswith(ext) for ext in extensions):
            result.artifact_path = token.rstrip(".,;")
            break

    if result.artifact_path:
        p = Path(result.artifact_path)
        result.artifact_exists = p.is_file()
        result.artifact_size_bytes = p.stat().st_size if result.artifact_exists else 0

    result.manifest_entry_found = _check_manifest(fixture_session_id)

    if not result.artifact_exists:
        result.layer_3_failure = True
        missing = (
            "not found in result"
            if not result.artifact_path
            else f"does not exist: {result.artifact_path}"
        )
        result.failure_detail = (
            f"generate_document returned success text but artifact path {missing}"
        )

    return result


def _print_result(r: IsoResult, as_json: bool) -> None:
    if as_json:
        print(json.dumps(asdict(r), indent=2))
        return

    verdict = (
        "LAYER_2_FAILURE" if r.layer_2_failure
        else "LAYER_3_FAILURE" if r.layer_3_failure
        else "PASS" if r.artifact_exists
        else "UNCLEAR"
    )
    print(f"\n{'='*60}")
    print(f"DOCX-ONLY ISO RESULT: {verdict}")
    print(f"{'='*60}")
    print(f"fixture_session_id : {r.fixture_session_id}")
    print(f"fixture_workspace  : {r.fixture_workspace}")
    print(f"dispatch_len       : {r.dispatch_len} chars")
    print(f"duration           : {r.duration_seconds:.1f}s")
    print()
    print(f"generate_document called : {r.generate_document_called}")
    print(f"all tool_calls observed  : {r.tool_calls_observed}")
    if r.content_arg_preview:
        print(f"content arg (first 500) : {r.content_arg_preview}")
    print(f"content_valid_json       : {r.content_arg_valid_json}")
    if r.content_arg_parse_error:
        print(f"content_parse_error     : {r.content_arg_parse_error}")
    if r.tool_result_preview:
        print(f"tool_result (first 600) : {r.tool_result_preview}")
    print(f"artifact_path            : {r.artifact_path or '(none)'}")
    print(f"artifact_exists          : {r.artifact_exists}")
    print(f"artifact_size_bytes      : {r.artifact_size_bytes}")
    print(f"manifest_entry_found     : {r.manifest_entry_found}")
    print()
    if r.failure_detail:
        print(f"FAILURE DETAIL: {r.failure_detail}")
    print(f"{'='*60}")


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print result as JSON")
    parser.add_argument(
        "--fixture",
        default=_DEFAULT_FIXTURE_SESSION_ID,
        help=(
            "Session ID of the fixture workspace under ~/.brandmind/projects/. "
            f"Defaults to '{_DEFAULT_FIXTURE_SESSION_ID}' (duplicate Phase 5). "
            "Use 'docx_iso_clean_fixture' to test against the clean smoke workspace."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Loguru log level",
    )
    args = parser.parse_args()

    # Configure loguru
    logger.remove()
    logger.add(sys.stderr, level=args.log_level, format="[{level}] {message}")

    result = asyncio.run(_run_iso(args.log_level, args.fixture))
    _print_result(result, args.json)

    sys.exit(0 if result.artifact_exists else 1)


if __name__ == "__main__":
    _main()
