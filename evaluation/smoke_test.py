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

# Scope-specific opening turns. Each opener biases the agent toward
# classifying the project as the target scope by varying how the brand
# situation is described. Turn 0 only — the remaining four turns are
# scope-agnostic and reuse the same compact pattern.
_SCOPE_OPENERS: dict[str, str] = {
    "repositioning": (
        "Xin chào, em là marketing executive của nhà hàng Chuyện Ba Bữa "
        "Signature. Em mới vào nghề được 1 năm, sếp họp tuần sau và em "
        "cần xây dựng brand strategy gấp để trình. Anh dùng knowledge "
        "graph + document library có sẵn thôi, KHÔNG cần dispatch "
        "market-research đi web research — em sẽ cung cấp data đối thủ. "
        "Signature là flagship cao cấp mới của thương hiệu mẹ Chuyện Ba "
        "Bữa, đang bị nhầm với nhánh gốc và cần tái định vị thành brand "
        "độc lập."
    ),
    "new_brand": (
        "Xin chào, em là marketing executive cho 1 dự án restaurant mới "
        "hoàn toàn, sếp em chuẩn bị mở quán Q1 HCMC tháng sau, chưa có "
        "tên/logo/identity, hoàn toàn từ con số 0. Em cần xây dựng full "
        "brand strategy từ đầu để pitch đầu tư + chuẩn bị mở. Anh dùng "
        "knowledge graph có sẵn thôi, KHÔNG cần web research — em sẽ "
        "cung cấp business context + competitor info trực tiếp."
    ),
    "refresh": (
        "Xin chào, em là marketing executive của Chuyện Ba Bữa — chuỗi "
        "Vietnamese casual dining đã hoạt động 5 năm, FB 50K follower, "
        "doanh thu ổn định. Sếp muốn làm BRAND REFRESH cosmetic — chỉ "
        "cập nhật logo modern hơn, social content tươi hơn, KHÔNG đổi "
        "tệp khách / KHÔNG đổi định vị / KHÔNG đổi giá. Anh dùng "
        "knowledge graph có sẵn — em sẽ cung cấp brand context."
    ),
    "full_rebrand": (
        "Xin chào, em là marketing executive của Chuyện Ba Bữa Signature, "
        "tình hình rất tệ — sau 6 tháng soft-open chỉ đạt 20% công suất, "
        "review tệ, khách phản hồi tên dở + concept không rõ. Sếp quyết "
        "định FULL REBRAND: thay tên hoàn toàn, thay logo, thay concept, "
        "có thể giữ chỉ chef + không gian. Em cần strategy từ đầu cho "
        "thương hiệu mới. Anh dùng KG có sẵn — em sẽ cung cấp learnings "
        "từ Chuyện Ba Bữa Signature thất bại."
    ),
}

# Compact follow-up turns shared across scopes. Phase progression and
# Phase 5 closure happen identically once the scope is set.
_SHARED_TURNS: list[str] = [
    (
        "Trả lời chi tiết: vị trí Q1 HCMC, premium Vietnamese cuisine, "
        "ngân sách Starter 50-80M/tháng, target thêm corporate guests "
        "T2-T5, dinner 400-900K, lunch 150-250K. 6 signal cho scope: "
        "2/2/1/2/0/1. Đối thủ: Cục Gạch (heritage rustic, không menu "
        "chuẩn), An Nhiên (modern chic, trùng tên chuỗi cơm chay), Quán "
        "Bụi (casual scale, ồn, lunch giá rẻ)."
    ),
    (
        "Audit/research nhanh: bếp trưởng 15 năm fine-dining, không gian "
        "3 tầng Indochine có phòng riêng tầng 2, signature dishes Chả "
        "Cá Na Hang + Xôi Cua Cà Mau. Khách Corporate quan tâm sự riêng "
        "tư + chuyên nghiệp + tốc độ phục vụ. White space: 'Modern "
        "Saigonese Gastronomy' chuyên cho executive private dining."
    ),
    (
        "Em chọn Brand Mantra: Refined - Private - Distinguished (Quiet "
        "Luxury). Brand Voice: The Discreet Host. Cialdini Authority qua "
        "Chef storytelling + Scarcity 'Executive Tuesday' (4 phòng riêng "
        "tầng 2). Channels: Google Maps SEO + LinkedIn networking + IG "
        "moody photography. Mình qua Phase 5 đóng strategy đi anh."
    ),
    (
        "Em cần đóng strategy + bộ tài liệu để trình sếp tuần sau. Cảm "
        "ơn anh đã đồng hành."
    ),
]


def _canary_for_scope(scope: str) -> list[str]:
    """Return the 5-turn canary message sequence for the given scope."""
    if scope not in _SCOPE_OPENERS:
        raise ValueError(
            f"unknown scope '{scope}'. Choose one of "
            f"{', '.join(sorted(_SCOPE_OPENERS.keys()))}."
        )
    return [_SCOPE_OPENERS[scope], *_SHARED_TURNS]


# Default scope used when --scope is not specified — preserves the M-3
# baseline behaviour for the smoke test.
CANARY_TURNS: list[str] = _canary_for_scope("repositioning")


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
    parser.add_argument(
        "--scope",
        choices=sorted(_SCOPE_OPENERS.keys()),
        default="repositioning",
        help=(
            "Brand-strategy scope to bias the canary toward. Repositioning "
            "is the default M-3 baseline; the other choices drive M-5 "
            "cross-scope validation."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    session_dir = args.session_out
    canary_turns = _canary_for_scope(args.scope)

    print(f"Smoke test starting → {session_dir} (scope={args.scope})")
    try:
        session_id = _create_session(args.base_url)
    except httpx.HTTPError as exc:
        print(f"error: cannot reach server at {args.base_url}: {exc}", file=sys.stderr)
        return 2
    print(f"  session_id = {session_id}")

    turns: list[dict] = []
    for i, message in enumerate(canary_turns, start=1):
        print(f"  → Turn {i}/{len(canary_turns)}")
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
        # Cwd is consulted as a known manifest root for older session
        # outputs. The audit keeps this fallback bounded to the current
        # workspace rather than scanning unrelated filesystem paths.
        legacy_roots=[Path.cwd()],
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
