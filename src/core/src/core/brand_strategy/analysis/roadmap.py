"""Implementation roadmap and KPI models for Phase 5.

3-horizon roadmap with budget-tier modifiers,
KPI framework, and measurement plan.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RoadmapItem(BaseModel):
    """An action in the implementation roadmap."""

    action: str
    owner: str = ""
    priority: str = "must_do"  # must_do | nice_to_have
    estimated_cost: str | None = None
    timeline: str = ""


class ImplementationRoadmap(BaseModel):
    """Implementation roadmap with 3 time horizons.

    Budget-tier modifiers:
    - Bootstrap (<50M VND): DIY, social setup, Canva, reuse
    - Starter (50-200M): Pro logo, basic packaging, selective paid
    - Growth (200M-1B): Full identity, website, content, local PR
    - Enterprise (>1B): Everything + interior, photo, influencer
    """

    budget_tier: str = ""
    quick_wins: list[RoadmapItem] = Field(default_factory=list)
    medium_term: list[RoadmapItem] = Field(default_factory=list)
    long_term: list[RoadmapItem] = Field(default_factory=list)
    total_estimated_investment: str = ""
    budget_fit_assessment: str = ""

    def apply_budget_modifier(self, budget_tier: str) -> None:
        """Adjust roadmap items based on budget tier."""
        self.budget_tier = budget_tier
        paid_keywords = [
            "paid",
            "ads",
            "influencer",
            "pr agency",
            "photography",
            "professional",
        ]
        if budget_tier == "bootstrap":
            for horizon in [
                self.quick_wins,
                self.medium_term,
                self.long_term,
            ]:
                for item in horizon:
                    if any(kw in item.action.lower() for kw in paid_keywords):
                        item.priority = "nice_to_have"
        elif budget_tier == "enterprise":
            for horizon in [
                self.quick_wins,
                self.medium_term,
                self.long_term,
            ]:
                for item in horizon:
                    item.priority = "must_do"


class KPIDefinition(BaseModel):
    """A brand KPI definition."""

    category: str
    metric: str
    baseline: str | None = None
    target: str = ""
    measurement_method: str = ""
    review_frequency: str = ""


class MeasurementPlan(BaseModel):
    """Brand measurement plan."""

    kpis: list[KPIDefinition] = Field(default_factory=list)
    tracking_tools: list[str] = Field(default_factory=list)
    review_cadence: str = ""
    reporting_format: str = ""
