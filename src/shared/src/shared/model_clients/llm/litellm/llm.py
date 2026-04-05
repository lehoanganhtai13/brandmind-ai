"""
LiteLLM client that follows the same design pattern as BaseLLM.

Provides a unified interface for calling any LLM provider through
litellm's completion API. Supports sync/async and streaming.

Requires: litellm>=1.82.0,<1.82.7
"""

from typing import Any, Dict, List

import litellm as litellm_sdk

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
    An LLM client that implements the BaseLLM interface using LiteLLM's
    unified API for calling any LLM provider.

    This class provides a standardized way to perform synchronous and
    asynchronous completions, including streaming, across any provider
    supported by LiteLLM (OpenAI, Anthropic, Google, Cohere, etc.).

    Unlike OpenAI/Google backends which use provider-specific client
    instances, LiteLLM uses module-level functions with per-call parameters.
    This is by design — litellm normalizes the interface across providers.
    """

    def __init__(self, config: LiteLLMClientLLMConfig, **kwargs):
        self.config: LiteLLMClientLLMConfig
        super().__init__(config, **kwargs)

    def _initialize_llm(self, **kwargs) -> None:
        """
        Configure litellm module-level settings.

        Unlike OpenAI/Google backends, litellm uses module-level functions
        (litellm.completion) rather than client instances. Configuration is
        applied per-call via parameters built by _call_kwargs().
        """
        # Suppress litellm's verbose logging by default
        litellm_sdk.suppress_debug_info = True

    def _prepare_messages(self, prompt: str) -> List[Dict[str, str]]:
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
        messages: List[Dict[str, str]] = []
        if self.config.system_prompt:
            messages.append({"role": "system", "content": self.config.system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _call_kwargs(self) -> Dict[str, Any]:
        """
        Build common kwargs for litellm completion calls.

        Centralizes all configuration into a single dict passed to every
        litellm.completion/acompletion call. Only includes optional params
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
        call_kwargs = self._call_kwargs()
        call_kwargs.update(kwargs)
        try:
            response = litellm_sdk.completion(
                messages=messages,
                stream=False,
                **call_kwargs,
            )
            content = response.choices[0].message.content or ""
            return CompletionResponse(text=content)
        except Exception as e:
            raise CallServerLLMError(f"LiteLLM API call failed: {e!s}") from e

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
        call_kwargs = self._call_kwargs()
        call_kwargs.update(kwargs)
        try:
            stream = litellm_sdk.completion(
                messages=messages,
                stream=True,
                **call_kwargs,
            )
            full_text = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        full_text += delta
                        yield CompletionResponse(text=full_text, delta=delta)
        except Exception as e:
            raise CallServerLLMError(
                f"LiteLLM stream call failed: {e!s}"
            ) from e

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
        call_kwargs = self._call_kwargs()
        call_kwargs.update(kwargs)
        try:
            response = await litellm_sdk.acompletion(
                messages=messages,
                stream=False,
                **call_kwargs,
            )
            content = response.choices[0].message.content or ""
            return CompletionResponse(text=content)
        except Exception as e:
            raise CallServerLLMError(
                f"Async LiteLLM API call failed: {e!s}"
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
        call_kwargs = self._call_kwargs()
        call_kwargs.update(kwargs)
        try:
            stream = await litellm_sdk.acompletion(
                messages=messages,
                stream=True,
                **call_kwargs,
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
                f"Async LiteLLM stream call failed: {e!s}"
            ) from e
