"""Unit tests for EnsureTasksFinishedMiddleware re-invocation duplication.

These tests cover the secondary duplicate-pass hypothesis that
``EnsureTasksFinishedMiddleware`` re-invokes the model handler when
the agent stops with incomplete todos, and that on each re-invocation
the model may emit additional user-facing text. With
``max_reminders=1`` (the configured production value in
``agent_config.py:304``), at most one extra invocation can fire — but
that single extra invocation IS sufficient to surface a Pass 2 if the
re-prompt template's wording does not forbid further user-facing
text.

The tests below isolate three assertions:

1. When the agent emits substantive text + tool calls, the middleware
   does **not** treat that as stopping — no re-invocation.
2. When the agent emits an empty response (truly stopping) and todos
   are incomplete, the middleware re-invokes once.
3. The re-prompt template content does not require user-facing text
   on the next invocation; if it does, the test asserts a regression
   so any future template change has to acknowledge the duplicate-pass
   risk.

These tests are scaffolds — they construct response objects against
the current ``ModelResponse`` shape but should be reviewed against
the live API at run time. An LLM is **not** invoked.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

from shared.agent_middlewares.stop_check.ensure_tasks_finished_middleware import (
    EnsureTasksFinishedMiddleware,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _model_response_with_text(text: str, tool_calls: list[Any] | None = None) -> Any:
    """Build a ``ModelResponse``-shaped stub carrying ``text``.

    Args:
        text: The string content for the synthetic AI message.
        tool_calls: Optional tool-call records to attach (controls
            whether the middleware classifies the response as
            stopping).

    Returns:
        A mock with a ``result`` attribute matching what the middleware
        introspects via ``response.result[-1]``.
    """
    ai_message = AIMessage(content=text)
    ai_message.tool_calls = tool_calls or []
    ai_message.additional_kwargs = {}
    ai_message.response_metadata = {"finish_reason": "STOP"} if not text else {}
    response = MagicMock()
    response.result = [ai_message]
    return response


def _request_with_todos(todos: list[dict[str, Any]]) -> Any:
    """Build a ``ModelRequest``-shaped stub exposing the given todos.

    Args:
        todos: The todo list under test. Empty list means no
            outstanding work; the middleware should not re-invoke when
            the agent stops in that case.

    Returns:
        A mock with ``state`` and ``messages`` attributes shaped for
        ``EnsureTasksFinishedMiddleware``.
    """
    request = MagicMock()
    request.state = {"todos": todos}
    request.messages = []
    return request


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_substantive_text_with_tool_calls_no_reinvocation() -> None:
    """Agent emits text + tool calls → middleware passes through once.

    This is the production-normal case. If this test fails — that is,
    handler is called more than once for a non-stopping response —
    the middleware is the duplicate-pass culprit.
    """
    middleware = EnsureTasksFinishedMiddleware(max_reminders=1)
    request = _request_with_todos([
        {"content": "task A", "status": "in_progress", "activeForm": "doing A", "priority": "high"}
    ])
    response = _model_response_with_text(
        "Pass 1 substantive text", tool_calls=[{"name": "write_todos", "args": {}, "id": "1"}]
    )
    handler = AsyncMock(return_value=response)

    result = await middleware.awrap_model_call(request, handler)

    assert handler.await_count == 1
    assert result is response


@pytest.mark.asyncio
async def test_empty_stop_with_pending_todos_triggers_one_reinvocation() -> None:
    """Empty AI text + STOP + incomplete todos → middleware re-invokes once.

    With ``max_reminders=1`` the middleware MUST cap re-invocations at
    one extra call. Any value greater than 2 total handler calls is
    a regression that compounds duplicate-pass risk.
    """
    middleware = EnsureTasksFinishedMiddleware(max_reminders=1)
    request = _request_with_todos([
        {
            "content": "complete artifact",
            "status": "in_progress",
            "activeForm": "completing artifact",
            "priority": "high",
        }
    ])

    stopping_response = _model_response_with_text("")
    recovered_response = _model_response_with_text("Pass 2 after reminder")

    handler = AsyncMock(side_effect=[stopping_response, recovered_response])

    result = await middleware.awrap_model_call(request, handler)

    assert handler.await_count <= 2, (
        "Re-invocation count exceeded max_reminders=1 budget. "
        "Each extra invocation may surface as a duplicate user-facing pass."
    )
    assert result is recovered_response


@pytest.mark.asyncio
async def test_reprompt_template_does_not_require_user_facing_text() -> None:
    """Pin: reprompt template currently requests continued WORK, not text.

    If a future change adds language asking the agent to "summarize
    progress to the user before continuing" or similar, that wording
    introduces a deterministic Pass 2. Assert the absence of such
    phrases so the regression is caught at unit-test time.
    """
    middleware = EnsureTasksFinishedMiddleware(max_reminders=1)
    template = middleware.re_prompt_template
    forbidden_phrases = (
        "summarize progress to the user",
        "report your progress to the user",
        "tell the user what you have done",
        "present the work so far to the user",
    )
    for phrase in forbidden_phrases:
        assert phrase.lower() not in template.lower(), (
            f"Reprompt template contains '{phrase}', which would deterministically "
            "produce a second user-facing text pass on re-invocation."
        )
