"""Phase 2 output schema matching Blueprint Section 3.4."""

from __future__ import annotations

from pydantic import BaseModel, Field

from core.brand_strategy.analysis.positioning import (
    PointOfDifference,
    PointOfParity,
    ProductBrandAlignment,
    StressTestResult,
)


class CompetitiveFrame(BaseModel):
    """Competitive frame of reference."""

    category: str = ""
    competitive_set: list[str] = Field(default_factory=list)
    category_associations: list[str] = Field(default_factory=list)


class Positioning(BaseModel):
    """Positioning block per blueprint Section 3.4."""

    points_of_parity: list[PointOfParity] = Field(default_factory=list)
    points_of_difference: list[PointOfDifference] = Field(default_factory=list)
    positioning_statement: str = ""
    positioning_rationale: str = ""


class ValueArchitecture(BaseModel):
    """Value architecture = value ladder."""

    attributes: list[str] = Field(default_factory=list)
    functional_benefits: list[str] = Field(default_factory=list)
    emotional_benefits: list[str] = Field(default_factory=list)
    customer_outcomes: list[str] = Field(default_factory=list)
    reasons_to_believe: list[str] = Field(default_factory=list)


class BrandEssenceBlock(BaseModel):
    """Brand essence block."""

    core_idea: str = ""
    brand_promise: str = ""
    brand_mantra: str = ""


class StrategicAlignment(BaseModel):
    """Insight-to-Strategy Bridge (Blueprint Activity 2.7)."""

    problem_addressed: str = ""
    insight_leveraged: str = ""
    differentiation_logic: str = ""


class Phase2Output(BaseModel):
    """Phase 2 output matching Blueprint Section 3.4 schema."""

    competitive_frame: CompetitiveFrame = Field(default_factory=CompetitiveFrame)
    positioning: Positioning = Field(default_factory=Positioning)
    value_architecture: ValueArchitecture = Field(default_factory=ValueArchitecture)
    brand_essence: BrandEssenceBlock = Field(default_factory=BrandEssenceBlock)
    strategic_alignment: StrategicAlignment = Field(default_factory=StrategicAlignment)
    product_brand_alignment: ProductBrandAlignment = Field(
        default_factory=ProductBrandAlignment
    )
    positioning_stress_test: StressTestResult = Field(default_factory=StressTestResult)
