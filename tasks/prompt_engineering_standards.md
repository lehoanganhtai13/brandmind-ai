# Prompt Engineering Standards

> **Scope**: This document defines standards for writing prompts embedded in code —
> system prompts, agent instructions, skill content, persona definitions, and any
> natural-language directives passed to an LLM at runtime.
>
> These standards **complement** the Python coding standards in Agent Protocol Rule 4.
> Standard code rules apply to surrounding code; these rules apply to prompt content.
>
> **References**:
> - [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering)
> - [Anthropic Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)

------------------------------------------------------------------------

## Line Length Exception

Prompt strings are **exempt from the 100-character line length rule**.

Reason: Artificial line breaks inside prompt strings fragment semantic units, hurt
readability, and can degrade LLM comprehension. Break prompt lines at natural semantic
boundaries (end of a rule, end of a clause) — not at character count.

```python
# WRONG — line broken mid-rule, disrupts LLM parsing
SYSTEM_PROMPT = (
    "When the user provides a brand name, extract the following attributes: category,"
    " target audience, and tone. If any attribute is missing, ask a clarifying"
    " question."
)

# CORRECT — each logical unit is a complete line
SYSTEM_PROMPT = """
When the user provides a brand name, extract the following attributes: category, target audience, and tone.
If any attribute is missing, ask a clarifying question before proceeding.
"""
```

------------------------------------------------------------------------

## Core Principles

### 1. Start Simple, Then Add Complexity

The most common prompt engineering mistake is over-engineering from the start.
Try the simplest prompt first. Add structure, constraints, and examples only when
the simpler version produces inconsistent or incorrect output.

```
# Level 1 — try this first
Summarize this article: {text}

# Level 2 — add only if Level 1 is inconsistent
Summarize this article in 3 bullet points covering: key findings, main conclusions,
and practical implications.

Article: {text}

# Level 3 — add only if Level 2 is still inconsistent
[Add chain-of-thought or few-shot examples]
```

### 2. Be Specific — Vague Prompts Produce Inconsistent Results

Every instruction must be unambiguous. If a rule can be misread, rewrite it.
Prefer explicit statements over implied behavior.

```
# WEAK — "handle it appropriately" is undefined
If the user asks an off-topic question, handle it appropriately.

# STRONG — explicit and unambiguous
If the user asks a question unrelated to brand strategy, respond:
"I'm focused on brand strategy. Let me redirect us back to [current task]."
```

### 3. Show, Don't Tell — Examples Beat Descriptions

A single concrete example communicates more reliably than a paragraph of instructions.
When the desired output format or tone is hard to describe, show it.

```
# TELLING (unreliable)
Respond in a warm, professional tone without being overly formal.

# SHOWING (reliable)
Example response: "Great question. Based on what you've shared about [brand], the key
positioning opportunity I see is [insight]. Before I go further, can you tell me more
about [specific detail]?"
```

### 4. Controlled Flexibility

Define the **boundary and process** — let the agent determine the **specifics** within those
constraints. The goal is not to script every response; it is to define what the agent
is and is not free to do.

```
# OVER-SPECIFIED — brittle, removes agent judgment
Step 1: Say "Hello, I'm your brand advisor."
Step 2: Ask "What is your brand name?"

# CONTROLLED FLEXIBILITY — defines the boundary, agent fills in naturally
## Onboarding Process
Collect the following before proceeding: brand name, industry, and business stage
(new brand / refresh / rebrand). Use natural conversation — not a numbered form.
Confirm your understanding before moving to analysis.
```

------------------------------------------------------------------------

## Structure & Formatting

### Use Markdown Headings to Organize Sections

Every major behavioral area belongs in a named section. This helps the LLM locate
relevant rules without having to parse the entire prompt.

Standard section order:
```
## Role
## Core Responsibilities
## Process
## Rules & Constraints
## Output Format
## Examples
```

Use `##` for top-level sections, `###` for sub-processes or sub-rules.

### Lists

