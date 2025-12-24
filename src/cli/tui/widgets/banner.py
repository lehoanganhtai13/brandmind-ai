"""
Banner widget displaying the BRANDMIND AI logo.

Styled with Teal Mint color from brand identity.
"""

from textual.widgets import Static

# ASCII Art logo for BRANDMIND AI
BRANDMIND_AI_ASCII = """
██████╗ ██████╗  █████╗ ███╗   ██╗██████╗ ███╗   ███╗██╗███╗   ██╗██████╗      █████╗ ██╗
██╔══██╗██╔══██╗██╔══██╗████╗  ██║██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗    ██╔══██╗██║
██████╔╝██████╔╝███████║██╔██╗ ██║██║  ██║██╔████╔██║██║██╔██╗ ██║██║  ██║    ███████║██║
██╔══██╗██╔══██╗██╔══██║██║╚██╗██║██║  ██║██║╚██╔╝██║██║██║╚██╗██║██║  ██║    ██╔══██║██║
██████╔╝██║  ██║██║  ██║██║ ╚████║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║██████╔╝    ██║  ██║██║
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝     ╚═╝  ╚═╝╚═╝

⚡ AI-Powered Mentor for Brand Strategy Development ⚡
"""


class BannerWidget(Static):
    """Banner widget showing the BRANDMIND AI logo.

    Displays ASCII art logo centered with Teal Mint color.
    The banner is shown on app startup and can be hidden after first query.
    """

    DEFAULT_CSS = """
    BannerWidget {
        text-align: center;
        color: #6DB3B3;
        padding: 1;
    }
    """

    def __init__(self, id: str | None = None) -> None:
        """Initialize banner widget with ASCII logo."""
        super().__init__(BRANDMIND_AI_ASCII, id=id)
