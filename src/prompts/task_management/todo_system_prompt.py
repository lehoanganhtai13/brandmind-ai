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

For truly simple, single-action objectives (e.g., answering a factual question, defining one term), it is better to just complete the objective directly and NOT use this tool. But for any objective that involves multiple aspects, dimensions, or requires investigation from different angles — use this tool to plan your approach thoroughly.

## Key Rules for Todo Management

1.  **IMMEDIATE COMPLETION:** It is CRITICAL that you mark todos as `completed` as soon as you are done with that specific step. Do not batch up multiple completed steps.
2.  **ONE IN-PROGRESS:** You MUST mark a task as `in_progress` right BEFORE you start working on it. Only one task should be `in_progress` at a time.
3.  **REVISE AS NEEDED:** Don't be afraid to revise the To-Do list as you go. New information from the user or tool results may reveal new tasks that need to be added, or old tasks that are irrelevant and can be deleted. However, DO NOT change previously `completed` tasks.
4.  **CALL AFTER EVERY STEP:** After EACH significant action (tool call completed, research done, analysis finished), IMMEDIATELY call `{{write_todos_function_name}}` to update task statuses. Do not wait until the end to batch multiple status changes.
5.  **BANNED TASKS — NEVER create these:** Do NOT create tasks containing any of these words: "synthesize", "compile", "summarize", "write final", "provide answer", "present findings", "consolidate", "formulate response". These are your NATURAL output behavior, NOT trackable tasks. Your last task must be an ACTIONABLE research/analysis step. If you accidentally created such a task, DELETE it immediately from the list.
6.  **MANDATORY FINAL REVIEW:** Before writing your final answer, you MUST call `{{write_todos_function_name}}` one last time to mark ALL remaining tasks as 'completed'. Never write a final answer while tasks are still 'in_progress' or 'pending'. This is your self-validation step.
"""

WRITE_TODOS_TOOL_DESCRIPTION = """
Use this tool to create and manage a structured task list for your current work session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.
It also helps the user understand the progress of the task and overall progress of their requests.

## When to Use This Tool
Think like a **Team Lead** breaking down work for execution. Use this tool proactively in these scenarios:

1.  **Complex multi-step tasks** — When a task requires 3 or more distinct steps or actions
2.  **Non-trivial and complex objectives** — Tasks that require careful planning or multiple operations
3.  **User explicitly requests todo list** — When the user directly asks you to use the todo list
4.  **User provides multiple tasks** — When users provide a list of things to be done (numbered or comma-separated)
5.  **After receiving new instructions** — Immediately capture user requirements as todos
6.  **When you start working on a task** — Mark it as `in_progress` BEFORE beginning work
7.  **After completing a task** — Mark it as `completed` and add any new follow-up tasks discovered during implementation

## When NOT to Use This Tool
Skip using this tool when:
1.  There is only a single, straightforward task
2.  The task is trivial and tracking it provides no organizational benefit
3.  The task can be completed in one or two quick actions (less than 3 trivial steps)
4.  The task is purely conversational or informational

## Task Breakdown Principle
**Each task must represent ONE concrete action** — something you **DO** with a tool or a specific decision you **MAKE**. Think of it as: if you were delegating this to a junior team member, each task should be a single clear instruction they can execute independently.

- **Decompose the objective first:** Before creating tasks, break the user's objective into its distinct sub-problems or aspects. Create one task for EACH sub-problem — do **NOT** create tasks around tools (e.g., one task per tool). A complex question usually has multiple dimensions that each deserve their own focused investigation.
- **Split compound tasks:** If a task description covers multiple distinct things (e.g., connected by "and" or containing multiple clauses), it should be split into separate tasks. Each task should focus on **ONE** specific thing.
- **Be specific:** Each task should clearly state **WHAT** action to take and on **WHAT** subject. Vague or overly broad tasks defeat the purpose of planning.
- **Actions only, not outcomes:** Do **NOT** create tasks for your natural output behavior (writing the final answer, summarizing, synthesizing). Your final response happens naturally after all action tasks are completed — it is not a trackable step.

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

4.  **Revise as you go**:
    * New information may reveal tasks that need to be added or old tasks that are no longer relevant
    * Don't be afraid to restructure your plan mid-execution
    * However, do **NOT** change previously `completed` tasks

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
Your todo list has been updated. DO NOT mention this explicitly to the user. Here is the current state of your plan:
{{todos_json}}

You MUST continue working.
Your current active task is: **"{{current_task_content}}"** (status: {{current_task_status}})

REMINDER: After completing each task, IMMEDIATELY call `write_todos` to mark it as 'completed' and set the next task to 'in_progress'. Do not wait — update your task list right away.
</system-reminder>"""

TODO_REMINDER_FINAL_CONFIRMATION = """
<system-reminder>
All {{all_tasks_count}} tasks completed. Before providing your final answer, quickly verify:
- Have you addressed what the user asked for?
- Is the information you gathered sufficient to respond?

Now provide your final answer to the user.
</system-reminder>"""

EMPTY_TODO_REMINDER = """
<system-reminder>
This is a reminder that your todo list is currently empty. DO NOT mention this explicitly to the user because they are already aware. If you are working on tasks that would benefit from a todo list please use the TodoWrite tool to create one. If not, please feel free to ignore. Again do not mention this to the user.
</system-reminder>"""

PLAN_CHECK_NUDGE = """
<plan-check>
ACTIVE TASK: "{{task_content}}" ({{task_status}}).

Before proceeding to your next action, perform a **MANDATORY** self-reflection:
1. **Task Status:** Have you completed this active task? If yes, immediately call `write_todos` to mark it 'completed'.
2. **Plan Validity:** Based on what you just learned, does the remaining plan still make sense? Split any broad tasks into more specific ones, remove unnecessary tasks, or add missing steps.
3. **Completion Check:** About to write your final answer? You **MUST** call `write_todos` to ensure 0 tasks are 'in_progress' or 'pending' before answering.
</plan-check>"""