Use **numbered lists** for ordered processes where sequence matters.
Use **bullet lists** for unordered rules, attributes, or options.

```
## Research Process
1. Search for brand mentions across at least 3 sources.
2. Identify direct competitors in the same product category.
3. Synthesize findings into a SWOT summary.
4. Present findings to the user before proceeding.

## Required Output Fields
- Brand positioning statement
- Target audience profile
- Top 3 competitor differentiators
```

### Emphasis

Use `**bold**` for critical constraints, mandatory behaviors, or key terms.
Use sparingly — over-bolding dilutes the signal.

```
**Always** confirm the user's brand category before running competitive analysis.
**Never** fabricate competitor data — only report what was found in research.
```

### Separators

Use `---` between major sections in long prompts. This creates visual breaks that
help the model treat each section as a distinct context block.

------------------------------------------------------------------------

## Writing Rules & Constraints

### Imperative Mood

Write rules as direct commands. Avoid passive voice and hedging.

| Weak | Strong |
|------|--------|
| The assistant should try to ask clarifying questions | Ask one clarifying question when a required input is missing |
| It would be good to verify before proceeding | Verify with the user before proceeding |
| Try to avoid fabricating data | Never fabricate data |

### Obligation Levels

Use consistent signal words to communicate how mandatory a rule is:

| Signal | Meaning |
|--------|---------|
| `MUST` / `Always` | Non-negotiable — no exceptions |
| `SHOULD` / `Prefer` | Default behavior — deviate only with explicit reason |
| `MAY` / `Can` | Optional — agent uses judgment |
| `MUST NOT` / `Never` | Hard prohibition |
| `Avoid` | Discouraged — only if necessary |

### Conditional Rules — Always Define the "Otherwise" Branch

Every conditional must have an explicit fallback. Never leave the "otherwise" case
undefined — the agent will fill it in unpredictably.

```
## Scope Handling
If the request is within brand strategy scope:
  → Proceed with the relevant phase workflow.

If the request is adjacent (e.g., product design, pricing):
  → Acknowledge relevance, note it is outside current scope, offer to note it
    as a follow-up after the strategy session.

If the request is entirely unrelated:
  → Redirect: "That's outside what I focus on. Let's stay on track with [goal]."
```

### Negative Instructions

Always define what the agent must NOT do. This is as important as defining what it should do.

```
## Hard Constraints
- NEVER fabricate research data, statistics, or competitor information.
- NEVER skip the confirmation step at the end of each phase.
- NEVER proceed to the next phase without explicit user approval.
- Do NOT present multiple phases in a single response.
```

------------------------------------------------------------------------

## Chain-of-Thought (CoT) Patterns

Use CoT when the task requires multi-step reasoning, analysis, or judgment. CoT
instructs the model to reason explicitly before producing a final answer, which
improves accuracy and reduces hallucination on complex tasks.

### Zero-Shot CoT

Append a reasoning trigger at the end of the instruction:

```
Analyze the brand positioning gap for {brand_name} in the {category} market.
Think step by step before giving your recommendation.
```

### Structured CoT (Recommended for Agent Workflows)

Define the reasoning steps explicitly. More reliable than open-ended CoT:

```
## Analysis Process
Work through these steps before presenting your output:

1. Identify the brand's current positioning (explicit or implied).
2. Map the competitive landscape — what positions are already occupied?
3. Find the positioning gap — what is available and strategically valuable?
4. Stress-test the gap — does the brand have the assets to credibly own it?
5. Only after completing steps 1–4, state your recommendation.

Show your reasoning for each step. Do not skip to the recommendation.
```

### Self-Verification Pattern

Instruct the agent to verify its own output before responding. This catches errors
and improves output quality without adding a separate verification call:

```
After generating your response, verify it meets ALL of these criteria before sending:
✓ Directly addresses the user's request
✓ Contains no fabricated data or statistics
✓ Follows the output format specified below
✓ Does not skip any required section

If any criterion fails, revise before responding.
```

