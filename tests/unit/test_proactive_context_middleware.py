"""Unit tests for proactive context assembly and injection."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from core.brand_strategy.session import BrandStrategySession, set_active_session
from shared.agent_middlewares.proactive_context import (
    ProactiveActionContract,
    ProactiveContextBuilder,
    ProactiveContextItem,
    ProactiveContextPacket,
    ProactiveProjectMatch,
    ProactiveTurnMiddleware,
)
from shared.agent_middlewares.proactive_context import middleware as proactive_mod


@dataclass
class _FakeRequest:
    """Minimal request double for testing middleware prompt overrides."""

    messages: list[object]
    system_prompt: str = "BASE SYSTEM"
    state: Mapping[str, object] | None = None

    def override(self, system_message: SystemMessage | None = None, **_: object):
        """Return a new fake request with the updated system prompt."""
        prompt = self.system_prompt
        if system_message is not None:
            prompt = str(system_message.content)
        return _FakeRequest(
            messages=self.messages,
            system_prompt=prompt,
            state=self.state,
        )


class _FakeBuilder:
    """Builder double that records the user text and active session id."""

    def __init__(self, packet: ProactiveContextPacket) -> None:
        """Create a builder double returning a fixed packet."""
        self.packet = packet
        self.calls: list[tuple[str, str | None]] = []

    def build(
        self,
        user_text: str,
        session_id: str | None = None,
        *,
        discovery_needed: bool = False,
        post_tool_context_seen: bool = False,
    ):
        """Return the configured packet while capturing call arguments."""
        self.calls.append(
            (user_text, session_id, discovery_needed, post_tool_context_seen)
        )
        return self.packet


def _write_project_index(home: Path, projects: dict[str, dict[str, object]]) -> None:
    """Write a BrandMind index fixture under a temporary home directory."""
    (home / "index.json").write_text(
        json.dumps({"projects": projects}, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_workspace(home: Path, session_id: str, brief: str, notes: str = "") -> None:
    """Write a minimal project workspace fixture."""
    workspace = home / "projects" / session_id / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "brand_brief.md").write_text(brief, encoding="utf-8")
    if notes:
        (workspace / "working_notes.md").write_text(notes, encoding="utf-8")


def test_builder_prioritizes_substantive_user_profile(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A real profile becomes personalization context without extra intake."""
    monkeypatch.setattr(proactive_mod.workspace_mod, "BRANDMIND_HOME", tmp_path)
    user_dir = tmp_path / "user"
    user_dir.mkdir(parents=True)
    (user_dir / "profile.md").write_text(
        "# User Profile\n\n"
        "## Communication Preferences\n"
        "User prefers direct Vietnamese guidance with clear tradeoffs, "
        "evidence boundaries, and practical next steps for brand strategy work.\n\n"
        "## Working Style\n"
        "User challenges loose assumptions and wants the assistant to verify "
        "workspace evidence before asking repetitive questions.\n",
        encoding="utf-8",
    )

    packet = ProactiveContextBuilder().build(
        "Tôi muốn làm brand strategy cho một nhà hàng mới.",
    )
    rendered = packet.to_prompt()

    assert packet.ask_budget == 2
    assert "User profile" in rendered
    assert "verify workspace evidence" in rendered
    assert "Recommended next action: ask_one_blocker" in rendered
    assert "Evidence level: profile_backed" in rendered


