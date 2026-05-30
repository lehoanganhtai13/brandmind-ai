"""Pill-shaped InputComposer — textarea, model picker, send button on one row.

Matches the ChatGPT / Gemini new-chat composer geometry: a single horizontal
row with the textarea taking the centre flex slot and the action chips
(model picker + send) inline on the right. The card uses ``28 px`` corner
radius so it reads as a pill at single-line height and as a rounded card
when the textarea grows to multi-line content (Shift+Enter). Action chips
are vertically aligned to the bottom via ``align="end"`` so they follow
the typing cursor down as the composer expands, again matching ChatGPT.

The textarea is uncontrolled: it has no ``value`` bound to server state, so a
server round-trip can never overwrite the DOM mid-keystroke. That keeps an IME
composition (Vietnamese Telex, Pinyin) from being corrupted — earlier a bound
value re-asserted the stale server echo during composition and duplicated the
just-typed syllable. Typing syncs one way to ``pending_input`` via ``on_change``
(for the send button and send body); a ``key`` bound to ``composer_epoch``
remounts the field empty after each send. A client bootstrap script keeps the
Enter key from sending while a composition is active.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens
from .model_picker import model_picker

# The Enter decision lives in this client listener, not the Reflex event: a server
# event cannot read the IME composition flag, so only a capture-phase listener can
# skip a mid-composition send and suppress the newline on a real send. Height is
# owned by the CSS `field-sizing` rule (the JS height path is a fallback only).
_COMPOSER_BOOTSTRAP_SCRIPT = """
(function bootstrap() {
  if (window.__bmComposerBootstrap) return;
  window.__bmComposerBootstrap = true;
  const nativeAutoSize = window.CSS && CSS.supports &&
    CSS.supports('field-sizing', 'content');
  function resize(ta) {
    ta.style.height = 'auto';
    const next = Math.min(ta.scrollHeight, 180);
    ta.style.height = next + 'px';
  }
  function onKeyDown(e) {
    if (e.key !== 'Enter') return;
    if (e.isComposing || e.keyCode === 229) { e.stopPropagation(); return; }
    if (e.shiftKey || e.ctrlKey || e.altKey || e.metaKey) return;
    e.preventDefault();
  }
  function attach(ta) {
    if (!ta || ta.__bmComposerBound) return;
    ta.__bmComposerBound = true;
    ta.addEventListener('keydown', onKeyDown, true);
    if (!nativeAutoSize) {
      ta.addEventListener('input', () => resize(ta));
      resize(ta);
    }
  }
  function scan() {
    document.querySelectorAll('[data-bm-composer-textarea]').forEach(attach);
  }
  scan();
  new MutationObserver(scan).observe(document.body, {
    childList: true,
    subtree: true,
  });
})();
"""


def _send_disabled() -> rx.Var:
    """Compute whether the send affordance should be inert."""
    return (
        ~BrandMindState.is_connected
        | BrandMindState.is_streaming
        | (BrandMindState.pending_input == "")
    )


def input_composer() -> rx.Component:
    """Pill-shaped composer with inline textarea, model picker, and send.

    Renders the composer as a single horizontal row so the empty-state
    matches the ChatGPT / Gemini visual language (one tight pill, all
    affordances on the same axis). When the textarea grows to multi-line
    content the card height expands up to ``180 px`` while the action
    chips stay pinned to the bottom-right via ``align="end"`` — the same
    way ChatGPT's expanded composer (Image #70) keeps its action row at
    the cursor's footing.
    """
    placeholder = rx.cond(
        BrandMindState.is_connected,
        "Message BrandMind",
        "Reconnecting...",
    )

    send_button = rx.button(
        rx.icon(tag="arrow_up", size=16),
        on_click=BrandMindState.send_message,
        disabled=_send_disabled(),
        style={
            "background_color": tokens.ACCENT_TEAL_SOLID,
            "color": "#003732",
            "width": "32px",
            "height": "32px",
            "min_width": "32px",
            "padding": "0",
            "border_radius": tokens.RADIUS_PILL,
            "cursor": "pointer",
            "flex_shrink": "0",
        },
    )

    composer_row = rx.hstack(
        rx.text_area(
            placeholder=placeholder,
            on_change=BrandMindState.set_pending_input,
            on_key_down=BrandMindState.on_composer_key_down,
            read_only=~BrandMindState.is_connected | BrandMindState.is_streaming,
            rows="1",
            key=BrandMindState.composer_epoch.to_string(),
            custom_attrs={"data-bm-composer-textarea": "true"},
            style={
                "flex": "1",
                "min_height": "24px",
                "max_height": "180px",
                "background_color": "transparent",
                "color": tokens.TEXT_PRIMARY,
                "font_family": tokens.FONT_SANS,
                "font_size": "15px",
                "line_height": "1.5",
                "border": "none",
                "outline": "none",
                "box_shadow": "none",
                "padding": "0",
                "resize": "none",
                "overflow_y": "auto",
                "field_sizing": "content",
            },
        ),
        model_picker(),
        send_button,
        align="end",
        spacing="2",
        width="100%",
    )

    composer_card = rx.box(
        composer_row,
        style={
            "width": "100%",
            "max_width": "720px",
            "margin": "0 auto",
            "background_color": tokens.BG_SURFACE_1,
            "border": f"1px solid {tokens.GLASS_BORDER}",
            "border_radius": tokens.RADIUS_COMPOSER,
            "padding": "10px 10px 10px 22px",
            "transition": "border-color 160ms ease, box-shadow 160ms ease",
            "_focus_within": {
                "border_color": "rgba(95, 179, 168, 0.45)",
                "box_shadow": "0 0 0 3px rgba(95, 179, 168, 0.10)",
            },
        },
    )

    return rx.box(
        composer_card,
        padding="12px 24px 20px 24px",
        width="100%",
        on_mount=rx.call_script(_COMPOSER_BOOTSTRAP_SCRIPT),
        style={
            "background_color": tokens.BG_CANVAS,
        },
    )
