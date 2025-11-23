# DeepAgent Examples

This directory contains working examples demonstrating how to use LangChain's DeepAgent framework.

## Available Examples

### [deep_agent_demo.py](deep_agent_demo.py)

A comprehensive demo showing how to create a custom Deep Agent with:
- **Gemini 2.5 Flash Lite** model with thinking/reasoning output enabled
- **FilesystemBackend** with `virtual_mode=True` for persistent file storage
- **Custom tools**: `search_web`, `scrape_web_content`
- **Middlewares**: 
  - `FilesystemMiddleware` - File operations (read, write, ls, etc.)
  - `TodoWriteMiddleware` - Task management
  - `SubAgentMiddleware` - Task delegation to sub-agents
  - `PatchToolCallsMiddleware` - Fix dangling tool calls

**Key Features:**
- ✅ Displays AI thinking/reasoning process before responses
- ✅ Proper filesystem path mapping with virtual mode
- ✅ Complete message history logging
- ✅ Sub-agent delegation support

**How to run:**
```bash
cd /Users/mac/projects/brandmind-ai
source .venv/bin/activate
python docs/langchain/examples/deep_agent_demo.py
```

**See also:** [LangChain DeepAgent Documentation](../langchain_deep_agent.md)

## Requirements

- Python 3.10+
- Virtual environment activated
- Required packages (see `pyproject.toml`):
  - `deepagents`
  - `langchain`
  - `langchain-google-genai`
  - `loguru`

## Environment Variables

Make sure these are set in your `.env` file:
- `GEMINI_API_KEY` - Your Google Gemini API key
- `SEARXNG_HOST` (optional) - For web search functionality
- `SEARXNG_PORT` (optional) - For web search functionality
