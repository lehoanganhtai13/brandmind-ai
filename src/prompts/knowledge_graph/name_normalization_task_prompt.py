"""
Task prompt template for entity name normalization.

This template is used to format the user message containing the batch of names
to be normalized by the LLM.
"""

NAME_NORMALIZATION_TASK_PROMPT = """
Apply the cognitive patterns and examples above to normalize the following list of entities. 

Input JSON:
{{NAMES_JSON}}

Response (JSON only):
"""
