# LangChain DeepAgent Research

This document summarizes the research findings on the **DeepAgents** library by LangChain.

> **📝 Working Example**: See [examples/deep_agent_demo.py](examples/deep_agent_demo.py) for a complete, runnable demo implementing all concepts covered in this document.

## 1. Overview
**DeepAgents** is an advanced agent framework built on top of **LangGraph** and **LangChain**. It is designed to create sophisticated AI agents capable of handling complex, multi-step tasks that require:
*   **Planning**: Breaking down high-level goals into manageable subtasks.
*   **Persistence**: Maintaining long-term memory and state across sessions.
*   **Filesystem Access**: interacting with a virtual or real filesystem.
*   **Sub-agents**: Delegating specialized work to isolated sub-agents.

## 2. Installation

To use DeepAgents, you need to install the `deepagents` package along with standard LangChain dependencies.

```bash
pip install deepagents langchain tavily-python
```
*   `deepagents`: The core library.
*   `langchain`: For base abstractions.
*   `tavily-python`: Recommended for web search capabilities (optional but common).

## 3. Core Concepts & Syntax

### 3.1. Basic Agent Setup
The simplest way to create a Deep Agent is using `create_deep_agent`.

```python
import os
from deepagents import create_deep_agent
from tavily import TavilyClient

# 1. Define Tools
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def internet_search(query: str, max_results: int = 5):
    """Run a web search to find information."""
    return tavily_client.search(query, max_results=max_results)

# 2. Create Agent
agent = create_deep_agent(
    tools=[internet_search],
    system_prompt="You are a helpful research assistant. Conduct research and write a polished report.",
)

# 3. Invoke Agent
result = agent.invoke({
    "messages": [
        {"role": "user", "content": "What is the architecture of LangGraph?"}
    ]
})
```

### 3.2. Customizing the Model
By default, it might use a specific Anthropic model. You can override this with any LangChain chat model.

```python
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

# Initialize OpenAI model
model = init_chat_model("openai:gpt-4o")

agent = create_deep_agent(
    model=model,
    tools=[...],
)
```

### 3.3. Sub-agents (Delegation)
Deep Agents can spawn sub-agents to handle specific domains. This isolates context and improves performance on complex tasks.

```python
from deepagents import create_deep_agent

# Define a sub-agent configuration
research_subagent = {
    "name": "research-agent",
    "description": "Used to research in-depth questions",
    "prompt": "You are an expert researcher. Focus on finding factual data.",
    "tools": [internet_search], # Give specific tools to sub-agent
    "model": "openai:gpt-4o",
}

# Register sub-agent with main agent
agent = create_deep_agent(
    subagents=[research_subagent]
)
```

## 4. Filesystem Backend (Detailed)

DeepAgents uses a **Pluggable Backend** system to manage how it reads and writes files. This is crucial for tasks involving code generation, report writing, or data analysis.

### 4.1. Backend Types
*   **StateBackend (Default)**:
    *   Files are stored in the agent's **state** (RAM).
    *   **Ephemeral**: Data is lost when the agent state is cleared or the session ends.
    *   Good for temporary scratchpads.

*   **FilesystemBackend**:
    *   Files are stored on the **local disk** of the machine running the code.
    *   **Persistent**: Files remain after the program exits.
    *   Good for generating artifacts (PDFs, code files) that the user needs to access.

*   **StoreBackend**:
    *   Files are stored in a **LangGraph Store** (database or KV store).
    *   Good for distributed systems or cloud deployments.

*   **CompositeBackend**:
    *   Routes different file paths to different backends.
    *   Example: `/tmp/` -> RAM, `/data/` -> Disk.

### 4.2. Configuration Examples

#### A. Writing to Local Disk (Most Common Use Case)

**CRITICAL**: When using `FilesystemBackend`, you **MUST** set `virtual_mode=True` to enable proper path mapping. Without it, the agent will try to write to the system root `/` and fail with "Read-only file system" error.

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

# CORRECT: Enable virtual_mode to map / to workspace directory
agent = create_deep_agent(
    backend=FilesystemBackend(
        root_dir="./workspace",
        virtual_mode=True  # Maps / paths to workspace directory
    ),
)

