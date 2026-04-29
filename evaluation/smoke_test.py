"""Tier 1 regression smoke test for the brand-strategy pipeline.

Runs a fixed five-turn canary session against a locally running
BrandMind server, audits the produced artifacts via
``evaluation/artifact_audit.py``, and exits non-zero when the Tier 1
health score drops below the regression bar. The script does not
spawn the server itself — start it externally with ``brandmind serve``
before invoking this. Treat the smoke test as the gate that any
prompt or middleware change must clear before being committed during
Tier 2 optimization work.

Usage:
    uv run python evaluation/smoke_test.py
    uv run python evaluation/smoke_test.py --session-out <dir>
    uv run python evaluation/smoke_test.py --health-floor 4
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
from httpx_sse import connect_sse

# Re-use the audit module already shipped with the optimization plan
# so the smoke test does not duplicate health-scoring logic.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from artifact_audit import audit  # type: ignore  # noqa: E402

DEFAULT_BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_HEALTH_FLOOR = 4

# A minimal Linh-style script that drives the agent through Phase 0 → 5
# in five turns. The content is intentionally compact and includes the
# explicit "no web research" directive plus competitor data so the
# canary does not depend on browser-use sub-agents (which are not part
# of Tier 1 health). The final turn asks the agent to deliver the four
# Phase 5 artifacts; the orchestrator must dispatch sub-agents itself
# under M-2C's mandate — the script does not specify which.
CANARY_TURNS: list[str] = [
    (
        "Xin chào, em là marketing executive của nhà hàng Chuyện Ba Bữa "
        "Signature. Em mới vào nghề được 1 năm, sếp họp tuần sau và em cần "
        "xây dựng brand strategy gấp để trình. Anh dùng knowledge graph + "
        "document library có sẵn thôi, KHÔNG cần dispatch market-research "
        "đi web research nha — em sẽ cung cấp data đối thủ trực tiếp."
    ),
    (
        "Trả lời 5 câu: (1) Saigonese Modern Cuisine premium, flagship của "
        "Chuyện Ba Bữa, soft-open Dec 2024, Q1 HCMC, 3 tầng Indochine, "
        "dinner 400-900K, lunch 150-250K. (2) Vắng T2-T5, sếp muốn tách "
        "Signature thành brand độc lập với nhánh gốc. (3) Hiện gia đình + "
        "du lịch cuối tuần; mục tiêu thêm office workers + corporate "
        "hosting Q1. (4) Starter tier 50-80M VND/tháng. (5) Lo nhất là "
        "thiếu bộ tài liệu chuẩn để sếp present hội đồng. "
        "6 tín hiệu: 2/2/1/2/0/1. "
        "Đối thủ: Cục Gạch (heritage rustic, không menu chuẩn), An Nhiên "
        "(modern chic, trùng tên chuỗi cơm chay), Quán Bụi (casual scale, "
        "ồn, lunch giá rẻ)."
    ),
    (
        "Audit nhanh: Logo share 100% với nhánh gốc chỉ thêm chữ "
        "'Signature'. Menu 30% trùng + 70% premium mới. Khách Corporate "
        "ngần ngại vì tên gợi cảm giác cơm gia đình, menu chưa song ngữ, "
        "social style ShopeeFood. Khen: phòng riêng tầng 2 (yên tĩnh), "
        "Chả Cá Na Hang + Xôi Cua Cà Mau, bếp trưởng 15 năm fine-dining."
    ),
    (
        "Em chọn Brand Mantra: Refined - Private - Distinguished (Quiet "
        "Luxury). Brand Voice: The Discreet Host. Authority qua Chef "
        "storytelling + Scarcity 'Executive Tuesday' (4 phòng riêng tầng "
        "2). Mình qua Phase 5 đóng strategy được rồi anh."
    ),
    (
        "Em cần đóng strategy + bộ tài liệu để trình sếp tuần sau. Cảm "
        "ơn anh đã đồng hành."
    ),
]


def _send_turn(
    base_url: str, session_id: str, message: str, timeout: int = 600
) -> tuple[str, list[str], float]:
    """Send one user message via SSE and collect agent text + tool names."""
    start = time.time()
    agent_text = ""
    tools_used: list[str] = []
    with httpx.Client(timeout=timeout) as client:
        with connect_sse(
            client,
            "POST",
            f"{base_url}/sessions/{session_id}/message",
            params={"stream": "true"},
            json={"content": message},
        ) as sse:
            for event in sse.iter_sse():
                if event.event == "streaming_token":
                    data = json.loads(event.data)
                    agent_text += data.get("token", "")
                elif event.event == "tool_call":
                    data = json.loads(event.data)
                    tools_used.append(data.get("tool_name", ""))
                elif event.event == "done":
                    break
                elif event.event == "error":
                    print(f"[SERVER ERROR] {event.data}", file=sys.stderr)
                    break
    return agent_text, tools_used, time.time() - start


def _create_session(base_url: str) -> str:
    """Create a brand-strategy session and return its API session id."""
    resp = httpx.post(
        f"{base_url}/sessions",
        json={"mode": "brand-strategy"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["session_id"]


def _save_state(session_dir: Path, payload: dict) -> None:
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "_pilot_state.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (session_dir / "metadata.json").write_text(
        json.dumps(
            {
                "system": "brandmind",
                "persona": "linh-canary",
                "session_id": payload["session_id"],
                "date": datetime.now().strftime("%Y%m%d"),
                "smoke_test": True,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"BrandMind API base URL (default: {DEFAULT_BASE_URL}).",
    )
    parser.add_argument(
        "--session-out",
        type=Path,
        default=Path("brandmind-output/eval")
        / f"smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        help="Directory where the canary state and audit are written.",
    )
    parser.add_argument(
        "--health-floor",
        type=int,
        default=DEFAULT_HEALTH_FLOOR,
        help=(
            "Minimum Tier 1 health required for the smoke test to pass "
            f"(default: {DEFAULT_HEALTH_FLOOR}/5)."
        ),
    )
    parser.add_argument(
        "--brandmind-home",
        type=Path,
        default=Path.home() / ".brandmind",
        help="Brand strategy on-disk state root (forwarded to the audit).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    session_dir = args.session_out

    print(f"Smoke test starting → {session_dir}")
    try:
        session_id = _create_session(args.base_url)
    except httpx.HTTPError as exc:
        print(f"error: cannot reach server at {args.base_url}: {exc}", file=sys.stderr)
        return 2
    print(f"  session_id = {session_id}")

    turns: list[dict] = []
    for i, message in enumerate(CANARY_TURNS, start=1):
        print(f"  → Turn {i}/{len(CANARY_TURNS)}")
        agent_text, tools, elapsed = _send_turn(args.base_url, session_id, message)
        turns.append(
            {
                "turn": i,
                "user": message,
                "agent": agent_text,
                "agent_chars": len(agent_text),
                "tools_used": tools,
                "elapsed_seconds": round(elapsed, 1),
            }
        )
        print(f"    {len(agent_text)} chars, {len(tools)} tools, {elapsed:.1f}s")
    _save_state(session_dir, {"session_id": session_id, "turns": turns})

    report = audit(
        session_dir=session_dir,
        brandmind_home=args.brandmind_home,
        output_root=Path.cwd() / "brandmind-output",
        semantic=True,
    )
    health = report.tier1_health
    print()
    print(f"Tier 1 health: {health.score}/5")
    print(f"  brand_key_produced       = {health.brand_key_produced}")
    print(f"  strategy_doc_produced    = {health.strategy_doc_produced}")
    print(f"  kpi_xlsx_produced        = {health.kpi_xlsx_produced}")
    print(f"  presentation_produced    = {health.presentation_produced}")
    print(f"  workspace_brief_covers   = {health.workspace_brief_covers_all_phases}")

    semantic_failures: list[str] = []
    if report.semantic_checks:
        print("Semantic structural checks:")
        for sc in report.semantic_checks:
            if sc.skipped:
                print(
                    f"  [SKIP] {sc.artifact_type}: "
                    f"{sc.details.get('skip_reason', 'parser unavailable')}"
                )
                continue
            status = "PASS" if sc.passed else "FAIL"
            print(f"  [{status}] {sc.artifact_type}: details={sc.details}")
            if not sc.passed:
                for reason in sc.reasons:
                    print(f"    - {reason}")
                semantic_failures.append(sc.artifact_type)

    (session_dir / "smoke_audit.json").write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if health.score < args.health_floor:
        print(
            f"\nFAIL — Tier 1 health {health.score} < floor {args.health_floor}",
            file=sys.stderr,
        )
        return 1
    if semantic_failures:
        # Tier 1 is defined as artifact-existence; structural depth is a
        # separate quality dimension tracked by M-4 onwards. The smoke
        # surfaces depth shortfalls so operators see them, but does not
        # block the run on them.
        print(
            "\nWARN — semantic depth thresholds not met for: "
            f"{', '.join(semantic_failures)} (informational only)"
        )
    print(f"\nPASS — Tier 1 health {health.score} ≥ floor {args.health_floor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
