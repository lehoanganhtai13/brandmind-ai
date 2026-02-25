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

{{next_task_instruction}}

IMPORTANT — Read carefully before acting:
1. CHECK if you have ALREADY completed any of these tasks but forgot to 
   call '{{write_todos_function_name}}' to update their status.
   → If YES: Call '{{write_todos_function_name}}' NOW to mark them
     as 'completed'. DO NOT redo work you have already finished.
2. If there are tasks you truly have NOT started yet → work on them.
3. If you just finished a task → call '{{write_todos_function_name}}' 
   to mark it 'completed' and set the next task 'in_progress'.

You MUST continue until ALL tasks are marked 'completed'.
This is a mandatory instruction, not optional.
</system_critical_reminder>
"""

STOP_CHECK_FINAL_CONFIRMATION = """
<system_final_check>
You completed all {{all_tasks_count}} tasks but stopped without providing a response to the user.

The user's original request was: "[User's original request]"

Based on everything you have gathered and accomplished, provide your final answer to the user now.
</system_final_check>
"""
