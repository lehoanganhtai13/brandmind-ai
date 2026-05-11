"""Middleware that gates phase advancement on user-facing text content.

Provides :class:`ContentCheckAdvanceMiddleware`, which intercepts
``report_progress(advance=True)`` calls and asks an LLM judge to verify
that the agent's recent user-facing messages contain the deliverable
expected for the current phase.

The judge reads the last few AI messages and compares them against a
per-phase deliverable specification (see :data:`PHASE_DELIVERABLE_SPECS`).
On PASS the tool call proceeds normally. On FAIL the middleware returns
a :class:`ToolMessage` describing what content is missing so the agent
can supply it in the next response and retry the advance. If the judge
call itself fails (network, model error, malformed response) the
middleware logs a warning and allows the advance — availability is
prioritized over strict enforcement so a degraded judge does not stall
an in-flight session.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
    ToolCallRequest,
)
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.types import Command
from loguru import logger
from pydantic import BaseModel, Field

from config.system_config import SETTINGS
from core.brand_strategy.session import (
    PHASE_SEQUENCES,
    BrandStrategySession,
    get_active_session,
    get_next_phase,
)
from shared.model_clients.llm.google import (
    GoogleAIClientLLM,
    GoogleAIClientLLMConfig,
)

# ---------------------------------------------------------------------------
# Per-phase deliverable specifications
# ---------------------------------------------------------------------------
# Each entry is a natural-language specification passed to the LLM judge
# describing the content the agent's user-facing text should contain
# before advancing out of that phase. Phases not keyed here are not
# gated by content-check (advance proceeds unconditionally for them).
#
# Each specification mirrors the deliverables defined in the
# corresponding skill reference file:
#   - phase_0_5 -> brand-strategy-orchestrator/references/phase_0_5_equity_audit.md
#   - phase_1   -> market-research/SKILL.md (Strategic Synthesis + Insight
#                  Prioritization) and phase_1_research.md checklist
#   - phase_2   -> brand-positioning-identity/SKILL.md (Step 8 stress test)
#   - phase_4   -> brand-communication-planning/SKILL.md (Phase 4 Quality Gate)
#   - phase_5   -> brand-communication-planning/SKILL.md (Phase 5 KPI
#                  Framework + Implementation Roadmap) combined with
#                  deliverable_assembly.md (Brand Key 9 components)

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
    "phase_1": (
        "Market Intelligence deliverables per market-research SKILL.md. "
        "Expected explicit treatment of ALL of:\n"
        "1. Competitive landscape — 3-5 direct competitors with competitive gaps "
        "named\n"
        "2. Target audience — primary segment with jobs-to-be-done, pain points, "
        "desires\n"
        "3. Customer insights — at least 3 insight/evidence/implication triples\n"
        "4. Strategic synthesis — SWOT plus a perceptual map with TWO explicit "
        "axes and an identified white space\n"
        "5. Prioritized insights — top 3-5 ranked by strategic value × "
        "actionability × evidence strength\n"
        "Each item must contain brand-specific content, not just concept names."
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
    "phase_4": (
        "Communication framework deliverables per brand-communication-planning "
        "SKILL.md Phase 4 Quality Gate. Expected ALL of:\n"
        "1. Value proposition at 3 levels — one-liner, elevator pitch, full "
        "story (2-3 paragraphs)\n"
        "2. Messaging system — 3-5 key messages, each carrying TWO dimensions: "
        "(a) Message Type label from {functional / emotional / differentiating / "
        "credibility / community}; (b) Messaging Hierarchy structure — primary "
        "line (core promise) + 2-3 supporting points + proof points / RTBs "
        "grounded in Phase 0 facts or Phase 1 research\n"
        "3. Cialdini persuasion — at least 2 principles applied with concrete "
        "F&B-specific mechanics, not just named\n"
        "4. AIDA mapping — distinct message angle for each of "
        "Attention / Interest / Desire / Action tied to specific channels or "
        "content types\n"
        "5. Channel strategy — prioritized channel list with operational detail "
        "(posting frequency per channel, primary format per channel)\n"
        "6. Content pillars — named pillars with percentage allocation and "
        "example content concepts per pillar\n"
        "7. Brand story draft — origin / conflict / resolution narrative\n"
        "Frameworks named without brand-specific content do not satisfy the spec."
    ),
    "phase_5": (
        "Strategy plan deliverables per brand-communication-planning SKILL.md "
        "Phase 5 combined with deliverable_assembly.md Brand Key.\n"
        "Expected Brand Key — ALL 9 components with brand-specific content:\n"
        "1. Root Strengths — core competency/heritage\n"
        "2. Competitive Environment — competitors + market context\n"
        "3. Target — target audience definition\n"
        "4. Insight — core consumer insight\n"
        "5. Benefits — functional + emotional benefits\n"
        "6. Values, Beliefs & Personality — traits\n"
        "7. Reasons to Believe (RTBs) — proof points\n"
        "8. Discriminator — key point of difference\n"
        "9. Brand Essence — core essence/mantra\n"
        "Expected KPI Framework — at least 5 metrics spanning 3+ categories "
        "(awareness / perception / engagement / behavior / loyalty / revenue / "
        "distinctiveness). Each metric MUST be rendered as one self-contained "
        "line in the form:\n"
        "  '<Metric name>: method = <how observed>, current = <value or "
        '"no data — measure before launch">, target = <value> by <date>, '
        "cadence = <weekly | monthly | quarterly>'.\n"
        "All four anchors (method / current / target+date / cadence) must "
        "appear together for that metric to count. Percentage-only targets "
        "(e.g. '+25%') without an explicit current-value anchor, targets "
        "without an end-date, or metrics without a measurement method do "
        "not satisfy this spec.\n"
        "Expected Implementation Roadmap — 3-horizon plan covering quick wins "
        "(0-3 months), medium-term (3-6 months), long-term (6-12 months). "
        "Within each horizon items are prioritized (e.g. must_do vs "
        "nice_to_have, or explicit ordering) and adapted to the declared budget "
        "tier.\n"
        "Brand Key components named without content, KPIs without baselines, "
        "or roadmap without prioritization do not satisfy the spec."
    ),
}


# ---------------------------------------------------------------------------
# LLM judge verdict schema
# ---------------------------------------------------------------------------


class ContentCheckVerdict(BaseModel):
    """Structured verdict returned by the LLM content-check judge.

    Attributes:
        passes: ``True`` when the agent's recent user-facing text
            contains the deliverable required by the phase specification.
        missing: Human-readable description of the components or details
            the judge could not find. Empty when ``passes`` is ``True``.
            May be in the user's language (e.g. Vietnamese) when the
            agent's text is in that language.
        reasoning: One-sentence justification for the verdict, suitable
            for surfacing back to the agent as retry guidance.
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


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class PhaseStateReminderMiddleware(AgentMiddleware):
    """Inject the authoritative phase state near the model call."""

    @staticmethod
    def _render_reminder(session: BrandStrategySession) -> str:
        """Build the per-turn phase-state reminder."""
        scope = session.scope or "(unset)"
        completed = ", ".join(session.completed_phases) or "(none)"
        next_phase = get_next_phase(session.scope, session.current_phase)
        next_label = next_phase or "(strategy complete)"
        return (
            "## Current Phase State (authoritative)\n"
            f"- Scope: {scope}\n"
            f"- Current phase: {session.current_phase}\n"
            f"- Completed phases: {completed}\n"
            f"- Next phase after this phase passes: {next_label}\n\n"
            "Use this state as the workflow boundary for this response. "
            "Produce only the current phase's user-facing work. If the user "
            "asks for later deliverables while current phase is not `phase_5`, "
            "acknowledge the request and close or continue the current phase "
            "instead of writing future phase sections. If the user's last reply "
            "confirms the current phase output, update the workspace for the "
            "current phase and call `report_progress(advance=True)` before "
            "presenting later-phase content. Future phase sections in "
            "`brand_brief.md` create conflicting specialist context, so only "
            "write a phase section after `report_progress` has advanced there."
        )

    @staticmethod
    def _with_reminder(request: ModelRequest) -> ModelRequest:
        """Return a model request with the latest phase-state reminder."""
        session = get_active_session()
        if session is None:
            return request

        reminder = PhaseStateReminderMiddleware._render_reminder(session)
        existing_prompt = request.system_prompt or ""
        prompt = f"{existing_prompt}\n\n{reminder}" if existing_prompt else reminder
        return request.override(system_message=SystemMessage(content=prompt))

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Add phase-state context to synchronous model calls."""
        return handler(self._with_reminder(request))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """Add phase-state context to asynchronous model calls."""
        return await handler(self._with_reminder(request))


class ContentCheckAdvanceMiddleware(AgentMiddleware):
    """Middleware that gates phase advancement on user-facing text content.

    Wraps every tool call; when the call is ``report_progress`` with
    ``advance=True`` and the session's current phase has a registered
    deliverable specification in :data:`PHASE_DELIVERABLE_SPECS`, the
    middleware invokes an LLM judge to compare the agent's recent
    ``AIMessage`` text against that specification.

    Outcomes:

    * **pass** — the ``handler`` runs normally and the phase advances.
    * **fail** — a :class:`ToolMessage` is returned instead of running
      the handler; the message lists the missing components and
      instructs the agent to add them before retrying the advance.
    * **judge error** — the exception is logged and the handler is
      allowed to run (fail-open). This prioritizes session liveness
      over strict enforcement when the judge backend is unavailable.

    The judge is invoked per-advance only, so tool calls other than
    ``report_progress``, and advances from phases without a
    specification, incur no overhead.
    """

    def __init__(
        self,
        judge_model: str = "gemini-3.1-flash-lite-preview",
        thinking_level: str = "low",
        temperature: float = 1.0,
    ) -> None:
        """Configure the judge model used for content verification.

        Args:
            judge_model: Google Gemini model identifier used for judging.
                Must match an ID returned by Google's ``/v1beta/models``
                endpoint for the configured API key. Gemini 3 family IDs
                carry a ``-preview`` suffix.
            thinking_level: Reasoning budget for Gemini 3 models. One of
                ``"minimal"``, ``"low"``, ``"medium"``, ``"high"``. The
                default keeps latency and cost low because the
                verification task is a simple yes/no comparison.
            temperature: Sampling temperature for the judge. ``1.0`` is
                Google's recommended default for Gemini 3 reasoning
                models and is preferred over lower values here because
                the judge always produces structured output constrained
                by :class:`ContentCheckVerdict`.
        """
        super().__init__()
        self._judge_model = judge_model
        self._thinking_level = thinking_level
        self._temperature = temperature
        self._llm: GoogleAIClientLLM | None = None

    # ---- LLM client (lazy init) --------------------------------------------

    def _get_llm(self) -> GoogleAIClientLLM:
        """Return the judge LLM client, instantiating it on first use.

        Deferring instantiation keeps middleware construction cheap so
        sessions that never reach a gated phase do not incur the cost
        of creating a Google API client they will not use.
        """
        if self._llm is None:
            self._llm = GoogleAIClientLLM(
                config=GoogleAIClientLLMConfig(
                    model=self._judge_model,
                    api_key=SETTINGS.GEMINI_API_KEY,
                    temperature=self._temperature,
                    thinking_level=self._thinking_level,
                    max_tokens=4000,
                    response_mime_type="application/json",
                    response_schema=ContentCheckVerdict,
                )
            )
        return self._llm

    # ---- helpers ------------------------------------------------------------

    @staticmethod
    def _is_advance_call(request: ToolCallRequest) -> bool:
        """Return ``True`` when ``request`` calls ``report_progress`` with
        ``advance=True``."""
        if request.tool_call.get("name") != "report_progress":
            return False
        return request.tool_call.get("args", {}).get("advance") is True

    @staticmethod
    def _extract_recent_ai_text(messages: list[Any], limit: int = 3) -> str:
        """Return the concatenated text of the most recent AI messages.

        Walks ``messages`` in reverse and collects ``AIMessage`` content
        until ``limit`` messages have been captured. Non-text content
        parts (thinking blocks, tool-use blocks) are skipped so the
        returned string contains only what the user would have read.

        Args:
            messages: The conversation history from the current
                ``ToolCallRequest`` state.
            limit: Maximum number of AI messages to include. The most
                recent messages are prioritized; older ones are
                discarded.

        Returns:
            Concatenated user-facing text, in chronological order, with
            messages separated by ``"---"``. Empty string when no AI
            messages have textual content.
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
        """Assemble the judge prompt for a given phase and agent text.

        The prompt embeds the phase's deliverable specification and the
        agent's recent user-facing text, then instructs the judge to
        return a :class:`ContentCheckVerdict`-shaped JSON object.

        Args:
            phase: The current session phase identifier. Must be a key
                present in :data:`PHASE_DELIVERABLE_SPECS`.
            agent_text: Concatenated recent AI message text, typically
                produced by :meth:`_extract_recent_ai_text`.

        Returns:
            The full judge prompt string.
        """
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
        """Return a tool message that blocks the advance with additive-delta guidance.

        The message frames the next response as an additive delta on top
        of the agent's previous reply: continue from where the previous
        reply left off and add only the gap items as new chat content.
        Together the previous reply plus the delta complete the
        deliverable as the user reads it, so the agent does not bundle a
        full re-narration into a second user-facing pass.

        Args:
            phase: The phase the agent is attempting to advance out of.
            verdict: The judge's FAIL verdict supplying the ``missing``
                and ``reasoning`` fields rendered into the message body.
            request: The intercepted tool call whose ``tool_call_id`` is
                used to address the returned ``ToolMessage``.

        Returns:
            A :class:`ToolMessage` that the framework surfaces back to
            the agent in place of the tool's normal result.
        """
        return ToolMessage(
            content=(
                f"Cannot advance from {phase}. The judge found gaps in "
                "the user-facing chat content for this phase deliverable.\n\n"
                f"**Missing**: {verdict.missing}\n\n"
                f"**Reasoning**: {verdict.reasoning}\n\n"
                "Continue from where your previous reply left off and add "
                "only the gap items above as new chat content for the user. "
                "Your previous reply plus this additive delta together "
                "complete the deliverable as the user reads it; re-narrating "
                "parts you already covered is redundant and bundles the "
                "response unnecessarily. Once the gap items are in chat, "
                "retry `report_progress(advance=True)`."
            ),
            tool_call_id=request.tool_call["id"],
        )

    @staticmethod
    def _parse_verdict(raw_text: str) -> ContentCheckVerdict:
        """Parse the judge's raw response into a :class:`ContentCheckVerdict`.

        First attempts a strict Pydantic JSON parse. When the judge
        wraps the JSON in prose (e.g. code fences), falls back to
        extracting the substring between the first ``{`` and last
        ``}`` and parsing that.

        Args:
            raw_text: The judge's response text.

        Returns:
            The parsed verdict.

        Raises:
            ValueError: When neither the strict parse nor the
                substring extraction yields valid JSON matching the
                schema. The caller treats any raised exception as a
                judge failure and falls open.
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
        """Gate a synchronous tool call on a content-check verdict.

        See :class:`ContentCheckAdvanceMiddleware` for the full
        decision flow. This synchronous variant exists for harnesses
        that do not drive the middleware through its async path.

        Args:
            request: The intercepted tool call request.
            handler: Downstream handler that executes the tool when
                the advance is allowed.

        Returns:
            Either the handler's result (when the advance is allowed,
            unrelated, or the judge has failed open) or a
            :class:`ToolMessage` blocking the advance with retry
            guidance when the judge returns a FAIL verdict.
        """
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
        """Gate an asynchronous tool call on a content-check verdict.

        Asynchronous counterpart to :meth:`wrap_tool_call`. Uses the
        LLM client's async interface so the event loop is not blocked
        while the judge runs.

        Args:
            request: The intercepted tool call request.
            handler: Downstream async handler that executes the tool
                when the advance is allowed.

        Returns:
            Either the handler's awaited result or a blocking
            :class:`ToolMessage` (see :meth:`wrap_tool_call` for the
            decision flow).
        """
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


class DeliverableDispatchGuardMiddleware(AgentMiddleware):
    """Block final artifact dispatch until the session reaches Phase 5.

    The orchestrator may mention final files before the phase state has
    caught up. This middleware keeps heavy deliverable generation behind
    the workflow state instead of relying only on prompt guidance.
    Research, analysis, and exploratory creative dispatches are left
    untouched.
    """

    _BRAND_KEY_MARKERS = (
        "brand key",
        "one-pager",
        "one pager",
        "một trang",
    )

    @staticmethod
    def _is_task_call(request: ToolCallRequest) -> bool:
        """Return whether the tool call targets the sub-agent task tool."""
        return request.tool_call.get("name") == "task"

    @classmethod
    def _is_deliverable_dispatch(cls, request: ToolCallRequest) -> bool:
        """Return whether the task call would produce final artifacts."""
        args = request.tool_call.get("args", {})
        subagent_type = args.get("subagent_type", "")
        description = str(args.get("description", "")).lower()

        if subagent_type == "document-generator":
            return True
        if subagent_type != "creative-studio":
            return False
        return any(marker in description for marker in cls._BRAND_KEY_MARKERS)

    @staticmethod
    def _phase_5_ready() -> bool:
        """Return whether the active session is legitimately at Phase 5."""
        session = get_active_session()
        if session is None or not session.scope:
            return False

        sequence = PHASE_SEQUENCES.get(session.scope)
        if not sequence or "phase_5" not in sequence:
            return False

        phase_5_index = sequence.index("phase_5")
        required_completed = set(sequence[:phase_5_index])
        return session.current_phase == "phase_5" and required_completed.issubset(
            set(session.completed_phases)
        )

    @staticmethod
    def _rejection(request: ToolCallRequest) -> ToolMessage:
        """Return phase-gate guidance in place of the task result."""
        return ToolMessage(
            content=(
                "Cannot dispatch final deliverable sub-agents yet. "
                "The session must reach Phase 5 through `report_progress` "
                "before generating Brand Key, DOCX, PPTX, or XLSX files. "
                "Finish the current phase in user-facing chat, update "
                "`/workspace/brand_brief.md` and `/workspace/quality_gates.md`, "
                "then call `report_progress(advance=True)`. If the files "
                'already exist, use `list_artifacts(scope="current_session")` '
                "instead of dispatching generation again."
            ),
            tool_call_id=request.tool_call["id"],
        )

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Gate synchronous final-deliverable task dispatches."""
        if (
            self._is_task_call(request)
            and self._is_deliverable_dispatch(request)
            and not self._phase_5_ready()
        ):
            return self._rejection(request)
        return handler(request)

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        """Gate asynchronous final-deliverable task dispatches."""
        if (
            self._is_task_call(request)
            and self._is_deliverable_dispatch(request)
            and not self._phase_5_ready()
        ):
            return self._rejection(request)
        return await handler(request)


__all__ = [
    "ContentCheckAdvanceMiddleware",
    "ContentCheckVerdict",
    "DeliverableDispatchGuardMiddleware",
    "PHASE_DELIVERABLE_SPECS",
]
