"""Tests for the BrandMind web sub-project's HTTP/SSE client + models.

Keeps the web sub-project's wire contract pinned against the backend
schemas mirrored from ``src/server/schemas`` and the agent event
taxonomy mirrored from ``src/shared/.../callback_types.py``. The
Reflex state class is exercised end-to-end in Phase 5's acceptance
ISO; this file focuses on the deterministic seams.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# The web sub-project is not a packaged module; tests get it on sys.path
# so they can import the client surface without installing it.
_WEB_ROOT = Path(__file__).resolve().parents[2] / "web"
if str(_WEB_ROOT) not in sys.path:
    sys.path.insert(0, str(_WEB_ROOT))

httpx = pytest.importorskip("httpx")
pytest.importorskip("httpx_sse")

from brandmind_web import api_client  # noqa: E402
from brandmind_web.models import (  # noqa: E402
    BrandStrategyMetadata,
    ChatMessage,
    PhaseAdvancePayload,
    SessionInfo,
    StreamDonePayload,
    StreamingTokenPayload,
    ToolCallInfo,
    ToolCallPayload,
    ToolResultPayload,
    UserProfileOption,
    UserProfileSettings,
    UserProfileSettingsOptions,
    UserProfileSettingsPayload,
)


class TestModels:
    """Pin the client-side Pydantic mirror of the backend schemas."""

    def test_session_info_defaults_match_unset_scope_state(self):
        info = SessionInfo(session_id="abc", mode="brand-strategy")
        assert info.metadata.current_phase == "phase_0"
        assert info.metadata.phase_sequence == []
        assert info.metadata.phase_display_labels == {}

    def test_brand_strategy_metadata_roundtrips_full_payload(self):
        payload = {
            "current_phase": "phase_4",
            "scope": "repositioning",
            "brand_name": "Quán Phở Hài",
            "completed_phases": [
                "phase_0",
                "phase_0_5",
                "phase_1",
                "phase_2",
                "phase_3",
            ],
            "phase_sequence": [
                "phase_0",
                "phase_0_5",
                "phase_1",
                "phase_2",
                "phase_3",
                "phase_4",
                "phase_5",
            ],
            "phase_display_labels": {
                "phase_0": "Chẩn đoán hiện trạng",
                "phase_0_5": "Audit thương hiệu hiện có",
                "phase_4": "Truyền thông",
            },
        }
        metadata = BrandStrategyMetadata.model_validate(payload)
        assert metadata.current_phase == "phase_4"
        assert metadata.scope == "repositioning"
        assert "phase_2" in metadata.phase_sequence
        assert metadata.phase_display_labels["phase_0_5"] == "Audit thương hiệu hiện có"

    def test_chat_message_user_role(self):
        msg = ChatMessage(role="user", content="Em chào Mentor")
        assert msg.role == "user"
        assert msg.is_streaming is False
        assert msg.timeline == []

    def test_phase_advance_payload_required_fields(self):
        payload = PhaseAdvancePayload(
            from_phase="phase_2",
            to_phase="phase_3",
            completed_phases=["phase_0", "phase_1", "phase_2"],
            scope="new_brand",
        )
        assert payload.scope == "new_brand"
        assert payload.completed_phases[-1] == "phase_2"

    def test_streaming_token_payload_done_flag_defaults_false(self):
        payload = StreamingTokenPayload(token="Hello")
        assert payload.done is False

    def test_tool_call_payload_arguments_default_dict(self):
        call = ToolCallPayload(tool_name="generate_brand_key")
        assert call.arguments == {}

    def test_tool_result_payload_carries_result_text(self):
        result = ToolResultPayload(
            tool_name="generate_brand_key",
            result="Saved to brandmind-output/...png",
        )
        assert result.result.startswith("Saved")

    def test_stream_done_payload_aggregates_metadata_and_tools(self):
        payload = StreamDonePayload(
            response="ok",
            metadata=BrandStrategyMetadata(
                current_phase="phase_5",
                scope="new_brand",
                phase_sequence=[
                    "phase_0",
                    "phase_1",
                    "phase_2",
                    "phase_3",
                    "phase_4",
                    "phase_5",
                ],
            ),
            tool_calls=[
                ToolCallInfo(tool_name="generate_document", result="saved"),
            ],
        )
        assert payload.metadata.current_phase == "phase_5"
        assert payload.tool_calls[0].tool_name == "generate_document"


class TestExtractFinalMetadata:
    """``extract_final_metadata`` should accept the wire dict and return typed payload."""

    def test_accepts_raw_dict(self):
        raw = {
            "response": "final answer",
            "metadata": {
                "current_phase": "phase_5",
                "scope": "new_brand",
                "phase_sequence": [
                    "phase_0",
                    "phase_1",
                    "phase_2",
                    "phase_3",
                    "phase_4",
                    "phase_5",
                ],
            },
            "tool_calls": [
                {"tool_name": "generate_document", "arguments": {}, "result": "ok"},
            ],
        }
        payload = api_client.extract_final_metadata(raw)
        assert payload.metadata.scope == "new_brand"
        assert payload.tool_calls[0].result == "ok"


class TestHealthCheck:
    """Pin the health-check probe behaviour against transient failures."""

    @pytest.mark.asyncio
    async def test_returns_true_on_2xx(self, monkeypatch):
        """Any 2xx response should read as connected."""

        class _MockResponse:
            is_success = True

        class _MockClient:
            def __init__(self, *args, **kwargs) -> None:
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args) -> None:
                return None

            async def get(self, *_args, **_kwargs):
                return _MockResponse()

        monkeypatch.setattr(api_client.httpx, "AsyncClient", _MockClient)
        assert await api_client.health_check("http://localhost:8000") is True

    @pytest.mark.asyncio
    async def test_returns_false_on_http_error(self, monkeypatch):
        """Network or timeout errors should read as disconnected without raising."""

        class _MockClient:
            def __init__(self, *args, **kwargs) -> None:
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args) -> None:
                return None

            async def get(self, *_args, **_kwargs):
                raise httpx.ConnectError("refused")

        monkeypatch.setattr(api_client.httpx, "AsyncClient", _MockClient)
        assert await api_client.health_check("http://localhost:8000") is False


class TestCreateBrandStrategySession:
    """Pin the request shape and response parsing for session creation."""

    @pytest.mark.asyncio
    async def test_posts_brand_strategy_mode_and_returns_session(self, monkeypatch):
        captured: dict = {}

        class _MockResponse:
            def __init__(self):
                self.status_code = 200

            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict:
                return {
                    "session_id": "sess-1",
                    "mode": "brand-strategy",
                    "message_count": 0,
                    "metadata": {
                        "current_phase": "phase_0",
                        "scope": None,
                        "brand_name": None,
                        "completed_phases": [],
                        "phase_sequence": [],
                        "phase_display_labels": {},
                    },
                }

        class _MockClient:
            def __init__(self, *args, **kwargs) -> None:
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args) -> None:
                return None

            async def post(self, url, json):
                captured["url"] = url
                captured["json"] = json
                return _MockResponse()

        monkeypatch.setattr(api_client.httpx, "AsyncClient", _MockClient)
        info = await api_client.create_brand_strategy_session("http://localhost:8000")

        assert captured["url"].endswith("/api/v1/sessions")
        assert captured["json"] == {"mode": "brand-strategy"}
        assert info.session_id == "sess-1"
        assert info.metadata.current_phase == "phase_0"


def test_user_profile_settings_defaults_match_backend_safe_fallback() -> None:
    """Defaults mirror BrandMind's backend safe-fallback for an empty install."""
    settings = UserProfileSettings()

    assert settings.job_domain == "unknown"
    assert settings.role == "unknown"
    assert settings.experience_years == "unknown"
    assert settings.brand_strategy_familiarity == "unknown"
    assert settings.mentoring_style == "balanced"
    assert settings.stakeholder_context == "unknown"
    assert settings.onboarding_completed is False
    assert settings.updated_at is None


