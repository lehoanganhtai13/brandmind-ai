"""
Input bar with hierarchical slash command autocomplete.

Pressing "/" shows available commands at current level.
Typing filters suggestions. Enter completes the selection.
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Input, Static

# Command hierarchy definition
SLASH_COMMANDS: dict[str, dict] = {
    "mode": {
        "description": "Change operation mode",
        "subcommands": {
            "ask": "Interactive Q&A with agent",
            "search-kg": "Search Knowledge Graph directly",
            "search-docs": "Search Document Library directly",
        },
    },
    "clear": {
        "description": "Clear conversation history",
        "subcommands": {},
    },
    "quit": {
        "description": "Exit the application",
        "subcommands": {},
    },
    "help": {
        "description": "Show available commands",
        "subcommands": {},
    },
}


class SuggestionItem(Static):
    """Single suggestion item in the popup.

    Styled like Gemini CLI - no border, highlighted background for selection.
    """

    DEFAULT_CSS = """
    SuggestionItem {
        width: 100%;
        height: 1;
        padding: 0 1;
        background: transparent;
    }

    SuggestionItem.selected {
        background: #30363d;
    }
    """

    def __init__(self, name: str, description: str) -> None:
        """Initialize suggestion item.

        Args:
            name: Command name
            description: Command description
        """
        # Use fixed width columns for alignment
        super().__init__(f"[bold]{name:<20}[/bold] [dim]{description}[/dim]")
        self.command_name = name


class SuggestionPopup(Vertical):
    """Popup widget showing command suggestions.

    Styled like Gemini CLI - no border, full width, simple highlight.
    Shows filtered suggestions based on user typing.
    Positioned above the input bar using dock: bottom with offset.
    """

    DEFAULT_CSS = """
    SuggestionPopup {
        background: #0d1117;
        padding: 0;
        border: none;
        dock: bottom;
        offset: 0 -4;
        width: 100%;
        max-height: 10;
        margin: 0 2;
    }
    """

    selected_index: reactive[int] = reactive(0)

    def __init__(self, suggestions: list[tuple[str, str]]) -> None:
        """Initialize popup with suggestions.

        Args:
            suggestions: List of (name, description) tuples
        """
        super().__init__()
        self.suggestions = suggestions

    def compose(self) -> ComposeResult:
        """Compose suggestion items."""
        for name, desc in self.suggestions:
            yield SuggestionItem(name, desc)

    def on_mount(self) -> None:
        """Update selection on mount."""
        self._update_selection()

    def watch_selected_index(self, value: int) -> None:
        """React to selection changes."""
        self._update_selection()

    async def update_suggestions(self, suggestions: list[tuple[str, str]]) -> None:
        """Update popup with new suggestions without remounting.

        Only updates if suggestions actually changed to avoid unnecessary work.

        Args:
            suggestions: New list of (name, description) tuples
        """
        # Skip update if suggestions haven't changed
        if suggestions == self.suggestions:
            return

        # Update suggestions list
        self.suggestions = suggestions
        self.selected_index = 0

        # Remove all current items and add new ones
        # This is simpler and more reliable than differential update
        await self.query(SuggestionItem).remove()
        for name, desc in suggestions:
            await self.mount(SuggestionItem(name, desc))

    def _update_selection(self) -> None:
        """Update visual selection state."""
        items = list(self.query(SuggestionItem))
        for i, item in enumerate(items):
            item.set_class(i == self.selected_index, "selected")

    def move_selection(self, delta: int) -> None:
        """Move selection up or down.

        Args:
            delta: -1 for up, +1 for down
        """
        new_index = self.selected_index + delta
        if 0 <= new_index < len(self.suggestions):
            self.selected_index = new_index

    def get_selected_command(self) -> str | None:
        """Get currently selected command name.

        Returns:
            Selected command name or None if no selection
        """
        if 0 <= self.selected_index < len(self.suggestions):
            return self.suggestions[self.selected_index][0]
        return None


class InputBar(Input):
    """Input bar with slash command support.

    Features:
    - "/" triggers command popup
    - Hierarchical navigation (/ -> /mode -> /mode ask)
    - Arrow keys to navigate suggestions
    - Tab/Enter to complete selection
    """

    class CommandSubmitted(Message):
        """Message emitted when a command is submitted."""

        def __init__(self, command: str) -> None:
            """Initialize message.

            Args:
                command: Full command string
            """
            super().__init__()
            self.command = command

    class QuerySubmitted(Message):
        """Message emitted when a query is submitted."""

        def __init__(self, query: str) -> None:
            """Initialize message.

            Args:
                query: User query string
            """
            super().__init__()
            self.query = query

    BINDINGS = [
        ("up", "history_prev", "Previous command"),
        ("down", "history_next", "Next command"),
    ]

    # fmt: off
    DEFAULT_CSS: ClassVar[str] = """
    InputBar {
        dock: bottom;
        width: 100%;
        margin: 0 2;
        border: round #30363d;
        background: #161b22;
    }

    InputBar:focus {
        border: round #6DB3B3;
    }
    """
    # fmt: on

    def __init__(
        self,
        placeholder: str = "> Type message or / for commands",
        id: str | None = None,
    ) -> None:
        """Initialize input bar.

        Args:
            placeholder: Placeholder text
            id: Widget ID
        """
        super().__init__(placeholder=placeholder, id=id)
        self._popup: SuggestionPopup | None = None

        # Command history
        self._history: list[str] = []
        self._history_index: int = -1  # -1 means not browsing history
        self._current_input: str = ""  # Save current input when browsing

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Show/update suggestions as user types.

        Args:
            event: Input changed event
        """
        value = event.value

        if value.startswith("/"):
            await self._show_suggestions(value[1:])
        elif self._popup:
            await self._hide_popup()

    async def _show_suggestions(self, query: str) -> None:
        """Show filtered suggestions for current query.

        Args:
            query: Query string after the /
        """
        suggestions = self._get_suggestions(query)

        if suggestions:
            if self._popup:
                # Update existing popup instead of recreating
                await self._popup.update_suggestions(suggestions)
            else:
                # Create new popup on first show
                self._popup = SuggestionPopup(suggestions)
                await self.app.mount(self._popup)
        elif self._popup:
            await self._hide_popup()

    def _get_suggestions(self, query: str) -> list[tuple[str, str]]:
        """Get filtered suggestions for query.

        Args:
            query: Query string after the /

        Returns:
            List of (name, description) tuples
        """
        parts = query.split()

        if not parts:
            # Top level - show all commands
            return [(cmd, data["description"]) for cmd, data in SLASH_COMMANDS.items()]

        if len(parts) == 1:
            prefix = parts[0].lower()
            # Check if exact match with subcommands
            if prefix in SLASH_COMMANDS and SLASH_COMMANDS[prefix]["subcommands"]:
                cmd_data = SLASH_COMMANDS[prefix]
                return [(sub, desc) for sub, desc in cmd_data["subcommands"].items()]
            # Filter by prefix
            return [
                (cmd, data["description"])
                for cmd, data in SLASH_COMMANDS.items()
                if cmd.startswith(prefix)
            ]

        # len(parts) >= 2: Check if we have a complete command
        parent = parts[0].lower()
        if parent in SLASH_COMMANDS:
            subcommands = SLASH_COMMANDS[parent]["subcommands"]
            # If second part is exact match (full subcommand), don't show suggestions
            if parts[1].lower() in subcommands:
                return []
            # Otherwise filter by prefix
            prefix = parts[-1].lower()
            return [
                (sub, desc)
                for sub, desc in subcommands.items()
                if sub.startswith(prefix)
            ]

        return []

    async def _hide_popup(self) -> None:
        """Hide the suggestion popup."""
        if self._popup:
            await self._popup.remove()
            self._popup = None

    def action_history_prev(self) -> None:
        """Navigate to previous command in history (up arrow)."""
        # If browsing history, continue even if popup appeared
        if self._history_index != -1:
            self._navigate_history(-1)
        elif self._popup:
            self._popup.move_selection(-1)
        else:
            self._navigate_history(-1)

    def action_history_next(self) -> None:
        """Navigate to next command in history (down arrow)."""
        # If browsing history, continue even if popup appeared
        if self._history_index != -1:
            self._navigate_history(1)
        elif self._popup:
            self._popup.move_selection(1)
        else:
            self._navigate_history(1)

    async def on_key(self, event) -> None:
        """Handle tab key for completion."""
        if self._popup and event.key == "tab":
            selected = self._popup.get_selected_command()
            if selected:
                await self._complete_command(selected)
            event.prevent_default()
            event.stop()

    async def _complete_command(self, command: str) -> None:
        """Complete input with selected command.

        Args:
            command: Command to complete with
        """
        current = self.value.strip()

        if current.startswith("/"):
            # Parse current command parts
            cmd_part = current[1:]  # Remove leading /
            parts = cmd_part.split()

            if len(parts) == 0:
                # Just "/" - complete with top level command
                self.value = f"/{command} "
            elif parts[0] in SLASH_COMMANDS:
                # Valid parent - preserve it when adding subcommand
                self.value = f"/{parts[0]} {command} "
            else:
                # Partial top-level typing - replace with matched command
                self.value = f"/{command} "
        else:
            self.value = f"/{command} "

        self.cursor_position = len(self.value)
        await self._hide_popup()

    async def action_submit(self) -> None:
        """Handle Enter key - submit command or show subcommands.

        Behavior:
        - If popup visible & command selected:
          - Commands without subcommands (/quit, /help, /clear) → submit immediately
          - Commands with subcommands (/mode) → complete and show subcommands
        - If no popup:
          - Submit current value
        """
        value = self.value.strip()

        # If popup visible, handle selected command
        if self._popup:
            selected = self._popup.get_selected_command()
            if selected:
                # Check if this is a top-level command (not a subcommand)
                current = value
                is_top_level = (
                    not current.startswith("/")
                    or current == "/"
                    or (current.startswith("/") and len(current[1:].split()) <= 1)
                )

                if is_top_level and selected in SLASH_COMMANDS:
                    # Top-level command selected
                    cmd_data = SLASH_COMMANDS[selected]
                    if cmd_data["subcommands"]:
                        # Has subcommands - complete and show them
                        self.value = f"/{selected} "
                        self.cursor_position = len(self.value)
                        # Popup will automatically update via on_input_changed
                        return
                    else:
                        # No subcommands - submit immediately
                        await self._hide_popup()
                        cmd = f"/{selected}"
                        self._add_to_history(cmd)
                        self.post_message(self.CommandSubmitted(cmd))
                        self.value = ""
                        return
                else:
                    # Subcommand selected - complete to full command and submit
                    await self._complete_command(selected)
                    await self._hide_popup()
                    final_value = self.value.strip()
                    self._add_to_history(final_value)
                    self.post_message(self.CommandSubmitted(final_value))
                    self.value = ""
                    return

        # No popup or no selection - submit current value as-is
        await self._hide_popup()

        if not value:
            return

        # Add to history before submitting
        self._add_to_history(value)

        if value.startswith("/"):
            self.post_message(self.CommandSubmitted(value))
        else:
            self.post_message(self.QuerySubmitted(value))

        self.value = ""

    def _navigate_history(self, direction: int) -> None:
        """Navigate command history.

        Args:
            direction: -1 for older (up), +1 for newer (down)
        """
        if not self._history:
            return

        if self._history_index == -1:
            # Starting to browse history - save current input
            self._current_input = self.value
            if direction == -1:
                # Up pressed - go to most recent (last item)
                self._history_index = len(self._history) - 1
            else:
                return  # Already at newest, nothing to do
        else:
            # direction -1 = older = lower index
            # direction +1 = newer = higher index
            new_index = self._history_index + direction
            if new_index < 0:
                # At oldest, can't go further back
                return
            elif new_index >= len(self._history):
                # Past newest - return to current input
                self._history_index = -1
                self.value = self._current_input
                self.cursor_position = len(self.value)
                return
            else:
                self._history_index = new_index

        # Show history item
        self.value = self._history[self._history_index]
        self.cursor_position = len(self.value)

    def _add_to_history(self, value: str) -> None:
        """Add command to history.

        Args:
            value: Command or query to add
        """
        # Strip whitespace for consistent comparison
        value = value.strip()
        if not value:
            return

        # Remove duplicate from anywhere in history (move to end)
        if value in self._history:
            self._history.remove(value)
        self._history.append(value)

        self._history_index = -1  # Reset browse position
        self._current_input = ""
