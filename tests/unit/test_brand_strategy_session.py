"""Unit tests for Brand Strategy Session (Task 46).

Tests BrandStrategySession persistence, phase advancement,
and brief synchronization.
"""

from __future__ import annotations

import pytest
from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.messages import ToolMessage

from core.brand_strategy.content_check import (
    DeliverableDispatchGuardMiddleware,
    PhaseStateReminderMiddleware,
)
from core.brand_strategy.session import (
    BrandStrategySession,
    check_brand_brief_phase_section,
    list_sessions,
    load_session,
    save_session,
    set_active_session,
    update_strategy_progress,
)


class TestBrandStrategySession:
    """Test session model."""

    def test_default_session(self):
        session = BrandStrategySession()
        assert session.current_phase == "phase_0"
        assert session.scope is None
        assert session.brand_name is None
        assert session.completed_phases == []
        assert session.brief is not None
        assert len(session.session_id) == 8

    def test_advance_phase(self):
        session = BrandStrategySession()
        session.advance_phase("phase_1")
        assert session.current_phase == "phase_1"
        assert "phase_0" in session.completed_phases
        assert session.updated_at != ""

    def test_advance_multiple_phases(self):
        session = BrandStrategySession()
        session.advance_phase("phase_1")
        session.advance_phase("phase_2")
        session.advance_phase("phase_3")
        assert session.current_phase == "phase_3"
        assert session.completed_phases == [
            "phase_0",
            "phase_1",
            "phase_2",
        ]

    def test_advance_turn_guard_tracks_one_advance_per_turn(self):
        session = BrandStrategySession()

        session.begin_user_turn()
        assert session.can_advance_in_current_turn()

        session.mark_advanced_in_current_turn()
        assert not session.can_advance_in_current_turn()

        session.begin_user_turn()
        assert session.can_advance_in_current_turn()

    def test_save_phase_output(self):
        session = BrandStrategySession()
        session.save_phase_output(
            "phase_0",
            {
                "problem_statement": "Low foot traffic",
                "scope": "NEW_BRAND",
            },
        )
        assert session.brief.phase_0_output["problem_statement"] == "Low foot traffic"
        assert session.updated_at != ""

    def test_sync_metadata_to_brief(self):
        session = BrandStrategySession(
            brand_name="Café X",
            scope="REFRESH",
            budget_tier="growth",
        )
        session.sync_metadata_to_brief()
        assert session.brief.brand_name == "Café X"
        assert session.brief.scope == "REFRESH"
        assert session.brief.budget_tier == "growth"
        assert session.brief.session_id == session.session_id

    def test_sync_metadata_handles_none(self):
        session = BrandStrategySession()
        session.sync_metadata_to_brief()
        assert session.brief.brand_name == ""
        assert session.brief.scope == ""


class TestBrandBriefPhaseSectionCheck:
    """Test workspace phase-section coverage detection."""

    def test_phase_0_and_0_5_headings_are_distinct(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path)
        workspace = tmp_path / "projects" / "abc123" / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "brand_brief.md").write_text(
            "\n".join(
                [
                    "# Brand Brief",
                    "## Phase 0: Business Problem Diagnosis",
                    "## Phase 0.5: Brand Equity Audit",
                ]
            ),
            encoding="utf-8",
        )

        phase_0 = check_brand_brief_phase_section("abc123", "phase_0")
        phase_0_5 = check_brand_brief_phase_section("abc123", "phase_0_5")

        assert phase_0.passes
        assert phase_0_5.passes

    def test_phase_0_5_heading_does_not_satisfy_phase_0(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path)
        workspace = tmp_path / "projects" / "abc123" / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "brand_brief.md").write_text(
            "# Brand Brief\n\n## Phase 0.5: Brand Equity Audit\n",
            encoding="utf-8",
        )

        result = check_brand_brief_phase_section("abc123", "phase_0")

        assert result.brief_exists
        assert not result.section_exists
        assert not result.passes

    def test_missing_phase_heading_fails_when_quality_gate_says_complete(
        self,
        tmp_path,
        monkeypatch,
    ):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path)
        workspace = tmp_path / "projects" / "abc123" / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "brand_brief.md").write_text(
            "\n".join(
                [
                    "# Brand Brief",
                    "## Phase 2: Brand Positioning",
                    "## Phase 3: Brand Identity",
                ]
            ),
            encoding="utf-8",
        )

        result = check_brand_brief_phase_section("abc123", "phase_1")

        assert result.brief_exists
        assert not result.section_exists
        assert not result.passes


