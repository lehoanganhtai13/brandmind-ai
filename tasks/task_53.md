# Task 53: LiteLLM Backend for Model Clients

## Metadata

- **Epic**: Quality Evaluation
- **Priority**: High
- **Status**: Done
- **Estimated Effort**: 0.5 day
- **Team**: Backend
- **Related Tasks**: Task 52 (judge pipeline uses this backend)
- **Blocking**: Task 52
- **Blocked by**: None

### Progress Checklist

- [x] Agent Protocol — Read and confirmed
- [x] Context & Goals
- [x] Solution Design
- [x] Pre-Implementation Research
- [x] Implementation Plan
- [x] Implementation Detail
    - [x] Component 1: LiteLLM Config
    - [x] Component 2: LiteLLM Client
- [x] Test Execution Log — All tests passed (unit + E2E)
- [x] Decision Log
- [x] Task Summary

## Reference Documentation

- **Base class**: `src/shared/src/shared/model_clients/llm/base_class.py`
- **Base LLM**: `src/shared/src/shared/model_clients/llm/base_llm.py`
- **OpenAI pattern**: `src/shared/src/shared/model_clients/llm/openai/` (follow this pattern)
- **Google pattern**: `src/shared/src/shared/model_clients/llm/google/`
- **LiteLLM docs**: https://docs.litellm.ai/

------------------------------------------------------------------------

## Agent Protocol

> **MANDATORY**: Read this section in full before starting.

### Rule 1 — Research Before Coding

1. Read base_class.py and base_llm.py to understand the interface
2. Read OpenAI implementation as the pattern to follow
3. Read litellm docs for completion/acompletion API
4. Log findings in Pre-Implementation Research

### Rule 2 — Ask, Don't Guess

### Rule 3 — Update Progress As You Go

### Rule 4 — Production-Grade Code Standards

All code: PEP 8, type hints, docstrings, double quotes. Follow exact patterns from OpenAI/Google implementations.

------------------------------------------------------------------------

## Context & Goals

### Boi canh

- `LLMBackend.LITELLM` enum already exists but has no implementation
- Judge pipeline (Task 52) needs to call 3 different model providers (Claude, Gemini, GPT)
- LiteLLM provides unified interface: one API call syntax for any provider
- User has litellm host URL and API key ready
- Need a proper backend following existing OpenAI/Google patterns, not a hack

### Muc tieu

Implement `LiteLLMClientLLM` backend following the same `BaseLLM` interface pattern as OpenAI and Google implementations. Supports sync/async completion and streaming via litellm's unified API.

### Success Metrics

- **Interface compliance**: Implements all 4 BaseLLM methods (complete, stream_complete, acomplete, astream_complete)
- **Pattern consistency**: Same code structure as OpenAI/Google backends
- **Provider-agnostic**: Any litellm-supported model works by changing model name
- **Config**: base_url + api_key configurable (user provides their litellm proxy)

------------------------------------------------------------------------

## Solution Design

### Architecture

```
model_clients/llm/
├── base_class.py          # LLMBackend.LITELLM already defined
├── base_llm.py
├── openai/                # Existing
├── google/                # Existing
└── litellm/               # NEW (this task)
    ├── __init__.py
    ├── config.py           # LiteLLMClientLLMConfig
    └── llm.py              # LiteLLMClientLLM
```

------------------------------------------------------------------------

## Pre-Implementation Research

### Codebase Audit

- **Files read**: base_class.py, base_llm.py, openai/config.py, openai/llm.py
- **Pattern**: Config class extends LLMConfig, LLM class extends BaseLLM, implements 4 methods
- **OpenAI pattern**: Creates sync + async clients in `_initialize_llm()`, `_prepare_messages()` helper, error handling with custom exception

### LiteLLM API

- **Sync**: `litellm.completion(model=..., messages=..., api_base=..., api_key=...)`
- **Async**: `await litellm.acompletion(model=..., messages=...)`
- **Streaming**: `litellm.completion(..., stream=True)` returns generator
- **Model naming**: `"claude-sonnet-4-6"`, `"gemini/gemini-3.1-pro"`, `"gpt-5.4"`
- **Proxy**: Set `api_base` to litellm proxy URL, `api_key` to proxy key

### Research Status

- [x] BaseLLM interface understood
- [x] OpenAI pattern analyzed
- [x] LiteLLM API confirmed
- [x] No unresolved ambiguities

------------------------------------------------------------------------

## Implementation Plan

### Phase 1: Config + Implementation

1. Create `litellm/config.py` following OpenAI config pattern
2. Create `litellm/llm.py` implementing all 4 BaseLLM methods
3. Create `litellm/__init__.py`
4. *Checkpoint: Unit test — complete + acomplete with litellm proxy*

