"""Brand-strategy discovery endpoints.

Exposes BrandMind's runtime configuration that the web client needs
before creating a session — currently just the supported main-agent
models so the model picker can render an option list without
hard-coding model identifiers on the client side.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.brand_strategy.model_profiles import (
    DEFAULT_BRAND_STRATEGY_MAIN_MODEL,
    list_supported_brand_strategy_main_models,
)
from shared.workspace.profile_settings import (
    UserProfileSettings,
    UserProfileSettingsOptions,
    get_user_profile_settings_options,
    load_user_profile_settings,
    read_user_profile_markdown,
    save_user_profile_settings,
)

router = APIRouter(prefix="/brand-strategy", tags=["brand-strategy"])


class MainModelOption(BaseModel):
    """One supported BrandMind main-agent model exposed to the client.

    ``model_id`` is the canonical key the client echoes back on
    :class:`server.schemas.session.CreateSessionRequest` to pin the
    new session to a specific profile. ``display_name`` is the human
    label the model picker renders. ``description`` is the short
    trade-off blurb shown under the name. ``is_default`` lets the
    picker pre-select the same profile the server would have used
    when no explicit choice was made.
    """

    model_id: str = Field(..., description="Canonical model profile key")
    display_name: str = Field(..., description="Label shown in the picker UI")
    description: str = Field(
        default="",
        description="Short trade-off blurb shown under the model name",
    )
    is_default: bool = Field(..., description="True for BrandMind's default profile")


class UserProfileSettingsResponse(BaseModel):
    """Current onboarding profile state exposed to Web and TUI clients.

    The settings are the structured source of truth for onboarding controls.
    ``profile_markdown`` shows the prompt-facing managed block after rendering,
    which lets clients verify what the agent will read without duplicating the
    renderer.
    """

    settings: UserProfileSettings = Field(..., description="Saved or default settings")
    options: UserProfileSettingsOptions = Field(
        ...,
        description="Supported option lists for onboarding controls",
    )
    profile_markdown: str = Field(
        ...,
        description="Current prompt-facing user profile markdown",
    )


@router.get("/models", response_model=list[MainModelOption])
async def list_main_agent_models() -> list[MainModelOption]:
    """Return supported main-agent model profiles for the picker UI."""
    return [
        MainModelOption(
            model_id=public_key,
            display_name=profile.display_name,
            description=profile.description,
            is_default=public_key == DEFAULT_BRAND_STRATEGY_MAIN_MODEL,
        )
        for public_key, profile in list_supported_brand_strategy_main_models()
    ]


@router.get(
    "/user-profile/settings",
    response_model=UserProfileSettingsResponse,
)
async def get_user_profile_settings() -> UserProfileSettingsResponse:
    """Return saved onboarding settings and option metadata for clients."""
    return UserProfileSettingsResponse(
        settings=load_user_profile_settings(),
        options=get_user_profile_settings_options(),
        profile_markdown=read_user_profile_markdown(),
    )


@router.put(
    "/user-profile/settings",
    response_model=UserProfileSettingsResponse,
)
async def put_user_profile_settings(
    settings: UserProfileSettings,
) -> UserProfileSettingsResponse:
    """Persist onboarding settings and refresh the prompt-facing profile."""
    saved = save_user_profile_settings(settings)
    return UserProfileSettingsResponse(
        settings=saved,
        options=get_user_profile_settings_options(),
        profile_markdown=read_user_profile_markdown(),
    )
