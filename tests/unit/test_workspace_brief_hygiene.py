"""Unit tests for brand brief edit hygiene middleware."""

from __future__ import annotations

from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.messages import HumanMessage, ToolMessage

from core.brand_strategy.session import BrandStrategySession, set_active_session
from shared.agent_middlewares.workspace_hygiene import (
    WorkspaceBriefHygieneMiddleware,
)
from shared.agent_middlewares.workspace_hygiene import middleware as hygiene_mod

_PHASE_0 = "## Phase 0: Business Problem Diagnosis (COMPLETED)\nContext.\n\n"
_PHASE_1 = "## Phase 1: Market Intelligence (COMPLETED)\nMarket analysis.\n\n"
_PHASE_5_OLD = "## Phase 5: Strategy Plan & Deliverables (COMPLETED)\nOld.\n\n"
_PHASE_5_NEW = "## Phase 5: Strategy Plan & Deliverables (COMPLETED)\nNew.\n\n"


def _edit_request(old_string: str, new_string: str) -> ToolCallRequest:
    return ToolCallRequest(
        tool_call={
            "name": "edit_file",
            "args": {
                "file_path": "/workspace/brand_brief.md",
                "old_string": old_string,
                "new_string": new_string,
            },
            "id": "call_1",
        },
        tool=None,
        state={},
        runtime=None,  # type: ignore[arg-type]
    )


def _profile_edit_request(user_texts: list[str]) -> ToolCallRequest:
    return ToolCallRequest(
        tool_call={
            "name": "edit_file",
            "args": {
                "file_path": "/user/profile.md",
                "old_string": "## Identity\n- Role: [To be discovered]",
                "new_string": "## Identity\n- Role: [Chủ doanh nghiệp F&B]",
            },
            "id": "call_profile",
        },
        tool=None,
        state={"messages": [HumanMessage(content=text) for text in user_texts]},
        runtime=None,  # type: ignore[arg-type]
    )


def test_blocks_edit_that_removes_existing_phase_heading() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "### P - What's next\n## Phase 1: Market Intelligence (COMPLETED)"
    new_string = "### P - What's next\n## Phase 4: Communication Framework"
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(_edit_request(old_string, new_string), handler)

    assert isinstance(result, ToolMessage)
    assert handler_called is False
    assert "preserve existing phase heading" in str(result.content)
    assert "`## Phase 1`" in str(result.content)


