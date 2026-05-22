"""
CLI for running inference on the Marketing Knowledge Base.

This CLI provides interactive and non-interactive modes for querying BrandMind AI:

Default (no args): Launch interactive TUI with rich UI
Subcommands:
- ask: Q&A using agentic reasoning with Knowledge Graph and Document Library
- search-kg: Direct Knowledge Graph search for concepts and relationships
- search-docs: Direct Document Library search with filtering options

Examples:
    brandmind     # Launch interactive TUI
    brandmind ask -q "What is Marketing Myopia?"
    brandmind search-kg -q "customer value" -n 5
    brandmind search-docs -q "pricing" --chapter "Chapter 10"
"""

import argparse
import asyncio
from pathlib import Path
from typing import Callable, Optional, Sequence
from urllib.error import URLError
from urllib.request import urlopen

from loguru import logger
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

_SERVE_PID_FILE = "brandmind-serve.pid"
_SERVE_LOG_FILE = "brandmind-serve.log"
_SERVE_HEALTH_TIMEOUT_SECONDS = 1.0
_SERVE_STARTUP_WAIT_SECONDS = 15.0
_SERVE_STOP_WAIT_SECONDS = 10.0
_SERVE_LOG_FOLLOW_INTERVAL_SECONDS = 0.5
_SERVE_DEFAULT_LOG_TAIL_LINES = 100


def create_qa_agent(
    callback: Optional[Callable] = None,
    on_tool_start: Optional[Callable[[str], object]] = None,
    on_tool_end: Optional[Callable[[object], None]] = None,
):
    """
    Create Q&A Agent with langchain agent for autonomous tool use.

    The agent uses Knowledge Graph and Document Library tools with research-first
    philosophy for evidence-based marketing knowledge retrieval.

    Args:
        callback: Optional callback for agent events (thinking, tool_call, tool_result)
        on_tool_start: Optional hook called when tool starts (returns token)
        on_tool_end: Optional hook called when tool ends (takes token)

    Returns:
        Configured langchain agent with middlewares and tools
    """
    from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
    from langchain.agents import create_agent
    from langchain.agents.middleware import (
        ClearToolUsesEdit,
        ContextEditingMiddleware,
        SummarizationMiddleware,
        ToolRetryMiddleware,
    )

    from config.system_config import SETTINGS
    from prompts.inference import QA_AGENT_SYSTEM_PROMPT
    from shared.agent_middlewares import (
        EnsureTasksFinishedMiddleware,
        LogModelMessageMiddleware,
    )
    from shared.agent_models.retry_gemini import RetryChatGoogleGenerativeAI
    from shared.agent_tools import TodoWriteMiddleware
    from shared.agent_tools.retrieval import (
        search_document_library,
        search_knowledge_graph,
    )

    # Initialize Gemini model with built-in retry for 503/429 errors
    model = RetryChatGoogleGenerativeAI(
        google_api_key=SETTINGS.GEMINI_API_KEY,
        model="gemini-3-flash-preview",
        temperature=1.0,
        thinking_level="medium",
        max_output_tokens=5000,
        include_thoughts=True,
    )
    model_context_window = 1048576  # 1M tokens

    # Setup middlewares
    todo_middleware = TodoWriteMiddleware()
    patch_middleware = PatchToolCallsMiddleware()
    retry_middleware = ToolRetryMiddleware()
    stop_check_middleware = EnsureTasksFinishedMiddleware()
    log_message_middleware = LogModelMessageMiddleware(
        callback=callback,  # Inject callback for event streaming
        on_tool_start=on_tool_start,  # Inject hook for context tracking
        on_tool_end=on_tool_end,  # Inject hook for context cleanup
        log_thinking=(
            True if not callback else False
        ),  # Fallback to loguru if no callback
        log_text_response=False,
        log_tool_calls=True if not callback else False,
        log_tool_results=True if not callback else False,
        truncate_thinking=1000,
        truncate_tool_results=1000,
        exclude_tools=[],
    )
    context_edit_middleware = ContextEditingMiddleware(
        edits=[
            ClearToolUsesEdit(
                trigger=100000,  # Clear after 100k tokens
                keep=5,  # Keep last 5 tool results
            )
        ]
    )
    msg_summary_middleware = SummarizationMiddleware(
        model=model,
        trigger=(
            "tokens",
            int(model_context_window * 0.6),  # Summarize at 60% context
        ),
        keep=("messages", 20),  # Keep last 20 messages
    )

    # Create agent with KG and Doc tools + all middlewares
    agent = create_agent(
        model=model,
        tools=[search_knowledge_graph, search_document_library],
        system_prompt=QA_AGENT_SYSTEM_PROMPT,
        middleware=[
            context_edit_middleware,
            msg_summary_middleware,
            todo_middleware,
            patch_middleware,
            log_message_middleware,
            retry_middleware,
            stop_check_middleware,
        ],
    )

    return agent


