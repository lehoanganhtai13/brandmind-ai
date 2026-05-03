"""Unit tests for the browser stealth configuration defaults.

Pins the macOS Keychain-bypass flags added in 2026-05-03 (Sub-plan #2). The
``BrowserStartEvent`` 30s timeout we observed during Phase A iso testing was
caused by the agent's Chrome subprocess trying to decrypt the encrypted
``Cookies`` / ``Login Data`` / ``Web Data`` SQLite stores in
``~/.brandmind/browser_data/Default/``. Decryption requires macOS Keychain
access; the new spawning context lacked the matching Keychain entry, so
Chrome stayed alive but never opened its CDP port and ``cdp_use`` polled
until the watchdog timed out.

The two Chromium flags asserted below are documented bypasses:

- ``--password-store=basic`` — Chromium stores passwords in a plaintext file
  on disk instead of calling the macOS Keychain.
- ``--use-mock-keychain`` — Chromium replaces the Keychain backend entirely
  with an in-memory mock; no system Keychain interaction happens.

Together they eliminate the Keychain-prompt path that caused the timeout,
without changing how stored cookies (which live in the plaintext
``storage_state.json``) are loaded by the browser session.
"""

from __future__ import annotations

from shared.agent_tools.browser.stealth_config import StealthConfig


class TestBrowserArgsKeychainBypass:
    """Pin the Keychain-bypass flags so a future refactor cannot regress them."""

    def test_password_store_basic_flag_present(self) -> None:
        """Default browser args include --password-store=basic.

        Without this flag, the agent's Chrome subprocess falls back to the
        macOS Keychain when reading/writing passwords, which prompts the user
        and hangs startup until the prompt is resolved.
        """
        config = StealthConfig()
        assert "--password-store=basic" in config.browser_args, (
            "Default StealthConfig must include --password-store=basic so the "
            "Chrome subprocess writes passwords to a plaintext file instead of "
            "calling macOS Keychain. Without this flag the agent hangs at "
            "BrowserStartEvent for 30s on macOS hosts where the existing "
            "encrypted Cookies SQLite store cannot be decrypted by the new "
            "spawning context."
        )

    def test_use_mock_keychain_flag_present(self) -> None:
        """Default browser args include --use-mock-keychain.

        Used in tandem with ``--password-store=basic`` to replace the Keychain
        backend with an in-memory mock — no system Keychain interaction at
        all. The two flags together eliminate every code path that could
        re-trigger the 30s startup hang.
        """
        config = StealthConfig()
        assert "--use-mock-keychain" in config.browser_args, (
            "Default StealthConfig must include --use-mock-keychain so the "
            "Chrome subprocess uses an in-memory Keychain mock and never "
            "blocks on macOS Keychain decryption."
        )

    def test_automation_flag_still_present_after_keychain_addition(self) -> None:
        """Adding Keychain flags must not regress the existing stealth flag.

        ``--disable-blink-features=AutomationControlled`` was the only flag in
        the default list before this change; the new flags are additive.
        """
        config = StealthConfig()
        assert "--disable-blink-features=AutomationControlled" in config.browser_args, (
            "AutomationControlled bypass must remain in the default browser_args; "
            "the Keychain-bypass additions are additive, not a replacement."
        )

    def test_browser_args_contains_no_duplicates(self) -> None:
        """Each Chromium flag should appear exactly once in the default list."""
        config = StealthConfig()
        assert len(config.browser_args) == len(set(config.browser_args)), (
            "Default browser_args must not contain duplicate flags — Chromium "
            "may warn or behave unexpectedly when the same switch is passed twice."
        )
