"""CLI for Brand Strategy interactive sessions.

Provides the interactive brand strategy mode where users work through
the 6-phase brand building process with the AI Brand Mentor.

Connects to BrandMind API server — requires `brandmind serve` running.
"""

from __future__ import annotations

from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from cli.client import BrandMindClient, ServerNotRunningError
from server.schemas.enums import SessionMode
from server.schemas.events import StreamDoneEvent
from server.schemas.session import BrandStrategyMetadata
from shared.agent_middlewares.callback_types import (
    ModelLoadingEvent,
    StreamingTokenEvent,
    ToolCallEvent,
    ToolResultEvent,
)

console = Console()

# Slash commands with descriptions
_COMMANDS: dict[str, str] = {
    "/status": "Show current phase & session info",
    "/sessions": "List all saved sessions",
    "/clear": "Reset session (start fresh)",
    "/exit": "Save and exit session",
    "/quit": "Save and exit session",
    "/help": "Show available commands",
}

_command_completer = WordCompleter(
    list(_COMMANDS.keys()),
    sentence=True,
)


async def run_brand_strategy_session(
    initial_message: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """Run interactive brand strategy session via server.

    Args:
        initial_message: Optional first message to send.
        session_id: Optional session ID to resume.
    """
    console.print(
        Panel(
            "[bold cyan]BrandMind — Brand Strategy Mode[/bold cyan]\n"
            "AI Brand Strategist & Mentor for F&B\n\n"
            "Commands: type [bold]/[/bold] to see suggestions\n"
            "  [bold]/status[/bold]    — Show current phase & session info\n"
            "  [bold]/sessions[/bold]  — List all saved sessions\n"
            "  [bold]/clear[/bold]     — Reset session (start fresh)\n"
            "  [bold]/help[/bold]      — Show available commands\n"
            "  [bold]/exit[/bold]      — Save and exit session",
            title="BrandMind",
        )
    )

    client = BrandMindClient()

    # Check server health
    try:
        await client.health()
    except ServerNotRunningError:
        console.print(
            "[bold red]BrandMind server not running.[/bold red]\n"
            "Start with: [bold]brandmind serve[/bold]"
        )
        return

    # Load or create session
    if session_id:
        try:
            info = await client.get_session(session_id)
            console.print(f"[green]Resumed session: {session_id}[/green]")
            phase = "?"
            if isinstance(info.metadata, BrandStrategyMetadata):
                phase = info.metadata.current_phase
            console.print(f"[dim]Current phase: {phase}[/dim]")
        except Exception:
            console.print(
                f"[yellow]Session {session_id} not found. Starting new.[/yellow]"
            )
            info = await client.create_session(SessionMode.BRAND_STRATEGY)
    else:
        info = await client.create_session(SessionMode.BRAND_STRATEGY)

    current_session_id = info.session_id
    console.print(f"[dim]Session ID: {current_session_id}[/dim]")
    console.print()

    # Handle initial message
    if initial_message:
        await _send_and_display(client, current_session_id, initial_message)

    # prompt_toolkit session for autocomplete
    prompt_session: PromptSession[str] = PromptSession(
        completer=_command_completer,
    )

    # Main conversation loop
    while True:
        try:
            user_input = await prompt_session.prompt_async(
                HTML("\n<ansigreen><b>You:</b></ansigreen> "),
            )
        except (KeyboardInterrupt, EOFError):
            break

        stripped = user_input.strip()
        if not stripped:
            continue

        cmd = stripped.lower()

        # Slash commands
        if cmd in ("/exit", "/quit"):
            console.print(
                f"\n[dim]Session saved ({current_session_id}). "
                f"Resume with:[/dim]\n"
                f"  [bold]brandmind brand-strategy "
                f"--session {current_session_id}[/bold]"
            )
            break

        if cmd == "/status":
            await _show_status(client, current_session_id)
            continue

        if cmd == "/sessions":
            await _show_sessions(client)
            continue

        if cmd == "/clear":
            # Delete ALL sessions to free server memory
            all_sessions = await client.list_sessions()
            for s in all_sessions:
                await client.delete_session(s.session_id)
            info = await client.create_session(SessionMode.BRAND_STRATEGY)
            current_session_id = info.session_id
            console.print(
                f"\n[green]Cleared {len(all_sessions)} session(s).[/green] "
                f"[dim]New ID: {current_session_id}[/dim]"
            )
            continue

        if cmd == "/help":
            _show_help()
            continue

        # Regular message — send to agent
        await _send_and_display(client, current_session_id, stripped)


async def _show_status(client: BrandMindClient, session_id: str) -> None:
    """Display current session status."""
    try:
        session_info = await client.get_session(session_id)
        meta = session_info.metadata
        phase = "?"
        scope = "Not yet classified"
        brand = "Not yet named"
        if isinstance(meta, BrandStrategyMetadata):
            phase = meta.current_phase
            scope = meta.scope or scope
            brand = meta.brand_name or brand
        console.print(
            Panel(
                f"Session: {session_id}\n"
                f"Phase: {phase}\n"
                f"Scope: {scope}\n"
                f"Brand: {brand}",
                title="Status",
            )
        )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def _show_sessions(client: BrandMindClient) -> None:
    """List all active sessions."""
    try:
        sessions = await client.list_sessions()
        if not sessions:
            console.print("[dim]No active sessions.[/dim]")
        else:
            for s in sessions:
                label = "Unnamed"
                if isinstance(s.metadata, BrandStrategyMetadata):
                    label = s.metadata.brand_name or label
                console.print(
                    f"  [bold]{s.session_id}[/bold] — {label} ({s.mode.value})"
                )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def _show_help() -> None:
    """Display available slash commands."""
    lines = [f"  [bold]{cmd}[/bold]  — {desc}" for cmd, desc in _COMMANDS.items()]
    console.print(Panel("\n".join(lines), title="Commands"))


async def _send_and_display(
    client: BrandMindClient,
    session_id: str,
    message: str,
) -> None:
    """Send message via SSE streaming with progress spinner.

    Shows a dynamic spinner while the agent works (thinking, tool calls),
    then displays the complete response in a Rich panel.

    Args:
        client: BrandMind API client.
        session_id: Target session ID.
        message: User message text.
    """
    try:
        response_tokens: list[str] = []
        console.print()

        with console.status("[cyan]Thinking...", spinner="dots") as status:
            async for event in client.stream_message(session_id, message):
                if isinstance(event, StreamDoneEvent):
                    break

                if isinstance(event, ModelLoadingEvent):
                    if event.loading:
                        status.update("[cyan]Thinking...")

                elif isinstance(event, ToolCallEvent):
                    status.update(f"[cyan]Using {event.tool_name}...")

                elif isinstance(event, ToolResultEvent):
                    status.update("[cyan]Processing results...")

                elif isinstance(event, StreamingTokenEvent):
                    if event.token and not event.done:
                        response_tokens.append(event.token)
                        status.update("[cyan]Generating response...")

        text = "".join(response_tokens)
        if text:
            console.print()
            console.print(
                Panel(
                    Markdown(text),
                    title="BrandMind",
                    border_style="cyan",
                )
            )

    except ServerNotRunningError:
        console.print(
            "[bold red]Lost connection to server.[/bold red]\n"
            "Restart with: [bold]brandmind serve[/bold]"
        )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
