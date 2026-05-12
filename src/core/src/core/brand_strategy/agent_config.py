"""Deep Agent configuration for Brand Strategy mode.

Creates a fully-configured agent with:
- Orchestrator tools plus specialist-owned tool registries
- SubAgentMiddleware for delegating to 4 specialized sub-agents
- SkillsMiddleware for progressive skill disclosure
- Context management middlewares (summarization, context editing)
"""

from __future__ import annotations

from typing import Any, Callable, Optional


def create_brand_strategy_agent(
    callback: Optional[Callable] = None,
    on_tool_start: Optional[Callable[[str], object]] = None,
    on_tool_end: Optional[Callable[[object], None]] = None,
):  # type: ignore[return]
    """Create Brand Strategy Agent with full tool suite.

    Args:
        callback: Optional callback for agent events.
        on_tool_start: Hook called when tool starts.
        on_tool_end: Hook called when tool ends.

    Returns:
        Configured langchain agent with all brand strategy capabilities.
    """
    from deepagents.middleware.patch_tool_calls import (
        PatchToolCallsMiddleware,
    )
    from langchain.agents import create_agent
    from langchain.agents.middleware import (
        ClearToolUsesEdit,
        ContextEditingMiddleware,
        SummarizationMiddleware,
        ToolRetryMiddleware,
    )

    from config.system_config import SETTINGS
    from core.brand_strategy.content_check import (
        ContentCheckAdvanceMiddleware,
        DeliverableDispatchGuardMiddleware,
        PhaseStateReminderMiddleware,
    )
    from core.brand_strategy.subagents import (
        create_brand_strategy_subagent_middleware,
    )
    from prompts.brand_strategy import BRAND_STRATEGY_SYSTEM_PROMPT
    from shared.agent_middlewares import (
        EnsureTasksFinishedMiddleware,
        LogModelMessageMiddleware,
        WorkspaceBriefHygieneMiddleware,
    )
    from shared.agent_models.retry_gemini import (
        RetryChatGoogleGenerativeAI,
    )
    from shared.agent_skills import (
        create_brand_strategy_skills_middleware,
    )
    from shared.agent_tools import TodoWriteMiddleware

    # ---- Tool Imports ----
    from shared.agent_tools.analysis import (
        analyze_social_profile,
        get_search_autocomplete,
    )
    from shared.agent_tools.browser import (
        BrowserManager,
        create_browse_tool,
    )
    from shared.agent_tools.crawler.crawl_web import (
        scrape_web_content,
    )
    from shared.agent_tools.document import (
        export_to_markdown,
        generate_document,
        generate_presentation,
        generate_spreadsheet,
        list_artifacts,
    )
    from shared.agent_tools.image import (
        edit_image,
        generate_brand_key,
        generate_image,
    )
    from shared.agent_tools.research import deep_research
    from shared.agent_tools.retrieval import (
        search_document_library,
        search_knowledge_graph,
    )
    from shared.agent_tools.search import search_web

    # Browser tool
    _browser_manager = BrowserManager()
    browse_and_research = create_browse_tool(_browser_manager)

    # Session tracking tool
    from core.brand_strategy.session import (
        get_active_session,
        update_strategy_progress,
    )

    def report_progress(
        advance: bool = False,
        scope: str = "",
        brand_name: str = "",
        loop_back_to: str = "",
    ) -> str:
        """Update session tracking: advance phases, set scope, or set brand name.

        This tool manages your position in the phase workflow. Use it to:
        - **Advance**: Move to the next phase in the sequence (based on scope)
        - **Set scope**: Classify the project scope in Phase 0
        - **Set brand name**: Record the brand name when identified
        - **Loop back**: Return to an earlier phase when a proactive trigger fires

        Args:
            advance: Set True to move to the **next phase** in the sequence.
                The tool determines which phase is next based on the current
                scope. You do NOT choose the phase — the sequence does.
                Content-check middleware verifies your recent user-facing text
                contains the phase deliverable before allowing advance.
            scope: Brand scope classification from Phase 0. Valid values:
                new_brand, refresh, repositioning, full_rebrand.
                Setting scope also defines the phase sequence.
            brand_name: The brand name once identified by the user.
            loop_back_to: Only for proactive loop-back triggers (e.g.,
                stress test fails). Specify the phase to return to.

        Returns:
            Confirmation with current phase, next steps, and remaining sequence.
        """
        session = get_active_session()
        if session is None:
            return "No active session."

        return update_strategy_progress(
            session,
            advance=advance,
            scope=scope,
            brand_name=brand_name,
            loop_back_to=loop_back_to,
        )

    # Initialize model
    model = RetryChatGoogleGenerativeAI(
        google_api_key=SETTINGS.GEMINI_API_KEY,
        model="gemini-3-flash-preview",
        temperature=1.0,
        thinking_level="high",
        max_output_tokens=8000,
        include_thoughts=True,
    )
    model_context_window = 262144  # 256K tokens

    # ---- Brand Strategy Tools ----
    # The tool set is split into three groups so delegation boundaries are
    # enforced at registration rather than by prompt guidance alone.
    # ``main_agent_tools`` carries theory/source retrieval, light creative,
    # artifact verification, and session-tracking tools that the
    # orchestrator uses directly.
    # External market/social research and heavy deliverable generation stay
    # out of that list so the orchestrator must route them through the
    # owning specialist. This preserves user-specified research budgets and
    # prevents Phase 1 from expanding into direct web crawling.
    main_agent_tools: list[Any] = [
        # Theory and source retrieval
        search_knowledge_graph,
        search_document_library,
        # Light creative (quick iteration inline OK)
        generate_image,
        edit_image,
        # Light export (inline markdown output)
        export_to_markdown,
        # Artifact verification — read-only manifest query the
        # orchestrator uses at Phase 5 closure to confirm what the
        # current session has produced before declaring done.
        list_artifacts,
        # Session tracking
        report_progress,
    ]

    # Specialist-only: external evidence collection. Market and social
    # sub-agents resolve these from ``tools_registry`` when a bounded
    # research brief genuinely needs them.
    specialist_research_tools: list[Any] = [
        search_web,
        scrape_web_content,
        browse_and_research,
        deep_research,
        analyze_social_profile,
        get_search_autocomplete,
    ]

    # Sub-agent-only: heavy generation tools. Main agent must delegate via
    # `task(subagent_type="creative-studio" | "document-generator", ...)`.
    specialist_generation_tools: list[Any] = [
        generate_brand_key,  # creative-studio only
        generate_document,  # document-generator only
        generate_presentation,  # document-generator only
        generate_spreadsheet,  # document-generator only
    ]

    # Combined tools registry for sub-agent resolution — sub-agents resolve
    # their tool lists from this registry via `_resolve_tools(names, registry)`.
    tools: list[Any] = (
        main_agent_tools + specialist_research_tools + specialist_generation_tools
    )

    # ---- Middlewares ----
    todo_middleware = TodoWriteMiddleware()
    patch_middleware = PatchToolCallsMiddleware()
    retry_middleware = ToolRetryMiddleware()
    # Allow a single premature-stop reminder. Each reminder re-invokes
    # the downstream handler, which re-runs the model call, so higher
    # values compound response length when the agent keeps an
    # aspirational todo list open. One reminder preserves the defense
    # against silent early exits while keeping the response count
    # bounded. MALFORMED_FUNCTION_CALL recovery is controlled by a
    # separate counter inside the middleware and remains unaffected.
    stop_check_middleware = EnsureTasksFinishedMiddleware(max_reminders=1)

    log_message_middleware = LogModelMessageMiddleware(
        callback=callback,
        on_tool_start=on_tool_start,
        on_tool_end=on_tool_end,
        log_thinking=True if not callback else False,
        log_text_response=False,
        log_tool_calls=True if not callback else False,
        log_tool_results=True if not callback else False,
        truncate_thinking=1500,
        truncate_tool_results=1500,
        exclude_tools=[],
    )

    # Context management
    context_edit_middleware = ContextEditingMiddleware(
        edits=[
            ClearToolUsesEdit(
                trigger=150000,
                keep=8,
            )
        ]
    )
    msg_summary_middleware = SummarizationMiddleware(
        model=model,
        trigger=(
            "tokens",
            int(model_context_window * 0.8),
        ),
        keep=("messages", 30),
    )

    # Pre-compact workspace notes reminder (Task 50)
    # Fires BEFORE summarization to give agent time to save workspace notes
    from shared.agent_middlewares import PreCompactNotesMiddleware

    pre_compact_middleware = PreCompactNotesMiddleware(
        context_window=model_context_window,
        trigger_ratio=0.65,
    )

    # Content-check advance middleware.
    # Intercepts ``report_progress(advance=True)`` and defers to an LLM
    # judge to confirm that the agent's recent user-facing text
    # contains the deliverable expected for the current phase before
    # letting the advance land. Registered after the context-management
    # middlewares so it runs against the same message window the model
    # just produced, before filesystem and specialist dispatch.
    content_check_middleware = ContentCheckAdvanceMiddleware()
    deliverable_dispatch_guard_middleware = DeliverableDispatchGuardMiddleware()
    phase_state_reminder_middleware = PhaseStateReminderMiddleware()
    workspace_hygiene_middleware = WorkspaceBriefHygieneMiddleware()

    # Skills middleware + filesystem + workspace (Task 35 + 48)
    workspace_dir: str | None = None
    user_dir: str | None = None
    session = get_active_session()
    if session is not None:
        from shared.workspace import ensure_project_workspace

        ws_path, user_path = ensure_project_workspace(
            session_id=session.session_id,
            brand_name=session.brand_name,
        )
        if ws_path is not None and user_path is not None:
            workspace_dir = str(ws_path)
            user_dir = str(user_path)

    skills_middleware, fs_middleware = create_brand_strategy_skills_middleware(
        workspace_dir=workspace_dir,
        user_dir=user_dir,
    )

    # Sub-agent middleware.
    # The registry maps every tool name to its implementation across
    # ``main_agent_tools`` and specialist-only groups so each
    # sub-agent can resolve the tools named in its config (for
    # example, creative-studio needs ``generate_brand_key`` while
    # document-generator needs ``generate_document``), even though
    # those tools are not exposed to the main agent directly.
    tools_registry = {
        getattr(tool, "name", getattr(tool, "__name__", str(tool))): tool
        for tool in tools
    }
    sub_agent_middleware = create_brand_strategy_subagent_middleware(
        tools_registry=tools_registry,
    )

    # Session-aware system prompt (Task 49)
    system_prompt = BRAND_STRATEGY_SYSTEM_PROMPT
    if session is not None and session.completed_phases:
        # Resumed session — instruct agent to restore context from workspace
        completed_str = ", ".join(
            p.replace("phase_", "Phase ") for p in session.completed_phases
        )
        current_str = session.current_phase.replace("phase_", "Phase ")
        resume_addendum = (
            "\n\n# SESSION RESUME\n\n"
            "This is a **RESUMED session**. "
            f"You have completed phases: {completed_str}. "
            f"Current phase: **{current_str}**.\n\n"
            "**BEFORE responding to the user**, read your workspace notes "
            "to restore context:\n"
            '1. `read_file("/workspace/brand_brief.md")` — '
            "Executive Summary + Golden Thread\n"
            '2. `read_file("/workspace/working_notes.md")` — '
            "Pending items + observations\n"
            '3. `read_file("/workspace/quality_gates.md")` — '
            "Current gate status\n"
            '4. `read_file("/user/profile.md")` — '
            "User preferences\n\n"
            "After reading, briefly acknowledge to the user where you "
            "left off and what comes next. "
            "Do NOT ask the user to repeat information that is already "
            "in your workspace notes."
        )
        system_prompt = system_prompt + resume_addendum

    # ---- Assemble Agent ----
    agent = create_agent(
        model=model,
        tools=main_agent_tools,
        system_prompt=system_prompt,
        middleware=[
            context_edit_middleware,
            pre_compact_middleware,  # Task 50: remind at 65%
            msg_summary_middleware,  # Summarize at 80%
            phase_state_reminder_middleware,
            content_check_middleware,  # Verify agent text before allowing phase advance
            deliverable_dispatch_guard_middleware,
            workspace_hygiene_middleware,
            fs_middleware,
            skills_middleware,
            sub_agent_middleware,
            todo_middleware,
            patch_middleware,
            log_message_middleware,
            retry_middleware,
            stop_check_middleware,
        ],
    )

    return agent
