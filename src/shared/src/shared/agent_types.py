"""
Shared Agent Types

This module contains shared type definitions used across the agent system
to ensure type consistency and avoid duplication.
"""

from typing import Literal
from typing_extensions import TypedDict


class TodoItem(TypedDict):
    """
    Represents a structured todo item with all mandatory fields.

    This data structure defines the standard format for todo items used throughout
    the agent system to maintain consistency and enable comprehensive task tracking.

    Attributes:
        content (str): Clear, actionable description of the task
        status (str): Current task status - "pending", "in_progress", or "completed"
        activeForm (str): Present continuous description of active work
        priority (str): Task priority level for scheduling decisions
    """
    content: str
    status: Literal["pending", "in_progress", "completed"]
    activeForm: str
    priority: Literal["high", "medium", "low"]