async def run_ask_mode(question: str, verbose: bool = False) -> None:
    """Run Q&A Agent mode via server SSE streaming.

    Connects to BrandMind API server, creates an ask session,
    and streams the response with Rich Live display.

    Args:
        question: Marketing question to answer
        verbose: Show detailed agent processing (not implemented yet)
    """
    from cli.agent_renderer import AgentOutputRenderer
    from cli.client import BrandMindClient, ServerNotRunningError
    from server.schemas.enums import SessionMode
    from server.schemas.events import StreamDoneEvent
    from shared.agent_middlewares.callback_types import StreamingTokenEvent

    console.print(
        Panel(
            f"[bold cyan]{question}[/bold cyan]",
            title="Question",
            border_style="cyan",
        )
    )

    renderer = AgentOutputRenderer(console)
    client = BrandMindClient()

    try:
        # Check server health
        await client.health()

        # Create session
        info = await client.create_session(SessionMode.ASK)

        with renderer:
            renderer.reset_streaming_state()

            accumulated_answer = ""

            async for event in client.stream_message(info.session_id, question):
                if isinstance(event, StreamDoneEvent):
                    break

                renderer.handle_event(event)

                if isinstance(event, StreamingTokenEvent):
                    if event.token and not event.done:
                        accumulated_answer += event.token

            if accumulated_answer:
                console.print()

    except ServerNotRunningError:
        console.print(
            Panel(
                "[bold red]BrandMind server not running.[/bold red]\n"
                "Start with: [bold]brandmind serve[/bold]",
                title="Error",
                border_style="red",
            )
        )
    except Exception as e:
        console.print(Panel(f"[red]{e}[/red]", title="Error", border_style="red"))
        logger.exception("Q&A Agent failed")


async def run_kg_search_mode(query: str, max_results: int = 10) -> None:
    """Run Knowledge Graph search mode via server.

    Args:
        query: Conceptual query about marketing
        max_results: Maximum number of results to return
    """
    from cli.client import BrandMindClient, ServerNotRunningError

    console.print(
        Panel(
            f"[bold magenta]{query}[/bold magenta]\n"
            f"[dim]Max Results: {max_results}[/dim]",
            title="Knowledge Graph Search",
            border_style="magenta",
        )
    )

    client = BrandMindClient()
    with console.status("[bold magenta]Searching...", spinner="dots"):
        try:
            results = await client.search_kg(query=query, max_results=max_results)
            console.print()
            console.print(Markdown(results))
        except ServerNotRunningError:
            console.print(
                "[bold red]BrandMind server not running.[/bold red]\n"
                "Start with: [bold]brandmind serve[/bold]"
            )
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            logger.exception("KG search failed")


async def run_docs_search_mode(
    query: str,
    book: Optional[str] = None,
    chapter: Optional[str] = None,
    author: Optional[str] = None,
    top_k: int = 10,
) -> None:
    """Run Document Library search mode via server.

    Args:
        query: Text to search for in documents
        book: Filter by book name (exact match)
        chapter: Filter by chapter (partial match)
        author: Filter by author (exact match)
        top_k: Number of results to return
    """
    from cli.client import BrandMindClient, ServerNotRunningError

    filters = []
    if book:
        filters.append(f"Book: {book}")
    if chapter:
        filters.append(f"Chapter: {chapter}")
    if author:
        filters.append(f"Author: {author}")
    filter_text = " | ".join(filters) if filters else "None"

    console.print(
        Panel(
            f"[bold blue]{query}[/bold blue]\n"
            f"[dim]Filters: {filter_text}[/dim]\n"
            f"[dim]Top K: {top_k}[/dim]",
            title="Document Library Search",
            border_style="blue",
        )
    )

    client = BrandMindClient()
    with console.status("[bold blue]Searching...", spinner="dots"):
        try:
            results = await client.search_docs(
                query=query,
                book=book,
                chapter=chapter,
                author=author,
                top_k=top_k,
            )
            console.print()
            console.print(results)
        except ServerNotRunningError:
            console.print(
                "[bold red]BrandMind server not running.[/bold red]\n"
                "Start with: [bold]brandmind serve[/bold]"
            )
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            logger.exception("Document search failed")


