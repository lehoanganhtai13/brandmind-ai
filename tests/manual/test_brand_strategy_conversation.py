"""Manual test: Multi-turn brand strategy conversation.

Simulates a junior marketing executive using BrandMind to develop
a brand strategy for "Chuyện Ba Bữa Signature" restaurant.

Run: uv run python tests/manual/test_brand_strategy_conversation.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Responses from the "marketing executive" persona
# Each response is sent after receiving the agent's previous message
CONVERSATION_TURNS: list[dict[str, str]] = [
    # Turn 1: Initial greeting
    {
        "role": "user",
        "message": (
            "Xin chào, tôi là marketing executive của nhà hàng Chuyện Ba Bữa Signature. "
            "Tôi muốn xây dựng brand strategy để tăng nhận diện thương hiệu và "
            "nhận được nhiều booking hơn cho nhà hàng."
        ),
    },
    # Turn 2: Answer business questions (Phase 0 interview)
    {
        "role": "user",
        "message": (
            "Dạ để em chia sẻ về nhà hàng:\n\n"
            "- Chuyện Ba Bữa Signature là nhà hàng flagship mới mở tháng 12/2024, "
            "concept 'Saigonese Modern Cuisine' - ẩm thực Sài Gòn hiện đại. "
            "Ngoài ra còn có chi nhánh gốc 'Chuyện Ba Bữa' ở 78 Nguyễn Đình Chiểu, Quận 1.\n"
            "- Target khách: dân văn phòng, gia đình trung lưu-cao, khách du lịch thích "
            "trải nghiệm ẩm thực Việt Nam cao cấp\n"
            "- Budget marketing khoảng 50-80 triệu/tháng\n"
            "- Mục tiêu: tăng nhận diện thương hiệu, tăng booking đặt bàn, "
            "đặc biệt vào các ngày trong tuần còn vắng\n"
            "- Thách thức: Signature mới mở nên chưa nhiều người biết, "
            "cạnh tranh rất nhiều nhà hàng Việt cao cấp ở khu vực Quận 1-3\n"
            "- Timeline: muốn thấy kết quả trong 3-6 tháng\n"
            "- Không gian: 3 tầng phong cách Indochine (tầng 1 cổ điển, "
            "tầng 2 giao thoa, tầng 3 hiện đại)\n"
            "- Món signature: Chả Cá Na Hang, Xôi Cua Cà Mau, Bánh Khọt Cua Truffle"
        ),
    },
    # Turn 3: Confirm/clarify scope
    {
        "role": "user",
        "message": (
            "Đúng rồi, nhà hàng gốc Chuyện Ba Bữa đã hoạt động được khoảng 1 năm rồi "
            "nên có một số khách quen. Signature là phiên bản nâng cấp về không gian và "
            "menu, nhưng vẫn giữ tinh thần 'vị quen sắc mới'. "
            "Em nghĩ đây không phải là brand mới hoàn toàn mà là mở rộng thương hiệu. "
            "Nhưng em cũng không chắc nên approach như thế nào, anh/chị tư vấn giúp em."
        ),
    },
    # Turn 4: Confirm problem statement / scope
    {
        "role": "user",
        "message": (
            "Em đồng ý với phân tích đó. Vậy mình tiến hành theo hướng đó được rồi ạ."
        ),
    },
    # Turn 5: Phase 1 - respond to research questions
    {
        "role": "user",
        "message": (
            "Dạ về đối thủ cạnh tranh trực tiếp em biết có:\n"
            "- Nhà hàng Cục Gạch Quán (Quận 1) - concept Việt truyền thống\n"
            "- The Deck Saigon - fine dining Việt\n"
            "- Noir. Dining in the Dark - trải nghiệm độc đáo\n"
            "- Nhà hàng An Nhiên - ẩm thực Việt fusion\n"
            "- Quán Bụi - Việt casual upscale\n\n"
            "Còn gián tiếp thì các nhà hàng Nhật, Hàn, Ý cao cấp cũng cạnh tranh "
            "vì target cùng phân khúc khách.\n\n"
            "Về social media hiện tại:\n"
            "- Facebook: Chuyện Ba Bữa Signature page mới có ~2000 followers\n"
            "- Instagram: @chuyenbabuasignature khoảng 1500 followers\n"
            "- Chưa có TikTok riêng\n"
            "- Chi nhánh gốc Chuyện Ba Bữa thì FB có khoảng 10k followers"
        ),
    },
    # Turn 6: Continue Phase 1 / agree to proceed
    {
        "role": "user",
        "message": (
            "Dạ em thấy phân tích rất chi tiết. Mình tiếp tục bước tiếp theo được rồi ạ."
        ),
    },
]

OUTPUT_DIR = Path(__file__).parent.parent.parent / "brandmind-output" / "test_conversation"


def _extract_text(content: Any) -> str:
    """Extract text from agent message content."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
            elif isinstance(part, str):
                parts.append(part)
        return "\n".join(parts)
    return str(content)


def _extract_tool_calls(messages: list) -> list[dict]:
    """Extract all tool calls from message history."""
    calls = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                calls.append({
                    "name": tc.get("name", "unknown"),
                    "args_preview": str(tc.get("args", {}))[:150],
                })
    return calls


