"""Configuration for the LiteLLM unified LLM client.

LiteLLM provides a single interface for calling any LLM provider
(OpenAI, Anthropic, Google, etc.) through a unified API or proxy.
"""

from typing import Optional

from shared.model_clients.llm.base_class import LLMBackend, LLMConfig


class LiteLLMClientLLMConfig(LLMConfig):
    """
    Configuration for the LiteLLM unified client.

    Supports calling any LLM provider through litellm's unified interface,
    either directly or via a litellm proxy server.

    Attributes:
        model (str):
            LiteLLM model identifier (e.g., "claude-sonnet-4-6",
            "gemini/gemini-3.1-pro", "gpt-5.4").
            Defaults to "claude-sonnet-4-6".
        api_key (str, optional):
            API key for the litellm proxy or direct provider.
            Falls back to SETTINGS.LITELLM_API_KEY if not provided.
        base_url (str, optional):
            Base URL of the litellm proxy server.
            Falls back to SETTINGS.LITELLM_PROXY_URL if not provided.
            If None, litellm routes directly to the provider using model prefix.
        temperature (float):
            Controls randomness. Lower values make the model more deterministic.
            Defaults to 0.1.
        max_tokens (int):
            The maximum number of tokens to generate in the completion.
            Defaults to 4096.
        reasoning_effort (str, optional):
            Controls reasoning depth for supported models.
            Values: "low", "medium", "high", or None (provider default).
            LiteLLM translates this per provider:
            - Anthropic: maps to thinking budget
            - OpenAI: maps to reasoning_effort
            - Google: maps to thinking_level
            Defaults to None.
        system_prompt (str, optional):
            A default system-level instruction for the model, applied to all
            requests. Defaults to None.
        response_format (dict, optional):
            Optional response format specification
            (e.g., {"type": "json_object"}).
            Defaults to None.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        reasoning_effort: Optional[str] = None,
        system_prompt: Optional[str] = None,
        response_format: Optional[dict] = None,
        **kwargs,
    ):
        super().__init__(backend=LLMBackend.LITELLM, **kwargs)
        self.model = model

        # Falls back to SETTINGS if not provided explicitly
        from config.system_config import SETTINGS

        self.api_key = api_key or SETTINGS.LITELLM_API_KEY or None
        self.base_url = base_url or SETTINGS.LITELLM_PROXY_URL or None

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.system_prompt = system_prompt
        self.response_format = response_format
