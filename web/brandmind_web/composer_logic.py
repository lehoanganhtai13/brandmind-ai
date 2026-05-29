"""Reflex-free composer decision rules for the BrandMind web UI.

Holds the pure send/keyboard rules the composer relies on so they can
be regression-tested without standing up the Reflex runtime. The Reflex
state imports these and keeps only the stateful side effects (clearing
the draft, flipping the streaming flag) in the event handler itself.
"""

from __future__ import annotations


def enter_sends_message(
    key: str,
    modifiers: dict,
    *,
    connected: bool,
    streaming: bool,
    has_content: bool,
) -> bool:
    """Decide whether a composer keydown is a deliberate send.

    A send fires only on a bare Enter while connected, not already
    streaming, and with non-empty content. Any modifier key composes a
    newline instead, and the IME-composition skip is handled earlier by
    the client bootstrap listener so this rule never sees a
    mid-composition Enter.

    Args:
        key (str): The event key name from the keyboard event.
        modifiers (dict): ``KeyInputInfo`` modifier flags for the event.
        connected (bool): Whether the backend stream is reachable.
        streaming (bool): Whether a turn is already in flight.
        has_content (bool): Whether the trimmed composer body is non-empty.

    Returns:
        should_send (bool): ``True`` when the keystroke should submit.
    """
    if key != "Enter":
        return False
    if (
        modifiers.get("shift_key")
        or modifiers.get("ctrl_key")
        or modifiers.get("alt_key")
        or modifiers.get("meta_key")
    ):
        return False
    return connected and not streaming and has_content
