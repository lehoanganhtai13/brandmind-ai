"""Utilities for correlating tool-call starts with tool-result events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

ToolCallPayload = TypeVar("ToolCallPayload")


@dataclass
class PendingToolCall(Generic[ToolCallPayload]):
    """Payload waiting for the matching tool result event."""

    tool_name: str
    payload: ToolCallPayload


class ToolCallMatcher(Generic[ToolCallPayload]):
    """Match tool-result events to tool-call payloads by id with FIFO fallback."""

    def __init__(self) -> None:
        self._by_id: dict[str, PendingToolCall[ToolCallPayload]] = {}
        self._by_name: dict[str, list[PendingToolCall[ToolCallPayload]]] = {}

    def add(
        self,
        tool_name: str,
        payload: ToolCallPayload,
        tool_call_id: str = "",
    ) -> None:
        """Track one pending tool call until a result settles it."""
        pending = PendingToolCall(tool_name=tool_name, payload=payload)
        if tool_call_id:
            self._by_id[tool_call_id] = pending
        self._by_name.setdefault(tool_name, []).append(pending)

    def pop(self, tool_name: str, tool_call_id: str = "") -> ToolCallPayload | None:
        """Return the payload for a result event, preferring provider ids."""
        if tool_call_id:
            pending = self._by_id.pop(tool_call_id, None)
            if pending is not None:
                self._remove_from_name_queue(pending)
                return pending.payload

        queue = self._by_name.get(tool_name)
        if not queue:
            return None

        pending = queue.pop(0)
        if not queue:
            self._by_name.pop(tool_name, None)
        self._drop_id_for(pending)
        return pending.payload

    def _remove_from_name_queue(
        self,
        pending: PendingToolCall[ToolCallPayload],
    ) -> None:
        """Remove a settled pending call from its name-based fallback queue."""
        queue = self._by_name.get(pending.tool_name)
        if queue is None:
            return
        self._by_name[pending.tool_name] = [
            candidate for candidate in queue if candidate is not pending
        ]
        if not self._by_name[pending.tool_name]:
            self._by_name.pop(pending.tool_name, None)

    def _drop_id_for(self, pending: PendingToolCall[ToolCallPayload]) -> None:
        """Drop the id mapping when a result had to use the legacy FIFO path."""
        for tool_call_id, candidate in list(self._by_id.items()):
            if candidate is pending:
                self._by_id.pop(tool_call_id, None)
                return
