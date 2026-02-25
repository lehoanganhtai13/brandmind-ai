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


class RetryChatGoogleGenerativeAI(ChatGoogleGenerativeAI):
    """
    A wrapper around ChatGoogleGenerativeAI that natively retries on
    Google GenAI SDK ServerError (503) and APIError without obscuring
    BaseChatModel methods like bind_tools or _llm_type, which happens
    when using LangChain's Runnable.with_retry().
    """

    async def _astream(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        async for attempt in AsyncRetrying(
            wait=wait_exponential(multiplier=1, min=2, max=10),
            stop=stop_after_attempt(5),
            retry=retry_if_exception_type(
                (genai_errors.ServerError, genai_errors.APIError)
            ),
            reraise=True,
        ):
            with attempt:
                parent_stream = super()._astream(*args, **kwargs)
                async for chunk in parent_stream:
                    yield chunk

    async def _agenerate(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> ChatResult:
        async for attempt in AsyncRetrying(
            wait=wait_exponential(multiplier=1, min=2, max=10),
            stop=stop_after_attempt(5),
            retry=retry_if_exception_type(
                (genai_errors.ServerError, genai_errors.APIError)
            ),
            reraise=True,
        ):
            with attempt:
                return await super()._agenerate(*args, **kwargs)

        # Unreachable: tenacity reraise=True guarantees an exception is raised
        # after all attempts are exhausted. This satisfies the type checker.
        raise RuntimeError("All retry attempts exhausted without returning")
