"""ChatPane container — empty centred hero, or scrolling messages + composer.

Implements ``docs/web_design.md`` § 9.3. The empty state mirrors the
Claude / Gemini / ChatGPT new-chat pattern: a single serif greeting
above an inline composer, vertically centred in the canvas, no
pre-filled starter chips. Once the first turn lands, the layout
switches to the conventional scrolling-messages + sticky-bottom
composer. Glass effects stay off the scroll surface to avoid
streaming-token repaint judder.
"""

from __future__ import annotations

import reflex as rx

from ..state import BrandMindState
from . import tokens
from .input_composer import input_composer
from .message_bubble import message_bubble


def _empty_state() -> rx.Component:
    """Minimal centered empty-state — serif greeting above inline composer.

    Mirrors the Claude / Gemini / ChatGPT new-chat pattern: a single
    quiet hero line above a centered composer with no pre-filled
    starter chips, so first-touch lands with iPhone-grade polish. The
    block centres vertically inside the chat-canvas flex column and
    reveals with a soft 600 ms ease-out fade. The composer is mounted
    here when ``messages`` is empty and at the bottom of
    :func:`chat_pane` after the first turn — Reflex re-mounts it on
    the transition, which is safe because composer state lives on
    :class:`BrandMindState`.
    """
    return rx.center(
        rx.vstack(
            rx.text(
                "Where would you like to start?",
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_DISPLAY,
                    "font_size": "40px",
                    "font_weight": "400",
                    "letter_spacing": "-0.025em",
                    "line_height": "1.15",
                    "text_align": "center",
                    "margin": "0",
                },
            ),
            rx.box(
                input_composer(),
                style={
                    "width": "100%",
                    "max_width": "720px",
                },
            ),
            spacing="6",
            align="center",
            width="100%",
            max_width="720px",
            style={
                "animation": (
                    "bm-empty-reveal 600ms cubic-bezier(0.16, 1, 0.3, 1) both"
                ),
            },
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


def _chatting_layout() -> rx.Component:
    """Render the active-chat layout: scrolling messages + bottom composer.

    Used once the first user turn lands so the composer can anchor to
    the bottom of the canvas in the conventional chat pattern. The
    empty-state layout (:func:`_empty_state`) renders the composer
    inline with the centred greeting; this branch resumes the
    sticky-bottom anchor after a message exists.
    """
    return rx.vstack(
        _message_scroll(),
        input_composer(),
        spacing="0",
        align="stretch",
        flex="1",
        width="100%",
        min_height="0",
    )


def chat_pane() -> rx.Component:
    """Render the ChatPane — empty centred hero, or scroll + composer.

    The ``on_mount`` hook boots the auto-scroll observer; the script
    polls until the message viewport appears in the DOM so it survives
    the empty-state ↔ scroll-area swap when the first message lands.
    """
    return rx.vstack(
        rx.cond(
            BrandMindState.messages.length() == 0,
            _empty_state(),
            _chatting_layout(),
        ),
        spacing="0",
        align="stretch",
        flex="1 1 0",
        min_width="0",
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
