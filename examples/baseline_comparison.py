"""
Baseline Comparison: Deep Agent vs RAG Basic

Compare Deep Agent (using KG + Doc tools) vs RAG Basic (hybrid search + LLM).
"""

import asyncio
import json
from pathlib import Path

from pydantic import BaseModel, Field

from config.system_config import SETTINGS
from shared.agent_tools.retrieval import search_document_library, search_knowledge_graph
from shared.model_clients.llm.google import GoogleAIClientLLM, GoogleAIClientLLMConfig

# Load test questions from external file
from test_questions import TEST_QUESTIONS


# Deep Agent Setup (WITHOUT langchain - direct tool calls)
DEEP_AGENT_INSTRUCTION = """# ROLE & OBJECTIVE
You are **The Deep Marketing Analyst**, a specialized AI consultant for marketing strategy and theory.
Your mission is to answer user inquiries by synthesizing verified information from two internal databases: a **Knowledge Graph** (Cognitive Map) and a **Document Library** (Evidence Archive).

**CORE PHILOSOPHY: RESEARCH-FIRST IMPLEMENTATION**
* **"Understand first, do later":** Never attempt to answer or search for details until you have constructed a solid mental model of the domain.
* **No Blind Searching:** Do not blindly search the Document Library with vague keywords. You must know *what* you are looking for and *where* it is likely located (Book, Chapter, Context) before you dig.
* **Evidence-Based:** Your knowledge comes from the provided tools, not your pre-training. Always ground your answers in the retrieved context.

# YOUR TOOLBOX

1.  `search_knowledge_graph(query)`: **The Strategist (Brain)**
    * *Use this FIRST.*
    * Returns: Concepts, relationships, principles, causal logic ("Why/How"), and **Source Pointers** (Book names, Chapters).
    * *Goal:* To brainstorm, understand the problem space, and identify *where* to look for details.

2.  `search_document_library(query, top_k=10, filter_by_book=None, filter_by_chapter=None)`: **The Archivist (Memory)**
    * *Use this SECOND (Conditional).*
    * Returns: Raw text passages, exact quotes, data tables, and specific examples.
    * *Goal:* To verify facts, get specific execution details, or retrieve exact citations based on the "leads" found in the Knowledge Graph.

# COGNITIVE WORKFLOW

## Phase 1: Sensemaking & Mapping (Mandatory)
* **Action:** Always start by consulting `search_knowledge_graph` with a conceptual query.
* **Reasoning:**
    * What concepts are involved? How do they relate?
    * What is the underlying logic or strategy?
    * *Crucial:* Note the **Source Metadata** returned by the KG (e.g., "This concept is discussed in Chapter 5 of Kotler's book").

## Phase 2: Sufficiency Assessment (The Decision Point)
Review the information retrieved from the Knowledge Graph. Ask yourself:
* *"Is this conceptual understanding sufficient to answer the user fully?"*
    * **YES (Conceptual/Strategic Questions):** If the user asks "What is the principle of 4P?", the KG's explanation is likely enough. -> **Proceed to Answer.**
    * **NO (Detailed/Executional Questions):** If the user asks for "Examples of IKEA's pricing" or "The exact steps to launch," the KG might be too abstract. -> **Proceed to Phase 3.**

## Phase 3: Targeted Deep Dive (Conditional)
* **Action:** Use `search_document_library` to fetch missing details.
* **Precision Targeting:** Do NOT search globally. Use the **metadata** found in Phase 1 to narrow your search.
    * *Bad:* Search "pricing" across the whole library.
    * *Good:* Search "product mix pricing examples" with `filter_by_chapter="Chapter 10"`.

## Phase 4: Synthesis & Response
Construct your final answer by weaving together the **Logic** (from KG) and the **Evidence** (from Library).
* **Structure:** Define the concept -> Explain the mechanics -> Provide specific examples/evidence.
* **Citation:** Explicitly mention where the information comes from (e.g., "According to Chapter 7...").

# GUIDELINES FOR SUCCESS
1.  **Don't Over-Tool:** If the Knowledge Graph gives you a perfect, comprehensive answer, do not waste time calling the Document Library just for the sake of it.
2.  **Contextual Querying:** When calling tools, write queries that match the tool's nature.
    * *KG Query:* Abstract & Relational (e.g., "Drivers of Customer Loyalty").
    * *Doc Query:* Specific & Lexical (e.g., "Customer Loyalty program case studies").
3.  **Be Transparent:** If you cannot find information in either tool, admit it. Do not hallucinate marketing theories.

# TOOL CALLING FORMAT
When you need to call tools, use this format:
```
TOOL_CALL: search_knowledge_graph
QUERY: <your conceptual query>
```

Or:
```
TOOL_CALL: search_document_library
QUERY: <your specific query>
TOP_K: 10
FILTER_BY_CHAPTER: <chapter name if needed>
```

After receiving tool results, synthesize them into your final answer.
"""