async def run_browser_setup_mode() -> None:
    """
    Run Browser Login Setup mode.

    Opens a headed browser in the persistent context allowing the user
    to manually log into social media platforms (Facebook, Instagram, TikTok)
    using clone accounts. Session is saved for future Agent use.
    """
    from shared.agent_tools.browser import BrowserManager

    # Print prominent warning using Rich
    warning_panel = Panel(
        "[bold yellow]⚠️ WARNING: ALWAYS USE CLONE ACCOUNTS ⚠️[/bold yellow]\n\n"
        "AI agents can sometimes trigger automated bot detection systems on social\n"
        "media platforms like Facebook, Instagram, or TikTok.\n\n"
        "[bold red]DO NOT use your personal or main business accounts.[/bold red]\n"
        "Please log in using secondary 'clone' accounts to absolutely guarantee\n"
        "that your primary accounts are not at risk of being banned or restricted.\n\n"
        "[dim]The browser will now open 3 platforms for you to log in.\n"
        "Close the browser window when you are completely finished.[/dim]",
        title="Security Advisory",
        border_style="yellow",
        expand=False,
    )
    console.print(warning_panel)
    console.print()

    from rich.prompt import Confirm

    if not Confirm.ask("[bold]I understand the risks and want to proceed[/bold]"):
        console.print("[yellow]Setup aborted.[/yellow]")
        return

    with console.status(
        "[bold cyan]Launching secure browser environment...", spinner="dots"
    ):
        manager = BrowserManager()

    try:
        # Default platforms for brand intelligence
        urls = [
            "https://www.facebook.com",
            "https://www.instagram.com",
            "https://www.tiktok.com",
        ]
        await manager.setup_login(urls)
        console.print("[bold green]✅ Browser session saved successfully![/bold green]")
        console.print("[dim]The AI Agent can now use this session for research.[/dim]")
    except Exception as e:
        console.print(f"[bold red]❌ Browser setup failed: {e}[/bold red]")
        logger.exception("Browser setup failed")


async def run_browser_status_mode() -> None:
    """Check the status of the persistent browser session."""
    from shared.agent_tools.browser import BrowserManager

    manager = BrowserManager()
    if manager.is_session_valid():
        console.print(
            "[bold green]✅ Browser session is VALID and ready "
            "for Agent use.[/bold green]"
        )
        console.print(f"[dim]Data directory: {manager.data_dir}[/dim]")
    else:
        console.print("[bold yellow]⚠️ No valid browser session found.[/bold yellow]")
        console.print(
            "Run [cyan]brandmind browser setup[/cyan] to login and create a session."
        )


async def run_browser_reset_mode() -> None:
    """Reset the persistent browser session."""
    from rich.prompt import Confirm

    from shared.agent_tools.browser import BrowserManager

    manager = BrowserManager()

    if not manager.is_session_valid():
        console.print("[yellow]No active session to reset.[/yellow]")
        return

    console.print(
        Panel(
            "[bold red]WARNING: This will delete your saved "
            "browser session.[/bold red]\n"
            "You will need to run 'brandmind browser setup' again "
            "to log into social platforms.",
            title="Reset Session",
            border_style="red",
        )
    )

    if Confirm.ask("[bold red]Are you sure you want to delete the session?[/bold red]"):
        manager.reset_session()
        console.print(
            "[bold green]✅ Browser session deleted successfully.[/bold green]"
        )
    else:
        console.print("[yellow]Reset aborted.[/yellow]")


def _serve_state_dir() -> Path:
    """Return the BrandMind server control directory under BRANDMIND_HOME."""
    from shared import workspace as workspace_mod

    return workspace_mod.BRANDMIND_HOME / "server"


