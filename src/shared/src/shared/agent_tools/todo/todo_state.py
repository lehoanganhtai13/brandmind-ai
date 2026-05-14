"""Shared todo state helpers for LangGraph agent middleware."""

from __future__ import annotations

from typing import Annotated, List

from shared.agent_types import TodoItem


def latest_todos(
    current: List[TodoItem] | None,
    update: List[TodoItem] | None,
) -> List[TodoItem]:
    """Resolve concurrent complete todo-list updates with last-writer wins.

    The ``write_todos`` tool writes the full todo list on every update,
    not a partial patch. When an LLM emits more than one ``write_todos``
    call in the same tool batch, LangGraph needs a reducer for the
    ``todos`` state key. The newest complete list is the only coherent
    state to carry forward.
    """
    if update is None:
        return current or []
    return update


TodoState = Annotated[List[TodoItem], latest_todos]
