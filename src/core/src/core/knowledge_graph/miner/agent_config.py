"""Deep Agent configuration for Knowledge Miner.

Sets up Gemini 2.5 Flash model with TodoWriteMiddleware and validate_triples
tool for knowledge extraction from document chunks.
"""

from langchain.agents import create_agent
from langchain.agents.middleware import (
    ContextEditingMiddleware,
    SummarizationMiddleware,
    ToolRetryMiddleware,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

from config.system_config import SETTINGS
from prompts.knowledge_graph.miner_system_prompt import (
    MINER_SYSTEM_PROMPT,
    SPECIALIZED_DOMAIN,
)
from shared.agent_middlewares import (
    EnsureTasksFinishedMiddleware,
    LogModelMessageMiddleware,
)
from shared.agent_tools.knowledge_graph import finalize_output, validate_triples


def create_miner_agent(
    model_name: str = "gemini-3-flash-preview",
) -> tuple[object, ChatGoogleGenerativeAI]:
    """Create a Deep Agent configured for knowledge extraction.

    This agent has access to:
    - validate_triples tool for quality assurance
    - StopCheck hook for ensuring tasks are completed
    - ContextEditing and Summarization middlewares for managing model context
    - LogModelMessage middleware for logging model messages
    - Gemini 2.5 Flash with thinking mode by default

    Args:
        model_name: Model to use (default: gemini-3-flash-preview)

    Returns:
        Tuple of (configured agent, model instance)
    """
    logger.info("Initializing Knowledge Miner agent...")

    # 1. Initialize Gemini model with thinking mode
    model = ChatGoogleGenerativeAI(
        google_api_key=SETTINGS.GEMINI_API_KEY,
        model=model_name,
        temperature=1.0,  # Gemini 3 default - recommended by Google
        thinking_level="medium",  # Gemini 3 uses thinking_level (medium for extraction)
        max_output_tokens=30000,
        include_thoughts=True,  # Enable reasoning output
    )
    model_context_window = 1048576
    logger.info(f"✓ {model_name.replace('-', ' ').title()} model initialized")

    # 2. Setup middlewares
    # Context editing middleware (clear tool uses after completion)
    from langchain.agents.middleware import ClearToolUsesEdit

    context_edit_middleware = ContextEditingMiddleware(
        edits=[ClearToolUsesEdit()],
    )

    # Message summarization middleware (compress old messages)
    msg_summary_middleware = SummarizationMiddleware(
        model=model,  # Required: model for summarization
        trigger=(
            "tokens",
            int(model_context_window * 0.6),
        ),  # Summarize after 60% of context window
        keep=("messages", 20),  # Keep last 20 messages
    )

    # Tool retry middleware (retry failed tool calls)
    retry_middleware = ToolRetryMiddleware()

    # Stop check middleware (ensure tasks are completed)
    stop_check_middleware = EnsureTasksFinishedMiddleware()

    # Log model message middleware (log model messages)
    log_message_middleware = LogModelMessageMiddleware()

    logger.info("✓ Middlewares configured")

    # 3. Collect tools
    tools = [validate_triples, finalize_output]
    logger.info(f"✓ Custom tools: {[t.__name__ for t in tools]}")

    # 4. Format system prompt with domain
    system_prompt = MINER_SYSTEM_PROMPT.replace("{{domain}}", SPECIALIZED_DOMAIN)

    # 5. Create agent with all middlewares
    agent = create_agent(  # type: ignore[var-annotated]
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=[
            context_edit_middleware,
            msg_summary_middleware,
            log_message_middleware,
            retry_middleware,
            stop_check_middleware,
        ],
    )
    logger.info("✓ Knowledge Miner Agent created successfully")

    return agent, model