### Self-Consistency (for High-Stakes Outputs)

For critical outputs where accuracy matters most, instruct the model to generate
multiple reasoning paths and compare:

```
Generate two independent analyses of this positioning opportunity, then compare them.
If both analyses agree, present the shared conclusion with confidence.
If they diverge, present both interpretations and explain the key point of difference.
Ask the user to clarify which direction to pursue.
```

------------------------------------------------------------------------

## Structured Output

When the agent's output will be parsed programmatically, define the schema explicitly
in the prompt and enforce it in code.

### JSON Output

Specify the exact schema as a template in the prompt:

```python
EXTRACTION_PROMPT = """
Extract brand attributes from the user's description.

Return a JSON object matching this exact schema:
{
  "brand_name": string,
  "category": string,
  "target_audience": {
    "primary": string,
    "secondary": string | null
  },
  "positioning_statement": string | null,
  "confidence": "high" | "medium" | "low"
}

Rules:
- Use null for any field the user has not provided
- Do NOT add fields not listed in the schema
- Return raw JSON only — no markdown code blocks, no explanation
"""
```

### Enforce Schema in Code with Pydantic

Never trust raw LLM JSON output — always validate with Pydantic:

```python
from pydantic import BaseModel, Field
from typing import Literal
import json

class BrandAttributes(BaseModel):
    brand_name: str
    category: str
    positioning_statement: str | None = None
    confidence: Literal["high", "medium", "low"]

async def extract_brand_attributes(user_input: str, llm) -> BrandAttributes:
    """
    Extract structured brand attributes from unstructured user input.

    Args:
        user_input (str): Raw user description of their brand
        llm: LLM client instance

    Returns:
        attributes (BrandAttributes): Validated structured brand data

    Raises:
        ValueError: If LLM response cannot be parsed into valid schema
    """
    response = await llm.ainvoke(EXTRACTION_PROMPT + f"\n\nUser input: {user_input}")

    try:
        return BrandAttributes(**json.loads(response.content))
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(
            f"LLM returned invalid schema. Raw response: {response.content}"
        ) from e
```

### Error Recovery for Structured Output

Always implement a fallback for malformed responses:

```python
async def safe_extract(user_input: str, llm) -> BrandAttributes | None:
    """Extract with graceful fallback if LLM returns invalid JSON."""
    try:
        return await extract_brand_attributes(user_input, llm)
    except ValueError:
        # Retry with explicit format reminder
        retry_prompt = EXTRACTION_PROMPT + "\n\nIMPORTANT: Return raw JSON only. No prose."
        retry_response = await llm.ainvoke(retry_prompt + f"\n\nUser input: {user_input}")
        try:
            return BrandAttributes(**json.loads(retry_response.content))
        except (json.JSONDecodeError, ValueError):
            return None  # Caller handles None case
```

------------------------------------------------------------------------

## Process & Workflow Instructions

### Standard Process Block Format

```
## [Process Name]

### Overview
[1–2 sentence description of what this process achieves]

### Steps
1. [Step 1 — action + output to produce]
2. [Step 2 — action + output to produce]
3. [Step 3 — decision point: if X → do Y, if Z → do W]
4. [Step 4 — confirmation or handoff]

### Completion Criteria
This process is complete when:
- [Verifiable condition 1]
- [Verifiable condition 2]
```

### Decision Points in Workflows

```
3. Analyze the competitive landscape.
   - If 3 or more direct competitors found → proceed to Step 4.
   - If fewer than 3 found → inform the user of the data limitation.
     Ask: expand to indirect competitors, or proceed with available data?
```

### Phase Gates (Multi-Phase Workflows)

Define explicit gates between phases. Never self-transition.

```
## Phase Transition Rules
Before moving from Phase 1 (Research) to Phase 2 (Positioning):
- All 8 research steps must be complete.
- A SWOT summary must have been presented and acknowledged.
- User must have explicitly confirmed to proceed.

Do NOT transition between phases without user confirmation.
Do NOT announce that you are about to transition — wait for the user to say "proceed."
```