class TestUpdateStrategyProgress:
    """Test phase transaction guards exposed through report_progress."""

    def test_blocks_second_advance_in_same_user_turn(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path)
        workspace = tmp_path / "projects" / "abc123" / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "brand_brief.md").write_text(
            "# Brand Brief\n\n## Phase 0: Business Problem Diagnosis\n",
            encoding="utf-8",
        )
        session = BrandStrategySession(session_id="abc123", scope="new_brand")
        session.begin_user_turn()

        first = update_strategy_progress(session, advance=True)
        second = update_strategy_progress(session, advance=True)

        assert "phase: phase_0 → phase_1" in first
        assert "already advanced one phase" in second
        assert session.current_phase == "phase_1"

    def test_blocks_advance_when_completed_phase_section_is_missing(
        self,
        tmp_path,
        monkeypatch,
    ):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path)
        workspace = tmp_path / "projects" / "abc123" / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "brand_brief.md").write_text(
            "# Brand Brief\n\n## Phase 2: Brand Positioning\n",
            encoding="utf-8",
        )
        session = BrandStrategySession(
            session_id="abc123",
            scope="repositioning",
            current_phase="phase_2",
            completed_phases=["phase_0", "phase_0_5", "phase_1"],
        )
        session.begin_user_turn()

        result = update_strategy_progress(session, advance=True)

        assert "brand brief is missing completed/current phase coverage" in result
        assert "`## Phase 0: ...`" in result
        assert "`## Phase 0.5: ...`" in result
        assert "`## Phase 1: ...`" in result
        assert session.current_phase == "phase_2"


class TestDeliverableDispatchGuard:
    """Test phase-state gating for final artifact sub-agent dispatch."""

    @staticmethod
    def _task_request(subagent_type: str, description: str) -> ToolCallRequest:
        return ToolCallRequest(
            tool_call={
                "name": "task",
                "args": {
                    "subagent_type": subagent_type,
                    "description": description,
                },
                "id": "call_1",
            },
            tool=None,
            state={},
            runtime=None,  # type: ignore[arg-type]
        )

    @staticmethod
    def _handler(request: ToolCallRequest) -> ToolMessage:
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    def test_blocks_document_generator_before_phase_5(self) -> None:
        guard = DeliverableDispatchGuardMiddleware()
        session = BrandStrategySession(
            scope="repositioning",
            current_phase="phase_2",
            completed_phases=["phase_0", "phase_0_5", "phase_1"],
        )
        set_active_session(session)

        try:
            result = guard.wrap_tool_call(
                self._task_request("document-generator", "Build the DOCX"),
                self._handler,
            )
        finally:
            set_active_session(None)

        assert isinstance(result, ToolMessage)
        assert "Cannot dispatch final deliverable sub-agents yet" in result.content

    def test_allows_document_generator_at_phase_5(self) -> None:
        guard = DeliverableDispatchGuardMiddleware()
        session = BrandStrategySession(
            scope="repositioning",
            current_phase="phase_5",
            completed_phases=[
                "phase_0",
                "phase_0_5",
                "phase_1",
                "phase_2",
                "phase_3",
                "phase_4",
            ],
        )
        set_active_session(session)

        try:
            result = guard.wrap_tool_call(
                self._task_request("document-generator", "Build the DOCX"),
                self._handler,
            )
        finally:
            set_active_session(None)

        assert isinstance(result, ToolMessage)
        assert result.content == "ran"

    def test_blocks_brand_key_creative_dispatch_before_phase_5(self) -> None:
        guard = DeliverableDispatchGuardMiddleware()
        session = BrandStrategySession(
            scope="new_brand",
            current_phase="phase_3",
            completed_phases=["phase_0", "phase_1", "phase_2"],
        )
        set_active_session(session)

        try:
            result = guard.wrap_tool_call(
                self._task_request("creative-studio", "Build Brand Key one-pager"),
                self._handler,
            )
        finally:
            set_active_session(None)

        assert isinstance(result, ToolMessage)
        assert "Cannot dispatch final deliverable sub-agents yet" in result.content

    def test_allows_non_deliverable_subagents_before_phase_5(self) -> None:
        guard = DeliverableDispatchGuardMiddleware()
        session = BrandStrategySession(
            scope="new_brand",
            current_phase="phase_1",
            completed_phases=["phase_0"],
        )
        set_active_session(session)

        try:
            research = guard.wrap_tool_call(
                self._task_request("market-research", "Research competitors"),
                self._handler,
            )
            moodboard = guard.wrap_tool_call(
                self._task_request("creative-studio", "Explore color palette"),
                self._handler,
            )
        finally:
            set_active_session(None)

        assert isinstance(research, ToolMessage)
        assert isinstance(moodboard, ToolMessage)
        assert research.content == "ran"
        assert moodboard.content == "ran"


