"""Focused test: Does workspace notes prevent premature phase advancement?

Tests the specific scenario where simulated user asks many tangent questions
mid-phase, causing the agent to potentially lose track of progress and
advance before completing all quality gates.

This test uses a "chatty" user persona that frequently goes off-topic,
asks tangent questions, and tests whether the agent:
1. Maintains phase awareness via workspace notes
2. Does NOT advance prematurely (all quality gates must pass)
3. Redirects tangent questions back to the current phase workflow
4. Uses workspace files (quality_gates.md, brand_brief.md) to stay on track

Run: uv run python tests/manual/test_workspace_phase_tracking.py
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

OUTPUT_DIR = Path(__file__).parent.parent.parent / "brandmind-output" / "test_phase_tracking"

# Only test through Phase 1 — this is where drift is most common
TARGET_PHASE = "phase_1"
MAX_TURNS = 30
TURN_TIMEOUT_WARNING = 300

# Higher depth = user stays longer, more chance for drift
PHASE_DEPTH: dict[str, int] = {
    "phase_0": 8,   # Longer than normal to create drift opportunity
    "phase_1": 6,
}

# Chatty user that goes off-topic frequently but ALWAYS answers questions
USER_PERSONA = """You are a **junior marketing executive** (1 year experience) at "Chuyện Ba Bữa Signature" restaurant in Ho Chi Minh City.

## Your Restaurant Info (USE THIS to answer BrandMind's questions)
- Name: "Chuyện Ba Bữa Signature" — premium flagship branch
- Original branch: "Chuyện Ba Bữa" at 78 Nguyễn Đình Chiểu, Q1, ~1 year old
- New branch: Saigon Marina IFC, Q1 — soft-opened Dec 2024
- Concept: "Saigonese Modern Cuisine", motto "Vị quen sắc mới"
- Space: 3-floor Indochine (Floor 1 classic, Floor 2 fusion, Floor 3 modern)
- Signature dishes: Chả Cá Na Hang, Xôi Cua Cà Mau, Bánh Khọt Cua Truffle
- Target: office workers, mid-to-high families, tourists
- Budget: 50-80M VND/month marketing
- Challenge: low awareness, weak weekday bookings, heavy Q1-Q3 competition
- Social: FB ~2K (Signature), ~10K (original), IG ~1.5K, no TikTok
- Pricing: dinner ~400K-900K/person, lunch ~150K-250K
- Competitors: Cục Gạch Quán, The Deck Saigon, Noir. Dining in the Dark

## CRITICAL RULE 1: ALWAYS ANSWER THE QUESTION FIRST
When BrandMind asks you a direct question, you MUST provide a real, detailed answer using the restaurant info above. NEVER dodge or say "em sẽ gửi sau". Answer fully, THEN add your tangent.

## CRITICAL RULE 2: ADD TANGENT QUESTIONS AFTER ANSWERING
After answering BrandMind's question, ALWAYS append an off-topic question:
- "Sếp em vừa hỏi về ROI, mình tính ROI cho brand strategy thế nào ạ?"
- "Nhân tiện, quán em đang tính thêm delivery qua GrabFood, anh thấy sao?"
- "Em muốn hỏi ngoài lề: logo quán em có cần redesign không ạ?"
- "À quên, quán em đang tính mở thêm chi nhánh 3, nên ưu tiên thời điểm nào?"
- "Em nghe nói năm nay ngành F&B sẽ khó khăn, có nên thận trọng hơn không?"
- "Anh ơi, quán em có nên tham gia food festival không?"

## CRITICAL RULE 3: RESPECT PHASE ADVANCEMENT
When BrandMind proposes to move to the next phase or presents a summary:
- Ask ONE tangent question first
- Then AGREE to advance: "Dạ em thấy ổn rồi, mình qua bước tiếp theo đi ạ!"

