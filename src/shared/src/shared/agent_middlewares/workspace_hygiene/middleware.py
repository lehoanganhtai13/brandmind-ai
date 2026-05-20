"""Guard structured brand brief edits made through workspace tools."""

from __future__ import annotations

import difflib
import re
from collections.abc import Awaitable, Callable
from pathlib import Path

from langchain.agents.middleware.types import AgentMiddleware, ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from loguru import logger

from shared.agent_middlewares.workspace_injection.middleware import (
    _PHASE_HEADER_RE,
    _normalize_phase_sections,
)
from shared.workspace import BRANDMIND_HOME

_BRAND_BRIEF_PATHS = {
    "/workspace/brand_brief.md",
    "workspace/brand_brief.md",
}

_USER_PROFILE_PATHS = {
    "/user/profile.md",
    "user/profile.md",
}

_WORKING_NOTES_PATHS = {
    "/workspace/working_notes.md",
    "workspace/working_notes.md",
}

_BROAD_ANCHORS = {"", "---", "---\n"}
_ANY_PHASE_HEADING_RE = re.compile(
    r"^#{2,4}\s+(Phase\s+\d+(?:\.\d+)?\b.*)$",
    re.MULTILINE,
)
_PROFILE_PROVENANCE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?"
    r"(?:source|evidence|evidence quote|provenance|user quote|nguồn|nguon|"
    r"bằng chứng|bang chung|trích dẫn|trich dan)\s*:\s*(.+?)\s*$"
)
_QUOTED_EVIDENCE_RE = re.compile(
    r"[\"'`“”‘’](.{8,}?)[\"'`“”‘’]",
)
_OBJECTIVE_SECTION_RE = re.compile(
    r"(?ims)^###\s+O\s+[—-]\s+What we found\s*\n(?P<body>.*?)(?=^###\s+|\Z)"
)
_MEMORY_CANDIDATES_SECTION_RE = re.compile(
    r"(?ims)^##\s+Memory Candidates\s*\n(?P<body>.*?)(?=^##\s+|\Z)"
)
_USER_INTERACTION_PATTERNS_SECTION_RE = re.compile(
    r"(?ims)^##\s+User Interaction Patterns\s*\n(?P<body>.*?)(?=^##\s+|\Z)"
)
_OBJECTIVE_EVIDENCE_RE = re.compile(
    r"(?i)\b("
    r"source|evidence|verified|tool|research|market-research|"
    r"search_knowledge_graph|search_document_library|search_web|"
    r"scrape_web_content|\[O\d+\]"
    r")\b"
)
_OBJECTIVE_NO_EVIDENCE_RE = re.compile(
    r"(?i)(no external evidence|not yet verified|not verified|none yet|pending|"
    r"chưa xác minh|chua xac minh|chưa có bằng chứng|chua co bang chung)"
)
_OBJECTIVE_HYPOTHESIS_RE = re.compile(
    r"(?i)\b("
    r"hypothesis|inference|inferred|likely|appears|seems|suggests|"
    r"usually|typically|may|might|could|có thể|co the|thường|thuong|"
    r"tạm|tam|giả thuyết|gia thuyet"
    r")\b"
)
_OBJECTIVE_PROVENANCE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\[[Oo]\d+\]\s*)?"
    r"(?:source|evidence|verified|tool result|research source|"
    r"nguồn|nguon|bằng chứng|bang chung)\s*:\s*(.+?)\s*$"
)
_MEMORY_CANDIDATE_SIGNAL_RE = re.compile(
    r"(?im)^\s*-\s*Candidate:\s*(?!$|\[)(.+?)\s*$"
)
_USER_INTERACTION_TEMPLATE_LINE_RE = re.compile(
    r"(?i)^\s*-\s*(Learning speed|Decision style|Engagement level|"
    r"Knowledge gaps|Strengths)\s*:\s*\[.+\]\s*$"
)
_PUBLIC_MARKET_FACT_RE = re.compile(
    r"(?i)\b("
    r"\[market fact\]|\[[Oo]\d+\]|objective\s*\([Oo]\)|tripadvisor|"
    r"restaurant guru|google maps|foody|"
    r"review|rating|đánh giá|danh gia|quận\s*\d+|district\s*\d+|"
    r"q\.?\s*\d+|tp\.?\s*hcm|hcmc|ho chi minh|hồ chí minh|"
    r"viet\s*nam|việt\s*nam|vietnam|địa chỉ|dia chi|existing location|"
    r"current location|mới mở|moi mo|hiện là|hien la|hiện có|hien co|"
    r"concept hiện tại|concept hien tai|chi nhánh|chi nhanh|cơ sở|co so|"
    r"public listings?|publicly listed|appears as|exists as|"
    r"\d{1,4}\s+[A-ZÀ-Ỵ]"
    r")\b"
)
_SOURCE_PLATFORM_RE = re.compile(
    r"(?i)\b("
    r"google maps|facebook|fanpage|foody|riviu|tripadvisor|restaurant guru|"
    r"website|official site|instagram|tiktok|báo|bao|article|listing|url"
    r")\b"
)
_PROJECT_SCOPED_PROFILE_RE = re.compile(
    r"(?i)\b("
    r"current project|project context|brand|thương hiệu|thuong hieu|"
    r"restaurant|nhà hàng|nha hang|venue|branch|chi nhánh|chi nhanh|"
    r"booking|revenue|doanh thu|sales|traffic|lượng khách|luong khach|"
    r"budget|ngân sách|ngan sach|cost|chi phí|chi phi|"
    r"deadline|timeline|this week|tuần này|tuan nay|"
    r"triệu|trieu|tỷ|ty|million|billion|%|"
    r"location|địa chỉ|dia chi|view|menu|customer segment|tệp khách|tep khach"
    r")\b"
)


