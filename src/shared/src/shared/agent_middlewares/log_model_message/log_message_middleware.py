"""
Log Model Message Middleware for LangGraph Agents

This middleware logs model thinking/reasoning messages in real-time
to help debug and understand agent decision-making processes.
"""

from collections.abc import Awaitable, Callable

from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelCallResult,
    ModelRequest,
    ModelResponse,
)
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest
from langgraph.types import Command
from loguru import logger


class LogModelMessageMiddleware(AgentMiddleware):
    """
    Middleware that logs model thinking and reasoning messages in real-time.

    This middleware intercepts model responses and extracts thinking/reasoning
    content to provide visibility into the agent's decision-making process.

    Key Features:
    - Logs thinking blocks from model responses
    - Logs text responses separately from tool calls
    - Logs tool calls and their results
    - Provides structured logging with emojis for readability
    - Non-intrusive - does not modify agent behavior
    """

    def __init__(
        self,
        *,
        log_thinking: bool = True,
        log_text_response: bool = True,
        log_tool_calls: bool = True,
        log_tool_results: bool = True,
        truncate_thinking: int = 0,  # 0 = no truncation
        truncate_tool_results: int = 500,  # Truncate tool results
        exclude_tools: list[str] | None = None,  # Tools to exclude from logging
    ):
        """
        Initialize the logging middleware.

        Args:
            log_thinking: Whether to log thinking blocks
            log_text_response: Whether to log text responses
            log_tool_calls: Whether to log tool call summaries
            log_tool_results: Whether to log tool results
            truncate_thinking: Max characters for thinking (0 = no limit)
            truncate_tool_results: Max characters for tool results
            exclude_tools: List of tool names to exclude from result logging
        """
        super().__init__()
        self.log_thinking = log_thinking
        self.log_text_response = log_text_response
        self.log_tool_calls = log_tool_calls
        self.log_tool_results = log_tool_results
        self.truncate_thinking = truncate_thinking
        self.truncate_tool_results = truncate_tool_results
        self.exclude_tools = exclude_tools or []

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        """
        Synchronous version of awrap_model_call.

        Logs model responses without modifying them.
        """
        # Let the model run normally
        response = handler(request)

        # Log the response
        self._log_response(response)

        return response

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        """
        Intercept model call to log thinking/reasoning messages.

        This method:
        1. Allows the model to run normally
        2. Extracts and logs thinking/reasoning content
        3. Returns the original response unmodified

        Args:
            request: The model request
            handler: The next handler in the chain

        Returns:
            The unmodified model response
        """
        # Let the model run normally
        response = await handler(request)

        # Log the response
        self._log_response(response)

        return response

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """
        Intercept tool calls to log them in real-time.

        This method logs tool execution as it happens, not from message history.

        Args:
            request: Tool call request
            handler: Next handler in chain

        Returns:
            Tool result
        """
        tool_name = request.tool_call.get("name", "unknown_tool")
        tool_args = request.tool_call.get("args", {})

        # Skip excluded tools
        if tool_name in self.exclude_tools:
            return handler(request)

        # Log tool call with arguments
        if self.log_tool_calls:
            logger.info(f"🔧 Tool Call: {tool_name}")
            if tool_args:
                for key, value in tool_args.items():
                    # Truncate long values
                    val_str = str(value)
                    if len(val_str) > 100:
                        val_str = val_str[:100] + "..."
                    logger.info(f"     └─ {key}: {val_str}")

        try:
            # Execute tool
            result = handler(request)

            # Log result
            if self.log_tool_results and hasattr(result, "text"):
                content = result.text
                if content:
                    # Truncate if needed
                    if self.truncate_tool_results > 0:
                        if len(content) > self.truncate_tool_results:
                            content = content[: self.truncate_tool_results] + "..."

                    logger.info(f"🔨 Tool Result [{tool_name}]:\n{content}")

            return result

        except Exception as e:
            logger.error(f"❌ Tool Error [{tool_name}]: {e}")
            raise

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        """
        Async version of wrap_tool_call.

        Args:
            request: Tool call request
            handler: Async handler

        Returns:
            Tool result
        """
        tool_name = request.tool_call.get("name", "unknown_tool")
        tool_args = request.tool_call.get("args", {})

        # Skip excluded tools
        if tool_name in self.exclude_tools:
            return await handler(request)

        # Log tool call with arguments
        if self.log_tool_calls:
            logger.info(f"🔧 Tool Call: {tool_name}")
            if tool_args:
                for key, value in tool_args.items():
                    # Truncate long values
                    val_str = str(value)
                    if len(val_str) > 100:
                        val_str = val_str[:100] + "..."
                    logger.info(f"     └─ {key}: {val_str}")

        try:
            # Execute tool
            result = await handler(request)

            # Log result
            if self.log_tool_results and hasattr(result, "text"):
                content = result.text
                if content:
                    # Truncate if needed
                    if self.truncate_tool_results > 0:
                        if len(content) > self.truncate_tool_results:
                            content = content[: self.truncate_tool_results] + "..."

                    logger.info(f"🔨 Tool Result [{tool_name}]:\n{content}")

            return result

        except Exception as e:
            logger.error(f"❌ Tool Error [{tool_name}]: {e}")
            raise

    def _log_response(self, response: ModelResponse) -> None:
        """
        Extract and log thinking/reasoning from model response.

        Args:
            response: The model response to log
        """
        # Get the last AIMessage from the response
        last_ai_message = None
        if hasattr(response, "result"):
            result = response.result  # type: ignore
            if result and len(result) > 0:
                last_ai_message = result[-1]

        if not last_ai_message:
            return

        # Extract content
        if not hasattr(last_ai_message, "content") or not last_ai_message.content:
            return

        content = last_ai_message.content

        # Handle list content (thinking + text)
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    # Log thinking blocks
                    if part.get("type") == "thinking" and self.log_thinking:
                        thinking = part.get("thinking", "")
                        if thinking:
                            # Truncate if needed
                            if self.truncate_thinking > 0:
                                if len(thinking) > self.truncate_thinking:
                                    thinking = (
                                        thinking[: self.truncate_thinking] + "..."
                                    )

                            logger.info(f"💭 Model Thinking:\n{thinking}")

                    # Log text responses
                    elif part.get("type") == "text" and self.log_text_response:
                        text = part.get("text", "")
                        if text:
                            logger.info(f"📝 Model Response:\n{text}")

        # Handle string content
        elif isinstance(content, str) and self.log_text_response:
            if content.strip():
                logger.info(f"📝 Model Response:\n{content}")

    def _log_tool_calls(self, tool_calls: list) -> None:
        """
        Log tool calls with their parameters.

        Args:
            tool_calls: List of tool call dictionaries
        """
        logger.info(f"🔧 Model Tool Calls ({len(tool_calls)}):")
        for i, tc in enumerate(tool_calls, 1):
            tool_name = tc.get("name", "unknown")
            tool_args = tc.get("args", {})

            # Format args for display
            if tool_args:
                args_str = ", ".join(
                    f"{k}={repr(v)[:100]}" for k, v in tool_args.items()
                )
                logger.info(f"  {i}. {tool_name}({args_str})")
            else:
                logger.info(f"  {i}. {tool_name}()")