------------------------------------------------------------------------

## Implementation Detail

### Component 1: LiteLLM Config

> Status: Pending

**Implementation**:

- `src/shared/src/shared/model_clients/llm/litellm/config.py`

```python
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
        model: LiteLLM model identifier (e.g., "claude-sonnet-4-6",
            "gemini/gemini-3.1-pro", "gpt-5.4").
        api_key: API key for the litellm proxy or direct provider.
        base_url: Base URL of the litellm proxy server. If None, litellm
            routes directly to the provider using the model prefix.
        temperature: Controls randomness. Defaults to 0.1.
        max_tokens: Maximum tokens to generate. Defaults to 4096.
        reasoning_effort: Controls reasoning depth for supported models.
            Values: "low", "medium", "high", or None (provider default).
            LiteLLM translates this per provider:
            - Anthropic: maps to thinking budget
            - OpenAI: maps to reasoning_effort
            - Google: maps to thinking_level
            Defaults to None.
        system_prompt: Default system-level instruction. Defaults to None.
        response_format: Optional response format (e.g., {"type": "json_object"}).
            Defaults to None.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        # Defaults read from environment if not provided explicitly
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
```

---

### Component 2: LiteLLM Client

> Status: Pending

**Implementation**:

- `src/shared/src/shared/model_clients/llm/litellm/llm.py`

```python
"""
LiteLLM client that follows the same design pattern as BaseLLM.

Provides a unified interface for calling any LLM provider through
litellm's completion API. Supports sync/async and streaming.

Requires: pip install litellm
"""

from typing import Any, Dict, List, Optional

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
    """

    def __init__(self, config: LiteLLMClientLLMConfig, **kwargs):
        self.config: LiteLLMClientLLMConfig
        super().__init__(config, **kwargs)

    def _initialize_llm(self, **kwargs) -> None:
        """
        Configure litellm settings.

        Unlike OpenAI/Google backends, litellm uses module-level functions
        (litellm.completion) rather than client instances. Configuration is
        applied per-call via parameters.
        """
        # Suppress litellm's verbose logging by default
        litellm_sdk.suppress_debug_info = True

    def _prepare_messages(self, prompt: str) -> List[Dict[str, str]]:
        """
        Construct the message payload for the API call.

        Args:
            prompt: The user-provided prompt.

        Returns:
            List of message dicts in OpenAI-compatible format.
        """
        messages: List[Dict[str, str]] = []
        if self.config.system_prompt:
            messages.append({"role": "system", "content": self.config.system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _call_kwargs(self) -> Dict[str, Any]:
        """Build common kwargs for litellm completion calls."""
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
        """Generate a single, non-streaming completion response synchronously."""
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
        """Generate a streaming completion response synchronously."""
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
        """Generate a single, non-streaming completion response asynchronously."""
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
        """Generate a streaming completion response asynchronously."""
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
```

- `src/shared/src/shared/model_clients/llm/litellm/__init__.py`

```python
from shared.model_clients.llm.litellm.config import LiteLLMClientLLMConfig
from shared.model_clients.llm.litellm.llm import LiteLLMClientLLM

__all__ = ["LiteLLMClientLLM", "LiteLLMClientLLMConfig"]
```

**Package dependency** — add via Makefile:

```bash
make add-shared PKG="litellm>=1.82.0,<1.82.7"
```

**Environment variables** — already defined in `environments/.template.env`:
- `LITELLM_PROXY_URL` — LiteLLM proxy server URL
- `LITELLM_API_KEY` — API key for the proxy

Config reads from these env vars by default (see `LiteLLMClientLLMConfig`).

**Acceptance Criteria**:
- [ ] Implements all 4 BaseLLM methods: complete, stream_complete, acomplete, astream_complete
- [ ] Config accepts model, api_key, base_url, temperature, max_tokens, reasoning_effort, system_prompt, response_format
- [ ] Follows exact same code structure as OpenAI backend
- [ ] Error handling wraps litellm exceptions into CallServerLLMError
- [ ] Works with litellm proxy (base_url + api_key) and direct provider routing
- [ ] reasoning_effort passed through to litellm (translates per provider automatically)
- [ ] `litellm` added to `src/shared/pyproject.toml` dependencies

------------------------------------------------------------------------

## Test Execution Log

### Test 1: Config — Env Var Fallback

- **Purpose**: Verify config reads from SETTINGS when no explicit values provided
- **Expected**: Config reads from SETTINGS
- **Actual Result**: PASSED — config.api_key and config.base_url match SETTINGS values
- **Status**: Passed

### Test 2: Config — Explicit Override