async def deep_agent_answer(question: str) -> str:
    """Deep Agent: Multi-step reasoning with KG and Doc tools."""
    llm = GoogleAIClientLLM(
        config=GoogleAIClientLLMConfig(
            model="gemini-2.5-flash-lite",
            api_key=SETTINGS.GEMINI_API_KEY,
            system_instruction=DEEP_AGENT_INSTRUCTION,
            temperature=0.1,
            thinking_budget=2000,
            max_tokens=5000,
        )
    )

    # Step 1: Search Knowledge Graph (mandatory)
    kg_result = await search_knowledge_graph(query=question, max_results=10)

    # Step 2: Build context with KG results
    context = f"""# Knowledge Graph Results

{kg_result}

---

Now answer the user's question based on the above knowledge graph information.
If the KG results are sufficient, provide your answer directly.
If you need more details, explain what additional information would be helpful."""

    # Step 3: Get LLM response
    response = await llm.acomplete(f"{context}\n\n# User Question: {question}")
    return response.text


# RAG Basic Setup
RAG_BASIC_INSTRUCTION = """# ROLE & OBJECTIVE
You are **The Marketing Knowledge Assistant**, an AI that answers marketing questions based on provided context.

**YOUR TASK:**
Answer the user's question using ONLY the information provided in the "Retrieved Context" section below.

**GUIDELINES:**
1. **Stay Grounded:** Base your answer strictly on the retrieved context. Do not use your pre-training knowledge.
2. **Be Comprehensive:** If the context contains relevant information, provide a complete answer covering all key points.
3. **Be Honest:** If the retrieved context does not contain enough information to answer the question, say "I don't have enough information in the retrieved context to answer this question fully."
4. **Structure Well:** Organize your answer clearly with definitions, explanations, and examples when available.
5. **Cite Sources:** Mention where information comes from (e.g., "According to the retrieved passage...").

**OUTPUT FORMAT:**
Provide a direct, well-structured answer. Do not add meta-commentary about the retrieval process.
"""


async def rag_basic_answer(question: str) -> str:
    """RAG Basic: Direct search + LLM response."""
    # Step 1: Retrieve context via hybrid search (fixed parameter)
    retrieved_context = await search_document_library(
        query=question,
        top_k=10,  # Fixed: use top_k instead of max_results
    )

    # Step 2: Build prompt with retrieved context
    prompt = f"""# RETRIEVED CONTEXT

{retrieved_context}

---

# USER QUESTION

{question}

---

Answer the question based on the retrieved context above.
"""

    # Step 3: Get LLM response
    llm = GoogleAIClientLLM(
        config=GoogleAIClientLLMConfig(
            model="gemini-2.5-flash-lite",
            api_key=SETTINGS.GEMINI_API_KEY,
            system_instruction=RAG_BASIC_INSTRUCTION,
            temperature=0.1,
            thinking_budget=2000,
            max_tokens=5000,
        )
    )

    response = await llm.acomplete(prompt)
    return response.text


# Evaluator Setup
class EvaluationResult(BaseModel):
    """Structured evaluation result."""

    is_correct: bool = Field(..., description="Whether the answer is correct")
    reasoning: str = Field(..., description="Explanation of the judgment")


EVALUATOR_TASK_PROMPT = """# ROLE & OBJECTIVE
You are **The Truth Arbiter**, an expert evaluator responsible for verifying the accuracy of AI-generated responses.
Your specific task is to compare an **AGENT_RESPONSE** against a **GROUND_TRUTH** (the correct answer) for a given **QUESTION**.

**YOUR CORE JUDGMENT PHILOSOPHY:**
You are judging based on **Information Containment**, not Keyword Matching.
* **CORRECT:** The Agent's response conveys the *same core meaning* and facts as the Ground Truth, even if the wording, length, or structure is different. Extra context provided by the Agent is acceptable as long as it does not contradict the truth.
* **INCORRECT:** The Agent's response contradicts the Ground Truth, fails to answer the core question, or omits the most critical piece of information required by the Ground Truth.

# INPUT DATA

**1. QUESTION:**
```
{{QUESTION}}
```

**2. GROUND_TRUTH (The Standard):**
```
{{GROUND_TRUTH}}
```

**3. AGENT_RESPONSE (The Candidate):**
```
{{AGENT_RESPONSE}}
```

# EVALUATION WORKFLOW

1.  **Extract Key Facts:** Identify the essential facts, numbers, or concepts in the `GROUND_TRUTH` that *must* be present for the answer to be valid.
2.  **Verify Presence:** Check if these essential facts are present in the `AGENT_RESPONSE`.
    * *Allow:* Paraphrasing, synonyms, and summarization.
    * *Allow:* Additional relevant details (unless they are explicitly wrong).
3.  **Determine Verdict:**
    * If the core facts are present and accurate -> **true**.
    * If core facts are missing, wrong, or hallucinated -> **false**.
"""


