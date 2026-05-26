"""Tests for model-authored progress-update guarding."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain.agents.middleware.types import ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from core.brand_strategy.progress_updates import NaturalProgressUpdateMiddleware


def _request(messages: list[object]) -> ModelRequest:
    """Build a minimal model request for middleware tests."""
    return ModelRequest(
        model=MagicMock(),
        messages=messages,
        state={},
    )


def _response(tool_names: list[str]) -> ModelResponse:
    """Build a model response with the requested tool calls."""
    return ModelResponse(
        result=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": name,
                        "args": {},
                        "id": f"call-{index}",
                    }
                    for index, name in enumerate(tool_names)
                ],
            )
        ]
    )


def test_retries_expensive_first_turn_tool_chain_with_progress_reminder() -> None:
    """Expensive opening work should be replaced by a progress-tool call."""
    middleware = NaturalProgressUpdateMiddleware()
    request = _request([HumanMessage(content="Làm giúp tôi một proposal đầy đủ.")])
    initial = _response(["task"])
    progress = _response(["share_progress_update"])
    calls: list[ModelRequest] = []

    def handler(model_request: ModelRequest) -> ModelResponse:
        calls.append(model_request)
        return initial if len(calls) == 1 else progress

    result = middleware.wrap_model_call(request, handler)

    assert result is progress
    assert len(calls) == 2
    assert any(
        isinstance(message, SystemMessage)
        and "`share_progress_update(message=...)` once" in str(message.content)
        for message in calls[1].messages
    )


def test_does_not_retry_routine_first_turn_workspace_chain() -> None:
    """Routine reads should not create a status-report style progress line."""
    middleware = NaturalProgressUpdateMiddleware()
    request = _request([HumanMessage(content="Em đang làm brand mới.")])
    response = _response(["ls", "read_file", "search_knowledge_graph"])
    calls = 0

    def handler(model_request: ModelRequest) -> ModelResponse:
        nonlocal calls
        calls += 1
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert calls == 1


def test_does_not_retry_when_model_already_authors_progress_tool() -> None:
    """A model-authored progress call is already the desired behavior."""
    middleware = NaturalProgressUpdateMiddleware()
    request = _request([HumanMessage(content="Tạo file chiến lược giúp tôi.")])
    progress = _response(["share_progress_update"])
    calls = 0

    def handler(model_request: ModelRequest) -> ModelResponse:
        nonlocal calls
        calls += 1
        return progress

    result = middleware.wrap_model_call(request, handler)

    assert result is progress
    assert calls == 1


def test_does_not_retry_after_tool_results_inside_same_turn() -> None:
    """Only the first model call of the user turn is guarded."""
    middleware = NaturalProgressUpdateMiddleware()
    request = _request(
        [
            HumanMessage(content="Xem lại workspace rồi làm tiếp."),
            AIMessage(
                content="",
                tool_calls=[{"name": "read_file", "args": {}, "id": "call-read"}],
            ),
            ToolMessage(content="workspace text", tool_call_id="call-read"),
        ]
    )
    response = _response(["search_knowledge_graph"])
    calls = 0

    def handler(model_request: ModelRequest) -> ModelResponse:
        nonlocal calls
        calls += 1
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert calls == 1


@pytest.mark.asyncio
async def test_async_retry_matches_sync_behavior() -> None:
    """Async streaming agent calls should get the same progress guard."""
    middleware = NaturalProgressUpdateMiddleware()
    request = _request([HumanMessage(content="Proceed và tạo artifacts luôn.")])
    initial = _response(["task"])
    progress = _response(["share_progress_update"])
    calls: list[ModelRequest] = []

    async def handler(model_request: ModelRequest) -> ModelResponse:
        calls.append(model_request)
        return initial if len(calls) == 1 else progress

    result = await middleware.awrap_model_call(request, handler)

    assert result is progress
    assert len(calls) == 2
