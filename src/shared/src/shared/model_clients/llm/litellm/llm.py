"""OpenAI-compatible client for calling a LiteLLM proxy."""

from typing import Any, Dict, List, cast

from openai import AsyncOpenAI, OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from shared.model_clients.llm.base_class import (
    CompletionResponse,
    CompletionResponseAsyncGen,
    CompletionResponseGen,
)
from shared.model_clients.llm.base_llm import BaseLLM
from shared.model_clients.llm.exceptions import CallServerLLMError
from shared.model_clients.llm.litellm.config import LiteLLMClientLLMConfig


class LiteLLMClientLLM(BaseLLM):
    """
    BaseLLM adapter for the local LiteLLM OpenAI-compatible proxy.

    The project uses LiteLLM as a hosted proxy, so this client talks to its
    `/v1` OpenAI-compatible endpoint through the official OpenAI SDK. That
    avoids installing the LiteLLM SDK inside the main app environment while
    preserving the same proxy routing behavior.
    """

    def __init__(self, config: LiteLLMClientLLMConfig, **kwargs):
        self.config: LiteLLMClientLLMConfig
        super().__init__(config, **kwargs)

    def _initialize_llm(self, **kwargs) -> None:
        """
        Initialize reusable OpenAI-compatible clients for the LiteLLM proxy.
        """
        self._sync_client = OpenAI(
            api_key=self.config.api_key,
            base_url=_normalize_litellm_base_url(self.config.base_url),
        )
        self._async_client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=_normalize_litellm_base_url(self.config.base_url),
        )

    def _prepare_messages(self, prompt: str) -> List[ChatCompletionMessageParam]:
        """
        Construct the message payload for the API call.

        Follows the same pattern as OpenAI backend's _prepare_messages(),
        building an OpenAI-compatible message list that litellm translates
        per provider.

        Args:
            prompt (str): The user-provided prompt.

        Returns:
            messages (List[Dict[str, str]]): Message list in OpenAI-compatible
                format with optional system message.
        """
        messages: List[ChatCompletionMessageParam] = []
        if self.config.system_prompt:
            messages.append(
                ChatCompletionSystemMessageParam(
                    role="system",
                    content=self.config.system_prompt,
                )
            )
        messages.append(ChatCompletionUserMessageParam(role="user", content=prompt))
        return messages

    def _call_kwargs(self) -> Dict[str, Any]:
        """
        Build common kwargs for LiteLLM proxy completion calls.

        Centralizes all configuration into a single dict passed to every
        completion call. Only includes optional params
        (api_key, api_base, response_format, reasoning_effort) when they
        are explicitly set — avoids sending None values to the API.

        Returns:
            kwargs (Dict[str, Any]): Keyword arguments for litellm calls.
        """
        kwargs: Dict[str, Any] = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if self.config.api_key:
            kwargs["api_key"] = self.config.api_key
        if self.config.base_url:
            kwargs["api_base"] = self.config.base_url
        if self.config.response_format:
            kwargs["response_format"] = self.config.response_format
        if self.config.reasoning_effort:
            kwargs["reasoning_effort"] = self.config.reasoning_effort
        return kwargs

    def _completion_kwargs(self) -> Dict[str, Any]:
        """
        Build request kwargs accepted by the OpenAI-compatible chat endpoint.

        Returns:
            Keyword arguments for ``chat.completions.create``.
        """
        kwargs = {
            key: value
            for key, value in self._call_kwargs().items()
            if key not in {"api_key", "api_base"}
        }
        return kwargs

    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """
        Generate a single, non-streaming completion response synchronously.

        Args:
            prompt (str): The input prompt to generate a response for.
            **kwargs: Additional parameters to override config defaults.

        Returns:
            CompletionResponse: The response containing the generated text.

        Raises:
            CallServerLLMError: If the API call fails.
        """
        messages = self._prepare_messages(prompt)
        call_kwargs = self._completion_kwargs()
        call_kwargs.update(kwargs)
        try:
            response = cast(
                Any,
                self._sync_client.chat.completions.create(
                    messages=messages,
                    stream=False,
                    **call_kwargs,
                ),
            )
            content = response.choices[0].message.content or ""
            return CompletionResponse(text=content)
        except Exception as e:
            raise CallServerLLMError(f"LiteLLM proxy API call failed: {e!s}") from e

    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        """
        Generate a streaming completion response synchronously.

        Args:
            prompt (str): The input prompt to generate a response for.
            **kwargs: Additional parameters to override config defaults.

        Yields:
            CompletionResponse: Incremental responses with full text and delta.

        Raises:
            CallServerLLMError: If the streaming call fails.
        """
        messages = self._prepare_messages(prompt)
        call_kwargs = self._completion_kwargs()
        call_kwargs.update(kwargs)
        try:
            stream = cast(
                Any,
                self._sync_client.chat.completions.create(
                    messages=messages,
                    stream=True,
                    **call_kwargs,
                ),
            )
            full_text = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        full_text += delta
                        yield CompletionResponse(text=full_text, delta=delta)
        except Exception as e:
            raise CallServerLLMError(f"LiteLLM proxy stream call failed: {e!s}") from e

    async def acomplete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """
        Generate a single, non-streaming completion response asynchronously.

        Args:
            prompt (str): The input prompt to generate a response for.
            **kwargs: Additional parameters to override config defaults.

        Returns:
            CompletionResponse: The response containing the generated text.

        Raises:
            CallServerLLMError: If the async API call fails.
        """
        messages = self._prepare_messages(prompt)
        call_kwargs = self._completion_kwargs()
        call_kwargs.update(kwargs)
        try:
            response = cast(
                Any,
                await self._async_client.chat.completions.create(
                    messages=messages,
                    stream=False,
                    **call_kwargs,
                ),
            )
            content = response.choices[0].message.content or ""
            return CompletionResponse(text=content)
        except Exception as e:
            raise CallServerLLMError(
                f"Async LiteLLM proxy API call failed: {e!s}"
            ) from e

    async def astream_complete(  # type: ignore[override]
        self, prompt: str, **kwargs: Any
    ) -> CompletionResponseAsyncGen:
        """
        Generate a streaming completion response asynchronously.

        Args:
            prompt (str): The input prompt to generate a response for.
            **kwargs: Additional parameters to override config defaults.

        Yields:
            CompletionResponse: Incremental responses with full text and delta.

        Raises:
            CallServerLLMError: If the async streaming call fails.
        """
        messages = self._prepare_messages(prompt)
        call_kwargs = self._completion_kwargs()
        call_kwargs.update(kwargs)
        try:
            stream = cast(
                Any,
                await self._async_client.chat.completions.create(
                    messages=messages,
                    stream=True,
                    **call_kwargs,
                ),
            )
            full_text = ""
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        full_text += delta
                        yield CompletionResponse(text=full_text, delta=delta)
        except Exception as e:
            raise CallServerLLMError(
                f"Async LiteLLM proxy stream call failed: {e!s}"
            ) from e


def _normalize_litellm_base_url(base_url: str | None) -> str | None:
    """
    Normalize a LiteLLM proxy root to its OpenAI-compatible `/v1` endpoint.

    Args:
        base_url: LiteLLM proxy root or OpenAI-compatible endpoint.

    Returns:
        Normalized base URL, or None when no proxy URL is configured.
    """
    if not base_url:
        return None
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1"
