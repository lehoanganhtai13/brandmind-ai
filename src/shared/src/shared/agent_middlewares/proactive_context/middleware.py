"""Inject proactive project context into BrandMind mentor sessions.

This middleware turns BrandMind's persistent memory files into just-in-time
context for the main brand-strategy agent. The system prompt already tells the
agent to personalize, use workspace notes, and avoid generic intake forms; this
middleware makes that guidance reliable by placing a compact, provenance-tagged
context packet in front of the model before it decides whether to ask or act.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelCallResult,
    ModelRequest,
    ModelResponse,
)
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from loguru import logger

import shared.workspace as workspace_mod

ContextSource = Literal[
    "user_profile",
    "current_workspace",
    "prior_project",
    "inference",
]
EvidenceLevel = Literal[
    "memory_backed",
    "workspace_backed",
    "profile_backed",
    "inferred",
    "none",
]
RecommendedAction = Literal[
    "continue_from_memory",
    "synthesize_collected_context",
    "discover_then_ask",
    "ask_needed_blockers",
    "normal_diagnosis",
]


_PLACEHOLDER_PATTERNS = (
    "[To be discovered]",
    "[Not yet started",
    "[Pending",
    "(Chưa xác định)",
    "(Đang cập nhật)",
)
_WORD_RE = re.compile(r"[a-z0-9]+")
_SECTION_RE_TEMPLATE = r"^##\s+{heading}\s*$"


@dataclass(frozen=True)
class ProactiveProjectMatch:
    """A prior BrandMind project that appears related to the current user turn."""

    session_id: str
    brand_name: str
    updated_at: str
    score: float
    workspace_excerpt: str = ""


@dataclass(frozen=True)
class ProactiveContextItem:
    """A compact context fact with source and confidence information."""

    source: ContextSource
    title: str
    content: str
    confidence: Literal["high", "medium", "low"] = "medium"
    needs_confirmation: bool = False


@dataclass(frozen=True)
class ProactiveActionContract:
    """Stateful next-action guidance for the mentor's imminent response."""

    available_context: tuple[str, ...] = field(default_factory=tuple)
    source_backed_context: tuple[str, ...] = field(default_factory=tuple)
    working_hypothesis: str = ""
    evidence_level: EvidenceLevel = "none"
    collectable_unknowns: tuple[str, ...] = field(default_factory=tuple)
    user_only_unknowns: tuple[str, ...] = field(default_factory=tuple)
    deferrable_unknowns: tuple[str, ...] = field(default_factory=tuple)
    unverified_hypotheses: tuple[str, ...] = field(default_factory=tuple)
    decision_relevant_external_unknowns: tuple[str, ...] = field(default_factory=tuple)
    verification_routes: tuple[str, ...] = field(default_factory=tuple)
    recommended_next_action: RecommendedAction = "normal_diagnosis"

    @property
    def has_content(self) -> bool:
        """Return whether this contract has useful decision guidance."""
        return bool(
            self.available_context
            or self.source_backed_context
            or self.working_hypothesis
            or self.collectable_unknowns
            or self.user_only_unknowns
            or self.deferrable_unknowns
            or self.unverified_hypotheses
            or self.decision_relevant_external_unknowns
            or self.verification_routes
            or self.recommended_next_action != "normal_diagnosis"
        )


