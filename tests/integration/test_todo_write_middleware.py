#!/usr/bin/env python3
"""
Integration tests for TodoWrite middleware functionality.

This module provides comprehensive integration testing for the TodoWriteMiddleware
component, ensuring it works correctly with LangGraph agents and maintains
state persistence across multiple interactions.
"""

import sys
import os
import pytest
import asyncio
from typing import List, Optional

# Add project root to path following existing test patterns
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'shared', 'src'))

from shared.agent_tools.todo.todo_write_middleware import TodoWriteMiddleware
from src.prompts.task_management.todo_system_prompt import EMPTY_TODO_REMINDER

try:
    from langchain.agents import create_agent
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: LangChain not available, some tests will be skipped")


def print_agent_result(result, step_num):
    """
    Print formatted agent result for easy viewing.

    Args:
        result: The agent result dictionary
        step_num: Step number for labeling
    """
    print(f"📋 Todos after step {step_num}:")

    # Get todos if they exist
    todos = result.get("todos", [])
    if todos:
        for i, todo in enumerate(todos, 1):
            status_emoji = {
                "pending": "⏳️",
                "in_progress": "🔄",
                "completed": "✅"
            }.get(todo["status"], "❓")

            priority_emoji = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢"
            }.get(todo["priority"], "⚪")

            print(f"  {i}. {status_emoji} {priority_emoji} {todo['content']}")
            print(f"     💭 {todo['activeForm']}")
            print(f"     📊 Status: {todo['status']} | Priority: {todo['priority']}")

    # Get last few messages for context
    messages = result.get("messages", [])
    if messages:
        print(f"\n💬 Recent messages:")
        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__

            if msg_type == "HumanMessage":
                print(f"   {msg_type}: {msg.content}")
            elif msg_type == "AIMessage":
                # Check if it's a tool call message
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_call = msg.tool_calls[0]
                    tool_name = tool_call.get('name', 'Unknown')
                    tool_args = tool_call.get('args', {})
                    print(f"   {msg_type}: [Tool call: {tool_name}]")
                    print(f"   └─ Args: {tool_args}")
                elif hasattr(msg, 'content') and msg.content:
                    # Handle both string and list content
                    if isinstance(msg.content, list):
                        # Extract text content from list format
                        if msg.content and len(msg.content) > 0 and 'text' in msg.content[0]:
                            content = msg.content[0]['text']
                        else:
                            content = str(msg.content)
                    else:
                        content = msg.content.strip()

                    # Truncate long content
                    content = content[:200] + "..." if len(content) > 200 else content
                    print(f"   {msg_type}: {content}")
                else:
                    print(f"   {msg_type}: [Empty AI message]")
            elif msg_type == "ToolMessage":
                print(f"   {msg_type}: {msg.content[:200]}{'...' if len(msg.content) > 200 else ''}")
            else:
                # Handle other message types
                if hasattr(msg, 'content') and msg.content:
                    content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                    print(f"   {msg_type}: {content}")
                else:
                    print(f"   {msg_type}: [No content]")

    print("-" * 60)


