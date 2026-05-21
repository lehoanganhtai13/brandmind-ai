"""Unit tests for Gemini retry behavior used by BrandMind agents."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI

from shared.agent_models.retry_gemini import RetryChatGoogleGenerativeAI


@pytest.mark.asyncio
async def test_agenerate_retries_malformed_function_call_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retry a Gemini response that contains no usable content or tool call."""
    malformed = ChatResult(
        generations=[
            ChatGeneration(
                message=AIMessage(
                    content="",
                ),
                generation_info={"finish_reason": "MALFORMED_FUNCTION_CALL"},
            )
        ]
    )
    success = ChatResult(
        generations=[
            ChatGeneration(
                message=AIMessage(
                    content="ok",
                    response_metadata={"finish_reason": "STOP"},
                )
            )
        ]
    )
    calls = 0

    async def fake_agenerate(
        self: ChatGoogleGenerativeAI,
        messages: list[BaseMessage],
        *args: Any,
        **kwargs: Any,
    ) -> ChatResult:
        nonlocal calls
        calls += 1
        return malformed if calls == 1 else success

    monkeypatch.setattr(ChatGoogleGenerativeAI, "_agenerate", fake_agenerate)
    model = RetryChatGoogleGenerativeAI(
        google_api_key="test-key",
        model="gemini-2.5-flash-lite",
    )

    result = await model._agenerate([HumanMessage(content="Build the DOCX")])

    assert result == success
    assert calls == 2


@pytest.mark.asyncio
async def test_agenerate_retries_empty_terminal_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retry a final Gemini message that has no content and no tool call."""
    empty = ChatResult(
        generations=[
            ChatGeneration(
                message=AIMessage(
                    content="",
                    response_metadata={"finish_reason": "STOP"},
                )
            )
        ]
    )
    success = ChatResult(
        generations=[
            ChatGeneration(
                message=AIMessage(
                    content="source ledger",
                    response_metadata={"finish_reason": "STOP"},
                )
            )
        ]
    )
    calls = 0

    async def fake_agenerate(
        self: ChatGoogleGenerativeAI,
        messages: list[BaseMessage],
        *args: Any,
        **kwargs: Any,
    ) -> ChatResult:
        nonlocal calls
        calls += 1
        return empty if calls == 1 else success

    monkeypatch.setattr(ChatGoogleGenerativeAI, "_agenerate", fake_agenerate)
    model = RetryChatGoogleGenerativeAI(
        google_api_key="test-key",
        model="gemini-2.5-flash-lite",
    )

    result = await model._agenerate([HumanMessage(content="Research this brand")])

    assert result == success
    assert calls == 2


@pytest.mark.asyncio
async def test_astream_retries_malformed_function_call_before_yield(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retry a malformed streaming response before exposing an empty AI chunk."""
    malformed = ChatGenerationChunk(
        message=AIMessageChunk(
            content="",
            response_metadata={"finish_reason": "MALFORMED_FUNCTION_CALL"},
        )
    )
    success = ChatGenerationChunk(
        message=AIMessageChunk(
            content="ok",
            response_metadata={"finish_reason": "STOP"},
        )
    )
    calls = 0

    async def fake_astream(
        self: ChatGoogleGenerativeAI,
        messages: list[BaseMessage],
        *args: Any,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        nonlocal calls
        calls += 1
        yield malformed if calls == 1 else success

    monkeypatch.setattr(ChatGoogleGenerativeAI, "_astream", fake_astream)
    model = RetryChatGoogleGenerativeAI(
        google_api_key="test-key",
        model="gemini-2.5-flash-lite",
    )

    chunks = [
        chunk
        async for chunk in model._astream([HumanMessage(content="Build the DOCX")])
    ]

    assert [chunk.message.content for chunk in chunks] == ["ok"]
    assert calls == 2