# If agent runs: write_file("/report.md", "content")
# File created at: ./workspace/report.md
```

**Why `virtual_mode=True` is required:**
- DeepAgent's filesystem tools use **absolute paths** starting with `/`
- Without `virtual_mode=True`, `/` refers to the system root (read-only)
- With `virtual_mode=True`, `/` is mapped to your `root_dir` (workspace)

#### B. Hybrid Configuration (Composite)
To mix ephemeral memory and persistent storage:

```python
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, FilesystemBackend

agent = create_deep_agent(
    backend=CompositeBackend(
        default=StateBackend(), # Default to RAM for temporary files
        routes={
            "/mnt/data/": FilesystemBackend(
                root_dir="./data",
                virtual_mode=True
            ),
        },
    ),
)
```

## 5. AgentMiddleware System

DeepAgents uses a **middleware architecture** where functionality is added through middleware components. When you pass middleware to `create_agent`, they automatically:
1. Inject their tools into the agent
2. Add system prompts to guide tool usage
3. Hook into the agent lifecycle for specialized processing

### 5.1. Using Middlewares with `create_agent`

```python
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents.backends import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemMiddleware
from shared.agent_tools import TodoWriteMiddleware

# Setup model
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

# Setup middlewares
backend = FilesystemBackend(root_dir="./workspace", virtual_mode=True)
fs_middleware = FilesystemMiddleware(backend=backend)
todo_middleware = TodoWriteMiddleware()

# Create agent - middlewares auto-inject tools and prompts
agent = create_agent(
    model=model,
    tools=[],  # Your custom tools
    middleware=[
        fs_middleware,      # Adds: read_file, write_file, ls, etc.
        todo_middleware,    # Adds: write_todos tool
    ],
)
```

**Key Points:**
- Middlewares automatically add their tools - no need to manually extract them
- System prompts are automatically injected
- Order matters: earlier middlewares process first

## 6. Enabling Thinking/Reasoning Output (Gemini Models)

Gemini 2.5+ models support internal reasoning/thinking processes. To display this:

### 6.1. Enable in Model Configuration

```python
from langchain_google_genai import ChatGoogleGenerativeAI

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    thinking_budget=4000,           # Max thinking tokens
    include_thoughts=True,          # Enable reasoning output
)
```

### 6.2. Parse Thinking Content

The response content will be a list with thinking and text parts:

```python
# Response structure:
[
    {'type': 'thinking', 'thinking': '...reasoning process...'},
    "...final response text..."
]
```

Example parsing code:

```python
for msg in result["messages"]:
    if isinstance(msg.content, list):
        for part in msg.content:
            if isinstance(part, dict) and part.get("type") == "thinking":
                print(f"💭 Thinking: {part.get('thinking')}")
            elif isinstance(part, str):
                print(f"🤖 Response: {part}")
```

**Important Notes:**
- Type is `"thinking"` (not `"reasoning"`)
- Content key is `"thinking"` (not `"text"`)
- Display thinking **before** tool calls/responses for logical flow

## 7. Complete Working Demo

Here's a full working example combining all concepts:

```python
from pathlib import Path
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents.backends import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from deepagents.middleware.subagents import SubAgentMiddleware

# 1. Initialize Gemini model with thinking enabled
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.1,
    thinking_budget=4000,
    include_thoughts=True,  # Enable reasoning output
)

# 2. Setup Filesystem Backend (MUST use virtual_mode=True)
workspace_dir = Path("./agent_workspace")
workspace_dir.mkdir(parents=True, exist_ok=True)

backend = FilesystemBackend(
    root_dir=str(workspace_dir.absolute()),
    virtual_mode=True  # Critical for proper path mapping
)
fs_middleware = FilesystemMiddleware(backend=backend)

# 3. Setup other middlewares
patch_middleware = PatchToolCallsMiddleware()
subagent_middleware = SubAgentMiddleware(
    default_model=model,
    default_middleware=[fs_middleware, patch_middleware],
    general_purpose_agent=True,
)

# 4. Add custom tools
from your_tools import search_web, scrape_web_content
tools = [search_web, scrape_web_content]