class WorkspaceBriefHygieneMiddleware(AgentMiddleware):
    """Protect structured workspace edits from unsafe model mutations."""

    @staticmethod
    def _is_brand_brief_edit(request: ToolCallRequest) -> bool:
        if request.tool_call.get("name") != "edit_file":
            return False
        args = request.tool_call.get("args", {})
        file_path = str(args.get("file_path", ""))
        return file_path in _BRAND_BRIEF_PATHS or file_path.endswith(
            "/workspace/brand_brief.md"
        )

    @staticmethod
    def _is_user_profile_edit(request: ToolCallRequest) -> bool:
        if request.tool_call.get("name") != "edit_file":
            return False
        args = request.tool_call.get("args", {})
        file_path = str(args.get("file_path", ""))
        return file_path in _USER_PROFILE_PATHS or file_path.endswith(
            "/user/profile.md"
        )

    @staticmethod
    def _is_working_notes_edit(request: ToolCallRequest) -> bool:
        if request.tool_call.get("name") != "edit_file":
            return False
        args = request.tool_call.get("args", {})
        file_path = str(args.get("file_path", ""))
        return file_path in _WORKING_NOTES_PATHS or file_path.endswith(
            "/workspace/working_notes.md"
        )

    @staticmethod
    def _human_texts(request: ToolCallRequest) -> list[str]:
        texts: list[str] = []
        messages = request.state.get("messages", [])
        for message in messages:
            message_type = getattr(message, "type", "")
            class_name = message.__class__.__name__
            if message_type not in {"human", "user"} and class_name != "HumanMessage":
                continue

            content = getattr(message, "content", "")
            if isinstance(content, str):
                if content.strip():
                    texts.append(content)
            elif isinstance(content, list):
                text = "\n".join(
                    str(part.get("text", ""))
                    for part in content
                    if isinstance(part, dict) and part.get("text")
                )
                if text.strip():
                    texts.append(text)
            elif isinstance(content, dict):
                text = str(content.get("text") or content.get("content") or "")
                if text.strip():
                    texts.append(text)
        return texts

    @staticmethod
    def _tool_texts(request: ToolCallRequest) -> list[str]:
        texts: list[str] = []
        messages = request.state.get("messages", [])
        for message in messages:
            message_type = getattr(message, "type", "")
            class_name = message.__class__.__name__
            if message_type != "tool" and class_name != "ToolMessage":
                continue

            content = getattr(message, "content", "")
            if isinstance(content, str):
                if content.strip():
                    texts.append(content)
            elif isinstance(content, list):
                text = "\n".join(
                    str(part.get("text", ""))
                    for part in content
                    if isinstance(part, dict) and part.get("text")
                )
                if text.strip():
                    texts.append(text)
            elif isinstance(content, dict):
                text = str(content.get("text") or content.get("content") or "")
                if text.strip():
                    texts.append(text)
        return texts

    @staticmethod
    def _normalize_evidence_text(text: str) -> str:
        return re.sub(r"\s+", " ", text.casefold()).strip()

    @classmethod
    def _has_exact_quote_from_texts(
        cls,
        text: str,
        source_texts: list[str],
        *,
        provenance_re: re.Pattern[str],
    ) -> bool:
        if not source_texts:
            return False

        source_blob = cls._normalize_evidence_text("\n".join(source_texts))
        for match in provenance_re.finditer(text):
            evidence = match.group(1).strip()
            quoted_snippets = [
                cls._normalize_evidence_text(snippet)
                for snippet in _QUOTED_EVIDENCE_RE.findall(evidence)
            ]
            if not quoted_snippets:
                continue
            if any(
                len(snippet) >= 12 and snippet in source_blob
                for snippet in quoted_snippets
            ):
                return True
        return False

    @classmethod
    def _profile_edit_has_source_quote(
        cls,
        new_string: str,
        human_texts: list[str],
    ) -> bool:
        return cls._has_exact_quote_from_texts(
            new_string,
            human_texts,
            provenance_re=_PROFILE_PROVENANCE_RE,
        )

    @staticmethod
    def _strip_provenance_lines(text: str) -> str:
        kept_lines: list[str] = []
        for line in text.splitlines():
            if _PROFILE_PROVENANCE_RE.match(line):
                continue
            kept_lines.append(line)
        return "\n".join(kept_lines)

    @staticmethod
    def _line_added_text(old_string: str, new_string: str) -> str:
        diff = difflib.ndiff(old_string.splitlines(), new_string.splitlines())
        added_lines: list[str] = []
        for line in diff:
            if line.startswith("+ "):
                added_lines.append(line[2:])
        return "\n".join(added_lines)

    @staticmethod
    def _active_project_names() -> list[str]:
        try:
            from core.brand_strategy.session import (  # type: ignore[import-not-found]
                get_active_session,
            )
        except ImportError:
            return []

        session = get_active_session()
        if session is None:
            return []

        names: list[str] = []
        brand_name = getattr(session, "brand_name", None)
        if isinstance(brand_name, str) and brand_name.strip():
            names.append(brand_name.strip())
        brief = getattr(session, "brief", None)
        brief_name = getattr(brief, "brand_name", None)
        if isinstance(brief_name, str) and brief_name.strip():
            names.append(brief_name.strip())
        return list(dict.fromkeys(names))

    @classmethod
    def _profile_edit_contains_project_scoped_content(
        cls,
        old_string: str,
        new_string: str,
    ) -> bool:
        added_text = cls._strip_provenance_lines(
            cls._line_added_text(old_string, new_string)
        )
        normalized_added = cls._normalize_evidence_text(added_text)
        if not normalized_added:
            return False

        for project_name in cls._active_project_names():
            normalized_name = cls._normalize_evidence_text(project_name)
            if normalized_name and normalized_name in normalized_added:
                return True

        return bool(_PROJECT_SCOPED_PROFILE_RE.search(added_text))

    @classmethod
    def _has_public_fact_source_quote(
        cls,
        text: str,
        source_texts: list[str],
    ) -> bool:
        if not source_texts:
            return False

        source_blob = cls._normalize_evidence_text("\n".join(source_texts))
        for match in _PROFILE_PROVENANCE_RE.finditer(text):
            evidence = match.group(1).strip()
            quoted_snippets = _QUOTED_EVIDENCE_RE.findall(evidence)
            for snippet in quoted_snippets:
                normalized = cls._normalize_evidence_text(snippet)
                if len(normalized) < 12 or normalized not in source_blob:
                    continue
                if _PUBLIC_MARKET_FACT_RE.search(snippet):
                    return True
                if _SOURCE_PLATFORM_RE.search(evidence):
                    return True
        return False

    @classmethod
    def _profile_guard_message(cls, request: ToolCallRequest) -> str | None:
        if not cls._is_user_profile_edit(request):
            return None

        human_texts = cls._human_texts(request)
        args = request.tool_call.get("args", {})
        new_string = str(args.get("new_string", ""))
        if not cls._profile_edit_has_source_quote(new_string, human_texts):
            return (
                "Cannot edit `/user/profile.md` without source evidence: durable "
                "profile memory must include a `Source:` or `Evidence:` line with "
                "an exact quote from the user's messages. If this is an inferred "
                "preference, project-specific context, or early observation, append "
                "it to `/workspace/working_notes.md` as a memory candidate with "
                "confidence and reason instead of promoting it to the durable "
                "profile. Continue using the tentative context normally."
            )

        old_string = str(args.get("old_string", ""))
        if cls._profile_edit_contains_project_scoped_content(old_string, new_string):
            return (
                "Cannot promote project-scoped details into `/user/profile.md`: "
                "durable profile memory should contain stable user traits, roles, "
                "working preferences, or constraints after abstracting away the "
                "current brand/project. Keep brand names, restaurant facts, budget, "
                "revenue, traffic, location, customer, or campaign metrics in "
                "`/workspace/working_notes.md` or `brand_brief.md`. If a durable "
                "user fact remains, retry with only that abstracted profile fact "
                "and its exact `Source:` quote."
            )

        return None

    @staticmethod
    def _objective_section_body(markdown: str) -> str:
        match = _OBJECTIVE_SECTION_RE.search(markdown)
        return match.group("body").strip() if match else ""

    @staticmethod
    def _memory_candidates_body(markdown: str) -> str:
        match = _MEMORY_CANDIDATES_SECTION_RE.search(markdown)
        return match.group("body").strip() if match else ""

    @staticmethod
    def _user_interaction_patterns_body(markdown: str) -> str:
        match = _USER_INTERACTION_PATTERNS_SECTION_RE.search(markdown)
        return match.group("body").strip() if match else ""

    @staticmethod
    def _has_substantive_objective_body(body: str) -> bool:
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("_") and stripped.endswith("_"):
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                continue
            return True
        return False

    @classmethod
    def _objective_evidence_guard_message(cls, request: ToolCallRequest) -> str | None:
        if not cls._is_brand_brief_edit(request):
            return None

        args = request.tool_call.get("args", {})
        new_string = str(args.get("new_string", ""))
        body = cls._objective_section_body(new_string)
        if not cls._has_substantive_objective_body(body):
            return None
        if _OBJECTIVE_NO_EVIDENCE_RE.search(body):
            return None

        has_evidence = bool(_OBJECTIVE_EVIDENCE_RE.search(body))
        has_hypothesis = bool(_OBJECTIVE_HYPOTHESIS_RE.search(body))
        has_source_quote = cls._has_exact_quote_from_texts(
            body,
            cls._tool_texts(request),
            provenance_re=_OBJECTIVE_PROVENANCE_RE,
        )
        if has_evidence and has_source_quote and not has_hypothesis:
            return None

        return (
            "Cannot write unsupported or hypothesis-style content into "
            "`/workspace/brand_brief.md` section `O — What we found`. Use `S` "
            "for first-party user facts, use `O` only for verified source/tool "
            "findings with an explicit source marker and an exact quote from a "
            "tool result. Move assumptions, name-based interpretations, or "
            "unverified market relationships to `A — What we concluded` or "
            "`/workspace/working_notes.md` as hypotheses. Do not fabricate "
            "source labels. If the public fact determines scope, run a bounded "
            "`market-research` pass or ask the user to confirm before treating "
            "it as evidence."
        )

    @classmethod
    def _memory_candidate_guard_message(cls, request: ToolCallRequest) -> str | None:
        if not cls._is_working_notes_edit(request):
            return None

        args = request.tool_call.get("args", {})
        new_string = str(args.get("new_string", ""))
        body = cls._memory_candidates_body(new_string)
        if not _MEMORY_CANDIDATE_SIGNAL_RE.search(body):
            return None

        source_texts = cls._human_texts(request) + cls._tool_texts(request)
        has_source_quote = cls._has_exact_quote_from_texts(
            body,
            source_texts,
            provenance_re=_PROFILE_PROVENANCE_RE,
        )
        if has_source_quote:
            return None

        return (
            "Cannot write a filled `Memory Candidates` entry without source "
            "evidence. Add an `Evidence quote:` line with an exact quote from "
            "the user's message or a tool result, or keep the point as a plain "
            "hypothesis outside `Memory Candidates`. Do not mark inferred "
            "project context as high-confidence, durable, or promotable until "
            "the evidence quote is present."
        )

    @classmethod
    def _user_interaction_pattern_guard_message(
        cls,
        request: ToolCallRequest,
    ) -> str | None:
        if not cls._is_working_notes_edit(request):
            return None

        args = request.tool_call.get("args", {})
        new_string = str(args.get("new_string", ""))
        body = cls._user_interaction_patterns_body(new_string)
        if not body:
            return None

        has_new_observation = False
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("_") and stripped.endswith("_"):
                continue
            if _USER_INTERACTION_TEMPLATE_LINE_RE.match(stripped):
                continue
            has_new_observation = True
            break
        if not has_new_observation:
            return None

        source_texts = cls._human_texts(request) + cls._tool_texts(request)
        has_source_quote = cls._has_exact_quote_from_texts(
            body,
            source_texts,
            provenance_re=_PROFILE_PROVENANCE_RE,
        )
        if has_source_quote:
            return None

        return (
            "Cannot write inferred user interaction patterns without source "
            "evidence. For first-turn impressions, use `Memory Candidates` "
            "with an exact `Evidence quote:` from the user or a tool result, "
            "or leave the interaction-pattern section unchanged until there "
            "is enough observed behavior. Do not convert a single project "
            "request into durable style or preference notes."
        )

    @classmethod
    def _public_market_fact_guard_message(
        cls,
        request: ToolCallRequest,
    ) -> str | None:
        if not (
            cls._is_brand_brief_edit(request) or cls._is_working_notes_edit(request)
        ):
            return None

        args = request.tool_call.get("args", {})
        new_string = str(args.get("new_string", ""))
        if not _PUBLIC_MARKET_FACT_RE.search(new_string):
            return None

        source_texts = cls._human_texts(request) + cls._tool_texts(request)
        has_source_quote = cls._has_public_fact_source_quote(
            new_string,
            source_texts,
        )
        if has_source_quote:
            return None

        return (
            "Cannot write current public market facts into workspace notes "
            "without source evidence. Add a `Source:` or `Evidence quote:` "
            "line with an exact quote from the user's message or a tool result, "
            "or move the point to a non-specific hypothesis without ratings, "
            "reviews, addresses, branch counts, or source-like facts. If this "
            "fact changes the strategy route, dispatch one bounded "
            "`market-research` pass before recording it as evidence."
        )

    @staticmethod
    def _phase_headers(text: str) -> list[str]:
        return [match.group(1) for match in _PHASE_HEADER_RE.finditer(text)]

    @staticmethod
    def _canonicalize_phase_headings(text: str) -> str:
        return _ANY_PHASE_HEADING_RE.sub(r"## \1", text)

    @classmethod
    def _has_phase_sections(cls, text: str) -> bool:
        return bool(cls._phase_headers(cls._canonicalize_phase_headings(text)))

    @classmethod
    def _looks_like_phase_section_upsert(cls, old_string: str, new_string: str) -> bool:
        return old_string.strip() in _BROAD_ANCHORS and cls._has_phase_sections(
            new_string
        )

    @classmethod
    def _upsert_phase_sections(
        cls,
        new_string: str,
        reason: str,
        tool_call_id: str,
    ) -> ToolMessage | None:
        path = cls._brand_brief_path()
        if path is None:
            return None

        try:
            current = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning(f"WorkspaceBriefHygiene: could not read brand brief: {exc}")
            return None

        merged = current.rstrip() + "\n\n" + new_string.strip() + "\n"
        normalized, removed, reordered = _normalize_phase_sections(
            cls._canonicalize_phase_headings(merged)
        )
        try:
            path.write_text(normalized, encoding="utf-8")
        except OSError as exc:
            logger.warning(f"WorkspaceBriefHygiene: could not write brand brief: {exc}")
            return None

        logger.info(
            "WorkspaceBriefHygiene: upserted phase sections after broad-anchor "
            f"{reason}; removed={removed}, reordered={reordered}"
        )
        return ToolMessage(
            content=(
                "Updated `/workspace/brand_brief.md` by upserting the supplied "
                "phase section(s) instead of applying a broad text replacement. "
                "Continue from the updated workspace state."
            ),
            tool_call_id=tool_call_id,
        )

    @classmethod
    def _heading_guard_message(cls, request: ToolCallRequest) -> str | None:
        args = request.tool_call.get("args", {})
        old_string = str(args.get("old_string", ""))
        new_string = str(args.get("new_string", ""))
        old_headers = cls._phase_headers(old_string)
        if not old_headers:
            return None

        new_headers = set(cls._phase_headers(new_string))
        missing = [header for header in old_headers if header not in new_headers]
        if not missing:
            return None

        missing_text = ", ".join(f"`{header}`" for header in missing)
        return (
            "Cannot edit `/workspace/brand_brief.md`: preserve existing phase "
            f"heading(s) used as anchors: {missing_text}. Retry with a targeted "
            "edit that keeps the original heading text in `new_string`, then "
            "insert new content before or after that heading."
        )

    @staticmethod
    def _brand_brief_path() -> Path | None:
        try:
            from core.brand_strategy.session import (  # type: ignore[import-not-found]
                get_active_session,
            )
        except ImportError:
            return None

        session = get_active_session()
        if session is None or not session.session_id:
            return None
        path = BRANDMIND_HOME / "projects" / session.session_id / "workspace"
        candidate = path / "brand_brief.md"
        return candidate if candidate.is_file() else None

    @staticmethod
    def _looks_like_stale_full_brief_replace(
        old_string: str,
        new_string: str,
    ) -> bool:
        stale_anchor = "# Brand Strategy Brief: [Brand Name]" in old_string
        placeholder_anchor = old_string.lstrip().startswith("# Brand Brief")
        if not stale_anchor and not placeholder_anchor:
            return False
        if not new_string.lstrip().startswith("# Brand"):
            return False

        normalized_new = WorkspaceBriefHygieneMiddleware._canonicalize_phase_headings(
            new_string
        )
        headers = set(WorkspaceBriefHygieneMiddleware._phase_headers(normalized_new))
        required = {
            "## Phase 0",
            "## Phase 0.5",
            "## Phase 1",
            "## Phase 2",
            "## Phase 3",
            "## Phase 4",
            "## Phase 5",
        }
        return required.issubset(headers)

    @classmethod
    def _recover_stale_full_brief_replace(
        cls,
        request: ToolCallRequest,
        result: ToolMessage | Command,
    ) -> ToolMessage | Command:
        if not isinstance(result, ToolMessage):
            return result
        if "String not found" not in str(result.content):
            return result

        args = request.tool_call.get("args", {})
        old_string = str(args.get("old_string", ""))
        new_string = str(args.get("new_string", ""))
        if not cls._looks_like_stale_full_brief_replace(old_string, new_string):
            return result

        path = cls._brand_brief_path()
        if path is None:
            return result

        normalized, _, _ = _normalize_phase_sections(
            cls._canonicalize_phase_headings(new_string)
        )
        try:
            path.write_text(normalized, encoding="utf-8")
        except OSError as exc:
            logger.warning(
                "WorkspaceBriefHygiene: could not recover full brand brief "
                f"replacement: {exc}"
            )
            return result

        logger.info(
            "WorkspaceBriefHygiene: recovered stale full brand_brief.md replacement"
        )
        return ToolMessage(
            content=(
                "Recovered `/workspace/brand_brief.md` by applying the full "
                "brand brief replacement after the stale template anchor failed."
            ),
            tool_call_id=request.tool_call["id"],
        )

    @staticmethod
    def _extract_last_user_text(request: ToolCallRequest) -> str:
        messages = request.state.get("messages", [])
        for message in reversed(messages):
            message_type = getattr(message, "type", "")
            class_name = message.__class__.__name__
            if message_type not in {"human", "user"} and class_name != "HumanMessage":
                continue

            content = getattr(message, "content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "\n".join(
                    str(part.get("text", ""))
                    for part in content
                    if isinstance(part, dict) and part.get("text")
                )
            if isinstance(content, dict):
                return str(content.get("text") or content.get("content") or "")
        return ""

    @classmethod
    def _sync_final_handoff_if_ready(
        cls,
        request: ToolCallRequest,
        result: ToolMessage | Command,
    ) -> ToolMessage | Command:
        if not isinstance(result, ToolMessage):
            return result

        try:
            from core.brand_strategy.session import (  # type: ignore[import-not-found]
                get_active_session,
                sync_to_deliverable_packaging_if_ready,
            )
        except ImportError:
            return result

        session = get_active_session()
        if session is None:
            return result

        sync_result = sync_to_deliverable_packaging_if_ready(
            session,
            cls._extract_last_user_text(request),
        )
        if sync_result is None:
            return result

        return ToolMessage(
            content=f"{result.content}\n\n{sync_result}",
            tool_call_id=request.tool_call["id"],
        )

    @classmethod
    def _recover_phase_section_upsert(
        cls,
        request: ToolCallRequest,
        result: ToolMessage | Command,
    ) -> ToolMessage | Command:
        if not isinstance(result, ToolMessage):
            return result

        result_text = str(result.content)
        if "appears" not in result_text and "String not found" not in result_text:
            return result

        args = request.tool_call.get("args", {})
        old_string = str(args.get("old_string", ""))
        new_string = str(args.get("new_string", ""))
        if not cls._looks_like_phase_section_upsert(old_string, new_string):
            return result

        recovered = cls._upsert_phase_sections(
            new_string,
            reason="edit recovery",
            tool_call_id=str(request.tool_call.get("id", "")),
        )
        return recovered if recovered is not None else result

    @classmethod
    def _intercept_broad_replace_all(
        cls,
        request: ToolCallRequest,
    ) -> ToolMessage | None:
        args = request.tool_call.get("args", {})
        if not bool(args.get("replace_all")):
            return None

        old_string = str(args.get("old_string", ""))
        new_string = str(args.get("new_string", ""))
        if not cls._looks_like_phase_section_upsert(old_string, new_string):
            return None

        return cls._upsert_phase_sections(
            new_string,
            reason="replace_all interception",
            tool_call_id=str(request.tool_call.get("id", "")),
        )

    @classmethod
    def _normalize_current_brief(cls) -> None:
        path = cls._brand_brief_path()
        if path is None:
            return
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning(f"WorkspaceBriefHygiene: could not read brand brief: {exc}")
            return

        canonical = cls._canonicalize_phase_headings(content)
        normalized, removed, reordered = _normalize_phase_sections(canonical)
        if normalized == content and removed == 0 and not reordered:
            return

        try:
            path.write_text(normalized, encoding="utf-8")
        except OSError as exc:
            logger.warning(f"WorkspaceBriefHygiene: could not write brand brief: {exc}")
            return
        logger.info(
            "WorkspaceBriefHygiene: normalized brand_brief.md after edit_file; "
            f"removed {removed} duplicate phase section(s), reordered={reordered}"
        )

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Guard synchronous structured workspace edits."""
        profile_guard_message = self._profile_guard_message(request)
        if profile_guard_message is not None:
            return ToolMessage(
                content=profile_guard_message,
                tool_call_id=request.tool_call["id"],
            )

        memory_candidate_guard_message = self._memory_candidate_guard_message(request)
        if memory_candidate_guard_message is not None:
            return ToolMessage(
                content=memory_candidate_guard_message,
                tool_call_id=request.tool_call["id"],
            )

        user_interaction_guard_message = (
            self._user_interaction_pattern_guard_message(request)
        )
        if user_interaction_guard_message is not None:
            return ToolMessage(
                content=user_interaction_guard_message,
                tool_call_id=request.tool_call["id"],
            )

        public_market_fact_guard_message = self._public_market_fact_guard_message(
            request
        )
        if public_market_fact_guard_message is not None:
            return ToolMessage(
                content=public_market_fact_guard_message,
                tool_call_id=request.tool_call["id"],
            )

        if not self._is_brand_brief_edit(request):
            return handler(request)

        objective_guard_message = self._objective_evidence_guard_message(request)
        if objective_guard_message is not None:
            return ToolMessage(
                content=objective_guard_message,
                tool_call_id=request.tool_call["id"],
            )

        guard_message = self._heading_guard_message(request)
        if guard_message is not None:
            return ToolMessage(
                content=guard_message,
                tool_call_id=request.tool_call["id"],
            )

        broad_replace_result = self._intercept_broad_replace_all(request)
        if broad_replace_result is not None:
            self._normalize_current_brief()
            return self._sync_final_handoff_if_ready(request, broad_replace_result)

        result = handler(request)
        result = self._recover_stale_full_brief_replace(request, result)
        result = self._recover_phase_section_upsert(request, result)
        self._normalize_current_brief()
        return self._sync_final_handoff_if_ready(request, result)

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        """Guard asynchronous structured workspace edits."""
        profile_guard_message = self._profile_guard_message(request)
        if profile_guard_message is not None:
            return ToolMessage(
                content=profile_guard_message,
                tool_call_id=request.tool_call["id"],
            )

        memory_candidate_guard_message = self._memory_candidate_guard_message(request)
        if memory_candidate_guard_message is not None:
            return ToolMessage(
                content=memory_candidate_guard_message,
                tool_call_id=request.tool_call["id"],
            )

        user_interaction_guard_message = (
            self._user_interaction_pattern_guard_message(request)
        )
        if user_interaction_guard_message is not None:
            return ToolMessage(
                content=user_interaction_guard_message,
                tool_call_id=request.tool_call["id"],
            )

        public_market_fact_guard_message = self._public_market_fact_guard_message(
            request
        )
        if public_market_fact_guard_message is not None:
            return ToolMessage(
                content=public_market_fact_guard_message,
                tool_call_id=request.tool_call["id"],
            )

        if not self._is_brand_brief_edit(request):
            return await handler(request)

        objective_guard_message = self._objective_evidence_guard_message(request)
        if objective_guard_message is not None:
            return ToolMessage(
                content=objective_guard_message,
                tool_call_id=request.tool_call["id"],
            )

        guard_message = self._heading_guard_message(request)
        if guard_message is not None:
            return ToolMessage(
                content=guard_message,
                tool_call_id=request.tool_call["id"],
            )

        broad_replace_result = self._intercept_broad_replace_all(request)
        if broad_replace_result is not None:
            self._normalize_current_brief()
            return self._sync_final_handoff_if_ready(request, broad_replace_result)

        result = await handler(request)
        result = self._recover_stale_full_brief_replace(request, result)
        result = self._recover_phase_section_upsert(request, result)
        self._normalize_current_brief()
        return self._sync_final_handoff_if_ready(request, result)
