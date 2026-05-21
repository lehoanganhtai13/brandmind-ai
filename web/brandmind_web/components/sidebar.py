"""Sidebar — collapsible left rail showing chat list + phase progress.

Two stacked sections:

- **Chats**: list of brand-strategy chats persisted on the backend with
  a "+ New chat" button. The active chat is highlighted; clicking
  another chat repaints the scroll via ``BrandMindState.switch_chat``.
- **Phases**: scope-dependent phase list with per-item states (idle /
  current / completed) following ``docs/web_design.md`` § 9.2.

Both sections collapse together into a 56 px rail (Codex review
Finding 5: numbered glyphs survive the collapse). State source-of-truth
is :class:`BrandMindState` — the component only renders.
"""

from __future__ import annotations

import reflex as rx

from ..models import SessionInfo
from ..state import BrandMindState
from . import tokens

_PHASE_DISPLAY_EN: dict[str, str] = {
    "phase_0": "Diagnosis",
    "phase_0_5": "Brand audit",
    "phase_1": "Market analysis",
    "phase_2": "Positioning",
    "phase_3": "Identity system",
    "phase_4": "Communication",
    "phase_5": "KPIs & roadmap",
}


def _phase_label(phase_key: rx.Var) -> rx.Var:
    """Project a phase id to its English UI label, falling back to the id."""
    label: rx.Var = phase_key
    for key, value in _PHASE_DISPLAY_EN.items():
        label = rx.cond(phase_key == key, value, label)
    return label


def _phase_number(phase_key: rx.Var) -> rx.Var:
    """Render the rail glyph for a phase id (numeric, with the 0.5 case)."""
    glyph: rx.Var = phase_key
    glyph = rx.cond(phase_key == "phase_0", "0", glyph)
    glyph = rx.cond(phase_key == "phase_0_5", "½", glyph)
    glyph = rx.cond(phase_key == "phase_1", "1", glyph)
    glyph = rx.cond(phase_key == "phase_2", "2", glyph)
    glyph = rx.cond(phase_key == "phase_3", "3", glyph)
    glyph = rx.cond(phase_key == "phase_4", "4", glyph)
    glyph = rx.cond(phase_key == "phase_5", "5", glyph)
    return glyph


def _phase_glyph(phase_key: rx.Var, color: rx.Var, base_size: str) -> rx.Component:
    """Render the phase pill's glyph with vertical metrics tuned per character.

    The half-phase ``½`` (U+00BD) sits above the cap height of the digits it
    neighbours, so a flat ``align-items: center`` row leaves it visually
    high. Bumping its size + nudging it down a hair restores parity with
    the digit set on the same row.
    """
    base_style = {
        "font_family": tokens.FONT_SANS,
        "font_weight": "600",
        "line_height": "1",
        "color": color,
        "display": "inline-block",
    }
    return rx.cond(
        phase_key == "phase_0_5",
        rx.el.span(
            "½",
            style={
                **base_style,
                "font_size": "15px",
                "transform": "translateY(1px)",
                "font_variant_numeric": "stacked-fractions",
            },
        ),
        rx.el.span(
            _phase_number(phase_key),
            style={**base_style, "font_size": base_size},
        ),
    )


def _expanded_row(phase_key: rx.Var) -> rx.Component:
    """One row in the expanded sidebar — number pill + label."""
    is_current = phase_key == BrandMindState.current_phase
    is_done = BrandMindState.completed_phases.contains(phase_key)

    pill = rx.box(
        _phase_glyph(
            phase_key,
            rx.cond(is_current | is_done, "#003732", tokens.TEXT_SECONDARY),
            "12px",
        ),
        style={
            "width": "26px",
            "height": "26px",
            "min_width": "26px",
            "border_radius": tokens.RADIUS_PILL,
            "display": "flex",
            "align_items": "center",
            "justify_content": "center",
            "background_color": rx.cond(
                is_current | is_done,
                tokens.ACCENT_TEAL_SOLID,
                "transparent",
            ),
            "border": rx.cond(
                is_current | is_done,
                "none",
                f"1px solid {tokens.GLASS_BORDER}",
            ),
        },
    )

    return rx.hstack(
        pill,
        rx.text(
            _phase_label(phase_key),
            style={
                "color": rx.cond(
                    is_current | is_done,
                    tokens.TEXT_PRIMARY,
                    tokens.TEXT_MUTED,
                ),
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "font_weight": rx.cond(is_current, "600", "400"),
                "line_height": "1.4",
            },
        ),
        spacing="3",
        align="center",
        padding="6px 16px",
        width="100%",
    )


