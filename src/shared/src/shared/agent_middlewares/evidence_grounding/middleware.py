"""Add evidence-boundary reminders for public facts."""

from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable, Sequence
from typing import cast

from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
    ToolCallRequest,
)
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.types import Command
from loguru import logger

_THEORY_TOOL_NAMES = {
    "search_knowledge_graph",
    "search_document_library",
}

_EVIDENCE_BOUNDARY_NOTE = (
    "\n\n---\n"
    "Evidence boundary: this result grounds marketing theory or source passages only. "
    "It does not verify current public market facts, live branch relationships, "
    "openings, reviews, pricing, or location reality. When a specific public "
    "brand or venue relationship would determine the next strategy route, "
    "dispatch one bounded `market-research` pass for that narrow fact before "
    "asking the user. If the pass is unavailable or inconclusive, label the "
    "point as an unverified hypothesis and ask the user to confirm. In the user "
    "reply, first anchor a clearly named brand with "
    "`report_progress(brand_name=...)` when it has not been recorded yet, then "
    "ask only the scope branch/blocker needed now. Defer concept, audience, "
    "budget, and other optional intake until the branch is answered."
)
_MARKET_RESEARCH_BOUNDARY_NOTE = (
    "\n\n---\n"
    "Market-research evidence boundary: use current public facts from this "
    "specialist result only when the result names a source, URL, platform, or "
    "search result for that exact point. If a claim has no source, or the "
    "search result was empty, blocked, or inconclusive, do not present it as a "
    "verified market fact. Keep the source ledger available internally so you "
    "can cite it if the user asks or the fact becomes stakeholder-defendability "
    "critical. In normal chat, sources do not need to be shown beside every "
    "fact; the important rule is that verified public facts must be traceable "
    "to the specialist result, while inconclusive points stay as hypotheses or "
    "confirmation questions."
)
_URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)\S+")
_SOURCE_LABEL_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?"
    r"(?:source|sources|nguồn|nguon|platform|title|link|url)\s*:\s*(.+?)\s*$"
)
_SOURCE_PLACEHOLDER_RE = re.compile(
    r"(?i)\b("
    r"inconclusive|unknown|not found|no result|no source|unavailable|blocked|"
    r"empty|none|n/a|chưa rõ|chua ro|không rõ|khong ro|không tìm thấy|"
    r"khong tim thay|không có|khong co|chưa xác thực|chua xac thuc"
    r")\b"
)
_SOURCE_PLATFORM_RE = re.compile(
    r"(?i)\b("
    r"google maps|facebook|fanpage|foody|riviu|tripadvisor|restaurant guru|"
    r"website|official site|instagram|tiktok|báo|bao|article|listing"
    r")\b"
)
_SOURCE_HEADER_RE = re.compile(r"(?i)\b(source|nguồn|nguon|url|platform|status)\b")
_SOURCE_LEDGER_AVAILABLE_NOTE = (
    "\n\nSource ledger status: SOURCE_MARKERS_DETECTED. Use only the public "
    "details that appear directly beside those source markers. Demote any "
    "public detail that is not tied to a source marker into a hypothesis or an "
    "open confirmation question."
)
_SOURCE_LEDGER_MISSING_NOTE = (
    "\n\nSource ledger status: NO_SOURCE_LEDGER_DETECTED. Treat this specialist "
    "result as inconclusive for current public facts. In the next user-facing "
    "answer, do not state branch relationship, venue location, opening status, "
    "address/district, menu concept, public positioning, reviews, ratings, "
    "pricing, or traffic as facts. Use only a clearly marked working hypothesis "
    "from the brand name and ask the user to confirm the route."
)

_PUBLIC_PROJECT_OPENING_RE = re.compile(
    r"(?i)(brand strategy|chiến lược thương hiệu|chien luoc thuong hieu)"
    r".{0,120}(nhà hàng|nha hang|quán|quan|cafe|thương hiệu|thuong hieu)"
)

