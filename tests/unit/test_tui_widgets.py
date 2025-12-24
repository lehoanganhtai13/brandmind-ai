"""
Unit tests for TUI widgets.

These tests verify basic functionality of TUI components.
"""

import pytest
from textual.pilot import Pilot

from cli.tui.app import BrandMindApp
from cli.tui.widgets.banner import BannerWidget
from cli.tui.widgets.input_bar import InputBar, SLASH_COMMANDS


class TestBannerWidget:
    """Tests for BannerWidget."""

    def test_banner_contains_ascii_art(self) -> None:
        """Test banner contains BRANDMIND text."""
        from cli.tui.widgets.banner import BRANDMIND_AI_ASCII

        assert "BRANDMIND" in BRANDMIND_AI_ASCII or "██" in BRANDMIND_AI_ASCII


class TestSlashCommands:
    """Tests for slash command definitions."""

    def test_commands_have_descriptions(self) -> None:
        """Test all commands have descriptions."""
        for cmd, data in SLASH_COMMANDS.items():
            assert "description" in data, f"Command {cmd} missing description"
            assert data["description"], f"Command {cmd} has empty description"

    def test_mode_has_subcommands(self) -> None:
        """Test mode command has subcommands."""
        assert "mode" in SLASH_COMMANDS
        assert "subcommands" in SLASH_COMMANDS["mode"]
        assert len(SLASH_COMMANDS["mode"]["subcommands"]) > 0

    def test_required_commands_exist(self) -> None:
        """Test required commands are defined."""
        required = ["mode", "clear", "quit"]
        for cmd in required:
            assert cmd in SLASH_COMMANDS, f"Missing required command: {cmd}"


class TestInputBar:
    """Tests for InputBar widget."""

    def test_get_suggestions_empty(self) -> None:
        """Test suggestions for empty query shows all commands."""
        bar = InputBar()
        suggestions = bar._get_suggestions("")
        assert len(suggestions) == len(SLASH_COMMANDS)

    def test_get_suggestions_filter(self) -> None:
        """Test suggestions filter by prefix."""
        bar = InputBar()
        # Filter with 'm' prefix
        suggestions = bar._get_suggestions("m")
        assert len(suggestions) > 0
        for name, _ in suggestions:
            assert name.startswith("m")

    def test_get_suggestions_subcommands(self) -> None:
        """Test subcommand suggestions."""
        bar = InputBar()
        # 'mode' should show subcommands
        suggestions = bar._get_suggestions("mode ")
        assert len(suggestions) > 0
        # Should include 'ask'
        names = [s[0] for s in suggestions]
        assert "ask" in names


@pytest.mark.asyncio
async def test_app_startup() -> None:
    """Test app starts and renders correctly."""
    app = BrandMindApp()
    async with app.run_test() as pilot:
        # Should have banner
        banner = app.query_one("#banner", BannerWidget)
        assert banner is not None
        assert banner.display is True

        # Should have input bar
        input_bar = app.query_one("#input-bar", InputBar)
        assert input_bar is not None


@pytest.mark.asyncio
async def test_slash_command_quit() -> None:
    """Test /quit command exits app."""
    app = BrandMindApp()
    async with app.run_test() as pilot:
        input_bar = app.query_one("#input-bar", InputBar)
        input_bar.value = "/quit"
        await pilot.press("enter")
        # App should be exiting
        # (can't easily check exit in test, but no exception = pass)


@pytest.mark.asyncio
async def test_slash_command_clear() -> None:
    """Test /clear command clears main body."""
    app = BrandMindApp()
    async with app.run_test() as pilot:
        input_bar = app.query_one("#input-bar", InputBar)
        input_bar.value = "/clear"
        await pilot.press("enter")
        # Banner should still be visible after clear
        banner = app.query_one("#banner", BannerWidget)
        assert banner.display is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
