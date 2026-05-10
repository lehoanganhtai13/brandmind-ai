"""Reference-based answer judging for knowledge-search comparison runs."""

from __future__ import annotations

import json
import re
from typing import Protocol

from evaluation.hipporag_comparison.benchmark_schema import BenchmarkItem
from evaluation.knowledge_search_comparison.prompts import (
    JUDGE_SYSTEM_INSTRUCTION,
    build_judge_prompt,
)
from evaluation.knowledge_search_comparison.schemas import AnswerJudgeResult


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