_RETRY_MARKET_RESEARCH_RENDER_REMINDER = (
    "## Market Research Evidence Render\n"
    "A market-research pass has happened in this turn. In the next user-facing "
    "answer, run a source-ledger check before writing any public detail. If "
    "the specialist result says `NO_SOURCE_LEDGER_DETECTED`, do not say you "
    '"found", "observed", or "researched" concrete public facts; say the '
    "quick public check was not conclusive enough to treat those details as "
    "verified. If it says `SOURCE_MARKERS_DETECTED`, use only details that are "
    "directly tied to a named source/URL/platform in that result. Keep the "
    "source ledger internal unless the user asks for sources or the fact must "
    "be defended to stakeholders. Do not use vague unsourced discovery phrases "
    "in any language as a substitute for source grounding. Keep the turn "
    "useful: anchor the brand, give the safest working hypothesis, and ask only "
    "the branch/blocker needed now."
)
_RETRY_OPENING_RESEARCH_REMINDER = (
    "## Opening Public-Brand Research\n"
    "The user's opening names a specific public-facing F&B project. Before "
    'answering, call `task(subagent_type="market-research", description=...)` '
    "with a narrow validation brief: check whether the named venue/brand has "
    "current public evidence, what the public relationship to the base brand "
    "appears to be, and what source-backed facts are safe to use. Limit the "
    "brief to 2-3 search sources and require a compact source ledger: public "
    "fact, source/platform/URL, and status. If a fact cannot be sourced in that "
    "budget, the ledger should mark it `INCONCLUSIVE`. After the specialist "
    "returns, anchor the brand name, state only source-backed findings or "
    "clearly marked hypotheses, and ask the scope branch/blocker."
)