@dataclass(frozen=True)
class ProactiveContextPacket:
    """The context packet injected into the main agent's model call."""

    initiative_mode: Literal[
        "continue_with_memory",
        "collect_then_answer",
        "discover_before_asking",
        "normal_diagnosis",
    ]
    items: tuple[ProactiveContextItem, ...] = field(default_factory=tuple)
    prior_matches: tuple[ProactiveProjectMatch, ...] = field(default_factory=tuple)
    action_contract: ProactiveActionContract = field(
        default_factory=ProactiveActionContract
    )

    @property
    def has_content(self) -> bool:
        """Return whether the packet carries useful context for this turn."""
        return bool(
            self.items
            or self.prior_matches
            or self.action_contract.has_content
            or self.initiative_mode == "discover_before_asking"
        )

    def to_prompt(self) -> str:
        """Render the packet as a compact system-context addendum."""
        if not self.has_content:
            return ""

        lines = [
            "# RUNTIME PROACTIVE CONTEXT",
            "",
            (
                "This context was assembled by the runtime before the response. "
                "Use it to reduce repeated intake and personalize the next turn. "
                "Do not mention file paths or internal source labels to the user."
            ),
            "",
            "## Decision Policy",
            f"- Initiative mode: {self.initiative_mode}.",
            (
                "- Context acquisition policy: before asking the user, separate "
                "what is already known, what can be collected or verified with "
                "available context/tools, what only the user can answer, and "
                "what can safely wait."
            ),
            (
                "- Evidence grounding policy: classify every decision-relevant "
                "claim before using it as strategy context: user-supplied fact, "
                "workspace/prior memory, KG/document-verified theory, "
                "specialist-verified market fact, or hypothesis."
            ),
            (
                "- External entity policy: named public brands, competitors, "
                "locations, branches, openings, pricing, reviews, and market "
                "relationships are external facts. If one changes the strategic "
                "route, verify it through a bounded specialist pass or clearly "
                "label it as an unverified hypothesis and ask for confirmation."
            ),
            (
                "- Public-brand verification policy: when the opening names a "
                "specific public-facing brand or venue and no prior workspace "
                "source verifies the relationship, prefer one bounded "
                "`market-research` pass for the route-changing fact before "
                "asking the user. Keep the brief narrow: existence, current "
                "branch/parent relationship, location/category, and stop after "
                "2-3 sources or no clear source. If the specialist cannot "
                "verify it, say the point remains unverified and ask the user "
                "to confirm."
            ),
            (
                "- Question policy: ask only the minimum set of user-only "
                "blockers needed to avoid choosing the wrong path. This is not "
                "a fixed one-question cap; ask one blocker when one is enough, "
                "and ask multiple only when they are truly needed now."
            ),
            (
                "- Branching rule: when one answer determines which later "
                "questions are relevant, ask that branching question first and "
                "defer the downstream intake items."
            ),
            (
                "- Phase 0 branch rule: if project scope is still ambiguous, "
                "treat scope classification as the first branch. Do not bundle "
                "audience, budget, differentiation, or operating-stage intake "
                "with that branch unless the user asked for a fast intake."
            ),
            (
                "- Metadata policy: if the user clearly names a brand or "
                "project, call `report_progress(brand_name=...)` to anchor "
                "workspace metadata. Do not infer scope or advance phase until "
                "the user confirms the branch."
            ),
            (
                "- Scope metadata policy: once the user answers the scope "
                "branch, call `report_progress(scope=...)` before continuing. "
                "This records the route; it is not a phase advance."
            ),
            (
                "- Deferral policy: after asking the branch question, do not "
                "append optional extra intake requests. Keep those items in "
                "deferrable context or workspace notes for later turns."
            ),
            (
                "- Workspace evidence policy: put first-party user facts in "
                "`S`, verified source/tool findings in `O`, and assumptions or "
                "name-based interpretations in `A` or `Ideas & Hypotheses`. "
                "Do not write hypotheses into `O — What we found`."
            ),
            (
                "- Treat prior-project context as reusable memory, not as fresh "
                "confirmation. Briefly confirm whether the user wants to "
                "continue/refine that work before locking scope or advancing "
                "the phase."
            ),
            (
                "- Personalization memory: proactively notice user preferences, "
                "working style, constraints, and repeated patterns. Save durable "
                "profile memory only with source evidence; route tentative, "
                "project-scoped, or inferred observations to working notes as "
                "memory candidates."
            ),
            (
                "- Workspace mutation policy: use `read_file` before changing "
                "workspace files and update existing files with `edit_file`. "
                "`write_file` is not available in BrandMind strategy sessions. "
                "Edit the smallest exact section you just read; do not build "
                "an `old_string` that skips intervening headings."
            ),
            (
                "- Keep the opening turn as one mentoring moment: working "
                "understanding plus the next useful question."
            ),
        ]

        if self.action_contract.has_content:
            lines.extend(
                [
                    "",
                    "## Proactive Action Contract",
                    (
                        "- Recommended next action: "
                        f"{self.action_contract.recommended_next_action}."
                    ),
                    f"- Evidence level: {self.action_contract.evidence_level}.",
                ]
            )
            if self.action_contract.available_context:
                lines.extend(
                    [
                        "- Available context to use now: "
                        + "; ".join(self.action_contract.available_context)
                        + ".",
                    ]
                )
            if self.action_contract.source_backed_context:
                lines.extend(
                    [
                        "- Source-backed context: "
                        + "; ".join(self.action_contract.source_backed_context)
                        + ".",
                    ]
                )
            if self.action_contract.working_hypothesis:
                lines.extend(
                    [
                        "- Working hypothesis: "
                        + self.action_contract.working_hypothesis,
                    ]
                )
            if self.action_contract.collectable_unknowns:
                lines.extend(
                    [
                        "- Resolve before asking when practical: "
                        + "; ".join(self.action_contract.collectable_unknowns)
                        + ".",
                    ]
                )
            if self.action_contract.user_only_unknowns:
                lines.extend(
                    [
                        "- User-only blockers: "
                        + "; ".join(self.action_contract.user_only_unknowns)
                        + ".",
                    ]
                )
            if self.action_contract.deferrable_unknowns:
                lines.extend(
                    [
                        "- Deferrable context: "
                        + "; ".join(self.action_contract.deferrable_unknowns)
                        + ".",
                    ]
                )
            if self.action_contract.unverified_hypotheses:
                lines.extend(
                    [
                        "- Unverified hypotheses: "
                        + "; ".join(self.action_contract.unverified_hypotheses)
                        + ".",
                    ]
                )
            if self.action_contract.decision_relevant_external_unknowns:
                lines.extend(
                    [
                        "- Decision-relevant external unknowns: "
                        + "; ".join(
                            self.action_contract.decision_relevant_external_unknowns
                        )
                        + ".",
                    ]
                )
            if self.action_contract.verification_routes:
                lines.extend(
                    [
                        "- Verification routes: "
                        + "; ".join(self.action_contract.verification_routes)
                        + ".",
                    ]
                )

        if self.prior_matches:
            lines.extend(
                [
                    (
                        "- Related prior projects were found. Start from that "
                        "memory: acknowledge the known direction, state the "
                        "most useful 1-2 facts, and ask a compact continuity "
                        "confirmation before treating the old direction as "
                        "current."
                    ),
                    (
                        "- Defer standard intake items such as status, budget, "
                        "target segment, or scope until the user confirms the "
                        "continuity branch, unless one of them is the only "
                        "blocking question."
                    ),
                ]
            )
        elif self.initiative_mode == "discover_before_asking":
            lines.extend(
                [
                    (
                        "- This is an early diagnosis turn without a related "
                        "prior project. Run a context-acquisition pass before "
                        "asking: inventory the user's wording, durable user "
                        "profile, current workspace context, and bounded "
                        "internal knowledge. When the user names a specific "
                        "brand or project, use available local project memory "
                        "and knowledge/search tools when that prevents a "
                        "generic reply. Avoid expensive specialist work unless "
                        "the next decision depends on it."
                    ),
                    (
                        "- If the opening names a specific public brand, "
                        "competitor, location, or branch relationship, treat "
                        "that relationship as unverified until a user or source "
                        "confirms it. A name can inspire a hypothesis, but it "
                        "does not prove market reality."
                    ),
                    (
                        "- Use your domain understanding to form a tentative "
                        "working understanding. Keep it explicitly tentative; "
                        "do not lock scope, private business facts, live "
                        "market facts, or stakeholder constraints without "
                        "user confirmation or tool evidence."
                    ),
                    (
                        "- In the user-facing reply, reflect that working "
                        "understanding naturally and ask only the user-owned "
                        "blocker(s) needed now. Do not turn the opening into "
                        "a full intake form."
                    ),
                ]
            )

        lines.append("")

        if self.items:
            lines.extend(["## Context Items"])
            for item in self.items:
                confirmation = "yes" if item.needs_confirmation else "no"
                lines.extend(
                    [
                        f"### {item.title}",
                        (
                            f"- Source: {item.source}; confidence: "
                            f"{item.confidence}; needs confirmation: "
                            f"{confirmation}."
                        ),
                        item.content.strip(),
                        "",
                    ]
                )

        if self.prior_matches:
            lines.extend(["## Related Prior Projects"])
            for match in self.prior_matches:
                lines.extend(
                    [
                        f"### {match.brand_name}",
                        (
                            f"- Session: {match.session_id}; updated: "
                            f"{match.updated_at or 'unknown'}; match score: "
                            f"{match.score:.2f}; needs confirmation: yes."
                        ),
                    ]
                )
                if match.workspace_excerpt:
                    lines.append(match.workspace_excerpt.strip())
                lines.append("")

        return "\n".join(lines).strip()