def _serve_pid_path() -> Path:
    """Return the detached server pid-file path."""
    return _serve_state_dir() / _SERVE_PID_FILE


def _serve_log_path() -> Path:
    """Return the detached server log-file path."""
    return _serve_state_dir() / _SERVE_LOG_FILE


def _read_detached_pid(pid_path: Path | None = None) -> int | None:
    """Read the tracked detached server pid if present and valid."""
    path = pid_path or _serve_pid_path()
    try:
        raw_pid = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    except OSError:
        return None

    try:
        return int(raw_pid)
    except ValueError:
        return None


def _is_pid_running(pid: int) -> bool:
    """Return whether the process id appears alive on this host."""
    import os

    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _remove_stale_pid_file(pid_path: Path | None = None) -> None:
    """Delete a stale pid file without failing the command."""
    path = pid_path or _serve_pid_path()
    try:
        path.unlink()
    except FileNotFoundError:
        return
    except OSError as exc:
        console.print(f"[yellow]Could not remove stale pid file: {exc}[/yellow]")


def _serve_health_url(host: str, port: int) -> str:
    """Build a local health URL for a configured server bind address.

    The ``"0.0.0.0"`` / ``"::"`` strings here are config values to
    recognize, not bind directives. Bandit's B104 rule flags the
    literal because it cannot tell the comparison from a bind; the
    ``nosec`` annotation marks the audit decision explicitly.
    """
    probe_host = (
        "127.0.0.1" if host in {"0.0.0.0", "::"} else host  # nosec B104
    )
    return f"http://{probe_host}:{port}/api/v1/health"


def _server_health_ok(host: str, port: int) -> bool:
    """Return whether the configured server health endpoint responds.

    The ``urlopen`` call below is invoked with a URL built entirely
    from :func:`_serve_health_url`, which hard-codes the ``http://``
    scheme around a sanitized host + integer port + fixed path. No
    portion of the URL is influenced by remote input, so B310's
    ``file://`` / custom-scheme concern does not apply; the
    ``nosec`` annotation records the audit.
    """
    url = _serve_health_url(host, port)
    try:
        with urlopen(  # nosec B310
            url, timeout=_SERVE_HEALTH_TIMEOUT_SECONDS
        ) as response:
            return 200 <= response.status < 300
    except (OSError, URLError):
        return False


def _run_uvicorn_server() -> None:
    """Run the BrandMind API server in the foreground."""
    import uvicorn

    from config.system_config import SETTINGS
    from server.main import create_app

    app = create_app()
    uvicorn.run(app, host=SETTINGS.BRANDMIND_HOST, port=SETTINGS.BRANDMIND_PORT)


