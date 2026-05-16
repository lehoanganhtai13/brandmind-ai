"""BrandMind web UI — Reflex entry point.

Wires the application state and registers the root page. The current
page renders a status-only placeholder that surfaces the session id,
current phase, scope-aware phase progress, and a connected /
disconnected indicator. Phase 3 replaces this placeholder with the
real Header + collapsible PhaseProgressSidebar + ChatPane layout; the
state class itself does not change.

Aesthetic anchors:

* Color mode ``dark`` with accent ``teal`` matches the TUI banner and
  the locked Web UI v1 design tone (teal ``#5fb3a8`` on dark base).
* Glass-effect surfaces are deferred to Phase 3 where they fit the
  larger layout; this placeholder uses a flat centered card so the
  smoke evidence (phase progresses, sidebar payload arrives) reads at
  a glance.
"""

from __future__ import annotations

import reflex as rx

from .state import BrandMindState


def _status_badge() -> rx.Component:
    """Render the connected / disconnected backend-status badge."""
    return rx.cond(
        BrandMindState.is_connected,
        rx.hstack(
            rx.icon(tag="check", size=20),
            rx.text("Backend: Connected", size="4", weight="medium"),
            spacing="2",
            align="center",
            padding="3",
            border_radius="medium",
            background_color=rx.color("teal", 3),
            color=rx.color("teal", 11),
        ),
        rx.hstack(
            rx.icon(tag="circle-x", size=20),
            rx.text("Backend: Disconnected", size="4", weight="medium"),
            spacing="2",
            align="center",
            padding="3",
            border_radius="medium",
            background_color=rx.color("red", 3),
            color=rx.color("red", 11),
        ),
    )


def _phase_progress_placeholder() -> rx.Component:
    """Surface the live phase sequence so Phase 2 evidence is visible."""
    return rx.vstack(
        rx.text(
            "Phase progress (Phase 2 placeholder — real sidebar in Phase 3)",
            size="2",
            color=rx.color("gray", 10),
        ),
        rx.foreach(
            BrandMindState.phase_sequence,
            lambda phase_key: rx.hstack(
                rx.cond(
                    BrandMindState.completed_phases.contains(phase_key),
                    rx.icon(tag="check", size=16, color=rx.color("teal", 11)),
                    rx.cond(
                        phase_key == BrandMindState.current_phase,
                        rx.icon(tag="circle-dot", size=16, color=rx.color("teal", 11)),
                        rx.icon(tag="circle", size=16, color=rx.color("gray", 8)),
                    ),
                ),
                rx.text(
                    BrandMindState.phase_display_labels[phase_key],
                    size="3",
                    color=rx.cond(
                        phase_key == BrandMindState.current_phase,
                        rx.color("teal", 11),
                        rx.color("gray", 11),
                    ),
                ),
                spacing="2",
                align="center",
            ),
        ),
        spacing="2",
        align="start",
        padding="3",
        border_radius="medium",
        background_color=rx.color("gray", 2),
        border=f"1px solid {rx.color('gray', 5)}",
        min_width="320px",
    )


def _session_meta() -> rx.Component:
    """Show identifying session metadata for Phase 2 smoke verification."""
    return rx.vstack(
        rx.hstack(
            rx.text("session_id:", size="2", color=rx.color("gray", 10)),
            rx.text(BrandMindState.session_id, size="2", weight="medium"),
            spacing="2",
        ),
        rx.hstack(
            rx.text("scope:", size="2", color=rx.color("gray", 10)),
            rx.text(BrandMindState.scope, size="2", weight="medium"),
            spacing="2",
        ),
        rx.hstack(
            rx.text("current_phase:", size="2", color=rx.color("gray", 10)),
            rx.text(BrandMindState.current_phase, size="2", weight="medium"),
            spacing="2",
        ),
        spacing="1",
        align="start",
    )


def _header() -> rx.Component:
    """Render the top bar with the BrandMind wordmark and aesthetic anchor."""
    return rx.hstack(
        rx.text(
            "BrandMind",
            size="6",
            weight="bold",
            color=rx.color("teal", 11),
        ),
        rx.text(
            "Web UI v1 — state layer",
            size="2",
            color=rx.color("gray", 10),
        ),
        spacing="4",
        align="center",
        padding="4",
        width="100%",
        border_bottom=f"1px solid {rx.color('gray', 5)}",
    )


def index() -> rx.Component:
    """Root page: header + placeholder showing live state from the backend.

    Reflex fires ``initialize_session`` once at mount which creates the
    backend brand-strategy session and seeds sidebar state; the
    background health poll keeps the connected indicator honest.
    """
    return rx.vstack(
        _header(),
        rx.center(
            rx.vstack(
                rx.text(
                    "BrandMind backend status",
                    size="3",
                    color=rx.color("gray", 11),
                ),
                _status_badge(),
                _session_meta(),
                _phase_progress_placeholder(),
                rx.cond(
                    BrandMindState.error_message != "",
                    rx.text(
                        BrandMindState.error_message,
                        size="2",
                        color=rx.color("red", 11),
                    ),
                    rx.fragment(),
                ),
                spacing="4",
                align="center",
            ),
            width="100%",
            flex="1",
        ),
        spacing="0",
        width="100vw",
        height="100vh",
        on_mount=[
            BrandMindState.initialize_session,
            BrandMindState.poll_health,
        ],
    )


app = rx.App()
app.add_page(index, title="BrandMind")
