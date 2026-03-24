"""Tool registry for dynamic tool loading.

Stores metadata for all loadable tools and provides keyword-based search
with scoring. Designed for small catalogs (10-50 tools) where in-memory
keyword matching is faster than embedding-based search.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolMetadata:
    """Immutable metadata for a tool in the registry.

    Attributes:
        name: Tool function name (must match LangChain tool name exactly).
        description: Human-readable description shown in search results.
        category: Logical grouping (e.g., "image_generation", "document_export").
        keywords: Search terms for discovery (converted to tuple for immutability).
        phases: Workflow phases where this tool is typically used.
    """

    name: str
    description: str
    category: str
    keywords: tuple[str, ...] = ()
    phases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Coerce lists to tuples for true immutability."""
        if isinstance(self.keywords, list):
            object.__setattr__(self, "keywords", tuple(self.keywords))
        if isinstance(self.phases, list):
            object.__setattr__(self, "phases", tuple(self.phases))


class ToolRegistry:
    """Registry for loadable tools with keyword-based search.

    Stores tools grouped by category. Search uses multi-signal scoring:
    - Exact name match: +10 points
    - Name contains query word: +5 points
    - Description contains query word: +3 points
    - Category contains query word: +4 points
    - Keyword exact match: +6 points
    - Keyword contains query word: +2 points

    Designed for small catalogs (10-50 tools). For larger catalogs,
    consider upgrading to embedding-based search.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._tools: dict[str, ToolMetadata] = {}
        self._categories: dict[str, list[str]] = {}

    def register(self, metadata: ToolMetadata) -> None:
        """Register a tool in the registry.

        Args:
            metadata: Tool metadata to register.

        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        if metadata.name in self._tools:
            raise ValueError(
                f"Tool '{metadata.name}' already registered. "
                f"Use update() to modify existing entries."
            )
        self._tools[metadata.name] = metadata

        # Index by category
        if metadata.category not in self._categories:
            self._categories[metadata.category] = []
        self._categories[metadata.category].append(metadata.name)

    def register_many(self, metadata_list: list[ToolMetadata]) -> None:
        """Register multiple tools at once.

        Args:
            metadata_list: List of tool metadata to register.
        """
        for metadata in metadata_list:
            self.register(metadata)

    def search(self, query: str, top_k: int = 5) -> list[ToolMetadata]:
        """Search tools by natural language query with relevance scoring.

        Args:
            query: Search query (e.g., "generate image", "social media analysis").
            top_k: Maximum results to return.

        Returns:
            List of ToolMetadata sorted by relevance, up to top_k items.
        """
        if not query or not query.strip():
            return []

        query_words = query.lower().split()
        scored_results: list[tuple[int, ToolMetadata]] = []

        for meta in self._tools.values():
            score = self._score_tool(meta, query_words)
            if score > 0:
                scored_results.append((score, meta))

        # Sort by score descending, then by name for stable ordering
        scored_results.sort(key=lambda x: (-x[0], x[1].name))
        return [meta for _, meta in scored_results[:top_k]]

    def get_tools_in_category(self, category: str) -> list[ToolMetadata]:
        """Get all tools in a category.

        Args:
            category: Category name to look up.

        Returns:
            List of ToolMetadata in the category, or empty list if not found.
        """
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def get_category_for_tool(self, tool_name: str) -> str | None:
        """Get the category for a tool.

        Args:
            tool_name: Tool name to look up.

        Returns:
            Category name, or None if tool not found.
        """
        meta = self._tools.get(tool_name)
        return meta.category if meta else None

    def get_all_tool_names_in_category(self, category: str) -> set[str]:
        """Get all tool names in a category as a set.

        Args:
            category: Category name to look up.

        Returns:
            Set of tool names in the category.
        """
        return set(self._categories.get(category, []))

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool exists in the registry.

        Args:
            tool_name: Tool name to check.

        Returns:
            True if the tool is registered, False otherwise.
        """
        return tool_name in self._tools

    def get_category_names(self) -> list[str]:
        """Get sorted list of all category names.

        Returns:
            Sorted list of category name strings.
        """
        return sorted(self._categories.keys())

    def get_summary(self) -> str:
        """Generate compact catalog summary for system prompt injection.

        The summary is kept under ~500 tokens to minimize context usage.
        Format: one line per category with tool names listed.

        Returns:
            Markdown-formatted summary string.
        """
        lines: list[str] = []
        for category, tool_names in sorted(self._categories.items()):
            tools = [self._tools[n] for n in tool_names if n in self._tools]
            if not tools:
                continue
            tool_list = ", ".join(t.name for t in tools)
            count = len(tools)
            category_label = category.replace("_", " ").title()
            lines.append(
                f"- **{category_label}** ({count} tool{'s' if count > 1 else ''}): "
                f"{tool_list}"
            )
        return "\n".join(lines)

    @staticmethod
    def _score_tool(meta: ToolMetadata, query_words: list[str]) -> int:
        """Score a tool against lowercased query words.

        Args:
            meta: Tool metadata to score.
            query_words: Lowercased query words to match against.

        Returns:
            Integer score (0 means no match).
        """
        score = 0
        name_lower = meta.name.lower()
        desc_lower = meta.description.lower()
        cat_lower = meta.category.lower()
        keywords_lower = [kw.lower() for kw in meta.keywords]

        for word in query_words:
            # Exact name match (full query word matches tool name)
            if word == name_lower:
                score += 10
            elif word in name_lower:
                score += 5

            # Description match
            if word in desc_lower:
                score += 3

            # Category match
            if word in cat_lower:
                score += 4

            # Keyword matching
            for kw in keywords_lower:
                if word == kw:
                    score += 6
                elif word in kw or kw in word:
                    score += 2

        return score