class ProactiveContextBuilder:
    """Build compact proactive context from profile, workspace, and project index.

    The builder is deterministic and read-only. It does not mutate workspace
    files and does not call external research tools. This keeps the first-turn
    mentor behavior fast, auditable, and safe from overreaching.
    """

    def __init__(
        self,
        *,
        max_prior_matches: int = 3,
        max_profile_chars: int = 1400,
        max_current_workspace_chars: int = 1600,
        max_prior_workspace_chars: int = 1400,
    ) -> None:
        """Create a proactive context builder with bounded context budgets."""
        self.max_prior_matches = max_prior_matches
        self.max_profile_chars = max_profile_chars
        self.max_current_workspace_chars = max_current_workspace_chars
        self.max_prior_workspace_chars = max_prior_workspace_chars

    def build(
        self,
        user_text: str,
        session_id: str | None = None,
        *,
        discovery_needed: bool = False,
        post_tool_context_seen: bool = False,
    ) -> ProactiveContextPacket:
        """Build a context packet for the current turn.

        Args:
            user_text: Latest user message text.
            session_id: Active BrandMind strategy session id, when available.
            discovery_needed: Whether runtime state says this is an early
                diagnosis turn where the agent should self-inventory before
                asking the user for more information.
            post_tool_context_seen: Whether the latest model call follows tool
                results, meaning the agent should synthesize collected context
                before asking generic follow-up questions.

        Returns:
            A compact packet. Empty packets are valid when no useful memory exists.
        """
        items: list[ProactiveContextItem] = []

        profile = self._read_profile()
        if profile:
            items.append(
                ProactiveContextItem(
                    source="user_profile",
                    title="User profile",
                    content=self._truncate(profile, self.max_profile_chars),
                    confidence="high",
                    needs_confirmation=False,
                )
            )

        current_workspace = self._read_current_workspace(session_id)
        if current_workspace:
            items.append(
                ProactiveContextItem(
                    source="current_workspace",
                    title="Current workspace summary",
                    content=self._truncate(
                        current_workspace,
                        self.max_current_workspace_chars,
                    ),
                    confidence="high",
                    needs_confirmation=False,
                )
            )

        matches = tuple(self._find_prior_projects(user_text, session_id))

        if matches:
            initiative_mode: Literal[
                "continue_with_memory",
                "collect_then_answer",
                "discover_before_asking",
                "normal_diagnosis",
            ] = "collect_then_answer"
        elif discovery_needed:
            initiative_mode = "discover_before_asking"
        elif items:
            initiative_mode = "normal_diagnosis"
        else:
            initiative_mode = "normal_diagnosis"

        action_contract = self._build_action_contract(
            initiative_mode=initiative_mode,
            items=tuple(items),
            matches=matches,
            post_tool_context_seen=post_tool_context_seen,
        )

        return ProactiveContextPacket(
            initiative_mode=initiative_mode,
            items=tuple(items),
            prior_matches=matches,
            action_contract=action_contract,
        )

    def _build_action_contract(
        self,
        *,
        initiative_mode: Literal[
            "continue_with_memory",
            "collect_then_answer",
            "discover_before_asking",
            "normal_diagnosis",
        ],
        items: tuple[ProactiveContextItem, ...],
        matches: tuple[ProactiveProjectMatch, ...],
        post_tool_context_seen: bool,
    ) -> ProactiveActionContract:
        """Build the stateful decision guidance carried by the prompt packet."""
        available_context = list(_available_context_labels(items, matches))
        if initiative_mode == "discover_before_asking":
            available_context.append("latest user wording")

        evidence_level = _evidence_level(items, matches, initiative_mode)

        if post_tool_context_seen:
            if initiative_mode == "discover_before_asking":
                user_only_unknowns = (
                    "scope branch: new brand, extension, refresh, or repositioning",
                )
                deferrable_unknowns = (
                    "audience, budget, differentiation, operating stage, "
                    "and challenge details",
                )
                working_hypothesis = (
                    "Tool results are now part of the context. Use them to "
                    "state a grounded working hypothesis, then ask the scope "
                    "branch first because downstream intake depends on it."
                )
            else:
                user_only_unknowns = (
                    "remaining strategic decision(s) that tool results and "
                    "memory cannot answer",
                )
                deferrable_unknowns = (
                    "standard intake details that do not change the "
                    "immediate next step",
                )
                working_hypothesis = (
                    "Tool results are now part of the context. Use them to "
                    "produce a grounded synthesis before asking for anything "
                    "that may already be answered by those results."
                )
            return ProactiveActionContract(
                available_context=tuple(available_context + ["recent tool results"]),
                source_backed_context=(
                    "recent tool results only for the facts those tools "
                    "actually returned",
                ),
                working_hypothesis=working_hypothesis,
                evidence_level=evidence_level,
                collectable_unknowns=(
                    "facts already present in recent tool results",
                    "facts present in workspace or durable profile context",
                ),
                user_only_unknowns=user_only_unknowns,
                deferrable_unknowns=deferrable_unknowns,
                unverified_hypotheses=(
                    "name-based brand relationship, premium/flagship cues, "
                    "or public-market assumptions not present in tool results",
                ),
                decision_relevant_external_unknowns=(
                    "current public brand/branch/location facts when they "
                    "change the strategy route",
                ),
                verification_routes=(
                    "dispatch one bounded `market-research` pass for live "
                    "business facts that determine scope; if the pass cannot "
                    "verify the fact, say the interpretation is tentative and "
                    "ask the user to confirm",
                ),
                recommended_next_action="synthesize_collected_context",
            )

        if matches:
            return ProactiveActionContract(
                available_context=tuple(available_context),
                source_backed_context=("related prior workspace memory",),
                working_hypothesis=(
                    "A related project appears to exist. Continue from that "
                    "memory only after confirming whether the user wants to "
                    "continue, refine, or restart the prior direction."
                ),
                evidence_level=evidence_level,
                collectable_unknowns=(
                    "prior workspace notes",
                    "durable user profile",
                ),
                user_only_unknowns=(
                    "whether this request continues, refines, or restarts "
                    "the prior work",
                ),
                deferrable_unknowns=(
                    "budget or target-segment details until continuity is clear",
                ),
                recommended_next_action="continue_from_memory",
            )

        if initiative_mode == "discover_before_asking":
            return ProactiveActionContract(
                available_context=tuple(available_context),
                source_backed_context=(
                    "latest user wording",
                    "durable profile or workspace excerpts when present",
                ),
                working_hypothesis=(
                    "This is an early strategy request. Infer only obvious "
                    "facts from the user's wording and keep private, live, or "
                    "stakeholder-specific facts open until confirmed."
                ),
                evidence_level=evidence_level,
                collectable_unknowns=(
                    "facts implied by the user's wording",
                    "durable profile and current workspace context",
                    "bounded internal knowledge or local search when the "
                    "reply would be generic",
                    "current public brand, branch, competitor, or location "
                    "facts when they would change the strategic route",
                ),
                user_only_unknowns=(
                    "scope branch when new, extension, refresh, or "
                    "repositioning is unclear",
                    "constraint that would make the next step unsafe if unknown",
                ),
                deferrable_unknowns=(
                    "target guest, differentiators, budget, operating stage, "
                    "and challenge details until the scope branch is answered",
                ),
                unverified_hypotheses=(
                    "name-based interpretation of brand tier, format, branch "
                    "relationship, or positioning cue",
                ),
                decision_relevant_external_unknowns=(
                    "whether a named public brand, branch, competitor, or "
                    "location fact is currently true",
                ),
                verification_routes=(
                    "prefer one bounded `market-research` specialist pass when "
                    "a named public brand, branch, competitor, or location fact "
                    "would determine the route; if verification is unavailable "
                    "or inconclusive, label the point as a hypothesis and ask "
                    "the user to confirm",
                ),
                recommended_next_action="discover_then_ask",
            )

        if items:
            return ProactiveActionContract(
                available_context=tuple(available_context),
                source_backed_context=tuple(available_context),
                working_hypothesis=(
                    "Some durable context is available. Use it to avoid "
                    "repeating questions already answered by profile or "
                    "workspace notes."
                ),
                evidence_level=evidence_level,
                collectable_unknowns=(
                    "facts already present in profile or workspace notes",
                ),
                user_only_unknowns=(
                    "decision-changing detail(s) not present in context",
                ),
                deferrable_unknowns=(
                    "details already answered by profile or workspace notes",
                ),
                recommended_next_action="ask_needed_blockers",
            )

        return ProactiveActionContract()

    def _read_profile(self) -> str:
        """Return the user's durable profile text when it contains real data."""
        profile_path = workspace_mod.BRANDMIND_HOME / "user" / "profile.md"
        text = _read_text(profile_path)
        if _matches_template(text, workspace_mod.USER_PROFILE_TEMPLATE):
            return ""
        if not _is_substantive(text):
            return ""
        return _heading_excerpt(text, fallback_heading="User Profile")

    def _read_current_workspace(self, session_id: str | None) -> str:
        """Return a digest of the active session workspace, when populated."""
        if not session_id:
            return ""
        workspace_dir = (
            workspace_mod.BRANDMIND_HOME / "projects" / session_id / "workspace"
        )
        return self._workspace_excerpt(workspace_dir, self.max_current_workspace_chars)

    def _find_prior_projects(
        self,
        user_text: str,
        current_session_id: str | None,
    ) -> list[ProactiveProjectMatch]:
        """Find prior projects whose brand names match the current user turn."""
        normalized_user = _normalize(user_text)
        if not normalized_user:
            return []

        index = _load_project_index(workspace_mod.BRANDMIND_HOME / "index.json")
        candidates: list[ProactiveProjectMatch] = []
        for session_id, metadata in index.items():
            if session_id == current_session_id:
                continue
            brand_name = str(metadata.get("brand_name") or "").strip()
            if not brand_name:
                continue
            score = _brand_match_score(normalized_user, brand_name)
            if score < 0.55:
                continue

            workspace_dir = (
                workspace_mod.BRANDMIND_HOME / "projects" / session_id / "workspace"
            )
            excerpt = self._workspace_excerpt(
                workspace_dir,
                self.max_prior_workspace_chars,
            )
            candidates.append(
                ProactiveProjectMatch(
                    session_id=session_id,
                    brand_name=brand_name,
                    updated_at=str(metadata.get("updated_at") or ""),
                    score=score,
                    workspace_excerpt=excerpt,
                )
            )

        candidates.sort(
            key=lambda item: (item.score, item.updated_at),
            reverse=True,
        )
        return candidates[: self.max_prior_matches]

    def _workspace_excerpt(self, workspace_dir: Path, max_chars: int) -> str:
        """Return a compact digest of workspace notes if they contain real work."""
        if not workspace_dir.is_dir():
            return ""

        parts: list[str] = []
        brief = _read_text(workspace_dir / "brand_brief.md")
        if not _matches_template(
            brief, workspace_mod.BRAND_BRIEF_TEMPLATE
        ) and _is_substantive(brief):
            parts.append(
                "Brand brief excerpt:\n"
                + _extract_useful_sections(
                    brief,
                    ("Executive Summary", "Golden Thread"),
                    max_chars=max_chars,
                )
            )

        notes = _read_text(workspace_dir / "working_notes.md")
        if not _matches_template(
            notes, workspace_mod.WORKING_NOTES_TEMPLATE
        ) and _is_substantive(notes):
            parts.append(
                "Working notes excerpt:\n"
                + _extract_useful_sections(
                    notes,
                    (
                        "User Interaction Patterns",
                        "Memory Candidates",
                        "Pending Questions",
                    ),
                    max_chars=max_chars // 2,
                )
            )

        return self._truncate("\n\n".join(part for part in parts if part), max_chars)

    @staticmethod
    def _truncate(text: str, max_chars: int) -> str:
        """Return text bounded to ``max_chars`` while preserving word boundaries."""
        return _truncate(text, max_chars)


