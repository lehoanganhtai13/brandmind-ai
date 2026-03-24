"""Automated brand strategy test with LLM-simulated user.

Uses a separate LLM (Gemini Flash) to play the role of a junior
marketing executive, responding dynamically to BrandMind's questions.

Run: uv run python tests/manual/test_brand_strategy_llm_user.py
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

OUTPUT_DIR = Path(__file__).parent.parent.parent / "brandmind-output" / "test_llm_user"

TARGET_PHASE = "phase_5"
MAX_TURNS = 50
TURN_TIMEOUT_WARNING = 300

# Expected depth per phase — how many turns the user should engage
# before suggesting to move on. Complex phases get more turns.
PHASE_DEPTH: dict[str, int] = {
    "phase_0": 4,      # Diagnosis — straightforward
    "phase_0_5": 3,    # Equity audit — moderate
    "phase_1": 5,      # Market research — needs discussion of findings
    "phase_2": 6,      # Positioning — most critical, needs deep POPs/PODs/stress test
    "phase_3": 5,      # Identity — creative decisions need feedback
    "phase_4": 4,      # Communication — framework + channel strategy
    "phase_5": 4,      # Deliverables — review + iterate
}

END_DETECTION_WINDOW = 3
END_SIMILARITY_THRESHOLD = 0.7

USER_PERSONA = """You are a **junior marketing executive** (1 year experience, fresh graduate) at "Chuyện Ba Bữa Signature" restaurant in Ho Chi Minh City. You are using BrandMind AI to develop a brand strategy.

## Your Background Knowledge

**Restaurant info:**
- "Chuyện Ba Bữa Signature" — premium flagship, soft-opened Dec 2024
- Original branch "Chuyện Ba Bữa" at 78 Nguyễn Đình Chiểu, Q1, ~1 year old
- Concept: "Saigonese Modern Cuisine", motto "Vị quen sắc mới"
- Space: 3-floor Indochine (Floor 1 classic, Floor 2 fusion, Floor 3 modern)
- Signature dishes: Chả Cá Na Hang, Xôi Cua Cà Mau, Bánh Khọt Cua Truffle, Nọng heo Iberico
- Target: office workers, mid-to-high families, tourists
- Budget: 50-80M VND/month marketing
- Challenge: low awareness, weak weekday bookings, heavy Q1-Q3 competition
- Social: FB ~2K (Signature), ~10K (original), IG ~1.5K, no TikTok
- Pricing: dinner ~400K-900K/person, lunch ~150K-250K

**Known competitors:** Cục Gạch Quán, The Deck Saigon, Noir. Dining in the Dark, An Nhiên, Quán Bụi

## BEHAVIORAL RULES

### Rule 1: ENGAGE, don't rubber-stamp
BAD: "Dạ em đồng ý, mình tiếp tục ạ."
GOOD: "Phần phân tích đối thủ rất hay, đặc biệt insight về Cục Gạch Quán. Nhưng em thắc mắc sao mình không xét thêm mấy quán Nhật Hàn cao cấp?"

### Rule 2: Ask "tại sao?" every 2-3 turns
When BrandMind introduces a concept, ask for explanation or example specific to your restaurant.

### Rule 3: Share concerns and doubts occasionally
"Em lo budget 50-80 triệu có đủ không?", "Sếp em hay hỏi ROI cụ thể"

### Rule 4: Detailed answers when asked about the restaurant
Share stories and observations, not one-liners.

### Rule 5: React specifically to visual/creative content
Comment on specific elements, not just "đẹp quá".

### Rule 6: Mention practical constraints occasionally
"Nhân viên đa phần part-time", "Em không có designer in-house"

### Rule 7: RESPECT THE PROCESS FLOW
This is CRITICAL. You are here to BUILD A STRATEGY, not just chat. When BrandMind:
- **Proposes to move to the next phase** → Agree after 1 brief comment or question. Do NOT keep asking new questions that delay the transition.
- **Presents a summary or quality gate** → Confirm it, suggest minor tweaks if needed, then let the process advance.
- **Has been in the same phase for 4+ turns** → YOU should proactively say something like "Em thấy phần này đã khá rõ rồi, mình qua bước tiếp theo được không ạ?"