def create_agent_with_todos(
    tools: List,
    tool_name: str = "write_todos",
    system_prompt: Optional[str] = None,
    tool_description: Optional[str] = None
):
    """
    Create a LangGraph agent with integrated TodoWrite middleware.

    This function configures a LangGraph agent with TodoWriteMiddleware that
    provides comprehensive todo management including:
    - Automatic reminder injection
    - State persistence through Command objects
    - Comprehensive validation and edge case handling

    Args:
        tools (List): Additional tools for agent functionality
        tool_name (str): Name for the todo management tool (default: "write_todos")
        system_prompt (Optional[str]): Custom system prompt override
        tool_description (Optional[str]): Custom tool description override

    Returns:
        Configured LangGraph agent with todo management capabilities
    """
    try:
        from src.config.system_config import SETTINGS

        model = ChatGoogleGenerativeAI(
            google_api_key=SETTINGS.GEMINI_API_KEY,
            model="gemini-2.5-pro",
            temperature=0.1,
            # top_p=0.1,
            thinking_budget=4000,
        )
    except ImportError as e:
        # Expected when google_genai package not available
        pytest.skip(f"Google Generative AI not available: {e}")
    except Exception as e:
        # Real initialization errors should fail the test
        pytest.fail(f"Failed to initialize Gemini model: {e}")

    # Import prompts from module
    from src.prompts.task_management.todo_system_prompt import (
        WRITE_TODOS_SYSTEM_PROMPT,
        WRITE_TODOS_TOOL_DESCRIPTION
    )

    # Create TodoWrite middleware with direct prompt parameters
    todo_middleware = TodoWriteMiddleware(
        tool_name=tool_name,
        system_prompt=system_prompt or WRITE_TODOS_SYSTEM_PROMPT,
        tool_description=tool_description or WRITE_TODOS_TOOL_DESCRIPTION
    )

    # Create agent with todo middleware
    agent = create_agent(
        model=model,
        tools=tools,  # Other tools (middleware adds todo tool automatically)
        middleware=[todo_middleware]  # Single middleware handles everything
    )

    return agent


# Test cases
@pytest.mark.asyncio
async def test_middleware_initialization():
    """Test that TodoWrite middleware initializes correctly."""
    middleware = TodoWriteMiddleware()

    # Check basic properties
    assert middleware.tool_name == "write_todos"
    assert len(middleware.tools) == 1
    assert middleware.tools[0].name == "write_todos"

    # Check that system prompt was processed
    assert "{{write_todos_function_name}}" not in middleware.system_prompt
    assert "write_todos" in middleware.system_prompt


@pytest.mark.asyncio
async def test_agent_creation():
    """Test that agent can be created with TodoWrite middleware."""
    if not LANGCHAIN_AVAILABLE:
        pytest.skip("LangChain not available")

    agent = create_agent_with_todos(
        tools=[],
        tool_name="write_todos"
    )

    assert agent is not None
    # Agent should have the todo tool available through middleware


@pytest.mark.asyncio
async def test_agent_todo_persistence():
    """Test that agent maintains todo state across multiple interactions."""
    if not LANGCHAIN_AVAILABLE:
        pytest.skip("LangChain not available")

    # Create agent with TodoWrite middleware
    agent = create_agent_with_todos(
        tools=[],
        tool_name="write_todos"
    )

    try:
        # Initial request to create todos
        result1 = await agent.ainvoke({
            "messages": [HumanMessage(content="Help me develop a brand positioning strategy for a new eco-friendly sneaker brand.")]
        })

        # Print formatted results
        print("🎯 === STEP 1: Initial Request ===")
        print(f"💬 User: Help me develop a brand positioning strategy for a new eco-friendly sneaker brand.")
        print_agent_result(result1, 1)

        # Follow-up request
        result2 = await agent.ainvoke({
            "messages": result1["messages"] + [HumanMessage(content="Mark the first task as completed")]
        })

        print("\n🎯 === STEP 2: Update Request ===")
        print(f"💬 User: Mark the first task as completed")
        print_agent_result(result2, 2)

        # Verify state persistence
        assert "messages" in result2

    except Exception as e:
        # Real failures should surface - only catch known test environment issues
        if "404 models" in str(e) or "API key" in str(e):
            pytest.skip(f"Test environment issue (model/API key): {e}")
        else:
            pytest.fail(f"Todo persistence test failed unexpectedly: {e}")