def test_user_profile_option_accepts_empty_description() -> None:
    """Options with no description still validate cleanly."""
    option = UserProfileOption(value="fb", label="F&B")

    assert option.value == "fb"
    assert option.label == "F&B"
    assert option.description == ""


def test_user_profile_settings_options_defaults_to_empty_lists() -> None:
    """Empty defaults let the dialog render before the backend round-trip."""
    options = UserProfileSettingsOptions()

    assert options.job_domain == []
    assert options.role == []
    assert options.experience_years == []
    assert options.brand_strategy_familiarity == []
    assert options.mentoring_style == []
    assert options.stakeholder_context == []


def test_user_profile_settings_payload_round_trips_representative_response() -> None:
    """A backend-shaped payload validates end-to-end without data loss."""
    raw = {
        "settings": {
            "job_domain": "fb",
            "role": "marketing_executive",
            "experience_years": "1_3",
            "brand_strategy_familiarity": "comfortable",
            "mentoring_style": "compact_first",
            "stakeholder_context": "boss",
            "onboarding_completed": True,
            "updated_at": "2026-05-21T00:00:00+00:00",
        },
        "options": {
            "job_domain": [
                {"value": "fb", "label": "F&B", "description": "Food and beverage."},
                {"value": "retail", "label": "Retail", "description": ""},
            ],
            "role": [],
            "experience_years": [],
            "brand_strategy_familiarity": [],
            "mentoring_style": [],
            "stakeholder_context": [],
        },
        "profile_markdown": "# User Profile\n\n<!-- managed -->\n",
    }

    payload = UserProfileSettingsPayload.model_validate(raw)

    assert payload.settings.job_domain == "fb"
    assert payload.settings.onboarding_completed is True
    assert payload.options.job_domain[0].label == "F&B"
    assert payload.options.job_domain[0].description == "Food and beverage."
    assert payload.profile_markdown.startswith("# User Profile")