async def run_test():
    """Run multi-turn brand strategy conversation test."""
    # Lazy imports to avoid slow startup
    from langchain_core.messages import AIMessage, HumanMessage

    from core.brand_strategy.agent_config import create_brand_strategy_agent
    from core.brand_strategy.session import (
        BrandStrategySession,
        set_active_session,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = OUTPUT_DIR / f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    print("=" * 80)
    print("BRANDMIND BRAND STRATEGY — AUTOMATED CONVERSATION TEST")
    print(f"Scenario: Chuyện Ba Bữa Signature — Marketing Executive")
    print(f"Turns: {len(CONVERSATION_TURNS)}")
    print(f"Log: {log_path}")
    print("=" * 80)

    # Setup
    session = BrandStrategySession()
    set_active_session(session)
    agent = create_brand_strategy_agent()

    messages: list[Any] = []
    conversation_log: list[dict] = []
    total_tool_calls: list[dict] = []

    for i, turn in enumerate(CONVERSATION_TURNS):
        turn_num = i + 1
        user_msg = turn["message"]

        print(f"\n{'─' * 80}")
        print(f"TURN {turn_num}/{len(CONVERSATION_TURNS)}")
        print(f"{'─' * 80}")
        print(f"\n📝 USER: {user_msg[:120]}...")

        messages.append(HumanMessage(content=user_msg))

        start_time = time.time()
        try:
            result = await agent.ainvoke(
                {"messages": messages},
                {"recursion_limit": 200},
            )
            elapsed = time.time() - start_time

            # Extract response
            new_messages = result.get("messages", messages)
            response_text = ""
            for msg in reversed(new_messages):
                if hasattr(msg, "content") and msg.content and isinstance(msg, AIMessage):
                    response_text = _extract_text(msg.content)
                    if response_text:
                        break

            # Extract tool calls from this turn
            turn_start_idx = len(messages)
            turn_tool_calls = _extract_tool_calls(new_messages[turn_start_idx:])
            total_tool_calls.extend(turn_tool_calls)

            messages = new_messages
            session.messages = messages

            # Print summary
            print(f"\n🤖 BRANDMIND ({elapsed:.1f}s, {len(turn_tool_calls)} tool calls):")
            print(f"{response_text[:500]}{'...' if len(response_text) > 500 else ''}")

            if turn_tool_calls:
                print(f"\n🔧 Tools used:")
                for tc in turn_tool_calls:
                    print(f"   - {tc['name']}: {tc['args_preview'][:80]}")

            # Log
            conversation_log.append({
                "turn": turn_num,
                "user": user_msg,
                "agent_response": response_text[:2000],
                "tool_calls": turn_tool_calls,
                "elapsed_seconds": round(elapsed, 1),
                "session_phase": session.current_phase,
                "session_scope": session.scope,
                "session_brand": session.brand_name,
            })

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n❌ ERROR ({elapsed:.1f}s): {e}")
            conversation_log.append({
                "turn": turn_num,
                "user": user_msg,
                "error": str(e),
                "elapsed_seconds": round(elapsed, 1),
            })
            # Don't break — try to continue

    # ── Final Analysis ──
    print(f"\n{'=' * 80}")
    print("PERFORMANCE ANALYSIS")
    print(f"{'=' * 80}")

    # Tool usage stats
    tool_counts: dict[str, int] = {}
    for tc in total_tool_calls:
        tool_counts[tc["name"]] = tool_counts.get(tc["name"], 0) + 1

    print(f"\n📊 Tool Usage Summary:")
    for name, count in sorted(tool_counts.items(), key=lambda x: -x[1]):
        print(f"   {name}: {count}x")

    kg_calls = tool_counts.get("search_knowledge_graph", 0)
    doc_calls = tool_counts.get("search_document_library", 0)
    web_calls = tool_counts.get("search_web", 0)
    research_calls = tool_counts.get("deep_research", 0)
    print(f"\n📚 Knowledge Verification:")
    print(f"   KG searches: {kg_calls}")
    print(f"   Doc searches: {doc_calls}")
    print(f"   Web searches: {web_calls}")
    print(f"   Deep research: {research_calls}")
    if kg_calls + doc_calls == 0:
        print(f"   ⚠️  NO knowledge verification via KG/docs!")
    elif kg_calls + doc_calls < 3:
        print(f"   ⚠️  Low knowledge verification — expected more KG/doc usage")
    else:
        print(f"   ✅ Good knowledge verification activity")

    print(f"\n📍 Session State:")
    print(f"   Phase: {session.current_phase}")
    print(f"   Scope: {session.scope or 'not set'}")
    print(f"   Brand: {session.brand_name or 'not set'}")

    report_progress_calls = tool_counts.get("report_progress", 0)
    print(f"\n📈 Phase Tracking:")
    print(f"   report_progress calls: {report_progress_calls}")
    if report_progress_calls == 0:
        print(f"   ⚠️  Agent never called report_progress!")

    total_time = sum(log.get("elapsed_seconds", 0) for log in conversation_log)
    print(f"\n⏱️  Total time: {total_time:.0f}s across {len(CONVERSATION_TURNS)} turns")
    print(f"   Average: {total_time / len(CONVERSATION_TURNS):.0f}s per turn")

    # Save log
    log_data = {
        "scenario": "Chuyện Ba Bữa Signature — Marketing Executive",
        "timestamp": datetime.now().isoformat(),
        "turns": conversation_log,
        "summary": {
            "total_turns": len(CONVERSATION_TURNS),
            "total_time_seconds": round(total_time, 1),
            "tool_counts": tool_counts,
            "final_phase": session.current_phase,
            "final_scope": session.scope,
            "final_brand": session.brand_name,
        },
    }
    log_path.write_text(json.dumps(log_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n📄 Full log saved to: {log_path}")


if __name__ == "__main__":
    asyncio.run(run_test())
