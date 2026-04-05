"""Unit tests for LiteLLM backend (Task 53).

Tests config, message preparation, call kwargs, and error handling.
E2E tests (8-10) require a live proxy and are in tests/integration/.
"""

import pytest

from shared.model_clients.llm.base_class import CompletionResponse, LLMBackend
from shared.model_clients.llm.exceptions import CallServerLLMError
from shared.model_clients.llm.litellm.config import LiteLLMClientLLMConfig
from shared.model_clients.llm.litellm.llm import LiteLLMClientLLM


# ── Test 1: Config — Env Var Fallback ────────────────────────────────


class TestConfigEnvFallback:
    """Test 1: Config reads from SETTINGS when no explicit values provided."""

    def test_config_reads_settings(self):
        from config.system_config import SETTINGS

        config = LiteLLMClientLLMConfig()
        # Should fall back to SETTINGS values (may be empty string in test env)
        assert config.api_key == (SETTINGS.LITELLM_API_KEY or None)
        assert config.base_url == (SETTINGS.LITELLM_PROXY_URL or None)

    def test_config_backend_is_litellm(self):
        config = LiteLLMClientLLMConfig()
        assert config.backend == LLMBackend.LITELLM


# ── Test 2: Config — Explicit Override ───────────────────────────────


class TestConfigExplicitOverride:
    """Test 2: Explicit params override SETTINGS."""

    def test_explicit_values_take_priority(self):
        config = LiteLLMClientLLMConfig(
            api_key="explicit-key",
            base_url="http://explicit:4000",
        )
        assert config.api_key == "explicit-key"
        assert config.base_url == "http://explicit:4000"

    def test_default_values(self):
        config = LiteLLMClientLLMConfig(
            api_key="test", base_url="http://test"
        )
        assert config.model == "claude-sonnet-4-6"
        assert config.temperature == 0.1
        assert config.max_tokens == 4096
        assert config.reasoning_effort is None
        assert config.system_prompt is None
        assert config.response_format is None


# ── Test 3: Config — Reasoning Effort Included ───────────────────────


class TestReasoningEffortIncluded:
    """Test 3: reasoning_effort included in call kwargs when set."""

    def test_reasoning_effort_in_kwargs(self):
        config = LiteLLMClientLLMConfig(
            reasoning_effort="high",
            api_key="test",
            base_url="http://test",
        )
        llm = LiteLLMClientLLM(config)
        kwargs = llm._call_kwargs()
        assert kwargs["reasoning_effort"] == "high"


# ── Test 4: Config — Reasoning Effort None ───────────────────────────


class TestReasoningEffortNone:
    """Test 4: reasoning_effort NOT in kwargs when None."""

    def test_reasoning_effort_absent(self):
        config = LiteLLMClientLLMConfig(
            api_key="test",
            base_url="http://test",
        )
        llm = LiteLLMClientLLM(config)
        kwargs = llm._call_kwargs()
        assert "reasoning_effort" not in kwargs


# ── Test 5: Message Preparation — With System Prompt ─────────────────


class TestMessagePrepWithSystem:
    """Test 5: _prepare_messages includes system prompt."""

    def test_messages_with_system_prompt(self):
        config = LiteLLMClientLLMConfig(
            system_prompt="You are a judge.",
            api_key="test",
            base_url="http://test",
        )
        llm = LiteLLMClientLLM(config)
        messages = llm._prepare_messages("Evaluate this.")

        assert len(messages) == 2
        assert messages[0] == {"role": "system", "content": "You are a judge."}
        assert messages[1] == {"role": "user", "content": "Evaluate this."}


# ── Test 6: Message Preparation — Without System Prompt ──────────────


class TestMessagePrepWithoutSystem:
    """Test 6: _prepare_messages works without system prompt."""

    def test_messages_without_system_prompt(self):
        config = LiteLLMClientLLMConfig(
            api_key="test",
            base_url="http://test",
        )
        llm = LiteLLMClientLLM(config)
        messages = llm._prepare_messages("Hello")

        assert len(messages) == 1
        assert messages[0] == {"role": "user", "content": "Hello"}


# ── Test 7: Error Handling ───────────────────────────────────────────


class TestErrorHandling:
    """Test 7: litellm exceptions wrapped into CallServerLLMError."""

    def test_invalid_url_raises_custom_error(self):
        config = LiteLLMClientLLMConfig(
            model="fake-model",
            api_key="fake-key",
            base_url="http://nonexistent:9999",
        )
        llm = LiteLLMClientLLM(config)
        with pytest.raises(CallServerLLMError) as exc_info:
            llm.complete("test")
        # Original exception should be chained
        assert exc_info.value.__cause__ is not None


# ── Test 11: System Config — LITELLM fields ──────────────────────────


class TestSystemConfig:
    """Test 11: SETTINGS has LITELLM_PROXY_URL and LITELLM_API_KEY."""

    def test_settings_has_litellm_fields(self):
        from config.system_config import SETTINGS

        assert hasattr(SETTINGS, "LITELLM_PROXY_URL")
        assert hasattr(SETTINGS, "LITELLM_API_KEY")


# ── Call kwargs completeness ─────────────────────────────────────────


class TestCallKwargs:
    """Additional kwargs tests for completeness."""

    def test_api_key_included(self):
        config = LiteLLMClientLLMConfig(
            api_key="my-key", base_url="http://proxy"
        )
        llm = LiteLLMClientLLM(config)
        kwargs = llm._call_kwargs()
        assert kwargs["api_key"] == "my-key"
        assert kwargs["api_base"] == "http://proxy"

    def test_response_format_included(self):
        config = LiteLLMClientLLMConfig(
            api_key="test",
            base_url="http://test",
            response_format={"type": "json_object"},
        )
        llm = LiteLLMClientLLM(config)
        kwargs = llm._call_kwargs()
        assert kwargs["response_format"] == {"type": "json_object"}

    def test_optional_fields_excluded_when_none(self):
        config = LiteLLMClientLLMConfig(
            model="test-model",
            api_key="test",
            base_url="http://test",
        )
        llm = LiteLLMClientLLM(config)
        kwargs = llm._call_kwargs()
        assert "response_format" not in kwargs
        assert "reasoning_effort" not in kwargs