def _collapsed_rail_item(phase_key: rx.Var) -> rx.Component:
    """One numbered pill on the collapsed rail with hover tooltip."""
    is_current = phase_key == BrandMindState.current_phase
    is_done = BrandMindState.completed_phases.contains(phase_key)

    pill = rx.box(
        _phase_glyph(
            phase_key,
            rx.cond(is_current | is_done, "#003732", tokens.TEXT_SECONDARY),
            "12px",
        ),
        style={
            "width": "28px",
            "height": "28px",
            "min_width": "28px",
            "border_radius": tokens.RADIUS_PILL,
            "display": "flex",
            "align_items": "center",
            "justify_content": "center",
            "background_color": rx.cond(
                is_current | is_done,
                tokens.ACCENT_TEAL_SOLID,
                "transparent",
            ),
            "border": rx.cond(
                is_current | is_done,
                "none",
                f"1px solid {tokens.GLASS_BORDER}",
            ),
        },
    )

    return rx.flex(
        rx.tooltip(
            pill,
            content=_phase_label(phase_key),
            side="right",
        ),
        width="100%",
        justify="center",
        align="center",
        padding_y="6px",
    )


def _section_label() -> rx.Component:
    """Top-of-sidebar label rendered only when expanded.

    Uses sentence-case sans (not all-caps mono) per Codex review Finding 1
    — the all-caps mono treatment read as "terminal product chrome".
    """
    return rx.cond(
        BrandMindState.sidebar_is_collapsed,
        rx.fragment(),
        rx.text(
            "Phases",
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
                "font_weight": "500",
                "letter_spacing": "0.02em",
                "padding": "20px 16px 8px 16px",
            },
        ),
    )


def _empty_state() -> rx.Component:
    """Placeholder when scope has not been classified yet.

    Hides entirely on the collapsed rail (Codex review Finding 1) so the
    rail does not show a lone spinning glyph that reads as a debug
    indicator; expanded view shows a brief explanatory line instead.
    """
    return rx.cond(
        BrandMindState.sidebar_is_collapsed,
        rx.fragment(),
        rx.text(
            "Awaiting scope classification.",
            style={
                "color": tokens.TEXT_MUTED,
                "font_family": tokens.FONT_SANS,
                "font_size": "12px",
                "font_style": "italic",
                "padding": "0 16px 16px 16px",
                "line_height": "1.5",
            },
        ),
    )


