"""Proactive loop triggers for brand strategy rework detection.

Monitors conditions during each phase and triggers loopbacks when
issues are detected that require revisiting earlier phases.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class LoopTrigger(BaseModel):
    """A condition that triggers revisiting a previous phase."""

    id: str
    detected_at: str  # Phase where detected
    target_phase: str  # Phase to revisit
    condition: str  # What to check
    action: str  # What to do when triggered
    scope_filter: list[str] | None = None


PROACTIVE_TRIGGERS = [
    LoopTrigger(
        id="stress_deliverability",
        detected_at="phase_2",
        target_phase="phase_0",
        condition="Positioning stress test fails on Deliverability",
        action=(
            "Revisit Phase 0 (product reality) or Phase 1 (re-evaluate opportunities)"
        ),
    ),
    LoopTrigger(
        id="stress_relevance",
        detected_at="phase_2",
        target_phase="phase_1",
        condition="Positioning stress test fails on Relevance",
        action="Revisit Phase 1 (deeper insight mining)",
    ),
    LoopTrigger(
        id="naming_blocked",
        detected_at="phase_3",
        target_phase="phase_2",
        condition="All promising brand names taken (domain + trademark)",
        action="Adjust positioning angle or naming strategy",
    ),
    LoopTrigger(
        id="visual_conflict",
        detected_at="phase_3",
        target_phase="phase_2",
        condition="Visual identity conflicts with positioning",
        action="Revisit Phase 2 brand essence for clarity",
    ),
    LoopTrigger(
        id="messaging_abstract",
        detected_at="phase_4",
        target_phase="phase_2",
        condition="Messaging reveals positioning is too abstract to communicate",
        action="Revisit Phase 2 for sharper positioning",
    ),
    LoopTrigger(
        id="budget_overrun",
        detected_at="phase_5",
        target_phase="phase_0",
        condition="Budget cannot support implementation plan",
        action="Revisit Phase 0 budget or simplify strategy scope",
    ),
    LoopTrigger(
        id="audit_no_equity",
        detected_at="phase_0_5",
        target_phase="phase_0",
        condition="Audit reveals no salvageable equity",
        action="Recommend upgrading scope to full_rebrand or retirement",
        scope_filter=["refresh", "repositioning", "full_rebrand"],
    ),
    LoopTrigger(
        id="backlash_risk",
        detected_at="phase_5",
        target_phase="phase_3",
        condition=(
            "Transition plan reveals high customer backlash risk for proposed changes"
        ),
        action="Scale back identity changes, consider phased approach",
        scope_filter=["refresh", "repositioning", "full_rebrand"],
    ),
]

# Maps trigger IDs to context keys that indicate the trigger has fired
_TRIGGER_CONTEXT_KEYS: dict[str, str] = {
    "stress_deliverability": "stress_test_deliverability_failed",
    "stress_relevance": "stress_test_relevance_failed",
    "naming_blocked": "naming_all_blocked",
    "visual_conflict": "visual_conflicts_with_positioning",
    "messaging_abstract": "messaging_too_abstract",
    "budget_overrun": "budget_exceeds_plan",
    "audit_no_equity": "no_salvageable_equity",
    "backlash_risk": "backlash_risk_high",
}

_PHASE_LABELS: dict[str, str] = {
    "phase_0": "Phase 0 — Business Problem Diagnosis",
    "phase_0_5": "Phase 0.5 — Brand Equity Audit",
    "phase_1": "Phase 1 — Market Intelligence",
    "phase_2": "Phase 2 — Brand Positioning",
    "phase_3": "Phase 3 — Brand Identity",
    "phase_4": "Phase 4 — Communication Framework",
    "phase_5": "Phase 5 — Strategy Plan & Deliverables",
}


class ProactiveLoopDetector:
    """Detects conditions that should trigger revisiting a previous phase.

    When a trigger fires, the agent should:
    1. EXPLAIN what failed and why
    2. PROPOSE specific changes
    3. GET user confirmation
    4. PRESERVE all existing work
    5. After rework, RE-VALIDATE the trigger condition
    """

    def check_triggers(
        self,
        current_phase: str,
        scope: str,
        context: dict[str, Any],
    ) -> list[LoopTrigger]:
        """Check if any proactive loop triggers should fire.

        Args:
            current_phase: Phase where detection occurs.
            scope: Brand scope string.
            context: Dict of context flags.

        Returns:
            List of LoopTrigger objects whose conditions are met.
        """
        fired: list[LoopTrigger] = []
        for trigger in PROACTIVE_TRIGGERS:
            if trigger.detected_at != current_phase:
                continue
            if trigger.scope_filter is not None and scope not in trigger.scope_filter:
                continue
            context_key = _TRIGGER_CONTEXT_KEYS.get(trigger.id)
            if context_key and context.get(context_key):
                fired.append(trigger)
        return fired

    def format_trigger_explanation(self, trigger: LoopTrigger) -> dict[str, str]:
        """Format a fired trigger into structured data for the agent.

        Args:
            trigger: The LoopTrigger that fired.

        Returns:
            Dict with trigger details for agent to compose user message.
        """
        target_label = _PHASE_LABELS.get(trigger.target_phase, trigger.target_phase)
        detected_label = _PHASE_LABELS.get(trigger.detected_at, trigger.detected_at)
        return {
            "trigger_id": trigger.id,
            "condition": trigger.condition,
            "recommended_action": trigger.action,
            "target_phase": target_label,
            "detected_at_phase": detected_label,
            "agent_guidance": (
                "Explain this trigger to the user in their language. "
                "Frame it positively — early adjustment prevents waste "
                "in later phases. Ask for user confirmation before "
                "looping back."
            ),
        }