class ProactiveTurnMiddleware(AgentMiddleware):
    """Inject proactive context into main brand-strategy model calls."""

    def __init__(self, builder: ProactiveContextBuilder | None = None) -> None:
        """Create middleware with an optional test-provided context builder."""
        super().__init__()
        self.builder = builder or ProactiveContextBuilder()

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        """Inject context before a synchronous model call."""
        return handler(self._inject_context(request))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        """Inject context before an asynchronous model call."""
        return await handler(self._inject_context(request))

    def _inject_context(self, request: ModelRequest) -> ModelRequest:
        """Return a request with a proactive context addendum when available."""
        try:
            user_text = _latest_user_text(request.messages)
            if not user_text:
                return request

            session = _active_brand_strategy_session()
            session_id = getattr(session, "session_id", None)
            packet = self.builder.build(
                user_text=user_text,
                session_id=session_id,
                discovery_needed=_needs_discovery_posture(
                    session,
                    request.messages,
                ),
                post_tool_context_seen=_has_recent_tool_results(request.messages),
            )
            prompt = packet.to_prompt()
            if not prompt:
                return request

            existing_prompt = request.system_prompt or ""
            system_message = SystemMessage(content=f"{existing_prompt}\n\n{prompt}")
            logger.info(
                "ProactiveTurnMiddleware injected context: "
                f"items={len(packet.items)} prior_matches={len(packet.prior_matches)} "
                f"mode={packet.initiative_mode} "
                f"action={packet.action_contract.recommended_next_action}"
            )
            return request.override(system_message=system_message)
        except Exception as exc:
            logger.warning(f"ProactiveTurnMiddleware skipped context injection: {exc}")
            return request


