"""PreCompactNotesMiddleware — auto-save safety net for workspace notes.

Monitors conversation token usage and injects a system reminder when
approaching the summarization threshold (~65% of context window).
This gives the agent a chance to persist critical thinking to workspace
files before older messages are compressed and lost.

Design rationale: docs/BRANDMIND_WORKSPACE_NOTES_RESEARCH.md Section 8 v3.1
(Decision 3: Pre-Compact Hook)

Analogy:
- Phase transition hooks = "Save As" (manual, deliberate, comprehensive)
- Pre-compact hook = "Auto-save" (automatic, safety net, incremental)

Middleware chain position: BEFORE SummarizationMiddleware.

Example:
    pre_compact = PreCompactNotesMiddleware(
        context_window=262144,   # 256K tokens
        trigger_ratio=0.65,      # Fire at 65% (~170K tokens)
    )
    # Place before SummarizationMiddleware in the chain:
    # middleware=[context_edit, pre_compact, summarization, ...]
"""

from typing import Any, Callable

from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
)
from langchain_core.messages import SystemMessage
from loguru import logger

# System reminder injected into messages when threshold is reached.
# Instructions are SPECIFIC per file to avoid generic "update your notes"
# which leads to low-quality, unfocused writing.
PRE_COMPACT_REMINDER = (
    "## WORKSPACE AUTO-SAVE REMINDER\n\n"
    "Context approaching limit. Summarization will fire soon and compress "
    "older messages. Do a quick incremental save to preserve current work:\n\n"
    "1. `/workspace/brand_brief.md` — Is current phase S/O/A/P section up "
    "to date? If not, EDIT the specific section that changed. Do NOT rewrite "
    "other phases.\n"
    "2. `/workspace/working_notes.md` — Any new inbox items or observations "
    "since last update? APPEND only. Do NOT rewrite existing content.\n"
    "3. `/workspace/quality_gates.md` — Any gates newly completed? "
    "Mark them.\n\n"
    "Skip files that are already current. This should take 1-3 edit_file "
    "calls.\nAfter saving, continue your current work normally."
)


class PreCompactNotesMiddleware(AgentMiddleware):
    """Middleware that reminds the agent to save workspace notes before compression.

    Monitors the approximate token count of the conversation. When it exceeds
    a configurable threshold (default 65% of context window), injects a system
    reminder instructing the agent to do an incremental workspace save.

    The reminder fires only ONCE per summarization cycle. After summarization
    compresses messages (detected by a significant drop in message count),
    the flag resets and the middleware can fire again in the next cycle.

    Args:
        context_window: Total context window size in tokens.
        trigger_ratio: Fraction of context window at which to trigger (0.0-1.0).
            Must be less than the SummarizationMiddleware trigger to provide
            buffer for the agent to perform save operations.
    """

    def __init__(
        self,
        context_window: int = 262144,
        trigger_ratio: float = 0.65,
    ) -> None:
        """Initialize PreCompactNotesMiddleware.

        Args:
            context_window: Total context window size in tokens (default: 256K).
            trigger_ratio: Trigger reminder at this fraction of context window.
                Default 0.65 (65%) provides ~15% buffer before summarization
                at 80%.
        """
        self.context_window = context_window
        self.trigger_threshold = int(context_window * trigger_ratio)
        self._reminded_this_cycle = False
        self._prev_message_count = 0

        logger.info(
            f"PreCompactNotesMiddleware initialized: "
            f"trigger at {trigger_ratio:.0%} of {context_window} "
            f"= {self.trigger_threshold:,} tokens"
        )

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Check token usage and inject reminder if approaching threshold."""
        self._detect_reset_and_inject(request)
        return handler(request)

    async def awrap_model_call(  # type: ignore[override]
        self,
        request: ModelRequest,
        handler: Callable[..., Any],
    ) -> ModelResponse:
        """Async version of wrap_model_call."""
        self._detect_reset_and_inject(request)
        return await handler(request)

    def _detect_reset_and_inject(self, request: ModelRequest) -> None:
        """Core logic: estimate tokens, inject reminder if needed, detect reset.

        Mutates request.messages in place if reminder is needed.

        Workflow:
        1. Check if message count dropped significantly (post-summarization)
           → reset the reminder flag
        2. Estimate current token usage
        3. If above threshold and not yet reminded → inject system message
        """
        current_message_count = len(request.messages)

        # Detect post-summarization: message count dropped significantly.
        # SummarizationMiddleware keeps ~30 messages from potentially hundreds,
        # so a >50% drop is a reliable indicator.
        if (
            self._prev_message_count > 0
            and current_message_count < self._prev_message_count * 0.5
        ):
            if self._reminded_this_cycle:
                logger.debug(
                    "Post-summarization detected "
                    f"({self._prev_message_count} → "
                    f"{current_message_count} messages). "
                    "Resetting pre-compact reminder flag."
                )
                self._reminded_this_cycle = False

        self._prev_message_count = current_message_count

        # Estimate current token usage (approximate: 1 token ≈ 4 characters)
        estimated_tokens = self._estimate_tokens(request.messages)

        # Inject reminder if threshold exceeded and not already reminded
        if estimated_tokens >= self.trigger_threshold and not self._reminded_this_cycle:
            logger.info(
                f"Pre-compact threshold reached: ~{estimated_tokens:,} tokens "
                f"(threshold: {self.trigger_threshold:,}). "
                "Injecting workspace save reminder."
            )
            request.messages.append(SystemMessage(content=PRE_COMPACT_REMINDER))
            self._reminded_this_cycle = True

    @staticmethod
    def _estimate_tokens(messages: list[Any]) -> int:
        """Estimate token count from messages using character-based approximation.

        Uses the heuristic that 1 token ≈ 4 characters for English/Vietnamese
        mixed content. This is intentionally approximate — exact counting would
        require a tokenizer and add latency. For a threshold comparison, ±10%
        accuracy is sufficient.

        Args:
            messages: List of LangChain message objects.

        Returns:
            Estimated token count.
        """
        total_chars = 0
        for msg in messages:
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                total_chars += len(content)
            elif isinstance(content, list):
                # Multimodal content (list of dicts)
                for part in content:
                    if isinstance(part, dict):
                        total_chars += len(str(part.get("text", "")))
                    elif isinstance(part, str):
                        total_chars += len(part)
        return total_chars // 4
