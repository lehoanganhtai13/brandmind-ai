"""Phase 3 output schema matching Blueprint Section 3.5.

IdentityTransition and PreserveDiscardItem are defined here
(embedded in Phase 3 output schema) per the spec.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from core.brand_strategy.analysis.naming import NamingProcess


class TraitDescriptor(BaseModel):
    """A single brand trait with what it means and doesn't mean."""

    trait: str = ""
    means: str = ""
    does_not_mean: str = ""


class VoiceExample(BaseModel):
    """A do/don't example for brand voice."""

    do: str = ""
    dont: str = ""


class ColorPalette(BaseModel):
    """Brand color palette."""

    primary: str = ""
    secondary: str = ""
    accent: str = ""
    rationale: str = ""


class DistinctiveBrandAssets(BaseModel):
    """Distinctive brand assets per blueprint."""

    priority_assets: list[str] = Field(default_factory=list)
    asset_strategy: str = ""


class SensoryIdentity(BaseModel):
    """Sensory identity for F&B brands."""

    taste_profile: str = ""
    aroma_signature: str = ""
    ambient_experience: str = ""
    packaging_tactile: str = ""


class BrandPersonality(BaseModel):
    """Brand personality (Aaker's 5 dimensions)."""

    archetype: str = ""
    traits: list[str] = Field(default_factory=list)
    trait_descriptors: list[TraitDescriptor] = Field(default_factory=list)
    brand_character: str = ""


class BrandVoice(BaseModel):
    """Brand voice."""

    tone_spectrum: dict[str, int] = Field(default_factory=dict)
    voice_principles: list[str] = Field(default_factory=list)
    voice_examples: list[VoiceExample] = Field(default_factory=list)


class VisualIdentity(BaseModel):
    """Visual identity direction."""

    color_palette: ColorPalette = Field(default_factory=ColorPalette)
    typography_direction: str = ""
    imagery_style: str = ""
    logo_direction: str = ""
    mood_board_images: list[str] = Field(default_factory=list)


class PreserveDiscardItem(BaseModel):
    """An element in the Preserve-Discard Matrix."""

    element: str
    current_state: str = ""
    action: str = ""  # preserve, evolve, replace, remove
    rationale: str = ""
    equity_value: str = ""  # high, medium, low


class IdentityTransition(BaseModel):
    """Identity transition plan for rebrands."""

    preserve_discard_items: list[PreserveDiscardItem] = Field(default_factory=list)
    elements_preserved: list[str] = Field(default_factory=list)
    elements_evolved: list[str] = Field(default_factory=list)
    elements_replaced: list[str] = Field(default_factory=list)
    elements_removed: list[str] = Field(default_factory=list)
    visual_bridge_strategy: str = ""
    dba_continuity_plan: str = ""


class Phase3Output(BaseModel):
    """Phase 3 output matching Blueprint Section 3.5 schema."""

    brand_personality: BrandPersonality = Field(default_factory=BrandPersonality)
    brand_voice: BrandVoice = Field(default_factory=BrandVoice)
    visual_identity: VisualIdentity = Field(default_factory=VisualIdentity)
    distinctive_brand_assets: DistinctiveBrandAssets = Field(
        default_factory=DistinctiveBrandAssets
    )
    sensory_identity: SensoryIdentity | None = None
    brand_naming: NamingProcess = Field(default_factory=NamingProcess)
    identity_transition: IdentityTransition | None = None
