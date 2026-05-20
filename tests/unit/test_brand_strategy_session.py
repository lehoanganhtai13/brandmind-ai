"""Unit tests for Brand Strategy Session (Task 46).

Tests BrandStrategySession persistence, phase advancement,
and brief synchronization.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.messages import HumanMessage, ToolMessage

from core.brand_strategy.content_check import (
    DeliverableDispatchGuardMiddleware,
    PhaseStateReminderMiddleware,
)
from core.brand_strategy.session import (
    BrandStrategySession,
    can_sync_to_deliverable_packaging,
    check_brand_brief_phase_section,
    get_phase_display_label,
    get_phase_display_labels,
    get_phase_sequence,
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


class TestPhaseSequenceAndDisplayLabels:
    """Pin phase-sequence and display-label helpers consumed by the web UI."""

    def test_phase_sequence_new_brand_skips_phase_0_5(self):
        sequence = get_phase_sequence("new_brand")
        assert sequence == [
            "phase_0",
            "phase_1",
            "phase_2",
            "phase_3",
            "phase_4",
            "phase_5",
        ]

    def test_phase_sequence_refresh_skips_phase_2(self):
        sequence = get_phase_sequence("refresh")
        assert sequence == [
            "phase_0",
            "phase_0_5",
            "phase_1",
            "phase_3",
            "phase_4",
            "phase_5",
        ]
        assert "phase_2" not in sequence

    def test_phase_sequence_repositioning_includes_all_seven_phases(self):
        sequence = get_phase_sequence("repositioning")
        assert sequence == [
            "phase_0",
            "phase_0_5",
            "phase_1",
            "phase_2",
            "phase_3",
            "phase_4",
            "phase_5",
        ]

    def test_phase_sequence_full_rebrand_matches_repositioning(self):
        assert get_phase_sequence("full_rebrand") == get_phase_sequence("repositioning")

    def test_phase_sequence_unknown_scope_is_empty_list(self):
        assert get_phase_sequence(None) == []
        assert get_phase_sequence("") == []
        assert get_phase_sequence("nonexistent_scope") == []

    def test_phase_sequence_returns_copy_not_internal_reference(self):
        first = get_phase_sequence("new_brand")
        first.append("mutated")
        second = get_phase_sequence("new_brand")
        assert "mutated" not in second

    def test_phase_display_label_returns_vietnamese_canonical(self):
        assert get_phase_display_label("phase_0") == "Chẩn đoán hiện trạng"
        assert get_phase_display_label("phase_0_5") == "Audit thương hiệu hiện có"
        assert get_phase_display_label("phase_2") == "Định vị thương hiệu"
        assert get_phase_display_label("phase_5") == "KPI & Lộ trình"

    def test_phase_display_label_unknown_phase_falls_back_to_title_case(self):
        assert get_phase_display_label("phase_99") == "Phase 99"

    def test_phase_display_labels_scoped_filters_to_scope_phases(self):
        labels = get_phase_display_labels("refresh")
        assert set(labels.keys()) == {
            "phase_0",
            "phase_0_5",
            "phase_1",
            "phase_3",
            "phase_4",
            "phase_5",
        }
        assert "phase_2" not in labels
        assert labels["phase_0_5"] == "Audit thương hiệu hiện có"

    def test_phase_display_labels_unset_scope_returns_empty_dict(self):
        assert get_phase_display_labels(None) == {}
        assert get_phase_display_labels("") == {}
        assert get_phase_display_labels("nonexistent_scope") == {}


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

    def test_advance_hint_uses_bounded_workspace_edits(self, tmp_path, monkeypatch):
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

        result = update_strategy_progress(session, advance=True)

        assert "Workspace handoff" in result
        assert "one `edit_file`" in result
        assert "update it in place" in result
        assert "do not retry multiple file edits" in result
        assert "Update `/user/profile.md` only if" in result

    def test_final_handoff_request_syncs_to_phase_5_when_brief_is_complete(
        self,
        tmp_path,
        monkeypatch,
    ):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path)
        workspace = tmp_path / "projects" / "abc123" / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "brand_brief.md").write_text(
            "\n\n".join(
                [
                    "# Brand Brief",
                    "## Phase 0: Business Problem Diagnosis\nDone.",
                    "## Phase 0.5: Brand Equity Audit\nDone.",
                    "## Phase 1: Market Intelligence\nDone.",
                    "## Phase 2: Brand Positioning\nDone.",
                    "## Phase 3: Brand Identity\nDone.",
                    "## Phase 4: Communication Framework\nDone.",
                ]
            ),
            encoding="utf-8",
        )
        session = BrandStrategySession(
            session_id="abc123",
            scope="repositioning",
            current_phase="phase_0",
            messages=[
                HumanMessage(
                    content=(
                        "Bạn làm giúp tôi bộ tài liệu cuối: một file "
                        "chiến lược, "
                        "một bộ slide, một bảng KPI, và một trang tóm tắt thương "
                        "hiệu để đem bàn với nhân viên."
                    )
                )
            ],
        )
        session.begin_user_turn()

        assert can_sync_to_deliverable_packaging(session)
        result = update_strategy_progress(session, advance=True)

        assert "phase: phase_0 → phase_5" in result
        assert session.current_phase == "phase_5"
        assert session.completed_phases == [
            "phase_0",
            "phase_0_5",
            "phase_1",
            "phase_2",
            "phase_3",
            "phase_4",
        ]

    def test_final_handoff_request_does_not_sync_when_brief_is_incomplete(
        self,
        tmp_path,
        monkeypatch,
    ):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path)
        workspace = tmp_path / "projects" / "abc123" / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "brand_brief.md").write_text(
            "# Brand Brief\n\n## Phase 0: Business Problem Diagnosis\nDone.\n",
            encoding="utf-8",
        )
        session = BrandStrategySession(
            session_id="abc123",
            scope="repositioning",
            current_phase="phase_0",
            messages=[
                HumanMessage(
                    content=(
                        "Làm bộ tài liệu cuối gồm file chiến lược, slide, "
                        "bảng KPI và trang tóm tắt thương hiệu."
                    )
                )
            ],
        )
        session.begin_user_turn()

        assert not can_sync_to_deliverable_packaging(session)
        result = update_strategy_progress(session, advance=True)

        assert "phase: phase_0 → phase_0_5" in result
        assert session.current_phase == "phase_0_5"


class TestDeliverableDispatchGuard:
    """Test phase-state gating for final artifact sub-agent dispatch."""

    @staticmethod
    def _task_request(
        subagent_type: str,
        description: str,
        messages: list[HumanMessage] | None = None,
    ) -> ToolCallRequest:
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
            state={"messages": messages or []},
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

    def test_syncs_to_phase_5_before_final_dispatch_when_workspace_is_ready(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path)
        workspace = tmp_path / "projects" / "abc123" / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "brand_brief.md").write_text(
            "\n\n".join(
                [
                    "# Brand Brief",
                    "## Phase 0: Business Problem Diagnosis\nDone.",
                    "## Phase 0.5: Brand Equity Audit\nDone.",
                    "## Phase 1: Market Intelligence\nDone.",
                    "## Phase 2: Brand Positioning\nDone.",
                    "## Phase 3: Brand Identity\nDone.",
                    "## Phase 4: Communication Framework\nDone.",
                ]
            ),
            encoding="utf-8",
        )
        guard = DeliverableDispatchGuardMiddleware()
        session = BrandStrategySession(
            session_id="abc123",
            scope="repositioning",
            current_phase="phase_2",
            completed_phases=["phase_0", "phase_0_5", "phase_1"],
        )
        final_request = HumanMessage(
            content=(
                "Làm bộ tài liệu cuối gồm file chiến lược, bộ slide, "
                "bảng KPI và trang tóm tắt thương hiệu."
            )
        )
        set_active_session(session)

        try:
            with patch.object(
                DeliverableDispatchGuardMiddleware,
                "_current_session_artifact_categories",
                side_effect=[set(), {"documents"}],
            ):
                result = guard.wrap_tool_call(
                    self._task_request(
                        "document-generator",
                        "Build the DOCX strategy document",
                        messages=[final_request],
                    ),
                    self._handler,
                )
        finally:
            set_active_session(None)

        assert isinstance(result, ToolMessage)
        assert result.content == "ran"
        assert session.current_phase == "phase_5"
        assert session.completed_phases == [
            "phase_0",
            "phase_0_5",
            "phase_1",
            "phase_2",
            "phase_3",
            "phase_4",
        ]

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
            with patch.object(
                DeliverableDispatchGuardMiddleware,
                "_current_session_artifact_categories",
                side_effect=[set(), {"documents"}],
            ):
                result = guard.wrap_tool_call(
                    self._task_request("document-generator", "Build the DOCX"),
                    self._handler,
                )
        finally:
            set_active_session(None)

        assert isinstance(result, ToolMessage)
        assert result.content == "ran"

    def test_blocks_dispatch_result_when_requested_artifact_is_missing(self) -> None:
        guard = DeliverableDispatchGuardMiddleware()
        session = BrandStrategySession(
            session_id="abc123",
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
            with patch.object(
                DeliverableDispatchGuardMiddleware,
                "_current_session_artifact_categories",
                side_effect=[set(), set()],
            ):
                result = guard.wrap_tool_call(
                    self._task_request("document-generator", "Build the PPTX deck"),
                    self._handler,
                )
        finally:
            set_active_session(None)

        assert isinstance(result, ToolMessage)
        assert "still does not contain: presentations" in result.content
        assert "Do not mark this deliverable as completed" in result.content
        assert 'list_artifacts(scope="current_session")' in result.content
        assert "fallback text does not satisfy" in result.content

    @pytest.mark.asyncio
    async def test_async_allows_dispatch_result_when_requested_artifact_exists(
        self,
    ) -> None:
        guard = DeliverableDispatchGuardMiddleware()
        session = BrandStrategySession(
            session_id="abc123",
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
        handler = AsyncMock(
            return_value=ToolMessage("ran", tool_call_id="call_1")
        )

        try:
            with patch.object(
                DeliverableDispatchGuardMiddleware,
                "_current_session_artifact_categories",
                side_effect=[set(), {"presentations"}],
            ):
                result = await guard.awrap_tool_call(
                    self._task_request("document-generator", "Build the PPTX deck"),
                    handler,
                )
        finally:
            set_active_session(None)

        handler.assert_awaited_once()
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

    def test_blocks_duplicate_document_dispatch_after_artifact_exists(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        guard = DeliverableDispatchGuardMiddleware()
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        manifest = tmp_path / ".manifest.jsonl"
        manifest.write_text(
            json.dumps(
                {
                    "session_id": "abc123",
                    "category": "documents",
                    "path": str(tmp_path / "strategy.docx"),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        session = BrandStrategySession(
            session_id="abc123",
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
        assert "already exist" in str(result.content)
        assert "documents" in str(result.content)

    def test_allows_missing_artifact_category_when_dispatch_creates_it(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        guard = DeliverableDispatchGuardMiddleware()
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        (tmp_path / ".manifest.jsonl").write_text("", encoding="utf-8")
        session = BrandStrategySession(
            session_id="abc123",
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
            with patch.object(
                DeliverableDispatchGuardMiddleware,
                "_current_session_artifact_categories",
                side_effect=[set(), {"documents"}],
            ):
                result = guard.wrap_tool_call(
                    self._task_request("document-generator", "Build the DOCX"),
                    self._handler,
                )
        finally:
            set_active_session(None)

        assert isinstance(result, ToolMessage)
        assert result.content == "ran"

    def test_allows_brand_key_dispatch_after_non_deliverable_image_exists(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        guard = DeliverableDispatchGuardMiddleware()
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        (tmp_path / ".manifest.jsonl").write_text(
            json.dumps(
                {
                    "session_id": "abc123",
                    "category": "images",
                    "tool": "generate_image",
                    "filename": "mood_board.jpeg",
                    "path": str(tmp_path / "mood_board.jpeg"),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        session = BrandStrategySession(
            session_id="abc123",
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

        def _handler_that_writes_brand_key(request: ToolCallRequest) -> ToolMessage:
            with (tmp_path / ".manifest.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "session_id": "abc123",
                            "category": "images",
                            "tool": "generate_brand_key",
                            "filename": "brand_key.jpeg",
                            "path": str(tmp_path / "brand_key.jpeg"),
                        }
                    )
                    + "\n"
                )
            return ToolMessage("ran", tool_call_id=request.tool_call["id"])

        try:
            result = guard.wrap_tool_call(
                self._task_request("creative-studio", "Build Brand Key one-pager"),
                _handler_that_writes_brand_key,
            )
        finally:
            set_active_session(None)

        assert isinstance(result, ToolMessage)
        assert result.content == "ran"

    def test_blocks_duplicate_brand_key_dispatch_after_brand_key_exists(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        guard = DeliverableDispatchGuardMiddleware()
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        (tmp_path / ".manifest.jsonl").write_text(
            json.dumps(
                {
                    "session_id": "abc123",
                    "category": "images",
                    "tool": "generate_brand_key",
                    "filename": "brand_key.jpeg",
                    "path": str(tmp_path / "brand_key.jpeg"),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        session = BrandStrategySession(
            session_id="abc123",
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
                self._task_request("creative-studio", "Build Brand Key one-pager"),
                self._handler,
            )
        finally:
            set_active_session(None)

        assert isinstance(result, ToolMessage)
        assert "already exist" in str(result.content)
        assert "images" in str(result.content)

    def test_blocks_kpi_xlsx_dispatch_that_substitutes_workspace_metrics(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        import shared.workspace as workspace_mod

        guard = DeliverableDispatchGuardMiddleware()
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path / "output"))
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / ".manifest.jsonl").write_text("", encoding="utf-8")
        monkeypatch.setattr(workspace_mod, "BRANDMIND_HOME", tmp_path / "home")
        workspace = tmp_path / "home" / "projects" / "abc123" / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "brand_brief.md").write_text(
            "\n".join(
                [
                    "# Brand Brief",
                    "## Phase 5: Strategy Plan & Deliverables (COMPLETED)",
                    "- **KPI Framework**:",
                    "    1. **Tổng Booking ngày thường (T2-T6)**: target",
                    "    2. **Tỷ lệ lấp đầy phòng riêng (Ngày thường)**: target",
                    "    3. **Qualified Booking Leads**: target",
                    "    4. **Engagement Rate (Nội dung Business)**: target",
                    "    5. **Cost Per Booking (CPB)**: target",
                ]
            ),
            encoding="utf-8",
        )
        session = BrandStrategySession(
            session_id="abc123",
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
        description = "\n".join(
            [
                "Build XLSX KPI Dashboard.",
                'row_1 KPI="Tổng Booking ngày thường (T2-T6)" Baseline="N/A"',
                'row_2 KPI="Tỷ lệ lấp đầy phòng riêng (Ngày thường)" Current="0"',
                'row_3 KPI="Qualified Booking Leads" '
                'Baseline="no data — measure pre-launch"',
                'row_4 KPI="Average Guest Check (AOV)" Baseline="[Current]"',
                'row_5 KPI="Cost Per Booking (CPB)" '
                'Current="no data — measure pre-launch"',
            ]
        )
        set_active_session(session)

        try:
            result = guard.wrap_tool_call(
                self._task_request("document-generator", description),
                self._handler,
            )
        finally:
            set_active_session(None)

        assert isinstance(result, ToolMessage)
        assert "Cannot dispatch KPI XLSX yet" in str(result.content)
        assert "Engagement Rate (Nội dung Business)" in str(result.content)
        assert "placeholder value(s)" in str(result.content)

    def test_allows_kpi_xlsx_dispatch_with_exact_workspace_metrics(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        import shared.workspace as workspace_mod

        guard = DeliverableDispatchGuardMiddleware()
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path / "output"))
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / ".manifest.jsonl").write_text("", encoding="utf-8")
        monkeypatch.setattr(workspace_mod, "BRANDMIND_HOME", tmp_path / "home")
        workspace = tmp_path / "home" / "projects" / "abc123" / "workspace"
        workspace.mkdir(parents=True)
        kpi_names = [
            "Tổng Booking ngày thường (T2-T6)",
            "Tỷ lệ lấp đầy phòng riêng (Ngày thường)",
            "Qualified Booking Leads",
            "Engagement Rate (Nội dung Business)",
            "Cost Per Booking (CPB)",
        ]
        (workspace / "brand_brief.md").write_text(
            "\n".join(
                [
                    "# Brand Brief",
                    "## Phase 5: Strategy Plan & Deliverables (COMPLETED)",
                    "- **KPI Framework**:",
                    *[
                        f"    {index}. **{name}**: target"
                        for index, name in enumerate(kpi_names, start=1)
                    ],
                ]
            ),
            encoding="utf-8",
        )
        session = BrandStrategySession(
            session_id="abc123",
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
        rows = [
            f'row_{index} KPI="{name}" Baseline="no data — measure pre-launch"'
            for index, name in enumerate(kpi_names, start=1)
        ]
        set_active_session(session)

        try:
            with patch.object(
                DeliverableDispatchGuardMiddleware,
                "_current_session_artifact_categories",
                side_effect=[set(), {"spreadsheets"}],
            ):
                result = guard.wrap_tool_call(
                    self._task_request(
                        "document-generator", "\n".join(["XLSX", *rows])
                    ),
                    self._handler,
                )
        finally:
            set_active_session(None)

        assert isinstance(result, ToolMessage)
        assert result.content == "ran"


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

        brandmind_home = tmp_path / "home.brandmind"
        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", brandmind_home)

        session = BrandStrategySession(
            brand_name="Test Café",
            scope="NEW_BRAND",
            current_phase="phase_1",
            budget_tier="starter",
        )
        filepath = save_session(session)
        assert filepath.exists()
        assert filepath.parent == brandmind_home / "sessions" / "brand_strategy"

        loaded = load_session(session.session_id)
        assert loaded is not None
        assert loaded.brand_name == "Test Café"
        assert loaded.current_phase == "phase_1"
        assert loaded.scope == "NEW_BRAND"
        assert loaded.budget_tier == "starter"
        assert loaded.session_id == session.session_id

    def test_load_nonexistent_returns_none(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path / "home.brandmind")

        result = load_session("nonexistent_id")
        assert result is None

    def test_load_legacy_message_shape(self, tmp_path, monkeypatch):
        import json

        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path / "home.brandmind")

        session = BrandStrategySession(session_id="legacy1", brand_name="Legacy")
        data = session.model_dump()
        data["messages"] = [
            {
                "content": "Xin chào",
                "additional_kwargs": {},
                "response_metadata": {},
                "type": "human",
                "name": None,
                "id": "message-1",
            },
            {
                "content": "Chào bạn.",
                "additional_kwargs": {},
                "response_metadata": {},
                "type": "ai",
                "name": None,
                "id": "message-2",
            },
        ]
        filepath = sess_mod.get_session_file("legacy1")
        filepath.parent.mkdir(parents=True)
        filepath.write_text(
            json.dumps(data, ensure_ascii=False),
            encoding="utf-8",
        )

        loaded = load_session("legacy1")

        assert loaded is not None
        assert [message.type for message in loaded.messages] == ["human", "ai"]
        assert loaded.messages[0].content == "Xin chào"

    def test_save_creates_directory(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        brandmind_home = tmp_path / "nested" / "home.brandmind"
        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", brandmind_home)

        session = BrandStrategySession()
        filepath = save_session(session)
        assert filepath.exists()
        assert sess_mod.get_sessions_dir().exists()

    def test_list_sessions(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path / "home.brandmind")

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

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path / "home.brandmind")

        sessions = list_sessions()
        assert sessions == []

    def test_save_updates_timestamp(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path / "home.brandmind")

        session = BrandStrategySession()
        assert session.updated_at == ""
        save_session(session)
        assert session.updated_at != ""

    def test_roundtrip_with_brief_data(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path / "home.brandmind")

        session = BrandStrategySession(brand_name="X")
        session.save_phase_output("phase_0", {"test_key": "test_value"})
        save_session(session)

        loaded = load_session(session.session_id)
        assert loaded is not None
        assert loaded.brief.phase_0_output["test_key"] == "test_value"

    def test_reset_home_boundary_clears_saved_sessions(self, tmp_path, monkeypatch):
        import shutil

        import core.brand_strategy.session as sess_mod

        brandmind_home = tmp_path / "home.brandmind"
        monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", brandmind_home)

        save_session(BrandStrategySession(brand_name="Reset Me"))
        assert list_sessions()

        shutil.rmtree(brandmind_home)

        assert list_sessions() == []
