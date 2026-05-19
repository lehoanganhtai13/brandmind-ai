"""Guard structured brand brief edits made through workspace tools."""

from __future__ import annotations

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

_BROAD_ANCHORS = {"", "---", "---\n"}
_ANY_PHASE_HEADING_RE = re.compile(
    r"^#{2,4}\s+(Phase\s+\d+(?:\.\d+)?\b.*)$",
    re.MULTILINE,
)
_EXPLICIT_PROFILE_SIGNAL_RE = re.compile(
    r"\b("
    r"i am|i'm|my role|i prefer|my preference|budget|deadline|timeline|"
    r"tôi là|toi la|mình là|minh la|anh là|anh la|em là|em la|"
    r"vai trò|vai tro|ngân sách|ngan sach|thời hạn|thoi han|"
    r"deadline|tôi thích|toi thich|mình thích|minh thich|"
    r"tôi muốn bạn|toi muon ban|mình muốn bạn|minh muon ban"
    r")\b",
    re.IGNORECASE,
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

    @classmethod
    def _profile_guard_message(cls, request: ToolCallRequest) -> str | None:
        if not cls._is_user_profile_edit(request):
            return None

        human_texts = cls._human_texts(request)
        if len(human_texts) != 1:
            return None

        latest_user_text = human_texts[-1]
        if _EXPLICIT_PROFILE_SIGNAL_RE.search(latest_user_text):
            return None

        return (
            "Cannot edit `/user/profile.md` from a sparse first turn: durable "
            "profile facts must come from explicit user-stated role, preference, "
            "constraint, or working style. Keep inferences such as likely role, "
            "industry expertise, language, and communication style in "
            "`/workspace/working_notes.md` as tentative observations until the "
            "user confirms them. Continue using the tentative context, and ask "
            "at most one focused blocker if user input is needed."
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

        if not self._is_brand_brief_edit(request):
            return handler(request)

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

        if not self._is_brand_brief_edit(request):
            return await handler(request)

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
