"""Regression tests for the BrandMind web composer's send decision.

Pins the bare-Enter send rule that the chat composer relies on so the
recurring keyboard regressions stay fixed: Enter sends a real message,
modifier-Enter composes a newline, and a send never fires while the
backend is unreachable, the composer is empty, or a turn is already
streaming. The rule lives in a reflex-free module so this suite runs
without standing up the Reflex runtime.
"""

from __future__ import annotations

import sys
from pathlib import Path

# The web sub-project is not a packaged module; tests get it on sys.path
# so they can import the composer logic without installing it.
_WEB_ROOT = Path(__file__).resolve().parents[2] / "web"
if str(_WEB_ROOT) not in sys.path:
    sys.path.insert(0, str(_WEB_ROOT))

from brandmind_web.composer_logic import enter_sends_message  # noqa: E402

_NO_MODIFIERS: dict = {}


def test_bare_enter_with_content_sends() -> None:
    assert enter_sends_message(
        "Enter", _NO_MODIFIERS, connected=True, streaming=False, has_content=True
    )


def test_shift_enter_composes_newline_instead_of_sending() -> None:
    assert not enter_sends_message(
        "Enter",
        {"shift_key": True},
        connected=True,
        streaming=False,
        has_content=True,
    )


def test_other_modifier_enter_does_not_send() -> None:
    for modifier in ("ctrl_key", "alt_key", "meta_key"):
        assert not enter_sends_message(
            "Enter",
            {modifier: True},
            connected=True,
            streaming=False,
            has_content=True,
        )


def test_non_enter_keys_never_send() -> None:
    assert not enter_sends_message(
        "a", _NO_MODIFIERS, connected=True, streaming=False, has_content=True
    )


def test_empty_composer_does_not_send() -> None:
    assert not enter_sends_message(
        "Enter", _NO_MODIFIERS, connected=True, streaming=False, has_content=False
    )


def test_disconnected_backend_does_not_send() -> None:
    assert not enter_sends_message(
        "Enter", _NO_MODIFIERS, connected=False, streaming=False, has_content=True
    )


def test_in_flight_turn_blocks_a_second_send() -> None:
    assert not enter_sends_message(
        "Enter", _NO_MODIFIERS, connected=True, streaming=True, has_content=True
    )