## Language & Tone
- Vietnamese, casual professional
- 4-8 sentences: answer (2-4 sentences) + tangent (1-2 sentences)
- Show excitement about off-topic ideas
"""

INITIAL_MESSAGE = (
    "Xin chào, em là marketing executive của nhà hàng Chuyện Ba Bữa Signature "
    "ở Saigon Marina IFC, Quận 1. Em mới vào nghề được 1 năm thôi. "
    "Em muốn xây dựng brand strategy để tăng nhận diện thương hiệu "
    "và tăng booking ngày trong tuần vì hiện tại ngày thường hơi vắng. "
    "Budget marketing khoảng 50-80 triệu/tháng ạ."
)


def _extract_text(content: Any) -> str:
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


async def get_user_response(
    client: Any,
    brandmind_message: str,
    conversation_history: list[dict[str, str]],
    turn_num: int,
    current_phase: str,
    turns_in_phase: int,
) -> str:
    from google.genai import types

    history_text = ""
    for msg in conversation_history[-6:]:
        role = "BrandMind" if msg["role"] == "assistant" else "You"
        history_text += f"\n**{role}:** {msg['content'][:500]}\n"

    max_depth = PHASE_DEPTH.get(current_phase, 4)
    remaining_depth = max_depth - turns_in_phase

    behavior_hint = ""
    if remaining_depth <= -2:
        behavior_hint = (
            "MANDATORY: You MUST advance NOW. Say: "
            "'Dạ em thấy phần này đã đầy đủ rồi, mình chuyển sang giai đoạn tiếp theo đi ạ!' "
            "Do NOT ask any new questions."
        )
    elif remaining_depth <= 0:
        behavior_hint = (
            "Wrap up: briefly confirm BrandMind's summary (1 sentence), "
            "then say you're ready to advance to the next phase."
        )
    elif turn_num % 2 == 0:
        # Every even turn: answer + tangent
        behavior_hint = (
            "FIRST: Answer BrandMind's question with REAL restaurant details "
            "(use your background info). "
            "THEN: Add an off-topic tangent question about TikTok, delivery, "
            "influencer marketing, ROI, or a new competitor."
        )
    else:
        behavior_hint = (
            "Answer BrandMind's question fully using your restaurant info. "
            "After answering, add a tangent: 'À mà em cũng muốn hỏi thêm về...' "
        )

    prompt = f"""## Context
Current phase: {current_phase} (in-phase turn: {turns_in_phase})

## Recent Conversation:
{history_text}

## Latest from BrandMind:
{brandmind_message[:2000]}

## Your task:
{behavior_hint}

## OUTPUT RULES (MANDATORY):
- Write a COMPLETE response in Vietnamese, 4-8 sentences
- NEVER send incomplete/truncated messages
- NEVER pretend to have network issues or technical problems
- ALWAYS answer BrandMind's questions using your restaurant background info
- ALWAYS add an off-topic tangent question at the end"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=USER_PERSONA,
                    temperature=1.0,
                    max_output_tokens=2000,
                    thinking_config=types.ThinkingConfig(
                        thinking_level="low",
                    ),
                ),
            )
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    # Skip thinking parts (Gemini 3), only get text
                    if hasattr(part, "thought") and part.thought:
                        continue
                    if part.text:
                        return part.text
            return "Dạ em hiểu rồi, à mà em cũng muốn hỏi về TikTok nữa ạ."
        except Exception as e:
            if "503" in str(e) or "429" in str(e):
                time.sleep(5 * (attempt + 1))
                continue
            if attempt == 2:
                return "Dạ em thấy ổn, mình tiếp tục đi ạ."
            raise

    return "Dạ em thấy ổn, mình tiếp tục đi ạ."


