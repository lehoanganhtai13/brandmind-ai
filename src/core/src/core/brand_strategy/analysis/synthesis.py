"""Strategic synthesis models for Phase 1 research.

SWOT analysis, perceptual mapping, customer insight prioritization,
and the strategic sweet spot that bridges Research -> Strategy.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SWOTAnalysis(BaseModel):
    """SWOT analysis from Phase 1 research."""

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    threats: list[str] = Field(default_factory=list)


class PerceptualMapAxis(BaseModel):
    """An axis on the competitive perceptual map."""

    label: str  # e.g., "Price Level"
    low_label: str  # e.g., "Budget"
    high_label: str  # e.g., "Premium"


class CompetitorPosition(BaseModel):
    """A competitor's position on the perceptual map."""

    name: str
    x_score: float  # Position on x-axis (0-10)
    y_score: float  # Position on y-axis (0-10)
    notes: str = ""


class PerceptualMap(BaseModel):
    """Competitive perceptual map."""

    x_axis: PerceptualMapAxis
    y_axis: PerceptualMapAxis
    competitors: list[CompetitorPosition] = Field(default_factory=list)
    white_space: str = ""
    recommended_position: str = ""


class CustomerInsight(BaseModel):
    """A prioritized customer insight."""

    observation: str
    motivation: str
    implication: str
    strategic_value: int = Field(default=1, ge=1, le=5)
    actionability: int = Field(default=1, ge=1, le=5)
    evidence_strength: int = Field(default=1, ge=1, le=5)
    priority_score: float = 0.0


class StrategicSynthesis(BaseModel):
    """Complete strategic synthesis bridging Research -> Strategy.

    Combines SWOT, Perceptual Map, Strategic Sweet Spot,
    and Insight Prioritization into actionable strategy inputs.
    """

    swot: SWOTAnalysis = Field(default_factory=SWOTAnalysis)
    perceptual_map: PerceptualMap | None = None
    strategic_sweet_spot: str = ""
    prioritized_insights: list[CustomerInsight] = Field(default_factory=list)
    key_strategic_questions: list[str] = Field(default_factory=list)

    def prioritize_insights(self) -> None:
        """Calculate priority scores and sort insights."""
        for insight in self.prioritized_insights:
            insight.priority_score = (
                insight.strategic_value
                * insight.actionability
                * insight.evidence_strength
            ) / 125  # Normalize to 0-1
        self.prioritized_insights.sort(key=lambda i: i.priority_score, reverse=True)
