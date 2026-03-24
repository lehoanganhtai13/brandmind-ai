"""Phase state machine for brand strategy workflow.

Manages phase transitions, scope-based sequencing, and loopbacks.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class BrandScope(str, Enum):
    """Brand strategy engagement scope."""

    NEW_BRAND = "new_brand"
    REFRESH = "refresh"
    REPOSITIONING = "repositioning"
    FULL_REBRAND = "full_rebrand"


class Phase(str, Enum):
    """Brand strategy workflow phases."""

    PHASE_0 = "phase_0"  # Business Problem Diagnosis
    PHASE_0_5 = "phase_0_5"  # Brand Equity Audit (rebrand only)
    PHASE_1 = "phase_1"  # Market Intelligence
    PHASE_2 = "phase_2"  # Brand Strategy Core
    PHASE_3 = "phase_3"  # Brand Identity & Expression
    PHASE_4 = "phase_4"  # Communication Framework
    PHASE_5 = "phase_5"  # Brand Strategy Plan
    COMPLETED = "completed"


class PhaseTransition(BaseModel):
    """Record of a phase transition."""

    from_phase: Phase
    to_phase: Phase
    timestamp: datetime = Field(default_factory=datetime.now)
    gate_passed: bool = True
    notes: str = ""


# Phase sequences per scope
_PHASE_SEQUENCES: dict[BrandScope, list[Phase]] = {
    BrandScope.NEW_BRAND: [
        Phase.PHASE_0,
        Phase.PHASE_1,
        Phase.PHASE_2,
        Phase.PHASE_3,
        Phase.PHASE_4,
        Phase.PHASE_5,
    ],
    BrandScope.REFRESH: [
        Phase.PHASE_0,
        Phase.PHASE_0_5,
        Phase.PHASE_1,
        Phase.PHASE_3,
        Phase.PHASE_4,
        Phase.PHASE_5,
    ],
    BrandScope.REPOSITIONING: [
        Phase.PHASE_0,
        Phase.PHASE_0_5,
        Phase.PHASE_1,
        Phase.PHASE_2,
        Phase.PHASE_3,
        Phase.PHASE_4,
        Phase.PHASE_5,
    ],
    BrandScope.FULL_REBRAND: [
        Phase.PHASE_0,
        Phase.PHASE_0_5,
        Phase.PHASE_1,
        Phase.PHASE_2,
        Phase.PHASE_3,
        Phase.PHASE_4,
        Phase.PHASE_5,
    ],
}


class PhaseState(BaseModel):
    """Tracks the brand strategy workflow state.

    Manages current phase, scope classification, transition
    history, and phase-specific configuration.
    """

    current_phase: Phase = Phase.PHASE_0
    scope: BrandScope | None = None  # Determined in Phase 0
    budget_tier: str | None = None  # Determined in Phase 0
    transition_history: list[PhaseTransition] = Field(default_factory=list)
    loopback_count: int = 0
    session_id: str = ""

    def get_next_phase(self) -> Phase | None:
        """Determine the next phase based on current scope.

        Returns:
            The next Phase, Phase.COMPLETED if at end, or None if
            scope is unset or phase not found.
        """
        if self.current_phase == Phase.COMPLETED:
            return None
        sequence = self.get_phase_sequence()
        if not sequence:
            return None
        try:
            current_idx = sequence.index(self.current_phase)
        except ValueError:
            return None
        next_idx = current_idx + 1
        if next_idx >= len(sequence):
            return Phase.COMPLETED
        return sequence[next_idx]

    def get_phase_sequence(self) -> list[Phase]:
        """Get the ordered phase sequence for the current scope.

        Returns:
            Ordered list of phases, or empty list if scope is unset.
        """
        if self.scope is None:
            return []
        return _PHASE_SEQUENCES.get(self.scope, [])

    def advance(self, gate_passed: bool = True, notes: str = "") -> Phase:
        """Advance to the next phase.

        Args:
            gate_passed: Whether the quality gate was satisfied.
            notes: Optional transition notes.

        Returns:
            The new current phase.

        Raises:
            ValueError: If scope is not set or workflow is complete.
        """
        if self.scope is None:
            raise ValueError(
                "Cannot advance: scope not set yet (complete Phase 0 first)"
            )
        next_phase = self.get_next_phase()
        if next_phase is None:
            raise ValueError(
                f"Cannot advance from {self.current_phase.value}: workflow complete"
            )
        transition = PhaseTransition(
            from_phase=self.current_phase,
            to_phase=next_phase,
            gate_passed=gate_passed,
            notes=notes,
        )
        self.transition_history.append(transition)
        self.current_phase = next_phase
        return self.current_phase

    def loopback(self, target_phase: Phase, reason: str) -> Phase:
        """Loop back to a previous phase for proactive rework.

        Args:
            target_phase: The earlier phase to return to.
            reason: Explanation for the loopback.

        Returns:
            The new current phase (same as target_phase).

        Raises:
            ValueError: If target is not in sequence or not before current.
        """
        sequence = self.get_phase_sequence()
        if target_phase not in sequence:
            raise ValueError(
                f"Cannot loop back to {target_phase.value}: "
                "not in current scope sequence"
            )
        current_idx = sequence.index(self.current_phase)
        target_idx = sequence.index(target_phase)
        if target_idx >= current_idx:
            raise ValueError(
                f"Cannot loop back to {target_phase.value}: "
                f"must be before current phase {self.current_phase.value}"
            )
        transition = PhaseTransition(
            from_phase=self.current_phase,
            to_phase=target_phase,
            gate_passed=False,
            notes=f"LOOPBACK: {reason}",
        )
        self.transition_history.append(transition)
        self.current_phase = target_phase
        self.loopback_count += 1
        return self.current_phase

    def is_rebrand(self) -> bool:
        """Check if the current scope involves rebranding."""
        return self.scope in {
            BrandScope.REFRESH,
            BrandScope.REPOSITIONING,
            BrandScope.FULL_REBRAND,
        }
