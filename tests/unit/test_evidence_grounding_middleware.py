"""Unit tests for retrieval evidence-boundary middleware."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from shared.agent_middlewares.evidence_grounding import EvidenceGroundingMiddleware


def _tool_request(tool_name: str) -> ToolCallRequest:
    return ToolCallRequest(
        tool_call={
            "name": tool_name,
            "args": {"query": "Signature restaurant branch relationship"},
            "id": "call_1",
        },
        tool=None,
        state={},
        runtime=None,  # type: ignore[arg-type]
    )


def _model_response(text: str, tool_calls: list[dict[str, Any]] | None = None) -> Any:
    message = AIMessage(content=text)
    message.tool_calls = tool_calls or []
    response = MagicMock()
    response.result = [message]
    return response


def _model_request(messages: list[object] | None = None) -> Any:
    request = MagicMock()
    request.messages = []
    request.state = {"messages": messages or []}
    return request


def _prior_market_research_dispatch() -> AIMessage:
    dispatch = AIMessage(content="")
    dispatch.tool_calls = [
        {
            "name": "task",
            "args": {"subagent_type": "market-research"},
            "id": "call_research",
        }
    ]
    return dispatch


def _prior_social_media_dispatch() -> AIMessage:
    dispatch = AIMessage(content="")
    dispatch.tool_calls = [
        {
            "name": "task",
            "args": {"subagent_type": "social-media-analyst"},
            "id": "call_social",
        }
    ]
    return dispatch


def test_appends_evidence_boundary_to_knowledge_graph_result() -> None:
    middleware = EvidenceGroundingMiddleware()

    def handler(request: ToolCallRequest) -> ToolMessage:
        return ToolMessage(
            "KG says Signature is a branding cue.",
            tool_call_id="call_1",
        )

    result = middleware.wrap_tool_call(_tool_request("search_knowledge_graph"), handler)

    assert isinstance(result, ToolMessage)
    assert "KG says Signature is a branding cue." in str(result.content)
    assert "Evidence boundary:" in str(result.content)
    assert "does not verify current public market facts" in str(result.content)
    assert "market-research" in str(result.content)
    assert "specific public brand or venue relationship" in str(result.content)
    assert "before asking the user" in str(result.content)
    assert "unverified hypothesis" in str(result.content)
    assert "report_progress(brand_name=...)" in str(result.content)
    assert "Defer concept, audience, budget" in str(result.content)


def test_leaves_non_theory_tool_result_unchanged() -> None:
    middleware = EvidenceGroundingMiddleware()

    def handler(request: ToolCallRequest) -> ToolMessage:
        return ToolMessage("Updated metadata.", tool_call_id="call_1")

    result = middleware.wrap_tool_call(_tool_request("report_progress"), handler)

    assert isinstance(result, ToolMessage)
    assert result.content == "Updated metadata."


def test_appends_boundary_to_market_research_task_result() -> None:
    middleware = EvidenceGroundingMiddleware()

    def handler(request: ToolCallRequest) -> ToolMessage:
        return ToolMessage("Found two public listings.", tool_call_id="call_1")

    request = _tool_request("task")
    request.tool_call["args"] = {
        "subagent_type": "market-research",
        "description": "Validate Chuyện Ba Bữa Signature.",
    }

    result = middleware.wrap_tool_call(request, handler)

    assert isinstance(result, ToolMessage)
    assert "Found two public listings." in str(result.content)
    assert "Market-research evidence boundary:" in str(result.content)
    assert "source, URL, platform" in str(result.content)
    assert "Treat this specialist result as inconclusive" in str(result.content)
    assert "inconclusive" in str(result.content)
    assert "NO_SOURCE_LEDGER_DETECTED" in str(result.content)


def test_appends_boundary_to_social_media_task_result() -> None:
    middleware = EvidenceGroundingMiddleware()

    def handler(request: ToolCallRequest) -> ToolMessage:
        return ToolMessage(
            "Profile exists, but no visual feed was inspected.",
            tool_call_id="call_1",
        )

    request = _tool_request("task")
    request.tool_call["args"] = {
        "subagent_type": "social-media-analyst",
        "description": "Audit current content fit for Signature.",
    }

    result = middleware.wrap_tool_call(request, handler)

    assert isinstance(result, ToolMessage)
    assert "Profile exists" in str(result.content)
    assert "Social-media evidence boundary:" in str(result.content)
    assert "browser-observed" in str(result.content)
    assert "story/video quality" in str(result.content)
    assert "evidence gaps or hypotheses" in str(result.content)


def test_marks_market_research_result_with_source_markers_only() -> None:
    middleware = EvidenceGroundingMiddleware()

    def handler(request: ToolCallRequest) -> ToolMessage:
        return ToolMessage(
            "Fact: Signature listing exists.\nSource: Google Maps\nURL: https://example.test",
            tool_call_id="call_1",
        )

    request = _tool_request("task")
    request.tool_call["args"] = {
        "subagent_type": "market-research",
        "description": "Validate Chuyện Ba Bữa Signature.",
    }

    result = middleware.wrap_tool_call(request, handler)

    assert isinstance(result, ToolMessage)
    assert "SOURCE_MARKERS_ONLY_DETECTED" in str(result.content)
    assert "did not provide exact quote/snippet support" in str(result.content)


def test_marks_market_research_result_with_source_quote_ledger() -> None:
    middleware = EvidenceGroundingMiddleware()

    def handler(request: ToolCallRequest) -> ToolMessage:
        return ToolMessage(
            "| Public fact | Source/URL | Exact quote/snippet | Status |\n"
            "| --- | --- | --- | --- |\n"
            "| Signature listing exists | Google Maps https://example.test | "
            '"Chuyện Ba Bữa Signature is listed at Saigon Marina IFC" | Verified |',
            tool_call_id="call_1",
        )

    request = _tool_request("task")
    request.tool_call["args"] = {
        "subagent_type": "market-research",
        "description": "Validate Chuyện Ba Bữa Signature.",
    }

    result = middleware.wrap_tool_call(request, handler)

    assert isinstance(result, ToolMessage)
    assert "SOURCE_QUOTE_LEDGER_DETECTED" in str(result.content)
    assert "source marker and exact quote or snippet" in str(result.content)


def test_injects_opening_restaurant_research_before_model_call() -> None:
    middleware = EvidenceGroundingMiddleware()
    request = _model_request(
        [
            HumanMessage(
                content=(
                    "Tôi muốn làm brand strategy cho nhà hàng Chuyện Ba Bữa Signature á"
                )
            )
        ]
    )
    response = _model_response(
        "",
        tool_calls=[
            {
                "name": "task",
                "args": {"subagent_type": "market-research"},
                "id": "call_research",
            }
        ],
    )
    calls = 0
    seen_messages: list[object] = []

    def handler(model_request: Any) -> Any:
        nonlocal calls
        calls += 1
        seen_messages.extend(model_request.messages)
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert calls == 1
    assert any(
        isinstance(message, SystemMessage)
        and "Opening Public-Brand Research" in str(message.content)
        for message in seen_messages
    )
    assert request.state["_evidence_opening_research_injected"] is True


def test_injects_opening_research_from_dict_messages() -> None:
    middleware = EvidenceGroundingMiddleware()
    request = _model_request(
        [
            {
                "role": "user",
                "content": (
                    "Tôi muốn làm brand strategy cho nhà hàng Chuyện Ba Bữa Signature á"
                ),
            }
        ]
    )
    response = _model_response(
        "",
        tool_calls=[
            {
                "name": "task",
                "args": {"subagent_type": "market-research"},
                "id": "call_research",
            }
        ],
    )
    calls = 0

    def handler(model_request: Any) -> Any:
        nonlocal calls
        calls += 1
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert calls == 1
    assert any(
        isinstance(message, SystemMessage)
        and "Opening Public-Brand Research" in str(message.content)
        for message in request.messages
    )


def test_injects_market_research_render_reminder_after_dispatch() -> None:
    middleware = EvidenceGroundingMiddleware()
    tool_result = ToolMessage(
        "No public source ledger was returned.",
        tool_call_id="call_research",
    )
    request = _model_request([_prior_market_research_dispatch(), tool_result])
    response = _model_response(
        "Tôi chưa có nguồn xác nhận nên xem đây là giả thuyết "
        "cần anh xác nhận."
    )
    calls = 0
    seen_messages: list[object] = []

    def handler(model_request: Any) -> Any:
        nonlocal calls
        calls += 1
        seen_messages.extend(model_request.messages)
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert calls == 1
    assert any(
        isinstance(message, SystemMessage)
        and "Market Research Evidence Render" in str(message.content)
        and "NO_SOURCE_LEDGER_DETECTED" in str(message.content)
        and "SOURCE_MARKERS_ONLY_DETECTED" in str(message.content)
        and "SOURCE_QUOTE_LEDGER_DETECTED" in str(message.content)
        and "source ledger internal" in str(message.content)
        and "vague unsourced discovery phrases" in str(message.content)
        and "Detected specialist source ledger status: NO_SOURCE_LEDGER_DETECTED"
        in str(message.content)
        for message in seen_messages
    )
    assert request.state["_evidence_render_injected"] is True


def test_injects_social_media_render_reminder_after_dispatch() -> None:
    middleware = EvidenceGroundingMiddleware()
    tool_result = ToolMessage(
        "Profile exists, but content surface was not observed.",
        tool_call_id="call_social",
    )
    request = _model_request([_prior_social_media_dispatch(), tool_result])
    response = _model_response("Social evidence should remain modality-bound.")
    calls = 0
    seen_messages: list[object] = []

    def handler(model_request: Any) -> Any:
        nonlocal calls
        calls += 1
        seen_messages.extend(model_request.messages)
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert calls == 1
    assert any(
        isinstance(message, SystemMessage)
        and "Social Media Evidence Render" in str(message.content)
        and "feed/grid aesthetics" in str(message.content)
        and "Detected social evidence modality status: NO_OBSERVATION_LEDGER_DETECTED"
        in str(message.content)
        for message in seen_messages
    )
    assert request.state["_evidence_social_render_injected"] is True


def test_social_media_render_reminder_detects_browser_observed_modality() -> None:
    middleware = EvidenceGroundingMiddleware()
    dispatch = _prior_social_media_dispatch()
    tool_result = ToolMessage(
        "Finding: recent reels show ambience mismatch. Modality: browser-observed.",
        tool_call_id="call_social",
    )
    request = _model_request([dispatch, tool_result])
    response = _model_response("Render reminder expected.")

    def handler(model_request: Any) -> Any:
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert any(
        isinstance(message, SystemMessage)
        and "Detected social evidence modality status: BROWSER_OBSERVED_DETECTED"
        in str(message.content)
        for message in request.messages
    )


def test_does_not_reinject_social_media_render_reminder() -> None:
    middleware = EvidenceGroundingMiddleware()
    tool_result = ToolMessage(
        "Profile exists, but content surface was not observed.",
        tool_call_id="call_social",
    )
    request = _model_request([_prior_social_media_dispatch(), tool_result])
    request.state["_evidence_social_render_injected"] = True
    response = _model_response("No extra reminder needed.")

    def handler(model_request: Any) -> Any:
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert request.messages == []


def test_detects_market_research_dispatch_from_additional_kwargs() -> None:
    middleware = EvidenceGroundingMiddleware()
    prior_dispatch = AIMessage(
        content="",
        additional_kwargs={
            "tool_calls": [
                {
                    "id": "call_research",
                    "function": {
                        "name": "task",
                        "arguments": '{"subagent_type": "market-research"}',
                    }
                }
            ]
        },
    )
    tool_result = ToolMessage(
        "Fact: listing exists. Source: Google Maps.",
        tool_call_id="call_research",
    )
    request = _model_request([prior_dispatch, tool_result])
    response = _model_response("Render reminder expected.")

    def handler(model_request: Any) -> Any:
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert any(
        isinstance(message, SystemMessage)
        and "Market Research Evidence Render" in str(message.content)
        for message in request.messages
    )


def test_detects_market_research_dispatch_from_tool_boundary() -> None:
    middleware = EvidenceGroundingMiddleware()
    tool_result = ToolMessage(
        "Summary.\n\n---\nMarket-research evidence boundary: cite sources.",
        tool_call_id="call_research",
    )
    request = _model_request([tool_result])
    response = _model_response("Render reminder expected.")

    def handler(model_request: Any) -> Any:
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert any(
        isinstance(message, SystemMessage)
        and "Market Research Evidence Render" in str(message.content)
        for message in request.messages
    )


def test_render_reminder_detects_source_marker_only_from_task_result() -> None:
    middleware = EvidenceGroundingMiddleware()
    dispatch = AIMessage(content="")
    dispatch.tool_calls = [
        {
            "name": "task",
            "args": {"subagent_type": "market-research"},
            "id": "call_research",
        }
    ]
    tool_result = ToolMessage(
        "Fact: listing exists. Source: Google Maps. URL: https://example.test",
        tool_call_id="call_research",
    )
    request = _model_request([dispatch, tool_result])
    response = _model_response("Render reminder expected.")

    def handler(model_request: Any) -> Any:
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert any(
        isinstance(message, SystemMessage)
        and "Detected specialist source ledger status: SOURCE_MARKERS_ONLY_DETECTED"
        in str(message.content)
        for message in request.messages
    )


def test_render_reminder_detects_source_quote_ledger_from_task_result() -> None:
    middleware = EvidenceGroundingMiddleware()
    dispatch = AIMessage(content="")
    dispatch.tool_calls = [
        {
            "name": "task",
            "args": {"subagent_type": "market-research"},
            "id": "call_research",
        }
    ]
    tool_result = ToolMessage(
        "| Public fact | Source/URL | Exact quote/snippet | Status |\n"
        "| --- | --- | --- | --- |\n"
        "| listing exists | Google Maps https://example.test | "
        '"Chuyện Ba Bữa Signature appears in the listing" | Verified |',
        tool_call_id="call_research",
    )
    request = _model_request([dispatch, tool_result])
    response = _model_response("Render reminder expected.")

    def handler(model_request: Any) -> Any:
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert any(
        isinstance(message, SystemMessage)
        and "Detected specialist source ledger status: SOURCE_QUOTE_LEDGER_DETECTED"
        in str(message.content)
        for message in request.messages
    )


def test_does_not_inject_market_render_after_unrelated_latest_tool() -> None:
    middleware = EvidenceGroundingMiddleware()
    dispatch = _prior_market_research_dispatch()
    research_result = ToolMessage(
        "Fact: listing exists. Source: Google Maps.",
        tool_call_id="call_research",
    )
    todo_result = ToolMessage(
        "Todo list updated.",
        tool_call_id="call_todo",
    )
    request = _model_request([dispatch, research_result, todo_result])
    response = _model_response("No repeated render reminder needed.")

    def handler(model_request: Any) -> Any:
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert request.messages == []


def test_render_reminder_treats_header_only_source_ledger_as_no_source() -> None:
    middleware = EvidenceGroundingMiddleware()
    dispatch = AIMessage(content="")
    dispatch.tool_calls = [
        {
            "name": "task",
            "args": {"subagent_type": "market-research"},
            "id": "call_research",
        }
    ]
    tool_result = ToolMessage(
        "| Public fact | Source/URL | Status |\n"
        "| --- | --- | --- |\n"
        "| Branch relationship | INCONCLUSIVE | Chưa rõ |",
        tool_call_id="call_research",
    )
    request = _model_request([dispatch, tool_result])
    response = _model_response("Render reminder expected.")

    def handler(model_request: Any) -> Any:
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert any(
        isinstance(message, SystemMessage)
        and "Detected specialist source ledger status: NO_SOURCE_LEDGER_DETECTED"
        in str(message.content)
        for message in request.messages
    )


def test_does_not_rewrite_user_facing_response_posthoc() -> None:
    middleware = EvidenceGroundingMiddleware()
    dispatch = _prior_market_research_dispatch()
    request = _model_request(
        [
            HumanMessage(
                content=(
                    "Tôi muốn làm brand strategy cho nhà hàng Chuyện Ba Bữa Signature á"
                )
            ),
            dispatch,
        ]
    )
    response = _model_response(
        "Chào bạn.\n\n"
        "Qua tìm hiểu sơ bộ, Chuyện Ba Bữa Signature tại Saigon Marina IFC "
        "đang theo đuổi phong cách Fusion hiện đại.\n\n"
        "Bạn giúp tôi xác nhận đây là brand mới hay repositioning nhé?"
    )
    original = str(response.result[-1].content)

    def handler(model_request: Any) -> Any:
        return response

    result = middleware.wrap_model_call(request, handler)
    content = str(result.result[-1].content)

    assert content == original


def test_leaves_sourced_public_fact_response_unchanged() -> None:
    middleware = EvidenceGroundingMiddleware()
    dispatch = _prior_market_research_dispatch()
    request = _model_request(
        [
            HumanMessage(content="I want brand strategy for Acme Restaurant."),
            dispatch,
        ]
    )
    original = (
        "Acme has a public listing in District 1 (Source: Google Maps). "
        "Let's confirm the scope."
    )
    response = _model_response(original)

    def handler(model_request: Any) -> Any:
        return response

    result = middleware.wrap_model_call(request, handler)

    assert str(result.result[-1].content) == original


def test_does_not_reinject_market_research_render_reminder() -> None:
    middleware = EvidenceGroundingMiddleware()
    request = _model_request([_prior_market_research_dispatch()])
    request.state["_evidence_render_injected"] = True
    response = _model_response("No extra reminder needed.")
    calls = 0

    def handler(model_request: Any) -> Any:
        nonlocal calls
        calls += 1
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert calls == 1
    assert request.messages == []


def test_reminder_text_is_not_counted_as_market_research_dispatch() -> None:
    middleware = EvidenceGroundingMiddleware()
    request = _model_request(
        [
            SystemMessage(
                content='Call `task(subagent_type="market-research")` before answering.'
            ),
            HumanMessage(
                content=(
                    "Tôi muốn làm brand strategy cho nhà hàng Chuyện Ba Bữa Signature á"
                )
            ),
        ]
    )
    response = _model_response("Tool call expected next.")
    calls = 0

    def handler(model_request: Any) -> Any:
        nonlocal calls
        calls += 1
        return response

    result = middleware.wrap_model_call(request, handler)

    assert result is response
    assert calls == 1
    assert any(
        isinstance(message, SystemMessage)
        and "Opening Public-Brand Research" in str(message.content)
        and "source ledger" in str(message.content)
        and "INCONCLUSIVE" in str(message.content)
        for message in request.messages
    )
