"""
BrandMind TUI Application.

Full-screen interactive terminal interface using Textual framework.
Features Gemini CLI-inspired design with banner, slash commands,
and collapsible request cards.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import pyperclip
from langchain_core.messages import AIMessageChunk
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.widgets import Header, Static

from cli.tui.widgets.banner import BannerWidget
from cli.tui.widgets.input_bar import InputBar
from shared.agent_middlewares.callback_types import (
    StreamingThinkingEvent,
    StreamingTokenEvent,
)

if TYPE_CHECKING:
    from cli.tui.tui_renderer import TUIRenderer


class BrandMindApp(App[None]):
    """Main BrandMind TUI application.

    Layout:
    - Header (top): App title
    - Banner: Logo display on startup
    - Body (middle): Scrollable request/response cards
    - Input (bottom): Text input with slash command support
    - Footer: Key bindings help

    Attributes:
        current_mode: Current operation mode (ask, search-kg, search-docs)
        show_banner: Whether to show banner on startup
    """

    CSS_PATH: ClassVar[str | Path] = Path(__file__).parent / "styles.tcss"

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+o", "toggle_expand", "Expand/Collapse", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear", "Clear", show=True),
        Binding("ctrl+y", "copy_answer", "Copy Answer", show=True),
        Binding("escape", "cancel_query", "Cancel", show=False, priority=True),
    ]

    TITLE = "BrandMind AI"
    SUB_TITLE = "Marketing Knowledge Assistant"

    def __init__(self) -> None:
        """Initialize BrandMind TUI app."""
        super().__init__()
        self._operation_mode: str = "ask"
        self.show_banner: bool = True
        self._is_expanded: bool = False
        self._current_renderer: "TUIRenderer | None" = None
        self._all_renderers: list["TUIRenderer"] = []
        self._cancel_requested: bool = False
        self._current_future = None
        self._last_answer: str = ""

    def compose(self) -> ComposeResult:
        """Compose app layout."""
        yield Header()
        with ScrollableContainer(id="main-body"):
            if self.show_banner:
                yield BannerWidget(id="banner")
        # Todo bar - always at bottom above input, initially hidden
        yield Static("", id="todo-bar", classes="hidden")
        # Status bar above input showing current mode
        yield Static(
            f"[dim]Mode:[/dim] [bold #6DB3B3]{self._operation_mode}[/bold #6DB3B3]  [dim]│  ESC to cancel[/dim]",  # noqa: E501
            id="status-bar",
        )
        yield InputBar(
            placeholder="> Type message or / for commands",
            id="input-bar",
        )

    def on_mount(self) -> None:
        """Focus input bar on mount and show current mode."""
        self.query_one("#input-bar", InputBar).focus()

        # Show startup mode notification
        main_body = self.query_one("#main-body", ScrollableContainer)
        mode_msg = Static(
            f"[dim]Current mode:[/dim] [bold #6DB3B3]{self._operation_mode}[/bold #6DB3B3] [dim](use /mode to change)[/dim]\n"  # noqa: E501
        )
        main_body.mount(mode_msg)

    async def on_input_bar_command_submitted(
        self, event: InputBar.CommandSubmitted
    ) -> None:
        """Handle command submission from InputBar.

        Args:
            event: Command submitted event
        """
        await self._handle_command(event.command)

    async def on_input_bar_query_submitted(
        self, event: InputBar.QuerySubmitted
    ) -> None:
        """Handle query submission from InputBar.

        Args:
            event: Query submitted event
        """
        await self._handle_query(event.query)

    async def _handle_command(self, command: str) -> None:
        """Handle slash commands.

        Args:
            command: Full command string starting with /
        """
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "/quit":
            self.exit()
        elif cmd == "/clear":
            self.action_clear()
        elif cmd == "/mode" and len(parts) > 1:
            self._operation_mode = parts[1]
            self.sub_title = f"Mode: {self._operation_mode}"
            # Update status bar
            try:
                status_bar = self.query_one("#status-bar", Static)
                status_bar.update(
                    f"[dim]Mode:[/dim] [bold #6DB3B3]{parts[1]}[/bold #6DB3B3]  [dim]│  ESC to cancel[/dim]"  # noqa: E501
                )
            except Exception:
                pass
            # Show mode change notification
            main_body = self.query_one("#main-body", ScrollableContainer)
            mode_msg = Static(
                f"\n[dim]>[/dim] [bold]/mode {parts[1]}[/bold]\n[#6DB3B3]✓ Switched to mode:[/#6DB3B3] [bold]{parts[1]}[/bold]\n"  # noqa: E501
            )
            main_body.mount(mode_msg)
            main_body.scroll_end(animate=False)
        elif cmd == "/help":
            await self._show_help()

    async def _show_help(self) -> None:
        """Show help message in main body as part of conversation history."""
        from textual.widgets import Static

        main_body = self.query_one("#main-body", ScrollableContainer)

        # Show the command that was typed (like Gemini CLI)
        command_widget = Static(
            "[dim]>[/dim] [bold]/help[/bold]", classes="command-echo"
        )
        main_body.mount(command_widget)

        help_text = """[bold #6DB3B3]Available Commands:[/]

[bold]/mode[/] <ask|search-kg|search-docs>  Change operation mode
[bold]/clear[/]                             Clear conversation history
[bold]/help[/]                              Show this help message
[bold]/quit[/]                              Exit the application

[bold #6DB3B3]Keyboard Shortcuts:[/]

[dim]Ctrl+O[/]   Expand/collapse logs
[dim]Ctrl+L[/]   Clear screen
[dim]Ctrl+Y[/]   Copy last answer to clipboard
[dim]Ctrl+Q[/]   Quit
[dim]↑↓[/]       Navigate suggestions / history
[dim]Tab[/]      Complete suggestion (add to input)
[dim]Enter[/]    Submit complete command or show subcommands

[bold #6DB3B3]Input Editing:[/]

[dim]Ctrl+U[/]   Delete to start of line
[dim]Ctrl+W[/]   Delete word left
"""
        # No ID - allow multiple help messages in history
        help_widget = Static(help_text, classes="help-message")
        main_body.mount(help_widget)
        # Scroll to bottom to show new help
        main_body.scroll_end(animate=False)

    async def _handle_query(self, query: str) -> None:
        """Execute query in current mode.

        Uses TUIRenderer for streaming output like Claude Code / Gemini CLI.

        Args:
            query: User query string
        """
        from cli.tui.tui_renderer import TUIRenderer

        # Reset cancel flag for new query
        self._cancel_requested = False

        # Get main body for streaming output
        main_body = self.query_one("#main-body", ScrollableContainer)

        # Hide todo-bar from previous query
        try:
            todo_bar = self.query_one("#todo-bar", Static)
            todo_bar.update("")
            todo_bar.add_class("hidden")
        except Exception:
            pass

        # Create renderer for streaming output
        renderer = TUIRenderer(main_body, is_expanded=self._is_expanded)
        self._current_renderer = renderer
        self._all_renderers.append(renderer)  # Track for Ctrl+O

        # Show query echo immediately
        renderer.show_query(query)
        renderer.show_spinner()

        # Execute in background thread for parallelism
        self.run_worker(
            lambda: self._run_agent_sync(query, renderer),
            thread=True,
            name="agent_worker",
            exclusive=True,
        )

    def _run_agent_sync(self, query: str, renderer: "TUIRenderer") -> None:
        """Sync wrapper for agent execution.

        Runs in a separate thread with a dedicated persistent event loop
        for Milvus compatibility. Tasks are submitted as Futures for
        proper cancellation support.
        """
        import asyncio
        import threading

        # Ensure we have a persistent loop running in background
        if (
            not hasattr(BrandMindApp, "_bg_loop")
            or BrandMindApp._bg_loop is None
            or BrandMindApp._bg_loop.is_closed()
        ):
            BrandMindApp._bg_loop = asyncio.new_event_loop()

            def run_loop(loop):
                asyncio.set_event_loop(loop)
                loop.run_forever()

            BrandMindApp._bg_thread = threading.Thread(
                target=run_loop, args=(BrandMindApp._bg_loop,), daemon=True
            )
            BrandMindApp._bg_thread.start()

        loop = BrandMindApp._bg_loop

        # Submit task to the background loop and get a Future
        future = asyncio.run_coroutine_threadsafe(
            self._execute_query_async(query, renderer), loop
        )

        # Store the future for cancellation
        self._current_future = future

        try:
            # Wait for completion (this blocks until done or cancelled)
            future.result()
        except asyncio.CancelledError:
            # Task was cancelled - this is expected
            pass
        except Exception:
            # Other errors handled in _execute_query_async
            pass

    async def _execute_query_async(self, query: str, renderer: "TUIRenderer") -> None:
        """Execute query based on current mode.

        Runs in a worker thread with its own event loop.
        Supports modes: ask, search-kg, search-docs.

        Args:
            query: User query string
            renderer: TUIRenderer for streaming output
        """

        try:
            mode = self._operation_mode

            # Check for cancellation before starting
            if self._cancel_requested:
                return

            if mode == "ask":
                from cli.inference import create_qa_agent
                from cli.log_capture import SmartLogCapture
                from cli.tool_context import reset_current_tool, set_current_tool

                # Create log capture that routes to renderer
                log_capture = SmartLogCapture(
                    on_tool_log=renderer.add_tool_log,
                    on_other_log=lambda msg: None,  # Ignore non-tool logs
                )

                with log_capture:
                    # Check cancellation again
                    if self._cancel_requested:
                        return

                    # Create agent with event callback and tool context hooks
                    agent = create_qa_agent(
                        callback=renderer.handle_event,
                        on_tool_start=set_current_tool,
                        on_tool_end=reset_current_tool,
                    )

                    if self._cancel_requested:
                        return

                    # Reset streaming state for new query
                    renderer.reset_streaming_state()

                    # Stream agent response token-by-token
                    accumulated_answer = ""
                    thinking_done = False  # Track if thinking phase has completed

                    async for message_chunk, metadata in agent.astream(
                        {"messages": [{"role": "user", "content": query}]},
                        {"recursion_limit": 100},
                        stream_mode="messages",
                    ):
                        # Check cancellation during streaming
                        if self._cancel_requested:
                            break

                        # Only process AI message chunks (not tool messages)
                        if isinstance(message_chunk, AIMessageChunk):
                            # Extract both thinking and text tokens from message chunk
                            # Models with thinking capability emit content as list with
                            # multiple parts: thinking blocks first, then text blocks
                            if isinstance(message_chunk.content, list):
                                # Complex content - may contain thinking + text
                                for part in message_chunk.content:
                                    if isinstance(part, dict):
                                        # Extract thinking tokens
                                        if part.get("type") == "thinking":
                                            # New thinking block
                                            if thinking_done:
                                                thinking_done = False

                                            thinking_text = part.get("thinking", "")
                                            if thinking_text:
                                                renderer.handle_event(
                                                    StreamingThinkingEvent(
                                                        token=thinking_text
                                                    )
                                                )

                                        # Extract text tokens
                                        elif part.get("type") == "text":
                                            token_text = part.get("text", "")
                                            if token_text:
                                                # Finalize thinking
                                                if not thinking_done:
                                                    renderer.handle_event(
                                                        StreamingThinkingEvent(
                                                            token="", done=True
                                                        )
                                                    )
                                                    thinking_done = True
                                                accumulated_answer += token_text
                                                renderer.handle_event(
                                                    StreamingTokenEvent(
                                                        token=token_text
                                                    )
                                                )

                            elif isinstance(message_chunk.content, str):
                                # Simple string content - just text
                                token_text = message_chunk.content
                                if token_text:
                                    # Finalize thinking if we haven't yet
                                    if not thinking_done:
                                        renderer.handle_event(
                                            StreamingThinkingEvent(token="", done=True)
                                        )
                                        thinking_done = True
                                    accumulated_answer += token_text
                                    renderer.handle_event(
                                        StreamingTokenEvent(token=token_text)
                                    )

                            # Handle messages with tool calls - they are intermediate
                            # responses, not the final answer.
                            # Important: If we encounter tool calls, thinking is done.
                            if message_chunk.tool_calls:
                                if not thinking_done:
                                    renderer.handle_event(
                                        StreamingThinkingEvent(token="", done=True)
                                    )
                                    thinking_done = True
                                continue

                    # Ensure thinking is finalized if stream ends without text/tools
                    if not thinking_done:
                        renderer.handle_event(
                            StreamingThinkingEvent(token="", done=True)
                        )
                        thinking_done = True

                    # Send done signal to finalize streaming (only if not cancelled)
                    if not self._cancel_requested:
                        renderer.handle_event(StreamingTokenEvent(token="", done=True))

                    # Check cancellation after execution
                    if self._cancel_requested:
                        return

                    # Set final answer
                    answer = accumulated_answer

                # Store final answer for history (only if not cancelled)
                if not self._cancel_requested:
                    final_answer = answer if answer else "No response generated"
                    self._last_answer = final_answer

            elif mode == "search-kg":
                # Direct KG search without agent
                from shared.agent_tools.retrieval import search_knowledge_graph

                if self._cancel_requested:
                    return

                renderer.hide_spinner()
                result = await search_knowledge_graph(query=query, max_results=10)

                if not self._cancel_requested:
                    self._last_answer = result
                    renderer.set_answer(result)

            elif mode == "search-docs":
                # Direct document search without agent
                from shared.agent_tools.retrieval import search_document_library

                if self._cancel_requested:
                    return

                renderer.hide_spinner()
                result = await search_document_library(query=query, top_k=10)

                if not self._cancel_requested:
                    self._last_answer = result
                    renderer.set_answer(result)

            else:
                # Unknown mode - fallback to ask
                renderer.hide_spinner()
                renderer.set_answer(f"[red]Unknown mode: {mode}[/red]")

        except Exception as e:
            import traceback

            renderer.hide_spinner()
            renderer.set_answer(f"[red]Error: {e}[/red]\n\n{traceback.format_exc()}")

    def _extract_answer(self, result: dict) -> str:
        """Extract answer text from agent result.

        Args:
            result: Agent result dict

        Returns:
            Answer text string
        """
        if not result or "messages" not in result:
            return ""

        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content:
                content = msg.content
                if isinstance(content, list):
                    # Extract all text parts
                    text_parts = []
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                        elif isinstance(part, str):
                            text_parts.append(part)
                    if text_parts:
                        return "\n".join(text_parts)
                elif isinstance(content, str):
                    return content
        return ""

    def action_toggle_expand(self) -> None:
        """Toggle expand/collapse on logs (Ctrl+O).

        Toggles the expand state for ALL renderers' logs.
        """
        self._is_expanded = not self._is_expanded

        # Update ALL renderers so Ctrl+O expands everything
        for renderer in self._all_renderers:
            renderer.set_expanded(self._is_expanded)

    def action_copy_answer(self) -> None:
        """Copy the last answer to clipboard (Ctrl+Y)."""
        if not self._last_answer:
            self.notify("No answer to copy", severity="warning")
            return

        try:
            # Strip Rich markup for plain text
            plain_text = re.sub(r"\[.*?\]", "", self._last_answer)
            pyperclip.copy(plain_text)
            self.notify("Answer copied to clipboard!", severity="information")
        except Exception as e:
            self.notify(f"Failed to copy: {e}", severity="error")

    def action_clear(self) -> None:
        """Clear conversation history."""
        main_body = self.query_one("#main-body", ScrollableContainer)
        # Remove all children except banner
        for child in list(main_body.children):
            if not isinstance(child, BannerWidget):
                child.remove()

        # Hide todo-bar
        try:
            todo_bar = self.query_one("#todo-bar", Static)
            todo_bar.update("")
            todo_bar.add_class("hidden")
        except Exception:
            pass

        # Show banner again
        try:
            banner = self.query_one("#banner", BannerWidget)
            banner.display = True
            self.show_banner = True
        except Exception:
            pass

        self._current_card = None

    def action_cancel_query(self) -> None:
        """Cancel currently running query (ESC key)."""
        # Set cancel flag
        self._cancel_requested = True

        # Cancel the Future (this will interrupt the async task)
        if self._current_future and not self._current_future.done():
            self._current_future.cancel()
            self._current_future = None

        # Cancel all workers
        self.workers.cancel_all()

        # Cancel current renderer (stops processing events and hides spinner)
        if self._current_renderer:
            self._current_renderer.cancel()
            try:
                main_body = self.query_one("#main-body", ScrollableContainer)
                cancel_msg = Static("\n[yellow]ⓘ Request cancelled.[/yellow]\n")
                main_body.mount(cancel_msg)
                main_body.scroll_end(animate=False)
            except Exception:
                pass
            self._current_renderer = None


def run_tui() -> None:
    """Run the BrandMind TUI application."""
    app = BrandMindApp()
    app.run()


if __name__ == "__main__":
    run_tui()
