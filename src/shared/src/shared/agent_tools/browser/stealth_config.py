"""
Stealth configuration for the browser sandbox.

This module provides a centralized, Pydantic-validated configuration class
for all anti-detection settings used by the browser agent. The design is
intentionally swappable: if the default Playwright stealth becomes insufficient,
the entire browser engine can be replaced (e.g., patchright, camoufox) without
touching BrowserManager's public interface.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class StealthConfig(BaseModel):
    """
    Centralized anti-detection configuration for the browser sandbox.

    This config implements a 4-layer stealth strategy to avoid bot detection
    on social media platforms (Facebook, Instagram, etc.):

    1. **Headed mode** (``headless=False``) — avoids GPU/font fingerprint leaks
       that are trivially detected in headless environments.
    2. **Remove automation flags** — strips ``--enable-automation`` from
       Chromium's default args, which hides ``navigator.webdriver = true``.
    3. **Consistent User-Agent** — by default, let Chromium report its own
       built-in UA. This guarantees the UA always matches the actual browser
       version and OS, eliminating any mismatch an anti-bot system could detect.
    4. **Human-like delays** — ``wait_between_actions`` introduces natural pauses
       between page interactions to avoid behavioral fingerprinting.

    The config is designed to be swappable: if the basic Playwright stealth is
    insufficient (e.g., Meta starts blocking), the entire browser engine can be
    swapped to ``patchright`` or ``camoufox`` without modifying BrowserManager's
    public interface — only the internals of ``_create_browser()`` need updating.

    Attributes:
        user_agent: Custom UA override. ``None`` = use Chromium's built-in
            default UA (recommended for maximum consistency with the actual
            browser version and OS). Only override this if you need to emulate
            a specific device (e.g., mobile).
        window_size: Browser window pixel dimensions for headed (visible) mode.
            Defaults to a standard 1440x900 desktop resolution.
        viewport: Content area pixel dimensions. Should match ``window_size``
            to avoid detectable discrepancies.
        wait_between_actions: Seconds the agent waits between page interactions
            (click, scroll, type). Mimics human reading/reaction time.
        ignore_default_args: List of Playwright's default Chromium launch args
            to suppress. ``--enable-automation`` is the primary flag that
            exposes ``navigator.webdriver = true``.
        browser_args: Additional Chromium command-line flags to inject at
            launch. ``--disable-blink-features=AutomationControlled`` prevents
            the Blink engine from advertising automation mode.

    Example:
        Default config (recommended for most use cases)::

            config = StealthConfig()

        Custom config for slower, more human-like behavior::

            config = StealthConfig(wait_between_actions=2.0)
    """

    # None = let Chromium use its own default User-Agent.
    # This is the safest option because it always matches the actual browser
    # version and OS, avoiding any mismatch that anti-bot systems could detect.
    # Only set a custom value if you need to emulate a specific device.
    user_agent: Optional[str] = Field(
        default=None,
        description=(
            "Custom User-Agent string. None = use Chromium's own default UA "
            "(recommended). Override only when emulating a specific device."
        ),
    )
    window_size: Dict[str, int] = Field(
        default={"width": 1440, "height": 900},
        description="Browser window dimensions for headed mode (pixels).",
    )
    viewport: Dict[str, int] = Field(
        default={"width": 1440, "height": 900},
        description=(
            "Content area dimensions. Should match window_size to avoid "
            "detectable size discrepancies."
        ),
    )
    wait_between_actions: float = Field(
        default=1.0,
        ge=0.0,
        description=(
            "Seconds to wait between agent page interactions. "
            "Higher values are more human-like but slower."
        ),
    )
    ignore_default_args: List[str] = Field(
        default=["--enable-automation"],
        description=(
            "Playwright default Chromium args to suppress. "
            "'--enable-automation' exposes navigator.webdriver=true."
        ),
    )
    browser_args: List[str] = Field(
        default=["--disable-blink-features=AutomationControlled"],
        description=(
            "Additional Chromium command-line flags. "
            "'--disable-blink-features=AutomationControlled' hides automation mode."
        ),
    )
