"""CLI for Brand Strategy interactive sessions.

Provides the interactive brand strategy mode where users work through
the 6-phase brand building process with the AI Brand Mentor.
"""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.messages import HumanMessage
from loguru import logger
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from core.brand_strategy.agent_config import (
    create_brand_strategy_agent,
)
from core.brand_strategy.session import (
    BrandStrategySession,
    list_sessions,
    load_session,
    save_session,
    set_active_session,
)

console = Console()


async def run_brand_strategy_session(
    initial_message: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """Run interactive brand strategy session."""
    console.print(
        Panel(
            "[bold cyan]BrandMind — Brand Strategy Mode[/bold cyan]\n"
            "AI Brand Strategist & Mentor for F&B\n\n"
            "Commands:\n"
            "  [bold]status[/bold]    — Show current phase & session info\n"
            "  [bold]sessions[/bold]  — List all saved sessions\n"
            "  [bold]exit/quit[/bold] — Save and exit",
            title="BrandMind",
        )
    )

    # Load or create session
    if session_id:
        session = load_session(session_id)
        if session:
            console.print(f"[green]Resumed session: {session_id}[/green]")
            console.print(f"[dim]Current phase: {session.current_phase}[/dim]")
        else:
            console.print(
                f"[yellow]Session {session_id} not found. Starting new.[/yellow]"
            )
            session = BrandStrategySession()
    else:
        session = BrandStrategySession()

    console.print(f"[dim]Session ID: {session.session_id}[/dim]")

    # Wire session to agent's report_progress tool
    set_active_session(session)

    # Create agent
    agent = create_brand_strategy_agent()

    # Conversation state
    messages: list[Any] = session.messages.copy() if session.messages else []

    if initial_message:
        messages.append(HumanMessage(content=initial_message))

    # Main conversation loop
    while True:
        if not initial_message or len(messages) > 1:
            try:
                user_input = console.input("[bold green]You:[/bold green] ")
            except (KeyboardInterrupt, EOFError):
                break

            cmd = user_input.strip().lower()
            if cmd in ("exit", "quit"):
                save_session(session)
                console.print(
                    f"[dim]Session saved ({session.session_id}). "
                    f"Resume with:[/dim]\n"
                    f"  [bold]brandmind brand-strategy "
                    f"--session {session.session_id}[/bold]"
                )
                break

            if cmd == "status":
                console.print(
                    Panel(
                        f"Session: {session.session_id}\n"
                        f"Phase: {session.current_phase}\n"
                        f"Scope: {session.scope or 'Not yet classified'}\n"
                        f"Brand: {session.brand_name or 'Not yet named'}",
                        title="Status",
                    )
                )
                continue

            if cmd == "sessions":
                saved = list_sessions()
                if not saved:
                    console.print("[dim]No saved sessions.[/dim]")
                else:
                    for s in saved:
                        label = s.get("brand_name") or "Unnamed"
                        sid = s["session_id"]
                        phase = s.get("phase", "?")
                        console.print(
                            f"  [bold]{sid}[/bold] — {label} (phase: {phase})"
                        )
                continue

            messages.append(HumanMessage(content=user_input))

        initial_message = None

        try:
            result = await agent.ainvoke(
                {"messages": messages},
                {"recursion_limit": 200},
            )

            if "messages" in result and result["messages"]:
                for msg in reversed(result["messages"]):
                    if hasattr(msg, "content") and msg.content:
                        response_text = _extract_text(msg.content)
                        if response_text:
                            console.print()
                            console.print(
                                Panel(
                                    Markdown(response_text),
                                    title="BrandMind",
                                    border_style="cyan",
                                )
                            )
                            break

            messages = result.get("messages", messages)
            session.messages = messages

        except Exception as e:
            logger.error(f"Agent error: {e}")
            console.print(f"[red]Error: {e}[/red]")
            continue


def _extract_text(content: Any) -> str:
    """Extract text from agent message content."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
            elif isinstance(part, str):
                parts.append(part)
        return "\n".join(parts)
    return str(content)