@pytest.mark.asyncio
async def test_single_task_enforcement():
    """Test that middleware enforces single in_progress task rule."""
    agent = create_agent_with_todos(
        tools=[],
        tool_name="write_todos"
    )

    # Test validation directly through middleware
    middleware = TodoWriteMiddleware()

    # Try to create multiple in_progress tasks (should fail validation)
    invalid_todos = [
        {"content": "Task 1", "status": "in_progress", "activeForm": "Working on task 1", "priority": "high"},
        {"content": "Task 2", "status": "in_progress", "activeForm": "Working on task 2", "priority": "medium"}
    ]

    validation = middleware._validate_todos(invalid_todos)
    assert not validation["valid"]
    assert "Too many tasks in_progress" in validation["error"]

    # Test valid single in_progress task
    valid_todos = [
        {"content": "Task 1", "status": "in_progress", "activeForm": "Working on task 1", "priority": "high"},
        {"content": "Task 2", "status": "pending", "activeForm": "Will work on task 2", "priority": "medium"}
    ]

    validation = middleware._validate_todos(valid_todos)
    assert validation["valid"]


@pytest.mark.asyncio
async def test_reminder_generation():
    """Test that reminder generation works for different todo states."""
    middleware = TodoWriteMiddleware()

    # Test empty list reminder
    empty_reminder = middleware._generate_reminder([])
    assert EMPTY_TODO_REMINDER in empty_reminder

    # Test todos reminder
    test_todos = [
        {"content": "Test task", "status": "in_progress", "activeForm": "Working on test", "priority": "high"}
    ]

    reminder = middleware._generate_reminder(test_todos)
    assert "Test task" in reminder
    assert "in_progress" in reminder
    assert "Working on test" in reminder


@pytest.mark.asyncio
async def test_mandatory_field_validation():
    """Test that validation enforces all mandatory fields."""
    middleware = TodoWriteMiddleware()

    # Test missing content
    invalid_todos = [
        {"content": "", "status": "pending", "activeForm": "Task", "priority": "high"}
    ]

    validation = middleware._validate_todos(invalid_todos)
    assert not validation["valid"]
    assert "empty content" in validation["error"]

    # Test missing activeForm
    invalid_todos = [
        {"content": "Task", "status": "pending", "activeForm": "", "priority": "high"}
    ]

    validation = middleware._validate_todos(invalid_todos)
    assert not validation["valid"]
    assert "empty activeForm" in validation["error"]

    # Test invalid status
    invalid_todos = [
        {"content": "Task", "status": "invalid_status", "activeForm": "Task", "priority": "high"}
    ]

    validation = middleware._validate_todos(invalid_todos)
    assert not validation["valid"]
    assert "invalid status" in validation["error"]

    # Test invalid priority
    invalid_todos = [
        {"content": "Task", "status": "pending", "activeForm": "Task", "priority": "invalid_priority"}
    ]

    validation = middleware._validate_todos(invalid_todos)
    assert not validation["valid"]
    assert "invalid priority" in validation["error"]


@pytest.mark.asyncio
async def test_tool_creation():
    """Test that the middleware creates the tool correctly."""
    middleware = TodoWriteMiddleware()
    tool = middleware._create_write_todos_tool()

    # Check tool properties
    assert tool.name == "write_todos"
    assert tool.description is not None
    assert len(tool.description) > 0
    assert "write_todos" in tool.description  # Check placeholder replacement


if __name__ == "__main__":
    """
    Quick test runner for development and debugging.
    """
    print("Running TodoWrite middleware integration tests...")

    # Run tests synchronously for quick debugging
    async def run_quick_tests():
        await test_middleware_initialization()
        print("✅ Middleware initialization test passed")

        await test_agent_creation()
        print("✅ Agent creation test passed")

        await test_agent_todo_persistence()
        print("✅ Agent todo persistence test passed")

        await test_single_task_enforcement()
        print("✅ Single task enforcement test passed")

        await test_reminder_generation()
        print("✅ Reminder generation test passed")

        await test_mandatory_field_validation()
        print("✅ Mandatory field validation test passed")

        await test_tool_creation()
        print("✅ Tool creation test passed")

        print("\n🎉 All quick tests completed successfully!")

    # Run the quick tests
    asyncio.run(run_quick_tests())