#!/usr/bin/env python3
"""
Test script for BrandMind TUI.

Run this script to test the TUI interface:
    python tests/test_tui_manual.py

Or from project root with venv:
    source .venv/bin/activate && cd src && python -m cli.tui.app
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from cli.tui.app import run_tui


def main() -> None:
    """Run the TUI test."""
    print("Starting BrandMind TUI...")
    print("Press Ctrl+C to quit")
    print("-" * 40)
    run_tui()


if __name__ == "__main__":
    main()
