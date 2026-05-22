"""Brand Strategy session state management.

Handles saving and loading of multi-phase brand strategy sessions,
allowing users to resume work across separate conversations.

Architecture: BrandStrategySession composes a BrandBrief (Task 42)
as the single source of truth for all phase outputs.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Optional

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    messages_from_dict,
    messages_to_dict,
)
from pydantic import BaseModel, Field

from core.brand_strategy.orchestrator.brand_brief import (
    BrandBrief,
)
from shared.workspace import BRANDMIND_HOME, ensure_project_workspace

SESSION_STORE_RELATIVE_PATH = Path("sessions") / "brand_strategy"

# Phase sequences per scope — defines the required order of phases.
# Used by report_progress to enforce correct progression.
PHASE_SEQUENCES: dict[str, list[str]] = {
    "new_brand": ["phase_0", "phase_1", "phase_2", "phase_3", "phase_4", "phase_5"],
    "refresh": ["phase_0", "phase_0_5", "phase_1", "phase_3", "phase_4", "phase_5"],
    "repositioning": [
        "phase_0",
        "phase_0_5",
        "phase_1",
        "phase_2",
        "phase_3",
        "phase_4",
        "phase_5",
    ],
    "full_rebrand": [
        "phase_0",
        "phase_0_5",
        "phase_1",
        "phase_2",
        "phase_3",
        "phase_4",
        "phase_5",
    ],
}

_PHASE_HEADINGS: dict[str, str] = {
    "phase_0": "Phase 0",
    "phase_0_5": "Phase 0.5",
    "phase_1": "Phase 1",
    "phase_2": "Phase 2",
    "phase_3": "Phase 3",
    "phase_4": "Phase 4",
    "phase_5": "Phase 5",
}

_PHASE_DISPLAY_LABELS: dict[str, str] = {
    "phase_0": "Chẩn đoán hiện trạng",
    "phase_0_5": "Audit thương hiệu hiện có",
    "phase_1": "Phân tích thị trường",
    "phase_2": "Định vị thương hiệu",
    "phase_3": "Bộ nhận diện",
    "phase_4": "Truyền thông",
    "phase_5": "KPI & Lộ trình",
}

_FINAL_HANDOFF_MARKERS = (
    "final",
    "handoff",
    "deliverable",
    "artifact",
    "stakeholder",
    "tài liệu cuối",
    "bộ tài liệu",
    "đem bàn",
    "bàn với",
)

_FINAL_ARTIFACT_MARKERS: tuple[tuple[str, ...], ...] = (
    ("strategy file", "strategy document", "file chiến lược", "tài liệu chiến lược"),
    ("slide", "presentation", "deck", "bộ slide"),
    ("kpi", "tracker", "spreadsheet", "bảng theo dõi", "bảng kpi"),
    ("brand key", "brand summary", "tóm tắt thương hiệu", "trang tóm tắt"),
)


def get_next_phase(scope: str | None, current_phase: str) -> str | None:
    """Get the next phase in the sequence for the given scope.

    Returns None if scope is not set, current phase is not in sequence,
    or already at the last phase.
    """
    if not scope or scope not in PHASE_SEQUENCES:
        return None
    sequence = PHASE_SEQUENCES[scope]
    if current_phase not in sequence:
        return None
    idx = sequence.index(current_phase)
    if idx + 1 >= len(sequence):
        return None
    return sequence[idx + 1]


def get_phase_sequence(scope: str | None) -> list[str]:
    """Return the canonical ordered phase sequence for a brand-strategy scope.

    The web UI sidebar consumes this list so each scope renders only the
    phases its workflow actually visits — refresh skips Phase 2, repositioning
    and full_rebrand include Phase 0.5 plus all of 0 through 5.

    Args:
        scope (str | None): Brand-strategy scope identifier such as
            ``"new_brand"``, ``"refresh"``, ``"repositioning"``, or
            ``"full_rebrand"``. ``None`` or unknown scopes produce an
            empty list rather than raising.

    Returns:
        sequence (list[str]): Ordered phase keys for the scope; empty when
        the scope is unset or not in :data:`PHASE_SEQUENCES`.
    """
    if not scope or scope not in PHASE_SEQUENCES:
        return []
    return list(PHASE_SEQUENCES[scope])


def get_phase_display_label(phase: str) -> str:
    """Return the Vietnamese display label for a canonical phase key.

    The label table is the source of truth for sidebar / progress UI
    surfaces; the backend mirrors what :file:`docs/web_design.md` § 9.2
    documents so implementation cannot drift from the design contract.

    Args:
        phase (str): Phase identifier such as ``"phase_0"`` or
            ``"phase_0_5"``.

    Returns:
        label (str): Human-readable Vietnamese label; falls back to a
        title-cased version of the key when the phase is not in the
        display table.
    """
    return _PHASE_DISPLAY_LABELS.get(phase, phase.replace("_", " ").title())


def get_phase_display_labels(scope: str | None) -> dict[str, str]:
    """Return the phase-key → display-label mapping restricted to ``scope``.

    The dict shape lets the API ship one self-contained payload that the
    web UI can look up by phase key without a second round trip. Mirrors
    :func:`get_phase_sequence` so that an unset scope produces an empty
    payload — the sidebar has nothing to render until classification
    lands, so shipping the full table would just be noise on the wire.

    Args:
        scope (str | None): Brand-strategy scope identifier. ``None`` or
            unknown scopes produce an empty dict.

    Returns:
        labels (dict[str, str]): Mapping from phase key to display
        label, restricted to the phases the scope visits; empty when
        the scope is unset or not in :data:`PHASE_SEQUENCES`.
    """
    sequence = get_phase_sequence(scope)
    return {phase: get_phase_display_label(phase) for phase in sequence}


@dataclass(frozen=True)
class PhaseBriefSectionCheck:
    """Workspace coverage result for a single phase section."""

    path: Path
    phase: str
    expected_heading: str
    brief_exists: bool
    section_exists: bool

    @property
    def passes(self) -> bool:
        """Return whether the phase has a matching brand brief section."""
        return self.brief_exists and self.section_exists


def check_brand_brief_phase_section(
    session_id: str,
    phase: str,
) -> PhaseBriefSectionCheck:
    """Check whether ``brand_brief.md`` has the canonical phase heading.

    Args:
        session_id: Brand strategy session id that owns the workspace.
        phase: Phase identifier such as ``"phase_0"`` or ``"phase_0_5"``.

    Returns:
        A coverage result with the expected heading and file path.
    """
    expected_heading = _PHASE_HEADINGS.get(phase, phase.replace("_", " ").title())
    path = BRANDMIND_HOME / "projects" / session_id / "workspace" / "brand_brief.md"
    if not path.is_file():
        return PhaseBriefSectionCheck(
            path=path,
            phase=phase,
            expected_heading=expected_heading,
            brief_exists=False,
            section_exists=False,
        )

    text = path.read_text(encoding="utf-8")
    heading_re = re.compile(
        rf"^##\s+{re.escape(expected_heading)}(?=\s|:|\(|$)",
        re.MULTILINE,
    )
    return PhaseBriefSectionCheck(
        path=path,
        phase=phase,
        expected_heading=expected_heading,
        brief_exists=True,
        section_exists=heading_re.search(text) is not None,
    )


def _message_text(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(part.get("text", ""))
            for part in content
            if isinstance(part, dict) and part.get("type") in {"text", "human"}
        )
    if isinstance(content, dict):
        return str(content.get("content") or content.get("text") or "")
    return ""


def _last_user_text(session: BrandStrategySession) -> str:
    for message in reversed(session.messages):
        message_type = getattr(message, "type", "")
        class_name = message.__class__.__name__
        if message_type == "human" or class_name == "HumanMessage":
            return _message_text(message)
    return ""


def _is_final_handoff_request(text: str) -> bool:
    normalized = text.lower()
    if not any(marker in normalized for marker in _FINAL_HANDOFF_MARKERS):
        return False
    artifact_hits = sum(
        1
        for marker_group in _FINAL_ARTIFACT_MARKERS
        if any(marker in normalized for marker in marker_group)
    )
    return artifact_hits >= 2


def _pre_deliverable_phases(scope: str | None) -> list[str]:
    sequence = PHASE_SEQUENCES.get(scope or "", [])
    if "phase_5" not in sequence:
        return []
    return sequence[: sequence.index("phase_5")]


def can_sync_to_deliverable_packaging(
    session: BrandStrategySession,
    final_request_text: str | None = None,
) -> bool:
    """Return whether session state can safely catch up to Phase 5 packaging.

    This is a narrow recovery path for long mentor sessions where the
    strategic work has been written into the workspace but the formal
    phase state lagged behind. It only activates when the user asks for
    final handoff artifacts and the workspace already contains every
    pre-deliverable phase section required by the selected scope.
    """
    if session.current_phase == "phase_5" or not session.scope:
        return False
    if final_request_text is not None:
        handoff_text = final_request_text
    else:
        handoff_text = _last_user_text(session)
    if not _is_final_handoff_request(handoff_text):
        return False

    required_phases = _pre_deliverable_phases(session.scope)
    if not required_phases:
        return False
    return all(
        check_brand_brief_phase_section(session.session_id, phase).passes
        for phase in required_phases
    )


def sync_to_deliverable_packaging_if_ready(
    session: BrandStrategySession,
    final_request_text: str | None = None,
) -> str | None:
    """Synchronize a lagging session to Phase 5 when handoff is ready.

    The sync is intentionally narrow: it requires an explicit final-file
    request and verified workspace coverage for every pre-deliverable phase.
    This keeps the mentor workflow intact while preventing a stale phase
    counter from blocking artifact packaging after the strategy is already
    written.
    """
    if not can_sync_to_deliverable_packaging(session, final_request_text):
        return None

    sequence = PHASE_SEQUENCES[session.scope or ""]
    target_idx = sequence.index("phase_5")
    old = session.current_phase
    pre_deliverable = sequence[:target_idx]
    session.completed_phases = list(pre_deliverable)
    session.current_phase = "phase_5"
    session.mark_advanced_in_current_turn()

    return (
        "Session updated: "
        f"phase: {old} → phase_5, "
        "Next: Read /brand-strategy-orchestrator/references/phase_5_deliverables.md, "
        "Remaining: P5, "
        "\n\nWorkspace handoff:\n"
        "- The workspace already contains every pre-deliverable phase section for "
        "the selected scope, so the session state has been synchronized to "
        "Phase 5 packaging.\n"
        "- Read `/brand-strategy-orchestrator/references/phase_5_deliverables.md` "
        "and dispatch the current-session Brand Key image, strategy DOCX, "
        "executive PPTX, and KPI XLSX.\n"
        '- Verify with `list_artifacts(scope="current_session")` before telling '
        "the user the files are complete."
    )


def update_strategy_progress(
    session: BrandStrategySession,
    *,
    advance: bool = False,
    scope: str = "",
    brand_name: str = "",
    loop_back_to: str = "",
) -> str:
    """Update session metadata and enforce phase-transition invariants.

    Args:
        session: Active brand strategy session to update.
        advance: Whether to move to the next scope-specific phase.
        scope: Optional brand scope classification from Phase 0.
        brand_name: Optional brand name for workspace metadata.
        loop_back_to: Optional proactive loop-back target phase.

    Returns:
        Human-readable tool result for the agent.
    """
    updated: list[str] = []

    if scope and scope != session.scope:
        session.scope = scope
        updated.append(f"scope: {scope}")
        seq = PHASE_SEQUENCES.get(scope, [])
        if seq:
            seq_str = " → ".join(p.replace("phase_", "P") for p in seq)
            updated.append(f"sequence: {seq_str}")

    if brand_name and brand_name != session.brand_name:
        session.brand_name = brand_name
        updated.append(f"brand: {brand_name}")
        ensure_project_workspace(session.session_id, brand_name)

    if advance:
        if not session.scope:
            return (
                "Cannot advance: scope not set yet. "
                "Set scope first with report_progress(scope='...') "
                "before advancing."
            )

        sync_result = sync_to_deliverable_packaging_if_ready(session)
        if sync_result is not None:
            return sync_result

        if not session.can_advance_in_current_turn():
            return (
                "Cannot advance: this user turn already advanced one phase. "
                "Stop here, respond to the user with the next teaching moment, "
                "and wait for their reply before advancing again."
            )

        phase_checks = [
            check_brand_brief_phase_section(session.session_id, phase)
            for phase in [*session.completed_phases, session.current_phase]
        ]
        missing_sections = [check for check in phase_checks if not check.passes]
        if missing_sections:
            first_missing = missing_sections[0]
            if first_missing.brief_exists:
                location = f"`{first_missing.path}`"
            else:
                location = "the session workspace"
            missing_headings = ", ".join(
                f"`## {check.expected_heading}: ...`" for check in missing_sections
            )
            return (
                "Cannot advance: the brand brief is missing completed/current "
                f"phase coverage in {location}. Add or restore these markdown "
                f"sections in `/workspace/brand_brief.md`: {missing_headings}. "
                "Each section should contain a concise SOAP summary. Do not "
                "continue into the next phase, ask next-phase questions, or "
                "describe next-phase work until this retry succeeds. First make "
                "one targeted `edit_file` repair for the missing section(s), then "
                "retry `report_progress(advance=True)`. If the anchor cannot be "
                "patched in one edit, tell the user the workspace save needs "
                "repair and continue the current phase without calling "
                "`report_progress` again in this turn."
            )

        next_phase = get_next_phase(session.scope, session.current_phase)
        if next_phase is None:
            return (
                f"All phases complete. "
                f"Current: {session.current_phase}. "
                f"Strategy finalized."
            )
        old = session.current_phase
        session.advance_phase(next_phase)
        session.mark_advanced_in_current_turn()
        ref_file = {
            "phase_0_5": "references/phase_0_5_equity_audit.md",
            "phase_1": "references/phase_1_research.md",
            "phase_2": "references/phase_2_positioning.md",
            "phase_3": "references/phase_3_identity.md",
            "phase_4": "references/phase_4_communication.md",
            "phase_5": "references/phase_5_deliverables.md",
        }.get(next_phase, f"references/{next_phase}.md")

        seq = PHASE_SEQUENCES[session.scope]
        idx = seq.index(next_phase)
        remaining = seq[idx:]
        remaining_str = " → ".join(p.replace("phase_", "P") for p in remaining)

        updated.append(f"phase: {old} → {next_phase}")
        updated.append(f"Next: Read /brand-strategy-orchestrator/{ref_file}")
        updated.append(f"Remaining: {remaining_str}")

        workspace_hint = (
            "\n\nWorkspace handoff:\n"
            f"- Use `read_file('/workspace/brand_brief.md')`, then one "
            f"`edit_file` to add or update the Phase {old} SOAP summary. "
            "The file already exists in normal sessions; update it in place.\n"
            "- If `edit_file` cannot find the anchor text, continue with "
            "the next phase and mention the workspace gap briefly; do not "
            "retry multiple file edits in the same turn.\n"
            f"- Read `/brand-strategy-orchestrator/{ref_file}` for "
            f"{next_phase} guidance."
        )
        if old in ("phase_0", "phase_0_5"):
            workspace_hint += (
                "\n- Update `/user/profile.md` only if this turn revealed "
                "a new stable preference or constraint; otherwise skip it."
            )
        updated.append(workspace_hint)

    if loop_back_to:
        old = session.current_phase
        session.advance_phase(loop_back_to)
        updated.append(f"Loop back: {old} → {loop_back_to} (proactive trigger)")

    if updated:
        return "Session updated: " + ", ".join(updated)
    return "No changes needed."


class PersistedToolCall(BaseModel):
    """Tool invocation captured for a single agent turn.

    Mirrors the live SSE wire shape so the chat scroll can rebuild the
    reasoning timeline from disk after a page reload without re-running
    the model.
    """

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: str = ""


class PersistedTimelineEntry(BaseModel):
    """One chronological reasoning-trace entry for an agent turn.

    Either a thinking block (``kind == "thinking"``) or a completed tool
    call (``kind == "tool_call"``). Exactly one of the payload fields is
    populated per entry; ``thinking_done`` is implicitly true after the
    turn closes so the field is intentionally omitted here.
    """

    kind: Literal["thinking", "tool_call"]
    thinking_text: str = ""
    tool_call: PersistedToolCall | None = None


class PersistedAgentTurn(BaseModel):
    """Reasoning timeline + duration captured for one agent message.

    Persisted alongside :class:`BrandStrategySession.messages` so the
    Nth ``PersistedAgentTurn`` corresponds to the Nth ``AIMessage`` in
    chronological order. ``duration_label`` is the same short string
    the web UI renders inside the collapsed "Thought for …" summary.
    """

    timeline: list[PersistedTimelineEntry] = Field(default_factory=list)
    duration_label: str = ""


def format_turn_duration(seconds: float) -> str:
    """Format a non-negative elapsed-seconds value as the timeline label.

    Mirrors the web UI's client-side helper so a turn rendered live and
    a turn rehydrated from disk display the same "Thought for …" cap.

    Args:
        seconds (float): Wall-clock duration of the agent turn.

    Returns:
        label (str): Compact human label such as ``"<1s"``, ``"23s"``,
        or ``"1m04s"``.
    """
    if seconds < 1.0:
        return "<1s"
    total = int(seconds)
    if total < 60:
        return f"{total}s"
    minutes, secs = divmod(total, 60)
    return f"{minutes}m{secs:02d}s"


class BrandStrategySession(BaseModel):
    """Persistent session state for brand strategy workflow.

    Composes a BrandBrief instance as the single source of truth
    for all accumulated phase outputs.
    """

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = ""

    title: str = ""
    pinned: bool = False

    main_agent_model: str = ""

    current_phase: str = "phase_0"
    scope: str | None = None
    budget_tier: str | None = None
    brand_name: str | None = None

    completed_phases: list[str] = Field(default_factory=list)
    brief: BrandBrief = Field(default_factory=BrandBrief)
    messages: list[Any] = Field(default_factory=list)
    agent_traces: list[PersistedAgentTurn] = Field(default_factory=list)
    turn_index: int = 0
    last_advance_turn_index: int | None = None

    def begin_user_turn(self) -> None:
        """Mark the start of a new user turn for phase-transition guards."""
        self.turn_index += 1
        self.updated_at = datetime.now().isoformat()

    def can_advance_in_current_turn(self) -> bool:
        """Return whether no phase advance has happened in this user turn."""
        return self.last_advance_turn_index != self.turn_index

    def mark_advanced_in_current_turn(self) -> None:
        """Record that this user turn already advanced the phase state."""
        self.last_advance_turn_index = self.turn_index
        self.updated_at = datetime.now().isoformat()

    def advance_phase(self, next_phase: str) -> None:
        """Move to the next phase, recording completion."""
        self.completed_phases.append(self.current_phase)
        self.current_phase = next_phase
        self.updated_at = datetime.now().isoformat()

    def save_phase_output(self, phase: str, output: dict[str, Any]) -> None:
        """Store structured output from a completed phase."""
        self.brief.add_phase_output(phase, output)
        self.updated_at = datetime.now().isoformat()

    def sync_metadata_to_brief(self) -> None:
        """Sync session metadata into the BrandBrief."""
        self.brief.session_id = self.session_id
        self.brief.brand_name = self.brand_name or ""
        self.brief.scope = self.scope or ""
        self.brief.budget_tier = self.budget_tier or ""


def get_sessions_dir() -> Path:
    """Return the BrandMind-home scoped directory for chat session records."""
    return BRANDMIND_HOME / SESSION_STORE_RELATIVE_PATH


def get_session_file(session_id: str) -> Path:
    """Return the persistence path for a brand strategy chat session."""
    return get_sessions_dir() / f"{session_id}.json"


def save_session(session: BrandStrategySession) -> Path:
    """Save session to disk.

    Uses LangChain's messages_to_dict for proper serialization of
    message objects (HumanMessage, AIMessage with tool_calls, ToolMessage).
    """
    sessions_dir = get_sessions_dir()
    sessions_dir.mkdir(parents=True, exist_ok=True)
    session.updated_at = datetime.now().isoformat()
    filepath = get_session_file(session.session_id)

    data = session.model_dump()
    data["messages"] = messages_to_dict(session.messages) if session.messages else []

    filepath.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return filepath


def _legacy_message_from_dict(message: dict[str, Any]) -> Any:
    """Rebuild messages saved before LangChain's ``messages_to_dict`` shape."""
    message_type = message.get("type")
    kwargs = {
        "content": message.get("content", ""),
        "additional_kwargs": message.get("additional_kwargs") or {},
        "response_metadata": message.get("response_metadata") or {},
        "name": message.get("name"),
        "id": message.get("id"),
    }
    if message_type == "human":
        return HumanMessage(**kwargs)
    if message_type == "ai":
        return AIMessage(**kwargs)
    if message_type == "system":
        return SystemMessage(**kwargs)
    if message_type == "tool":
        return ToolMessage(
            **kwargs,
            tool_call_id=str(message.get("tool_call_id") or ""),
        )
    return message


