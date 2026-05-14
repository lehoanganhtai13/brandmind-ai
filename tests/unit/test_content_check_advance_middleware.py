"""Unit tests for ContentCheckAdvanceMiddleware re-emission behaviour.

These tests pin the E1-D rejection contract introduced on 2026-05-03 to
fix the duplicate-pass framework bug surfaced in the Phase A iso run
(see ``project_duplicate_pass_resurrection_2026_05_03.md``). Under
E1-D the rejection ``ToolMessage`` frames the next response as an
**additive delta** on top of the agent's previous reply: continue
from where the previous reply left off and add only the gap items as
new chat content. Together the previous reply plus the delta complete
the deliverable as the user reads it, so the agent does not bundle a
full re-narration into a second user-facing pass.

The unit tests below exercise the observable behaviours of the
middleware in isolation; an LLM is **not** invoked. The judge is
mocked to return deterministic verdicts so the tests verify only the
control-flow surface that decides whether the advance is allowed,
blocked, or short-circuited, and the wording contract that the
rejection body honours the additive-delta framing while never
redirecting content to workspace (which would conflict with the
project's "judge = user" principle).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from core.brand_strategy.content_check import (
    ContentCheckAdvanceMiddleware,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_advance_request(messages: list[Any]) -> Any:
    """Build a ``ToolCallRequest`` shaped object for an advance call.

    The middleware reads ``request.tool_call`` and
    ``request.state.get("messages", ...)``. The shape mirrors what
    ``langchain.agents.middleware`` constructs at runtime; we use a
    light ``MagicMock`` rather than an actual ``ToolCallRequest`` so
    the tests do not depend on the exact langchain version.

    Args:
        messages: The conversation history that will be exposed via
            ``request.state["messages"]``. Production code reads recent
            ``AIMessage`` text from this list.

    Returns:
        A mock object with ``tool_call`` and ``state`` attributes that
        the middleware can introspect.
    """
    request = MagicMock()
    request.tool_call = {
        "name": "report_progress",
        "args": {"advance": True},
        "id": "test-tool-call-id-001",
    }
    request.state = {"messages": messages}
    return request


def _ai_message_with_text(text: str) -> AIMessage:
    """Return an ``AIMessage`` carrying the given user-facing text.

    Args:
        text: The user-facing string the test wants to expose to the
            middleware as recent agent output.

    Returns:
        A langchain ``AIMessage`` with string content.
    """
    return AIMessage(content=text)


def _phase_session_stub(phase: str) -> Any:
    """Build a stub for ``get_active_session`` returning ``phase``.

    Args:
        phase: One of the keys in ``PHASE_DELIVERABLE_SPECS``
            (``"phase_0_5"``, ``"phase_1"``, ``"phase_2"``,
            ``"phase_4"``, ``"phase_5"``) or any other string for the
            ungated path.

    Returns:
        A simple object exposing ``current_phase`` as the configured
        phase identifier.
    """
    session = MagicMock()
    session.current_phase = phase
    return session


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pass_verdict_allows_handler_to_run() -> None:
    """When the judge passes, the handler runs untouched.

    This is the negative control: confirms the middleware does not
    inject any extra ToolMessage when content is sufficient. If a
    duplicate-pass surfaces in production but this test still passes,
    the bug is upstream of the judge verdict.
    """
    middleware = ContentCheckAdvanceMiddleware()
    request = _build_advance_request([_ai_message_with_text("Phase 0.5 content here")])

    handler = AsyncMock(return_value="HANDLER_RAN")

    with (
        patch(
            "core.brand_strategy.content_check.get_active_session",
            return_value=_phase_session_stub("phase_0_5"),
        ),
        patch.object(
            middleware,
            "_get_llm",
            return_value=MagicMock(
                acomplete=AsyncMock(
                    return_value=MagicMock(
                        text='{"passes": true, "missing": "", "reasoning": "ok"}'
                    )
                )
            ),
        ),
    ):
        result = await middleware.awrap_tool_call(request, handler)

    handler.assert_awaited_once_with(request)
    assert result == "HANDLER_RAN"


@pytest.mark.asyncio
async def test_phase_5_missing_artifact_blocks_advance_before_judge() -> None:
    """Phase 5 cannot complete while a promised artifact category is missing.

    The Phase 5 artifact gate is deterministic and runs before the LLM
    judge. This pins the process contract surfaced by the Linh
    acceptance trace: a slide outline in chat must not substitute for a
    generated PPTX artifact in the current-session manifest.
    """
    middleware = ContentCheckAdvanceMiddleware()
    request = _build_advance_request(
        [_ai_message_with_text("Here is the final strategy and artifact summary.")]
    )

    handler = AsyncMock()

    with (
        patch(
            "core.brand_strategy.content_check.get_active_session",
            return_value=_phase_session_stub("phase_5"),
        ),
        patch(
            "core.brand_strategy.content_check."
            "DeliverableDispatchGuardMiddleware._current_session_artifact_categories",
            return_value={"images", "documents", "spreadsheets"},
        ),
        patch.object(middleware, "_get_llm") as get_llm,
    ):
        result = await middleware.awrap_tool_call(request, handler)

    handler.assert_not_awaited()
    get_llm.assert_not_called()
    assert isinstance(result, ToolMessage)
    assert "Cannot complete Phase 5 yet" in result.content
    assert "presentations" in result.content
    assert "generated PPTX file" in result.content
    assert 'list_artifacts(scope="current_session")' in result.content


@pytest.mark.asyncio
async def test_phase_5_complete_artifacts_continue_to_content_judge() -> None:
    """When Phase 5 artifacts are complete, the normal content judge still applies."""
    middleware = ContentCheckAdvanceMiddleware()
    request = _build_advance_request(
        [_ai_message_with_text("Phase 5 text includes Brand Key, KPI, and roadmap.")]
    )

    handler = AsyncMock(return_value="HANDLER_RAN")

    with (
        patch(
            "core.brand_strategy.content_check.get_active_session",
            return_value=_phase_session_stub("phase_5"),
        ),
        patch(
            "core.brand_strategy.content_check."
            "DeliverableDispatchGuardMiddleware._current_session_artifact_categories",
            return_value={"images", "documents", "presentations", "spreadsheets"},
        ),
        patch.object(
            middleware,
            "_get_llm",
            return_value=MagicMock(
                acomplete=AsyncMock(
                    return_value=MagicMock(
                        text='{"passes": true, "missing": "", "reasoning": "ok"}'
                    )
                )
            ),
        ),
    ):
        result = await middleware.awrap_tool_call(request, handler)

    handler.assert_awaited_once_with(request)
    assert result == "HANDLER_RAN"


@pytest.mark.asyncio
async def test_fail_verdict_returns_rejection_tool_message() -> None:
    """A FAIL verdict short-circuits the handler with an additive-delta rejection.

    Under E1-D the rejection body frames the next response as an
    additive delta on top of the previous reply: "continue from where
    your previous reply left off" and "add only the gap items". The
    judge's ``missing`` field still surfaces verbatim so the agent
    knows which gap items to append. If the framing changes the
    rejection contract, this test pins the prompt-level cues so any
    proposed fix must update them deliberately rather than silently.
    """
    middleware = ContentCheckAdvanceMiddleware()
    request = _build_advance_request([_ai_message_with_text("Pass 1 brief only")])

    handler = AsyncMock()

    with (
        patch(
            "core.brand_strategy.content_check.get_active_session",
            return_value=_phase_session_stub("phase_0_5"),
        ),
        patch.object(
            middleware,
            "_get_llm",
            return_value=MagicMock(
                acomplete=AsyncMock(
                    return_value=MagicMock(
                        text=(
                            '{"passes": false, '
                            '"missing": "Brand Inventory across '
                            'visual/verbal/experiential", '
                            '"reasoning": "shallow"}'
                        )
                    )
                )
            ),
        ),
    ):
        result = await middleware.awrap_tool_call(request, handler)

    handler.assert_not_awaited()
    assert isinstance(result, ToolMessage)
    assert "Continue from where your previous reply left off" in result.content
    assert "add only the gap items" in result.content
    assert "Brand Inventory" in result.content


@pytest.mark.asyncio
async def test_fail_verdict_does_not_redirect_to_workspace() -> None:
    """Regression: rejection ToolMessage never redirects content to workspace.

    The project's "judge = user" principle requires the deliverable to
    live in user-facing chat, because the cross-system fairness
    guarantee assumes the judge reads the same chat the user reads —
    never an internal workspace, file, or silent-mode artifact. This
    test pins that contract: the rejection body must not contain
    workspace-, silent-, or file-redirect phrases. Re-narration
    discouragement language ("redundant", "previous reply", "delta",
    "continue") IS allowed because that framing keeps the content in
    chat as an additive delta rather than redirecting it elsewhere.
    """
    middleware = ContentCheckAdvanceMiddleware()
    request = _build_advance_request([_ai_message_with_text("Pass 1 brief only")])

    with (
        patch(
            "core.brand_strategy.content_check.get_active_session",
            return_value=_phase_session_stub("phase_1"),
        ),
        patch.object(
            middleware,
            "_get_llm",
            return_value=MagicMock(
                acomplete=AsyncMock(
                    return_value=MagicMock(
                        text=(
                            '{"passes": false, "missing": "competitive landscape", '
                            '"reasoning": "x"}'
                        )
                    )
                )
            ),
        ),
    ):
        result = await middleware.awrap_tool_call(request, AsyncMock())

    assert isinstance(result, ToolMessage)
    body = result.content if isinstance(result.content, str) else str(result.content)
    forbidden_phrases = (
        "workspace",
        "silent",
        "file",
    )
    for phrase in forbidden_phrases:
        assert phrase.lower() not in body.lower(), (
            f"Unexpected workspace-redirect phrase '{phrase}' present in "
            "rejection body. The judge=user principle requires deliverable "
            "content to stay in user-facing chat."
        )


@pytest.mark.asyncio
async def test_judge_failure_falls_open_to_handler() -> None:
    """When the judge raises, the middleware allows advance (fail-open).

    Confirms a degraded judge does not contribute to duplicate-pass
    behaviour: it simply lets the original advance through.
    """
    middleware = ContentCheckAdvanceMiddleware()
    request = _build_advance_request([_ai_message_with_text("Pass 1")])

    handler = AsyncMock(return_value="HANDLER_RAN")

    with (
        patch(
            "core.brand_strategy.content_check.get_active_session",
            return_value=_phase_session_stub("phase_0_5"),
        ),
        patch.object(
            middleware,
            "_get_llm",
            return_value=MagicMock(
                acomplete=AsyncMock(side_effect=RuntimeError("judge backend down"))
            ),
        ),
    ):
        result = await middleware.awrap_tool_call(request, handler)

    handler.assert_awaited_once_with(request)
    assert result == "HANDLER_RAN"


@pytest.mark.asyncio
async def test_unrelated_tool_call_passes_through() -> None:
    """Non-advance tool calls bypass the judge entirely.

    Pins the early-exit so future changes do not accidentally route
    every tool call (e.g. ``write_todos``, ``edit_file``) through the
    judge — that would explode latency and create new duplicate-pass
    shapes.
    """
    middleware = ContentCheckAdvanceMiddleware()
    request = MagicMock()
    request.tool_call = {"name": "write_todos", "args": {}, "id": "x"}
    request.state = {"messages": []}

    handler = AsyncMock(return_value="HANDLER_RAN")
    result = await middleware.awrap_tool_call(request, handler)

    handler.assert_awaited_once_with(request)
    assert result == "HANDLER_RAN"
