"""Positioning framework models for Phase 2.

POPs, PODs, product-brand alignment, stress test, and positioning
statement following Keller's CBBE + Ries & Trout.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PointOfParity(BaseModel):
    """A Point of Parity (POP)."""

    type: str  # "category" or "competitive"
    description: str
    evidence: str = ""


class PointOfDifference(BaseModel):
    """A Point of Difference (POD)."""

    description: str
    desirable: bool = False
    deliverable: bool = False
    differentiating: bool = False
    evidence: str = ""


class ProductBrandAlignment(BaseModel):
    """F&B Product-Brand Alignment check."""

    product_truth: str = ""
    menu_positioning_fit: str = ""
    pricing_positioning_fit: str = ""
    service_brand_fit: str = ""
    gap_actions: list[str] = Field(default_factory=list)


class StressTestResult(BaseModel):
    """Positioning Stress Test (5 criteria)."""

    competitive_vacancy: bool = False
    deliverability: bool = False
    relevance: bool = False
    defensibility: bool = False
    budget_feasibility: bool = False
    notes: dict[str, str] = Field(default_factory=dict)
    overall_verdict: str = ""

    @property
    def passed(self) -> bool:
        """All 5 criteria must pass."""
        return all(
            [
                self.competitive_vacancy,
                self.deliverability,
                self.relevance,
                self.defensibility,
                self.budget_feasibility,
            ]
        )

    @property
    def failed_criteria(self) -> list[str]:
        """List criteria that failed."""
        criteria = {
            "competitive_vacancy": self.competitive_vacancy,
            "deliverability": self.deliverability,
            "relevance": self.relevance,
            "defensibility": self.defensibility,
            "budget_feasibility": self.budget_feasibility,
        }
        return [k for k, v in criteria.items() if not v]


class PositioningStatement(BaseModel):
    """Complete positioning statement.

    Template: "For [target] who [need], [brand] is the [frame]
    that [POD] because [RTB]."
    """

    target_audience: str = ""
    need: str = ""
    brand_name: str = ""
    competitive_frame: str = ""
    key_pod: str = ""
    reasons_to_believe: str = ""
    full_statement: str = ""
    brand_essence: str = ""
    brand_mantra: str = ""
