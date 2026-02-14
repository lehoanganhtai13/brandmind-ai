"""
Ensure Tasks Finished Middleware for LangGraph Agents

This middleware ensures that agents cannot prematurely stop working
when there are incomplete todos. It acts as a "stop check" guardrail
similar to Claude Code's stop prevention mechanism.
"""

from collections.abc import Awaitable, Callable
from typing import Dict, List, Optional

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelCallResult,
    ModelRequest,
    ModelResponse,
)
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from prompts.task_management.stop_check_prompts import (
    STOP_CHECK_CRITICAL_REMINDER,
    STOP_CHECK_FINAL_CONFIRMATION,
)
from shared.agent_types import TodoItem


class PlanningState(AgentState):
    """
    Extended agent state schema that includes todo management capabilities.

    This should match the PlanningState definition in todo_write_middleware.py
    to ensure state consistency across the application.
    """

    todos: List[TodoItem]


class EnsureTasksFinishedMiddleware(AgentMiddleware):
    """
    Middleware that prevents agents from stopping prematurely when todos are incomplete.

    This middleware acts as a "stop check" guardrail that intercepts model responses
    and forces the agent to continue working if there are incomplete tasks.

    Key Features:
    - Detects when agent is attempting to stop (empty AI response without tool calls)
    - Checks todo completion status from agent state
    - Forces re-prompting with critical reminder if tasks are incomplete
    - Maintains conversation flow while ensuring task completion
    """

    state_schema = PlanningState

    def __init__(
        self,
        *,
        tool_name: str = "write_todos",
        re_prompt_template: Optional[str] = None,
        final_confirmation_template: Optional[str] = None,
        max_reminders: int = 3,
        max_retries_malformed: int = 3,
    ):
        """
        Initialize the stop check middleware.

        Args:
            tool_name (str): Name of the todo management tool for re-prompting
            re_prompt_template (Optional[str]): Custom re-prompt template override
            max_reminders (int): Maximum number of reminders before giving up
            max_retries_malformed (int): Maximum number of retries for malformed calls
        """
        super().__init__()
        self.tool_name = tool_name
        self.max_reminders = max_reminders
        self.max_retries_malformed = max_retries_malformed
        self.re_prompt_template = re_prompt_template or STOP_CHECK_CRITICAL_REMINDER
        self.final_confirmation_template = (
            final_confirmation_template or STOP_CHECK_FINAL_CONFIRMATION
        )

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        """
        Synchronous version of awrap_model_call.

        This provides the same functionality for synchronous environments.
        """
        # 1. Let the model run and make its decision
        response = handler(request)

        # 2. Check if model call is malformed
        if self._is_malformed_call(response):
            logger.warning(
                "Detected MALFORMED_FUNCTION_CALL from model. "
                "Attempting auto-recovery..."
            )

            for retry in range(self.max_retries_malformed):
                # Add error message to ask model to fix the error
                error_msg = (
                    "<system_critical_reminder> Your last function call was "
                    "malformed (invalid JSON or schema). "
                    "Please analyze the tool schema carefully and try calling "
                    "the function again with valid arguments. "
                    "</system_critical_reminder>"
                )
                request.messages.append(SystemMessage(content=error_msg))

                # Call model again
                response = handler(request)

                # If no more error, exit retry loop
                if not self._is_malformed_call(response):
                    logger.info("Recovered from MALFORMED_FUNCTION_CALL successfully.")
                    break

        # 3. Check if model is attempting to stop
        # logger.debug(f"Model response: {response}")
        is_stopping = self._is_agent_stopping(response)
        # logger.debug(f"Is agent stopping? {is_stopping}")

        # 4. If agent is stopping, check if todos are complete
        if is_stopping:
            todos = request.state.get("todos", [])
            if not isinstance(todos, list):
                raise TypeError("Todos in agent state must be a list.")

            incomplete_tasks = self._get_incomplete_tasks(todos)

            # 5. If there are incomplete tasks, force continuation
            if isinstance(incomplete_tasks, dict) and (
                len(incomplete_tasks.get("in_progress", [])) > 0
                or len(incomplete_tasks.get("pending", [])) > 0
            ):
                logger.warning(
                    "Agent attempted to stop with "
                    f"{len(incomplete_tasks.get('pending', []))} pending and "
                    f"{len(incomplete_tasks.get('in_progress', []))} in-progress "
                    "tasks. Injecting critical reminder to continue working."
                )
                # Try multiple reminders in the same stopping attempt
                current_response = response
                for attempt in range(self.max_reminders):
                    # Generate critical reminder
                    re_prompt = self._generate_re_prompt(incomplete_tasks)

                    # Add re-prompt to conversation history
                    request.messages.append(SystemMessage(content=re_prompt))

                    # Force the model to re-think with the critical reminder
                    current_response = handler(request)

                    # Check if agent is still stopping after reminder
                    still_stopping = self._is_agent_stopping(current_response)

                    if not still_stopping:
                        # Agent is working again, return the good response
                        return current_response

                    # logger.debug(f"Model response after reminder: {current_response}")

                    # Update incomplete tasks for next attempt
                    todos = request.state.get("todos", [])
                    if not isinstance(todos, list):
                        raise TypeError("Todos in agent state must be a list.")
                    incomplete_tasks = self._get_incomplete_tasks(todos)
                    if not isinstance(incomplete_tasks, dict):
                        incomplete_tasks = {"pending": [], "in_progress": []}
                    if not incomplete_tasks:
                        # All tasks completed, return response
                        return current_response

                # If we get here, agent ignored all reminders
                if isinstance(incomplete_tasks, dict):
                    incomplete_count = len(incomplete_tasks.get("pending", [])) + len(
                        incomplete_tasks.get("in_progress", [])
                    )
                else:
                    incomplete_count = 0
                raise RuntimeError(
                    f"Agent failed to complete tasks after {self.max_reminders} "
                    f"reminders. Still has {incomplete_count} incomplete tasks. "
                    f"Agent is ignoring critical reminders and refusing to work."
                )
            else:
                # All tasks completed - inject final confirmation
                if len(todos) > 0:
                    logger.warning(
                        "Agent completed all tasks but stopped without confirmation. "
                        "Injecting final confirmation prompt."
                    )

                    original_query = "[User's original request]"  # Default placeholder
                    if request.messages:
                        for msg in request.messages:
                            if isinstance(msg, HumanMessage):
                                if isinstance(msg.content, str):
                                    original_query = msg.content
                                break

                    # logger.debug(f"Found original user query: {original_query}")

                    # Try multiple reminders in the same stopping attempt
                    final_response = response
                    for attempt in range(self.max_reminders):
                        final_confirmation_reminder = (
                            self.final_confirmation_template.replace(
                                "{{all_tasks_count}}", str(len(todos))
                            ).replace("[User's original request]", original_query)
                        )
                        request.messages.append(
                            SystemMessage(content=final_confirmation_reminder)
                        )

                        # Force the model to re-think with the final confirmation
                        # reminder
                        final_response = handler(request)

                        # Check if agent is still stopping after reminder
                        still_stopping = self._is_agent_stopping(final_response)

                        if not still_stopping:
                            # Agent is working again, return the good response
                            return final_response

                    logger.warning(
                        "Agent is still stopping without confirmation after "
                        f"{self.max_reminders} final confirmation reminders. "
                        "Returning original response."
                    )

        # 6. Either agent didn't stop, or todos are complete - return original response
        return response

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        """
        Intercept model call to prevent premature stopping.

        This method:
        1. Allows the model to run and make its decision
        2. Checks if the model call is malformed
        3. If the model call is malformed, injects a critical reminder and
           forces re-thinking
        4. Checks if the model is attempting to stop prematurely
        5. If stopping is premature, injects a critical reminder and forces
           re-thinking
        6. Returns either the original or modified response

        Args:
            request: The model request containing state and messages
            handler: The next handler in the middleware chain

        Returns:
            ModelCallResult with potentially modified response
        """
        # 1. Let the model run and make its decision
        response = await handler(request)

        # 2. Check if the model performed a malformed function call
        if self._is_malformed_call(response):
            logger.warning(
                "Detected MALFORMED_FUNCTION_CALL from model. "
                "Attempting auto-recovery..."
            )

            for retry in range(self.max_retries_malformed):
                # Add error message to ask model to fix the error
                error_msg = (
                    "<system_critical_reminder> Your last function call was "
                    "malformed (invalid JSON or schema). "
                    "Please analyze the tool schema carefully and try calling "
                    "the function again with valid arguments. "
                    "</system_critical_reminder>"
                )
                request.messages.append(SystemMessage(content=error_msg))

                # Call model again
                response = await handler(request)

                # If no more error, exit retry loop
                if not self._is_malformed_call(response):
                    logger.info("Recovered from MALFORMED_FUNCTION_CALL successfully.")
                    break

            # If still error after retry, raise error or let it fall through
            # to the next logic (will fail)
            if self._is_malformed_call(response):
                logger.error(
                    "Failed to recover from MALFORMED_FUNCTION_CALL after retries."
                )

        # 3. Check if model is attempting to stop (empty AI response without tool calls)
        # logger.debug(f"Model response: {response}")
        is_stopping = self._is_agent_stopping(response)
        # logger.debug(f"Is agent stopping? {is_stopping}")

        # 4. If agent is stopping, check if todos are complete
        if is_stopping:
            todos = request.state.get("todos", [])
            if not isinstance(todos, list):
                raise TypeError("Todos in agent state must be a list.")
            incomplete_tasks = self._get_incomplete_tasks(todos)

            # 5. If there are incomplete tasks, force continuation
            if isinstance(incomplete_tasks, dict) and (
                len(incomplete_tasks.get("in_progress", [])) > 0
                or len(incomplete_tasks.get("pending", [])) > 0
            ):
                logger.warning(
                    f"Agent attempted to stop with "
                    f"{len(incomplete_tasks.get('pending', []))} pending and "
                    f"{len(incomplete_tasks.get('in_progress', []))} in-progress "
                    "tasks. Injecting critical reminder to continue working."
                )
                # Try multiple reminders in the same stopping attempt
                current_response = response
                for attempt in range(self.max_reminders):
                    # Generate critical reminder
                    re_prompt = self._generate_re_prompt(incomplete_tasks)

                    # Add re-prompt to conversation history
                    request.messages.append(SystemMessage(content=re_prompt))

                    # Force the model to re-think with the critical reminder
                    current_response = await handler(request)

                    # Check if agent is still stopping after reminder
                    still_stopping = self._is_agent_stopping(current_response)

                    if not still_stopping:
                        # Agent is working again, return the good response
                        return current_response

                    # logger.debug(f"Model response after reminder: {current_response}")

                    # Update incomplete tasks for next attempt
                    todos = request.state.get("todos", [])
                    if not isinstance(todos, list):
                        raise TypeError("Todos in agent state must be a list.")
                    incomplete_tasks = self._get_incomplete_tasks(todos)
                    if not isinstance(incomplete_tasks, dict):
                        incomplete_tasks = {"pending": [], "in_progress": []}
                    if not incomplete_tasks:
                        # All tasks completed, return response
                        return current_response

                # If we get here, agent ignored all reminders
                if isinstance(incomplete_tasks, dict):
                    incomplete_count = len(incomplete_tasks.get("pending", [])) + len(
                        incomplete_tasks.get("in_progress", [])
                    )
                else:
                    incomplete_count = 0
                raise RuntimeError(
                    f"Agent failed to complete tasks after {self.max_reminders} "
                    f"reminders. Still has {incomplete_count} incomplete tasks. "
                    f"Agent is ignoring critical reminders and refusing to work."
                )
            else:
                # All tasks completed - inject final confirmation
                if len(todos) > 0:
                    logger.warning(
                        "Agent completed all tasks but stopped without confirmation. "
                        "Injecting final confirmation prompt."
                    )

                    original_query = "[User's original request]"  # Default placeholder
                    if request.messages:
                        for msg in request.messages:
                            if isinstance(msg, HumanMessage):
                                if isinstance(msg.content, str):
                                    original_query = msg.content
                                break

                    # logger.debug(f"Found original user query: {original_query}")

                    # Try multiple reminders in the same stopping attempt
                    final_response = response
                    for attempt in range(self.max_reminders):
                        final_confirmation_reminder = (
                            self.final_confirmation_template.replace(
                                "{{all_tasks_count}}", str(len(todos))
                            ).replace("[User's original request]", original_query)
                        )
                        request.messages.append(
                            SystemMessage(content=final_confirmation_reminder)
                        )

                        # Force the model to re-think with the final confirmation
                        # reminder
                        final_response = await handler(request)

                        # Check if agent is still stopping after reminder
                        still_stopping = self._is_agent_stopping(final_response)

                        if not still_stopping:
                            # Agent is working again, return the good response
                            return final_response

                    logger.warning(
                        "Agent is still stopping without confirmation after "
                        f"{self.max_reminders} final confirmation reminders. "
                        "Returning original response."
                    )

        # 6. Either agent didn't stop, or todos are complete - return original response
        return response

    def _is_malformed_call(self, response: ModelResponse) -> bool:
        """
        Determine if the response indicates that the model
        performed a malformed function call.

        Args:
            response: The model response to check

        Returns:
            bool: True if the response indicates a malformed
                function call, False otherwise
        """
        # Get the last AIMessage from the response
        if not hasattr(response, "result"):
            return False

        result = response.result  # type: ignore
        if not result or len(result) == 0:
            return False

        last_ai_message = result[-1]
        if not last_ai_message:
            # No message found, cannot determine stopping
            logger.warning("No message found in response")
            return False

        if (
            last_ai_message.response_metadata
            and last_ai_message.response_metadata.get("finish_reason")
            == "MALFORMED_FUNCTION_CALL"
        ):
            return True

        return False

    def _is_agent_stopping(self, response: ModelResponse) -> bool:
        """
        Determine if the agent is attempting to stop.

        Args:
            response: The model response to check

        Returns:
            bool: True if agent is stopping, False otherwise
        """
        # Get the last AIMessage from the response
        if not hasattr(response, "result"):
            return False

        result = response.result  # type: ignore
        if not result or len(result) == 0:
            return False

        last_ai_message = result[-1]
        if not last_ai_message:
            # No message found, cannot determine stopping
            logger.warning("No message found in response")
            return False

        if last_ai_message.content is not None:
            # Check string content
            if (
                isinstance(last_ai_message.content, str)
                and last_ai_message.content.strip() != ""
            ):
                return False  # Has text content, not stopping

            # Check list content - iterate ALL items to find text
            # Thinking models put thinking blocks before text blocks,
            # so we must check all items, not just content[0]
            if isinstance(last_ai_message.content, list):
                for part in last_ai_message.content:
                    if (
                        isinstance(part, dict)
                        and part.get("type") == "text"
                        and isinstance(part.get("text"), str)
                        and part["text"].strip() != ""
                    ):
                        return False  # Has text content, not stopping

        # Check for function calls
        if (
            last_ai_message.additional_kwargs is not None
            and "function_call" in last_ai_message.additional_kwargs
        ):
            return False  # Has function call, not stopping

        # No content and no function call - check finish reason
        if last_ai_message.response_metadata is not None:
            metadata = last_ai_message.response_metadata
            if metadata.get("finish_reason") == "STOP":
                # Model indicated stopping
                return True

        # Default case: not stopping
        return False

    def _get_incomplete_tasks(self, todos: List[TodoItem]) -> Dict[str, List[TodoItem]]:
        """
        Identify incomplete tasks from the todo list.

        Args:
            todos: List of todo items to check

        Returns:
            Dict containing incomplete tasks categorized by status
        """
        pending_tasks = [t for t in todos if t.get("status") == "pending"]
        in_progress_tasks = [t for t in todos if t.get("status") == "in_progress"]

        return {"pending": pending_tasks, "in_progress": in_progress_tasks}

    def _generate_re_prompt(self, incomplete_tasks: Dict[str, List[TodoItem]]) -> str:
        """
        Generate a critical reminder to force task continuation.

        Args:
            incomplete_tasks: Dictionary of incomplete tasks

        Returns:
            str: Formatted re-prompt message
        """
        if not isinstance(incomplete_tasks, dict):
            return "Please continue working on your tasks."

        pending_tasks = incomplete_tasks.get("pending", [])
        in_progress_tasks = incomplete_tasks.get("in_progress", [])

        # Determine next task instruction
        next_task_instruction = ""
        if in_progress_tasks:
            next_task = in_progress_tasks[0]
            next_task_content = next_task.get("content", "Unknown task")
            next_task_status = "in_progress" if next_task_content else "unknown"
            next_task_instruction = (
                "Your current active task is: "
                f'"{next_task_content}" '
                f"(status: {next_task_status})."
            )
        elif pending_tasks:
            next_task = pending_tasks[0]
            next_task_content = next_task.get("content", "Unknown task")
            next_task_status = "pending" if next_task_content else "unknown"
            next_task_instruction = (
                f'Your next task is: "{next_task_content}" '
                f"(status: {next_task_status})."
            )

        return (
            self.re_prompt_template.replace(
                "{{in_progress_count}}", str(len(in_progress_tasks))
            )
            .replace("{{pending_count}}", str(len(pending_tasks)))
            .replace("{{next_task_instruction}}", next_task_instruction)
            .replace("{{write_todos_function_name}}", self.tool_name)
        )
