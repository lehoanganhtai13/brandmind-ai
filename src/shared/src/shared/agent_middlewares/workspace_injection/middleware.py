"""WorkspaceInjectionMiddleware — auto-prepend workspace files to sub-agent context.

Sub-agents in the brand-strategy stack (document-generator, creative-studio)
have no filesystem access; their only input is the dispatch description.
The orchestrator's system prompt asks it to paste ``brand_brief.md`` and
``quality_gates.md`` verbatim into every Phase 5 dispatch, but in long
Phase 5 contexts the orchestrator has been observed to compress the
description to one-line task framings — leaving the sub-agent without
the substance it needs to populate artifact templates correctly.

This middleware closes the gap deterministically: on the sub-agent's
first model call, it locates the active brand-strategy session's
workspace directory and prepends the configured files to the first
human message as a ``=== WORKSPACE: <name> (auto-injected) ===`` block.
The sub-agent then sees the workspace content regardless of how thin
the orchestrator's dispatch description was.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
)
from langchain_core.messages import AIMessage, HumanMessage
from loguru import logger

_DEFAULT_FILES = ("brand_brief.md", "quality_gates.md")
_DEFAULT_WORKSPACE_ROOT = Path.home() / ".brandmind" / "projects"
_PHASE_HEADER_RE = re.compile(r"^(## Phase \d+(?:\.\d+)?)\b", re.MULTILINE)


def _dedup_phase_sections(content: str) -> tuple[str, int]:
    """Remove earlier duplicate top-level phase sections from brand_brief.md.

    When the duplicate-pass framework bug fires, the orchestrator writes the same
    phase block to brand_brief.md twice — typically an English skeleton first, then
    a full Vietnamese content block. Injecting both contradictory "COMPLETED" sections
    into the sub-agent causes it to return empty output with zero tool calls (Layer 2
    failure). This helper keeps only the last occurrence of each duplicate phase block,
    which is the fuller, more recent version.

    Only top-level ``## Phase N`` or ``## Phase N.M`` section boundaries are
    considered; sub-headings and non-phase sections are preserved with their
    original relative order.

    Args:
        content (str): Raw text of brand_brief.md read from the workspace directory.

    Returns:
        deduplicated_content (str): Content with earlier duplicate phase sections
            removed. Identical to ``content`` when no duplicates exist.
        sections_removed (int): Number of duplicate sections dropped; 0 when the
            content was already clean.
    """
    lines = content.splitlines(keepends=True)

    segments: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if _PHASE_HEADER_RE.match(line):
            segments.append(current)
            current = [line]
        else:
            current.append(line)
    segments.append(current)

    preamble = segments[0]
    phase_segments = segments[1:]

    if not phase_segments:
        return content, 0

    phase_keys: list[str] = []
    for seg in phase_segments:
        first_line = seg[0] if seg else ""
        m = _PHASE_HEADER_RE.match(first_line)
        phase_keys.append(m.group(1) if m else first_line.rstrip())

    last_index_for_key: dict[str, int] = {}
    for i, key in enumerate(phase_keys):
        last_index_for_key[key] = i

    removed = len(phase_segments) - len(last_index_for_key)
    if removed == 0:
        return content, 0

    result_lines = list(preamble)
    for i, (key, seg) in enumerate(zip(phase_keys, phase_segments)):
        if last_index_for_key[key] == i:
            result_lines.extend(seg)

    return "".join(result_lines), removed


class WorkspaceInjectionMiddleware(AgentMiddleware):
    """Inject brand-strategy workspace files into a sub-agent's first turn.

    Args:
        files: Names of files inside the active session's workspace
            directory to inject. Files that do not exist are skipped
            silently so a missing optional file never blocks dispatch.
        workspace_root: Root under which per-session workspace
            directories live. Defaults to ``~/.brandmind/projects``,
            matching :func:`shared.workspace.ensure_project_workspace`.
    """

    def __init__(
        self,
        files: tuple[str, ...] = _DEFAULT_FILES,
        workspace_root: Path = _DEFAULT_WORKSPACE_ROOT,
    ) -> None:
        self.files = files
        self.workspace_root = workspace_root
        logger.info(
            "WorkspaceInjectionMiddleware initialized: "
            f"files={list(files)} root={workspace_root}"
        )

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        self._inject_if_first_turn(request)
        return handler(request)

    async def awrap_model_call(  # type: ignore[override]
        self,
        request: ModelRequest,
        handler: Callable[..., Any],
    ) -> ModelResponse:
        self._inject_if_first_turn(request)
        return await handler(request)

    def _inject_if_first_turn(self, request: ModelRequest) -> None:
        """Prepend workspace blocks to the first HumanMessage on the first turn.

        A turn is "first" when the message history contains no
        :class:`AIMessage` from this sub-agent yet — subsequent turns
        already carry the injected content via conversation history,
        so re-injecting would duplicate it.
        """
        if any(isinstance(m, AIMessage) for m in request.messages):
            return

        workspace_dir = self._resolve_workspace_dir()
        if workspace_dir is None:
            return

        blocks: list[str] = []
        for filename in self.files:
            file_path = workspace_dir / filename
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except OSError as exc:
                logger.warning(
                    f"WorkspaceInjectionMiddleware: skipping {filename}: {exc}"
                )
                continue
            if filename == "brand_brief.md":
                content, removed = _dedup_phase_sections(content)
                if removed > 0:
                    logger.info(
                        f"WorkspaceInjectionMiddleware: deduped brand_brief.md — "
                        f"removed {removed} duplicate phase section(s); "
                        f"injecting {len(content)} chars after dedup"
                    )
            blocks.append(
                f"=== WORKSPACE: {filename} (auto-injected) ===\n"
                f"{content.strip()}\n"
                f"=== END {filename} ==="
            )

        if not blocks:
            return

        prefix = (
            "The following workspace files describe the active session's "
            "strategy. Treat them as the source of truth for any artifact "
            "body content; render quoted decisions verbatim and do not "
            "invent details that contradict them.\n\n" + "\n\n".join(blocks) + "\n\n"
        )

        for i, msg in enumerate(request.messages):
            if isinstance(msg, HumanMessage):
                existing = (
                    msg.content if isinstance(msg.content, str) else str(msg.content)
                )
                request.messages[i] = HumanMessage(content=prefix + existing)
                logger.debug(
                    "WorkspaceInjectionMiddleware: injected "
                    f"{len(blocks)} workspace file(s) "
                    f"({sum(len(b) for b in blocks)} chars) into sub-agent dispatch"
                )
                return

    def _resolve_workspace_dir(self) -> Path | None:
        """Return the active session's workspace directory, or ``None``.

        Uses a late import so the ``shared`` package keeps a soft
        dependency on ``core``. Returns ``None`` whenever the active
        session is unset (CLI / unit-test contexts), so the middleware
        is a no-op outside a real brand-strategy session.
        """
        try:
            from core.brand_strategy.session import (  # type: ignore[import-not-found]
                get_active_session,
            )
        except ImportError:
            return None
        session = get_active_session()
        if session is None or not session.session_id:
            return None
        candidate = self.workspace_root / session.session_id / "workspace"
        return candidate if candidate.is_dir() else None