def test_builder_adds_generic_discovery_posture_for_early_unknown_project(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Unknown early cases should get process guidance without domain overfit."""
    monkeypatch.setattr(proactive_mod.workspace_mod, "BRANDMIND_HOME", tmp_path)

    packet = ProactiveContextBuilder().build(
        "Tôi muốn làm brand strategy cho một thương hiệu mới.",
        discovery_needed=True,
    )
    rendered = packet.to_prompt()

    assert packet.has_content is True
    assert packet.ask_budget == 1
    assert packet.initiative_mode == "discover_before_asking"
    assert packet.action_contract.recommended_next_action == "discover_then_ask"
    assert "self-discovery pass" in rendered
    assert "## Proactive Action Contract" in rendered
    assert "single focused blocker" in rendered
    assert "Resolve before asking when practical" in rendered
    assert "single most decision-changing user-only blocker" in rendered

    lower_rendered = rendered.casefold()
    for forbidden in ("cafe", "restaurant", "signature", "mây rêu", "nếp nhà"):
        assert forbidden not in lower_rendered


def test_builder_keeps_empty_packet_when_discovery_not_needed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """No prior context should stay silent outside the early diagnosis trigger."""
    monkeypatch.setattr(proactive_mod.workspace_mod, "BRANDMIND_HOME", tmp_path)

    packet = ProactiveContextBuilder().build(
        "Tôi muốn làm brand strategy cho một thương hiệu mới.",
        discovery_needed=False,
    )

    assert packet.has_content is False
    assert packet.to_prompt() == ""


def test_builder_ignores_template_only_profile(tmp_path: Path, monkeypatch) -> None:
    """The default profile template must not masquerade as personalization."""
    monkeypatch.setattr(proactive_mod.workspace_mod, "BRANDMIND_HOME", tmp_path)
    user_dir = tmp_path / "user"
    user_dir.mkdir(parents=True)
    (user_dir / "profile.md").write_text(
        "# User Profile\n\n"
        "## Identity\n"
        "- Role: [To be discovered]\n"
        "- Industry expertise: [To be discovered]\n"
        "- Language: [To be discovered]\n\n"
        "## Communication Preferences\n"
        "_How user prefers to interact — concise vs detailed._\n",
        encoding="utf-8",
    )

    packet = ProactiveContextBuilder().build("Tôi muốn làm brand strategy.")

    assert packet.has_content is False
    assert packet.to_prompt() == ""


def test_builder_ignores_current_workspace_starter_templates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Starter workspace files should not look like real project memory."""
    monkeypatch.setattr(proactive_mod.workspace_mod, "BRANDMIND_HOME", tmp_path)
    workspace = tmp_path / "projects" / "current-session" / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "brand_brief.md").write_text(
        proactive_mod.workspace_mod.BRAND_BRIEF_TEMPLATE,
        encoding="utf-8",
    )
    (workspace / "working_notes.md").write_text(
        proactive_mod.workspace_mod.WORKING_NOTES_TEMPLATE,
        encoding="utf-8",
    )

    packet = ProactiveContextBuilder().build(
        "Tôi muốn làm brand strategy.",
        session_id="current-session",
    )

    assert packet.has_content is False


