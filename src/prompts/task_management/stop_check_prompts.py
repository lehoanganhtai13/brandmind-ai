"""
Stop Check Prompts for Task Completion Enforcement

This module contains prompts for the stop check middleware that ensures
agents complete all tasks before terminating.
Organized under task_management/ for clear functional categorization.
"""

STOP_CHECK_CRITICAL_REMINDER = """
<system_critical_reminder>
You attempted to stop working, but your todo list is NOT finished.

Current Status:
- Tasks in progress: {{in_progress_count}}
- Tasks pending: {{pending_count}}

You MUST continue working until ALL tasks are marked 'completed'.

{{next_task_instruction}}

DO NOT STOP until all tasks are completed. Think about the next step:
- If you just finished a task → call '{{write_todos_function_name}}' to mark it 'completed' and set the next task 'in_progress'
- If you need to perform an action for the current task → do it
- If all tasks are completed → you may stop

This is a mandatory instruction, not optional.
</system_critical_reminder>
"""

STOP_CHECK_FINAL_CONFIRMATION = """
<system_final_check>
You have completed all {{all_tasks_count}} tasks in your todo list, which is excellent! 

However, you stopped without confirming whether you have fully addressed the user's original request.

Please review:
1. Have you truly solved the user's problem: "[User's original request]"
2. Is there anything else the user might need to know?
3. Are there any follow-up actions or recommendations you should provide?

If you have fully addressed the user's request, provide the final output in the format requested by the user (e.g., JSON, structured output) or a concise summary of what was accomplished.
If there's more to add, please continue with any additional helpful information.

This is a final quality check to ensure complete user satisfaction.
</system_final_check>
"""
