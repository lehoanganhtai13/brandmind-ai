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

from .configs import (
    CREATIVE_STUDIO_TOOLS,
    DOCUMENT_GENERATOR_TOOLS,
    MARKET_RESEARCH_TOOLS,
    SOCIAL_MEDIA_TOOLS,
    create_subagent_models,
)

# Each sub-agent gets PatchToolCallsMiddleware to fix Gemini tool call
# format issues. SummarizationMiddleware is NOT needed since sub-agents
# are ephemeral (context resets per task delegation).
_SUBAGENT_MIDDLEWARE = [PatchToolCallsMiddleware()]


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
                "Research agent for competitor analysis, local market mapping, "
                "deep market research, review sentiment analysis, and search "
                "trend discovery. Use for data-heavy research tasks requiring "
                "multiple tool calls."
            ),
            "system_prompt": MARKET_RESEARCH_SYSTEM_PROMPT,
            "model": models["market-research"],
            "tools": _resolve_tools(MARKET_RESEARCH_TOOLS, tools_registry),
            "middleware": _SUBAGENT_MIDDLEWARE,
        },
        {
            "name": "social-media-analyst",
            "description": (
                "Analyzes F&B brand social media presence on Instagram, "
                "Facebook, TikTok. Performs profile analysis, content audits, "
                "brand voice assessment, and competitive social benchmarking."
            ),
            "system_prompt": SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT,
            "model": models["social-media-analyst"],
            "tools": _resolve_tools(SOCIAL_MEDIA_TOOLS, tools_registry),
            "middleware": _SUBAGENT_MIDDLEWARE,
        },
        {
            "name": "creative-studio",
            "description": (
                "Generates brand visual assets — mood boards, logo concept "
                "directions, color palette visualizations, packaging mockups, "
                "and Brand Key one-pager visuals. Images are direction drafts."
            ),
            "system_prompt": CREATIVE_STUDIO_SYSTEM_PROMPT,
            "model": models["creative-studio"],
            "tools": _resolve_tools(CREATIVE_STUDIO_TOOLS, tools_registry),
            "middleware": _SUBAGENT_MIDDLEWARE,
        },
        {
            "name": "document-generator",
            "description": (
                "Compiles brand strategy data into professional deliverables: "
                "PDF/DOCX strategy documents, PPTX pitch decks, XLSX spreadsheets, "
                "Markdown exports, and Brand Key one-pager compilation."
            ),
            "system_prompt": DOCUMENT_GENERATOR_SYSTEM_PROMPT,
            "model": models["document-generator"],
            "tools": _resolve_tools(DOCUMENT_GENERATOR_TOOLS, tools_registry),
            "middleware": _SUBAGENT_MIDDLEWARE,
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
