"""
Task prompt for reranking with diversity.

This prompt provides the input data structure for candidate reranking.
"""

RERANK_DIVERSITY_TASK_PROMPT = """
Please analyze and rank the following candidates based on the User Query.

**USER QUERY:**
"{{QUERY}}"

**CANDIDATES:**
{{CANDIDATES_LIST}}

**INSTRUCTION:**
Rank the top {{TOP_K}} candidates. Prioritize unique insights. If candidates are redundant, keep only the best one.
"""