def test_builder_finds_related_prior_project_by_brand_name(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Prior project matches should let the agent continue before re-asking."""
    monkeypatch.setattr(proactive_mod.workspace_mod, "BRANDMIND_HOME", tmp_path)
    _write_project_index(
        tmp_path,
        {
            "prior-1": {
                "brand_name": "Chuyện Ba Bữa Signature",
                "updated_at": "2026-05-16T10:00:00",
            }
        },
    )
    _write_workspace(
        tmp_path,
        "prior-1",
        "# Brand Brief\n\n"
        "## Executive Summary\n"
        "Signature is positioned as a refined Vietnamese business table for "
        "weekday business lunch and private dinner in central Saigon.\n\n"
        "## Golden Thread\n"
        "Weekday empty tables become a privacy advantage for business dining.\n",
        notes=(
            "# Working Notes\n\n## Pending Questions\nConfirm latest menu packages.\n"
        ),
    )

    packet = ProactiveContextBuilder().build(
        "Tôi muốn làm brand strategy cho nhà hàng Chuyện Ba Bữa Signature á",
        session_id="current-session",
        discovery_needed=True,
    )
    rendered = packet.to_prompt()

    assert packet.ask_budget == 1
    assert packet.initiative_mode == "collect_then_answer"
    assert packet.action_contract.recommended_next_action == "continue_from_memory"
    assert packet.prior_matches[0].brand_name == "Chuyện Ba Bữa Signature"
    assert "weekday business lunch" in rendered
    assert "needs confirmation: yes" in rendered
    assert "ask exactly one confirmation question" in rendered
    assert "Recommended next action: continue_from_memory" in rendered


def test_builder_skips_current_session_when_matching_prior_projects(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The active workspace should not be duplicated as a prior project."""
    monkeypatch.setattr(proactive_mod.workspace_mod, "BRANDMIND_HOME", tmp_path)
    _write_project_index(
        tmp_path,
        {
            "current-session": {
                "brand_name": "Chuyện Ba Bữa Signature",
                "updated_at": "2026-05-16T10:00:00",
            }
        },
    )

    packet = ProactiveContextBuilder().build(
        "Làm tiếp cho Chuyện Ba Bữa Signature",
        session_id="current-session",
    )

    assert packet.prior_matches == ()


def test_builder_adds_post_tool_synthesis_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """After tool results, context should be synthesized before generic asks."""
    monkeypatch.setattr(proactive_mod.workspace_mod, "BRANDMIND_HOME", tmp_path)

    packet = ProactiveContextBuilder().build(
        "Tôi muốn làm brand strategy cho một thương hiệu mới.",
        discovery_needed=True,
        post_tool_context_seen=True,
    )
    rendered = packet.to_prompt()

    assert (
        packet.action_contract.recommended_next_action == "synthesize_collected_context"
    )
    assert "Recommended next action: synthesize_collected_context" in rendered
    assert "recent tool results" in rendered
    assert "Use them to produce a grounded synthesis" in rendered


def test_middleware_injects_context_and_active_session_id() -> None:
    """Middleware should append context using the current session id."""
    packet = ProactiveContextPacket(
        initiative_mode="collect_then_answer",
        ask_budget=1,
        items=(
            ProactiveContextItem(
                source="user_profile",
                title="User profile",
                content="User prefers proactive Vietnamese strategy mentoring.",
                confidence="high",
            ),
        ),
        prior_matches=(
            ProactiveProjectMatch(
                session_id="prior-1",
                brand_name="Chuyện Ba Bữa Signature",
                updated_at="2026-05-16T10:00:00",
                score=1.0,
                workspace_excerpt="Existing positioning already exists.",
            ),
        ),
    )
    builder = _FakeBuilder(packet)
    middleware = ProactiveTurnMiddleware(builder=builder)
    request = _FakeRequest(messages=[HumanMessage(content="Làm tiếp Signature")])
    set_active_session(BrandStrategySession(session_id="active-1"))

    try:
        result = middleware._inject_context(request)  # noqa: SLF001
    finally:
        set_active_session(None)

    assert builder.calls == [("Làm tiếp Signature", "active-1", True, False)]
    assert "BASE SYSTEM" in result.system_prompt
    assert "# RUNTIME PROACTIVE CONTEXT" in result.system_prompt
    assert "Ask budget for this response: at most 1" in result.system_prompt
    assert "Chuyện Ba Bữa Signature" in result.system_prompt


def test_middleware_marks_post_tool_context_seen() -> None:
    """Middleware should tell the builder when a model call follows tool output."""
    packet = ProactiveContextPacket(
        initiative_mode="discover_before_asking",
        ask_budget=1,
        action_contract=ProactiveActionContract(
            recommended_next_action="synthesize_collected_context",
        ),
    )
    builder = _FakeBuilder(packet)
    middleware = ProactiveTurnMiddleware(builder=builder)
    request = _FakeRequest(
        messages=[
            HumanMessage(content="Tôi muốn làm brand strategy."),
            ToolMessage(content="Workspace context loaded.", tool_call_id="tool-1"),
        ]
    )

    middleware._inject_context(request)  # noqa: SLF001

    assert builder.calls == [("Tôi muốn làm brand strategy.", None, True, True)]


def test_middleware_noops_when_builder_has_no_context() -> None:
    """Empty packets should leave the model request unchanged."""
    builder = _FakeBuilder(
        ProactiveContextPacket(
            initiative_mode="normal_diagnosis",
            ask_budget=3,
        )
    )
    middleware = ProactiveTurnMiddleware(builder=builder)
    request = _FakeRequest(messages=[HumanMessage(content="Start new strategy")])

    result = middleware._inject_context(request)  # noqa: SLF001

    assert result is request
