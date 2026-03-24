"""Messaging architecture models for Phase 4.

Value proposition, messaging hierarchy, Cialdini persuasion,
AIDA mapping, channel strategy, and content pillars.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ValueProposition(BaseModel):
    """Core value proposition at 3 levels."""

    one_liner: str = ""
    elevator_pitch: str = ""
    full_story: str = ""


class KeyMessage(BaseModel):
    """A key message in the messaging hierarchy."""

    type: str  # functional, emotional, differentiating, credibility, community
    message: str = ""
    proof_points: list[str] = Field(default_factory=list)


class PersuasionApplication(BaseModel):
    """Application of a Cialdini persuasion principle."""

    principle: str
    application: str = ""
    message_example: str = ""
    f_and_b_example: str = ""


class AIDAMapping(BaseModel):
    """AIDA communication flow mapping."""

    attention: str = ""
    interest: str = ""
    desire: str = ""
    action: str = ""


class ChannelStrategy(BaseModel):
    """Channel with strategy definition."""

    channel: str
    purpose: str
    content_types: list[str] = Field(default_factory=list)
    posting_frequency: str = ""
    audience_match: str = ""


class ContentPillar(BaseModel):
    """A content pillar in the content strategy."""

    pillar: str
    percentage: int = 0
    description: str = ""
    example_topics: list[str] = Field(default_factory=list)


CIALDINI_FNB_EXAMPLES: dict[str, str] = {
    "social_proof": ("Join 500+ coffee lovers who start their day with us"),
    "authority": "Beans selected by Q-grader certified roasters",
    "scarcity": "Limited seasonal menu — available this month only",
    "liking": "Community-building, barista-as-brand-ambassador",
    "reciprocity": "Free tasting events, generous sampling",
    "commitment": "Loyalty program, 'your daily ritual' framing",
    "unity": "'Part of the neighborhood' identity",
}

DEFAULT_FNB_PILLARS = [
    ContentPillar(
        pillar="Product Showcase",
        percentage=40,
        description="Menu items, preparation, ingredients",
    ),
    ContentPillar(
        pillar="Behind the Scenes",
        percentage=20,
        description="Team, sourcing, craftsmanship",
    ),
    ContentPillar(
        pillar="Community & Lifestyle",
        percentage=20,
        description="Customer moments, local events, culture",
    ),
    ContentPillar(
        pillar="Education & Story",
        percentage=10,
        description="Origin stories, brewing methods, food pairing",
    ),
    ContentPillar(
        pillar="Promotions & News",
        percentage=10,
        description="New items, events, special offers",
    ),
]
