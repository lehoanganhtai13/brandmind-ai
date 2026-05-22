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
_SOCIAL_MEDIA_BOUNDARY_NOTE = (
    "\n\n---\n"
    "Social-media evidence boundary: use profile, content, and visual facts "
    "from this specialist result only when each point is tied to a source, URL, "
    "platform, or explicit evidence modality such as `search/scrape-observed` "
    "or `browser-observed`. Logo meaning, feed/grid aesthetics, story/video "
    "quality, and audience-content fit require `browser-observed` evidence or "
    "source text that explicitly describes that exact observation. If the "
    "result used only lightweight search/scrape and did not observe the "
    "visual/content surface, keep those points as evidence gaps or hypotheses "
    "instead of verified social facts."
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
_QUOTE_LABEL_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?"
    r"(?:quote|snippet|evidence quote|exact quote|source quote|trích dẫn|"
    r"trich dan|đoạn trích|doan trich)\s*:\s*(.+?)\s*$"
)
_QUOTE_HEADER_RE = re.compile(
    r"(?i)\b(quote|snippet|evidence quote|exact quote|trích|trich|đoạn trích|"
    r"doan trich)\b"
)
_SOURCE_QUOTE_LEDGER_AVAILABLE_NOTE = (
    "\n\nSource ledger status: SOURCE_QUOTE_LEDGER_DETECTED. Use only the public "
    "details that appear directly beside a source marker and exact quote or "
    "snippet. Demote any public detail that is not tied to both into a "
    "hypothesis or an open confirmation question."
)
_SOURCE_MARKERS_ONLY_NOTE = (
    "\n\nSource ledger status: SOURCE_MARKERS_ONLY_DETECTED. The specialist "
    "named a source, URL, platform, or query, but did not provide exact "
    "quote/snippet support for each public fact. Treat public details as "
    "tentative unless the fact itself is directly supported by the returned "
    "source text."
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
    "verified. If it says `SOURCE_MARKERS_ONLY_DETECTED`, use the source as a "
    "directional clue only and avoid precise public facts unless the exact "
    "supporting text is present. If it says `SOURCE_QUOTE_LEDGER_DETECTED`, use "
    "only details that are directly tied to a named source/URL/platform and "
    "quote/snippet in that result. Keep the source ledger internal unless the "
    "user asks for sources or the fact must be defended to stakeholders. Do not "
    "use vague unsourced discovery phrases in any language as a substitute for "
    "source grounding. Keep the turn useful: anchor the brand, give the safest "
    "working hypothesis, and ask only the branch/blocker needed now."
)
_RETRY_SOCIAL_MEDIA_RENDER_REMINDER = (
    "## Social Media Evidence Render\n"
    "A social-media-analyst pass has happened in this turn. Before the next "
    "user-facing answer, run a modality check: use social/profile/content facts "
    "only when the specialist tied them to a source, URL, platform, or evidence "
    "modality. Treat logo meaning, feed/grid aesthetics, story/video quality, "
    "and audience-content fit as verified only when the result is "
    "`browser-observed` or the returned source text explicitly describes that "
    "observation. If the specialist marked a point as `not observed`, blocked, "
    "or inconclusive, present it as an evidence gap or ask for user/media "
    "confirmation. Keep the response useful and concise; do not turn modality "
    "limits into a long citation lecture unless the user asks."
)
_RETRY_OPENING_RESEARCH_REMINDER = (
    "## Opening Public-Brand Research\n"
    "The user's opening names a specific public-facing F&B project. Before "
    'answering, call `task(subagent_type="market-research", description=...)` '
    "with a narrow validation brief: check whether the named venue/brand has "
    "current public evidence, what the public relationship to the base brand "
    "appears to be, and what source-backed facts are safe to use. Limit the "
    "brief to 2-3 search sources and require a compact source ledger: public "
    "fact, source/platform/URL or query, exact quote/snippet, and status. If a "
    "fact cannot be sourced with an exact quote or snippet in that budget, the "
    "ledger should mark it `INCONCLUSIVE`. After the specialist returns, anchor "
    "the brand name, state only quote-backed findings or clearly marked "
    "hypotheses, and ask the scope branch/blocker."
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
    def _is_social_media_task(request: ToolCallRequest) -> bool:
        args = request.tool_call.get("args", {})
        return (
            str(request.tool_call.get("name", "")) == "task"
            and args.get("subagent_type") == "social-media-analyst"
        )

    @staticmethod
    def _with_boundary_note(result: ToolMessage, note: str) -> ToolMessage:
        content = str(result.content)
        if "Market-research evidence boundary:" in note:
            marker = "Market-research evidence boundary:"
        elif "Social-media evidence boundary:" in note:
            marker = "Social-media evidence boundary:"
        else:
            marker = "Evidence boundary:"
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
    def _has_usable_quote_marker(cls, content: str) -> bool:
        for match in _QUOTE_LABEL_RE.finditer(content):
            if cls._is_usable_quote(match.group(1)):
                return True

        quote_indices: set[int] = set()
        source_indices: set[int] = set()
        for line in content.splitlines():
            if "|" not in line:
                continue

            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                continue
            if all(set(cell) <= {"-", ":"} for cell in cells if cell):
                continue

            header_quote_indices = {
                index
                for index, cell in enumerate(cells)
                if _QUOTE_HEADER_RE.search(cell)
            }
            header_source_indices = {
                index
                for index, cell in enumerate(cells)
                if _SOURCE_HEADER_RE.search(cell)
            }
            if header_quote_indices and header_source_indices:
                quote_indices = header_quote_indices
                source_indices = header_source_indices
                continue

            if quote_indices and len(cells) > max(quote_indices | source_indices):
                quote_text = " ".join(cells[index] for index in quote_indices)
                source_text = " ".join(cells[index] for index in source_indices)
                if cls._is_usable_quote(quote_text) and (
                    _URL_RE.search(source_text)
                    or _SOURCE_PLATFORM_RE.search(source_text)
                    or not cls._is_placeholder_source(source_text)
                ):
                    return True

            if len(cells) >= 4 and any(
                cls._is_usable_quote(cell) for cell in cells[2:]
            ):
                source_cells = cells[1:-1] or cells[1:]
                if any(
                    _URL_RE.search(cell) or _SOURCE_PLATFORM_RE.search(cell)
                    for cell in source_cells
                ):
                    return True
        return False

    @staticmethod
    def _is_usable_quote(value: str) -> bool:
        stripped = value.strip(" |:-").strip()
        if len(stripped) < 8 or _SOURCE_PLACEHOLDER_RE.search(stripped):
            return False
        if _QUOTE_HEADER_RE.search(stripped) or _SOURCE_HEADER_RE.search(stripped):
            return False
        return any(character.isalpha() for character in stripped)

    @classmethod
    def _market_research_source_ledger_note(cls, content: str) -> str:
        if cls._has_usable_source_marker(content) and cls._has_usable_quote_marker(
            content
        ):
            logger.info(
                "EvidenceGroundingMiddleware marked market-research result "
                "SOURCE_QUOTE_LEDGER_DETECTED"
            )
            return _SOURCE_QUOTE_LEDGER_AVAILABLE_NOTE
        if cls._has_usable_source_marker(content):
            logger.info(
                "EvidenceGroundingMiddleware marked market-research result "
                "SOURCE_MARKERS_ONLY_DETECTED"
            )
            return _SOURCE_MARKERS_ONLY_NOTE
        logger.info(
            "EvidenceGroundingMiddleware marked market-research result "
            "NO_SOURCE_LEDGER_DETECTED"
        )
        return _SOURCE_LEDGER_MISSING_NOTE

    @staticmethod
    def _task_subagent_type(tool_call: object) -> str | None:
        if not isinstance(tool_call, dict):
            return None

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
        if name != "task" or not isinstance(args, dict):
            return None

        subagent_type = args.get("subagent_type")
        return str(subagent_type) if subagent_type else None

    @classmethod
    def _specialist_tool_call_ids(
        cls,
        messages: Sequence[object],
        *,
        subagent_type: str,
    ) -> set[str]:
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
                if cls._task_subagent_type(tool_call) != subagent_type:
                    continue
                if isinstance(tool_call, dict):
                    call_id = tool_call.get("id") or tool_call.get("tool_call_id")
                    if call_id:
                        call_ids.add(str(call_id))
        return call_ids

    @classmethod
    def _market_research_tool_call_ids(
        cls,
        messages: Sequence[object],
    ) -> set[str]:
        return cls._specialist_tool_call_ids(
            messages,
            subagent_type="market-research",
        )

    @classmethod
    def _social_media_tool_call_ids(
        cls,
        messages: Sequence[object],
    ) -> set[str]:
        return cls._specialist_tool_call_ids(
            messages,
            subagent_type="social-media-analyst",
        )

    @classmethod
    def _specialist_result_texts(
        cls,
        request: ModelRequest,
        *,
        subagent_type: str,
    ) -> list[str]:
        messages = request.state.get("messages", [])
        call_ids = cls._specialist_tool_call_ids(
            messages,
            subagent_type=subagent_type,
        )
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

    @classmethod
    def _latest_tool_result_matches_specialist(
        cls,
        request: ModelRequest,
        *,
        subagent_type: str,
        boundary_marker: str,
    ) -> bool:
        messages = request.state.get("messages", [])
        call_ids = cls._specialist_tool_call_ids(
            messages,
            subagent_type=subagent_type,
        )
        for message in reversed(messages):
            if isinstance(message, dict):
                message_type = str(message.get("type") or message.get("role") or "")
                if message_type not in {"tool", "toolmessage"}:
                    continue
                content = str(message.get("content", ""))
                if boundary_marker in content:
                    return True
                tool_call_id = message.get("tool_call_id")
                return bool(tool_call_id and str(tool_call_id) in call_ids)

            if not cls._tool_message_is_tool_message(message):
                continue
            content = str(getattr(message, "content", ""))
            if boundary_marker in content:
                return True
            tool_call_id = getattr(message, "tool_call_id", "")
            return bool(tool_call_id and str(tool_call_id) in call_ids)
        return False

    @classmethod
    def _market_research_result_texts(cls, request: ModelRequest) -> list[str]:
        return cls._specialist_result_texts(
            request,
            subagent_type="market-research",
        )

    @classmethod
    def _social_media_result_texts(cls, request: ModelRequest) -> list[str]:
        return cls._specialist_result_texts(
            request,
            subagent_type="social-media-analyst",
        )

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
        if any(
            cls._has_usable_source_marker(text) and cls._has_usable_quote_marker(text)
            for text in texts
        ):
            return "SOURCE_QUOTE_LEDGER_DETECTED"
        if any(cls._has_usable_source_marker(text) for text in texts):
            return "SOURCE_MARKERS_ONLY_DETECTED"
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
        return (
            EvidenceGroundingMiddleware._task_subagent_type(tool_call)
            == "market-research"
        )

    @staticmethod
    def _tool_call_is_social_media(tool_call: object) -> bool:
        return (
            EvidenceGroundingMiddleware._task_subagent_type(tool_call)
            == "social-media-analyst"
        )

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
    def _tool_message_is_social_media_boundary(message: object) -> bool:
        message_type = getattr(message, "type", "")
        class_name = message.__class__.__name__
        if message_type != "tool" and class_name != "ToolMessage":
            return False
        return "Social-media evidence boundary:" in str(getattr(message, "content", ""))

    @classmethod
    def _has_specialist_dispatch(
        cls,
        request: ModelRequest,
        *,
        subagent_type: str,
        boundary_marker: str,
    ) -> bool:
        messages = request.state.get("messages", [])
        for message in messages:
            if isinstance(message, dict):
                tool_calls = message.get("tool_calls") or []
                for tool_call in tool_calls:
                    if cls._task_subagent_type(tool_call) == subagent_type:
                        return True
                content = str(message.get("content", ""))
                if boundary_marker in content:
                    return True
                continue

            tool_calls = getattr(message, "tool_calls", None) or []
            for tool_call in tool_calls:
                if cls._task_subagent_type(tool_call) == subagent_type:
                    return True
            additional_kwargs = getattr(message, "additional_kwargs", {}) or {}
            for tool_call in additional_kwargs.get("tool_calls", []) or []:
                if cls._task_subagent_type(tool_call) == subagent_type:
                    return True
            if boundary_marker in str(getattr(message, "content", "")):
                return True
        return False

    @classmethod
    def _has_market_research_dispatch(cls, request: ModelRequest) -> bool:
        return cls._has_specialist_dispatch(
            request,
            subagent_type="market-research",
            boundary_marker="Market-research evidence boundary:",
        )

    @classmethod
    def _has_social_media_dispatch(cls, request: ModelRequest) -> bool:
        return cls._has_specialist_dispatch(
            request,
            subagent_type="social-media-analyst",
            boundary_marker="Social-media evidence boundary:",
        )

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
        if not cls._latest_tool_result_matches_specialist(
            request,
            subagent_type="market-research",
            boundary_marker="Market-research evidence boundary:",
        ):
            return False
        if request.state.get("_evidence_render_injected"):
            return False
        return True

    @classmethod
    def _should_inject_social_media_render(
        cls,
        request: ModelRequest,
    ) -> bool:
        if not cls._has_social_media_dispatch(request):
            return False
        if not cls._latest_tool_result_matches_specialist(
            request,
            subagent_type="social-media-analyst",
            boundary_marker="Social-media evidence boundary:",
        ):
            return False
        if request.state.get("_evidence_social_render_injected"):
            return False
        return True

    @classmethod
    def _social_media_observation_status(cls, request: ModelRequest) -> str:
        texts = cls._social_media_result_texts(request)
        if any("browser-observed" in text.casefold() for text in texts):
            return "BROWSER_OBSERVED_DETECTED"
        if texts and any(cls._has_usable_source_marker(text) for text in texts):
            return "SOURCE_MARKERS_DETECTED"
        return "NO_OBSERVATION_LEDGER_DETECTED"

    @classmethod
    def _social_media_render_reminder(cls, request: ModelRequest) -> str:
        status = cls._social_media_observation_status(request)
        return (
            _RETRY_SOCIAL_MEDIA_RENDER_REMINDER
            + "\n\nDetected social evidence modality status: "
            + status
            + ". This detected status is the operational modality boundary "
            "for the next user-facing answer."
        )

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

        if cls._should_inject_social_media_render(request):
            request.messages.append(
                SystemMessage(content=cls._social_media_render_reminder(request))
            )
            cast(dict[str, object], request.state)[
                "_evidence_social_render_injected"
            ] = True
            logger.info(
                "EvidenceGroundingMiddleware injected social-media render reminder"
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
        if self._is_social_media_task(request):
            return self._with_boundary_note(result, _SOCIAL_MEDIA_BOUNDARY_NOTE)
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
        if self._is_social_media_task(request):
            return self._with_boundary_note(result, _SOCIAL_MEDIA_BOUNDARY_NOTE)
        return result
