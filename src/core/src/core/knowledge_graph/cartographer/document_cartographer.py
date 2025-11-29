"""Document Cartographer - Autonomous Document Structure Analyzer.

This module provides the DocumentCartographer class which uses a Deep Agent
to analyze document structure and generate a hierarchical map.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage
from loguru import logger

from core.knowledge_graph.cartographer.agent_config import create_cartographer_agent
from core.knowledge_graph.models import GlobalMap
from prompts.knowledge_graph.cartographer_task_prompt import CARTOGRAPHER_TASK_PROMPT


class DocumentCartographer:
    """Orchestrates document structure mapping using a Deep Agent.

    This class manages the entire process of analyzing a parsed document folder
    and generating a global_map.json file with hierarchical structure information.
    """

    def __init__(self, document_folder: str) -> None:
        """Initialize the Document Cartographer.

        Args:
            document_folder: Absolute path to parsed document folder
        """
        self.document_folder = Path(document_folder)
        if not self.document_folder.exists():
            raise ValueError(f"Document folder not found: {document_folder}")

        logger.info(f"Initialized DocumentCartographer for: {self.document_folder}")

        # Create agent
        self.agent, self.model = create_cartographer_agent(str(self.document_folder))

    async def analyze(self) -> tuple[GlobalMap, list[Any]]:
        """Analyze document structure and generate global map.

        Returns:
            Tuple of (GlobalMap instance, list of agent messages)

        Raises:
            ValueError: If agent output cannot be parsed into GlobalMap
                after all retries
        """
        MAX_ANALYSIS_RETRIES = 3

        for attempt in range(1, MAX_ANALYSIS_RETRIES + 1):
            try:
                logger.info(f"📊 Analysis attempt {attempt}/{MAX_ANALYSIS_RETRIES}")
                return await self._run_analysis_attempt()
            except ValueError as e:
                if attempt < MAX_ANALYSIS_RETRIES:
                    logger.warning(f"⚠️  Analysis attempt {attempt} failed: {e}")
                    logger.warning(
                        f"🔄 Retrying... ({attempt + 1}/{MAX_ANALYSIS_RETRIES})"
                    )
                    await asyncio.sleep(2)  # Brief delay before retry
                else:
                    logger.error(
                        f"❌ All {MAX_ANALYSIS_RETRIES} analysis attempts failed"
                    )
                    raise

        raise ValueError("Analysis failed after all retries")

    async def _run_analysis_attempt(self) -> tuple[GlobalMap, list[Any]]:
        """Run a single analysis attempt.

        Returns:
            Tuple of (GlobalMap instance, list of agent messages)

        Raises:
            ValueError: If this attempt fails
        """
        logger.info("Starting document structure analysis...")
        logger.info("🚀 Invoking agent with analysis task...")
        logger.info(f"📁 Document folder: {self.document_folder}")
        logger.info("⏳ This may take several minutes for large documents...")

        # Invoke agent with retry logic (handles transient API errors)
        RETRY_TIMES = 3
        result = None
        last_error = None

        while RETRY_TIMES > 0:
            try:
                result = await self.agent.ainvoke(  # type: ignore[attr-defined]
                    {"messages": [HumanMessage(content=CARTOGRAPHER_TASK_PROMPT)]},
                    {"recursion_limit": 2000},
                )
                break  # Success, exit retry loop
            except Exception as e:
                last_error = e
                RETRY_TIMES -= 1
                if RETRY_TIMES == 0:
                    logger.error(f"Agent invocation failed after 3 retries: {e}")
                    raise e  # Reraise after final failure
                logger.warning(
                    f"Agent invocation failed, retrying... ({3 - RETRY_TIMES}/3): {e}"
                )
                await asyncio.sleep(1)  # Brief pause before retry

        if result is None:
            raise ValueError(f"Agent invocation failed: {last_error}")

        # Check if recursion limit was hit
        if "recursion_limit" in str(result):
            logger.warning("Agent may have hit recursion limit!")

        # Extract messages from the result for logging and debugging
        messages = result.get("messages", [])
        logger.info(f"Agent completed with {len(messages)} messages")
        logger.debug(f"Result keys: {result.keys()}")

        # Agent writes global_map.json directly via write_file tool
        # We just need to validate the file exists and is valid JSON
        global_map_path = Path(self.document_folder) / "global_map.json"

        if not global_map_path.exists():
            logger.error(f"global_map.json not found at {global_map_path}")

            # Save messages for debugging
            debug_log_path = self.save_message_log(messages)
            logger.error(f"Saved debug messages to: {debug_log_path}")

            raise ValueError(
                "Agent did not create global_map.json file. "
                "Check agent logs for errors."
            )

        logger.info(f"✓ Found global_map.json at {global_map_path}")

        # Validate JSON format
        try:
            with open(global_map_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            global_map = GlobalMap(**data)
            logger.info(
                f"✓ Successfully validated global_map with {len(global_map.structure)} "
                "top-level sections"
            )

            return global_map, messages

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse global_map.json: {e}")
            logger.error(f"File path: {global_map_path}")

            # Save messages for debugging
            debug_log_path = self.save_message_log(messages)
            logger.error(f"Saved debug messages to: {debug_log_path}")

            raise ValueError(f"Invalid JSON in global_map.json: {e}") from e

    def _format_message_pretty(self, msg: Any, index: int) -> str:
        """Format a single message for human-readable output.

        Args:
            msg: Message object
            index: Message index in conversation

        Returns:
            Formatted string representation
        """
        msg_type = type(msg).__name__
        lines = [f"\n{'=' * 80}", f"Message #{index + 1}: {msg_type}", f"{'=' * 80}"]

        if msg_type == "HumanMessage":
            content = msg.content if hasattr(msg, "content") else "[No content]"
            lines.append(f"\n{content}")

        elif msg_type == "AIMessage":
            # Check for content first (thinking + text)
            if hasattr(msg, "content") and msg.content:
                content = msg.content
                if isinstance(content, list):
                    # Handle list content (thinking + text)
                    for part in content:
                        if isinstance(part, dict):
                            if part.get("type") == "thinking":
                                thinking = part.get("thinking", "")
                                if thinking:
                                    lines.append("\n💭 Thinking:")
                                    # Show full thinking (no truncation)
                                    lines.append(f"  {thinking}")
                            elif part.get("type") == "text":
                                text = part.get("text", "")
                                if text:
                                    lines.append("\n📝 Response:")
                                    # Show full response (no truncation)
                                    lines.append(f"  {text}")
                        elif isinstance(part, str):
                            lines.append(f"\n{part}")
                else:
                    # String content - show full text
                    lines.append(f"\n{str(content)}")

            # Check for tool calls AFTER content
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                lines.append("\n🔧 Tool Calls:")
                for i, tool_call in enumerate(msg.tool_calls, 1):
                    tool_name = tool_call.get("name", "Unknown")
                    tool_args = tool_call.get("args", {})
                    lines.append(f"  {i}. {tool_name}")
                    for key, value in tool_args.items():
                        # Truncate long values
                        val_str = str(value)
                        if len(val_str) > 100:
                            val_str = val_str[:100] + "..."
                        lines.append(f"     └─ {key}: {val_str}")

        elif msg_type == "ToolMessage":
            content = msg.content if hasattr(msg, "content") else "[No content]"
            # Truncate long tool output
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"\n{content}")

        else:
            # Generic message type
            if hasattr(msg, "content"):
                content = str(msg.content)
                if len(content) > 500:
                    content = content[:500] + "..."
                lines.append(f"\n{content}")

        return "\n".join(lines)

    def save_message_log(
        self, messages: list[Any], output_dir: Path | None = None
    ) -> Path:
        """Save agent conversation messages to both JSON and pretty-printed text logs.

        Args:
            messages: List of agent messages
            output_dir: Directory to save log (defaults to document_folder/logs)

        Returns:
            Path to saved JSON log file
        """
        if output_dir is None:
            output_dir = self.document_folder / "logs"

        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_log_file = output_dir / f"cartographer_messages_{timestamp}.json"
        text_log_file = output_dir / f"cartographer_messages_{timestamp}.txt"

        # Save JSON log (for programmatic access)
        message_log = []
        for msg in messages:
            msg_data: dict[str, Any] = {
                "type": type(msg).__name__,
                "content": msg.content if hasattr(msg, "content") else None,
            }
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                msg_data["tool_calls"] = msg.tool_calls

            message_log.append(msg_data)

        json_log_file.write_text(json.dumps(message_log, indent=2, ensure_ascii=False))

        # Save pretty-printed text log (for human reading)
        text_lines = [
            "=" * 80,
            "DOCUMENT CARTOGRAPHER - MESSAGE LOG",
            "=" * 80,
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Document: {self.document_folder.name}",
            f"Total Messages: {len(messages)}",
            "=" * 80,
        ]

        for i, msg in enumerate(messages):
            text_lines.append(self._format_message_pretty(msg, i))

        text_lines.append("\n" + "=" * 80)
        text_lines.append("END OF LOG")
        text_lines.append("=" * 80)

        text_log_file.write_text("\n".join(text_lines), encoding="utf-8")

        logger.info(f"✓ Saved message log to {json_log_file}")
        logger.info(f"✓ Saved pretty log to {text_log_file}")

        return json_log_file
