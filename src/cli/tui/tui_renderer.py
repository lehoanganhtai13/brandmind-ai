"""
TUI Renderer - Direct append pattern with in-place updates.

Features:
- Animated spinner using Rich Spinner + set_interval
- Spinner shows during model loading (ModelLoadingEvent)
- Markdown rendering for all content
- In-place tool updates with expand/collapse
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.spinner import Spinner as RichSpinner
from textual.widgets import Markdown, Static

from shared.agent_middlewares.callback_types import (
    BaseAgentEvent,
    ModelLoadingEvent,
    ThinkingEvent,
    TodoUpdateEvent,
    ToolCallEvent,
    ToolResultEvent,
)

if TYPE_CHECKING:
    from textual.containers import ScrollableContainer


def _snake_to_pascal(name: str) -> str:
    """Convert snake_case to PascalCase.

    Example: search_document_library -> SearchDocumentLibrary
    """
    return "".join(word.capitalize() for word in name.split("_"))


class SpinnerWidget(Static):
    """Animated spinner widget using Rich Spinner."""

    def __init__(self) -> None:
        super().__init__("")
        self._spinner = RichSpinner(
            "dots", text="[bold #8FCECE]Thinking...[/bold #8FCECE]"
        )
        self._interval = None

    def on_mount(self) -> None:
        """Start animation when mounted."""
        self._interval = self.set_interval(1 / 30, self._update_spinner)

    def _update_spinner(self) -> None:
        """Update spinner animation frame."""
        self.update(self._spinner)

    def on_unmount(self) -> None:
        """Stop animation when unmounted."""
        if self._interval:
            self._interval.stop()


class TUIRenderer:
    """Appends output directly to main-body like terminal.

    Features:
    - Animated spinner during model loading
    - Markdown rendering for all content
    - In-place tool updates
    """

    def __init__(
        self,
        main_body: "ScrollableContainer",
        is_expanded: bool = False,
    ) -> None:
        self.main_body = main_body
        self.is_expanded = is_expanded
        self._app = main_body.app

        # Spinner widget
        self._spinner: SpinnerWidget | None = None
        self._is_loading: bool = False

        # Track thinking blocks for expand/collapse
        self._thinking_widgets: list[Markdown] = []
        self._thinking_contents: list[str] = []

        # Track tools for in-place updates
        self._tool_widgets: dict[str, Static] = {}
        self._tool_data: dict[str, dict] = {}

        # Track tool result widgets for expand/collapse
        self._tool_result_widgets: dict[str, Markdown] = {}

        # Track todos
        self._todos: list[dict] = []
        self._todo_widget: Static | None = None

        # Tool call counter for unique keys (same tool can be called multiple times)
        self._tool_call_counter: int = 0
        self._current_tool_key: str | None = None  # Key of most recent tool call

        # Deduplication
        self._last_thinking: str = ""

        # Cancellation flag - ignore events after cancel
        self._cancelled: bool = False

    def show_query(self, query: str) -> None:
        """Append query to main body."""
        widget = Static(f"\n[dim]>[/dim] [bold]{query}[/bold]")
        self.main_body.mount(widget)
        self._scroll()

    def show_spinner(self) -> None:
        """Show animated spinner."""
        if not self._spinner:
            self._spinner = SpinnerWidget()
            self.main_body.mount(self._spinner)
            self._scroll()

    def hide_spinner(self) -> None:
        """Remove spinner widget."""
        if self._spinner:
            self._spinner.remove()
            self._spinner = None

    def handle_event(self, event: BaseAgentEvent) -> None:
        """Handle event - schedule on main thread."""
        # Ignore events if cancelled
        if self._cancelled:
            return
        try:
            self._app.call_later(self._process_event, event)
        except Exception:
            pass

    def cancel(self) -> None:
        """Mark renderer as cancelled to ignore subsequent events."""
        self._cancelled = True
        self.hide_spinner()

    def _process_event(self, event: BaseAgentEvent) -> None:
        """Process event on main thread."""
        # Double check cancelled in case event was already scheduled
        if self._cancelled:
            return

        if isinstance(event, ModelLoadingEvent):
            self._on_model_loading(event.loading)
        elif isinstance(event, ThinkingEvent):
            self._on_thinking(event.content)
        elif isinstance(event, ToolCallEvent):
            self._on_tool_call(event)
        elif isinstance(event, ToolResultEvent):
            self._on_tool_result(event)
        elif isinstance(event, TodoUpdateEvent):
            self._on_todo_update(event.todos)

    def _on_model_loading(self, loading: bool) -> None:
        """Handle model loading state - show/hide spinner."""
        self._is_loading = loading
        if loading:
            self.show_spinner()
        else:
            self.hide_spinner()

    def _on_thinking(self, content: str) -> None:
        """Append thinking block with Markdown rendering."""
        # Deduplication
        if self._last_thinking:
            if content.startswith(self._last_thinking[:50]):
                return
            if self._last_thinking.startswith(content[:50]) and len(content) <= len(
                self._last_thinking
            ):
                return

        self._last_thinking = content
        self.hide_spinner()

        # Store full content
        self._thinking_contents.append(content)

        # Create header
        header = Static("\n[bold #8FCECE]● Thinking[/bold #8FCECE]")
        self.main_body.mount(header)

        # Create Markdown widget for content
        display_content = self._get_thinking_display(content)
        md_widget = Markdown(display_content)
        self.main_body.mount(md_widget)
        self._thinking_widgets.append(md_widget)

        self._scroll()

    def _get_thinking_display(self, content: str) -> str:
        """Get display content based on expand state."""
        if self.is_expanded or len(content) <= 600:
            return content
        # Inline Ctrl+O hint at end of truncated text
        return content[:600] + " *... (Ctrl+O to expand)*"

    def _on_tool_call(self, event: ToolCallEvent) -> None:
        """Create tool widget."""
        if event.tool_name == "write_todos":
            return

        self.hide_spinner()

        # Create unique key for this tool call
        self._tool_call_counter += 1
        call_key = f"{event.tool_name}_{self._tool_call_counter}"
        self._current_tool_key = call_key

        self._tool_data[call_key] = {
            "name": event.tool_name,
            "args": event.arguments,
            "logs": [],
            "result": None,
            "done": False,
        }

        widget = Static(self._build_tool_display(call_key))
        self.main_body.mount(widget)
        self._tool_widgets[call_key] = widget

        self._scroll()

    def _on_tool_result(self, event: ToolResultEvent) -> None:
        """Update tool widget in-place."""
        if event.tool_name == "write_todos":
            return

        # Find the most recent undone tool call with this name
        call_key = None
        for key in reversed(list(self._tool_data.keys())):
            data = self._tool_data[key]
            if data.get("name") == event.tool_name and not data.get("done"):
                call_key = key
                break

        if not call_key:
            return

        self._tool_data[call_key]["result"] = event.result
        self._tool_data[call_key]["done"] = True

        if call_key in self._tool_widgets:
            # Update Static widget in-place (header + args + logs)
            widget = self._tool_widgets[call_key]
            widget.update(self._build_tool_display(call_key))

            # Mount separate Markdown widget for result content
            if event.result:
                result_content = self._get_result_display(event.result)
                result_widget = Markdown(result_content)
                self.main_body.mount(result_widget)
                # Track for expand/collapse
                self._tool_result_widgets[call_key] = result_widget

        self._scroll()

    def _on_todo_update(self, todos: list) -> None:
        """Display/update todo list in docked #todo-bar widget."""
        self._todos = todos

        # Build todo display
        lines = ["[bold]📋 Todos[/bold]"]
        for todo in todos:
            status = todo.get("status", "pending")
            content = todo.get("content", "")
            if status == "completed":
                lines.append(f"   [green]☒[/green] [dim strike]{content}[/dim strike]")
            elif status == "in_progress":
                lines.append(f"   [bold #afafff]☐ {content}[/bold #afafff]")
            else:
                lines.append(f"   ☐ {content}")

        display = "\n".join(lines)

        # Query global #todo-bar widget and update
        try:
            todo_bar = self._app.query_one("#todo-bar", Static)
            todo_bar.update(display)
            # Show the widget (remove hidden class)
            todo_bar.remove_class("hidden")
        except Exception:
            pass

    def _build_tool_display(self, call_key: str) -> str:
        """Build tool display for Static widget (running state)."""
        data = self._tool_data.get(call_key, {})
        tool_name = data.get("name", call_key.rsplit("_", 1)[0])  # Fallback to parsing
        args = data.get("args", {})
        logs = data.get("logs", [])
        done = data.get("done", False)

        # Convert to PascalCase for display
        display_name = _snake_to_pascal(tool_name)

        # Style like thinking block with colored dot
        # Running: orange dot ◐, Done: green dot ●
        if done:
            lines = [f"\n[bold #6DB3B3]● {display_name}[/bold #6DB3B3]"]
        else:
            lines = [f"\n[bold #E8834A]◐ {display_name}[/bold #E8834A]"]

        for k, v in args.items():
            val = str(v)[:50] + "..." if len(str(v)) > 50 else str(v)
            lines.append(f"  [dim]{k}:[/dim] {val}")

        if logs:
            if self.is_expanded:
                lines.append("  [bold]📋 Logs:[/bold]")
                for log in logs[-5:]:
                    lines.append(f"    [dim]{log}[/dim]")
                if len(logs) > 5:
                    lines.append(f"    [italic #6e7681]... +{len(logs) - 5} more[/]")
            else:
                # Inline log count
                lines.append(f"  [italic #6e7681]📋 [{len(logs)} logs] (Ctrl+O)[/]")

        return "\n".join(lines)

    def _get_result_display(self, result: str) -> str:
        """Get result content based on expand state."""
        result_str = str(result)
        if self.is_expanded or len(result_str) <= 400:
            return result_str
        return result_str[:400] + f"\n\n*... (+{len(result_str) - 400} chars)*"

    def _build_tool_markdown(self, tool_name: str) -> str:
        """Build tool display as Markdown (for result with proper formatting)."""
        data = self._tool_data.get(tool_name, {})
        args = data.get("args", {})
        logs = data.get("logs", [])
        result = data.get("result")
        done = data.get("done", False)

        lines = []

        # Convert to PascalCase for display
        display_name = _snake_to_pascal(tool_name)

        # Header with styled dot (like thinking block)
        if done:
            lines.append(f"**● {display_name}**")
        else:
            lines.append(f"**◐ {display_name}**")

        # Arguments
        for k, v in args.items():
            val = str(v)[:50] + "..." if len(str(v)) > 50 else str(v)
            lines.append(f"  - {k}: `{val}`")

        # Logs
        if logs:
            if self.is_expanded:
                lines.append("\n**📋 Logs:**")
                for log in logs[-5:]:
                    lines.append(f"  - {log}")
                if len(logs) > 5:
                    lines.append(f"  - *... +{len(logs) - 5} more*")
            else:
                lines.append(f"  - *📋 [{len(logs)} logs] (Ctrl+O)*")

        # Result as markdown
        if result:
            preview = str(result)[:400]
            if len(str(result)) > 400:
                preview += f"\n\n*... (+{len(str(result)) - 400} chars)*"
            lines.append(f"\n**Result:**\n{preview}")

        return "\n".join(lines)

    def add_tool_log(self, tool_name: str, message: str) -> None:
        """Add log - schedule on main thread."""
        # Ignore if cancelled
        if self._cancelled:
            return
        try:
            self._app.call_later(self._add_log, tool_name, message)
        except Exception:
            pass

    def _add_log(self, tool_name: str, message: str) -> None:
        """Add log and update tool widget."""
        # Find the most recent undone tool call with this name
        call_key = None
        for key in reversed(list(self._tool_data.keys())):
            data = self._tool_data[key]
            if data.get("name") == tool_name and not data.get("done"):
                call_key = key
                break

        if not call_key:
            return

        self._tool_data[call_key]["logs"].append(message)

        if call_key in self._tool_widgets:
            widget = self._tool_widgets[call_key]
            # Only update if widget is Static (not done yet)
            if isinstance(widget, Static) and not isinstance(widget, Markdown):
                widget.update(self._build_tool_display(call_key))
                self._scroll()

    def set_answer(self, answer: str) -> None:
        """Set answer - schedule on main thread."""
        # Ignore if cancelled
        if self._cancelled:
            return
        try:
            self._app.call_later(self._show_answer, answer)
        except Exception:
            pass

    def _show_answer(self, answer: str) -> None:
        """Append answer with Markdown."""
        # Ignore if cancelled
        if self._cancelled:
            return

        self.hide_spinner()

        header = Static(
            "\n[bold #6DB3B3]━━━ 📝 Answer ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold #6DB3B3]\n"  # noqa: E501
        )
        self.main_body.mount(header)

        # Use Markdown for answer content
        content = Markdown(answer)
        self.main_body.mount(content)

        footer = Static(
            "\n[bold #6DB3B3]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold #6DB3B3]\n"  # noqa: E501
        )
        self.main_body.mount(footer)

        self._scroll()

    def toggle_expand(self) -> None:
        """Toggle expand state."""
        self.is_expanded = not self.is_expanded
        self._refresh_all_widgets()

    def set_expanded(self, expanded: bool) -> None:
        """Set expand state."""
        if self.is_expanded != expanded:
            self.is_expanded = expanded
            self._refresh_all_widgets()

    def _refresh_all_widgets(self) -> None:
        """Refresh all widgets for expand/collapse."""
        # Refresh thinking (Markdown widgets)
        for i, widget in enumerate(self._thinking_widgets):
            if i < len(self._thinking_contents):
                content = self._thinking_contents[i]
                widget.update(self._get_thinking_display(content))

        # Refresh tool headers (Static widgets)
        for tool_name, widget in self._tool_widgets.items():
            if isinstance(widget, Static):
                widget.update(self._build_tool_display(tool_name))

        # Refresh tool results (Markdown widgets)
        for tool_name, widget in self._tool_result_widgets.items():
            data = self._tool_data.get(tool_name, {})
            result = data.get("result")
            if result:
                widget.update(self._get_result_display(result))

    def _scroll(self) -> None:
        """Scroll to bottom."""
        try:
            self.main_body.scroll_end(animate=False)
        except Exception:
            pass
