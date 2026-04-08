"""
BrandMind TUI Application.

Full-screen interactive terminal interface using Textual framework.
Features Gemini CLI-inspired design with banner, slash commands,
and collapsible request cards.

Connects to BrandMind API server via HTTP/SSE — no direct agent imports.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import pyperclip
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.widgets import Header, Static

from cli.client import BrandMindClient, ServerNotRunningError
from cli.tui.widgets.banner import BannerWidget
from cli.tui.widgets.input_bar import InputBar
from server.schemas.enums import SessionMode
from server.schemas.events import StreamDoneEvent

if TYPE_CHECKING:
    from cli.tui.tui_renderer import TUIRenderer


# Map slash command mode names to SessionMode enum
_MODE_MAP: dict[str, SessionMode] = {
    "ask": SessionMode.ASK,
    "brand-strategy": SessionMode.BRAND_STRATEGY,
}

# Modes that use stateless search (no session needed)
_SEARCH_MODES = {"search-kg", "search-docs"}

# All valid mode names for /mode command
_VALID_MODES = set(_MODE_MAP.keys()) | _SEARCH_MODES


class BrandMindApp(App[None]):
    """Main BrandMind TUI application.

    Layout:
    - Header (top): App title
    - Banner: Logo display on startup
    - Body (middle): Scrollable request/response cards
    - Input (bottom): Text input with slash command support
    - Footer: Key bindings help

    Connects to BrandMind API server for all agent interactions.
    Sessions are created lazily per mode and reused across queries.
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
        self._last_answer: str = ""

        # HTTP client for server communication
        self._client = BrandMindClient()

        # Session per mode — created lazily on first query
        self._sessions: dict[SessionMode, str] = {}

    def compose(self) -> ComposeResult:
        """Compose app layout."""
        yield Header()
        with ScrollableContainer(id="main-body"):
            if self.show_banner:
                yield BannerWidget(id="banner")
        yield Static("", id="todo-bar", classes="hidden")
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

        main_body = self.query_one("#main-body", ScrollableContainer)
        mode_msg = Static(
            f"[dim]Current mode:[/dim] [bold #6DB3B3]{self._operation_mode}[/bold #6DB3B3] [dim](use /mode to change)[/dim]\n"  # noqa: E501
        )
        main_body.mount(mode_msg)

    async def on_input_bar_command_submitted(
        self, event: InputBar.CommandSubmitted
    ) -> None:
        """Handle command submission from InputBar."""
        await self._handle_command(event.command)

    async def on_input_bar_query_submitted(
        self, event: InputBar.QuerySubmitted
    ) -> None:
        """Handle query submission from InputBar."""
        await self._handle_query(event.query)

    async def _handle_command(self, command: str) -> None:
        """Handle slash commands."""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "/quit":
            self.exit()
        elif cmd == "/clear":
            self.action_clear()
        elif cmd == "/mode" and len(parts) > 1:
            new_mode = parts[1].lower()
            if new_mode not in _VALID_MODES:
                main_body = self.query_one("#main-body", ScrollableContainer)
                valid = ", ".join(sorted(_VALID_MODES))
                msg = Static(f"\n[red]Unknown mode: {new_mode}. Valid: {valid}[/red]\n")
                main_body.mount(msg)
                main_body.scroll_end(animate=False)
                return

            self._operation_mode = new_mode
            self.sub_title = f"Mode: {self._operation_mode}"
            try:
                status_bar = self.query_one("#status-bar", Static)
                status_bar.update(
                    f"[dim]Mode:[/dim] [bold #6DB3B3]{new_mode}[/bold #6DB3B3]  [dim]│  ESC to cancel[/dim]"  # noqa: E501
                )
            except Exception:
                pass
            main_body = self.query_one("#main-body", ScrollableContainer)
            mode_msg = Static(
                f"\n[dim]>[/dim] [bold]/mode {new_mode}[/bold]\n[#6DB3B3]✓ Switched to mode:[/#6DB3B3] [bold]{new_mode}[/bold]\n"  # noqa: E501
            )
            main_body.mount(mode_msg)
            main_body.scroll_end(animate=False)
        elif cmd == "/help":
            await self._show_help()

    async def _show_help(self) -> None:
        """Show help message in main body as part of conversation history."""
        from textual.widgets import Static

        main_body = self.query_one("#main-body", ScrollableContainer)

        command_widget = Static(
            "[dim]>[/dim] [bold]/help[/bold]", classes="command-echo"
        )
        main_body.mount(command_widget)

        help_text = """[bold #6DB3B3]Available Commands:[/]

[bold]/mode[/] <ask|brand-strategy|search-kg|search-docs>  Change operation mode
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
        help_widget = Static(help_text, classes="help-message")
        main_body.mount(help_widget)
        main_body.scroll_end(animate=False)

    async def _handle_query(self, query: str) -> None:
        """Execute query in current mode via server HTTP/SSE.

        Args:
            query: User query string
        """
        from cli.tui.tui_renderer import TUIRenderer

        self._cancel_requested = False

        main_body = self.query_one("#main-body", ScrollableContainer)

        try:
            todo_bar = self.query_one("#todo-bar", Static)
            todo_bar.update("")
            todo_bar.add_class("hidden")
        except Exception:
            pass

        renderer = TUIRenderer(main_body, is_expanded=self._is_expanded)
        self._current_renderer = renderer
        self._all_renderers.append(renderer)

        renderer.show_query(query)
        renderer.show_spinner()

        # Run as async Textual worker — no separate event loop needed
        # since we now use httpx (async-native) instead of direct agent calls
        self.run_worker(
            self._execute_query_async(query, renderer),
            name="agent_worker",
            exclusive=True,
        )

    async def _ensure_session(self) -> str:
        """Get or create session for current mode.

        Returns:
            session_id for the current mode's session.

        Raises:
            ServerNotRunningError: If server is not reachable.
        """
        mode_enum = _MODE_MAP.get(self._operation_mode)
        if mode_enum is None:
            raise ValueError(f"Mode {self._operation_mode} does not use sessions")

        if mode_enum not in self._sessions:
            info = await self._client.create_session(mode_enum)
            self._sessions[mode_enum] = info.session_id

        return self._sessions[mode_enum]

    async def _execute_query_async(self, query: str, renderer: "TUIRenderer") -> None:
        """Execute query based on current mode via server.

        Agent-based modes (ask, brand-strategy) use SSE streaming.
        Search modes use stateless HTTP endpoints.

        Args:
            query: User query string
            renderer: TUIRenderer for streaming output
        """
        try:
            mode = self._operation_mode

            if self._cancel_requested:
                return

            if mode in _MODE_MAP:
                # Agent mode — stream via SSE
                session_id = await self._ensure_session()

                if self._cancel_requested:
                    return

                renderer.reset_streaming_state()

                accumulated_answer = ""

                async for event in self._client.stream_message(session_id, query):
                    if self._cancel_requested:
                        break

                    if isinstance(event, StreamDoneEvent):
                        break

                    renderer.handle_event(event)

                    # Track accumulated answer for copy
                    from shared.agent_middlewares.callback_types import (
                        StreamingTokenEvent,
                    )

                    if isinstance(event, StreamingTokenEvent):
                        if event.token and not event.done:
                            accumulated_answer += event.token

                if not self._cancel_requested:
                    self._last_answer = (
                        accumulated_answer
                        if accumulated_answer
                        else "No response generated"
                    )

            elif mode == "search-kg":
                if self._cancel_requested:
                    return

                renderer.hide_spinner()
                result = await self._client.search_kg(query=query, max_results=10)

                if not self._cancel_requested:
                    self._last_answer = result
                    renderer.set_answer(result)

            elif mode == "search-docs":
                if self._cancel_requested:
                    return

                renderer.hide_spinner()
                result = await self._client.search_docs(query=query, top_k=10)

                if not self._cancel_requested:
                    self._last_answer = result
                    renderer.set_answer(result)

            else:
                renderer.hide_spinner()
                renderer.set_answer(f"[red]Unknown mode: {mode}[/red]")

        except ServerNotRunningError:
            renderer.hide_spinner()
            self._show_error(
                "[bold red]BrandMind server not running.[/bold red]\n"
                "[dim]Start with:[/dim] [bold]brandmind serve[/bold]"
            )
        except Exception as e:
            renderer.hide_spinner()
            self._show_error(f"[bold red]Error:[/bold red] {e}")

    def _show_error(self, message: str) -> None:
        """Show error message using Rich markup (not Markdown)."""
        main_body = self.query_one("#main-body", ScrollableContainer)
        main_body.mount(Static(f"\n{message}\n"))
        main_body.scroll_end(animate=False)

    def action_toggle_expand(self) -> None:
        """Toggle expand/collapse on logs (Ctrl+O)."""
        self._is_expanded = not self._is_expanded
        for renderer in self._all_renderers:
            renderer.set_expanded(self._is_expanded)

    def action_copy_answer(self) -> None:
        """Copy the last answer to clipboard (Ctrl+Y)."""
        if not self._last_answer:
            self.notify("No answer to copy", severity="warning")
            return

        try:
            plain_text = re.sub(r"\[.*?\]", "", self._last_answer)
            pyperclip.copy(plain_text)
            self.notify("Answer copied to clipboard!", severity="information")
        except Exception as e:
            self.notify(f"Failed to copy: {e}", severity="error")

    def action_clear(self) -> None:
        """Clear conversation history.

        Resets current mode's session so next query starts fresh.
        """
        main_body = self.query_one("#main-body", ScrollableContainer)
        for child in list(main_body.children):
            if not isinstance(child, BannerWidget):
                child.remove()

        try:
            todo_bar = self.query_one("#todo-bar", Static)
            todo_bar.update("")
            todo_bar.add_class("hidden")
        except Exception:
            pass

        try:
            banner = self.query_one("#banner", BannerWidget)
            banner.display = True
            self.show_banner = True
        except Exception:
            pass

        # Reset current mode's session so next query creates a fresh one
        mode_enum = _MODE_MAP.get(self._operation_mode)
        if mode_enum and mode_enum in self._sessions:
            del self._sessions[mode_enum]

        self._current_card = None

    def action_cancel_query(self) -> None:
        """Cancel currently running query (ESC key)."""
        self._cancel_requested = True
        self.workers.cancel_all()

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
