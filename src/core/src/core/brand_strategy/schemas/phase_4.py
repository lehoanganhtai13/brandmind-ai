"""Phase 4 output schema matching Blueprint Section 3.6."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from core.brand_strategy.analysis.messaging import (
    AIDAMapping,
    ChannelStrategy,
    ContentPillar,
    KeyMessage,
    PersuasionApplication,
    ValueProposition,
)


class MessagingHierarchy(BaseModel):
    """Messaging hierarchy per blueprint."""

    primary_message: str = ""
    supporting_messages: list[KeyMessage] = Field(default_factory=list)
    proof_points: list[str] = Field(default_factory=list)
    tagline_options: list[str] = Field(default_factory=list)


class ChannelStrategyOutput(BaseModel):
    """Channel strategy output per blueprint."""

    channels: list[ChannelStrategy] = Field(default_factory=list)
    content_pillars: list[ContentPillar] = Field(default_factory=list)


class BrandStory(BaseModel):
    """Brand storytelling per blueprint."""

    origin_story: str = ""
    customer_story_template: str = ""
    narrative_themes: list[str] = Field(default_factory=list)


class Phase4Output(BaseModel):
    """Phase 4 output matching Blueprint Section 3.6 schema."""

    value_proposition: ValueProposition = Field(default_factory=ValueProposition)
    messaging_hierarchy: MessagingHierarchy = Field(default_factory=MessagingHierarchy)
    audience_messaging: list[dict[str, Any]] = Field(default_factory=list)
    persuasion_strategy: list[PersuasionApplication] = Field(default_factory=list)
    aida_framework: AIDAMapping = Field(default_factory=AIDAMapping)
    channel_strategy: ChannelStrategyOutput = Field(
        default_factory=ChannelStrategyOutput
    )
    brand_story: BrandStory = Field(default_factory=BrandStory)
