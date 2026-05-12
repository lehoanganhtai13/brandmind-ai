"""Guard structured brand brief edits made through workspace tools."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path

from langchain.agents.middleware.types import AgentMiddleware, ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from loguru import logger

from shared.agent_middlewares.workspace_injection.middleware import (
    _PHASE_HEADER_RE,
    _dedup_phase_sections,
)
from shared.workspace import BRANDMIND_HOME

_BRAND_BRIEF_PATHS = {
    "/workspace/brand_brief.md",
    "workspace/brand_brief.md",
}


class WorkspaceBriefHygieneMiddleware(AgentMiddleware):
    """Protect phase headings and normalize duplicate phase sections."""

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
    def _phase_headers(text: str) -> list[str]:
        return [match.group(1) for match in _PHASE_HEADER_RE.finditer(text)]

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

        normalized, removed = _dedup_phase_sections(content)
        if removed == 0:
            return

        try:
            path.write_text(normalized, encoding="utf-8")
        except OSError as exc:
            logger.warning(f"WorkspaceBriefHygiene: could not write brand brief: {exc}")
            return
        logger.info(
            "WorkspaceBriefHygiene: normalized brand_brief.md after edit_file; "
            f"removed {removed} duplicate phase section(s)"
        )

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Guard synchronous brand brief edits."""
        if not self._is_brand_brief_edit(request):
            return handler(request)

        guard_message = self._heading_guard_message(request)
        if guard_message is not None:
            return ToolMessage(
                content=guard_message,
                tool_call_id=request.tool_call["id"],
            )

        result = handler(request)
        self._normalize_current_brief()
        return result

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        """Guard asynchronous brand brief edits."""
        if not self._is_brand_brief_edit(request):
            return await handler(request)

        guard_message = self._heading_guard_message(request)
        if guard_message is not None:
            return ToolMessage(
                content=guard_message,
                tool_call_id=request.tool_call["id"],
            )

        result = await handler(request)
        self._normalize_current_brief()
        return result
