"""Unit tests for the natural working-note checkpoint middleware."""

from __future__ import annotations

from collections.abc import MutableMapping

from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.messages import HumanMessage, ToolMessage

from core.brand_strategy.session import BrandStrategySession, set_active_session
from core.brand_strategy.working_notes import WorkingNoteCheckpointMiddleware


def _request(
    tool_name: str,
    *,
    state: MutableMapping[str, object] | None = None,
    call_id: str = "call_1",
) -> ToolCallRequest:
    """Build a minimal tool-call request for checkpoint tests."""
    return ToolCallRequest(
        tool_call={
            "name": tool_name,
            "args": {},
            "id": call_id,
        },
        tool=None,
        state=state
        or {
            "messages": [
                HumanMessage(content="Owner không muốn giảm giá sâu."),
            ],
        },
        runtime=None,  # type: ignore[arg-type]
    )


def _handler(request: ToolCallRequest) -> ToolMessage:
    """Return a normal tool result for requests that pass the checkpoint."""
    return ToolMessage(content="ran", tool_call_id=str(request.tool_call["id"]))


def test_first_hidden_tool_returns_internal_checkpoint() -> None:
    """The first hidden tool is paused before user-visible work continues."""
    middleware = WorkingNoteCheckpointMiddleware()
    state: MutableMapping[str, object] = {
        "messages": [HumanMessage(content="Owner không muốn giảm giá sâu.")]
    }

    result = middleware.wrap_tool_call(_request("read_file", state=state), _handler)

    assert isinstance(result, ToolMessage)
    assert "NCWN_WORKING_NOTE_CHECKPOINT" in str(result.content)
    assert "share_working_note" in str(result.content)
    assert "assumption risk" in str(result.content)
    assert result.tool_call_id == "call_1"


def test_retry_after_model_sees_checkpoint_allows_hidden_tool() -> None:
    """The checkpoint is advisory; retrying the tool after seeing it proceeds."""
    middleware = WorkingNoteCheckpointMiddleware()
    messages: list[object] = [HumanMessage(content="Owner không muốn giảm giá sâu.")]
    state: MutableMapping[str, object] = {"messages": messages}
    first = middleware.wrap_tool_call(_request("read_file", state=state), _handler)
    messages.append(first)

    retry = middleware.wrap_tool_call(
        _request("read_file", state=state, call_id="call_2"),
        _handler,
    )

    assert isinstance(retry, ToolMessage)
    assert retry.content == "ran"
    assert retry.tool_call_id == "call_2"


def test_parallel_hidden_tool_before_model_sees_checkpoint_is_paused() -> None:
    """A second same-step hidden tool is also paused until the model reacts."""
    middleware = WorkingNoteCheckpointMiddleware()
    state: MutableMapping[str, object] = {
        "messages": [HumanMessage(content="Owner không muốn giảm giá sâu.")]
    }
    first = middleware.wrap_tool_call(_request("read_file", state=state), _handler)

    second = middleware.wrap_tool_call(
        _request("task", state=state, call_id="call_2"),
        _handler,
    )

    assert isinstance(first, ToolMessage)
    assert isinstance(second, ToolMessage)
    assert "NCWN_WORKING_NOTE_CHECKPOINT" in str(second.content)
    assert second.tool_call_id == "call_2"


def test_working_note_before_hidden_tool_bypasses_checkpoint() -> None:
    """A model-authored working note satisfies the checkpoint for that turn."""
    middleware = WorkingNoteCheckpointMiddleware()
    state: MutableMapping[str, object] = {
        "messages": [HumanMessage(content="Owner không muốn giảm giá sâu.")]
    }
    note_result = middleware.wrap_tool_call(
        _request("share_working_note", state=state),
        _handler,
    )

    hidden_result = middleware.wrap_tool_call(
        _request("read_file", state=state, call_id="call_2"),
        _handler,
    )

    assert isinstance(note_result, ToolMessage)
    assert note_result.content == "ran"
    assert isinstance(hidden_result, ToolMessage)
    assert hidden_result.content == "ran"


def test_report_progress_does_not_consume_checkpoint() -> None:
    """Quick session metadata updates do not count as hidden work."""
    middleware = WorkingNoteCheckpointMiddleware()
    state: MutableMapping[str, object] = {
        "messages": [HumanMessage(content="Chuyện Ba Bữa Signature.")]
    }

    report_result = middleware.wrap_tool_call(
        _request("report_progress", state=state),
        _handler,
    )
    hidden_result = middleware.wrap_tool_call(
        _request("read_file", state=state, call_id="call_2"),
        _handler,
    )

    assert isinstance(report_result, ToolMessage)
    assert report_result.content == "ran"
    assert isinstance(hidden_result, ToolMessage)
    assert "NCWN_WORKING_NOTE_CHECKPOINT" in str(hidden_result.content)


def test_checkpoint_resets_on_next_brand_strategy_turn() -> None:
    """Turn-scoped state lets the next user turn receive its own checkpoint."""
    middleware = WorkingNoteCheckpointMiddleware()
    session = BrandStrategySession(session_id="abc123")
    messages: list[object] = [HumanMessage(content="Owner không muốn giảm giá sâu.")]
    state: MutableMapping[str, object] = {"messages": messages}
    set_active_session(session)

    try:
        session.begin_user_turn()
        first = middleware.wrap_tool_call(_request("read_file", state=state), _handler)
        messages.append(first)
        retry = middleware.wrap_tool_call(
            _request("read_file", state=state, call_id="call_2"),
            _handler,
        )

        session.begin_user_turn()
        next_turn = middleware.wrap_tool_call(
            _request("read_file", state=state, call_id="call_3"),
            _handler,
        )
    finally:
        set_active_session(None)

    assert isinstance(first, ToolMessage)
    assert isinstance(retry, ToolMessage)
    assert retry.content == "ran"
    assert isinstance(next_turn, ToolMessage)
    assert "NCWN_WORKING_NOTE_CHECKPOINT" in str(next_turn.content)