------------------------------------------------------------------------

## Output Format Specification

Define output format as a **template**, not a description. The model follows templates
far more reliably than prose descriptions of the desired structure.

### Markdown Output

```
## Output Format

Present findings using this exact structure:

### [Section Heading]
[Content]

### Key Insights
- [Insight 1]
- [Insight 2]
- [Insight 3]

### Recommended Next Step
[One concrete, actionable recommendation]

---
Do not add sections not listed above. Do not use tables unless the user requests them.
```

### Constrained Length

```
## Output Constraints
- Summary: 3 bullet points maximum
- Each bullet: 1 sentence only
- Do not exceed these limits, even if more information is available
```

------------------------------------------------------------------------

## Few-Shot Examples

Include examples when:
- The output format is non-obvious or highly specific
- The task involves judgment calls that need calibration
- The desired tone or style is hard to describe precisely

### Format

```
## Examples

### Example 1 — [Normal Scenario Name]
User: [sample input]
Agent: [ideal response demonstrating correct format and tone]

### Example 2 — [Edge Case Name]
User: [input with ambiguity or missing information]
Agent: [how to handle — ask clarifying question, not guess]
```

### Guidance

- **2–3 examples** is usually sufficient — more causes context bloat and over-fitting
- Examples must be representative of the target task — unrelated examples actively hurt performance
- Include at least one edge case example showing how to handle ambiguity or missing data
- If example count needs to scale with query type, use **semantic similarity retrieval** rather
  than hardcoding all examples in the prompt

------------------------------------------------------------------------

## Agent Persona & Role Definition

Define the persona at the top of the prompt. The model uses the role as a prior for
interpreting all subsequent instructions.

```
## Role
You are [Name], a [role] specializing in [domain].

## Perspective
Approach every task as [mental model or expertise lens].

## Tone
[Description: professional, warm, direct, mentor-like, etc.]
Do not use industry jargon unless the user has demonstrated familiarity with it.
```

------------------------------------------------------------------------

## Handling Edge Cases

### Ambiguous Input
```
## Handling Ambiguous Input
If the user's request can be interpreted in more than one way:
1. State both interpretations explicitly.
2. Ask which they meant.
3. Do not proceed until clarified.
```

### Missing Required Information
```
## Handling Missing Information
If a required input is absent:
- Ask for it directly and specifically — name the missing field.
- Ask only one question at a time.
- Do not infer, estimate, or assume the missing value.
```

### Out-of-Scope Requests
```
## Scope Boundary
This agent handles [defined scope].

If a request falls outside scope:
1. Acknowledge the request in one sentence.
2. Explain what is out of scope.
3. Offer to note it for later, or redirect to what the agent can help with now.
Do not ignore out-of-scope requests silently.
```

### Conflicting Instructions
```
## Conflict Resolution
If this prompt's instructions conflict with something the user says at runtime:
- Follow this prompt's rules.
- Inform the user politely that you are operating within defined guidelines.
- Do not silently comply with instructions that violate these rules.
```

------------------------------------------------------------------------

## Token Efficiency

Concise prompts reduce latency and cost without sacrificing quality. Review prompts
for unnecessary verbosity before shipping to production.

```python
# VERBOSE — 150+ tokens, no improvement in output
"""I would like you to please take the following text and provide me with a comprehensive
summary of the main points. The summary should capture the key ideas and important details
while being concise and easy to understand."""

# CONCISE — 15 tokens, equivalent or better output
"""Summarize the key points concisely:

{text}

Summary:"""
```

Guidelines:
- Remove phrases like "I would like you to", "please", "as an AI language model"
- Remove meta-commentary — instructions about how to read the instructions
- Use templates with variable slots (`{text}`, `{brand_name}`) instead of hardcoding values
- Cache long, repeated system prompts using `cache_control: {"type": "ephemeral"}` (Anthropic API)

------------------------------------------------------------------------