def _chat_row(info: rx.Var[SessionInfo]) -> rx.Component:
    """One chat row: clickable title + meta, hover-revealed actions menu.

    The title falls back to ``Untitled`` while the backend's auto-title
    job is still pending. The "…" trigger surfaces rename / pin / delete
    without disturbing the row-level click target that switches chats.
    """
    is_active = info.session_id == BrandMindState.session_id
    is_pinned = info.metadata.pinned
    label = rx.cond(info.metadata.title, info.metadata.title, "Untitled")
    meta = rx.cond(
        info.message_count > 0,
        info.message_count.to_string() + " msgs",
        "No messages yet",
    )
    title_text = rx.tooltip(
        rx.text(
            label,
            style={
                "color": rx.cond(is_active, tokens.TEXT_PRIMARY, tokens.TEXT_SECONDARY),
                "font_family": tokens.FONT_SANS,
                "font_size": "13px",
                "font_weight": rx.cond(is_active, "600", "500"),
                "line_height": "1.3",
                "overflow": "hidden",
                "text_overflow": "ellipsis",
                "white_space": "nowrap",
                "max_width": "100%",
            },
        ),
        content=label,
        side="right",
        delay_duration=300,
    )
    title_block = rx.hstack(
        rx.cond(
            is_pinned,
            rx.icon(
                tag="pin",
                size=12,
                color=tokens.ACCENT_TEAL_SOLID,
                style={"flex_shrink": "0"},
            ),
            rx.fragment(),
        ),
        title_text,
        spacing="2",
        align="center",
        width="100%",
        style={"min_width": "0"},
    )

    clickable = rx.box(
        rx.vstack(
            title_block,
            rx.text(
                meta,
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "11px",
                    "line_height": "1.3",
                },
            ),
            spacing="1",
            align="start",
            width="100%",
            style={"min_width": "0"},
        ),
        on_click=BrandMindState.switch_chat(info.session_id),
        style={
            "cursor": "pointer",
            "flex": "1",
            "min_width": "0",
        },
    )

    menu = rx.menu.root(
        rx.menu.trigger(
            rx.icon(
                tag="ellipsis",
                size=18,
                color=tokens.TEXT_SECONDARY,
            ),
            style={
                "padding": "6px",
                "border_radius": tokens.RADIUS_SM,
                "cursor": "pointer",
                "background_color": "transparent",
                "min_width": "28px",
                "min_height": "28px",
                "display": "flex",
                "align_items": "center",
                "justify_content": "center",
                "_hover": {
                    "background_color": "rgba(255, 255, 255, 0.10)",
                    "color": tokens.TEXT_PRIMARY,
                },
            },
        ),
        rx.menu.content(
            rx.menu.item(
                "Rename",
                on_click=BrandMindState.open_rename_dialog(
                    info.session_id, info.metadata.title
                ),
            ),
            rx.menu.item(
                rx.cond(is_pinned, "Unpin", "Pin"),
                on_click=BrandMindState.toggle_pin(info.session_id),
            ),
            rx.menu.separator(),
            rx.menu.item(
                "Delete",
                color=tokens.ACCENT_TEAL_SOLID,
                on_click=BrandMindState.open_delete_dialog(info.session_id),
            ),
            align="end",
        ),
    )

    return rx.hstack(
        clickable,
        menu,
        spacing="1",
        align="center",
        style={
            "width": "100%",
            "padding": "8px 10px 8px 14px",
            "border_radius": tokens.RADIUS_SM,
            "background_color": rx.cond(
                is_active,
                "rgba(95, 179, 168, 0.10)",
                "transparent",
            ),
            "border_left": rx.cond(
                is_active,
                f"2px solid {tokens.ACCENT_TEAL_SOLID}",
                "2px solid transparent",
            ),
            "transition": "background-color 160ms ease",
            "_hover": {
                "background_color": rx.cond(
                    is_active,
                    "rgba(95, 179, 168, 0.14)",
                    "rgba(255, 255, 255, 0.04)",
                ),
            },
        },
    )


def _new_chat_button() -> rx.Component:
    """Pill button that resets the workspace into a fresh empty chat."""
    return rx.button(
        rx.hstack(
            rx.icon(tag="plus", size=14, color=tokens.TEXT_PRIMARY),
            rx.text(
                "New chat",
                style={
                    "color": tokens.TEXT_PRIMARY,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "13px",
                    "font_weight": "500",
                },
            ),
            spacing="2",
            align="center",
        ),
        on_click=BrandMindState.start_new_chat,
        variant="ghost",
        style={
            "width": "100%",
            "justify_content": "flex-start",
            "padding": "8px 14px",
            "border_radius": tokens.RADIUS_SM,
            "background_color": "transparent",
            "border": f"1px solid {tokens.GLASS_BORDER}",
            "cursor": "pointer",
            "transition": "border-color 160ms ease, background-color 160ms ease",
            "_hover": {
                "border_color": "rgba(95, 179, 168, 0.35)",
                "background_color": "rgba(95, 179, 168, 0.06)",
            },
        },
    )