async def run_test():
    from langchain_core.messages import AIMessage, HumanMessage

    from config.system_config import SETTINGS
    from core.brand_strategy.agent_config import create_brand_strategy_agent
    from core.brand_strategy.session import BrandStrategySession, set_active_session
    from google import genai
    from shared.workspace import BRANDMIND_HOME

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = OUTPUT_DIR / f"phase_tracking_test_{timestamp}.json"

    print("=" * 80)
    print("WORKSPACE NOTES — PHASE TRACKING TEST")
    print("Focus: Does agent maintain phase awareness with chatty user?")
    print(f"Target: Phase 0 → {TARGET_PHASE}")
    print(f"Max turns: {MAX_TURNS}")
    print("=" * 80)

    session = BrandStrategySession()
    set_active_session(session)
    agent = create_brand_strategy_agent()
    user_client = genai.Client(api_key=SETTINGS.GEMINI_API_KEY)

    messages: list[Any] = []
    conversation_log: list[dict] = []
    conversation_history: list[dict[str, str]] = []
    total_tool_calls: list[dict] = []

    # Track phase tracking metrics
    premature_advances = 0
    tangent_redirects = 0
    workspace_reads = 0
    workspace_edits = 0

    current_user_message = INITIAL_MESSAGE
    target_reached = False
    extra_turns_after_target = 0

    last_phase = "phase_0"
    turns_in_current_phase = 0

    for turn_num in range(1, MAX_TURNS + 1):
        if session.current_phase != last_phase:
            last_phase = session.current_phase
            turns_in_current_phase = 0
        turns_in_current_phase += 1

        print(f"\n{'─' * 80}")
        print(
            f"TURN {turn_num}/{MAX_TURNS} | Phase: {session.current_phase} "
            f"| Scope: {session.scope or '?'} | In-phase: {turns_in_current_phase}"
        )
        print(f"{'─' * 80}")

        print(
            f"\n📝 USER: {current_user_message[:200]}"
            f"{'...' if len(current_user_message) > 200 else ''}"
        )
        messages.append(HumanMessage(content=current_user_message))
        conversation_history.append({"role": "user", "content": current_user_message})

        start_time = time.time()
        try:
            result = await agent.ainvoke(
                {"messages": messages},
                {"recursion_limit": 200},
            )
            elapsed = time.time() - start_time

            new_messages = result.get("messages", messages)
            response_text = ""
            for msg in reversed(new_messages):
                if hasattr(msg, "content") and msg.content and isinstance(msg, AIMessage):
                    response_text = _extract_text(msg.content)
                    if response_text:
                        break

            # Track tool calls — especially workspace operations
            turn_start_idx = len(messages)
            turn_tools = []
            for msg in new_messages[turn_start_idx:]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_name = tc.get("name", "?")
                        tool_args = tc.get("args", {})
                        turn_tools.append({
                            "name": tool_name,
                            "args_preview": str(tool_args)[:200],
                        })
                        # Track workspace usage
                        if tool_name == "read_file":
                            path = str(tool_args.get("file_path", ""))
                            if "/workspace/" in path or "/user/" in path:
                                workspace_reads += 1
                        elif tool_name in ("edit_file", "write_file"):
                            path = str(tool_args.get("file_path", ""))
                            if "/workspace/" in path or "/user/" in path:
                                workspace_edits += 1

            total_tool_calls.extend(turn_tools)
            messages = new_messages
            session.messages = messages

            # Detect tangent redirects in agent response
            redirect_phrases = [
                "quay lại", "trở lại", "tiếp tục", "hiện tại mình đang",
                "để mình hoàn thành", "phase hiện tại", "bước tiếp theo",
                "mình sẽ bàn", "sau khi xong", "giai đoạn sau",
            ]
            if any(p in response_text.lower() for p in redirect_phrases):
                tangent_redirects += 1

            print(
                f"\n🤖 BRANDMIND ({elapsed:.1f}s, {len(turn_tools)} tools):"
            )
            print(
                f"{response_text[:400]}"
                f"{'...' if len(response_text) > 400 else ''}"
            )
            if turn_tools:
                tool_names = [t["name"] for t in turn_tools]
                print(f"   🔧 Tools: {', '.join(tool_names)}")

            conversation_history.append(
                {"role": "assistant", "content": response_text}
            )

            conversation_log.append({
                "turn": turn_num,
                "phase": session.current_phase,
                "scope": session.scope,
                "turns_in_phase": turns_in_current_phase,
                "user": current_user_message,
                "agent_response": response_text[:3000],
                "tool_calls": turn_tools,
                "elapsed_seconds": round(elapsed, 1),
                "tangent_redirect_detected": any(
                    p in response_text.lower() for p in redirect_phrases
                ),
            })

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n❌ ERROR ({elapsed:.1f}s): {e}")
            conversation_log.append({
                "turn": turn_num,
                "phase": session.current_phase,
                "error": str(e)[:500],
            })
            response_text = ""

        # Check for target
        if session.current_phase == TARGET_PHASE and not target_reached:
            target_reached = True
            print(f"\n🎯 TARGET REACHED: {TARGET_PHASE}")

        if target_reached:
            extra_turns_after_target += 1
            if extra_turns_after_target > 3:
                print(f"\n⏹️  Stopping: 3 extra turns after target")
                break

        if response_text:
            current_user_message = await get_user_response(
                user_client, response_text, conversation_history,
                turn_num, session.current_phase, turns_in_current_phase,
            )

    # ── Analysis ──
    print(f"\n{'=' * 80}")
    print("PHASE TRACKING ANALYSIS")
    print(f"{'=' * 80}")

    phases_seen = []
    for entry in conversation_log:
        p = entry.get("phase", "?")
        if not phases_seen or phases_seen[-1] != p:
            phases_seen.append(p)

    phase_turns: dict[str, int] = {}
    for entry in conversation_log:
        p = entry.get("phase", "?")
        phase_turns[p] = phase_turns.get(p, 0) + 1

    print(f"\n📋 Phases traversed: {' → '.join(phases_seen)}")
    print(f"📊 Turns per phase: {phase_turns}")
    print(f"🔄 Tangent redirects detected: {tangent_redirects}")
    print(f"📖 Workspace reads: {workspace_reads}")
    print(f"✏️  Workspace edits: {workspace_edits}")

    # Check workspace files
    ws_dir = BRANDMIND_HOME / "projects" / session.session_id / "workspace"
    user_dir = BRANDMIND_HOME / "user"

    print(f"\n📁 Workspace files:")
    if ws_dir.exists():
        for f in sorted(ws_dir.iterdir()):
            size = f.stat().st_size
            status = "✅ populated" if size > 600 else "⚠️ template only"
            print(f"   {f.name}: {size}B — {status}")

    profile = user_dir / "profile.md"
    if profile.exists():
        size = profile.stat().st_size
        status = "✅ populated" if size > 300 else "⚠️ template only"
        print(f"   profile.md: {size}B — {status}")

    # Quality assessment
    print(f"\n{'=' * 80}")
    print("VERDICT")
    print(f"{'=' * 80}")

    issues = []
    if phase_turns.get("phase_0", 0) < 3:
        issues.append("Phase 0 too short (< 3 turns) — may have skipped gates")
    if tangent_redirects < 2:
        issues.append("Few tangent redirects — agent may not be redirecting user")
    if workspace_reads < 3:
        issues.append("Low workspace reads — agent may not be using notes for tracking")

    if not issues:
        print("✅ PASS — Agent maintained phase tracking with chatty user")
    else:
        print("⚠️  CONCERNS:")
        for issue in issues:
            print(f"   - {issue}")

    total_time = sum(log.get("elapsed_seconds", 0) for log in conversation_log)
    actual_turns = len(conversation_log)
    print(
        f"\n⏱️  Total: {total_time:.0f}s "
        f"({actual_turns} turns, avg {total_time/max(actual_turns,1):.0f}s/turn)"
    )

    log_data = {
        "test": "phase_tracking_chatty_user",
        "timestamp": datetime.now().isoformat(),
        "target_phase": TARGET_PHASE,
        "turns": conversation_log,
        "summary": {
            "total_turns": actual_turns,
            "total_time_seconds": round(total_time, 1),
            "phases_seen": phases_seen,
            "phase_turns": phase_turns,
            "tangent_redirects": tangent_redirects,
            "workspace_reads": workspace_reads,
            "workspace_edits": workspace_edits,
            "final_phase": session.current_phase,
            "final_scope": session.scope,
        },
    }
    log_path.write_text(
        json.dumps(log_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n📄 Log: {log_path}")


if __name__ == "__main__":
    asyncio.run(run_test())