# 5. Create agent with all middlewares
agent = create_agent(
    model=model,
    tools=tools,
    middleware=[
        fs_middleware,
        subagent_middleware,
        patch_middleware,
        ToolRetryMiddleware(on_failure="Tool call failed, please try again."),
    ],
)

# 6. Run agent
result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "Research topic X and save to report.md"}]},
    {"recursion_limit": 100},
)

# 7. Display results with thinking
for msg in result["messages"]:
    if hasattr(msg, "content") and isinstance(msg.content, list):
        # Extract thinking
        for part in msg.content:
            if isinstance(part, dict) and part.get("type") == "thinking":
                print(f"💭 AI Thinking:\n{part.get('thinking')}\n")
        
        # Extract response
        for part in msg.content:
            if isinstance(part, str):
                print(f"🤖 AI Response:\n{part}\n")
```

## 8. Replicating `create_deep_agent` Manually

If you want to completely replicate the behavior of `create_deep_agent` but maintain full control over the graph construction, you need to combine several middlewares.

### Core Middlewares (Essential)
1.  **`FilesystemMiddleware`**: For file operations.
2.  **`TodoListMiddleware`**: For planning and task tracking (`write_todos`, `read_todos`).
3.  **`SubAgentMiddleware`**: For delegation (`task`).

### Advanced Middlewares (Included by default in `create_deep_agent`)
4.  **`SummarizationMiddleware`**: Automatically summarizes conversation history when it exceeds token limits (e.g., 170k tokens) to prevent overflow.
5.  **`HumanInTheLoopMiddleware`**: Pauses execution for human approval on sensitive tools (configured via `interrupt_on`).
6.  **`PatchToolCallsMiddleware`**: Fixes dangling tool calls from interrupted steps.
7.  **`AnthropicPromptCachingMiddleware`**: Optimizes costs when using Anthropic models by caching system prompts.

### Replication Steps (Full Version)

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# Import DeepAgent Middlewares
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.middleware.todo import TodoListMiddleware
from deepagents.middleware.subagents import SubAgentMiddleware
from deepagents.middleware.summarize import SummarizationMiddleware
from deepagents.backends import FilesystemBackend

# 1. Setup Backend
backend = FilesystemBackend(root_dir="./workspace", virtual_mode=True)

# 2. Initialize Middlewares
fs_middleware = FilesystemMiddleware(backend=backend)
todo_middleware = TodoListMiddleware()
subagent_middleware = SubAgentMiddleware(default_model=model)
summary_middleware = SummarizationMiddleware()

# 3. Create Agent with middlewares (tools auto-injected)
model = ChatOpenAI(model="gpt-4o")
agent = create_agent(
    model=model,
    tools=[],  # Add custom tools here
    middleware=[
        fs_middleware,
        todo_middleware,
        subagent_middleware,
        summary_middleware,
    ],
)

# Now you have a "Deep Agent" built manually!
```

## 9. Common Issues & Solutions

### Issue 1: "Read-only file system" error
**Cause**: `FilesystemBackend` created without `virtual_mode=True`
**Solution**: Always use `FilesystemBackend(root_dir="...", virtual_mode=True)`

### Issue 2: Thinking/reasoning not showing
**Cause**: 
- `include_thoughts=True` not set in model config
- Parsing code looking for wrong keys (`"reasoning"` instead of `"thinking"`)
**Solution**: Use `include_thoughts=True` and parse `type="thinking"` with key `"thinking"`

### Issue 3: Middlewares not adding tools
**Cause**: Trying to manually extract tools instead of passing middleware to `create_agent`
**Solution**: Pass middlewares directly to `create_agent(..., middleware=[...])` - they auto-inject tools

## 10. Resources
*   **GitHub Repository**: [https://github.com/langchain-ai/deepagents](https://github.com/langchain-ai/deepagents)
*   **Quickstarts**: [https://github.com/langchain-ai/deepagents-quickstarts](https://github.com/langchain-ai/deepagents-quickstarts)
*   **LangChain Docs**: [https://docs.langchain.com/](https://docs.langchain.com/)
