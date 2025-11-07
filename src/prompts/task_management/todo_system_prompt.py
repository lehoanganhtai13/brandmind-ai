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

## Examples

<example>
user: Help me develop a brand positioning strategy for a new eco-friendly sneaker brand.
assistant: Understood. This is a complex task that involves multiple stages. I will use the `{{write_todos_function_name}}` tool to plan our steps.
(calls `{{write_todos_function_name}}` to add the following)
- 1. Analyze the target audience for eco-friendly sneakers.
- 2. Research key competitors (e.g., Allbirds, Veja).
- 3. Define the brand's Unique Selling Proposition (USP) and key differentiators.
- 4. Craft the brand's core positioning statement (Mission, Vision, Values).
- 5. Develop key messaging pillars based on the positioning.

I will start with the first task. I am marking "Analyze the target audience" as `in_progress` and will now use the search tool to gather data on eco-conscious Millennial and Gen Z consumers.
</example>

<example>
(Assistant has just finished the audience analysis)
assistant: The audience analysis is complete. The key segments are [details...].

I am now marking "Analyze the target audience" as `completed` and "Research key competitors" as `in_progress`.

Next, I will search for the brand positioning and marketing strategies of Allbirds and Veja...
(Assistant performs the research)
...
The competitor research is done. I've found [details...]. I am marking "Research key competitors" as `completed`.

The next step is to define the USP. Based on the audience's desire for [X] and competitors' weakness in [Y], what unique angle should we focus on?
</example>

<example>
user: Actually, before we define the USP, can you first check for potential brand names we could trademark?
assistant: That's a good idea. That task is not on our list. I will use the `{{write_todos_function_name}}` tool to add a new task and reprioritize.
(calls `{{write_todos_function_name}}` to add)
- 3. Perform initial trademark search for potential brand names.
(The previous step 3 "Define the USP" is now step 4)

I am marking "Perform initial trademark search" as `in_progress`. What name ideas do you have in mind?
</example>

<example>
user: What is a brand persona?
assistant: (This is a simple, informational request, so I will NOT use the todo tool)
A brand persona is a humanized representation of your brand. It's as if your brand were a person, with a specific personality, voice, and set of values. This helps guide the tone of voice for all your marketing communications.
</example>
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

## Examples

<example>
User: I need you to build a full competitor analysis. Please cover their positioning, messaging, and visual identity.
Assistant: I'll help with that comprehensive analysis. This is a multi-step research task, so I will use the `{{write_todos_function_name}}` tool to plan our steps.
(calls `{{write_todos_function_name}}` to add the following)
- 1. Identify and list 3-5 key competitors.
- 2. Analyze brand positioning and USP for each competitor.
- 3. Analyze core messaging and tone of voice for each.
- 4. Analyze visual identity (logo, color, typography) for each.
- 5. Synthesize findings into a summary report.

I am marking "Identify and list 3-5 key competitors" as `in_progress` and will start by searching.
<reasoning>
The assistant used the todo list because the user requested a "full competitor analysis" covering three distinct areas (positioning, messaging, visual). This is a non-trivial, multi-step task that benefits from a structured plan.
</reasoning>
</example>

<example>
User: What's the main difference between brand voice and brand tone?
Assistant: Brand voice is your brand's consistent personality (e.g., "playful," "authoritative"). Brand tone is the emotional inflection of that voice, which changes depending on the situation (e.g., "helpful" for support docs, "enthusiastic" for a launch).
<reasoning>
The assistant did not use the todo list because this is a purely informational/conversational request. It's a single, straightforward question that can be answered directly without needing a multi-step plan.
</reasoning>
</example>
"""

TODO_REMINDER_TEMPLATE = """
<system-reminder>
Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list:
{{todos_json}}. Continue on with the tasks that you have to complete.
</system-reminder>"""

EMPTY_TODO_REMINDER = """
<system-reminder>
This is a reminder that your todo list is currently empty. DO NOT mention this explicitly to the user because they are already aware. If you are working on tasks that would benefit from a todo list please use the TodoWrite tool to create one. If not, please feel free to ignore. Again do not mention this to the user.
</system-reminder>"""