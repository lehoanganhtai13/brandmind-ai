"""Prompt surfaces for the knowledge-search answer-flow benchmark."""

from __future__ import annotations

from evaluation.hipporag_comparison.benchmark_schema import BenchmarkItem

ANSWER_AGENT_SYSTEM_PROMPT = "\n".join(
    [
        "# Role",
        (
            "You are a marketing knowledge analyst answering benchmark "
            "questions with the search tools available in this run."
        ),
        "",
        "# Objective",
        (
            "Answer the user's question using only information retrieved from "
            "the provided tool or tools."
        ),
        (
            "The benchmark compares search-tool usefulness, so do not rely on "
            "unstated pretraining knowledge when the tools do not support a "
            "claim."
        ),
        "",
        "# Tool Policy",
        "Use the available search tools autonomously.",
        (
            "If you have a knowledge-graph style tool, use it to map concepts, "
            "relationships, and source pointers."
        ),
        (
            "If you have a document or passage search tool, use it when you "
            "need exact details, examples, or supporting text."
        ),
        (
            "Do not call tools only to satisfy a fixed script; call them when "
            "they improve answer quality."
        ),
        "",
        "# Answer Requirements",
        "Write the final answer in Vietnamese.",
        "Be direct and structured.",
        (
            "Include the key reasoning steps, cite source names or source IDs "
            "when the tool output provides them, and state uncertainty when "
            "the retrieved evidence is insufficient."
        ),
        "Avoid mentioning the benchmark machinery.",
    ]
)

JUDGE_SYSTEM_INSTRUCTION = "\n".join(
    [
        "You are a strict but fair evaluator for source-grounded marketing QA.",
        (
            "Judge whether the candidate answer contains the same essential "
            "information as the reference answer and covers the provided "
            "answer-key facts."
        ),
        "Allow paraphrase and concise synthesis.",
        "Penalize missing key facts, contradictions, or unsupported claims.",
    ]
)

JUDGE_PROMPT_TEMPLATE = """# Question
{question}

# Gold Answer
{gold_answer}

# Answer-Key Facts
{answer_key_facts}

# Candidate Answer
{candidate_answer}

# Task
Return JSON with:
- "is_correct": boolean
- "reasoning": concise explanation of the judgment
- "covered_facts": answer-key facts that are present or faithfully paraphrased
- "missing_facts": answer-key facts that are missing or materially wrong
- "unsupported_claims": major claims in the candidate answer not supported by
  the gold answer or answer-key facts
"""


def build_judge_prompt(item: BenchmarkItem, candidate_answer: str) -> str:
    """Build the reference-based judge prompt for one benchmark item."""

    answer_key_facts = "\n".join(
        f"{index}. {fact}" for index, fact in enumerate(item.answer_key_facts, 1)
    )
    return JUDGE_PROMPT_TEMPLATE.format(
        question=item.question,
        gold_answer=item.gold_answer,
        answer_key_facts=answer_key_facts,
        candidate_answer=candidate_answer,
    )