def _chats_section() -> rx.Component:
    """Top section: section label + new-chat button + persisted chat list."""
    return rx.cond(
        BrandMindState.sidebar_is_collapsed,
        rx.center(
            rx.button(
                rx.icon(tag="plus", size=16, color=tokens.TEXT_PRIMARY),
                on_click=BrandMindState.start_new_chat,
                variant="ghost",
                style={
                    "width": "32px",
                    "height": "32px",
                    "padding": "0",
                    "border_radius": tokens.RADIUS_PILL,
                    "border": f"1px solid {tokens.GLASS_BORDER}",
                    "cursor": "pointer",
                    "_hover": {
                        "border_color": "rgba(95, 179, 168, 0.35)",
                    },
                },
            ),
            width="100%",
            padding="16px 0 8px 0",
        ),
        rx.vstack(
            rx.text(
                "Chats",
                style={
                    "color": tokens.TEXT_MUTED,
                    "font_family": tokens.FONT_SANS,
                    "font_size": "12px",
                    "font_weight": "500",
                    "letter_spacing": "0.02em",
                    "padding": "20px 16px 8px 16px",
                },
            ),
            rx.box(_new_chat_button(), padding="0 12px 8px 12px", width="100%"),
            rx.cond(
                BrandMindState.sessions.length() == 0,
                rx.text(
                    "No chats yet — send a message to start.",
                    style={
                        "color": tokens.TEXT_MUTED,
                        "font_family": tokens.FONT_SANS,
                        "font_size": "12px",
                        "font_style": "italic",
                        "padding": "4px 16px 16px 16px",
                        "line_height": "1.5",
                    },
                ),
                rx.vstack(
                    rx.foreach(BrandMindState.sessions, _chat_row),
                    spacing="1",
                    align="stretch",
                    padding="0 12px",
                    width="100%",
                ),
            ),
            spacing="0",
            align="stretch",
            width="100%",
        ),
    )


def _phases_section() -> rx.Component:
    """Bottom section: scope-dependent phase tracker."""
    return rx.vstack(
        _section_label(),
        rx.cond(
            BrandMindState.phase_sequence.length() == 0,
            _empty_state(),
            rx.cond(
                BrandMindState.sidebar_is_collapsed,
                rx.vstack(
                    rx.foreach(
                        BrandMindState.phase_sequence,
                        _collapsed_rail_item,
                    ),
                    spacing="0",
                    width="100%",
                    padding_top="12px",
                ),
                rx.vstack(
                    rx.foreach(
                        BrandMindState.phase_sequence,
                        _expanded_row,
                    ),
                    spacing="0",
                    width="100%",
                    padding_top="4px",
                ),
            ),
        ),
        spacing="0",
        align="start",
        width="100%",
    )


def _settings_footer() -> rx.Component:
    """Sidebar bottom row that opens the Settings dialog.

    Pinned to the bottom of the rail via ``margin_top: auto`` on the
    enclosing vstack spacer. In the collapsed rail the row reduces to a
    single gear-icon button so the affordance survives the 56-px width.
    """
    return rx.cond(
        BrandMindState.sidebar_is_collapsed,
        rx.center(
            rx.button(
                rx.icon(tag="settings", size=18, color=tokens.TEXT_SECONDARY),
                on_click=BrandMindState.open_settings,
                variant="ghost",
                aria_label="Open settings",
                style={
                    "width": "32px",
                    "height": "32px",
                    "padding": "0",
                    "border_radius": tokens.RADIUS_PILL,
                    "cursor": "pointer",
                    "_hover": {
                        "background_color": "rgba(255, 255, 255, 0.04)",
                    },
                },
            ),
            width="100%",
            padding="12px 0 16px 0",
        ),
        rx.box(
            rx.button(
                rx.hstack(
                    rx.icon(tag="settings", size=16, color=tokens.TEXT_SECONDARY),
                    rx.text(
                        "Settings",
                        style={
                            "color": tokens.TEXT_SECONDARY,
                            "font_family": tokens.FONT_SANS,
                            "font_size": "13px",
                            "font_weight": "500",
                        },
                    ),
                    spacing="2",
                    align="center",
                ),
                on_click=BrandMindState.open_settings,
                variant="ghost",
                style={
                    "width": "100%",
                    "justify_content": "flex-start",
                    "padding": "10px 12px",
                    "border_radius": tokens.RADIUS_SM,
                    "cursor": "pointer",
                    "_hover": {
                        "background_color": "rgba(255, 255, 255, 0.04)",
                    },
                },
            ),
            padding="8px 12px 16px 12px",
            width="100%",
        ),
    )


def _section_divider() -> rx.Component:
    """Hairline between the Chats and Phases sections."""
    return rx.box(
        style={
            "height": "1px",
            "background_color": tokens.GLASS_BORDER,
            "margin": "8px 16px",
        },
    )


