#!/usr/bin/env python3
"""
Deep Agent Demo

This demo creates a custom deep agent using:
- Gemini 2.5 Flash Lite model with thinking/reasoning output
- Custom tools: search_web, scrape_web_content
- DeepAgent middlewares: FilesystemMiddleware, SubAgentMiddleware, PatchToolCallsMiddleware
- TodoWriteMiddleware for task management

Location: docs/langchain/examples/deep_agent_demo.py
See also: docs/langchain/langchain_deep_agent.md
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project paths
# This file is at: /Users/mac/projects/brandmind-ai/docs/langchain/examples/deep_agent_demo.py
# So project_root is 3 levels up
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "src" / "shared" / "src"))
sys.path.append(str(project_root / "src" / "config"))

from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

from config.system_config import SETTINGS
from shared.agent_tools import TodoWriteMiddleware, search_web, scrape_web_content

# Import DeepAgent components
try:
    from deepagents.backends import FilesystemBackend
    from deepagents.middleware.filesystem import FilesystemMiddleware
    from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
    from deepagents.middleware.subagents import SubAgentMiddleware
except ImportError as e:
    logger.error(f"Failed to import DeepAgent components: {e}")
    logger.error("Please ensure deepagents is installed: pip install deepagents")
    sys.exit(1)


def create_custom_deep_agent():
    """
    Create a custom deep agent with Gemini model and various middlewares.

    Returns:
        Configured agent with all middlewares attached
    """
    # 1. Initialize Gemini model
    logger.info("Initializing Gemini 2.5 Flash Lite model...")
    model = ChatGoogleGenerativeAI(
        google_api_key=SETTINGS.GEMINI_API_KEY,
        model="gemini-2.5-flash-lite",
        temperature=0.1,
        thinking_budget=4000,
        max_output_tokens=50000,
        include_thoughts=True,  # Enable reasoning/thinking output
    )

    # 2. Setup DeepAgent Filesystem Backend
    logger.info("Setting up filesystem backend...")
    workspace_dir = project_root / "agent_workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Workspace directory: {workspace_dir.absolute()}")
    logger.info(f"Workspace exists: {workspace_dir.exists()}")
    
    # CRITICAL: virtual_mode=True is required to map / paths to workspace directory
    # Without it, agent will try to write to system root and fail with "Read-only file system"
    backend = FilesystemBackend(
        root_dir=str(workspace_dir.absolute()),
        virtual_mode=True  # Maps / to workspace directory
    )
    fs_middleware = FilesystemMiddleware(backend=backend)

    # 3. Setup TodoWrite Middleware
    logger.info("Setting up TodoWrite middleware...")
    todo_middleware = TodoWriteMiddleware()

    # 4. Setup PatchToolCalls Middleware
    logger.info("Setting up PatchToolCalls middleware...")
    patch_middleware = PatchToolCallsMiddleware()

    # 5. Collect all tools
    logger.info("Collecting tools...")
    tools = []
    
    tools.append(search_web)
    logger.info("Added web_search tool")
    
    tools.append(scrape_web_content)
    logger.info("Added fetch_web_content tool")

    # 6. Setup SubAgent Middleware
    logger.info("Setting up SubAgent middleware...")
    subagent_middleware = SubAgentMiddleware(
        default_model=model,
        default_middleware=[
            fs_middleware,
            todo_middleware,
            patch_middleware,
            ToolRetryMiddleware(on_failure="Tool call failed, please try again."),
        ],
        default_tools=tools,
        general_purpose_agent=True,
    )

    # 7. Create agent with all middlewares
    logger.info("Creating agent with middlewares...")
    agent = create_agent(
        model=model,
        tools=tools,
        middleware=[
            todo_middleware,
            fs_middleware,
            subagent_middleware,
            patch_middleware,
            ToolRetryMiddleware(on_failure="Tool call failed, please try again."),
        ],
    )

    logger.info("✅ Custom deep agent created successfully!")
    logger.info(f"Total tools available: {len(tools)}")
    logger.info(f"Workspace directory: {workspace_dir}")
    
    return agent


async def run_demo():
    """Run a demo task with the custom deep agent."""
    logger.info("=" * 80)
    logger.info("CUSTOM DEEP AGENT DEMO")
    logger.info("=" * 80)
    
    # Create the agent
    agent = create_custom_deep_agent()
    
    # Define a research task
    research_task = """
    Help me develop a brand positioning strategy for a new eco-friendly sneaker brand.
    Save the report in file "eco_sneaker_brand_positioning.md" so I can read it later.
    """
    
    logger.info("📋 Research Task:")
    logger.info(research_task)
    logger.info("=" * 80)
    logger.info("🚀 Starting agent execution...")
    
    try:
        # Execute the task
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=research_task)]},
            {"recursion_limit": 1000},
        )
        
        # Print results
        logger.info("=" * 80)
        logger.info("📊 EXECUTION RESULTS")
        logger.info("=" * 80)
        
        # Print full result structure
        logger.info("🔍 FULL RESULT STRUCTURE:")
        logger.info(f"Result keys: {list(result.keys())}")
        
        # Print todos if available
        if "todos" in result:
            logger.info("📝 Todos Created:")
            for i, todo in enumerate(result["todos"], 1):
                status_emoji = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅",
                }.get(todo["status"], "❓")
                
                logger.info(f"{i}. {status_emoji} {todo['content']}")
                logger.info(f"   Status: {todo['status']} | Priority: {todo['priority']}")
                logger.info(f"   Active Form: {todo.get('activeForm', 'N/A')}")
        
        # Print ALL messages in detail
        if "messages" in result:
            logger.info(f"💬 Total messages exchanged: {len(result['messages'])}")
            logger.info("=" * 80)
            logger.info("📜 COMPLETE MESSAGE HISTORY:")
            logger.info("=" * 80)
            
            for i, msg in enumerate(result["messages"], 1):
                msg_type = type(msg).__name__
                logger.info(f"[Message {i}/{len(result['messages'])}] Type: {msg_type}")
                logger.info("-" * 60)
                
                if msg_type == "HumanMessage":
                    logger.info(f"👤 Human: {msg.content}")
                    
                elif msg_type == "AIMessage":
                    # First, extract and display thinking/reasoning if available
                    if hasattr(msg, "content") and msg.content:
                        content = msg.content
                        
                        # Handle list content (may contain thinking + text)
                        if isinstance(content, list):
                            thinking_parts = []
                            text_parts = []
                            
                            for part in content:
                                if isinstance(part, dict):
                                    # Extract thinking content (Gemini uses 'thinking' not 'reasoning')
                                    if part.get("type") == "thinking":
                                        thinking_parts.append(part.get("thinking", ""))
                                    # Extract text content
                                    elif part.get("type") == "text":
                                        text_parts.append(part.get("text", ""))
                                elif isinstance(part, str):
                                    # Direct string content
                                    text_parts.append(part)
                            
                            # Display thinking FIRST (before tool calls or response)
                            if thinking_parts:
                                logger.info("💭 AI Thinking/Reasoning:")
                                for thinking in thinking_parts:
                                    logger.info(f"{thinking}")
                                logger.info("-" * 60)
                    
                    # Then, check if it's a tool call message
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        logger.info("🤖 AI: [Tool Calls]")
                        for j, tool_call in enumerate(msg.tool_calls, 1):
                            tool_name = tool_call.get("name", "Unknown")
                            tool_args = tool_call.get("args", {})
                            tool_id = tool_call.get("id", "N/A")
                            logger.info(f"  Tool Call {j}:")
                            logger.info(f"    - Name: {tool_name}")
                            logger.info(f"    - ID: {tool_id}")
                            logger.info(f"    - Args: {tool_args}")
                    
                    # Finally, display text response (if not a tool call)
                    elif hasattr(msg, "content") and msg.content:
                        content = msg.content
                        
                        # Handle list content
                        if isinstance(content, list):
                            # We already extracted text_parts above, just display them
                            text_parts = []
                            for part in content:
                                if isinstance(part, dict) and part.get("type") == "text":
                                    text_parts.append(part.get("text", ""))
                                elif isinstance(part, str):
                                    text_parts.append(part)
                            
                            if text_parts:
                                logger.info("🤖 AI Response:")
                                logger.info("\n".join(text_parts))
                        else:
                            # Simple string content
                            logger.info(f"🤖 AI Response:\n{content}")
                    
                elif msg_type == "ToolMessage":
                    tool_name = getattr(msg, "name", "Unknown")
                    logger.info(f"🔧 Tool Result ({tool_name}):")
                    logger.info(f"{msg.content}")
                    
                else:
                    # Handle other message types
                    if hasattr(msg, "content"):
                        logger.info(f"📨 {msg_type}: {msg.content}")
                    else:
                        logger.info(f"📨 {msg_type}: [No content]")
        
        logger.info("=" * 80)
        logger.info("✅ Demo completed successfully!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Error during execution: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    # Run the demo
    asyncio.run(run_demo())
