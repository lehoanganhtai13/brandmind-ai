"""Brand Strategy session state management.

Handles saving and loading of multi-phase brand strategy sessions,
allowing users to resume work across separate conversations.

Architecture: BrandStrategySession composes a BrandBrief (Task 42)
as the single source of truth for all phase outputs.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from core.brand_strategy.orchestrator.brand_brief import (
    BrandBrief,
)

SESSIONS_DIR = Path("data/brand_strategy_sessions")

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


class BrandStrategySession(BaseModel):
    """Persistent session state for brand strategy workflow.

    Composes a BrandBrief instance as the single source of truth
    for all accumulated phase outputs.
    """

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = ""

    current_phase: str = "phase_0"
    scope: str | None = None
    budget_tier: str | None = None
    brand_name: str | None = None

    completed_phases: list[str] = Field(default_factory=list)
    brief: BrandBrief = Field(default_factory=BrandBrief)
    messages: list[Any] = Field(default_factory=list)

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


def save_session(session: BrandStrategySession) -> Path:
    """Save session to disk."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    session.updated_at = datetime.now().isoformat()
    filepath = SESSIONS_DIR / f"{session.session_id}.json"
    filepath.write_text(
        session.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return filepath


def load_session(
    session_id: str,
) -> Optional[BrandStrategySession]:
    """Load session from disk."""
    filepath = SESSIONS_DIR / f"{session_id}.json"
    if not filepath.exists():
        return None
    data = json.loads(filepath.read_text(encoding="utf-8"))
    return BrandStrategySession(**data)


def list_sessions() -> list[dict[str, Any]]:
    """List all saved sessions."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    sessions: list[dict[str, Any]] = []
    for filepath in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
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
# Active session state (module-level, set by CLI before agent creation)
# Pattern: same as ToolSearchMiddleware._registry
# ---------------------------------------------------------------------------

_active_session: BrandStrategySession | None = None


def set_active_session(session: BrandStrategySession) -> None:
    """Set the active session for report_progress tool access."""
    global _active_session
    _active_session = session


def get_active_session() -> BrandStrategySession | None:
    """Get the currently active session."""
    return _active_session
