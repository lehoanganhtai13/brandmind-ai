"""
Task prompt for entity merge decision.

This prompt provides the input data structure for entity comparison.
"""

ENTITY_MERGE_TASK_PROMPT = """
Compare these two entities and decide if they should be merged:

**EXISTING_ENTITY:**
```json
{
  "name": "{{EXISTING_NAME}}",
  "type": "{{EXISTING_TYPE}}",
  "description": "{{EXISTING_DESC}}"
}
```

**NEW_ENTITY:**
```json
{
  "name": "{{NEW_NAME}}",
  "type": "{{NEW_TYPE}}",
  "description": "{{NEW_DESC}}"
}
```

Analyze and provide your decision.
"""
