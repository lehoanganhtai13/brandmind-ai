"""Brand strategy document and presentation templates.

Defines Pydantic data models for document structure (sections,
slides) and default templates for brand strategy deliverables.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentSection(BaseModel):
    """A section in the brand strategy document."""

    id: str
    title: str
    subtitle: str = ""
    content_key: str
    required: bool = True
    page_break_before: bool = True


class BrandStrategyTemplate(BaseModel):
    """Template for brand strategy documents (PDF/DOCX)."""

    brand_name: str = "Brand"
    brand_colors: list[str] = Field(
        default_factory=lambda: ["#1B365D", "#F5F0E8", "#D4A84B"]
    )
    sections: list[DocumentSection] = Field(
        default_factory=lambda: _default_document_sections()
    )


class PresentationSlideTemplate(BaseModel):
    """A slide in the brand strategy pitch deck."""

    id: str
    layout: str  # "title", "content", "two_column", "image", "table"
    title: str
    content_key: str
    required: bool = True
    notes: str = ""


class BrandStrategyDeckTemplate(BaseModel):
    """Template for brand strategy pitch deck (PPTX)."""

    brand_name: str = "Brand"
    brand_colors: list[str] = Field(
        default_factory=lambda: ["#1B365D", "#F5F0E8", "#D4A84B"]
    )
    slides: list[PresentationSlideTemplate] = Field(
        default_factory=lambda: _default_deck_slides()
    )


def _default_document_sections() -> list[DocumentSection]:
    """Create default 10-section document structure."""
    return [
        DocumentSection(
            id="cover",
            title="Brand Strategy Document",
            content_key="cover",
            page_break_before=False,
        ),
        DocumentSection(
            id="executive_summary",
            title="Executive Summary",
            content_key="executive_summary",
        ),
        DocumentSection(
            id="business_context",
            title="Business Context & Problem Statement",
            subtitle="Phase 0",
            content_key="phase_0_output",
        ),
        DocumentSection(
            id="brand_equity_audit",
            title="Brand Equity Audit",
            subtitle="Phase 0.5",
            content_key="phase_0_5_output",
            required=False,
        ),
        DocumentSection(
            id="market_intelligence",
            title="Market Intelligence & Research",
            subtitle="Phase 1",
            content_key="phase_1_output",
        ),
        DocumentSection(
            id="brand_strategy_core",
            title="Brand Strategy Core",
            subtitle="Phase 2",
            content_key="phase_2_output",
        ),
        DocumentSection(
            id="brand_identity",
            title="Brand Identity & Expression",
            subtitle="Phase 3",
            content_key="phase_3_output",
        ),
        DocumentSection(
            id="communication_framework",
            title="Brand Communication Framework",
            subtitle="Phase 4",
            content_key="phase_4_output",
        ),
        DocumentSection(
            id="implementation_roadmap",
            title="Implementation Roadmap",
            content_key="phase_5_output.roadmap",
        ),
        DocumentSection(
            id="kpi_measurement",
            title="KPI & Measurement Plan",
            content_key="phase_5_output.measurement",
        ),
        DocumentSection(
            id="appendices",
            title="Appendices",
            content_key="appendices",
            required=False,
        ),
    ]


def _default_deck_slides() -> list[PresentationSlideTemplate]:
    """Create default 12-slide pitch deck structure."""
    return [
        PresentationSlideTemplate(
            id="title",
            layout="title",
            title="Brand Strategy",
            content_key="cover",
            notes="Opening slide — brand name and strategy tagline.",
        ),
        PresentationSlideTemplate(
            id="executive_summary",
            layout="content",
            title="Executive Summary",
            content_key="executive_summary",
            notes="High-level overview of key recommendations.",
        ),
        PresentationSlideTemplate(
            id="business_context",
            layout="content",
            title="Business Context",
            content_key="phase_0_output",
            notes="Problem statement and business diagnosis.",
        ),
        PresentationSlideTemplate(
            id="market_overview",
            layout="content",
            title="Market Intelligence",
            content_key="phase_1_output",
            notes="Key market findings and competitive landscape.",
        ),
        PresentationSlideTemplate(
            id="target_audience",
            layout="two_column",
            title="Target Audience",
            content_key="phase_1_output.target_segments",
            notes="STP analysis and target segment profiles.",
        ),
        PresentationSlideTemplate(
            id="positioning",
            layout="content",
            title="Brand Positioning",
            content_key="phase_2_output",
            notes="POPs, PODs, positioning statement.",
        ),
        PresentationSlideTemplate(
            id="brand_identity",
            layout="two_column",
            title="Brand Identity",
            content_key="phase_3_output",
            notes="Personality, values, visual identity direction.",
        ),
        PresentationSlideTemplate(
            id="mood_board",
            layout="image",
            title="Visual Direction",
            content_key="images.mood_board",
            notes="Mood board showcasing brand aesthetic direction.",
            required=False,
        ),
        PresentationSlideTemplate(
            id="communication",
            layout="content",
            title="Communication Framework",
            content_key="phase_4_output",
            notes="Messaging hierarchy and channel strategy.",
        ),
        PresentationSlideTemplate(
            id="roadmap",
            layout="table",
            title="Implementation Roadmap",
            content_key="phase_5_output.roadmap",
            notes="Phased implementation timeline and milestones.",
        ),
        PresentationSlideTemplate(
            id="kpis",
            layout="table",
            title="KPIs & Measurement",
            content_key="phase_5_output.measurement",
            notes="Key performance indicators and tracking plan.",
        ),
        PresentationSlideTemplate(
            id="brand_key",
            layout="image",
            title="Brand Key",
            content_key="images.brand_key",
            notes="Brand Key one-pager visual summary.",
            required=False,
        ),
    ]
