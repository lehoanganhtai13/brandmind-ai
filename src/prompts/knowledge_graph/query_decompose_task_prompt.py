"""
Task prompt for query decomposition.

This prompt provides the input data structure for decomposing user queries.
"""

QUERY_DECOMPOSE_TASK_PROMPT = """
**USER QUERY:**
"{{QUERY}}"

**INSTRUCTION:**
Decompose this query into **Global** (thematic/conceptual) and **Local** (entity-specific) sub-queries based on your system instructions.
"""
