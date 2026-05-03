"""Unit tests for EnsureTasksFinishedMiddleware._is_agent_stopping detection.

These tests pin the patched detection contract introduced after the
2026-05-04 Phase A iso v3 turn 4 silent-dispatch investigation. The
investigation surfaced two gaps in the pre-patch implementation:

1. ``finish_reason``-gated detection — the previous check only treated
   ``finish_reason == "STOP"`` as a stop signal, which let Gemini 3
   thinking-mode terminal responses with ``finish_reason`` values like
   ``"TOOL_USE"`` / ``"OTHER"`` / ``"MAX_TOKENS"`` slip through with
   empty user-facing text.
2. Modern ``tool_calls`` attribute blindness — the previous check only
   inspected the legacy ``additional_kwargs["function_call"]`` slot,
   leaving the modern LangChain ``AIMessage.tool_calls`` attribute
   un-checked.

The patched ``_is_agent_stopping`` is finish_reason-agnostic and reads
both the modern and legacy tool-call slots: a terminal message with no
user-visible text AND no tool calls (in either slot) is a stop. The
test cases below confirm the patched contract holds for the canonical
positive control, the previously-missed Gemini thinking-mode shapes,
the modern ``tool_calls`` regression guard, and the legacy backward-
compatibility path.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from shared.agent_middlewares.stop_check.ensure_tasks_finished_middleware import (
    EnsureTasksFinishedMiddleware,
)


def _response_with_message(message: AIMessage) -> Any:
    """Build a ``ModelResponse``-shaped object exposing ``result`` for the middleware.

    The middleware's detection helper reads ``response.result`` and pulls the
    last entry. Production code uses ``langchain.agents.middleware`` types we do
    not need to instantiate fully — a light ``MagicMock`` with the right
    ``result`` attribute suffices for behavioral assertions.

    Args:
        message: The terminal ``AIMessage`` the middleware will inspect.

    Returns:
        An object whose ``result`` attribute is a single-element list containing
        ``message``.
    """
    response = MagicMock()
    response.result = [message]
    return response


class TestPositiveControl:
    """Pin the obviously-stopping case so any detection regression surfaces."""

    def test_empty_content_no_tool_calls_finish_stop_is_stopping(self) -> None:
        """Empty content + no tool calls + finish_reason STOP must register as stopping.

        This is the canonical "premature stop" the middleware was built for.
        If this assertion ever fails, the middleware has lost its primary
        guardrail and every other gap discussed below is moot.
        """
        msg = AIMessage(content="")
        msg.response_metadata = {"finish_reason": "STOP"}
        middleware = EnsureTasksFinishedMiddleware(max_reminders=1)

        assert middleware._is_agent_stopping(_response_with_message(msg)) is True


class TestThinkingOnlyContent:
    """Gemini 3 thinking-mode pattern observed in turn 4: thinking blocks only, no text block."""

    def test_thinking_only_content_with_finish_stop_is_detected_as_stopping(
        self,
    ) -> None:
        """Content list with only a thinking block and finish_reason STOP should be stopping.

        Turn 4 evidence: ``thinking_chars=2000`` and ``agent_chars=0``. The
        terminal AIMessage is plausibly shaped like ``[{"type": "thinking", ...}]``
        with no ``text`` part. The middleware walks the content list for a
        non-empty ``text`` part — finds none — and falls through to the
        ``finish_reason`` branch.
        """
        msg = AIMessage(
            content=[
                {
                    "type": "thinking",
                    "thinking": "Internal reasoning only — never reaches the user.",
                }
            ]
        )
        msg.response_metadata = {"finish_reason": "STOP"}
        middleware = EnsureTasksFinishedMiddleware(max_reminders=1)

        assert middleware._is_agent_stopping(_response_with_message(msg)) is True

    def test_thinking_only_content_with_non_stop_finish_is_detected(self) -> None:
        """Thinking-only content with finish_reason != STOP must still register as stopping.

        This pins the regression fix that closed the original detection gap.
        The pre-fix middleware only treated ``finish_reason == "STOP"`` as
        stopping; Gemini 3 thinking-mode regularly emits terminal responses
        with values like ``"TOOL_USE"`` / ``"OTHER"`` / ``"MAX_TOKENS"`` even
        when no further work follows. The patched check is finish_reason-
        agnostic: no user-visible text plus no tool calls means the turn is
        yielding with nothing for the user, regardless of what the provider
        reports as the stop signal.
        """
        msg = AIMessage(
            content=[
                {"type": "thinking", "thinking": "I have updated workspace."},
            ]
        )
        msg.response_metadata = {"finish_reason": "TOOL_USE"}
        middleware = EnsureTasksFinishedMiddleware(max_reminders=1)

        assert middleware._is_agent_stopping(_response_with_message(msg)) is True


class TestModernToolCallsAttribute:
    """Modern LangChain AIMessage uses ``tool_calls``, not legacy ``function_call``."""

    def test_modern_tool_calls_attribute_marks_not_stopping(self) -> None:
        """Empty content + populated modern ``tool_calls`` must register as not-stopping.

        The patched detection reads both the modern ``tool_calls`` attribute
        and the legacy ``additional_kwargs["function_call"]`` slot. This guards
        against a regression where the middleware would otherwise classify a
        still-working turn (tool calls outstanding) as a premature stop and
        spuriously fire the FINAL_CONFIRMATION re-prompt every time the
        provider used the modern schema.
        """
        msg = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "write_todos",
                    "args": {"todos": []},
                    "id": "tc-1",
                }
            ],
        )
        msg.additional_kwargs = {}
        msg.response_metadata = {"finish_reason": "TOOL_USE"}
        middleware = EnsureTasksFinishedMiddleware(max_reminders=1)

        assert middleware._is_agent_stopping(_response_with_message(msg)) is False


class TestFinishReasonAgnosticPolicy:
    """Pin behavior for finish_reason values Gemini emits beyond ``STOP``."""

    def test_finish_reason_other_with_empty_content_and_no_tools_is_stopping(
        self,
    ) -> None:
        """Empty content + no tool calls + finish_reason=OTHER must register as stopping.

        Pins the patched contract: any terminal message that carries no user-
        visible text and no tool calls is a stop, regardless of the
        ``finish_reason`` string the provider reports. Without this, Gemini's
        non-STOP terminal reasons (``OTHER``, ``MAX_TOKENS``, ``TOOL_USE``,
        provider-specific values) can let a silent dispatch slip through.
        """
        msg = AIMessage(content="")
        msg.additional_kwargs = {}
        msg.response_metadata = {"finish_reason": "OTHER"}
        middleware = EnsureTasksFinishedMiddleware(max_reminders=1)

        assert middleware._is_agent_stopping(_response_with_message(msg)) is True


class TestEmptyContentWithLegacyFunctionCall:
    """Sanity check the legacy path still works (regression guard)."""

    def test_empty_content_legacy_function_call_not_stopping(self) -> None:
        """Legacy ``additional_kwargs.function_call`` must register as not-stopping."""
        msg = AIMessage(content="")
        msg.additional_kwargs = {
            "function_call": {"name": "write_todos", "arguments": "{}"}
        }
        msg.response_metadata = {"finish_reason": "TOOL_USE"}
        middleware = EnsureTasksFinishedMiddleware(max_reminders=1)

        assert middleware._is_agent_stopping(_response_with_message(msg)) is False