def test_normalizes_duplicate_phases_after_allowed_edit(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(hygiene_mod, "BRANDMIND_HOME", tmp_path)
    workspace = tmp_path / "projects" / "abc123" / "workspace"
    workspace.mkdir(parents=True)
    brief = workspace / "brand_brief.md"
    brief.write_text("# Brand\n\n" + _PHASE_0 + _PHASE_5_OLD + _PHASE_1, "utf-8")

    middleware = WorkspaceBriefHygieneMiddleware()
    request = _edit_request(_PHASE_1, _PHASE_5_NEW + _PHASE_1)
    session = BrandStrategySession(session_id="abc123")
    set_active_session(session)

    def handler(request: ToolCallRequest) -> ToolMessage:
        brief.write_text(
            "# Brand\n\n" + _PHASE_0 + _PHASE_5_OLD + _PHASE_1 + _PHASE_5_NEW,
            "utf-8",
        )
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    try:
        result = middleware.wrap_tool_call(request, handler)
    finally:
        set_active_session(None)

    persisted = brief.read_text("utf-8")
    assert isinstance(result, ToolMessage)
    assert result.content == "ran"
    assert "Old." not in persisted
    assert "New." in persisted
    assert _PHASE_1 in persisted


def test_recovers_stale_full_brief_template_replace(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(hygiene_mod, "BRANDMIND_HOME", tmp_path)
    workspace = tmp_path / "projects" / "abc123" / "workspace"
    workspace.mkdir(parents=True)
    brief = workspace / "brand_brief.md"
    brief.write_text("# Brand Brief\n\n" + _PHASE_0, "utf-8")

    old_string = "# Brand Strategy Brief: [Brand Name]\n\n## Phase 0\n"
    new_string = "\n\n".join(
        [
            "# Brand Strategy Brief: Cà Phê Cũ",
            "## Phase 0: Business Problem Diagnosis\nDone.",
            "## Phase 0.5: Brand Equity Audit\nDone.",
            "## Phase 1: Market Intelligence\nDone.",
            "## Phase 2: Brand Positioning\nDone.",
            "## Phase 3: Brand Identity\nDone.",
            "## Phase 4: Communication Framework\nDone.",
            "## Phase 5: Strategy Plan & Deliverables\nDone.",
        ]
    )

    middleware = WorkspaceBriefHygieneMiddleware()
    session = BrandStrategySession(session_id="abc123")
    set_active_session(session)

    def handler(request: ToolCallRequest) -> ToolMessage:
        return ToolMessage("Error: String not found in file", tool_call_id="call_1")

    try:
        result = middleware.wrap_tool_call(
            _edit_request(old_string, new_string), handler
        )
    finally:
        set_active_session(None)

    persisted = brief.read_text("utf-8")
    assert isinstance(result, ToolMessage)
    assert "Recovered `/workspace/brand_brief.md`" in str(result.content)
    assert "# Brand Strategy Brief: Cà Phê Cũ" in persisted
    assert "## Phase 0.5: Brand Equity Audit" in persisted
    assert "## Phase 5: Strategy Plan & Deliverables" in persisted


def test_recovers_placeholder_full_brief_with_nested_phases_and_syncs_handoff(
    tmp_path,
    monkeypatch,
) -> None:
    import core.brand_strategy.session as sess_mod

    monkeypatch.setattr(hygiene_mod, "BRANDMIND_HOME", tmp_path)
    monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path)
    workspace = tmp_path / "projects" / "abc123" / "workspace"
    workspace.mkdir(parents=True)
    brief = workspace / "brand_brief.md"
    brief.write_text(
        "# Brand Brief\n\n## Phase 0: Business Problem Diagnosis\nOld.",
        "utf-8",
    )

    old_string = "# Brand Brief\n(Empty or placeholder content)\n"
    new_string = "\n\n".join(
        [
            "# Brand Brief - Cà Phê Cũ",
            "## 3. Chi tiết các giai đoạn",
            "### Phase 0: Business Problem Diagnosis\nDone.",
            "### Phase 0.5: Brand Equity Audit\nDone.",
            "### Phase 1: Market Intelligence\nDone.",
            "### Phase 2: Brand Positioning\nDone.",
            "### Phase 3: Brand Identity\nDone.",
            "### Phase 4: Communication Framework\nDone.",
            "### Phase 5: Strategy Plan & Deliverables\nReady.",
        ]
    )

    request = _edit_request(old_string, new_string)
    request.state["messages"] = [
        HumanMessage(
            content=(
                "Làm giúp tôi bộ tài liệu cuối gồm file chiến lược, "
                "bộ slide, bảng KPI và trang tóm tắt thương hiệu."
            )
        )
    ]
    middleware = WorkspaceBriefHygieneMiddleware()
    session = BrandStrategySession(
        session_id="abc123",
        scope="repositioning",
        current_phase="phase_0_5",
        completed_phases=["phase_0"],
    )
    set_active_session(session)

    def handler(request: ToolCallRequest) -> ToolMessage:
        return ToolMessage("Error: String not found in file", tool_call_id="call_1")

    try:
        result = middleware.wrap_tool_call(request, handler)
    finally:
        set_active_session(None)

    persisted = brief.read_text("utf-8")
    assert isinstance(result, ToolMessage)
    assert "Recovered `/workspace/brand_brief.md`" in str(result.content)
    assert "phase: phase_0_5 → phase_5" in str(result.content)
    assert session.current_phase == "phase_5"
    assert "### Phase" not in persisted
    assert "## Phase 2: Brand Positioning" in persisted
    assert "## Phase 5: Strategy Plan & Deliverables" in persisted


def test_intercepts_broad_replace_all_as_phase_section_upsert(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(hygiene_mod, "BRANDMIND_HOME", tmp_path)
    workspace = tmp_path / "projects" / "abc123" / "workspace"
    workspace.mkdir(parents=True)
    brief = workspace / "brand_brief.md"
    brief.write_text("# Brand Brief\n\n" + _PHASE_0 + _PHASE_1, "utf-8")

    new_string = "\n\n".join(
        [
            "---",
            "## Phase 2: Brand Positioning\nPositioning summary.",
            "## Phase 3: Brand Identity\nIdentity summary.",
        ]
    )
    request = _edit_request("---", new_string)
    request.tool_call["args"]["replace_all"] = True
    middleware = WorkspaceBriefHygieneMiddleware()
    session = BrandStrategySession(session_id="abc123")
    set_active_session(session)
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    try:
        result = middleware.wrap_tool_call(request, handler)
    finally:
        set_active_session(None)

    persisted = brief.read_text("utf-8")
    assert handler_called is False
    assert isinstance(result, ToolMessage)
    assert "upserting the supplied phase section" in str(result.content)
    assert "## Phase 0: Business Problem Diagnosis" in persisted
    assert "## Phase 1: Market Intelligence" in persisted
    assert "## Phase 2: Brand Positioning" in persisted
    assert "## Phase 3: Brand Identity" in persisted


def test_recovers_ambiguous_separator_edit_as_phase_section_upsert(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(hygiene_mod, "BRANDMIND_HOME", tmp_path)
    workspace = tmp_path / "projects" / "abc123" / "workspace"
    workspace.mkdir(parents=True)
    brief = workspace / "brand_brief.md"
    brief.write_text("# Brand Brief\n\n" + _PHASE_0, "utf-8")

    new_string = "---\n\n## Phase 2: Brand Positioning\nPositioning summary."
    middleware = WorkspaceBriefHygieneMiddleware()
    session = BrandStrategySession(session_id="abc123")
    set_active_session(session)

    def handler(request: ToolCallRequest) -> ToolMessage:
        return ToolMessage(
            "Error: String '---' appears 3 times in file.",
            tool_call_id=request.tool_call["id"],
        )

    try:
        result = middleware.wrap_tool_call(_edit_request("---", new_string), handler)
    finally:
        set_active_session(None)

    persisted = brief.read_text("utf-8")
    assert isinstance(result, ToolMessage)
    assert "upserting the supplied phase section" in str(result.content)
    assert "## Phase 0: Business Problem Diagnosis" in persisted
    assert "## Phase 2: Brand Positioning" in persisted


def test_ignores_non_brand_brief_edits() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    request = ToolCallRequest(
        tool_call={
            "name": "edit_file",
            "args": {
                "file_path": "/workspace/working_notes.md",
                "old_string": "## Phase 1",
                "new_string": "## Phase 4",
            },
            "id": "call_1",
        },
        tool=None,
        state={},
        runtime=None,  # type: ignore[arg-type]
    )

    result = middleware.wrap_tool_call(
        request,
        lambda req: ToolMessage("ran", tool_call_id=req.tool_call["id"]),
    )

    assert isinstance(result, ToolMessage)
    assert result.content == "ran"


def test_blocks_sparse_first_turn_profile_inference() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    request = _profile_edit_request(
        ["Tôi muốn làm brand strategy cho nhà hàng Chuyện Ba Bữa Signature á"]
    )
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(request, handler)

    assert isinstance(result, ToolMessage)
    assert handler_called is False
    assert "Cannot edit `/user/profile.md` from a sparse first turn" in str(
        result.content
    )
    assert "tentative observations" in str(result.content)


def test_allows_explicit_first_turn_profile_fact() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    request = _profile_edit_request(
        ["Tôi là founder, ngân sách dự kiến khoảng 80 triệu cho launch."]
    )
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(request, handler)

    assert handler_called is True
    assert isinstance(result, ToolMessage)
    assert result.content == "ran"


def test_allows_profile_update_after_multiple_user_turns() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    request = _profile_edit_request(
        [
            "Tôi muốn làm brand strategy cho một nhà hàng.",
            "Tôi là founder, đang cần bản trình sếp tuần này.",
        ]
    )
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(request, handler)

    assert handler_called is True
    assert isinstance(result, ToolMessage)
    assert result.content == "ran"
