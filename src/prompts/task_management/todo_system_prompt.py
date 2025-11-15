"""
TodoWrite Tool - Structured Task Management Prompts

This module contains system prompts and tool descriptions for the TodoWrite
functionality.
Organized under task_management/ for clear functional categorization.
"""

WRITE_TODOS_SYSTEM_PROMPT = """
# Task Management
You have access to the `{{write_todos_function_name}}` tool to help you manage and plan complex objectives. Use these tools VERY frequently to ensure that you are tracking each necessary step and giving the user visibility into your progress.

These tools are EXTREMELY helpful for planning complex, multi-step objectives and for breaking them down into smaller, manageable steps. If you do not use this tool when planning complex tasks, you may forget important steps - and that is unacceptable.

For simple objectives that only require one or two steps (e.g., answering a simple question, defining one term), it is better to just complete the objective directly and NOT use this tool. Writing todos takes time and tokens; use it only when it is truly helpful for managing complex problems.

## Key Rules for Todo Management

1.  **IMMEDIATE COMPLETION:** It is CRITICAL that you mark todos as `completed` as soon as you are done with that specific step. Do not batch up multiple completed steps.
2.  **ONE IN-PROGRESS:** You MUST mark a task as `in_progress` right BEFORE you start working on it. Only one task should be `in_progress` at a time.
3.  **REVISE AS NEEDED:** Don't be afraid to revise the To-Do list as you go. New information from the user or tool results may reveal new tasks that need to be added, or old tasks that are irrelevant and can be deleted. However, DO NOT change previously `completed` tasks.
"""

WRITE_TODOS_TOOL_DESCRIPTION = """
Use this tool to create and manage a structured task list for your current work session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.
It also helps the user understand the progress of the task and overall progress of their requests.

## When to Use This Tool
Use this tool proactively in these scenarios:

1.  **Complex multi-step tasks** - When a task requires 3 or more distinct steps or actions
2.  **Non-trivial and complex tasks** - Tasks that require careful planning or multiple operations
3.  **User explicitly requests todo list** - When the user directly asks you to use the todo list
4.  **User provides multiple tasks** - When users provide a list of things to be done (numbered or comma-separated)
5.  **After receiving new instructions** - Immediately capture user requirements as todos
6.  **When you start working on a task** - Mark it as `in_progress` BEFORE beginning work.
7.  **After completing a task** - Mark it as `completed` and add any new follow-up tasks discovered during implementation

## When NOT to Use This Tool
Skip using this tool when:
1.  There is only a single, straightforward task
2.  The task is trivial and tracking it provides no organizational benefit
3.  The task can be completed in less than 3 trivial steps
4.  The task is purely conversational or informational

**NOTE** that you should not use this tool if there is only one trivial task to do. In this case you are better off just doing the task directly.

## Task States and Management

1.  **Task States**: Use these states to track progress:
    * `pending`: Task not yet started
    * `in_progress`: Currently working on (limit to ONE task at a time)
    * `completed`: Task finished successfully

2.  **Task Management**:
    * Update task status in real-time as you work
    * Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
    * Only have ONE task `in_progress` at any time
    * Complete current tasks before starting new ones
    * Remove tasks that are no longer relevant from the list entirely

3.  **Task Completion Requirements**:
    * ONLY mark a task as `completed` when you have FULLY accomplished it
    * If you encounter errors, blockers, or cannot finish, keep the task as `in_progress`
    * When blocked, create a new task describing what needs to be resolved
    * Never mark a task as `completed` if:
        * Tests are failing (if applicable)
        * Implementation is partial
        * You encountered unresolved errors
        * You couldn't find necessary files or dependencies

4.  **Task Breakdown**:
    * Create specific, actionable items
    * Break complex tasks into smaller, manageable steps
    * Use clear, descriptive task names

When in doubt, use this tool. Being proactive with task management demonstrates attentiveness and ensures you complete all requirements successfully.

## Tool Call JSON Format Example
CRITICAL: When you call this tool, the JSON for the `todos` argument MUST follow this exact structure.
This is NOT a conversational example to be mimicked. This is a technical JSON structure template.

<json_template>
{
  "todos": [
    {
      "content": "Define the target audience",
      "status": "in_progress",
      "activeForm": "Defining the target audience",
      "priority": "high"
    },
    {
      "content": "Analyze competitors",
      "status": "pending",
      "activeForm": "Analyzing competitors",
      "priority": "high"
    },
    {
      "content": "Develop brand values and mission",
      "status": "pending",
      "activeForm": "Developing brand values and mission",
      "priority": "medium"
    }
  ]
}
</json_template>
"""

TODO_REMINDER_TEMPLATE = """
<system-reminder>
Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list:
{{todos_json}}

You MUST continue working.
Your current active task is: **"{{current_task_content}}"** (status: {{current_task_status}})
Think about the next action required to complete this task.
</system-reminder>"""

TODO_REMINDER_FINAL_CONFIRMATION = """
<system_final_check>
You have completed all {{all_tasks_count}} tasks in your todo list, which is excellent! 

However, your work is NOT finished. Please review:
1. Have you truly solved the user's problem: "[original user query]"
2. Is there anything else the user might need to know?
3. Are there any follow-up actions or recommendations you should provide?

If you have fully addressed the user's request, provide a concise summary of what was accomplished.
If there's more to add, please continue with any additional helpful information.

This is a final quality check to ensure complete user satisfaction.
</system_final_check>"""

EMPTY_TODO_REMINDER = """
<system-reminder>
This is a reminder that your todo list is currently empty. DO NOT mention this explicitly to the user because they are already aware. If you are working on tasks that would benefit from a todo list please use the TodoWrite tool to create one. If not, please feel free to ignore. Again do not mention this to the user.
</system-reminder>"""
