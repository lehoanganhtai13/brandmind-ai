"""Reference-based answer judging for knowledge-search comparison runs."""

from __future__ import annotations

import json
import re
from typing import Any, Literal, Protocol

from evaluation.hipporag_comparison.benchmark_schema import BenchmarkItem
from evaluation.knowledge_search_comparison.prompts import (
    JUDGE_SYSTEM_INSTRUCTION,
    build_judge_prompt,
)
from evaluation.knowledge_search_comparison.schemas import (
    AnswerJudgeResult,
    ReasoningLevel,
)


class AnswerJudge(Protocol):
    """Protocol for answer judges used by the runner."""

    async def judge(
        self,
        *,
        item: BenchmarkItem,
        candidate_answer: str,
    ) -> AnswerJudgeResult:
        """Judge one final answer against one benchmark item."""


class GeminiAnswerJudge:
    """Gemini-backed judge using the project's structured LLM client."""

    def __init__(
        self,
        *,
        model: str = "gemini-2.5-flash",
        api_key: str | None = None,
        thinking_budget: int = 2000,
    ) -> None:
        """Initialize the judge without printing or storing secret values."""

        self.model = model
        self.api_key = api_key
        self.thinking_budget = thinking_budget

    async def judge(
        self,
        *,
        item: BenchmarkItem,
        candidate_answer: str,
    ) -> AnswerJudgeResult:
        """Judge one final answer against benchmark gold labels."""

        from config.system_config import SETTINGS
        from shared.model_clients.llm.google import (
            GoogleAIClientLLM,
            GoogleAIClientLLMConfig,
        )

        llm = GoogleAIClientLLM(
            config=GoogleAIClientLLMConfig(
                model=self.model,
                api_key=self.api_key or SETTINGS.GEMINI_API_KEY,
                system_instruction=JUDGE_SYSTEM_INSTRUCTION,
                temperature=0.0,
                max_tokens=3000,
                thinking_budget=self.thinking_budget,
                response_mime_type="application/json",
                response_schema=AnswerJudgeResult,
            )
        )
        response = await llm.acomplete(build_judge_prompt(item, candidate_answer))
        payload = parse_json_object(response.text)
        return AnswerJudgeResult.model_validate(payload)


class LiteLLMAnswerJudge:
    """LiteLLM-backed judge for evaluator-version comparison runs.

    This judge keeps the same reference-based prompt and output schema as the
    Gemini judge while routing through the local OpenAI-compatible LiteLLM proxy.
    It is intended for judge calibration and explicitly labeled evaluator runs,
    not as a silent replacement for the default Gemini judge.
    """

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        api_base: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 3000,
        reasoning_effort: ReasoningLevel | None = None,
    ) -> None:
        """Initialize the LiteLLM judge without exposing secret values.

        Args:
            model: LiteLLM model group or OpenAI-compatible model ID.
            api_key: Optional LiteLLM API key override.
            api_base: Optional LiteLLM proxy root or `/v1` base URL.
            temperature: Judge sampling temperature.
            max_tokens: Maximum completion tokens for the JSON judgment.
            reasoning_effort: Optional OpenAI-compatible reasoning effort.
        """

        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort

    async def judge(
        self,
        *,
        item: BenchmarkItem,
        candidate_answer: str,
    ) -> AnswerJudgeResult:
        """Judge one final answer through the LiteLLM proxy."""

        from openai import AsyncOpenAI

        from config.system_config import SETTINGS

        api_key = self.api_key or SETTINGS.LITELLM_API_KEY
        if not api_key:
            raise ValueError("LiteLLM judge provider requires LITELLM_API_KEY.")

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=litellm_openai_base_url(
                self.api_base or SETTINGS.LITELLM_PROXY_URL
            ),
        )
        request: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": JUDGE_SYSTEM_INSTRUCTION},
                {"role": "user", "content": build_judge_prompt(item, candidate_answer)},
            ],
            "temperature": self.temperature,
            "max_completion_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        if self.reasoning_effort:
            request["reasoning_effort"] = self.reasoning_effort

        response = await client.chat.completions.create(**request)
        raw_text = response.choices[0].message.content or ""
        payload = parse_json_object(raw_text)
        return AnswerJudgeResult.model_validate(payload)


class AnswerKeyFactJudge:
    """Deterministic fixture judge for tests and smoke dry-runs."""

    async def judge(
        self,
        *,
        item: BenchmarkItem,
        candidate_answer: str,
    ) -> AnswerJudgeResult:
        """Mark facts covered when their lowercase text appears verbatim."""

        normalized_answer = candidate_answer.lower()
        covered_facts = [
            fact for fact in item.answer_key_facts if fact.lower() in normalized_answer
        ]
        missing_facts = [
            fact for fact in item.answer_key_facts if fact not in covered_facts
        ]
        return AnswerJudgeResult(
            is_correct=not missing_facts,
            reasoning="Deterministic answer-key fact containment check.",
            covered_facts=covered_facts,
            missing_facts=missing_facts,
        )


def create_answer_judge(
    *,
    provider: Literal["gemini", "litellm"],
    model: str,
    temperature: float = 0.0,
    thinking_budget: int | None = 2000,
    thinking_level: ReasoningLevel | None = None,
) -> AnswerJudge:
    """Create the live answer judge for the configured provider.

    Args:
        provider: Normalized judge provider.
        model: Provider-specific judge model ID.
        temperature: Judge sampling temperature.
        thinking_budget: Gemini thinking-budget control.
        thinking_level: LiteLLM/OpenAI-compatible reasoning effort.

    Returns:
        A judge implementation that follows the shared `AnswerJudge` protocol.

    Raises:
        ValueError: If the provider is unsupported.
    """

    if provider == "gemini":
        return GeminiAnswerJudge(
            model=model,
            thinking_budget=thinking_budget or 0,
        )
    if provider == "litellm":
        return LiteLLMAnswerJudge(
            model=model,
            temperature=temperature,
            reasoning_effort=thinking_level,
        )
    raise ValueError(f"Unsupported judge provider: {provider}")


def parse_json_object(raw_text: str) -> dict[str, object]:
    """Parse a JSON object from plain or fenced LLM output."""

    text = raw_text.strip()
    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced_match:
        text = fenced_match.group(1)
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Expected judge output to be a JSON object.")
    return payload


def litellm_openai_base_url(raw_url: str | None) -> str:
    """Return the OpenAI-compatible `/v1` endpoint for the LiteLLM proxy."""

    base_url = (raw_url or "http://localhost:4000").rstrip("/")
    return base_url if base_url.endswith("/v1") else f"{base_url}/v1"