- **Purpose**: Verify explicit params override SETTINGS
- **Expected**: Explicit values take priority
- **Actual Result**: PASSED — explicit api_key="explicit-key" and base_url="http://explicit:4000" used instead of SETTINGS
- **Status**: Passed

### Test 3: Config — Reasoning Effort Included

- **Purpose**: Verify reasoning_effort is included in call kwargs when set
- **Expected**: reasoning_effort present in kwargs
- **Actual Result**: PASSED — kwargs["reasoning_effort"] == "high"
- **Status**: Passed

### Test 4: Config — Reasoning Effort None

- **Purpose**: Verify reasoning_effort NOT in kwargs when None
- **Expected**: reasoning_effort absent from kwargs
- **Actual Result**: PASSED — "reasoning_effort" not in kwargs
- **Status**: Passed

### Test 5: Message Preparation — With System Prompt

- **Purpose**: Verify _prepare_messages includes system prompt
- **Expected**: 2 messages: system + user
- **Actual Result**: PASSED — messages[0]=system, messages[1]=user
- **Status**: Passed

### Test 6: Message Preparation — Without System Prompt

- **Purpose**: Verify _prepare_messages works without system prompt
- **Expected**: 1 message: user only
- **Actual Result**: PASSED — len(messages)==1, messages[0]=user
- **Status**: Passed

### Test 7: Error Handling

- **Purpose**: Verify litellm exceptions wrapped into CallServerLLMError
- **Expected**: CallServerLLMError raised with cause
- **Actual Result**: PASSED — CallServerLLMError raised, __cause__ is not None
- **Status**: Passed

### Test 8: Sync Completion — E2E

- **Purpose**: Verify full sync completion works with real proxy
- **Expected**: Non-empty CompletionResponse
- **Actual Result**: PASSED — response.text = "Hello!"
- **Status**: Passed

### Test 9: Async Completion — E2E

- **Purpose**: Verify async completion works
- **Expected**: Non-empty CompletionResponse
- **Actual Result**: PASSED — response.text = "Hello!"
- **Status**: Passed

### Test 10: 3 Judge Models via Proxy

- **Purpose**: Verify all 3 eval judge models work through proxy
- **Expected**: All 3 return non-empty responses
- **Actual Result**: PASSED — claude-sonnet-4-6: "hello", gemini/gemini-3.1-pro-preview: "hello", gpt-5.4: "hello"
- **Status**: Passed

### Test 11: System Config — LITELLM fields

- **Purpose**: Verify SETTINGS has LITELLM_PROXY_URL and LITELLM_API_KEY
- **Expected**: Both attributes exist
- **Actual Result**: PASSED — both hasattr checks true
- **Status**: Passed

### Regression Check

- **Purpose**: Verify no existing tests broken
- **Actual Result**: 427 passed, 1 skipped, 0 failures
- **Status**: Passed

------------------------------------------------------------------------

## Decision Log

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | Client pattern | Instance-based (like OpenAI) vs module-level (litellm native) | Module-level with per-call params | litellm uses module-level functions, not client instances. _call_kwargs() centralizes config. |
| 2 | Import alias | `import litellm` vs `from litellm import completion` | `import litellm as litellm_sdk` | Avoid name collision with our module directory name |

------------------------------------------------------------------------

## Task Summary

### What Was Implemented

**Components Completed**:
- [x] **LiteLLMClientLLMConfig**: Config class with env var fallback (SETTINGS), reasoning_effort, response_format
- [x] **LiteLLMClientLLM**: Full BaseLLM implementation — complete, stream_complete, acomplete, astream_complete
- [x] **System config**: LITELLM_PROXY_URL + LITELLM_API_KEY added to SETTINGS, .template.env, setup_env.sh

**Files Created / Modified**:
```
src/shared/src/shared/model_clients/llm/litellm/
├── __init__.py                    # Package exports
├── config.py                      # LiteLLMClientLLMConfig
└── llm.py                         # LiteLLMClientLLM

src/config/system_config.py        # Added LITELLM_PROXY_URL, LITELLM_API_KEY
environments/.template.env         # Added LITELLM env vars
scripts/setup_env.sh               # Added LiteLLM section
src/shared/pyproject.toml          # Added litellm>=1.82.0,<1.82.7

tests/unit/test_litellm_backend.py           # 13 unit tests
tests/integration/test_litellm_e2e.py        # 5 E2E tests
```

**Validation Results**:
- Unit tests: 13/13 passed
- E2E tests: 5/5 passed (claude-sonnet-4-6, gemini-3.1-pro-preview, gpt-5.4)
- mypy: 0 errors (122 files checked)
- Regression: 427 existing tests still pass
