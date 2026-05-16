"""Reflex configuration for the BrandMind web UI.

Runs as a separate Reflex sub-project at the repo root, distinct from the
Python source tree under ``src/``. The Reflex CLI (`reflex run`) discovers
this file when invoked with ``web/`` as the working directory; the
sibling ``brandmind_web/`` package contains the app definition.

Ports are intentionally non-default so they do not collide with the
FastAPI backend (`brandmind serve` on port 8000). The actual port values
come from environment variables read in :mod:`config.system_config` and
forwarded through the ``brandmind web`` CLI launcher's ``reflex run``
command-line arguments — Reflex picks the CLI arguments over this file,
so the values here act as fallbacks for direct ``reflex run`` invocations
outside the CLI launcher.
"""

from __future__ import annotations

import os

import reflex as rx
from reflex.plugins.sitemap import SitemapPlugin

_FRONTEND_PORT_DEFAULT = 8501
_BACKEND_PORT_DEFAULT = 8502

# Theme is configured here (Reflex 0.9+ pattern) rather than on the
# ``rx.App`` constructor, which became deprecated in 0.9.0 and will be
# removed in 1.0. Teal accent on a dark base matches the TUI and the
# locked Web UI v1 aesthetic.
_radix_theme = rx.theme(
    appearance="dark",
    accent_color="teal",
    radius="medium",
)


config = rx.Config(
    app_name="brandmind_web",
    frontend_port=int(os.getenv("BRANDMIND_WEB_PORT", _FRONTEND_PORT_DEFAULT)),
    backend_port=int(
        os.getenv("BRANDMIND_WEB_BACKEND_PORT", _BACKEND_PORT_DEFAULT)
    ),
    telemetry_enabled=False,
    show_built_with_reflex=False,
    plugins=[
        rx.plugins.RadixThemesPlugin(theme=_radix_theme),
    ],
    disable_plugins=[
        SitemapPlugin,
    ],
)
