"""Google Gemini chat model wrapper with BrandMind-safe retry behavior."""

from typing import Any, AsyncIterator

import google.genai.errors as genai_errors
from langchain_core.outputs import ChatGenerationChunk, ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class RetryableGeminiResponseError(RuntimeError):
    """Raised when Gemini returns a retryable response-level failure."""


def _has_malformed_function_call(result: ChatResult) -> bool:
    """Return whether Gemini ended with a malformed tool-call response.

    Gemini can return ``finish_reason="MALFORMED_FUNCTION_CALL"`` as a normal
    response instead of raising an API exception. In agent runs this produces an
    empty AIMessage with no tool calls, so the wrapper must convert it into a
    retryable error before the agent treats the turn as complete.
    """
    for generation in result.generations:
        generation_info = getattr(generation, "generation_info", {}) or {}
        if generation_info.get("finish_reason") == "MALFORMED_FUNCTION_CALL":
            return True
        message = getattr(generation, "message", None)
        metadata = getattr(message, "response_metadata", {}) or {}
        if metadata.get("finish_reason") == "MALFORMED_FUNCTION_CALL":
            return True
    return False


def _message_has_payload(message: Any) -> bool:
    """Return whether a generated message has content or tool intent."""
    content = getattr(message, "content", "")
    if content:
        return True
    if getattr(message, "tool_call_chunks", None):
        return True
    return bool(getattr(message, "tool_calls", None))


def _has_empty_terminal_response(result: ChatResult) -> bool:
    """Return whether Gemini produced no content and no tool calls."""
    return not any(
        _message_has_payload(getattr(generation, "message", None))
        for generation in result.generations
    )


def _chunk_has_payload(chunk: ChatGenerationChunk) -> bool:
    """Return whether a streaming chunk contains usable user-visible payload."""
    message = getattr(chunk, "message", None)
    content = getattr(message, "content", "")
    if content:
        return True
    if getattr(message, "tool_call_chunks", None):
        return True
    return bool(getattr(message, "tool_calls", None))


def _chunks_have_malformed_function_call(
    chunks: list[ChatGenerationChunk],
) -> bool:
    """Return whether buffered chunks ended with a malformed tool-call response."""
    for chunk in chunks:
        message = getattr(chunk, "message", None)
        metadata = getattr(message, "response_metadata", {}) or {}
        if metadata.get("finish_reason") == "MALFORMED_FUNCTION_CALL":
            return True
    return False


class RetryChatGoogleGenerativeAI(ChatGoogleGenerativeAI):
    """A wrapper around ChatGoogleGenerativeAI that natively retries on
    Google GenAI SDK ServerError (503) and APIError without obscuring
    BaseChatModel methods like bind_tools or _llm_type, which happens
    when using LangChain's Runnable.with_retry().
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    async def _astream(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        async for attempt in AsyncRetrying(
            wait=wait_exponential(multiplier=1, min=2, max=10),
            stop=stop_after_attempt(5),
            retry=retry_if_exception_type(
                (
                    genai_errors.ServerError,
                    genai_errors.APIError,
                    RetryableGeminiResponseError,
                )
            ),
            reraise=True,
        ):
            with attempt:
                buffered_chunks: list[ChatGenerationChunk] = []
                payload_started = False
                parent_stream = super()._astream(*args, **kwargs)
                async for chunk in parent_stream:
                    if payload_started:
                        yield chunk
                        continue

                    buffered_chunks.append(chunk)
                    if _chunk_has_payload(chunk):
                        payload_started = True
                        for buffered_chunk in buffered_chunks:
                            yield buffered_chunk
                        buffered_chunks.clear()

                if not payload_started and _chunks_have_malformed_function_call(
                    buffered_chunks
                ):
                    raise RetryableGeminiResponseError(
                        "Gemini returned MALFORMED_FUNCTION_CALL"
                    )

                for buffered_chunk in buffered_chunks:
                    yield buffered_chunk

    async def _agenerate(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> ChatResult:
        async for attempt in AsyncRetrying(
            wait=wait_exponential(multiplier=1, min=2, max=10),
            stop=stop_after_attempt(5),
            retry=retry_if_exception_type(
                (
                    genai_errors.ServerError,
                    genai_errors.APIError,
                    RetryableGeminiResponseError,
                )
            ),
            reraise=True,
        ):
            with attempt:
                result = await super()._agenerate(*args, **kwargs)
                if _has_malformed_function_call(result):
                    raise RetryableGeminiResponseError(
                        "Gemini returned MALFORMED_FUNCTION_CALL"
                    )
                if _has_empty_terminal_response(result):
                    raise RetryableGeminiResponseError(
                        "Gemini returned empty response without content or tool calls"
                    )
                return result

        # Unreachable: tenacity reraise=True guarantees an exception is raised
        # after all attempts are exhausted. This satisfies the type checker.
        raise RuntimeError("All retry attempts exhausted without returning")
