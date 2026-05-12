"""Builder function for Brand Strategy SubAgentMiddleware.

Creates a SubAgentMiddleware with 4 named sub-agents for brand strategy.
Each sub-agent has its own model instance, tool set, and system prompt.
"""

from __future__ import annotations

from typing import Any

from deepagents.backends.state import StateBackend
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from deepagents.middleware.subagents import SubAgentMiddleware
from langchain_core.tools import BaseTool
from langgraph.prebuilt.tool_node import ToolRuntime
from loguru import logger

from prompts.brand_strategy.subagents import (
    CREATIVE_STUDIO_SYSTEM_PROMPT,
    DOCUMENT_GENERATOR_SYSTEM_PROMPT,
    MARKET_RESEARCH_SYSTEM_PROMPT,
    SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT,
)
from shared.agent_middlewares import WorkspaceInjectionMiddleware

from .configs import (
    CREATIVE_STUDIO_TOOLS,
    DOCUMENT_GENERATOR_TOOLS,
    MARKET_RESEARCH_TOOLS,
    SOCIAL_MEDIA_TOOLS,
    create_subagent_models,
)

# Default middleware for every sub-agent: PatchToolCallsMiddleware
# normalises Gemini tool-call formatting. SummarizationMiddleware is
# unnecessary because sub-agent contexts are ephemeral (one task call).
_SUBAGENT_MIDDLEWARE = [PatchToolCallsMiddleware()]

# Sub-agents that produce brand-strategy artifacts also receive
# WorkspaceInjectionMiddleware so brand_brief.md and quality_gates.md
# arrive in their first turn regardless of how thin the orchestrator's
# dispatch description ended up. market-research and social-media-analyst
# operate on web data, not workspace state, so they keep the lean
# default chain.
_ARTIFACT_SUBAGENT_MIDDLEWARE = [
    *_SUBAGENT_MIDDLEWARE,
    WorkspaceInjectionMiddleware(),
]


def _resolve_tools(
    tool_names: list[str],
    tools_registry: dict[str, BaseTool],
) -> list[BaseTool]:
    """Resolve tool name strings to actual tool instances.

    Args:
        tool_names: List of tool names (e.g. ["search_web", "scrape_web_content"])
        tools_registry: Mapping of tool name to tool instance

    Returns:
        List of resolved tool instances (skips missing tools with warning).
    """
    resolved: list[BaseTool] = []
    for name in tool_names:
        if name in tools_registry:
            resolved.append(tools_registry[name])
        else:
            logger.warning(f"Tool '{name}' not found in registry, skipping")
    return resolved


def create_brand_strategy_subagent_middleware(
    tools_registry: dict[str, BaseTool],
) -> SubAgentMiddleware:
    """Create SubAgentMiddleware with 4 named brand strategy sub-agents.

    Each sub-agent has its own name, description, system prompt, model
    instance (RetryChatGoogleGenerativeAI), and tool set. The main
    agent LLM naturally selects which sub-agent to delegate to via
    the task() tool based on name/description.

    Args:
        tools_registry: Mapping of tool name to tool instance.
            Built in the agent factory (task_46) as:
            ``{tool.name: tool for tool in all_tools}``

    Returns:
        Configured SubAgentMiddleware ready for agent middleware stack.
    """
    models = create_subagent_models()

    subagents: list[dict[str, Any]] = [
        {
            "name": "market-research",
            "description": (
                "Researches markets, competitors, audiences, and category "
                "trends using web tools, knowledge graph, and document "
                "library. Dispatch only when the user explicitly asks for "
                "fresh external research, or when one critical missing fact "
                "would change the strategy and cannot be resolved from the "
                "conversation or KG. Don't dispatch when the user has already "
                "provided competitor context and asks to search only if truly "
                "needed; synthesize that context in the main agent and name "
                "any evidence gaps instead. Don't dispatch for visual asset "
                "generation (creative-studio), deliverable assembly "
                "(document-generator), or strategy analysis already grounded "
                "in the conversation."
            ),
            "system_prompt": MARKET_RESEARCH_SYSTEM_PROMPT,
            "model": models["market-research"],
            "tools": _resolve_tools(MARKET_RESEARCH_TOOLS, tools_registry),
            "middleware": _SUBAGENT_MIDDLEWARE,
        },
        {
            "name": "social-media-analyst",
            "description": (
                "Audits F&B brand presence on Instagram, Facebook, and TikTok "
                "at profile depth: follower mix, content cadence, brand-voice "
                "tone, hashtag patterns. Dispatch for a focused look at one "
                "specific competitor's social account or the user's own pages. "
                "Don't dispatch for broad multi-channel competitive research "
                "(market-research has wider scope), or for generating new "
                "social content (creative-studio for visuals)."
            ),
            "system_prompt": SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT,
            "model": models["social-media-analyst"],
            "tools": _resolve_tools(SOCIAL_MEDIA_TOOLS, tools_registry),
            "middleware": _SUBAGENT_MIDDLEWARE,
        },
        {
            "name": "creative-studio",
            "description": (
                "Compiles brand visuals from finalized strategy data. Primary "
                "deliverable: the Brand Key one-pager visual via "
                "`generate_brand_key` — dispatch when Phase 5 closes and the "
                "orchestrator has the 9-component Brand Key text ready. Also "
                "produces exploratory mood boards, logo concept directions, "
                "and color-palette visualizations via `generate_image` / "
                "`edit_image` for early-phase brainstorming. Don't dispatch "
                "for document, presentation, or spreadsheet generation "
                "(document-generator), or for research / analysis tasks."
            ),
            "system_prompt": CREATIVE_STUDIO_SYSTEM_PROMPT,
            "model": models["creative-studio"],
            "tools": _resolve_tools(CREATIVE_STUDIO_TOOLS, tools_registry),
            "middleware": _ARTIFACT_SUBAGENT_MIDDLEWARE,
        },
        {
            "name": "document-generator",
            "description": (
                "Compiles brand strategy data into editable deliverables: "
                "PDF / DOCX strategy documents via `generate_document`, PPTX "
                "executive decks via `generate_presentation`, and XLSX "
                "tracking spreadsheets via `generate_spreadsheet`. Dispatch "
                "at Phase 5 closure when the orchestrator has the finalized "
                "phase-by-phase strategy content ready for the boss meeting. "
                "Don't dispatch for the Brand Key one-pager visual (that's "
                "creative-studio's `generate_brand_key`), for image work, or "
                "for fresh research."
            ),
            "system_prompt": DOCUMENT_GENERATOR_SYSTEM_PROMPT,
            "model": models["document-generator"],
            "tools": _resolve_tools(DOCUMENT_GENERATOR_TOOLS, tools_registry),
            "middleware": _ARTIFACT_SUBAGENT_MIDDLEWARE,
        },
    ]

    # BackendFactory: StateBackend for ephemeral sub-agent state.
    # The factory receives ToolRuntime at agent build time.
    # The task() tool parameter for selecting a sub-agent is
    # `subagent_type` (e.g., task(description="...", subagent_type="market-research"))
    def _backend_factory(runtime: ToolRuntime) -> StateBackend:
        return StateBackend(runtime)

    return SubAgentMiddleware(
        backend=_backend_factory,
        subagents=subagents,  # type: ignore[arg-type]
    )
