"""Deep Agent configuration for Document Cartographer.

Sets up Gemini 2.5 Flash Lite model with FilesystemMiddleware, TodoWriteMiddleware,
SubAgentMiddleware, and custom tools for document structure analysis.
"""

from pathlib import Path

from deepagents.backends import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from deepagents.middleware.subagents import SubAgentMiddleware
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ClearToolUsesEdit,
    ContextEditingMiddleware,
    SummarizationMiddleware,
    ToolRetryMiddleware,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

from config.system_config import SETTINGS
from prompts.knowledge_graph import CARTOGRAPHER_SYSTEM_PROMPT
from shared.agent_middlewares import (
    EnsureTasksFinishedMiddleware,
    LogModelMessageMiddleware,
)
from shared.agent_tools import TodoWriteMiddleware, line_search


def create_cartographer_agent(
    document_folder: str,
    model_name: str = "gemini-2.5-pro",
) -> tuple[object, ChatGoogleGenerativeAI]:
    """Create a Deep Agent configured for document structure mapping.

    This agent has access to:
    - Filesystem tools (read_file, ls, glob, grep)
    - TodoWrite tool for planning
    - line_search tool for finding exact line numbers
    - SubAgent for delegating repetitive tasks
    - StopCheck hook for ensuring tasks are completed
    - ContextEditing and Summarization middlewares for managing model context
    - LogModelMessage middleware for logging model messages
    - Gemini 2.5 Pro with thinking mode by default

    Args:
        document_folder: Absolute path to parsed document folder

    Returns:
        Tuple of (configured agent, model instance)
    """
    logger.info("Initializing Document Cartographer agent...")

    # 1. Initialize Gemini model with thinking mode
    model = ChatGoogleGenerativeAI(
        google_api_key=SETTINGS.GEMINI_API_KEY,
        model=model_name,
        temperature=0.1,
        thinking_budget=4000,
        max_output_tokens=50000,
        include_thoughts=True,  # Enable reasoning output
    )
    model_context_window = 1048576
    logger.info(f"✓ {model_name.replace('-', ' ').title()} model initialized")

    # 2. Setup Filesystem Backend
    # Use virtual_mode=True to map / to document folder
    backend = FilesystemBackend(
        root_dir=str(Path(document_folder).absolute()), virtual_mode=True
    )
    fs_middleware = FilesystemMiddleware(backend=backend)
    logger.info(f"✓ Filesystem backend: {document_folder}")

    # 2.1 Fix grep tool's virtual glob pattern bug
    # FilesystemBackend doesn't resolve glob parameter from virtual to real path
    # We wrap the original grep to strip leading / from glob patterns
    original_grep = None
    for t in fs_middleware.tools:
        if t.name == "grep":
            original_grep = t
            break

    if original_grep:
        from typing import Literal

        from deepagents.middleware.filesystem import (
            GREP_TOOL_DESCRIPTION,
            FilesystemState,
        )
        from langchain.tools import ToolRuntime, tool

        @tool(description=GREP_TOOL_DESCRIPTION)
        def grep(
            pattern: str,
            runtime: ToolRuntime[None, FilesystemState],
            path: str | None = None,
            glob: str | None = None,
            output_mode: Literal[
                "files_with_matches", "content", "count"
            ] = "files_with_matches",
        ) -> str:
            """Search for pattern in files (with virtual glob fix)."""
            # Fix: Strip leading / from virtual glob pattern
            # Virtual: /page_*.md → Real: page_*.md
            if glob and glob.startswith("/"):
                glob = glob.lstrip("/")

            # Call original grep implementation
            return original_grep.func(
                pattern=pattern,
                runtime=runtime,
                path=path,
                glob=glob,
                output_mode=output_mode,
            )

        # Replace grep in middleware's tools list
        for i, t in enumerate(fs_middleware.tools):
            if t.name == "grep":
                fs_middleware.tools[i] = grep
                logger.info("✓ Grep tool patched with virtual glob fix")
                break

    # 3. Setup Middlewares
    todo_middleware = TodoWriteMiddleware()
    patch_middleware = PatchToolCallsMiddleware()
    retry_middleware = ToolRetryMiddleware()
    stop_check_middleware = EnsureTasksFinishedMiddleware()
    log_message_middleware = LogModelMessageMiddleware(
        log_thinking=True,
        log_text_response=False,
        log_tool_calls=True,
        log_tool_results=True,  # Enable tool result logging
        truncate_thinking=1000,  # Truncate long thinking to 1000 chars
        truncate_tool_results=1000,  # Truncate tool results to 1000 chars
        exclude_tools=["line_search"],  # Exclude verbose tools from result logging
    )
    context_edit_middleware = ContextEditingMiddleware(
        edits=[
            ClearToolUsesEdit(
                trigger=100000,  # Clear tool call results after 100000 tokens
                keep=5,  # Keep last 5 tool call results
            )
        ]
    )
    msg_summary_middleware = SummarizationMiddleware(
        model=model,
        trigger=(
            "tokens",
            int(model_context_window * 0.6),
        ),  # Summarize after 60% of context window
        keep=("messages", 20),  # Keep last 20 messages
    )

    # 4. Create line_search wrapper that resolves virtual paths
    # FilesystemBackend maps / to document_folder, but line_search uses real paths
    def line_search_wrapper(
        file_path: str,
        pattern: str,
        fuzzy_threshold: float = 85.0,
    ) -> dict[str, bool | int | str | float | None]:
        """Wrapper for line_search that resolves virtual filesystem paths.

        Args:
            file_path: Virtual path from agent (e.g., /page_26.md)
            pattern: Text pattern to find
            fuzzy_threshold: Minimum similarity score

        Returns:
            Same as line_search
        """
        # Resolve virtual path to real path
        # Remove leading / and join with document_folder
        if file_path.startswith("/"):
            file_path = file_path[1:]  # Remove leading /
        real_path = str(Path(document_folder) / file_path)

        logger.debug(f"Resolving virtual path to real: {file_path} -> {real_path}")
        return line_search(real_path, pattern, fuzzy_threshold)

    # Copy metadata from original function
    line_search_wrapper.__name__ = "line_search"  # type: ignore[attr-defined]
    line_search_wrapper.__doc__ = line_search.__doc__

    # 5. Setup SubAgent Middleware
    # Sub-agents can handle repetitive tasks (e.g., searching multiple headers)
    # They have same tools/middlewares as main agent (except SubAgentMiddleware itself)
    subagent_middleware = SubAgentMiddleware(
        default_model=model,
        default_tools=[line_search_wrapper],  # Sub-agent uses wrapped tool
        default_middleware=[
            context_edit_middleware,
            msg_summary_middleware,
            todo_middleware,
            fs_middleware,
            patch_middleware,
            log_message_middleware,
            retry_middleware,
            stop_check_middleware,
        ],
        general_purpose_agent=True,  # Sub-agent can handle general tasks
    )
    logger.info("✓ Middlewares configured (including SubAgent)")

    # 6. Collect tools
    tools = [line_search_wrapper]
    logger.info(f"✓ Custom tools: {[t.__name__ for t in tools]}")

    # 7. Create agent with all middlewares
    agent = create_agent(  # type: ignore[var-annotated]
        model=model,
        tools=tools,
        system_prompt=CARTOGRAPHER_SYSTEM_PROMPT,
        middleware=[
            context_edit_middleware,
            msg_summary_middleware,
            todo_middleware,
            fs_middleware,
            subagent_middleware,  # Enable sub-agent delegation
            patch_middleware,
            log_message_middleware,
            retry_middleware,
            stop_check_middleware,
        ],
    )
    logger.info("✓ Agent created successfully")

    return agent, model
