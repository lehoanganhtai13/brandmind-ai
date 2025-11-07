import os
import asyncio
import sys
from typing import List

# Add project root to path to allow imports from root
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

# Setup environment
from src.config.system_config import SETTINGS
os.environ["GOOGLE_API_KEY"] = SETTINGS.GEMINI_API_KEY

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Import the OFFICIAL LangChain middleware
from shared.agent_tools.todo.todo_write_middleware import TodoWriteMiddleware 
from langgraph.checkpoint.memory import InMemorySaver

async def main():
    """Main function to test the OFFICIAL LangChain middleware."""
    print("--- Running Test with OFFICIAL TodoListMiddleware (Expected to PASS) ---")

    # 1. Instantiate the official middleware and a checkpointer
    todo_middleware = TodoWriteMiddleware()
    memory_saver = InMemorySaver()

    # 2. Create Model
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.1, thinking_budget=4000)

    # 3. Create Agent with the official middleware and checkpointer
    agent = create_agent(
        model=model,
        tools=[], # Tools are provided by the middleware
        middleware=[todo_middleware],
        checkpointer=memory_saver
    )

    # 4. Invoke Agent
    prompt = "Develop a comprehensive marketing strategy for a new eco-friendly coffee brand launch."
    print(f"\nUser Prompt: {prompt}")

    try:
        # The agent needs a thread_id when using a checkpointer
        config = {"configurable": {"thread_id": "official-test-thread-1"}}
        
        result = await agent.ainvoke({
            "messages": [HumanMessage(content=prompt)]
        }, config=config)

        print("\n--- Agent Result ---")
        final_message = result["messages"][-1]
        print(f"Final Message Content: {final_message.content}")

        # Print all messages including tool calls
        print("\n--- Full Message History ---")
        for i, msg in enumerate(result["messages"]):
            print(f"[{i}] {msg}")
        
        assert "todos" in result and len(result["todos"]) > 0
        print(f"Todo list created with {len(result['todos'])} items: {result['todos']}")

        print("\n✅ SUCCESS: The official middleware ran successfully without errors!")

    except Exception as e:
        print(f"\n❌ TEST FAILED: The script with the official middleware failed unexpectedly.")
        print(f"Exception: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())