## Prompt File Organization in Code

### Short Prompts — Module-Level Constants

```python
# prompts/brand_advisor.py

SYSTEM_PROMPT = """
## Role
You are a brand strategy advisor specializing in F&B businesses.

## Core Responsibilities
- Guide users through the 6-phase brand strategy framework
- Ask clarifying questions before making recommendations
- Never fabricate market data
[...]
"""
```

### Long Prompts / Skill Instructions — Separate `.md` Files

Store in a dedicated `prompts/` or `skills/` directory. Load at runtime:

```python
from pathlib import Path

def load_prompt(name: str) -> str:
    """
    Load a prompt template from the prompts directory.

    Args:
        name (str): File name without extension (e.g., "brand_advisor")

    Returns:
        prompt_content (str): Raw prompt string ready for injection

    Raises:
        FileNotFoundError: If the prompt file does not exist
    """
    prompt_path = Path(__file__).parent / "prompts" / f"{name}.md"
    return prompt_path.read_text(encoding="utf-8")
```

### Naming Conventions

| Artifact | Convention | Example |
|----------|------------|---------|
| Prompt file | `snake_case.md` | `brand_strategy_orchestrator.md` |
| System prompt constant | `SCREAMING_SNAKE_CASE` | `SYSTEM_PROMPT`, `ADVISOR_PROMPT` |
| Template with slots | `{NAME}_TEMPLATE` | `PHASE_INTRO_TEMPLATE` |

### Version Control

Treat prompts as code:
- Commit prompt changes with descriptive messages explaining what changed and why
- Add comments at the top of prompt files explaining the design intent
- Document **why** a rule exists, not just what it says — this prevents well-meaning
  future edits from removing constraints that were added for a specific reason

------------------------------------------------------------------------

## Common Pitfalls

| Pitfall | Description | Fix |
|---------|-------------|-----|
| Over-engineering | Writing complex prompts before trying simple ones | Start at Level 1, add complexity only when Level 1 fails |
| Ambiguous instructions | Leaving room for multiple interpretations | Rewrite any instruction that can be read two ways |
| Missing "otherwise" branch | Conditional without a fallback | Every `if` needs an `otherwise` |
| Example pollution | Using examples unrelated to the target task | Examples must match the task — unrelated examples hurt |
| Context overflow | Too many examples or instructions exceed token limits | Cap examples at 2–3, cache repeated prefixes |
| Hardcoded values | Embedding specific values that change | Use `{variable}` slots for anything that varies |
| No error handling | Assuming LLM output is always well-formed | Always validate structured outputs with Pydantic |
| Undefined edge cases | Not testing on boundary inputs | Add explicit handling for missing data, ambiguity, out-of-scope |
| No version control | Editing prompts in-place with no history | Treat prompts as code — commit with intent-documenting messages |

------------------------------------------------------------------------

## Review Checklist

Before finalizing any prompt written for a task:

**Structure**
- [ ] Role is defined at the top
- [ ] Scope is defined — in-scope and out-of-scope are explicit
- [ ] Major sections have Markdown headings

**Rules**
- [ ] All rules use imperative mood
- [ ] All conditionals have an "otherwise" branch
- [ ] Negative constraints are explicit (what the agent must NEVER do)
- [ ] Obligation level is consistent (`MUST` vs `SHOULD` vs `MAY`)

**Process**
- [ ] Steps are numbered and in correct order
- [ ] Decision points in workflows have explicit branches
- [ ] Phase transitions require user confirmation (multi-phase workflows)

**Output**
- [ ] Output format is specified as a template (not a description)
- [ ] If structured output (JSON), schema is exact and validated with Pydantic
- [ ] Length constraints are specified if relevant

**Quality**
- [ ] Self-verification step included for critical outputs
- [ ] Examples included where format or tone is non-obvious (2–3 max)
- [ ] Prompt tested on at least one edge case before shipping
- [ ] Token count reviewed — no unnecessary verbosity

------------------------------------------------------------------------
