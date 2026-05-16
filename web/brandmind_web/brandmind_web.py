"""BrandMind web UI — placeholder page with backend health badge.

Scaffold deliverable for Task #89. The real chat / phase-sidebar /
canvas / artifact UI lands in Tasks #91 and #92 on top of this skeleton.

What this module ships today:

* :class:`HealthState` — a Reflex state class with one reactive flag
  (``is_connected``) and a background coroutine that polls the FastAPI
  backend's ``/api/v1/health`` endpoint every ten seconds. Reading a
  reactive var in a component re-renders that component when the var
  changes, so the badge follows the poll result without any extra
  wiring.
* :func:`index` — the root page. Header with the BrandMind wordmark
  and a centered status badge.
* ``app`` — the :class:`reflex.App` instance Reflex auto-discovers
  through the ``app_name`` in ``rxconfig.py``.

Aesthetic anchors:

* Color mode ``dark`` with accent ``teal`` matches the TUI banner and
  the locked Web UI v1 design tone (teal ``#5fb3a8`` on dark base).
* Glass-effect surfaces are deferred to Task #91 where they fit the
  larger layout; this scaffold uses a flat centered card so the smoke
  test reads obviously connected / disconnected at a glance.
"""

from __future__ import annotations

import asyncio
import os

import httpx
import reflex as rx

_DEFAULT_API_URL = "http://localhost:8000"
_HEALTH_POLL_INTERVAL_SECONDS = 10
_HEALTH_REQUEST_TIMEOUT_SECONDS = 3


def _api_base_url() -> str:
    """Return the FastAPI backend base URL the web UI should reach.

    Reads ``BRANDMIND_API_URL`` from the environment so a Docker
    deployment can swap the host without rebuilding the image. Falls
    back to ``localhost:8000`` which matches a default
    ``brandmind serve`` install on the same machine.
    """
    return os.getenv("BRANDMIND_API_URL", _DEFAULT_API_URL).rstrip("/")


class HealthState(rx.State):
    """Reactive backend-connectivity state for the placeholder page.

    The single reactive var :attr:`is_connected` drives every
    health-aware component. Components that read this var re-render
    automatically when the background poll flips its value.
    """

    is_connected: bool = False

    @rx.event(background=True)
    async def poll_health(self) -> None:
        """Poll ``/api/v1/health`` on a fixed cadence and mirror the result.

        Runs as a Reflex background task so the UI stays responsive
        while the request is in flight. Any 2xx response counts as
        connected; exceptions, non-2xx codes, and timeouts count as
        disconnected. State mutations happen inside ``async with self``
        so Reflex serialises them against UI reads.
        """
        url = f"{_api_base_url()}/api/v1/health"
        timeout = _HEALTH_REQUEST_TIMEOUT_SECONDS
        while True:
            connected = False
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(url)
                connected = response.is_success
            except httpx.HTTPError:
                connected = False

            async with self:
                self.is_connected = connected

            await asyncio.sleep(_HEALTH_POLL_INTERVAL_SECONDS)


def _status_badge() -> rx.Component:
    """Render the connected / disconnected backend-status badge.

    The badge's text and color are driven by ``HealthState.is_connected``;
    Reflex re-renders this subtree whenever the reactive var flips.
    """
    return rx.cond(
        HealthState.is_connected,
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
            "Web UI v1 — scaffold",
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
    """Root page: header + centered health badge.

    Reflex calls :meth:`HealthState.poll_health` once via ``on_mount`` so
    the background polling starts on first navigation and lives for the
    lifetime of the session.
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
                rx.text(
                    f"Polling {_api_base_url()}/api/v1/health every "
                    f"{_HEALTH_POLL_INTERVAL_SECONDS}s",
                    size="1",
                    color=rx.color("gray", 9),
                ),
                spacing="3",
                align="center",
            ),
            width="100%",
            flex="1",
        ),
        spacing="0",
        width="100vw",
        height="100vh",
        on_mount=HealthState.poll_health,
    )


app = rx.App()
app.add_page(index, title="BrandMind")
