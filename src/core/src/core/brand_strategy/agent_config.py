"""Deep Agent configuration for Brand Strategy mode.

Creates a fully-configured agent with:
- All brand strategy tools (search, analysis, creative, document)
- SubAgentMiddleware for delegating to 4 specialized sub-agents
- SkillsMiddleware for progressive skill disclosure
- Context management middlewares (summarization, context editing)
- ToolSearchMiddleware for dynamic tool loading
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
    from core.brand_strategy.subagents import (
        create_brand_strategy_subagent_middleware,
    )
    from prompts.brand_strategy import BRAND_STRATEGY_SYSTEM_PROMPT
    from shared.agent_middlewares import (
        EnsureTasksFinishedMiddleware,
        LogModelMessageMiddleware,
        create_tool_search_middleware,
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
        PHASE_SEQUENCES,
        get_active_session,
        get_next_phase,
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

        updated: list[str] = []

        # Set scope
        if scope and scope != session.scope:
            session.scope = scope
            updated.append(f"scope: {scope}")
            seq = PHASE_SEQUENCES.get(scope, [])
            if seq:
                seq_str = " → ".join(p.replace("phase_", "P") for p in seq)
                updated.append(f"sequence: {seq_str}")

        # Set brand name
        if brand_name and brand_name != session.brand_name:
            session.brand_name = brand_name
            updated.append(f"brand: {brand_name}")

        # Advance to next phase
        if advance:
            if not session.scope:
                return (
                    "Cannot advance: scope not set yet. "
                    "Set scope first with report_progress(scope='...') "
                    "before advancing."
                )
            next_phase = get_next_phase(session.scope, session.current_phase)
            if next_phase is None:
                return (
                    f"All phases complete. "
                    f"Current: {session.current_phase}. "
                    f"Strategy finalized."
                )
            old = session.current_phase
            session.advance_phase(next_phase)
            # Build reference file hint
            phase_ref = next_phase.replace("phase_", "phase_")
            ref_file = f"references/{phase_ref.replace('phase_', 'phase_')}"
            if next_phase == "phase_0_5":
                ref_file = "references/phase_0_5_equity_audit.md"
            elif next_phase == "phase_1":
                ref_file = "references/phase_1_research.md"
            elif next_phase == "phase_2":
                ref_file = "references/phase_2_positioning.md"
            elif next_phase == "phase_3":
                ref_file = "references/phase_3_identity.md"
            elif next_phase == "phase_4":
                ref_file = "references/phase_4_communication.md"
            elif next_phase == "phase_5":
                ref_file = "references/phase_5_deliverables.md"

            # Remaining phases
            seq = PHASE_SEQUENCES[session.scope]
            idx = seq.index(next_phase)
            remaining = seq[idx:]
            remaining_str = " → ".join(p.replace("phase_", "P") for p in remaining)

            updated.append(f"phase: {old} → {next_phase}")
            updated.append(f"Next: Read /brand-strategy-orchestrator/{ref_file}")
            updated.append(f"Remaining: {remaining_str}")

        # Loop back (proactive triggers)
        if loop_back_to:
            old = session.current_phase
            session.advance_phase(loop_back_to)
            updated.append(f"Loop back: {old} → {loop_back_to} (proactive trigger)")

        if updated:
            return "Session updated: " + ", ".join(updated)
        return "No changes needed."

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

    # ---- All Brand Strategy Tools ----
    tools: list[Any] = [
        # Research (existing + new)
        search_knowledge_graph,
        search_document_library,
        search_web,
        scrape_web_content,
        browse_and_research,
        deep_research,
        # Analysis
        analyze_social_profile,
        get_search_autocomplete,
        # Creative
        generate_image,
        edit_image,
        generate_brand_key,
        # Document
        generate_document,
        generate_presentation,
        generate_spreadsheet,
        export_to_markdown,
        # Session tracking
        report_progress,
    ]

    # ---- Middlewares ----
    todo_middleware = TodoWriteMiddleware()
    patch_middleware = PatchToolCallsMiddleware()
    retry_middleware = ToolRetryMiddleware()
    stop_check_middleware = EnsureTasksFinishedMiddleware()

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

    # ToolSearch middleware (Task 47)
    tool_search_middleware = create_tool_search_middleware(
        all_tools=tools,
    )

    # Skills middleware + filesystem (Task 35)
    skills_middleware, fs_middleware = create_brand_strategy_skills_middleware()

    # Sub-agent middleware (Task 41)
    tools_registry = {
        getattr(tool, "name", getattr(tool, "__name__", str(tool))): tool
        for tool in tools
    }
    sub_agent_middleware = create_brand_strategy_subagent_middleware(
        tools_registry=tools_registry,
    )

    # ---- Assemble Agent ----
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=BRAND_STRATEGY_SYSTEM_PROMPT,
        middleware=[
            context_edit_middleware,
            msg_summary_middleware,
            tool_search_middleware,
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