def _latest_user_text(messages: Sequence[object]) -> str:
    """Return the most recent human message text from a message list."""
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content
            return content if isinstance(content, str) else str(content)
    return ""


def _active_brand_strategy_session() -> object | None:
    """Return the active brand-strategy session without hard dependency cycles."""
    try:
        from core.brand_strategy.session import (  # type: ignore[import-not-found]
            get_active_session,
        )
    except ImportError:
        return None

    return get_active_session()


def _needs_discovery_posture(
    session: object | None,
    messages: Sequence[object],
) -> bool:
    """Return whether the next turn needs a generic self-discovery nudge."""
    if session is None:
        return not any(isinstance(message, AIMessage) for message in messages)

    current_phase = getattr(session, "current_phase", "")
    scope = getattr(session, "scope", None)
    completed_phases = getattr(session, "completed_phases", [])
    turn_index = getattr(session, "turn_index", 0)

    return (
        current_phase == "phase_0"
        and not scope
        and not completed_phases
        and isinstance(turn_index, int)
        and turn_index <= 2
    )


def _has_recent_tool_results(messages: Sequence[object]) -> bool:
    """Return whether the next model call follows tool-result context."""
    for message in reversed(messages):
        if isinstance(message, ToolMessage):
            return True
        if isinstance(message, HumanMessage):
            return False
    return False


