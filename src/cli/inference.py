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
from typing import Callable, Optional

from loguru import logger
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()


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


async def qa_agent_answer(question: str) -> str:
    """
    Answer marketing question using Q&A Agent with autonomous tool use.

    Args:
        question: Marketing question to answer

    Returns:
        Agent's answer based on retrieved knowledge
    """
    from langchain_core.messages import HumanMessage

    agent = create_qa_agent()

    # Agent expects {"messages": [HumanMessage(...)]} format
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=question)]},
        {"recursion_limit": 100},  # Limit recursion for safety
    )

    # Extract final response from messages
    if "messages" in result and result["messages"]:
        # Get last AI message
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content:
                # Handle both string and list content
                if isinstance(msg.content, list):
                    # Extract text parts
                    text_parts = []
                    for part in msg.content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                        elif isinstance(part, str):
                            text_parts.append(part)
                    if text_parts:
                        return "\n".join(text_parts)
                else:
                    return str(msg.content)

    return "No response generated"


async def run_ask_mode(question: str, verbose: bool = False) -> None:
    """
    Run Q&A Agent mode to answer marketing questions.

    Uses Rich Live display with agent renderer for Claude Code-style output.
    Tool logs are automatically routed based on contextvars.

    Args:
        question: Marketing question to answer
        verbose: Show detailed agent processing (not implemented yet)
    """
    from cli.agent_renderer import AgentOutputRenderer
    from cli.log_capture import SmartLogCapture
    from cli.tool_context import reset_current_tool, set_current_tool

    console.print(
        Panel(
            f"[bold cyan]{question}[/bold cyan]",
            title="🎯 Question",
            border_style="cyan",
        )
    )

    # Create renderer
    renderer = AgentOutputRenderer(console)

    # Create smart log capture with routing callbacks
    log_capture = SmartLogCapture(
        on_tool_log=renderer.add_tool_log,
        on_other_log=renderer.add_other_log,
    )

    try:
        # Start log capture FIRST - to catch early logs (FalkorDB init, etc.)
        with log_capture:
            # Then start renderer
            with renderer:
                # Create agent with:
                # - callback: for middleware events (thinking, tool_call, tool_result)
                # - on_tool_start/end: for context tracking (logs routing)
                agent = create_qa_agent(
                    callback=renderer.handle_event,
                    on_tool_start=set_current_tool,  # Inject hook
                    on_tool_end=reset_current_tool,  # Inject hook
                )

                # Stream agent response token-by-token for real-time display
                from langchain_core.messages import AIMessageChunk

                from shared.agent_middlewares.callback_types import (
                    StreamingThinkingEvent,
                    StreamingTokenEvent,
                )

                accumulated_answer = ""
                thinking_done = False  # Track if thinking phase has completed

                # Reset streaming state for new query
                renderer.reset_streaming_state()

                async for message_chunk, metadata in agent.astream(
                    {"messages": [{"role": "user", "content": question}]},
                    stream_mode="messages",
                ):
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
                                        # New block (e.g. multi-step)
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
                                            # When first text arrives, finalize thinking
                                            if not thinking_done:
                                                renderer.handle_event(
                                                    StreamingThinkingEvent(
                                                        token="", done=True
                                                    )
                                                )
                                                thinking_done = True
                                            accumulated_answer += token_text
                                            renderer.handle_event(
                                                StreamingTokenEvent(token=token_text)
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
                    renderer.handle_event(StreamingThinkingEvent(token="", done=True))
                    thinking_done = True

                # Send done signal to finalize streaming
                renderer.handle_event(StreamingTokenEvent(token="", done=True))
    except Exception as e:
        console.print(Panel(f"[red]{e}[/red]", title="❌ Error", border_style="red"))
        logger.exception("Q&A Agent failed")


async def run_kg_search_mode(query: str, max_results: int = 10) -> None:
    """
    Run Knowledge Graph search mode.

    Searches for marketing concepts, relationships, and source references
    using direct KG query without agent overhead.

    Args:
        query: Conceptual query about marketing
        max_results: Maximum number of results to return
    """
    from shared.agent_tools.retrieval import search_knowledge_graph

    console.print(
        Panel(
            f"[bold magenta]{query}[/bold magenta]\n"
            f"[dim]Max Results: {max_results}[/dim]",
            title="🔍 Knowledge Graph Search",
            border_style="magenta",
        )
    )

    with console.status("[bold magenta]Searching...", spinner="dots"):
        try:
            results = await search_knowledge_graph(query=query, max_results=max_results)
            console.print()
            console.print(Markdown(results))
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
    """
    Run Document Library search mode.

    Searches for text passages with optional book/chapter/author filters
    using hybrid search (dense + BM25).

    Args:
        query: Text to search for in documents
        book: Filter by book name (exact match)
        chapter: Filter by chapter (partial match)
        author: Filter by author (exact match)
        top_k: Number of results to return
    """
    from shared.agent_tools.retrieval import search_document_library

    # Build filter display
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
            title="📚 Document Library Search",
            border_style="blue",
        )
    )

    with console.status("[bold blue]Searching...", spinner="dots"):
        try:
            results = await search_document_library(
                query=query,
                filter_by_book=book,
                filter_by_chapter=chapter,
                filter_by_author=author,
                top_k=top_k,
            )
            console.print()
            console.print(results)
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
  brandmind ask -q "What is Marketing Myopia?"   # One-shot Q&A
  brandmind search-kg -q "customer value" -n 10  # Search Knowledge Graph
  brandmind search-docs -q "pricing" -c "Ch 10"  # Search Documents
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
    if args.mode == "ask":
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

    # Otherwise run the async CLI
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
