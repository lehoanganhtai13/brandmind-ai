"""
TodoWrite Middleware for LangGraph Agents

This module provides comprehensive todo management functionality for LangGraph agents,
including validation, state persistence, and automatic reminder generation.
Inspired by Claude Code's TodoWrite functionality with enterprise-level reliability.
"""

from loguru import logger
from typing import List, Dict, Any, Annotated
from collections.abc import Callable, Awaitable

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command
from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelCallResult,
    ModelRequest,
    ModelResponse,
)
from langchain.tools import InjectedToolCallId
import json

from prompts.task_management.todo_system_prompt import (
    WRITE_TODOS_SYSTEM_PROMPT,
    WRITE_TODOS_TOOL_DESCRIPTION,
    EMPTY_TODO_REMINDER,
    TODO_REMINDER_TEMPLATE,
    TODO_REMINDER_FINAL_CONFIRMATION
)

# Import shared types to ensure consistency
from shared.agent_types import TodoItem


class PlanningState(AgentState):
    """
    Extended agent state schema that includes todo management capabilities.

    This state structure extends the base LangChain agent state to include
    persistent todo list storage, enabling agents to maintain task context
    across multiple turns and tool executions.

    Attributes:
        todos (List[TodoItem]): Persistent todo list for task tracking
    """
    todos: List[TodoItem]


class TodoWriteMiddleware(AgentMiddleware):
    """
    Complete middleware providing TodoWrite functionality.

    This middleware provides comprehensive todo management with custom tool naming
    and direct prompt parameter passing, including edge case handling, state
    validation, and persistent storage.

    The middleware automatically injects reminders based on todo state changes
    and enforces business rules for single-task execution and mandatory fields.
    """

    state_schema = PlanningState

    def __init__(
        self,
        *,
        tool_name: str = "write_todos",
        system_prompt: str = WRITE_TODOS_SYSTEM_PROMPT,
        tool_description: str = WRITE_TODOS_TOOL_DESCRIPTION
    ):
        """
        Initialize TodoWrite middleware with custom parameters.

        Args:
            tool_name (str): Name for the todo management tool
            system_prompt (str): System prompt template with placeholders
            tool_description (str): Tool description template with placeholders
        """
        super().__init__()
        self.tool_name = tool_name
        self.system_prompt = system_prompt.replace("{{write_todos_function_name}}", tool_name)
        self.tool_description = tool_description.replace("{{write_todos_function_name}}", tool_name)
        self.tools = [self._create_write_todos_tool()]

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        """
        Inject system prompt and reminders based on current todo state.

        Always injects the main system prompt with TodoWrite instructions.
        Provides additional initial guidance when no todos exist.
        State change reminders are handled through tool responses.

        Args:
            request: The model request containing state and system prompt
            handler: The next handler in the middleware chain

        Returns:
            ModelCallResult with potentially modified system prompt
        """
        try:
            # Always inject the main TodoWrite system prompt
            existing_prompt = request.system_prompt or ""
            request.system_prompt = f"{existing_prompt}\n\n{self.system_prompt}"

            # Get todos from request state, default to empty list
            todos = request.state.get("todos", [])

            # Inject additional reminder for empty todo lists (initial state)
            if not todos:
                reminder = self._generate_reminder(todos)  # Will return EMPTY_TODO_REMINDER
                if reminder:
                    request.system_prompt = f"{request.system_prompt}\n\n{reminder}"

            return handler(request)
        except Exception as e:
            # Log error but don't break the middleware chain
            logger.error(f"Failed to inject system reminder: {e}")
            return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        """
        Async version of wrap_model_call - inject system prompt and reminders based on todo state.

        Always injects the main system prompt with TodoWrite instructions.
        Provides additional initial guidance when no todos exist.
        State change reminders are handled through tool responses.

        Args:
            request: The model request containing state and system prompt
            handler: The next handler in the middleware chain

        Returns:
            ModelCallResult with potentially modified system prompt
        """
        try:
            # Always inject the main TodoWrite system prompt
            existing_prompt = request.system_prompt or ""
            request.system_prompt = f"{existing_prompt}\n\n{self.system_prompt}"

            # Get todos from request state, default to empty list
            todos = request.state.get("todos", [])

            # Inject additional reminder for empty todo lists (initial state)
            if not todos:
                reminder = self._generate_reminder(todos)  # Will return EMPTY_TODO_REMINDER
                if reminder:
                    request.system_prompt = f"{request.system_prompt}\n\n{reminder}"

            return await handler(request)
        except Exception as e:
            # Log error but don't break the middleware chain
            logger.error(f"Failed to inject system reminder: {e}")
            return await handler(request)

    def _create_write_todos_tool(self):
        """Create the todo management tool with comprehensive validation and state management."""
        @tool(self.tool_name, description=self.tool_description)
        def write_todos(
            todos: List[TodoItem],
            tool_call_id: Annotated[str, InjectedToolCallId]
        ) -> Command:
            """
            Manage todo list for complex multi-step tasks (3+ steps or more).

            CRITICAL: ALWAYS provide the COMPLETE list of todos, not just changes!

            Each todo MUST include:
            - content (str): Clear, actionable description
            - status (str): "pending" | "in_progress" | "completed"
            - activeForm (str): Present continuous description
            - priority (str): "high" | "medium" | "low"

            Rules:
            - Mark tasks as in_progress BEFORE beginning work on them
            - Only ONE task can be in_progress at a time (single-threading principle)
            - ONLY mark tasks completed when FULLY done and verified
            - Include validation/testing steps in your task breakdowns
            """

            try:
                # Validation with mandatory activeForm check
                validation = self._validate_todos(todos)
                if not validation["valid"]:
                    return Command(
                        update={
                            "messages": [ToolMessage(
                                f"Validation error: {validation['error']}",
                                tool_call_id=tool_call_id
                            )]
                        }
                    )

                # Create base response message
                response_message = f"Todo list updated with {len(todos)} tasks"

                # Add contextual reminders for existing todos
                if todos:
                    reminder = self._generate_reminder(todos)  # Generate state change reminder
                    if reminder:
                        response_message += f"\n\n{reminder}"

                # Update state with new todos using Command object
                return Command(
                    update={
                        "todos": todos,
                        "messages": [ToolMessage(
                            response_message,
                            tool_call_id=tool_call_id
                        )]
                    }
                )

            except Exception as e:
                # Return error message if something goes wrong
                return Command(
                    update={
                        "messages": [ToolMessage(
                            f"Error updating todo list: {str(e)}",
                            tool_call_id=tool_call_id
                        )]
                    }
                )

        return write_todos

    def _generate_reminder(self, todos: List[TodoItem]) -> str:
        """
        Generate reminders based on todo state.

        Covers all edge cases:
        - Empty list (initial or post-completion)
        - State changes (any update)

        Args:
            todos: Current list of todo items

        Returns:
            Reminder string or empty string if no reminder needed
        """
        try:
            # Case A: Empty list reminder
            if not todos:
                return EMPTY_TODO_REMINDER
            
            in_progress_tasks = [task for task in todos if task.get("status") == "in_progress"]
            pending_tasks = [task for task in todos if task.get("status") == "pending"]

            # Case B: All tasks completed reminder
            if not in_progress_tasks and not pending_tasks:
                return (
                    TODO_REMINDER_FINAL_CONFIRMATION
                    .replace("{{all_tasks_count}}", str(len(todos)))
                )

            # Case C: State change reminder with placeholder
            todos_json = json.dumps([
                {
                    "content": todo["content"],
                    "status": todo["status"],
                    "activeForm": todo["activeForm"]
                } for todo in todos
            ], indent=2)

            return (
                TODO_REMINDER_TEMPLATE
                .replace("{{todos_json}}", todos_json)
                .replace(
                    "{{current_task_content}}",
                    in_progress_tasks[0]["content"] if in_progress_tasks else ""
                )
                .replace(
                    "{{current_task_status}}",
                    in_progress_tasks[0]["status"] if in_progress_tasks else ""
                )
            )

        except Exception as e:
            print(f"Warning: TodoWriteMiddleware reminder generation failed: {e}")
            return ""

    def _validate_todos(self, todos: List[TodoItem]) -> Dict[str, Any]:
        """
        Validate todo list with mandatory activeForm and business rules.

        Enforces:
        - Single in_progress rule (max_in_progress = 1)
        - Mandatory activeForm field
        - Required field validation
        - Status value validation

        Args:
            todos: List of todo items to validate

        Returns:
            Dictionary with validation result and error message if applicable
        """
        try:
            if not todos:
                return {"valid": True, "error": None}

            # Single in_progress rule (fixed at 1)
            in_progress = [t for t in todos if t.get("status") == "in_progress"]
            if len(in_progress) > 1:
                return {
                    "valid": False,
                    "error": f"Too many tasks in_progress ({len(in_progress)}). Only 1 task allowed at a time."
                }

            # Mandatory field validation
            for i, todo in enumerate(todos):
                # Check required content field
                if not todo.get("content", "").strip():
                    return {"valid": False, "error": f"Todo at index {i} has empty content"}

                # Check mandatory activeForm field
                if not todo.get("activeForm", "").strip():
                    return {"valid": False, "error": f"Todo at index {i} has empty activeForm field"}

                # Check valid status values
                if todo.get("status") not in ["pending", "in_progress", "completed"]:
                    return {
                        "valid": False,
                        "error": f"Todo at index {i} has invalid status '{todo.get('status')}'. Must be one of: pending, in_progress, completed"
                    }

                # Check valid priority values
                if todo.get("priority") not in ["high", "medium", "low"]:
                    return {
                        "valid": False,
                        "error": f"Todo at index {i} has invalid priority '{todo.get('priority')}'. Must be one of: high, medium, low"
                    }

            return {"valid": True, "error": None}

        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }


if __name__ == "__main__":
    """
    Quick test example for TodoWriteMiddleware.

    This section allows for direct testing of the middleware functionality
    without requiring a full agent setup.
    """
    # Create middleware with default settings
    middleware = TodoWriteMiddleware()

    print("TodoWriteMiddleware Quick Test")
    print("=" * 40)
    print(f"Tool name: {middleware.tool_name}")
    print(f"Available tools: {[tool.name for tool in middleware.tools]}")

    # Test validation
    test_todos = [
        {
            "content": "Test task 1",
            "status": "pending",
            "activeForm": "Starting test task 1",
            "priority": "high"
        },
        {
            "content": "Test task 2",
            "status": "in_progress",
            "activeForm": "Working on test task 2",
            "priority": "medium"
        }
    ]

    validation = middleware._validate_todos(test_todos)
    print(f"Validation result: {validation}")

    # Test reminder generation
    reminder = middleware._generate_reminder(test_todos)
    print(f"Generated reminder preview: {reminder}")

    # Test validation with invalid data (multiple in_progress)
    invalid_todos = [
        {
            "content": "Task 1",
            "status": "in_progress",
            "activeForm": "Working on task 1",
            "priority": "high"
        },
        {
            "content": "Task 2",
            "status": "in_progress",
            "activeForm": "Working on task 2",
            "priority": "medium"
        }
    ]

    invalid_validation = middleware._validate_todos(invalid_todos)
    print(f"Invalid validation result: {invalid_validation}")

    print("\nQuick test completed successfully!")