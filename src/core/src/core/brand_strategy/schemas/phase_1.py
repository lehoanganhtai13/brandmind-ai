"""Phase 1 output schema matching Blueprint Section 3.3.

Field names match blueprint YAML keys exactly for consistency.
Uses typed models instead of bare dicts for Pydantic validation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from core.brand_strategy.analysis.synthesis import (
    StrategicSynthesis,
)


class CompetitorProfile(BaseModel):
    """Individual competitor profile."""

    name: str
    location: str = ""
    category: str = ""
    rating: float | None = None
    review_count: int | None = None
    price_range: str = ""
    positioning: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    brand_perception: str = ""
    social_presence: str = ""
    key_differentiator: str = ""


class CompetitiveLandscape(BaseModel):
    """Competitive landscape per blueprint Section 3.3."""

    direct_competitors: list[CompetitorProfile] = Field(default_factory=list)
    indirect_competitors: list[CompetitorProfile] = Field(default_factory=list)
    competitive_gaps: list[str] = Field(default_factory=list)


class AudienceSegment(BaseModel):
    """Target audience segment."""

    name: str
    demographics: str = ""
    psychographics: str = ""
    behaviors: str = ""
    jobs_to_be_done: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    desires: list[str] = Field(default_factory=list)
    size_estimate: str = ""


class TargetAudience(BaseModel):
    """Target audience with primary/secondary structure."""

    primary_segment: AudienceSegment | None = None
    secondary_segment: AudienceSegment | None = None


class MarketOverview(BaseModel):
    """Market overview per blueprint Section 3.3."""

    industry_trends: list[str] = Field(default_factory=list)
    category_dynamics: str = ""
    market_size_estimate: str = ""
    growth_direction: str = ""


class Phase1CustomerInsight(BaseModel):
    """Customer insight per blueprint schema."""

    insight: str = ""
    evidence: str = ""
    implication: str = ""


class Opportunities(BaseModel):
    """Market opportunities per blueprint schema."""

    market_gaps: list[str] = Field(default_factory=list)
    unmet_needs: list[str] = Field(default_factory=list)
    trend_opportunities: list[str] = Field(default_factory=list)


class CurrentBrandPosition(BaseModel):
    """Current brand position (rebrand only)."""

    actual_perception: str = ""
    position_vs_competitors: str = ""
    perception_gaps: list[str] = Field(default_factory=list)


class Phase1Output(BaseModel):
    """Complete Phase 1 output matching Blueprint Section 3.3."""

    market_overview: MarketOverview = Field(default_factory=MarketOverview)
    competitive_landscape: CompetitiveLandscape = Field(
        default_factory=CompetitiveLandscape
    )
    target_audience: TargetAudience = Field(default_factory=TargetAudience)
    customer_insights: list[Phase1CustomerInsight] = Field(default_factory=list)
    opportunities: Opportunities = Field(default_factory=Opportunities)
    strategic_synthesis: StrategicSynthesis = Field(default_factory=StrategicSynthesis)
    current_brand_position: CurrentBrandPosition | None = None