def _available_context_labels(
    items: tuple[ProactiveContextItem, ...],
    matches: tuple[ProactiveProjectMatch, ...],
) -> tuple[str, ...]:
    """Return human-readable context labels for the runtime contract."""
    labels: list[str] = []
    if any(item.source == "user_profile" for item in items):
        labels.append("durable user profile")
    if any(item.source == "current_workspace" for item in items):
        labels.append("current workspace notes")
    if matches:
        labels.append("related prior project memory")
    return tuple(labels)


def _evidence_level(
    items: tuple[ProactiveContextItem, ...],
    matches: tuple[ProactiveProjectMatch, ...],
    initiative_mode: str,
) -> EvidenceLevel:
    """Return the strongest evidence tier available to the action contract."""
    if matches:
        return "memory_backed"
    if any(item.source == "current_workspace" for item in items):
        return "workspace_backed"
    if any(item.source == "user_profile" for item in items):
        return "profile_backed"
    if initiative_mode == "discover_before_asking":
        return "inferred"
    return "none"


def _read_text(path: Path) -> str:
    """Read a text file, returning an empty string when unavailable."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _load_project_index(index_path: Path) -> dict[str, dict[str, object]]:
    """Load the BrandMind project index, tolerating missing or malformed files."""
    try:
        raw = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    projects = raw.get("projects") if isinstance(raw, dict) else None
    return projects if isinstance(projects, dict) else {}


def _normalize(text: str) -> str:
    """Normalize Vietnamese and English text for rough brand-name matching."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    without_marks = "".join(
        char for char in decomposed if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", without_marks).strip()