class TestPhaseStateReminder:
    """Test dynamic phase-state prompt reminders."""

    def test_reminder_names_authoritative_current_phase(self) -> None:
        session = BrandStrategySession(
            scope="repositioning",
            current_phase="phase_2",
            completed_phases=["phase_0", "phase_0_5", "phase_1"],
        )

        reminder = PhaseStateReminderMiddleware._render_reminder(session)

        assert "Current phase: phase_2" in reminder
        assert "Completed phases: phase_0, phase_0_5, phase_1" in reminder
        assert "Next phase after this phase passes: phase_3" in reminder
        assert "Produce only the current phase" in reminder
        assert "Future phase sections" in reminder


class TestSessionPersistence:
    """Test save/load/list."""

    def test_save_and_load(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path)

        session = BrandStrategySession(
            brand_name="Test Café",
            scope="NEW_BRAND",
            current_phase="phase_1",
            budget_tier="starter",
        )
        filepath = save_session(session)
        assert filepath.exists()

        loaded = load_session(session.session_id)
        assert loaded is not None
        assert loaded.brand_name == "Test Café"
        assert loaded.current_phase == "phase_1"
        assert loaded.scope == "NEW_BRAND"
        assert loaded.budget_tier == "starter"
        assert loaded.session_id == session.session_id

    def test_load_nonexistent_returns_none(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path)

        result = load_session("nonexistent_id")
        assert result is None

    def test_save_creates_directory(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        nested = tmp_path / "nested" / "dir"
        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", nested)

        session = BrandStrategySession()
        filepath = save_session(session)
        assert filepath.exists()
        assert nested.exists()

    def test_list_sessions(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path)

        # Save 3 sessions
        for name in ["Brand A", "Brand B", "Brand C"]:
            s = BrandStrategySession(brand_name=name)
            save_session(s)

        sessions = list_sessions()
        assert len(sessions) == 3
        names = {s["brand_name"] for s in sessions}
        assert names == {"Brand A", "Brand B", "Brand C"}

    def test_list_sessions_empty_dir(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path)

        sessions = list_sessions()
        assert sessions == []

    def test_save_updates_timestamp(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path)

        session = BrandStrategySession()
        assert session.updated_at == ""
        save_session(session)
        assert session.updated_at != ""

    def test_roundtrip_with_brief_data(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path)

        session = BrandStrategySession(brand_name="X")
        session.save_phase_output("phase_0", {"test_key": "test_value"})
        save_session(session)

        loaded = load_session(session.session_id)
        assert loaded is not None
        assert loaded.brief.phase_0_output["test_key"] == "test_value"
