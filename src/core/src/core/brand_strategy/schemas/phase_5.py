"""Phase 5 output schema matching Blueprint Section 3.7."""

from __future__ import annotations

from pydantic import BaseModel, Field

from core.brand_strategy.analysis.roadmap import (
    ImplementationRoadmap,
    KPIDefinition,
    MeasurementPlan,
)
from core.brand_strategy.analysis.transition import (
    TransitionPlan,
)


class BrandStrategyDocument(BaseModel):
    """Generated strategy document per blueprint."""

    format: str = "pdf"
    file_path: str = ""
    sections: list[str] = Field(default_factory=list)


class BrandKeyComponents(BaseModel):
    """Brand Key 9 components per blueprint."""

    root_strength: str = ""
    competitive_environment: str = ""
    target: str = ""
    insight: str = ""
    benefits: str = ""
    values_and_personality: str = ""
    reasons_to_believe: str = ""
    discriminator: str = ""
    brand_essence: str = ""


class BrandKeySummary(BaseModel):
    """Brand Key one-pager per blueprint."""

    visual: str = ""
    components: BrandKeyComponents = Field(default_factory=BrandKeyComponents)


class Phase5Output(BaseModel):
    """Phase 5 output matching Blueprint Section 3.7 schema."""

    brand_strategy_document: BrandStrategyDocument = Field(
        default_factory=BrandStrategyDocument
    )
    brand_key_summary: BrandKeySummary = Field(default_factory=BrandKeySummary)
    kpis: list[KPIDefinition] = Field(default_factory=list)
    implementation_roadmap: ImplementationRoadmap = Field(
        default_factory=ImplementationRoadmap
    )
    measurement_plan: MeasurementPlan = Field(default_factory=MeasurementPlan)
    transition_plan: TransitionPlan | None = None
