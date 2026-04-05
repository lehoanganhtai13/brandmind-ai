"""E2E tests for LiteLLM backend (Task 53, Tests 8-10).

Requires a live litellm proxy with LITELLM_PROXY_URL and LITELLM_API_KEY
configured in environments/.env.

Run: uv run pytest tests/integration/test_litellm_e2e.py -v
"""

import asyncio

import pytest

from config.system_config import SETTINGS
from shared.model_clients.llm.base_class import CompletionResponse
from shared.model_clients.llm.litellm.config import LiteLLMClientLLMConfig
from shared.model_clients.llm.litellm.llm import LiteLLMClientLLM

# Skip all tests if proxy not configured
pytestmark = pytest.mark.skipif(
    not SETTINGS.LITELLM_PROXY_URL or not SETTINGS.LITELLM_API_KEY,
    reason="LITELLM_PROXY_URL and LITELLM_API_KEY required for E2E tests",
)


JUDGE_MODELS = [
    "claude-sonnet-4-6",
    "gemini/gemini-3.1-pro-preview",
    "gpt-5.4",
]


def _make_llm(model: str = JUDGE_MODELS[0]) -> LiteLLMClientLLM:
    """Create a LiteLLMClientLLM with default proxy config."""
    config = LiteLLMClientLLMConfig(model=model)
    return LiteLLMClientLLM(config)


# ── Test 8: Sync Completion — E2E ────────────────────────────────────


class TestSyncCompletionE2E:
    """Test 8: Full sync completion with real proxy."""

    def test_sync_complete(self):
        llm = _make_llm()
        response = llm.complete("Say hello in one word.")
        assert isinstance(response, CompletionResponse)
        assert len(response.text) > 0
        print(f"Response: {response.text[:100]}")


# ── Test 9: Async Completion — E2E ───────────────────────────────────


class TestAsyncCompletionE2E:
    """Test 9: Async completion with real proxy."""

    def test_async_complete(self):
        llm = _make_llm()
        response = asyncio.get_event_loop().run_until_complete(
            llm.acomplete("Say hello in one word.")
        )
        assert isinstance(response, CompletionResponse)
        assert len(response.text) > 0
        print(f"Response: {response.text[:100]}")


# ── Test 10: 3 Judge Models via Proxy ────────────────────────────────


class TestJudgeModelsE2E:
    """Test 10: All 3 eval judge models work through proxy."""

    def test_claude_sonnet(self):
        llm = _make_llm("claude-sonnet-4-6")
        response = llm.complete("Reply with exactly one word: hello")
        assert isinstance(response, CompletionResponse)
        assert len(response.text) > 0
        print(f"Claude Sonnet 4.6: {response.text[:100]}")

    def test_gemini_pro(self):
        llm = _make_llm("gemini/gemini-3.1-pro-preview")
        response = llm.complete("Reply with exactly one word: hello")
        assert isinstance(response, CompletionResponse)
        assert len(response.text) > 0
        print(f"Gemini 3.1 Pro: {response.text[:100]}")

    def test_gpt(self):
        llm = _make_llm("gpt-5.4")
        response = llm.complete("Reply with exactly one word: hello")
        assert isinstance(response, CompletionResponse)
        assert len(response.text) > 0
        print(f"GPT 5.4: {response.text[:100]}")
