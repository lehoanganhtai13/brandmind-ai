"""
Rich-based renderer for agent output visualization.

Provides Claude Code-style real-time feedback during agent execution,
including thinking blocks, tool calls with inline logs, and todo tracking.
"""

from typing import Any

from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.text import Text
from rich.tree import Tree

from shared.agent_middlewares.callback_types import (
    BaseAgentEvent,
    ModelLoadingEvent,
    StreamingTokenEvent,
    ThinkingEvent,
    TodoUpdateEvent,
    ToolCallEvent,
    ToolResultEvent,
)


class AgentOutputRenderer:
    """
    Renders agent events in real-time using Rich Live display.

    Features:
    - Chronological event display (thinking and tools interleaved)
    - Tool calls as trees with inline logs
    - write_todos is hidden (only updates todo display)
    - Todo list at bottom, updates dynamically
    """

    def __init__(self, console: Console | None = None):
        """Initialize renderer."""
        self.console = console or Console()
        self._events: list[dict[str, Any]] = []
        self._tool_logs: dict[str, list[str]] = {}  # tool_name -> logs
        self._other_logs: list[str] = []
        self._todos: list[dict[str, Any]] = []
        self._live: Live | None = None
        self._is_loading: bool = False
        self._streaming_text: str = ""

    def start(self) -> None:
        """Start the live display."""
        self._live = Live(
            self._build_display(),
            console=self.console,
            refresh_per_second=4,
            vertical_overflow="visible",
        )
        self._live.start()

    def stop(self) -> None:
        """Stop the live display."""
        if self._live:
            self._live.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def handle_event(self, event: BaseAgentEvent) -> None:
        """
        Process agent event from middleware callback.
        Events are added to ordered list for chronological display.
        """
        if isinstance(event, ThinkingEvent):
            # Deduplication: Check if this thinking content is a version
            # (prefix/suffix) of any existing thinking block to prevent replays.
            for ev in self._events:
                if ev["type"] == "thinking":
                    c1 = ev["content"]
                    c2 = event.content

                    # Check if one is a prefix of the other (streaming)
                    # Length check to avoid matching short phrases
                    is_match = c1.startswith(c2) or c2.startswith(c1)

                    if len(c1) < 20 and len(c2) < 20:
                        # For very short content, require exact match
                        is_match = c1 == c2

                    if is_match:
                        # It matches an existing block
                        if ev is self._events[-1]:
                            # It's the ACTIVE block -> Update if growing
                            if len(c2) > len(c1):
                                ev["content"] = c2
                            # If shorter/same, it's a replay prefix -> Ignore
                            self._refresh()
                            return
                        else:
                            # It matches a PAST block -> History replay -> Ignore
                            return

            # No match found -> Append as new thinking block
            self._events.append(
                {
                    "type": "thinking",
                    "content": event.content,
                }
            )
            self._refresh()

        elif isinstance(event, ToolCallEvent):
            if event.tool_name == "write_todos":
                # We handle this via TodoUpdateEvent only
                return

            # Deduplication: Strict check for duplicate tool calls
            # If an identical tool call (same name and args) exists, ignore it.
            # This prevents history replay loops from duplicating tool entries.
            for ev in self._events:
                if ev["type"] == "tool" and ev["name"] == event.tool_name:
                    if ev["args"] == event.arguments:
                        return

            self._events.append(
                {
                    "type": "tool",
                    "name": event.tool_name,
                    "args": event.arguments,
                    "result": None,
                    "done": False,
                    "logs": [],
                }
            )
            self._refresh()
        elif isinstance(event, ToolResultEvent):
            if event.tool_name == "write_todos":
                return
            # Find and update matching tool in events list
            for ev in reversed(self._events):
                if (
                    ev["type"] == "tool"
                    and ev["name"] == event.tool_name
                    and not ev["done"]
                ):
                    ev["result"] = event.result
                    ev["done"] = True
                    break
        elif isinstance(event, TodoUpdateEvent):
            self._todos = event.todos

        elif isinstance(event, StreamingTokenEvent):
            # Handle streaming token
            if event.done:
                # Reset buffer when done
                self._streaming_text = ""
            else:
                self._streaming_text += event.token

        elif isinstance(event, ModelLoadingEvent):
            self._is_loading = event.loading

        self._refresh()

    def add_tool_log(self, tool_name: str, message: str) -> None:
        """Add log message for the currently active tool instance."""
        # Find the most recent active tool with this name
        # We search reversed to find the latest instance
        target_event = None
        for ev in reversed(self._events):
            if ev["type"] == "tool" and ev["name"] == tool_name and not ev["done"]:
                target_event = ev
                break

        if target_event:
            if "logs" not in target_event:
                target_event["logs"] = []
            target_event["logs"].append(message)
        else:
            # Fallback: if no active tool found (or already done),
            # add to other_logs with prefix for visibility
            self._other_logs.append(f"[{tool_name}] {message}")

        self._refresh()

    def add_other_log(self, message: str) -> None:
        """Add log message not belonging to any tool."""
        self._other_logs.append(message)
        self._refresh()

    def _refresh(self) -> None:
        """Refresh the live display."""
        if self._live:
            self._live.update(self._build_display())

    def _build_display(self) -> Group:
        """Build Rich renderable from current state in chronological order."""
        elements = []

        # Events in chronological order
        for event in self._events:
            if event["type"] == "thinking":
                # Thinking block with header
                thinking_header = Text()
                thinking_header.append("● Agent thinking", style="bold magenta")
                elements.append(thinking_header)

                # Render as Markdown (truncate if too long)
                content = event["content"][:800]
                if len(event["content"]) > 800:
                    content += "..."
                elements.append(Markdown(content))
                elements.append(Text(""))  # Spacing

            elif event["type"] == "tool":
                tool_name = event["name"]

                # Build tree for tool call
                if event["done"]:
                    header = f"[bold green]✓[/] [bold cyan]{tool_name}[/]"
                else:
                    header = f"[bold yellow]⟳[/] [bold cyan]{tool_name}[/]"

                tree = Tree(header)

                # Add arguments
                for key, val in event["args"].items():
                    val_str = str(val)[:60]
                    if len(str(val)) > 60:
                        val_str += "..."
                    tree.add(f"[dim]{key}:[/] {val_str}")

                # Add inline logs for this tool instance
                # Read logs directly from the event object
                event_logs = event.get("logs", [])
                if event_logs:
                    logs_branch = tree.add("[dim]📋 Logs:[/]")
                    for log in event_logs[-5:]:
                        logs_branch.add(f"[dim]{log}[/]")
                    if len(event_logs) > 5:
                        logs_branch.add(
                            f"[dim italic]... +{len(event_logs) - 5} more[/]"
                        )

                # Add result preview if done
                if event["done"] and event["result"]:
                    result_preview = event["result"][:150]
                    if len(event["result"]) > 150:
                        result_preview += f"... (+{len(event['result']) - 150} chars)"
                    tree.add(f"[green]Result:[/] {result_preview}")

                elements.append(tree)

        # === Streaming answer (if currently streaming) ===
        if self._streaming_text:
            elements.append(Text(""))  # Separator
            elements.append(Text("═" * 60, style="bold #6DB3B3"))
            elements.append(Text("\n📝 Answer", style="bold #6DB3B3"))
            elements.append(Markdown(self._streaming_text))
            elements.append(Text("═" * 60, style="bold #6DB3B3"))

        # === Other logs ===
        if self._other_logs:
            other_text = Text("\n📋 Other Logs\n", style="bold dim")
            for log in self._other_logs[-3:]:
                other_text.append(f"   {log}\n", style="dim")
            if len(self._other_logs) > 3:
                other_text.append(
                    f"   ... +{len(self._other_logs) - 3} more\n", style="dim italic"
                )
            elements.append(other_text)

        # Spinner while waiting for first event OR when model is loading
        if not elements or self._is_loading:
            if self._is_loading and elements:
                elements.append(Text(""))  # Spacing

            spinner_text = "[bold green]Thinking...[/bold green]"
            elements.append(Spinner("dots", text=spinner_text, style="bold green"))

        # === Todo list at bottom (Footer) ===
        if self._todos:
            # Add separator before todos
            elements.append(Text("\n" + "─" * 40 + "\n", style="dim"))

            todo_text = Text("📋 Todos\n", style="bold")
            for todo in self._todos:
                status = todo.get("status", "pending")
                content = todo.get("content", "")
                if status == "completed":
                    # Dim for completed
                    todo_text.append("   ☒ ", style="green")
                    todo_text.append(content + "\n", style="dim strike")
                elif status == "in_progress":
                    # Lavender/Light Blue-Purple for in-progress
                    todo_text.append("   ☐ ", style="bold #afafff")
                    todo_text.append(content + "\n", style="bold #afafff")
                else:
                    # Normal white for pending (not dim)
                    todo_text.append(f"   ☐ {content}\n", style="")
            elements.append(todo_text)

        return Group(*elements)