Your GOAL is to complete the full brand strategy, not to explore every tangent forever. Balance curiosity with progress.

## Language & Tone
- Vietnamese, casual professional
- 3-7 sentences typically
- Show emotion: excitement about good ideas, concern about challenges
"""

INITIAL_MESSAGE = (
    "Xin chào, em là marketing executive của nhà hàng Chuyện Ba Bữa Signature. "
    "Em mới vào nghề được 1 năm thôi nên cũng chưa có nhiều kinh nghiệm về "
    "brand strategy lắm. Em muốn xây dựng brand strategy để tăng nhận diện "
    "thương hiệu và nhận được nhiều booking hơn cho nhà hàng ạ. "
    "Hiện tại ngày trong tuần hơi vắng khách, em muốn cải thiện chỗ đó."
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


def _detect_conversation_end(
    recent_responses: list[str],
    current_phase: str,
) -> bool:
    # Only detect end in late phases (phase_4 or phase_5)
    late_phases = {"phase_4", "phase_5"}
    if current_phase not in late_phases:
        return False

    if len(recent_responses) < END_DETECTION_WINDOW:
        return False
    window = recent_responses[-END_DETECTION_WINDOW:]

    end_patterns = ["chào tạm biệt", "chúc bạn", "hẹn gặp lại", "chúc mọi điều",
                     "rất trân trọng", "mảnh ghép cuối cùng", "hoàn thành hành trình"]
    end_count = sum(
        1 for resp in window
        if any(p in resp.lower() for p in end_patterns)
    )
    if end_count >= END_DETECTION_WINDOW - 1:
        return True

    # Check repetitive responses (thank-you loop)
    if len(window) >= 2:
        for i in range(len(window) - 1):
            words_a = set(window[i][:300].split())
            words_b = set(window[i + 1][:300].split())
            if words_a and words_b:
                overlap = len(words_a & words_b) / max(len(words_a), len(words_b))
                if overlap > END_SIMILARITY_THRESHOLD:
                    return True
    return False


async def get_user_response(
    client: Any,
    brandmind_message: str,
    conversation_history: list[dict[str, str]],
    turn_num: int,
    current_phase: str,
    turns_in_phase: int,
) -> str:
    from google.genai import types

    # Last 6 messages for context
    history_text = ""
    for msg in conversation_history[-6:]:
        role = "BrandMind" if msg["role"] == "assistant" else "You"
        history_text += f"\n**{role}:** {msg['content'][:500]}\n"

    # Phase-aware depth: how many turns before suggesting advance
    max_depth = PHASE_DEPTH.get(current_phase, 4)
    remaining_depth = max_depth - turns_in_phase

    behavior_hint = ""
    if remaining_depth <= -2:
        # WAY past target — force advance, no more questions
        behavior_hint = (
            "MANDATORY: You MUST move on NOW. Say ONLY something like: "
            "'Dạ em thấy phần này đã đầy đủ rồi, mình chuyển sang giai đoạn tiếp theo đi ạ!' "
            "Do NOT ask any new questions. Do NOT comment on details. Just agree and advance."
        )
    elif remaining_depth <= 0:
        # Past target depth — strongly push to advance
        behavior_hint = (
            "You have spent enough time in this phase. Your ONLY job now: "
            "briefly acknowledge BrandMind's point (1 sentence max), then "
            "clearly say you want to proceed to the next phase. "
            "Do NOT introduce new topics or ask follow-up questions."
        )
    elif remaining_depth == 1:
        # One turn left — wrap up
        behavior_hint = (
            "This is your last turn in this phase. Confirm BrandMind's summary "
            "or give brief feedback, then signal you're ready to move on."
        )
    elif turns_in_phase <= 2:
        # Early in phase — engage deeply
        behavior_hint = (
            "You're early in this phase — engage deeply. "
            "Ask a clarifying question, share a relevant observation, "
            "or raise a practical concern."
        )
    else:
        # Mid-phase — mix of engagement
        if turn_num % 3 == 0:
            behavior_hint = "Ask a clarifying question about a concept BrandMind mentioned."
        elif turn_num % 4 == 0:
            behavior_hint = "Share a specific story or observation from your restaurant."
        else:
            behavior_hint = "Give feedback on BrandMind's proposal — what you like, what concerns you."

    prompt = f"""## Context