def _restore_messages(raw_messages: list[Any]) -> list[Any]:
    """Restore current and legacy persisted LangChain message records."""
    if not raw_messages:
        return []
    first = raw_messages[0]
    if isinstance(first, dict) and "data" not in first:
        return [
            _legacy_message_from_dict(message)
            for message in raw_messages
            if isinstance(message, dict)
        ]
    return messages_from_dict(raw_messages)


def load_session(
    session_id: str,
) -> Optional[BrandStrategySession]:
    """Load session from disk.

    Converts serialized message dicts back to LangChain message objects
    via messages_from_dict.
    """
    filepath = get_session_file(session_id)
    if not filepath.exists():
        return None
    data = json.loads(filepath.read_text(encoding="utf-8"))

    raw_messages = data.pop("messages", [])
    session = BrandStrategySession(**data)
    session.messages = _restore_messages(raw_messages)

    return session


def list_sessions() -> list[dict[str, Any]]:
    """List all saved sessions."""
    sessions_dir = get_sessions_dir()
    sessions_dir.mkdir(parents=True, exist_ok=True)
    sessions: list[dict[str, Any]] = []
    for filepath in sorted(sessions_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            sessions.append(
                {
                    "session_id": data.get("session_id"),
                    "brand_name": data.get("brand_name", "Unnamed"),
                    "phase": data.get("current_phase", "phase_0"),
                    "scope": data.get("scope", "Unknown"),
                    "updated_at": data.get("updated_at", ""),
                }
            )
        except Exception:
            continue
    return sessions


# ---------------------------------------------------------------------------
# Active session state (module-level, set before agent creation/invocation)
# ---------------------------------------------------------------------------

_active_session: BrandStrategySession | None = None


def set_active_session(session: BrandStrategySession | None) -> None:
    """Set or clear the active session for report_progress tool access."""
    global _active_session
    _active_session = session


def get_active_session() -> BrandStrategySession | None:
    """Get the currently active session."""
    return _active_session
