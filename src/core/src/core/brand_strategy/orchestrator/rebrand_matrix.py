"""Rebrand Decision Matrix — 6-signal scoring for scope diagnosis.

Used in Phase 0 when the user has an existing brand. Scores 6 diagnostic
signals (0-2 each) to recommend scope: reinforce, refresh, reposition, or
full rebrand.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RebrandSignal(BaseModel):
    """A signal in the Rebrand Decision Matrix."""

    name: str
    question: str
    score: int = 0
    evidence: str = ""


class RebrandDecisionResult(BaseModel):
    """Result of the Rebrand Decision Matrix scoring."""

    signals: list[RebrandSignal] = Field(default_factory=list)
    total_score: int = 0
    max_score: int = 12  # 6 signals x 2
    recommended_scope: str = ""
    explanation: str = ""


class RebrandDecisionMatrix:
    """Diagnoses rebrand need using 6 diagnostic signals.

    Signals (each scored 0-2):
    1. Brand-Market Misalignment
    2. Competitive Erosion
    3. Audience Disconnect
    4. Internal Fragmentation
    5. Reputation Damage
    6. Strategic Pivot

    Scoring:
    0-3  -> REINFORCE (no rebrand needed)
    4-6  -> REFRESH (minor updates)
    7-9  -> REPOSITION (strategic shift)
    10-12 -> FULL REBRAND (start fresh)
    """

    SIGNALS = [
        RebrandSignal(
            name="Brand-Market Misalignment",
            question=(
                "Brand positioning no longer fits market reality? "
                "(0=still relevant, 1=somewhat outdated, 2=completely misaligned)"
            ),
        ),
        RebrandSignal(
            name="Competitive Erosion",
            question=(
                "Competitors have eroded your differentiation? "
                "(0=still unique, 1=some overlap, 2=no clear difference)"
            ),
        ),
        RebrandSignal(
            name="Audience Disconnect",
            question=(
                "Target audience has shifted or brand no longer resonates? "
                "(0=strong connection, 1=weakening, 2=disconnected)"
            ),
        ),
        RebrandSignal(
            name="Internal Fragmentation",
            question=(
                "Brand identity inconsistent across touchpoints? "
                "(0=consistent, 1=some gaps, 2=fragmented)"
            ),
        ),
        RebrandSignal(
            name="Reputation Damage",
            question=(
                "Brand has negative associations? "
                "(0=positive perception, 1=some concerns, 2=significant damage)"
            ),
        ),
        RebrandSignal(
            name="Strategic Pivot",
            question=(
                "Business model or strategy changing significantly? "
                "(0=stable, 1=evolving, 2=major pivot)"
            ),
        ),
    ]

    def score(self, signal_scores: dict[str, int]) -> RebrandDecisionResult:
        """Score the rebrand decision matrix.

        Args:
            signal_scores: Dict mapping signal names to 0-2 scores.

        Returns:
            RebrandDecisionResult with scored signals and recommendation.
        """
        scored_signals: list[RebrandSignal] = []
        for signal in self.SIGNALS:
            signal_copy = signal.model_copy()
            raw_score = signal_scores.get(signal.name, 0)
            signal_copy.score = max(0, min(2, raw_score))
            scored_signals.append(signal_copy)

        total = sum(s.score for s in scored_signals)
        recommended_scope, explanation = self.interpret_score(total)

        return RebrandDecisionResult(
            signals=scored_signals,
            total_score=total,
            recommended_scope=recommended_scope,
            explanation=explanation,
        )

    def get_diagnostic_questions(self) -> list[str]:
        """Get the 6 diagnostic questions for the agent to ask."""
        return [f"**{signal.name}**: {signal.question}" for signal in self.SIGNALS]

    def interpret_score(self, total: int) -> tuple[str, str]:
        """Map total score to scope recommendation.

        Args:
            total: Sum of all signal scores (0-12).

        Returns:
            Tuple of (scope_string, explanation_string).
        """
        if total <= 3:
            return (
                "reinforce",
                f"Score {total}/12: Brand fundamentals are sound. "
                "Focus on strengthening current positioning rather than rebranding.",
            )
        elif total <= 6:
            return (
                "refresh",
                f"Score {total}/12: Core brand is viable but "
                "expression needs updating. Keep strategic "
                "foundation, refresh visual identity and messaging.",
            )
        elif total <= 9:
            return (
                "repositioning",
                f"Score {total}/12: Significant strategic gaps "
                "detected. Brand needs repositioning — new target,"
                " new POD, or new value proposition.",
            )
        else:
            return (
                "full_rebrand",
                f"Score {total}/12: Multiple critical signals indicate comprehensive "
                "overhaul needed. Recommend starting fresh with full rebrand process.",
            )
