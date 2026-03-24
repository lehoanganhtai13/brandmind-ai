"""ToolSearch middleware — dynamic tool loading for LangChain agents.

Provides tool_search/load_tools/unload_tools inventory pattern.
Blacklist approach: catalog tools hidden until loaded, all others visible.
Place BEFORE SkillsMiddleware in the middleware chain.

Architecture:
    The middleware intercepts load_tools and unload_tools calls entirely
    in wrap_tool_call (the tool functions are never executed). This avoids
    ToolRuntime schema issues and keeps state mutation in one place.
    tool_search passes through to the tool function normally.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
    ToolCallRequest,
)
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command
from loguru import logger

from .registry import ToolMetadata, ToolRegistry

# Module-level registry — set once by factory function.
# Tool functions read this; it's immutable config after init.
_registry: ToolRegistry | None = None


# ---------------------------------------------------------------------------
# 3 Inventory Tools (schemas for the LLM)
# ---------------------------------------------------------------------------


@tool
def tool_search(query: str) -> str:
    """Search the tool warehouse for specialized capabilities.

    You start with core tools only. This BROWSES the catalog (does NOT load).
    After reviewing results, use load_tools() to equip what you need.

    Searchable: image generation, document creation (PDF/DOCX/PPTX/XLSX),
    local market (Google Places), social media analysis, customer reviews.

    Args:
        query: Capability description. Examples: "generate image",
              "social media analysis", "create PDF document"
    """
    if _registry is None:
        return "Tool registry not initialized. Contact system administrator."

    results = _registry.search(query, top_k=8)

    if not results:
        return (
            f"No matching tools found for '{query}'. "
            f"Try different search terms. Available categories: "
            f"{', '.join(_registry.get_category_names())}"
        )

    lines = [f"Found {len(results)} tool(s) matching '{query}':\n"]
    seen_categories: set[str] = set()

    for meta in results:
        lines.append(f"**{meta.name}**")
        lines.append(f"  Category: {meta.category}")
        lines.append(f"  Description: {meta.description}")
        if meta.phases:
            lines.append(f"  Typical phases: {', '.join(meta.phases)}")
        lines.append("")
        seen_categories.add(meta.category)

    # Show related tools in same categories that weren't in top results
    related: list[str] = []
    for cat in seen_categories:
        cat_tools = _registry.get_all_tool_names_in_category(cat)
        result_names = {m.name for m in results}
        additional = cat_tools - result_names
        if additional:
            related.extend(additional)

    if related:
        lines.append(f"Other tools in same categories: {', '.join(sorted(related))}")

    lines.append(
        "\nTo use these tools, call load_tools() with the tool names you need."
    )

    return "\n".join(lines)


@tool
def load_tools(tool_names: list[str]) -> str:
    """Load (equip) tools into your active set so you can use them.

    After tool_search(), call this with the tool names you want.
    Loaded tools appear in your tool list on the next action.

    Args:
        tool_names: Tool names from catalog. Example: ["generate_image"]
    """
    # This function body is never executed — wrap_tool_call intercepts it.
    # The schema is what matters for the LLM.
    return "Processing load request..."


@tool
def unload_tools(tool_names: list[str]) -> str:
    """Unload (unequip) tools from your active set to keep context lean.

    Call when done with tools. You can always load them again later.

    Args:
        tool_names: Tool names to unload. Example: ["generate_image"]
    """
    # This function body is never executed — wrap_tool_call intercepts it.
    return "Processing unload request..."


# ---------------------------------------------------------------------------
# ToolSearch State Schema
# ---------------------------------------------------------------------------


class ToolSearchState(AgentState):
    """Extended agent state with loaded tools tracking.

    Attributes:
        loaded_tools: Set of currently loaded tool names.
    """

    loaded_tools: set[str]


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class ToolSearchMiddleware(AgentMiddleware):
    """Filters tool visibility and manages load/unload state.

    Provides 3 inventory tools (tool_search, load_tools, unload_tools) and
    filters model context using a blacklist: catalog tools are hidden until
    loaded, all other tools are always visible.
    Place BEFORE SkillsMiddleware in the middleware chain.

    State management:
        - wrap_model_call: reads state["loaded_tools"] to filter visible tools
        - wrap_tool_call: intercepts load/unload calls to mutate state
        - tool_search: passes through to tool function (read-only)
    """

    # 3 inventory tools — always available to the agent
    tools = [tool_search, load_tools, unload_tools]

    state_schema = ToolSearchState

    def __init__(
        self,
        registry: ToolRegistry,
        catalog_names: set[str],
    ) -> None:
        """Initialize middleware.

        Args:
            registry: ToolRegistry with metadata for all loadable tools.
            catalog_names: Names of tools in the loadable catalog.
                These are hidden until loaded. All other tools are
                always visible.
        """
        super().__init__()
        self.registry = registry
        self._catalog_names = catalog_names

        # Set module-level registry for tool_search function
        global _registry
        _registry = registry

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Filter visible tools to core + loaded; inject catalog on first call.

        Args:
            request: Model request with all registered tools.
            handler: Next handler in the middleware chain.

        Returns:
            Model response from handler with filtered tools.
        """
        state = request.state
        loaded_names: set[str] = set(
            state.get("loaded_tools", set())  # type: ignore[call-overload]
        )

        # Filter tools: hide catalog tools unless loaded, show everything else
        visible_tools = [
            t
            for t in request.tools
            if getattr(t, "name", "") not in self._catalog_names
            or getattr(t, "name", "") in loaded_names
        ]

        # Inject tool catalog into system prompt on first call
        catalog_injected = bool(
            state.get("_tool_catalog_injected", False)  # type: ignore[call-overload]
        )

        if not catalog_injected:
            catalog_summary = self.registry.get_summary()
            addendum = (
                "\n\n## Tool Warehouse\n\n"
                "You currently see only core tools. Specialized tools are in "
                "the warehouse. Use the inventory workflow:\n"
                "1. `tool_search(query)` — browse catalog, find tools\n"
                "2. `load_tools([names])` — equip tools you need\n"
                "3. Use the loaded tools\n"
                "4. `unload_tools([names])` — unequip when done\n\n"
                f"Available in warehouse:\n{catalog_summary}\n"
            )

            current_prompt = request.system_prompt or ""
            new_prompt = current_prompt + addendum
            new_system = SystemMessage(content=new_prompt)

            state["_tool_catalog_injected"] = True  # type: ignore[typeddict-unknown-key]
            return handler(
                request.override(
                    system_message=new_system,
                    tools=visible_tools,
                )
            )

        return handler(request.override(tools=visible_tools))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """Async version of wrap_model_call.

        Args:
            request: Model request with all registered tools.
            handler: Next async handler in the middleware chain.

        Returns:
            Model response from handler with filtered tools.
        """
        state = request.state
        loaded_names: set[str] = set(
            state.get("loaded_tools", set())  # type: ignore[call-overload]
        )

        visible_tools = [
            t
            for t in request.tools
            if getattr(t, "name", "") not in self._catalog_names
            or getattr(t, "name", "") in loaded_names
        ]

        catalog_injected = bool(
            state.get("_tool_catalog_injected", False)  # type: ignore[call-overload]
        )

        if not catalog_injected:
            catalog_summary = self.registry.get_summary()
            addendum = (
                "\n\n## Tool Warehouse\n\n"
                "You currently see only core tools. Specialized tools are in "
                "the warehouse. Use the inventory workflow:\n"
                "1. `tool_search(query)` — browse catalog, find tools\n"
                "2. `load_tools([names])` — equip tools you need\n"
                "3. Use the loaded tools\n"
                "4. `unload_tools([names])` — unequip when done\n\n"
                f"Available in warehouse:\n{catalog_summary}\n"
            )

            current_prompt = request.system_prompt or ""
            new_prompt = current_prompt + addendum
            new_system = SystemMessage(content=new_prompt)

            state["_tool_catalog_injected"] = True  # type: ignore[typeddict-unknown-key]
            return await handler(
                request.override(
                    system_message=new_system,
                    tools=visible_tools,
                )
            )

        return await handler(request.override(tools=visible_tools))

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Intercept load/unload calls; pass everything else through.

        For load_tools and unload_tools: handles entirely in middleware
        (tool function is NOT executed). Reads and mutates state directly,
        then returns an informative ToolMessage.

        For tool_search and all other tools: passes through to handler.

        Args:
            request: Tool call request with tool_call dict and state.
            handler: Next handler (executes actual tool function).

        Returns:
            ToolMessage with result or Command for state update.
        """
        tool_name = request.tool_call["name"]

        if tool_name == "load_tools":
            return self._handle_load_tools(request)
        elif tool_name == "unload_tools":
            return self._handle_unload_tools(request)

        # tool_search and all other tools: pass through
        return handler(request)

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        """Async version of wrap_tool_call.

        Args:
            request: Tool call request with tool_call dict and state.
            handler: Next async handler.

        Returns:
            ToolMessage with result or Command for state update.
        """
        tool_name = request.tool_call["name"]

        if tool_name == "load_tools":
            return self._handle_load_tools(request)
        elif tool_name == "unload_tools":
            return self._handle_unload_tools(request)

        return await handler(request)

    def _handle_load_tools(self, request: ToolCallRequest) -> ToolMessage:
        """Handle load_tools call: validate, update state, return message.

        Args:
            request: Tool call request containing tool_names to load.

        Returns:
            ToolMessage with detailed load result.
        """
        names_to_load: list[str] = request.tool_call["args"].get("tool_names", [])
        loaded: set[str] = set(
            request.state.get("loaded_tools", set())  # type: ignore[call-overload]
        )

        newly_loaded: list[str] = []
        already_loaded: list[str] = []
        not_found: list[str] = []

        for name in names_to_load:
            if not self.registry.has_tool(name):
                not_found.append(name)
            elif name in loaded:
                already_loaded.append(name)
            else:
                newly_loaded.append(name)

        # Update state — only add names that exist in registry
        valid_names = {n for n in names_to_load if self.registry.has_tool(n)}
        request.state["loaded_tools"] = loaded | valid_names  # type: ignore[typeddict-unknown-key]

        # Build informative message
        parts: list[str] = []
        if newly_loaded:
            parts.append(
                f"Loaded {len(newly_loaded)} tool(s): {', '.join(newly_loaded)}"
            )
        if already_loaded:
            parts.append(f"Already loaded: {', '.join(already_loaded)}")
        if not_found:
            parts.append(
                f"Not found in catalog: {', '.join(not_found)}. "
                f"Use tool_search() to find valid tool names."
            )
        if newly_loaded:
            parts.append("These tools are now available for use.")

        msg = "\n".join(parts) if parts else "No tools specified."

        logger.debug(f"load_tools: {newly_loaded=}, {already_loaded=}, {not_found=}")

        return ToolMessage(content=msg, tool_call_id=request.tool_call["id"])

    def _handle_unload_tools(self, request: ToolCallRequest) -> ToolMessage:
        """Handle unload_tools call: validate, update state, return message.

        Args:
            request: Tool call request containing tool_names to unload.

        Returns:
            ToolMessage with detailed unload result.
        """
        names_to_unload: list[str] = request.tool_call["args"].get("tool_names", [])
        loaded: set[str] = set(
            request.state.get("loaded_tools", set())  # type: ignore[call-overload]
        )

        unloaded: list[str] = []
        not_loaded: list[str] = []

        for name in names_to_unload:
            if name in loaded:
                unloaded.append(name)
            else:
                not_loaded.append(name)

        # Update state — remove unloaded tools
        request.state["loaded_tools"] = loaded - set(names_to_unload)  # type: ignore[typeddict-unknown-key]

        # Build informative message
        parts: list[str] = []
        if unloaded:
            parts.append(f"Unloaded {len(unloaded)} tool(s): {', '.join(unloaded)}")
        if not_loaded:
            parts.append(f"Not currently loaded: {', '.join(not_loaded)}")
        if unloaded:
            parts.append("These tools are no longer in your active set.")

        msg = "\n".join(parts) if parts else "No tools specified."

        logger.debug(f"unload_tools: {unloaded=}, {not_loaded=}")

        return ToolMessage(content=msg, tool_call_id=request.tool_call["id"])


# ---------------------------------------------------------------------------
# Brand Strategy Tool Catalog
# ---------------------------------------------------------------------------

# Defines metadata for all loadable tools in the catalog.
# Core tools (search_knowledge_graph, search_document_library, search_web,
# scrape_web_content, deep_research) are NOT in this catalog — they are always visible.

BRAND_STRATEGY_TOOL_CATALOG: list[ToolMetadata] = [
    # ---- Category: social_media ----
    ToolMetadata(
        name="browse_and_research",
        description=(
            "Browse and research social media profiles using automated "
            "browser. Analyze competitor content strategy, engagement, "
            "and brand presence."
        ),
        category="social_media",
        keywords=(
            "instagram",
            "facebook",
            "tiktok",
            "social",
            "followers",
            "engagement",
            "content",
            "posts",
            "stories",
            "reels",
            "social media",
            "browse",
            "profile",
        ),
        phases=("0.5", "1", "3", "4"),
    ),
    ToolMetadata(
        name="analyze_social_profile",
        description=(
            "Analyze a social media profile's brand strategy — "
            "content themes, engagement patterns, posting frequency, "
            "audience."
        ),
        category="social_media",
        keywords=(
            "social profile",
            "brand analysis",
            "content strategy",
            "engagement rate",
            "social analysis",
            "competitor social",
        ),
        phases=("1",),
    ),
    # ---- Category: customer_analysis ----
    ToolMetadata(
        name="get_search_autocomplete",
        description=(
            "Get Google search autocomplete suggestions for keyword "
            "and topic research. Discover what consumers are searching "
            "for related to your brand/category."
        ),
        category="customer_analysis",
        keywords=(
            "autocomplete",
            "search trends",
            "keyword research",
            "google suggest",
            "consumer search",
            "search behavior",
        ),
        phases=("1", "4"),
    ),
    # ---- Category: image_generation ----
    ToolMetadata(
        name="generate_image",
        description=(
            "Generate visual brand assets using Gemini 3 Pro Image "
            "— mood boards, logo concepts, color palette "
            "visualizations, social media mockups. Returns the image "
            "visually for evaluation."
        ),
        category="image_generation",
        keywords=(
            "image",
            "visual",
            "mood board",
            "logo",
            "color palette",
            "design",
            "mockup",
            "brand visual",
            "illustration",
            "generate image",
            "create image",
        ),
        phases=("3", "5"),
    ),
    ToolMetadata(
        name="edit_image",
        description=(
            "Edit/refine an existing image with text instructions "
            "using Gemini 3 Pro Image — adjust colors, simplify "
            "designs, change style, add/remove elements. Send a "
            "previously generated image + edit prompt."
        ),
        category="image_generation",
        keywords=(
            "edit image",
            "refine",
            "adjust",
            "modify image",
            "change colors",
            "simplify",
            "redesign",
            "iterate",
            "image editing",
        ),
        phases=("3", "5"),
    ),
    ToolMetadata(
        name="generate_brand_key",
        description=(
            "Generate Brand Key one-pager visual — the summary "
            "infographic of the complete brand strategy (positioning, "
            "personality, values, target audience)."
        ),
        category="image_generation",
        keywords=(
            "brand key",
            "one-pager",
            "infographic",
            "brand summary",
            "visual summary",
            "brand key visual",
        ),
        phases=("5",),
    ),
    # ---- Category: document_export ----
    ToolMetadata(
        name="generate_document",
        description=(
            "Generate brand strategy documents in PDF or DOCX format. "
            "Professional formatting with cover page, table of "
            "contents, and sections."
        ),
        category="document_export",
        keywords=(
            "document",
            "PDF",
            "DOCX",
            "report",
            "strategy document",
            "brand book",
            "generate document",
            "create document",
        ),
        phases=("5",),
    ),
    ToolMetadata(
        name="generate_presentation",
        description=(
            "Generate brand strategy presentations in PPTX format. "
            "Executive pitch decks with branded slides."
        ),
        category="document_export",
        keywords=(
            "presentation",
            "PPTX",
            "PowerPoint",
            "pitch deck",
            "slides",
            "executive summary",
            "generate presentation",
        ),
        phases=("5",),
    ),
    ToolMetadata(
        name="generate_spreadsheet",
        description=(
            "Generate brand strategy spreadsheets in XLSX format — "
            "competitor analysis matrix, brand audit scorecard, "
            "content calendar, KPI dashboard, budget plan. "
            "Formula-driven with auto-calculations."
        ),
        category="document_export",
        keywords=(
            "spreadsheet",
            "XLSX",
            "Excel",
            "matrix",
            "scorecard",
            "calendar",
            "dashboard",
            "budget",
            "table",
            "data",
        ),
        phases=("5",),
    ),
    ToolMetadata(
        name="export_to_markdown",
        description=(
            "Export brand strategy content to well-formatted Markdown. "
            "Clean text export for documentation, README files, "
            "or wikis."
        ),
        category="document_export",
        keywords=(
            "markdown",
            "export",
            "text",
            "format",
            "documentation",
            "MD",
            "plain text",
        ),
        phases=("0", "1", "2", "3", "4", "5"),
    ),
]


# ---------------------------------------------------------------------------
# Factory Function
# ---------------------------------------------------------------------------


def create_tool_search_middleware(
    all_tools: list | None = None,
    tool_catalog: list[ToolMetadata] | None = None,
) -> ToolSearchMiddleware:
    """Build ToolRegistry from catalog and return configured middleware.

    Args:
        all_tools: All tool instances for validation. None skips validation.
        tool_catalog: Loadable tool metadata. Defaults to
            BRAND_STRATEGY_TOOL_CATALOG.

    Returns:
        Configured ToolSearchMiddleware for the middleware chain.
    """
    catalog = tool_catalog or BRAND_STRATEGY_TOOL_CATALOG
    catalog_names = {meta.name for meta in catalog}

    # Build registry from catalog
    registry = ToolRegistry()
    registry.register_many(catalog)

    # Validate: check that catalog tool names exist in all_tools
    if all_tools is not None:
        actual_names = {
            getattr(t, "name", None) or getattr(t, "__name__", str(t))
            for t in all_tools
        }
        missing = catalog_names - actual_names
        if missing:
            logger.warning(
                f"ToolSearch catalog references tools not in all_tools: "
                f"{missing}. These tools will appear in search results "
                f"but won't be executable until registered."
            )

    logger.info(
        f"ToolSearchMiddleware initialized: "
        f"blacklist={len(catalog_names)} catalog tools hidden until loaded, "
        f"3 inventory tools (tool_search, load_tools, unload_tools), "
        f"{len(catalog)} loadable tools in "
        f"{len(registry._categories)} categories"
    )

    return ToolSearchMiddleware(
        registry=registry,
        catalog_names=catalog_names,
    )
