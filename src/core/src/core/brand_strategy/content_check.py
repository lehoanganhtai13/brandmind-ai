"""ContentCheckAdvanceMiddleware — binding constraint C1 fix.

Intercepts `report_progress(advance=True)` tool calls and verifies the
agent's recent user-facing text contains the phase-specific deliverable
content (skill-derived, not rubric-derived).

Uses Gemini 3.1 Flash Lite via GoogleAIClientLLM as an LLM judge for
semantic verification — scalable to rubric/persona/model evolution,
handles paraphrase/bilingual content, interpretable error messages.

Fail-open on judge API errors: if the judge call fails, advance is
allowed (logged as warning). Availability > strictness — we prefer
not blocking real work over defending against transient API issues.

Middleware position: register at stack position 4 (after context
management, before tool_search) in agent_config.py.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, ToolCallRequest
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import Command
from loguru import logger
from pydantic import BaseModel, Field

from config.system_config import SETTINGS
from core.brand_strategy.session import get_active_session
from shared.model_clients.llm.google import (
    GoogleAIClientLLM,
    GoogleAIClientLLMConfig,
)

# =============================================================================
# Skill-derived deliverable specs (NOT rubric-derived — anti-overfit)
# =============================================================================
# Each spec describes WHAT the agent should have presented in user-facing text
# for that phase's deliverable, grounded in the phase's skill reference file.
# The LLM judge uses these as evaluation criteria — content vs spec.
#
# Sources:
# - phase_0_5: brand-strategy-orchestrator/references/phase_0_5_equity_audit.md
# - phase_2:   brand-positioning-identity/SKILL.md (Step 8 stress test)
# - phase_5:   brand-communication-planning/references/deliverable_assembly.md
# =============================================================================

PHASE_DELIVERABLE_SPECS: dict[str, str] = {
    "phase_0_5": (
        "Brand Equity Audit per phase_0_5_equity_audit.md. Expected meaningful "
        "discussion of:\n"
        "1. Brand Inventory across 3 dimensions — visual (logo/colors/typography), "
        "verbal (name/tagline/voice), experiential (service/ambiance/touchpoints)\n"
        "2. Current brand Perception — how customers actually perceive the brand\n"
        "3. Preserve-Discard Matrix — which brand assets to KEEP, EVOLVE, or DISCARD\n"
        "Require actual analysis with specifics, not just listing concept names."
    ),
    "phase_2": (
        "Positioning Stress Test per brand-positioning-identity SKILL.md Step 8. "
        "Positioning must be evaluated against 5 criteria with specific analysis:\n"
        "1. Competitive vacancy — no competitor currently owns this position\n"
        "2. Deliverability — product truth supports the claim\n"
        "3. Relevance — target audience cares about this\n"
        "4. Defensibility/Credibility — sustainable + believable\n"
        "5. Sustainability/Budget feasibility\n"
        "Each criterion addressed with specific content, not just named."
    ),
    "phase_5": (
        "Brand Key 9 components per deliverable_assembly.md. Expected ALL 9 "
        "components described with brand-specific content:\n"
        "1. Root Strength — core competency/heritage\n"
        "2. Competitive Environment — competitors + market context\n"
        "3. Target — target audience definition\n"
        "4. Insight — core consumer insight\n"
        "5. Benefits — functional + emotional benefits\n"
        "6. Values & Personality — traits\n"
        "7. Reasons to Believe (RTBs) — proof points\n"
        "8. Discriminator — key point of difference\n"
        "9. Brand Essence — core essence/mantra\n"
        "Each component must contain actual content for THIS brand, not just label."
    ),
}


# =============================================================================
# Verdict schema (structured LLM judge output)
# =============================================================================


class ContentCheckVerdict(BaseModel):
    """Structured output from LLM content-check judge.

    Fields:
        passes: True if agent's recent text contains the deliverable.
        missing: Description of missing components (bilingual agent output
            means missing can be in Vietnamese).
        reasoning: Brief one-sentence justification.
    """

    passes: bool = Field(
        ...,
        description="Whether the agent's recent text contains the deliverable content.",
    )
    missing: str = Field(
        default="",
        description="Specific components or content not sufficiently present.",
    )
    reasoning: str = Field(
        ...,
        description="Brief one-sentence justification of the verdict.",
    )


# =============================================================================
# Middleware
# =============================================================================


class ContentCheckAdvanceMiddleware(AgentMiddleware):
    """Binding constraint C1 fix: gate phase advance on user-facing text content.

    Workflow:
    1. Intercept tool calls via wrap_tool_call / awrap_tool_call.
    2. If tool is report_progress with advance=True AND current phase has a
       deliverable spec → run LLM judge check.
    3. LLM judge (Gemini 3.1 Flash Lite) evaluates last 3 AIMessages vs spec.
    4. If PASS → proceed with handler (advance happens).
    5. If FAIL → return ToolMessage with missing content + retry instruction.
    6. If judge error (API fail, parse error) → fail-open, log, allow advance.

    Scalability: new phases = new entry in PHASE_DELIVERABLE_SPECS. No code
    change. Persona/language changes: Gemini handles bilingual natively.
    """

    def __init__(
        self,
        judge_model: str = "gemini-3.1-flash-lite-preview",
        thinking_level: str = "low",
        temperature: float = 1.0,
    ) -> None:
        """Initialize middleware.

        Args:
            judge_model: Gemini model identifier. Default
                "gemini-3.1-flash-lite-preview" — fast, cheap, sufficient
                for binary verification. Note: Google's model IDs for
                Gemini 3 family require the "-preview" suffix (verified
                via Google's /v1beta/models endpoint on 2026-04-22).
                Using the bare "gemini-3.1-flash-lite" returns 404 and
                fails-open silently.
            thinking_level: Gemini 3 thinking level ("minimal", "low",
                "medium", "high"). Default "low" — verification is simple,
                deep reasoning not required.
            temperature: Sampling temperature. Default 1.0 per Google's
                recommendation for Gemini 3 reasoning models.
        """
        super().__init__()
        self._judge_model = judge_model
        self._thinking_level = thinking_level
        self._temperature = temperature
        self._llm: GoogleAIClientLLM | None = None

    # ---- LLM client (lazy init) --------------------------------------------

    def _get_llm(self) -> GoogleAIClientLLM:
        """Lazy-initialize the Google LLM client on first check."""
        if self._llm is None:
            self._llm = GoogleAIClientLLM(
                config=GoogleAIClientLLMConfig(
                    model=self._judge_model,
                    api_key=SETTINGS.GEMINI_API_KEY,
                    temperature=self._temperature,
                    thinking_level=self._thinking_level,
                    max_tokens=1000,
                    response_mime_type="application/json",
                    response_schema=ContentCheckVerdict,
                )
            )
        return self._llm

    # ---- helpers ------------------------------------------------------------

    @staticmethod
    def _is_advance_call(request: ToolCallRequest) -> bool:
        """Check if the tool call is report_progress(advance=True)."""
        if request.tool_call.get("name") != "report_progress":
            return False
        return request.tool_call.get("args", {}).get("advance") is True

    @staticmethod
    def _extract_recent_ai_text(messages: list[Any], limit: int = 3) -> str:
        """Concatenate the last N AIMessages' text content (user-facing only).

        Walks the message list backward, collecting AIMessage text content.
        Stops once `limit` AIMessages have been collected. Ignores non-text
        parts (thinking blocks, tool_use blocks).
        """
        ai_texts: list[str] = []
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                content = msg.content
                if isinstance(content, str) and content.strip():
                    ai_texts.append(content)
                elif isinstance(content, list):
                    parts = [
                        p.get("text", "")
                        for p in content
                        if isinstance(p, dict) and p.get("type") == "text"
                    ]
                    text = "\n".join(parts).strip()
                    if text:
                        ai_texts.append(text)
                if len(ai_texts) >= limit:
                    break
        return "\n\n---\n\n".join(reversed(ai_texts))

    def _build_judge_prompt(self, phase: str, agent_text: str) -> str:
        """Build the LLM judge prompt for a given phase + agent text."""
        spec = PHASE_DELIVERABLE_SPECS[phase]
        return (
            "You are a content verification judge for BrandMind AI.\n\n"
            f"TASK: Verify whether the agent presented the Phase {phase} "
            "deliverable in their recent user-facing text.\n\n"
            "DELIVERABLE SPEC (what the agent SHOULD have presented):\n"
            f"{spec}\n\n"
            "AGENT'S RECENT USER-FACING TEXT (last 3 responses):\n"
            f"---\n{agent_text}\n---\n\n"
            "EVALUATION RULES:\n"
            "1. Check CONTENT, not vocabulary. Paraphrasing OK if meaning "
            "preserved.\n"
            "2. Bilingual (Vietnamese + English) — both acceptable.\n"
            "3. PASS if agent meaningfully addressed the deliverable (partial "
            "discussion OK).\n"
            "4. FAIL if content absent, shallow (just naming concepts without "
            "discussion), or expressed in denial (e.g., 'we won't do X').\n"
            "5. Ignore tool calls/technical markers. Only evaluate natural "
            "language content.\n"
        )

    @staticmethod
    def _rejection(
        phase: str, verdict: ContentCheckVerdict, request: ToolCallRequest
    ) -> ToolMessage:
        """Build a ToolMessage rejecting the advance call with guidance."""
        return ToolMessage(
            content=(
                f"⚠️ Cannot advance from {phase}. Deliverable content not "
                f"sufficiently present in your recent responses.\n\n"
                f"**Missing**: {verdict.missing}\n\n"
                f"**Reasoning**: {verdict.reasoning}\n\n"
                f"Present the missing content in your next response (natural "
                f"language to the user, not tool calls), then retry "
                f"`report_progress(advance=True)`."
            ),
            tool_call_id=request.tool_call["id"],
        )

    @staticmethod
    def _parse_verdict(raw_text: str) -> ContentCheckVerdict:
        """Parse the LLM judge response into a ContentCheckVerdict.

        Raises:
            ValueError / pydantic ValidationError on parse failure (caller
            catches and fails open).
        """
        try:
            return ContentCheckVerdict.model_validate_json(raw_text)
        except Exception:
            # Try extracting JSON substring if model wrapped output
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            if start >= 0 and end > start:
                return ContentCheckVerdict.model_validate(
                    json.loads(raw_text[start:end])
                )
            raise

    # ---- public hooks (sync + async) ---------------------------------------

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Sync path — server runs async primarily, this is fallback."""
        if not self._is_advance_call(request):
            return handler(request)

        session = get_active_session()
        if session is None or session.current_phase not in PHASE_DELIVERABLE_SPECS:
            return handler(request)

        recent_text = self._extract_recent_ai_text(request.state.get("messages", []))
        if not recent_text:
            return handler(request)

        try:
            response = self._get_llm().complete(
                self._build_judge_prompt(session.current_phase, recent_text)
            )
            verdict = self._parse_verdict(response.text)
        except Exception as exc:
            logger.warning(
                f"ContentCheckAdvance LLM judge failed (sync): {exc}. Allowing advance."
            )
            return handler(request)

        if verdict.passes:
            return handler(request)
        return self._rejection(session.current_phase, verdict, request)

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        """Async path — primary for FastAPI + SSE BrandMind server."""
        if not self._is_advance_call(request):
            return await handler(request)

        session = get_active_session()
        if session is None or session.current_phase not in PHASE_DELIVERABLE_SPECS:
            return await handler(request)

        recent_text = self._extract_recent_ai_text(request.state.get("messages", []))
        if not recent_text:
            return await handler(request)

        try:
            response = await self._get_llm().acomplete(
                self._build_judge_prompt(session.current_phase, recent_text)
            )
            verdict = self._parse_verdict(response.text)
        except Exception as exc:
            logger.warning(
                f"ContentCheckAdvance LLM judge failed (async): {exc}. "
                "Allowing advance."
            )
            return await handler(request)

        if verdict.passes:
            return await handler(request)
        return self._rejection(session.current_phase, verdict, request)


__all__ = [
    "ContentCheckAdvanceMiddleware",
    "ContentCheckVerdict",
    "PHASE_DELIVERABLE_SPECS",
]
