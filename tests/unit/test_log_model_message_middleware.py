"""Unit tests for tool-result event logging middleware."""

from __future__ import annotations

import pytest
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest
from langgraph.types import Command

from shared.agent_middlewares.callback_types import BaseAgentEvent, ToolResultEvent
from shared.agent_middlewares.log_model_message import LogModelMessageMiddleware


def _tool_request() -> ToolCallRequest:
    return ToolCallRequest(
        tool_call={
            "name": "task",
            "args": {"subagent_type": "market-research"},
            "id": "call_research",
        },
        tool=None,
        state={},
        runtime=None,  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_command_wrapped_tool_message_emits_tool_result_event() -> None:
    events: list[BaseAgentEvent] = []
    middleware = LogModelMessageMiddleware(
        callback=events.append,
        log_thinking=False,
        log_text_response=False,
        log_tool_calls=False,
        log_tool_results=True,
    )

    async def handler(_request: ToolCallRequest) -> Command:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        "Public Fact: Signature exists.\nSource: Google Maps",
                        tool_call_id="call_research",
                    )
                ]
            }
        )

    result = await middleware.awrap_tool_call(_tool_request(), handler)

    assert isinstance(result, Command)
    tool_results = [event for event in events if isinstance(event, ToolResultEvent)]
    assert len(tool_results) == 1
    assert tool_results[0].tool_name == "task"
    assert tool_results[0].tool_call_id == "call_research"
    assert "Public Fact: Signature exists." in tool_results[0].result