def _tokens(text: str) -> set[str]:
    """Return meaningful normalized tokens for fuzzy brand matching."""
    return {
        token
        for token in _WORD_RE.findall(text)
        if len(token) > 1 and token not in {"cho", "toi", "lam", "brand", "strategy"}
    }


def _brand_match_score(normalized_user_text: str, brand_name: str) -> float:
    """Score how strongly a brand name appears to match the user message."""
    normalized_brand = _normalize(brand_name)
    if not normalized_brand:
        return 0.0
    if normalized_brand in normalized_user_text:
        return 1.0
    user_tokens = _tokens(normalized_user_text)
    brand_tokens = _tokens(normalized_brand)
    if not user_tokens or not brand_tokens:
        return 0.0
    overlap = len(user_tokens & brand_tokens) / len(brand_tokens)
    if overlap == 1.0:
        return 0.9
    return overlap


def _is_substantive(text: str) -> bool:
    """Return whether a memory file contains content beyond templates."""
    if not text.strip():
        return False
    cleaned = text
    for placeholder in _PLACEHOLDER_PATTERNS:
        cleaned = cleaned.replace(placeholder, "")
    cleaned = re.sub(r"_.*?_", "", cleaned)
    cleaned = re.sub(r"\[[^\]]+\]", "", cleaned)
    meaningful_lines = [
        line.strip()
        for line in cleaned.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    return sum(len(line) for line in meaningful_lines) >= 80


def _matches_template(text: str, template: str) -> bool:
    """Return whether a file still equals its starter template."""
    return _compact_markdown(text) == _compact_markdown(template)


def _compact_markdown(text: str) -> str:
    """Normalize markdown text for exact starter-template detection."""
    return re.sub(r"\s+", " ", text.strip())


def _heading_excerpt(text: str, fallback_heading: str) -> str:
    """Return a compact excerpt with a heading label for profile-like files."""
    return f"{fallback_heading}:\n{_truncate(text.strip(), 1400)}"


def _extract_useful_sections(
    text: str,
    headings: tuple[str, ...],
    *,
    max_chars: int,
) -> str:
    """Extract selected markdown sections, falling back to the first useful lines."""
    sections: list[str] = []
    for heading in headings:
        section = _extract_markdown_section(text, heading)
        if _is_substantive(section):
            sections.append(section.strip())
    if sections:
        return _truncate("\n\n".join(sections), max_chars)
    return _truncate(_first_substantive_lines(text), max_chars)


def _extract_markdown_section(text: str, heading: str) -> str:
    """Extract a level-two markdown section by exact heading text."""
    header_re = re.compile(
        _SECTION_RE_TEMPLATE.format(heading=re.escape(heading)),
        re.MULTILINE,
    )
    match = header_re.search(text)
    if match is None:
        return ""
    start = match.start()
    next_match = re.search(r"^##\s+", text[match.end() :], flags=re.MULTILINE)
    end = match.end() + next_match.start() if next_match else len(text)
    return text[start:end]


def _first_substantive_lines(text: str, max_lines: int = 18) -> str:
    """Return the first non-placeholder lines from a markdown file."""
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(placeholder in line for placeholder in _PLACEHOLDER_PATTERNS):
            continue
        lines.append(raw_line)
        if len(lines) >= max_lines:
            break
    return "\n".join(lines)


def _truncate(text: str, max_chars: int) -> str:
    """Truncate text to a character budget with a clear omission marker."""
    stripped = text.strip()
    if len(stripped) <= max_chars:
        return stripped
    cut = stripped[:max_chars].rsplit(" ", 1)[0].rstrip()
    return f"{cut}\n[Excerpt truncated]"
