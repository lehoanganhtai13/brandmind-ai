from typing import Any, List

from openai import APIError, AsyncOpenAI, OpenAI
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
from shared.model_clients.llm.openai.config import OpenAIClientLLMConfig


class OpenAIClientLLM(BaseLLM):
    """
    An LLM client that implements the BaseLLM interface for OpenAI and compatible APIs.

    This class provides a standardized, simplified, and robust way to perform
    synchronous and asynchronous completions, including streaming. It is designed
    for enterprise use, ensuring efficient client management and clear error handling.
    """

    def __init__(self, config: OpenAIClientLLMConfig, **kwargs):
        self.config: OpenAIClientLLMConfig
        super().__init__(config, **kwargs)

    def _initialize_llm(self, **kwargs) -> None:
        """
        Initializes the synchronous and asynchronous OpenAI clients.
        This method is called once during instantiation to set up the clients
        for reuse, which is more efficient than creating them on each call.
        """
        self._sync_client = OpenAI(
            api_key=self.config.api_key, base_url=self.config.base_url
        )
        self._async_client = AsyncOpenAI(
            api_key=self.config.api_key, base_url=self.config.base_url
        )

    def _prepare_messages(self, prompt: str) -> List[ChatCompletionMessageParam]:
        """
        Constructs the message payload for the API call.

        Args:
            prompt (str): The user-provided prompt.

        Returns:
            messages (List[ChatCompletionMessageParam]): A list of typed message objects
            in the format required by the OpenAI API.
        """
        messages: List[ChatCompletionMessageParam] = []
        if self.config.system_prompt:
            messages.append(
                ChatCompletionSystemMessageParam(
                    role="system", content=self.config.system_prompt
                )
            )
        messages.append(ChatCompletionUserMessageParam(role="user", content=prompt))
        return messages

    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """
        Generates a single, non-streaming completion response synchronously.
        """
        messages = self._prepare_messages(prompt)
        try:
            response = self._sync_client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=False,
                **kwargs,  # Allow overriding defaults
            )
            content = response.choices[0].message.content or ""
            return CompletionResponse(text=content)
        except APIError as e:
            raise CallServerLLMError(f"OpenAI API call failed: {e!s}") from e

    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        """
        Generates a streaming completion response synchronously.
        """
        messages = self._prepare_messages(prompt)
        try:
            stream = self._sync_client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
                **kwargs,  # Allow overriding defaults
            )

            full_text = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        full_text += delta
                        yield CompletionResponse(text=full_text, delta=delta)
        except APIError as e:
            raise CallServerLLMError(f"OpenAI API stream call failed: {e!s}") from e

    async def acomplete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """
        Generates a single, non-streaming completion response asynchronously.
        """
        messages = self._prepare_messages(prompt)
        try:
            response = await self._async_client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=False,
                **kwargs,  # Allow overriding defaults
            )
            content = response.choices[0].message.content or ""
            return CompletionResponse(text=content)
        except APIError as e:
            raise CallServerLLMError(f"Async OpenAI API call failed: {e!s}") from e

    async def astream_complete(  # type: ignore[override]
        self, prompt: str, **kwargs: Any
    ) -> CompletionResponseAsyncGen:
        """
        Generates a streaming completion response asynchronously.
        """
        messages = self._prepare_messages(prompt)
        try:
            stream = await self._async_client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
                **kwargs,  # Allow overriding defaults
            )

            full_text = ""
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        full_text += delta
                        yield CompletionResponse(text=full_text, delta=delta)
        except APIError as e:
            raise CallServerLLMError(
                f"Async OpenAI API stream call failed: {e!s}"
            ) from e