class EvidenceGroundingMiddleware(AgentMiddleware):
    """Keep theory retrieval results from being mistaken for live market evidence."""

    @staticmethod
    def _should_annotate(request: ToolCallRequest) -> bool:
        return str(request.tool_call.get("name", "")) in _THEORY_TOOL_NAMES

    @staticmethod
    def _is_market_research_task(request: ToolCallRequest) -> bool:
        args = request.tool_call.get("args", {})
        return (
            str(request.tool_call.get("name", "")) == "task"
            and args.get("subagent_type") == "market-research"
        )

    @staticmethod
    def _with_boundary_note(result: ToolMessage, note: str) -> ToolMessage:
        content = str(result.content)
        marker = (
            "Market-research evidence boundary:"
            if "Market-research evidence boundary:" in note
            else "Evidence boundary:"
        )
        if marker in content:
            return result

        updated_content = content.rstrip() + note
        try:
            return result.model_copy(update={"content": updated_content})
        except AttributeError:
            return ToolMessage(
                content=updated_content,
                tool_call_id=str(getattr(result, "tool_call_id", "")),
            )

    @staticmethod
    def _is_placeholder_source(value: str) -> bool:
        stripped = value.strip(" |:-").strip()
        return not stripped or bool(_SOURCE_PLACEHOLDER_RE.search(stripped))

    @classmethod
    def _has_usable_source_marker(cls, content: str) -> bool:
        if _URL_RE.search(content):
            return True

        for match in _SOURCE_LABEL_RE.finditer(content):
            if not cls._is_placeholder_source(match.group(1)):
                return True

        for line in content.splitlines():
            if "|" not in line:
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                continue
            if all(set(cell) <= {"-", ":"} for cell in cells if cell):
                continue
            if any(_SOURCE_HEADER_RE.search(cell) for cell in cells):
                continue
            source_cells = cells[1:-1] or cells[1:]
            if any(
                _SOURCE_PLATFORM_RE.search(cell)
                and not cls._is_placeholder_source(cell)
                for cell in source_cells
            ):
                return True
        return False

    @classmethod
    def _market_research_source_ledger_note(cls, content: str) -> str:
        if cls._has_usable_source_marker(content):
            logger.info(
                "EvidenceGroundingMiddleware marked market-research result "
                "SOURCE_MARKERS_DETECTED"
            )
            return _SOURCE_LEDGER_AVAILABLE_NOTE
        logger.info(
            "EvidenceGroundingMiddleware marked market-research result "
            "NO_SOURCE_LEDGER_DETECTED"
        )
        return _SOURCE_LEDGER_MISSING_NOTE

    @staticmethod
    def _market_research_tool_call_ids(messages: Sequence[object]) -> set[str]:
        call_ids: set[str] = set()
        for message in messages:
            tool_calls: list[object] = []
            if isinstance(message, dict):
                tool_calls.extend(message.get("tool_calls") or [])
            else:
                tool_calls.extend(getattr(message, "tool_calls", None) or [])
                additional_kwargs = getattr(message, "additional_kwargs", {}) or {}
                tool_calls.extend(additional_kwargs.get("tool_calls", []) or [])

            for tool_call in tool_calls:
                if not EvidenceGroundingMiddleware._tool_call_is_market_research(
                    tool_call
                ):
                    continue
                if isinstance(tool_call, dict):
                    call_id = tool_call.get("id") or tool_call.get("tool_call_id")
                    if call_id:
                        call_ids.add(str(call_id))
        return call_ids

    @classmethod
    def _market_research_result_texts(cls, request: ModelRequest) -> list[str]:
        messages = request.state.get("messages", [])
        call_ids = cls._market_research_tool_call_ids(messages)
        if not call_ids:
            return []

        texts: list[str] = []
        for message in messages:
            if isinstance(message, dict):
                message_type = str(message.get("type") or message.get("role") or "")
                tool_call_id = message.get("tool_call_id")
                if message_type not in {"tool", "toolmessage"}:
                    continue
                if tool_call_id and str(tool_call_id) not in call_ids:
                    continue
                content = str(message.get("content", ""))
                if content.strip():
                    texts.append(content)
                continue

            if not cls._tool_message_is_tool_message(message):
                continue
            tool_call_id = getattr(message, "tool_call_id", "")
            if tool_call_id and str(tool_call_id) not in call_ids:
                continue
            content = str(getattr(message, "content", ""))
            if content.strip():
                texts.append(content)
        return texts

    @staticmethod
    def _tool_message_is_tool_message(message: object) -> bool:
        message_type = getattr(message, "type", "")
        class_name = message.__class__.__name__
        return message_type == "tool" or class_name == "ToolMessage"

    @classmethod
    def _market_research_source_status(cls, request: ModelRequest) -> str:
        texts = cls._market_research_result_texts(request)
        if not texts:
            return "NO_SOURCE_LEDGER_DETECTED"
        if any(cls._has_usable_source_marker(text) for text in texts):
            return "SOURCE_MARKERS_DETECTED"
        return "NO_SOURCE_LEDGER_DETECTED"

    @classmethod
    def _market_research_render_reminder(cls, request: ModelRequest) -> str:
        status = cls._market_research_source_status(request)
        return (
            _RETRY_MARKET_RESEARCH_RENDER_REMINDER
            + "\n\nDetected specialist source ledger status: "
            + status
            + ". This detected status is the operational source boundary for "
            "the next user-facing answer."
        )

    @staticmethod
    def _tool_call_is_market_research(tool_call: object) -> bool:
        if not isinstance(tool_call, dict):
            return False

        name = tool_call.get("name")
        args = tool_call.get("args") or {}
        function = tool_call.get("function")
        if isinstance(function, dict):
            name = name or function.get("name")
            args = args or function.get("arguments") or {}

        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        if not isinstance(args, dict):
            return False

        return name == "task" and args.get("subagent_type") == "market-research"

    @staticmethod
    def _tool_message_is_market_research_boundary(message: object) -> bool:
        message_type = getattr(message, "type", "")
        class_name = message.__class__.__name__
        if message_type != "tool" and class_name != "ToolMessage":
            return False
        return "Market-research evidence boundary:" in str(
            getattr(message, "content", "")
        )

    @staticmethod
    def _has_market_research_dispatch(request: ModelRequest) -> bool:
        messages = request.state.get("messages", [])
        for message in messages:
            if isinstance(message, dict):
                tool_calls = message.get("tool_calls") or []
                for tool_call in tool_calls:
                    if EvidenceGroundingMiddleware._tool_call_is_market_research(
                        tool_call
                    ):
                        return True
                content = str(message.get("content", ""))
                if "Market-research evidence boundary:" in content:
                    return True
                continue

            tool_calls = getattr(message, "tool_calls", None) or []
            for tool_call in tool_calls:
                if EvidenceGroundingMiddleware._tool_call_is_market_research(tool_call):
                    return True
            additional_kwargs = getattr(message, "additional_kwargs", {}) or {}
            for tool_call in additional_kwargs.get("tool_calls", []) or []:
                if EvidenceGroundingMiddleware._tool_call_is_market_research(tool_call):
                    return True
            if EvidenceGroundingMiddleware._tool_message_is_market_research_boundary(
                message
            ):
                return True
        return False

    @staticmethod
    def _latest_human_text(request: ModelRequest) -> str:
        messages = request.state.get("messages", []) or getattr(request, "messages", [])
        for message in reversed(messages):
            if isinstance(message, dict):
                message_type = str(
                    message.get("type") or message.get("role") or ""
                ).lower()
                if message_type not in {"human", "user"}:
                    continue
                content = message.get("content", "")
                return content if isinstance(content, str) else str(content)

            message_type = getattr(message, "type", "")
            class_name = message.__class__.__name__
            if message_type != "human" and class_name != "HumanMessage":
                continue
            content = getattr(message, "content", "")
            if isinstance(content, str):
                return content
        return ""

    @classmethod
    def _should_inject_opening_research(
        cls,
        request: ModelRequest,
    ) -> bool:
        if cls._has_market_research_dispatch(request):
            return False
        if request.state.get("_evidence_opening_research_injected"):
            return False
        return bool(_PUBLIC_PROJECT_OPENING_RE.search(cls._latest_human_text(request)))

    @classmethod
    def _should_inject_market_research_render(
        cls,
        request: ModelRequest,
    ) -> bool:
        if not cls._has_market_research_dispatch(request):
            return False
        if request.state.get("_evidence_render_injected"):
            return False
        return True

    @classmethod
    def _inject_pre_call_reminder(cls, request: ModelRequest) -> None:
        if cls._should_inject_opening_research(request):
            request.messages.append(
                SystemMessage(content=_RETRY_OPENING_RESEARCH_REMINDER)
            )
            cast(dict[str, object], request.state)[
                "_evidence_opening_research_injected"
            ] = True
            logger.info(
                "EvidenceGroundingMiddleware injected opening research reminder"
            )
            return

        if cls._should_inject_market_research_render(request):
            request.messages.append(
                SystemMessage(content=cls._market_research_render_reminder(request))
            )
            cast(dict[str, object], request.state)["_evidence_render_injected"] = True
            logger.info(
                "EvidenceGroundingMiddleware injected market-research render reminder"
            )

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Inject evidence guidance before the model chooses tools or final text."""
        self._inject_pre_call_reminder(request)
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """Async pre-call injection for evidence guidance."""
        self._inject_pre_call_reminder(request)
        return await handler(request)

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Annotate theory retrieval output with evidence-boundary guidance."""
        result = handler(request)
        if not isinstance(result, ToolMessage):
            return result
        if self._should_annotate(request):
            return self._with_boundary_note(result, _EVIDENCE_BOUNDARY_NOTE)
        if self._is_market_research_task(request):
            return self._with_boundary_note(
                result,
                _MARKET_RESEARCH_BOUNDARY_NOTE
                + self._market_research_source_ledger_note(str(result.content)),
            )
        return result

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        """Annotate async theory retrieval output with evidence-boundary guidance."""
        result = await handler(request)
        if not isinstance(result, ToolMessage):
            return result
        if self._should_annotate(request):
            return self._with_boundary_note(result, _EVIDENCE_BOUNDARY_NOTE)
        if self._is_market_research_task(request):
            return self._with_boundary_note(
                result,
                _MARKET_RESEARCH_BOUNDARY_NOTE
                + self._market_research_source_ledger_note(str(result.content)),
            )
        return result
