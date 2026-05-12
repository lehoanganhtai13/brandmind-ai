"""Unit tests for brand brief edit hygiene middleware."""

from __future__ import annotations

from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.messages import ToolMessage

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