def _start_detached_server() -> None:
    """Start `brandmind serve` in the background and record its pid."""
    import os
    import subprocess  # nosec B404
    import sys
    import time

    from config.system_config import SETTINGS

    state_dir = _serve_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    pid_path = _serve_pid_path()
    log_path = _serve_log_path()

    tracked_pid = _read_detached_pid(pid_path)
    if tracked_pid and _is_pid_running(tracked_pid):
        health_url = _serve_health_url(
            SETTINGS.BRANDMIND_HOST,
            SETTINGS.BRANDMIND_PORT,
        )
        console.print(
            "[yellow]BrandMind server is already tracked as running "
            f"(pid {tracked_pid}).[/yellow]\n"
            f"Health: {health_url}\n"
            f"Log: {log_path}"
        )
        return
    if tracked_pid:
        _remove_stale_pid_file(pid_path)

    if _server_health_ok(SETTINGS.BRANDMIND_HOST, SETTINGS.BRANDMIND_PORT):
        console.print(
            "[yellow]BrandMind server already responds on the configured port, "
            "but it is not tracked by a detached pid file.[/yellow]\n"
            "Stop that foreground process before starting a detached server."
        )
        return

    command = [sys.executable, "-m", "cli.inference", "serve"]
    env = os.environ.copy()
    with log_path.open("ab") as log_file:
        process = subprocess.Popen(  # nosec B603
            command,
            cwd=Path.cwd(),
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    pid_path.write_text(f"{process.pid}\n", encoding="utf-8")

    deadline = time.monotonic() + _SERVE_STARTUP_WAIT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            _remove_stale_pid_file(pid_path)
            console.print(
                "[red]BrandMind detached server exited during startup.[/red]\n"
                f"Check log: {log_path}"
            )
            return
        if _server_health_ok(SETTINGS.BRANDMIND_HOST, SETTINGS.BRANDMIND_PORT):
            health_url = _serve_health_url(
                SETTINGS.BRANDMIND_HOST,
                SETTINGS.BRANDMIND_PORT,
            )
            console.print(
                "[green]BrandMind server started in detached mode.[/green]\n"
                f"PID: {process.pid}\n"
                f"Health: {health_url}\n"
                f"Log: {log_path}"
            )
            return
        time.sleep(0.25)

    console.print(
        "[yellow]BrandMind detached server started but is still warming up.[/yellow]\n"
        f"PID: {process.pid}\n"
        f"Log: {log_path}\n"
        "Run `brandmind serve --status` to check readiness."
    )


def _terminate_process_group(pid: int) -> None:
    """Terminate a detached process group, falling back to the pid only."""
    import os
    import signal

    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except OSError:
        os.kill(pid, signal.SIGTERM)


def _kill_process_group(pid: int) -> None:
    """Kill a detached process group, falling back to the pid only."""
    import os
    import signal

    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except OSError:
        os.kill(pid, signal.SIGKILL)


def _stop_detached_server() -> None:
    """Stop the tracked detached BrandMind server if one exists."""
    import time

    pid_path = _serve_pid_path()
    pid = _read_detached_pid(pid_path)
    if pid is None:
        console.print("[yellow]No detached BrandMind server pid file found.[/yellow]")
        return

    if not _is_pid_running(pid):
        _remove_stale_pid_file(pid_path)
        console.print("[yellow]Removed stale BrandMind server pid file.[/yellow]")
        return

    _terminate_process_group(pid)
    deadline = time.monotonic() + _SERVE_STOP_WAIT_SECONDS
    while time.monotonic() < deadline:
        if not _is_pid_running(pid):
            _remove_stale_pid_file(pid_path)
            console.print("[green]BrandMind detached server stopped.[/green]")
            return
        time.sleep(0.2)

    _kill_process_group(pid)
    _remove_stale_pid_file(pid_path)
    console.print("[yellow]BrandMind detached server was force-stopped.[/yellow]")


def _print_detached_status() -> None:
    """Print detached server pid and health status."""
    from config.system_config import SETTINGS

    pid_path = _serve_pid_path()
    log_path = _serve_log_path()
    pid = _read_detached_pid(pid_path)
    health_ok = _server_health_ok(SETTINGS.BRANDMIND_HOST, SETTINGS.BRANDMIND_PORT)
    health_url = _serve_health_url(SETTINGS.BRANDMIND_HOST, SETTINGS.BRANDMIND_PORT)

    if pid is not None and _is_pid_running(pid):
        health_text = "healthy" if health_ok else "not ready"
        console.print(
            f"[green]BrandMind detached server pid {pid} is running.[/green]\n"
            f"Health: {health_text} ({health_url})\n"
            f"Log: {log_path}"
        )
        return

    if pid is not None:
        _remove_stale_pid_file(pid_path)
        console.print("[yellow]Removed stale BrandMind server pid file.[/yellow]")

    if health_ok:
        console.print(
            "[yellow]BrandMind server responds, but no detached pid is "
            "tracked.[/yellow]\n"
            f"Health: {health_url}"
        )
        return

    console.print("[dim]BrandMind detached server is not running.[/dim]")


def _read_log_tail(log_path: Path, lines: int) -> list[str]:
    """Read the last N lines from a detached server log file."""
    from collections import deque

    if lines <= 0:
        return []

    with log_path.open("r", encoding="utf-8", errors="replace") as log_file:
        return list(deque(log_file, maxlen=lines))


def _print_server_logs(*, follow: bool, tail_lines: int) -> None:
    """Print detached server logs, optionally following new lines."""
    import time

    log_path = _serve_log_path()
    if not log_path.exists():
        console.print(
            "[yellow]No BrandMind server log file found.[/yellow]\n"
            f"Expected: {log_path}\n"
            "Start a detached server with: brandmind serve --detach"
        )
        return

    for line in _read_log_tail(log_path, tail_lines):
        console.print(line.rstrip("\n"), markup=False, highlight=False)

    if not follow:
        return

    console.print(
        f"[dim]Following BrandMind server log: {log_path} (Ctrl-C to stop)[/dim]"
    )
    try:
        with log_path.open("r", encoding="utf-8", errors="replace") as log_file:
            log_file.seek(0, 2)
            while True:
                line = log_file.readline()
                if line:
                    console.print(
                        line.rstrip("\n"),
                        markup=False,
                        highlight=False,
                    )
                    continue
                time.sleep(_SERVE_LOG_FOLLOW_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        console.print("[dim]Stopped following BrandMind server log.[/dim]")


def _run_serve_command(argv: Sequence[str]) -> None:
    """Run foreground, detached, stop, or status behavior for `brandmind serve`."""
    parser = argparse.ArgumentParser(
        prog="brandmind serve",
        description="Start or manage the BrandMind API server.",
    )
    parser.add_argument(
        "--detach",
        "-d",
        action="store_true",
        help="Start the API server in the background and write a pid file.",
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop the tracked detached API server.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show tracked detached server status and health.",
    )
    parser.add_argument(
        "--logs",
        action="store_true",
        help="Print detached server logs.",
    )
    parser.add_argument(
        "--follow",
        "-f",
        action="store_true",
        help="Follow detached server logs after printing the current tail.",
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=_SERVE_DEFAULT_LOG_TAIL_LINES,
        help=(
            "Number of log lines to print with --logs "
            f"(default: {_SERVE_DEFAULT_LOG_TAIL_LINES})."
        ),
    )
    args = parser.parse_args(list(argv))

    selected_actions = sum(
        bool(flag) for flag in (args.detach, args.stop, args.status, args.logs)
    )
    if selected_actions > 1:
        parser.error("Choose only one of --detach, --stop, --status, or --logs.")
    if args.follow and not args.logs:
        parser.error("--follow can only be used with --logs.")
    if args.tail < 0:
        parser.error("--tail must be zero or greater.")

    if args.stop:
        _stop_detached_server()
    elif args.status:
        _print_detached_status()
    elif args.logs:
        _print_server_logs(follow=args.follow, tail_lines=args.tail)
    elif args.detach:
        _start_detached_server()
    else:
        _run_uvicorn_server()


async def async_main() -> None:
    """
    Main CLI entry point for inference operations.

    Parses command-line arguments and dispatches to appropriate mode handler.
    """
    parser = argparse.ArgumentParser(
        description=(
            "BrandMind AI - Marketing Knowledge Assistant.\n\n"
            "Run without arguments to launch interactive TUI."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  brandmind                                      # Launch interactive TUI (default)
  brandmind brand-strategy                       # Interactive brand strategy session
  brandmind brand-strategy -m "Quán café mới"    # Start with initial message
  brandmind brand-strategy --session abc123      # Resume a saved session
  brandmind ask -q "What is Marketing Myopia?"   # One-shot Q&A
  brandmind search-kg -q "customer value" -n 10  # Search Knowledge Graph
  brandmind search-docs -q "pricing" -c "Ch 10"  # Search Documents
  brandmind serve                                # Start API server (port from .env)
  brandmind browser setup                        # Login to social media
  brandmind browser status                       # Check session validity
  brandmind browser reset                        # Delete current session
        """,
    )

    subparsers = parser.add_subparsers(dest="mode", help="Inference mode")

    # Mode: ask
    ask_parser = subparsers.add_parser("ask", help="Ask a marketing question")
    ask_parser.add_argument(
        "--question", "-q", required=True, help="Marketing question to answer"
    )
    ask_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show agent thinking and tool calls",
    )

    # Mode: search-kg
    kg_parser = subparsers.add_parser("search-kg", help="Search Knowledge Graph")
    kg_parser.add_argument(
        "--query", "-q", required=True, help="Conceptual query about marketing"
    )
    kg_parser.add_argument(
        "--max-results",
        "-n",
        type=int,
        default=10,
        help="Maximum results (default: 10)",
    )

    # Mode: search-docs
    docs_parser = subparsers.add_parser("search-docs", help="Search Document Library")
    docs_parser.add_argument("--query", "-q", required=True, help="Text to search for")
    docs_parser.add_argument("--book", "-b", help="Filter by book (exact)")
    docs_parser.add_argument("--chapter", "-c", help="Filter by chapter (partial)")
    docs_parser.add_argument("--author", "-a", help="Filter by author (exact)")
    docs_parser.add_argument(
        "--top-k", "-k", type=int, default=10, help="Number of results (default: 10)"
    )

    # Mode: brand-strategy
    brand_strategy_parser = subparsers.add_parser(
        "brand-strategy",
        help="Start interactive brand strategy session",
    )
    brand_strategy_parser.add_argument(
        "-m",
        "--message",
        help="Initial message to start the session",
        default=None,
    )
    brand_strategy_parser.add_argument(
        "--session",
        help="Resume a previous session by ID",
        default=None,
    )

    # Mode: serve
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start BrandMind API server (config via BRANDMIND_HOST/PORT in .env)",
    )
    serve_parser.add_argument(
        "--detach",
        "-d",
        action="store_true",
        help="Start the API server in the background and write a pid file.",
    )
    serve_parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop the tracked detached API server.",
    )
    serve_parser.add_argument(
        "--status",
        action="store_true",
        help="Show tracked detached server status and health.",
    )
    serve_parser.add_argument(
        "--logs",
        action="store_true",
        help="Print detached server logs.",
    )
    serve_parser.add_argument(
        "--follow",
        "-f",
        action="store_true",
        help="Follow detached server logs after printing the current tail.",
    )
    serve_parser.add_argument(
        "--tail",
        type=int,
        default=_SERVE_DEFAULT_LOG_TAIL_LINES,
        help=(
            "Number of log lines to print with --logs "
            f"(default: {_SERVE_DEFAULT_LOG_TAIL_LINES})."
        ),
    )

    # Mode: web
    subparsers.add_parser(
        "web",
        help=(
            "Start the BrandMind web UI (Reflex). "
            "Install with `uv sync --group web` first. "
            "Backend reached via BRANDMIND_API_URL."
        ),
        description=(
            "Start the BrandMind web UI as a Reflex frontend that talks to "
            "an already-running `brandmind serve` backend.\n\n"
            "Environment variables (sensible defaults in .env):\n"
            "  BRANDMIND_WEB_PORT          Frontend port (default 8501)\n"
            "  BRANDMIND_WEB_BACKEND_PORT  Reflex state-sync port (default 8502)\n"
            "  BRANDMIND_API_URL           Backend URL (default localhost:8000)\n\n"
            "Pre-flight: install Reflex with `uv sync --group web` once.\n"
            "Then in another shell start the backend: `brandmind serve`.\n"
            "Open http://localhost:8501 in a browser after Reflex finishes "
            "compiling."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Mode: browser
    browser_parser = subparsers.add_parser(
        "browser", help="Manage browser agent settings"
    )
    browser_subparsers = browser_parser.add_subparsers(
        dest="browser_action", help="Browser action"
    )

    # Sub-mode: browser setup
    browser_subparsers.add_parser(
        "setup",
        help="Open browser to login to social platforms using clone accounts",
    )
    # Sub-mode: browser status
    browser_subparsers.add_parser(
        "status",
        help="Check if the saved browser session is valid",
    )
    # Sub-mode: browser reset
    browser_subparsers.add_parser(
        "reset",
        help="Delete the saved browser session",
    )

    args = parser.parse_args()

    if args.mode is None:
        # TUI will be handled in sync main() - just return
        return None

    # Dispatch to handlers
    if args.mode == "serve":
        # Serve runs synchronously (uvicorn manages its own event loop)
        # Return early so async_main doesn't try to await it
        return args.mode
    elif args.mode == "web":
        # Web mode launches Reflex as a subprocess from `main()` (sync)
        # for the same reason serve runs sync — Reflex manages its own
        # event loop + Node.js frontend dev server.
        return args.mode
    elif args.mode == "brand-strategy":
        from cli.brand_strategy import run_brand_strategy_session

        await run_brand_strategy_session(
            initial_message=args.message,
            session_id=args.session,
        )
    elif args.mode == "ask":
        await run_ask_mode(args.question, verbose=args.verbose)
    elif args.mode == "search-kg":
        await run_kg_search_mode(args.query, args.max_results)
    elif args.mode == "search-docs":
        await run_docs_search_mode(
            args.query, args.book, args.chapter, args.author, args.top_k
        )
    elif args.mode == "browser":
        if args.browser_action == "setup":
            await run_browser_setup_mode()
        elif args.browser_action == "status":
            await run_browser_status_mode()
        elif args.browser_action == "reset":
            await run_browser_reset_mode()
        else:
            parser.parse_args(["browser", "--help"])

    return args.mode


def _launch_web_ui() -> None:
    """Spawn the Reflex frontend / state-sync backend for the web UI.

    Resolves the Reflex project root (``<repo>/web``) relative to this
    file, builds the ``reflex run`` command with explicit frontend +
    backend ports drawn from :data:`config.system_config.SETTINGS`, and
    runs it as a foreground subprocess so Ctrl-C from the user shell
    terminates Reflex cleanly. ``BRANDMIND_API_URL`` is propagated into
    the child process so the placeholder page polls the right backend
    without separate configuration.
    """
    import os
    import shutil
    import subprocess  # nosec B404
    import sys
    from pathlib import Path

    from config.system_config import SETTINGS

    repo_root = Path(__file__).resolve().parents[2]
    web_dir = repo_root / "web"
    if not (web_dir / "rxconfig.py").is_file():
        console.print(
            "[red]Reflex project not found at "
            f"{web_dir}/rxconfig.py.[/red] Did the repo move?"
        )
        sys.exit(1)

    reflex_cmd = shutil.which("reflex")
    if reflex_cmd is None:
        console.print(
            "[yellow]Reflex is not installed in the active environment.[/yellow]\n"
            "Install with: [bold]uv sync --group web[/bold]\n"
            "Then re-run: [bold]brandmind web[/bold]"
        )
        sys.exit(1)

    env = os.environ.copy()
    env.setdefault("BRANDMIND_API_URL", SETTINGS.BRANDMIND_API_URL)

    command = [
        reflex_cmd,
        "run",
        "--frontend-port",
        str(SETTINGS.BRANDMIND_WEB_PORT),
        "--backend-port",
        str(SETTINGS.BRANDMIND_WEB_BACKEND_PORT),
        "--backend-host",
        SETTINGS.BRANDMIND_HOST,
    ]
    console.print(
        f"[cyan]Launching BrandMind web UI on "
        f"http://localhost:{SETTINGS.BRANDMIND_WEB_PORT}[/cyan]\n"
        f"Backend pollee: [bold]{SETTINGS.BRANDMIND_API_URL}[/bold]\n"
        f"Start the BrandMind API server in another shell with: "
        f"[bold]brandmind serve[/bold]"
    )
    try:
        subprocess.run(command, cwd=web_dir, env=env, check=False)  # nosec B603
    except KeyboardInterrupt:
        # Reflex propagates Ctrl-C internally; suppress the traceback
        # so the user gets a clean shell prompt back.
        return


def main() -> None:
    """Synchronous entry point for CLI."""
    import os
    import sys

    # Suppress verbose gRPC logs (must be set before gRPC is imported)
    os.environ.setdefault("GRPC_VERBOSITY", "ERROR")

    # Check if no args or help requested - launch TUI
    # We need to check before asyncio.run() to avoid nested event loops
    if len(sys.argv) == 1:
        # No args - launch interactive TUI
        from cli.tui.app import run_tui

        run_tui()
        return

    # Handle 'serve' mode synchronously (uvicorn runs its own loop)
    if len(sys.argv) >= 2 and sys.argv[1] == "serve":
        _run_serve_command(sys.argv[2:])
        return

    # Handle 'web' mode synchronously (Reflex manages its own loop + Node).
    # Fall through to argparse when --help / -h is present so the user gets
    # the subcommand's argparse-generated help instead of `reflex run --help`.
    if (
        len(sys.argv) >= 2
        and sys.argv[1] == "web"
        and not any(arg in {"--help", "-h"} for arg in sys.argv[2:])
    ):
        _launch_web_ui()
        return

    # Otherwise run the async CLI
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
