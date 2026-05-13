"""Prompt surfaces for the knowledge-search answer-flow benchmark."""

from __future__ import annotations

from evaluation.hipporag_comparison.benchmark_schema import BenchmarkItem
from evaluation.knowledge_search_comparison.schemas import ComparisonSystem

COMMON_ANSWER_AGENT_SYSTEM_PROMPT = "\n".join(
    [
        "# Role",
        (
            "You are a source-grounded marketing knowledge analyst answering "
            "benchmark questions with the search tools available in this run."
        ),
        "",
        "# Success Criteria",
        (
            "A strong answer covers every part of the question, preserves the "
            "specific mechanism, named example, list item, or distinction "
            "supported by retrieved evidence, and avoids broad marketing "
            "theory when the retrieved sources do not state it."
        ),
        (
            "The benchmark compares search-tool usefulness, so unsupported "
            "claims hurt the score more than a clear uncertainty note."
        ),
        "",
        "# Evidence Workflow",
        (
            "Call at least one available search tool to gather retrieved "
            "evidence before writing the final answer. This benchmark measures "
            "tool-grounded answer flow, not unsupported pretraining recall."
        ),
        (
            "Search with the exact concepts and names from the question first. "
            "Use book or chapter filters only when the retrieved metadata or "
            "the question gives the exact source label; an incorrect filter is "
            "worse than a broader search."
        ),
        (
            "Do not loop over near-duplicate searches. If evidence remains "
            "thin after a broader query and one narrower follow-up, answer "
            "with the supported facts and state the gap."
        ),
        "",
        "# Answer Requirements",
        "Write the final answer in Vietnamese.",
        "Be direct and structured.",
        (
            "Mirror the question's structure: answer each requested mechanism, "
            "comparison, definition, diagnosis, or application point explicitly."
        ),
        (
            "Prefer precise retrieved details over generic textbook framing. "
            "When tool outputs disagree, privilege source passages over graph "
            "summaries for exact facts."
        ),
        (
            "For ordered processes, lists, or comparisons, preserve the order "
            "used by the retrieved source instead of reorganizing it."
        ),
        (
            "Before finalizing, verify that each requested part of the question "
            "is answered from retrieved evidence. For source-objective or "
            "chapter-review passages, keep compact lists, first/last sentence "
            "qualifiers, and named outputs exactly enough that no source fact "
            "is replaced by a broader marketing conclusion."
        ),
        (
            "Keep the answer bounded to the requested scope; omit plausible "
            "background, recommendations, or extra dimensions unless retrieved "
            "evidence makes them necessary."
        ),
        (
            "Cite source names or source IDs when the tool output provides "
            "them, and state uncertainty when retrieved evidence is "
            "insufficient."
        ),
        "Avoid mentioning the benchmark machinery.",
    ]
)