async def evaluate_response(
    question: str,
    ground_truth: str,
    agent_response: str,
) -> EvaluationResult:
    """Evaluate agent response against ground truth."""
    # Build evaluation prompt
    prompt = (
        EVALUATOR_TASK_PROMPT.replace("{{QUESTION}}", question)
        .replace("{{GROUND_TRUTH}}", ground_truth)
        .replace("{{AGENT_RESPONSE}}", agent_response)
    )

    # Use Gemini-2.5-Flash for evaluation
    evaluator = GoogleAIClientLLM(
        config=GoogleAIClientLLMConfig(
            model="gemini-2.5-flash",
            api_key=SETTINGS.GEMINI_API_KEY,
            temperature=0.0,  # Deterministic evaluation
            max_tokens=3000,
            thinking_budget=2000,
            response_mime_type="application/json",
            response_schema=EvaluationResult,
        )
    )

    response = await evaluator.acomplete(prompt)
    result = json.loads(response.text)
    return EvaluationResult(**result)


# Main Comparison
async def run_comparison():
    """Run full comparison between Deep Agent and RAG Basic."""
    results = {
        "deep_agent": [],
        "rag_basic": [],
    }

    for i, test_case in enumerate(TEST_QUESTIONS, 1):
        question = test_case["question"]
        ground_truth = test_case["ground_truth"]

        print(f"\n{'='*80}")
        print(f"Question {i}/{len(TEST_QUESTIONS)}: {question}")
        print(f"{'='*80}")

        # Test Deep Agent
        print("\n[Deep Agent] Processing...")
        try:
            deep_answer = await deep_agent_answer(question)
            print(f"Answer: {deep_answer[:200]}...")

            # Evaluate
            deep_eval = await evaluate_response(question, ground_truth, deep_answer)
            print(f"Evaluation: {'✓ CORRECT' if deep_eval.is_correct else '✗ INCORRECT'}")
            print(f"Reasoning: {deep_eval.reasoning}")

            results["deep_agent"].append(
                {
                    "question": question,
                    "answer": deep_answer,
                    "is_correct": deep_eval.is_correct,
                    "reasoning": deep_eval.reasoning,
                }
            )
        except Exception as e:
            print(f"Error: {e}")
            results["deep_agent"].append(
                {
                    "question": question,
                    "answer": f"ERROR: {e}",
                    "is_correct": False,
                    "reasoning": "Failed to generate response",
                }
            )

        # Test RAG Basic
        print("\n[RAG Basic] Processing...")
        try:
            rag_answer = await rag_basic_answer(question)
            print(f"Answer: {rag_answer[:200]}...")

            # Evaluate
            rag_eval = await evaluate_response(question, ground_truth, rag_answer)
            print(f"Evaluation: {'✓ CORRECT' if rag_eval.is_correct else '✗ INCORRECT'}")
            print(f"Reasoning: {rag_eval.reasoning}")

            results["rag_basic"].append(
                {
                    "question": question,
                    "answer": rag_answer,
                    "is_correct": rag_eval.is_correct,
                    "reasoning": rag_eval.reasoning,
                }
            )
        except Exception as e:
            print(f"Error: {e}")
            results["rag_basic"].append(
                {
                    "question": question,
                    "answer": f"ERROR: {e}",
                    "is_correct": False,
                    "reasoning": "Failed to generate response",
                }
            )

    return results


def analyze_results(results):
    """Analyze and display comparison results."""
    deep_correct = sum(1 for r in results["deep_agent"] if r["is_correct"])
    rag_correct = sum(1 for r in results["rag_basic"] if r["is_correct"])
    total = len(TEST_QUESTIONS)

    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)

    print(f"\nDeep Agent Accuracy: {deep_correct}/{total} ({deep_correct/total*100:.1f}%)")
    print(f"RAG Basic Accuracy:  {rag_correct}/{total} ({rag_correct/total*100:.1f}%)")

    print("\n" + "=" * 80)
    print("DETAILED BREAKDOWN")
    print("=" * 80)

    for i, (deep, rag) in enumerate(
        zip(results["deep_agent"], results["rag_basic"]), 1
    ):
        print(f"\nQ{i}: {deep['question']}")
        print(f"  Deep Agent: {'✓' if deep['is_correct'] else '✗'} | {deep['reasoning']}")
        print(f"  RAG Basic:  {'✓' if rag['is_correct'] else '✗'} | {rag['reasoning']}")

    # Save results to JSON
    output_path = Path("baseline_comparison_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to {output_path}")


if __name__ == "__main__":
    print("Starting Baseline Comparison...")
    print(f"Loaded {len(TEST_QUESTIONS)} test questions\n")

    results = asyncio.run(run_comparison())
    analyze_results(results)