Current phase: {current_phase} (you've been in this phase for {turns_in_phase} turns)

## Recent Conversation:
{history_text}

## Latest from BrandMind:
{brandmind_message[:1500]}

## Your task:
Respond naturally as the marketing executive.
{behavior_hint}

Respond in Vietnamese, 3-7 sentences."""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=USER_PERSONA,
                    temperature=0.8,
                    max_output_tokens=500,
                ),
            )
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        return part.text
            return "Dạ em hiểu rồi, mình qua bước tiếp theo được không ạ?"
        except Exception as e:
            if "503" in str(e) or "429" in str(e):
                wait = 5 * (attempt + 1)
                time.sleep(wait)
                continue
            if attempt == 2:
                return "Dạ em thấy ổn rồi, mình tiếp tục bước tiếp theo đi ạ."
            raise

    return "Dạ em thấy ổn rồi, mình tiếp tục bước tiếp theo đi ạ."


async def run_test():
    from langchain_core.messages import AIMessage, HumanMessage

    from core.brand_strategy.agent_config import create_brand_strategy_agent
    from core.brand_strategy.session import BrandStrategySession, set_active_session

    from google import genai
    from config.system_config import SETTINGS

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = OUTPUT_DIR / f"llm_user_test_{timestamp}.json"

    print("=" * 80)
    print("BRANDMIND — LLM USER TEST")
    print(f"Target: Phase 0 → {TARGET_PHASE}")
    print(f"Max turns: {MAX_TURNS}")
    print(f"Log: {log_path}")
    print("=" * 80)

    session = BrandStrategySession()
    set_active_session(session)
    agent = create_brand_strategy_agent()
    user_client = genai.Client(api_key=SETTINGS.GEMINI_API_KEY)

    messages: list[Any] = []
    conversation_log: list[dict] = []
    conversation_history: list[dict[str, str]] = []
    total_tool_calls: list[dict] = []
    recent_agent_responses: list[str] = []

    current_user_message = INITIAL_MESSAGE
    target_reached = False
    extra_turns_after_target = 0
    MAX_EXTRA_TURNS = 5

    # Track turns per phase for user behavior hints
    last_phase = "phase_0"
    turns_in_current_phase = 0

    for turn_num in range(1, MAX_TURNS + 1):
        # Track phase duration
        if session.current_phase != last_phase:
            last_phase = session.current_phase
            turns_in_current_phase = 0
        turns_in_current_phase += 1

        print(f"\n{'─' * 80}")
        print(f"TURN {turn_num}/{MAX_TURNS} | Phase: {session.current_phase} "
              f"| Scope: {session.scope or '?'} | In-phase: {turns_in_current_phase}")
        print(f"{'─' * 80}")

        print(f"\n📝 USER: {current_user_message[:200]}{'...' if len(current_user_message) > 200 else ''}")
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

            turn_start_idx = len(messages)
            turn_tools = []
            for msg in new_messages[turn_start_idx:]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        turn_tools.append({
                            "name": tc.get("name", "?"),
                            "args_preview": str(tc.get("args", {}))[:120],
                        })
            total_tool_calls.extend(turn_tools)

            messages = new_messages
            session.messages = messages
            recent_agent_responses.append(response_text)

            speed = "⚠️ SLOW" if elapsed > TURN_TIMEOUT_WARNING else "✅"
            print(f"\n🤖 BRANDMIND ({elapsed:.1f}s {speed}, {len(turn_tools)} tools):")
            print(f"{response_text[:500]}{'...' if len(response_text) > 500 else ''}")
            if turn_tools:
                tool_names = [t["name"] for t in turn_tools]
                print(f"   🔧 Tools: {', '.join(tool_names)}")

            conversation_history.append({"role": "assistant", "content": response_text})

            conversation_log.append({
                "turn": turn_num,
                "phase": session.current_phase,
                "scope": session.scope,
                "turns_in_phase": turns_in_current_phase,
                "user": current_user_message,
                "agent_response": response_text[:4000],
                "agent_response_length": len(response_text),
                "tool_calls": turn_tools,
                "elapsed_seconds": round(elapsed, 1),
            })

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n❌ ERROR ({elapsed:.1f}s): {e}")
            conversation_log.append({
                "turn": turn_num,
                "phase": session.current_phase,
                "user": current_user_message,
                "error": str(e)[:500],
                "elapsed_seconds": round(elapsed, 1),
            })
            response_text = ""

        # Stop conditions
        if session.current_phase == TARGET_PHASE and not target_reached:
            target_reached = True
            print(f"\n🎯 TARGET REACHED: {TARGET_PHASE}")

        if target_reached:
            extra_turns_after_target += 1
            if extra_turns_after_target > MAX_EXTRA_TURNS:
                print(f"\n⏹️  Stopping: {MAX_EXTRA_TURNS} extra turns after target")
                break

        if _detect_conversation_end(recent_agent_responses, session.current_phase):
            print(f"\n⏹️  Stopping: conversation ended naturally")
            break

        # Generate next user response
        if response_text:
            current_user_message = await get_user_response(
                user_client, response_text, conversation_history,
                turn_num, session.current_phase, turns_in_current_phase,
            )

    # ── Analysis ──
    print(f"\n{'=' * 80}")
    print("PERFORMANCE ANALYSIS")
    print(f"{'=' * 80}")

    tool_counts: dict[str, int] = {}
    for tc in total_tool_calls:
        tool_counts[tc["name"]] = tool_counts.get(tc["name"], 0) + 1

    print(f"\n📊 Tool Usage ({sum(tool_counts.values())} total):")
    for name, count in sorted(tool_counts.items(), key=lambda x: -x[1]):
        print(f"   {name}: {count}x")

    kg = tool_counts.get("search_knowledge_graph", 0)
    doc = tool_counts.get("search_document_library", 0)
    web = tool_counts.get("search_web", 0)
    research = tool_counts.get("deep_research", 0)
    print(f"\n📚 Knowledge: KG={kg}, Doc={doc}, Web={web}, Research={research}")

    print(f"\n📍 Session: phase={session.current_phase}, scope={session.scope}, brand={session.brand_name}")
    print(f"📈 report_progress: {tool_counts.get('report_progress', 0)} calls")

    total_time = sum(log.get("elapsed_seconds", 0) for log in conversation_log)
    actual_turns = len(conversation_log)
    print(f"⏱️  Total: {total_time:.0f}s ({actual_turns} turns, avg {total_time/max(actual_turns,1):.0f}s/turn)")

    phases_seen = []
    for log_entry in conversation_log:
        p = log_entry.get("phase", "?")
        if not phases_seen or phases_seen[-1] != p:
            phases_seen.append(p)
    print(f"📋 Phases: {' → '.join(phases_seen)}")

    # Phase duration
    phase_turns: dict[str, int] = {}
    for log_entry in conversation_log:
        p = log_entry.get("phase", "?")
        phase_turns[p] = phase_turns.get(p, 0) + 1
    print(f"📊 Turns per phase: {phase_turns}")

    log_data = {
        "scenario": "Chuyện Ba Bữa Signature — LLM User",
        "timestamp": datetime.now().isoformat(),
        "target_phase": TARGET_PHASE,
        "turns": conversation_log,
        "summary": {
            "total_turns": actual_turns,
            "total_time_seconds": round(total_time, 1),
            "tool_counts": tool_counts,
            "final_phase": session.current_phase,
            "final_scope": session.scope,
            "final_brand": session.brand_name,
            "phases_seen": phases_seen,
            "phase_turns": phase_turns,
        },
    }
    log_path.write_text(json.dumps(log_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n📄 Log: {log_path}")


if __name__ == "__main__":
    asyncio.run(run_test())