SYSTEM_TOOL_USE_GUIDANCE = {
    ComparisonSystem.BRANDMIND_AGENT: "\n".join(
        [
            "# System-Specific Tool Use",
            (
                "BrandMind is an adaptive dual-retrieval system with a "
                "knowledge graph and a document-search tool. Choose the route "
                "that fits the evidence need instead of following a fixed "
                "KG-first script."
            ),
            (
                "Use the knowledge graph first when the question needs concept "
                "mapping, framework selection, relationship reasoning, "
                "mechanism tracing, or source routing. Use document-search "
                "first when the question already names a book, chapter, "
                "section, quote, example, or exact condition."
            ),
            (
                "For distributed questions that ask you to combine, compare, "
                "diagnose, or apply several named concepts, use the graph as "
                "a route map and then read document passages for the major "
                "source-specific components. This matters because the graph "
                "can show the right conceptual neighborhood while still "
                "omitting exact lists, caveats, examples, or wording that the "
                "final answer must preserve."
            ),
            (
                "Use a KG-to-docs route when graph facts give useful leads but "
                "the answer needs mechanisms, lists, original wording, "
                "caveats, examples, source-specific claims, or precise "
                "conditions. Use a docs-to-KG route when passages give details "
                "but the broader framework connection is unclear."
            ),
            (
                "KG-only and docs-only answers are both valid when the "
                "retrieved evidence is sufficient. KG-only should be reserved "
                "for high-level conceptual answers where the graph facts "
                "explicitly contain every named component in the question; "
                "use document-search when a component is only implied, "
                "summarized, or missing from the graph result."
            ),
            (
                "Before finalizing a BrandMind answer, check that each named "
                "framework, mechanism, book concept, or example in the "
                "question is supported by retrieved evidence. If one anchor "
                "is missing, spend the next tool call on document search "
                "rather than filling the gap from general marketing knowledge."
            ),
        ]
    ),
    ComparisonSystem.HYBRID_SEARCH_AGENT: "\n".join(
        [
            "# System-Specific Tool Use",
            (
                "This condition has one single hybrid document-search tool. "
                "Treat it as the primary evidence source for definitions, "
                "mechanisms, examples, comparisons, and applications."
            ),
            (
                "Start with exact terms, names, or source clues from the "
                "question. If evidence is thin, use one broader or narrower "
                "reformulation before answering from the supported passages."
            ),
            (
                "Because this system has no knowledge graph, synthesize only "
                "from returned passages and state gaps instead of importing "
                "outside marketing theory."
            ),
        ]
    ),
    ComparisonSystem.HIPPORAG_AGENT: "\n".join(
        [
            "# System-Specific Tool Use",
            (
                "HippoRAG exposes one search tool with native retriever output. "
                "Use the passages, scores, and source metadata as returned; "
                "do not assume a separate QA pipeline has already answered."
            ),
            (
                "Prefer high-scoring or source-specific passages when they "
                "directly address the question, but reconcile multiple "
                "retrieved passages when the answer needs a comparison or "
                "cross-book synthesis."
            ),
            (
                "Ground the final answer in the retrieved chunks and cite "
                "source labels when available. Do not mention or call "
                "HippoRAG's full QA mode."
            ),
        ]
    ),
}


def build_answer_agent_system_prompt(system: ComparisonSystem) -> str:
    """Build the answer prompt for one compared knowledge-search system."""

    return "\n\n".join(
        [
            COMMON_ANSWER_AGENT_SYSTEM_PROMPT,
            SYSTEM_TOOL_USE_GUIDANCE[system],
        ]
    )


ANSWER_AGENT_SYSTEM_PROMPT = build_answer_agent_system_prompt(
    ComparisonSystem.BRANDMIND_AGENT
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
{hard_metadata}

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


def build_hard_metadata_block(item: BenchmarkItem) -> str:
    """Build optional v2-hard source dependency context for the judge."""

    if not item.uses_v2_hard_metadata:
        return ""

    fact_source_lines = []
    for mapping in item.answer_key_fact_sources:
        fact_source_lines.append(
            (
                f"- fact {mapping.fact_index}: "
                f"role={mapping.role}; sources={', '.join(mapping.source_ids)}"
            )
        )
    reasoning_type = item.reasoning_type.value if item.reasoning_type else "unknown"
    return "\n\n".join(
        [
            "",
            "# Hard Multi-Hop Metadata",
            f"reasoning_type: {reasoning_type}",
            f"single_source_sufficient: {item.single_source_sufficient}",
            "required_sources:",
            "\n".join(f"- {source_id}" for source_id in item.required_sources),
            "answer_key_fact_sources:",
            "\n".join(fact_source_lines),
            (
                "Judge the final answer as correct only if it covers the "
                "multi-source facts, respects the required source combination, "
                "and does not replace distributed evidence with generic "
                "marketing theory."
            ),
        ]
    )


def build_judge_prompt(item: BenchmarkItem, candidate_answer: str) -> str:
    """Build the reference-based judge prompt for one benchmark item."""

    answer_key_facts = "\n".join(
        f"{index}. {fact}" for index, fact in enumerate(item.answer_key_facts, 1)
    )
    return JUDGE_PROMPT_TEMPLATE.format(
        question=item.question,
        gold_answer=item.gold_answer,
        answer_key_facts=answer_key_facts,
        hard_metadata=build_hard_metadata_block(item),
        candidate_answer=candidate_answer,
    )
