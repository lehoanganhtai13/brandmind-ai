"""
Agent event handler for TUI integration.

Bridges agent middleware events to Textual RequestCard updates.
Uses RequestCard.handle_event which already has deduplication logic.
"""

from typing import TYPE_CHECKING, Callable, Optional

from shared.agent_middlewares.callback_types import BaseAgentEvent

if TYPE_CHECKING:
    from cli.tui.widgets.request_card import RequestCard


class TUIAgentHandler:
    """Handles agent events and updates TUI RequestCard.

    Features:
    - Delegates to RequestCard.handle_event for deduplication
    - Thread-safe UI updates via on_update callback
    - Provides set_answer for final response

    Attributes:
        card: RequestCard widget to update
        _on_update: Callback for thread-safe UI refresh
    """

    def __init__(
        self,
        card: "RequestCard",
        on_update: Optional[Callable] = None,
    ) -> None:
        """Initialize handler.

        Args:
            card: RequestCard widget to update with events
            on_update: Optional callback for thread-safe UI refresh
        """
        self.card = card
        self._on_update = on_update

    def handle_event(self, event: BaseAgentEvent) -> None:
        """Process agent event and update RequestCard.

        Delegates to RequestCard.handle_event which handles deduplication.

        Args:
            event: Agent callback event
        """
        self.card.handle_event(event)
        if self._on_update:
            self._on_update()

    def add_tool_log(self, tool_name: str, message: str) -> None:
        """Add log message for active tool.

        Args:
            tool_name: Name of the tool
            message: Log message
        """
        self.card.add_tool_log(tool_name, message)

    def set_answer(self, answer: str) -> None:
        """Set final answer.

        Args:
            answer: Final answer text
        """
        self.card.set_answer(answer)
        self.card.hide_spinner()


def create_event_callback(
    card: "RequestCard",
    call_from_thread: Callable,
) -> tuple[Callable, "TUIAgentHandler"]:
    """Create callback function for agent middleware.

    Returns a callback that handles events in thread-safe manner.

    Args:
        card: RequestCard to update
        call_from_thread: Textual's thread-safe UI update function

    Returns:
        Tuple of (callback function, TUIAgentHandler instance)
    """
    handler = TUIAgentHandler(card)

    def callback(event: BaseAgentEvent) -> None:
        # Use call_from_thread for thread-safe UI updates
        call_from_thread(handler.handle_event, event)

    return callback, handler
