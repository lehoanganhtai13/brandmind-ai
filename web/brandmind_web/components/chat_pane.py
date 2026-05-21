"""ChatPane container — vertical scroll of messages + sticky composer.

Implements ``docs/web_design.md`` § 9.3 with Codex review Finding 4
applied: the empty state hero is smaller (28 px), anchored in the upper
third of the canvas, and offers three prefill prompt chips so the
first interaction has texture. Glass effects stay off the scroll
surface to avoid streaming-token repaint judder.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens
from .input_composer import input_composer
from .message_bubble import message_bubble

_STARTER_PROMPTS: tuple[str, ...] = (
    "I'm launching a specialty cafe and need a brand strategy.",
    "Help me reposition an existing F&B brand.",
    "Refresh the visual identity of my restaurant.",
)


def _prompt_chip(prompt: str) -> rx.Component:
    """One starter-prompt chip that prefills the composer on click."""
    return rx.button(
        rx.text(
            prompt,
            style={
                "color": tokens.TEXT_SECONDARY,
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "line_height": "1.45",
                "text_align": "left",
            },
        ),
        on_click=BrandMindState.set_pending_input(prompt),
        variant="ghost",
        style={
            "padding": "10px 14px",
            "border_radius": tokens.RADIUS_LG,
            "border": f"1px solid {tokens.GLASS_BORDER}",
            "background_color": "transparent",
            "cursor": "pointer",
            "height": "auto",
            "max_width": "100%",
            "white_space": "normal",
            "transition": "border-color 160ms ease, background-color 160ms ease",
            "_hover": {
                "border_color": "rgba(95, 179, 168, 0.35)",
                "background_color": "rgba(95, 179, 168, 0.06)",
            },
        },
    )


def _empty_state() -> rx.Component:
    """Calm hero with three prefill prompts to seed the first turn."""
    return rx.center(
        rx.vstack(
            rx.text(
                "Where would you like to start?",
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_DISPLAY,
                    "font_size": "28px",
                    "font_weight": "400",
                    "letter_spacing": "-0.01em",
                    "line_height": "1.2",
                    "text_align": "center",
                },
            ),
            rx.text(
                "BrandMind is your brand-strategy mentor for F&B. Pick a "
                "prompt below or write your own.",
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "14px",
                    "line_height": "1.6",
                    "max_width": "440px",
                    "text_align": "center",
                },
            ),
            rx.vstack(
                *[_prompt_chip(p) for p in _STARTER_PROMPTS],
                spacing="2",
                align="stretch",
                width="100%",
                max_width="440px",
                padding_top="8px",
            ),
            spacing="4",
            align="center",
            padding_top="14vh",
        ),
        flex="1",
        width="100%",
        padding="0 24px",
    )


_TABLE_BULLET_SCRIPT = """
(function bootstrap() {
  if (window.__bmTableBulletsBootstrap) return;
  window.__bmTableBulletsBootstrap = true;
  function extractMarker(group) {
    const first = group[0];
    if (!first || first.nodeType !== 3) return null;
    const v = first.nodeValue;
    let m = v.match(/^(\\s*)(\\*|•)\\s+/);
    if (m) {
      first.nodeValue = v.slice(m[0].length);
      return { marker: '•', kind: 'bullet' };
    }
    m = v.match(/^(\\s*)(\\d+)\\.\\s+/);
    if (m) {
      first.nodeValue = v.slice(m[0].length);
      return { marker: m[2] + '.', kind: 'numbered' };
    }
    return null;
  }
  function fixCell(cell) {
    if (cell.__bmBulletsFixed) return;
    cell.__bmBulletsFixed = true;
    const groups = [[]];
    Array.from(cell.childNodes).forEach(node => {
      if (node.nodeType === 1 && node.tagName === 'BR') {
        groups.push([]);
      } else {
        groups[groups.length - 1].push(node);
      }
    });
    if (groups.length === 1 && groups[0].length === 0) return;
    const blocks = groups
      .filter(g => g.length > 0)
      .map(group => ({ group, meta: extractMarker(group) }));
    let bulletSeen = false;
    blocks.forEach(b => {
      if (b.meta && b.meta.kind === 'bullet') bulletSeen = true;
      if (b.meta && b.meta.kind === 'numbered' && bulletSeen) {
        b.meta.kind = 'sub-numbered';
      }
    });
    while (cell.firstChild) cell.removeChild(cell.firstChild);
    blocks.forEach(({ group, meta }) => {
      if (!meta) {
        const plain = document.createElement('div');
        group.forEach(n => plain.appendChild(n));
        cell.appendChild(plain);
        return;
      }
      const row = document.createElement('div');
      row.style.display = 'flex';
      row.style.alignItems = 'flex-start';
      row.style.gap = meta.kind === 'bullet' ? '0.4em' : '0.3em';
      row.style.marginTop = meta.kind === 'bullet' ? '2px' : '1px';
      if (meta.kind === 'sub-numbered') {
        row.style.marginLeft = '1.5em';
      }
      const marker = document.createElement('span');
      marker.textContent = meta.marker;
      marker.style.flex = '0 0 auto';
      if (meta.kind !== 'bullet') {
        marker.style.minWidth = '1.05em';
        marker.style.fontVariantNumeric = 'tabular-nums';
      }
      const body = document.createElement('span');
      body.style.flex = '1 1 auto';
      body.style.minWidth = '0';
      group.forEach(n => body.appendChild(n));
      row.appendChild(marker);
      row.appendChild(body);
      cell.appendChild(row);
    });
  }
  function scan() {
    document.querySelectorAll(
      '[data-bm-chat-scroll] td, [data-bm-chat-scroll] th'
    ).forEach(fixCell);
  }
  scan();
  new MutationObserver(scan).observe(document.body, {
    childList: true,
    subtree: true,
  });
})();
"""


_AUTO_SCROLL_SCRIPT = """
(function bootstrap() {
  if (window.__bmAutoScrollBootstrap) return;
  window.__bmAutoScrollBootstrap = true;
  const THRESHOLD_PX = 96;
  function attachTo(viewport) {
    if (!viewport || viewport.__bmAutoScroll) return;
    viewport.__bmAutoScroll = true;
    let pinned = true;
    const nearBottom = () =>
      viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight
        < THRESHOLD_PX;
    viewport.addEventListener(
      'scroll',
      () => { pinned = nearBottom(); },
      { passive: true }
    );
    const stick = () => {
      if (pinned) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    };
    new MutationObserver(stick).observe(viewport, {
      childList: true,
      subtree: true,
      characterData: true,
    });
    new ResizeObserver(stick).observe(viewport);
    stick();
  }
  function scan() {
    document
      .querySelectorAll('[data-bm-chat-scroll]')
      .forEach(attachTo);
  }
  scan();
  new MutationObserver(scan).observe(document.body, {
    childList: true,
    subtree: true,
  });
})();
"""


def _message_scroll() -> rx.Component:
    """Vertical scroll of message bubbles within a centered reading column.

    Uses a plain ``rx.box`` (instead of Radix ``scroll_area``) so the
    scrolling element itself carries ``data-bm-chat-scroll`` — the
    auto-scroll script can then attach directly without having to guess
    which descendant Radix designates as the viewport. A small
    client-side script pins the scroll to the bottom while the agent
    streams tokens or appends timeline entries, mirroring the ChatGPT /
    Gemini behaviour: the viewport stays glued to the latest chunk
    unless the user scrolls up to read earlier content, in which case
    auto-scroll backs off until they return to the bottom.
    """
    return rx.box(
        rx.vstack(
            rx.foreach(
                BrandMindState.messages,
                lambda msg, idx: message_bubble(msg, idx),
            ),
            spacing="1",
            align="stretch",
            padding="28px 24px 24px 24px",
            max_width="880px",
            width="100%",
            margin_x="auto",
        ),
        custom_attrs={"data-bm-chat-scroll": "true"},
        style={
            "flex": "1",
            "min_height": "0",
            "width": "100%",
            "overflow_y": "auto",
            "overflow_x": "hidden",
            "scrollbar_width": "thin",
            "scrollbar_color": "rgba(255, 255, 255, 0.18) transparent",
            "&::-webkit-scrollbar": {"width": "10px"},
            "&::-webkit-scrollbar-track": {"background": "transparent"},
            "&::-webkit-scrollbar-thumb": {
                "background": "rgba(255, 255, 255, 0.16)",
                "border_radius": "8px",
                "border": "2px solid transparent",
                "background_clip": "padding-box",
            },
            "&::-webkit-scrollbar-thumb:hover": {
                "background": "rgba(255, 255, 255, 0.26)",
                "background_clip": "padding-box",
            },
        },
    )


def chat_pane() -> rx.Component:
    """Render the ChatPane — message scroll + sticky InputComposer.

    The ``on_mount`` hook boots the auto-scroll observer; the script
    polls until the message viewport appears in the DOM so it survives
    the empty-state ↔ scroll-area swap when the first message lands.
    """
    return rx.vstack(
        rx.cond(
            BrandMindState.messages.length() == 0,
            _empty_state(),
            _message_scroll(),
        ),
        input_composer(),
        spacing="0",
        align="stretch",
        flex="1",
        width="100%",
        height="100%",
        on_mount=[
            rx.call_script(_AUTO_SCROLL_SCRIPT),
            rx.call_script(_TABLE_BULLET_SCRIPT),
        ],
        style={
            "background_color": tokens.BG_CANVAS,
            "background_image": tokens.CANVAS_AMBIENT,
            "overflow": "hidden",
        },
    )
