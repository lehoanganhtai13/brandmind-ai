"""Tests for concurrent todo state updates in LangGraph batches."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from shared.agent_tools.todo.todo_state import TodoState, latest_todos


class _TodoGraphState(TypedDict):
    todos: TodoState


def _todo(content: str, status: str = "pending") -> dict[str, str]:
    return {
        "content": content,
        "status": status,
        "activeForm": f"Handling {content}",
        "priority": "high",
    }


def test_latest_todos_uses_complete_update_list() -> None:
    """A todo update replaces the prior complete list, not patches it."""
    first = [_todo("first")]
    second = [_todo("second", "in_progress")]

    assert latest_todos(first, second) == second
    assert latest_todos(first, None) == first


def test_todo_state_accepts_concurrent_complete_list_updates() -> None:
    """Parallel ``todos`` writes should merge instead of raising.

    A live Linh replay emitted two ``write_todos`` calls in the same
    model step. Without the reducer on ``TodoState``, LangGraph raises
    ``InvalidUpdateError`` because ``todos`` is a LastValue channel.
    """

    def first_writer(_: _TodoGraphState) -> dict[str, list[dict[str, str]]]:
        return {"todos": [_todo("first")]}

    def second_writer(_: _TodoGraphState) -> dict[str, list[dict[str, str]]]:
        return {"todos": [_todo("second", "in_progress")]}

    graph = StateGraph(_TodoGraphState)
    graph.add_node("first_writer", first_writer)
    graph.add_node("second_writer", second_writer)
    graph.add_edge(START, "first_writer")
    graph.add_edge(START, "second_writer")
    graph.add_edge("first_writer", END)
    graph.add_edge("second_writer", END)

    result = graph.compile().invoke({"todos": []})

    assert result["todos"] in (
        [_todo("first")],
        [_todo("second", "in_progress")],
    )
