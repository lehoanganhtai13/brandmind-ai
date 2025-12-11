"""
Task prompt for description synthesis.

This prompt provides the input data for merging two entity descriptions.
"""

DESCRIPTION_SYNTHESIS_TASK_PROMPT = """
Synthesize these two descriptions into one cohesive text:

**Target Length:** {{TARGET_LENGTH}} characters

**Existing Description:**
{{EXISTING_DESC}}

**New Information:**
{{NEW_DESC}}

Provide the synthesized description.
"""
