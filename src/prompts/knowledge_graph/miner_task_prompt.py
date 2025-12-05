"""Task prompt template for Knowledge Miner agent.

This template provides the specific extraction task for each chunk,
including domain context, section summary, and chunk content.
"""

MINER_TASK_PROMPT_TEMPLATE = """# EXTRACTION TASK

**Domain:** {{domain}}

**Section Context:** {{section_summary}}
Use this context to anchor meanings and disambiguate entities.

**Chunk Content:**
{{chunk_content}}

# YOUR MISSION
Extract knowledge triples from the chunk above. Focus on enduring knowledge (concepts, strategies, principles) rather than temporal data.

Remember to:
1. Use PascalCase for entity types
2. Use lowerCamelCase active verbs for relation types
3. Write comprehensive descriptions
4. VALIDATE your extraction using the validate_triples tool before finalizing
"""
