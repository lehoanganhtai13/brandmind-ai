"""
Task prompt for Document Cartographer agent.
This is the initial instruction given to the agent when starting analysis.
"""

CARTOGRAPHER_TASK_PROMPT = """
Analyze the document structure in this folder and create a global_map.json file.

Follow your cognitive workflow:
1. RECONNAISSANCE: Find the Table of Contents
2. TARGET ACQUISITION: For each section, verify location and pinpoint exact line numbers
3. CONTEXTUALIZATION: Create rich, detailed summaries with concepts and entities
4. ARTIFACT GENERATION: Write the complete JSON to /global_map.json

Remember: Use write_file tool to save the final JSON. Do not output JSON in chat.
"""
