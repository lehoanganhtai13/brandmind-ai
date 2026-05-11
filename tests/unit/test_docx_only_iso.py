"""Unit tests for the DOCX isolation diagnostic harness."""

from __future__ import annotations

from langchain_core.messages import AIMessage, ToolMessage

from evaluation.docx_only_iso import _content_is_valid, _content_preview, _inspect_messages


def test_inspect_messages_uses_latest_generate_document_result() -> None:
    """Select the final generate_document retry result when an earlier call failed."""
    valid_content = '{"cover": "Brand", "phase_5_output": {"roadmap": [], "measurement": []}}'
    messages = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "generate_document",
                    "args": {"content": '{"cover": "broken"'},
                    "id": "call_invalid",
                }
            ],
        ),
        ToolMessage(
            content="Invalid content JSON: Expecting ',' delimiter",
            tool_call_id="call_invalid",
        ),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "generate_document",
                    "args": {"content": valid_content},
                    "id": "call_valid",
                }
            ],
        ),
        ToolMessage(
            content=(
                "DOCX generated: "
                "/Users/lehoanganhtai/projects/brandmind-ai/brandmind-output/documents/"
                "brand/20260511_005643_brand_strategy.docx"
            ),
            tool_call_id="call_valid",
        ),
    ]

    inspection = _inspect_messages(messages)

    assert inspection["tool_calls"] == ["generate_document", "generate_document"]
    assert inspection["gen_doc_input"] == valid_content
    assert "DOCX generated" in inspection["gen_doc_result"]


def test_content_helpers_accept_structured_tool_args() -> None:
    """Structured content args are valid after the DOCX tool contract update."""
    content = {
        "cover": "Brand",
        "phase_5_output": {"roadmap": [], "measurement": []},
    }

    assert _content_is_valid(content) == (True, "")
    assert '"phase_5_output"' in _content_preview(content)