def chat_action_dialogs() -> rx.Component:
    """Page-level rename + delete dialogs driven by BrandMindState targets.

    Composed once at the top of the page so the dialog DOM is not
    duplicated per chat row. Visibility is controlled by the
    ``rename_target`` / ``delete_target`` state variables.
    """
    rename_dialog = rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Rename chat"),
            rx.dialog.description(
                "Pick a label that helps you spot this chat later.",
                size="2",
                color=tokens.TEXT_MUTED,
            ),
            rx.input(
                value=BrandMindState.rename_draft,
                placeholder="Chat title",
                on_change=BrandMindState.set_rename_draft,
                style={
                    "margin_top": "12px",
                    "background_color": tokens.BG_SURFACE_2,
                    "color": tokens.TEXT_PRIMARY,
                    "border": f"1px solid {tokens.GLASS_BORDER}",
                },
            ),
            rx.hstack(
                rx.button(
                    "Cancel",
                    variant="soft",
                    color_scheme="gray",
                    on_click=BrandMindState.cancel_rename,
                ),
                rx.button(
                    "Save",
                    on_click=BrandMindState.confirm_rename,
                    style={
                        "background_color": tokens.ACCENT_TEAL_SOLID,
                        "color": "#003732",
                    },
                ),
                spacing="3",
                justify="end",
                margin_top="16px",
            ),
            style={
                "background_color": tokens.BG_SURFACE_1,
                "border": f"1px solid {tokens.GLASS_BORDER}",
                "max_width": "420px",
            },
        ),
        open=BrandMindState.rename_target != "",
        on_open_change=BrandMindState.cancel_rename,
    )
    delete_dialog = rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Delete this chat?"),
            rx.alert_dialog.description(
                "The chat and its message history will be removed. "
                "This cannot be undone.",
                size="2",
                color=tokens.TEXT_MUTED,
            ),
            rx.hstack(
                rx.checkbox(
                    checked=BrandMindState.delete_workspace_too,
                    on_change=BrandMindState.toggle_delete_workspace_too,
                    color_scheme="red",
                ),
                rx.vstack(
                    rx.text(
                        "Also clear this chat's saved progress",
                        size="2",
                        weight="medium",
                        color=tokens.TEXT_PRIMARY,
                    ),
                    rx.text(
                        "Permanently removes the strategy notes the "
                        "assistant kept while working on this chat.",
                        size="1",
                        color=tokens.TEXT_MUTED,
                    ),
                    spacing="1",
                    align="start",
                ),
                spacing="3",
                align="start",
                margin_top="16px",
                padding="12px",
                style={
                    "background_color": tokens.BG_SURFACE_2,
                    "border": f"1px solid {tokens.GLASS_BORDER}",
                    "border_radius": tokens.RADIUS_SM,
                },
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=BrandMindState.cancel_delete,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        "Delete",
                        color_scheme="red",
                        on_click=BrandMindState.confirm_delete,
                    ),
                ),
                spacing="3",
                justify="end",
                margin_top="16px",
            ),
            style={
                "background_color": tokens.BG_SURFACE_1,
                "border": f"1px solid {tokens.GLASS_BORDER}",
                "max_width": "440px",
            },
        ),
        open=BrandMindState.delete_target != "",
        on_open_change=BrandMindState.cancel_delete,
    )
    return rx.fragment(rename_dialog, delete_dialog)


def phase_progress_sidebar() -> rx.Component:
    """Render the collapsible sidebar with chats, phases, and the Settings footer."""
    return rx.vstack(
        _chats_section(),
        _section_divider(),
        _phases_section(),
        rx.box(flex="1", width="100%"),
        _settings_footer(),
        spacing="0",
        align="stretch",
        style={
            "width": rx.cond(
                BrandMindState.sidebar_is_collapsed,
                f"{tokens.SIDEBAR_COLLAPSED_PX}px",
                f"{tokens.SIDEBAR_EXPANDED_PX}px",
            ),
            "min_width": rx.cond(
                BrandMindState.sidebar_is_collapsed,
                f"{tokens.SIDEBAR_COLLAPSED_PX}px",
                f"{tokens.SIDEBAR_EXPANDED_PX}px",
            ),
            "height": "100%",
            "background_color": tokens.GLASS_BG_SUBTLE,
            "backdrop_filter": "blur(20px)",
            "-webkit-backdrop-filter": "blur(20px)",
            "border_right": f"1px solid {tokens.GLASS_BORDER}",
            "transition": "width 240ms cubic-bezier(0.4, 0, 0.2, 1)",
            "overflow_y": "auto",
            "overflow_x": "hidden",
        },
    )
