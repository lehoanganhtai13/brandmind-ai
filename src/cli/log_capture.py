"""
Smart log capture with automatic tool-based routing.

Uses contextvars to automatically determine which tool a log belongs to,
routing it to the appropriate section in the output renderer.

Key feature: Temporarily disables default loguru handler to prevent
logs from leaking to stdout while our capture is active.
"""

from typing import Callable, Optional

from loguru import logger

from cli.tool_context import get_current_tool


class SmartLogCapture:
    """
    Captures loguru logs and routes them based on tool context.

    Logs emitted during tool execution are grouped with that tool.
    Logs emitted outside tool execution go to "other_logs".

    IMPORTANT: This class temporarily removes the default loguru handler
    to prevent logs from appearing in stdout while capture is active.
    """

    def __init__(
        self,
        on_tool_log: Callable[[str, str], None],  # (tool_name, message)
        on_other_log: Callable[[str], None],  # (message)
    ):
        """
        Initialize log capture with routing callbacks.

        Args:
            on_tool_log: Called when log belongs to a tool: (tool_name, message)
            on_other_log: Called when log doesn't belong to any tool
        """
        self._on_tool_log = on_tool_log
        self._on_other_log = on_other_log
        self._handler_id: Optional[int] = None
        self._removed_handlers: list = []  # Store removed handler configs
        self.tool_logs: dict[str, list[str]] = {}
        self.other_logs: list[str] = []

    def _sink(self, message) -> None:
        """
        Custom loguru sink that routes logs based on context.

        Checks current_tool context to determine routing.
        """
        record = message.record

        # Format log message: module:function - message
        formatted = (
            f"{record['name'].split('.')[-1]}:{record['function']} - "
            f"{record['message']}"
        )

        # Check which tool is currently executing
        current_tool = get_current_tool()

        if current_tool:
            # Log belongs to a tool - route to tool section
            if current_tool not in self.tool_logs:
                self.tool_logs[current_tool] = []
            self.tool_logs[current_tool].append(formatted)
            self._on_tool_log(current_tool, formatted)
        else:
            # No tool context - route to other section
            self.other_logs.append(formatted)
            self._on_other_log(formatted)

    def start(self) -> None:
        """
        Start capturing logs.

        Removes default loguru handlers to prevent stdout leakage,
        then adds our custom routing handler.
        """
        # Remove ALL existing handlers (including default stderr handler)
        # This prevents logs from appearing in stdout
        try:
            logger.remove()  # Remove all handlers
        except ValueError:
            pass  # No handlers to remove

        # Add our custom routing handler
        self._handler_id = logger.add(
            self._sink,
            level="INFO",
            format="{message}",
            filter=lambda record: record["level"].name != "DEBUG",
        )

    def stop(self) -> None:
        """
        Stop capturing logs and restore default handler.
        """
        if self._handler_id is not None:
            logger.remove(self._handler_id)
            self._handler_id = None

        # Re-add default stderr handler
        logger.add(
            lambda msg: print(msg, end=""),  # Simple stderr-like output
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            level="INFO",
            colorize=True,
        )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def get_logs_for_tool(self, tool_name: str) -> list[str]:
        """Get all logs captured for a specific tool."""
        return self.tool_logs.get(tool_name, [])

    def clear(self) -> None:
        """Clear all captured logs."""
        self.tool_logs.clear()
        self.other_logs.clear()
