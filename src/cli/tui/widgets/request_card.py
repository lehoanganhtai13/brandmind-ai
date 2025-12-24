"""
Request card widget with collapsible sections.

Displays query, thinking, tool calls, logs, and answer.
Logs are collapsed by default, expanded with Ctrl+O.
"""

from __future__ import annotations

import time
from typing import Any, ClassVar

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from shared.agent_middlewares.callback_types import (
    BaseAgentEvent,
    ModelLoadingEvent,
    ThinkingEvent,
    TodoUpdateEvent,
    ToolCallEvent,
    ToolResultEvent,
)


class RequestCard(Widget):
    """Card displaying a single request/response cycle.

    Features:
    - Rounded border (via CSS)
    - Collapsible thinking/logs sections
    - Ctrl+O toggles expand state
    - Real-time event updates from agent

    Attributes:
        query: The user's query string
        is_expanded: Whether logs are expanded
    """

    # fmt: off
    DEFAULT_CSS: ClassVar[str] = """
    RequestCard {
        border: round #30363d;
        background: #161b22;
        padding: 1;
        margin: 1 0;
        width: 100%;
    }

    RequestCard:focus {
        border: round #6DB3B3;
    }

    RequestCard .query-header {
        color: #6DB3B3;
        text-style: bold;
        margin-bottom: 1;
    }

    RequestCard .thinking-section {
        margin: 0 0 1 0;
    }

    RequestCard .thinking-header {
        color: #8FCECE;
        text-style: bold;
    }

    RequestCard .thinking-content {
        color: #8b949e;
        margin-left: 2;
    }

    RequestCard .tool-section {
        margin: 0 0 1 0;
    }

    RequestCard .tool-header {
        color: #E8834A;
        text-style: bold;
    }

    RequestCard .tool-args {
        color: #8b949e;
        margin-left: 2;
    }

    RequestCard .tool-logs {
        color: #6e7681;
        text-style: italic;
        margin-left: 2;
    }

    RequestCard .answer-section {
        border-top: solid #30363d;
        padding-top: 1;
        margin-top: 1;
    }

    RequestCard .answer-header {
        color: #6DB3B3;
        text-style: bold;
    }

    RequestCard .answer-content {
        color: #e6edf3;
        margin-left: 2;
    }

    RequestCard .spinner-section {
        color: #8FCECE;
    }
    """
    # fmt: on

    is_expanded: reactive[bool] = reactive(False)
    is_loading: reactive[bool] = reactive(False)

    def __init__(self, query: str, id: str | None = None) -> None:
        """Initialize request card.

        Args:
            query: User's query string
            id: Widget ID
        """
        super().__init__(id=id)
        self.query = query
        self._thinking_content: str = ""
        self._tool_events: list[dict[str, Any]] = []
        self._answer: str = ""
        self._last_refresh: float = 0.0

    def compose(self) -> ComposeResult:
        """Compose card contents."""
        yield Static(f"[bold #6DB3B3]Q:[/] {self.query}", classes="query-header")

        # Spinner shown while loading
        yield Static("● Thinking...", id="spinner", classes="spinner-section")

        # Thinking section (collapsible)
        yield Vertical(id="thinking-container", classes="thinking-section")

        # Tools section
        yield Vertical(id="tools-container", classes="tool-section")

        # Answer section
        yield Vertical(id="answer-container", classes="answer-section")

    def on_mount(self) -> None:
        """Initialize display state on mount."""
        self.query_one("#spinner", Static).display = False
        self.query_one("#answer-container", Vertical).display = False

    def show_spinner(self) -> None:
        """Show thinking spinner."""
        self.is_loading = True
        self.query_one("#spinner", Static).display = True

    def hide_spinner(self) -> None:
        """Hide thinking spinner."""
        self.is_loading = False
        self.query_one("#spinner", Static).display = False

    def toggle_expand(self) -> None:
        """Toggle expanded/collapsed state."""
        self.is_expanded = not self.is_expanded
        # Use call_later to avoid blocking - schedule refresh
        self.call_later(self._do_refresh_content)

    def handle_event(self, event: BaseAgentEvent) -> None:
        """Handle agent event and update display.

        Args:
            event: Agent event from callback
        """
        if isinstance(event, ModelLoadingEvent):
            if event.loading:
                self.show_spinner()
            else:
                self.hide_spinner()

        elif isinstance(event, ThinkingEvent):
            self._update_thinking(event.content)

        elif isinstance(event, ToolCallEvent):
            self._add_tool_call(event.tool_name, event.arguments)

        elif isinstance(event, ToolResultEvent):
            self._update_tool_result(event.tool_name, event.result)

        elif isinstance(event, TodoUpdateEvent):
            # TODO: Handle todos if needed
            pass

        self._debounced_refresh()

    def _update_thinking(self, content: str) -> None:
        """Update thinking section.

        Args:
            content: Thinking content string
        """
        self.hide_spinner()
        self._thinking_content = content
        self._refresh_thinking()

    def _refresh_thinking(self) -> None:
        """Refresh thinking display."""
        container = self.query_one("#thinking-container", Vertical)

        # Clear existing content
        container.remove_children()

        if not self._thinking_content:
            return

        # Header
        header = Static("● Thinking", classes="thinking-header")
        container.mount(header)

        # Content (truncated unless expanded)
        content = self._thinking_content
        if not self.is_expanded and len(content) > 200:
            content = content[:200] + "... [dim](Ctrl+O to expand)[/dim]"

        content_widget = Static(content, classes="thinking-content")
        container.mount(content_widget)

    def _add_tool_call(self, name: str, args: dict[str, Any]) -> None:
        """Add tool call to display.

        Args:
            name: Tool name
            args: Tool arguments
        """
        # Skip write_todos tool from display
        if name == "write_todos":
            return

        # Check for duplicate
        for tool in self._tool_events:
            if tool["name"] == name and tool["args"] == args:
                return

        self._tool_events.append(
            {
                "name": name,
                "args": args,
                "result": None,
                "done": False,
                "logs": [],
            }
        )
        self._refresh_tools()

    def _update_tool_result(self, name: str, result: str) -> None:
        """Update tool call with result.

        Args:
            name: Tool name
            result: Tool result string
        """
        # Find matching tool (most recent with this name)
        for tool in reversed(self._tool_events):
            if tool["name"] == name and not tool["done"]:
                tool["result"] = result
                tool["done"] = True
                break
        self._refresh_tools()

    def _refresh_tools(self) -> None:
        """Refresh tools display."""
        container = self.query_one("#tools-container", Vertical)
        container.remove_children()

        for tool in self._tool_events:
            tool_widget = self._create_tool_widget(tool)
            container.mount(tool_widget)

    def _create_tool_widget(self, tool: dict[str, Any]) -> Static:
        """Create widget for a single tool call.

        Args:
            tool: Tool event dict

        Returns:
            Static widget for the tool
        """
        name = tool["name"]
        args = tool["args"]
        done = tool["done"]
        logs = tool.get("logs", [])

        # Icon based on status
        icon = "✓" if done else "⟳"
        icon_color = "#6DB3B3" if done else "#E8834A"

        # Build text
        lines = [f"[bold {icon_color}]{icon} {name}[/]"]

        # Arguments
        for k, v in args.items():
            val_str = str(v)[:60]
            if len(str(v)) > 60:
                val_str += "..."
            lines.append(f"  [dim]{k}:[/dim] {val_str}")

        # Logs
        if logs:
            if self.is_expanded:
                for log in logs[-5:]:
                    lines.append(f"  [italic #6e7681]📋 {log}[/]")
                if len(logs) > 5:
                    lines.append(f"  [italic #6e7681]... +{len(logs) - 5} more[/]")
            else:
                lines.append(
                    f"  [italic #6e7681]📋 [{len(logs)} logs] (Ctrl+O to expand)[/]"
                )

        # Result preview
        if done and tool.get("result"):
            result = tool["result"]
            preview = result[:100]
            if len(result) > 100:
                preview += f"... (+{len(result) - 100} chars)"
            lines.append(f"  [#8FCECE]Result:[/] {preview}")

        return Static("\n".join(lines), classes="tool-header")

    def set_answer(self, answer: str) -> None:
        """Set final answer.

        Args:
            answer: Answer content string
        """
        self.hide_spinner()
        self._answer = answer
        self._refresh_answer()

    def _refresh_answer(self) -> None:
        """Refresh answer display."""
        container = self.query_one("#answer-container", Vertical)
        container.remove_children()

        if not self._answer:
            container.display = False
            return

        container.display = True

        # Header
        header = Static("[bold #6DB3B3]📝 Answer[/]", classes="answer-header")
        container.mount(header)

        # Content
        content = Static(self._answer, classes="answer-content")
        container.mount(content)

    def _refresh_content(self) -> None:
        """Refresh all content sections."""
        self._refresh_thinking()
        self._refresh_tools()
        self._refresh_answer()

    def _do_refresh_content(self) -> None:
        """Async-safe refresh triggered by call_later."""
        try:
            self._refresh_thinking()
            self._refresh_tools()
            self._refresh_answer()
        except Exception:
            pass  # Ignore errors during refresh

    def _debounced_refresh(self) -> None:
        """Debounce refresh to prevent flickering."""
        now = time.monotonic()
        if now - self._last_refresh > 0.033:  # ~30 FPS
            self.refresh()
            self._last_refresh = now

    def add_tool_log(self, tool_name: str, message: str) -> None:
        """Add log message to a tool.

        Args:
            tool_name: Name of the tool
            message: Log message
        """
        for tool in reversed(self._tool_events):
            if tool["name"] == tool_name and not tool["done"]:
                tool["logs"].append(message)
                # Re-render tools to show new log
                self._refresh_tools()
                break
        self._debounced_refresh()
