"""End-to-end integration tests for Brand Strategy workflow (Task 46).

These tests require external services (Gemini API, FalkorDB, Milvus)
and verify the full agent pipeline:
1. Agent creation with all tools + middlewares
2. Phase 0 interview response
3. Rebrand scenario recognition
4. All tools registered on the agent

NOTE: Tests that call agent.ainvoke() require a valid GEMINI_API_KEY
and running database services. Mark with @pytest.mark.e2e for CI
to skip when services are unavailable.
"""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from core.brand_strategy.agent_config import (
    create_brand_strategy_agent,
)


def _get_tool_names(agent) -> list[str]:
    """Extract tool names from a CompiledStateGraph agent.

    CompiledStateGraph (from create_agent) stores tools in the 'tools'
    node as a ToolNode. Access via: agent.nodes['tools'].bound.tools_by_name
    """
    tools_node = agent.nodes.get("tools")
    if tools_node and hasattr(tools_node, "bound"):
        tool_node = tools_node.bound
        if hasattr(tool_node, "tools_by_name"):
            return list(tool_node.tools_by_name.keys())
    return []


@pytest.fixture
def brand_strategy_agent():
    """Create a brand strategy agent for testing."""
    return create_brand_strategy_agent()


class TestAgentCreation:
    """Test agent factory creates a working agent."""

    def test_agent_exposes_orchestrator_tools(self, brand_strategy_agent):
        """Verify the main agent exposes only orchestrator-owned tools."""
        tool_names = _get_tool_names(brand_strategy_agent)

        expected_tools = [
            "search_knowledge_graph",
            "search_document_library",
            "generate_image",
            "edit_image",
            "export_to_markdown",
            "list_artifacts",
            "report_progress",
        ]
        for tool_name in expected_tools:
            assert tool_name in tool_names, f"Missing tool: {tool_name}"

    def test_external_research_tools_are_specialist_owned(
        self, brand_strategy_agent
    ):
        """Verify web/social research cannot run directly from the main agent."""
        tool_names = _get_tool_names(brand_strategy_agent)

        specialist_tools = [
            "search_web",
            "scrape_web_content",
            "browse_and_research",
            "deep_research",
            "analyze_social_profile",
            "get_search_autocomplete",
        ]
        for tool_name in specialist_tools:
            assert tool_name not in tool_names, f"Direct research tool leaked: {tool_name}"

    def test_agent_does_not_use_tool_inventory_runtime(self, brand_strategy_agent):
        """Verify Brand Strategy exposes main-owned tools directly."""
        tool_names = _get_tool_names(brand_strategy_agent)
        for meta_tool in ["tool_search", "load_tools", "unload_tools"]:
            assert meta_tool not in tool_names, f"Unexpected inventory tool: {meta_tool}"

    def test_agent_has_subagent_task_tool(self, brand_strategy_agent):
        """Verify the 'task' tool (from SubAgentMiddleware) is registered."""
        tool_names = _get_tool_names(brand_strategy_agent)
        assert "task" in tool_names, "Missing 'task' subagent tool"

    def test_agent_has_todo_tool(self, brand_strategy_agent):
        """Verify write_todos tool (from TodoWriteMiddleware) is registered."""
        tool_names = _get_tool_names(brand_strategy_agent)
        assert "write_todos" in tool_names, "Missing 'write_todos' tool"

    def test_agent_total_tool_count(self, brand_strategy_agent):
        """Verify the narrowed orchestrator tool surface remains complete."""
        tool_names = _get_tool_names(brand_strategy_agent)
        # 7 orchestrator-owned tools + task + write_todos + deepagent
        # filesystem tools, without the ToolSearch inventory triad.
        assert len(tool_names) >= 15, (
            f"Expected at least 15 tools, got {len(tool_names)}: {tool_names}"
        )


class TestNewBrandE2E:
    """E2E tests for new brand creation scenario.

    Requires GEMINI_API_KEY and database services.
    """

    @pytest.mark.asyncio
    async def test_phase_0_interview(self, brand_strategy_agent):
        """Phase 0: Agent should ask structured questions."""
        result = await brand_strategy_agent.ainvoke(
            {
                "messages": [
                    HumanMessage(
                        content=(
                            "Tôi muốn xây dựng thương hiệu "
                            "cho quán café specialty mới "
                            "ở Quận 3, TPHCM"
                        )
                    )
                ]
            },
            {"recursion_limit": 100},
        )
        response = _get_response(result)
        assert response is not None
        assert len(response) > 100


class TestRebrandE2E:
    """E2E tests for rebrand scenario.

    Requires GEMINI_API_KEY and database services.
    """

    @pytest.mark.asyncio
    async def test_rebrand_scenario(self, brand_strategy_agent):
        """Rebrand context should trigger appropriate response."""
        messages = [
            HumanMessage(
                content=(
                    "Quán café của tôi đã hoạt động 5 năm "
                    "nhưng doanh thu giảm, brand cũ không "
                    "còn phù hợp. Tôi muốn làm mới "
                    "thương hiệu."
                )
            ),
        ]
        result = await brand_strategy_agent.ainvoke(
            {"messages": messages},
            {"recursion_limit": 100},
        )
        response = _get_response(result)
        assert response is not None


def _get_response(result: dict) -> str | None:
    """Extract text response from agent result."""
    if "messages" in result and result["messages"]:
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content:
                if isinstance(msg.content, str):
                    return msg.content
                if isinstance(msg.content, list):
                    parts = [
                        p.get("text", "")
                        for p in msg.content
                        if isinstance(p, dict)
                        and p.get("type") == "text"
                    ]
                    return "\n".join(parts)
    return None
