"""
Browser lifecycle manager for the AI agent's isolated browser sandbox.

This module provides ``BrowserManager``, a class that manages a persistent,
isolated Chrome browser instance for social media research. It supports two
distinct operating modes:

- **Login Setup** (``setup_login``): Launches a visible browser via Playwright's
  ``launch_persistent_context()`` for the user to manually log into social media
  accounts. Session data (cookies, localStorage) is persisted to a dedicated
  sandbox directory and reused on subsequent runs.

- **Agent Browsing** (``get_browser``): Returns a ``browser-use`` ``Browser``
  instance pre-configured with the saved session and stealth settings, ready for
  autonomous AI navigation.

The sandbox directory (``~/.brandmind/browser_data/`` by default) is completely
isolated from the user's personal browser profile — no cross-contamination of
cookies, sessions, or cached credentials.
"""

import asyncio
import glob
import logging
import os
import platform
import shutil
from pathlib import Path
from typing import Optional, cast

from browser_use import Browser
from playwright.async_api import ViewportSize, async_playwright

from .stealth_config import StealthConfig

logger = logging.getLogger(__name__)

# Default path for the isolated browser sandbox data.
# All cookies, cache, and localStorage for the agent's clone accounts are stored
# here, completely separated from the user's personal browser profile.
DEFAULT_BROWSER_DATA_DIR = str(Path.home() / ".brandmind" / "browser_data")

# Stale lock files left by Chromium when a process exits uncleanly.
# These must be removed before launching a new browser on the same profile.
_CHROME_LOCK_FILES = ["SingletonLock", "SingletonCookie", "SingletonSocket"]

# Filename for the exported cookie/storage state JSON file.
# This file is the canonical source for session data, used to bypass
# macOS Keychain cookie encryption mismatch between Playwright and
# browser-use Chrome instances.
_STORAGE_STATE_FILENAME = "storage_state.json"


class BrowserManager:
    """
    Manages the lifecycle of an isolated, persistent browser instance for
    AI agent web browsing on social media platforms.

    This class abstracts the two phases of browser usage:

    **Phase 1 — Login Setup** (run once per account):
    Opens a visible Playwright browser at the target social media URL.
    The user logs in manually. Playwright's ``launch_persistent_context()``
    saves all session data (cookies, localStorage, IndexedDB) to ``data_dir``.
    The browser stays open until the user closes it.

    **Phase 2 — Agent Browsing** (run on every agent request):
    Creates a ``browser-use`` ``Browser`` instance pointing to the same
    ``data_dir``. The saved session is automatically restored, so the agent
    browses as the logged-in clone account without requiring a new login.

    The browser sandbox is completely isolated from the user's personal browser.
    All data lives under ``~/.brandmind/browser_data/`` by default.

    Attributes:
        data_dir: Absolute path to the persistent browser sandbox directory.
        stealth_config: Anti-detection configuration applied to all browser
            instances created by this manager.

    Example:
        One-time login setup::

            manager = BrowserManager()
            await manager.setup_login("https://www.facebook.com")
            # User logs in, closes window — session is saved automatically

        Agent browsing (after login)::

            manager = BrowserManager()
            browse_tool = create_browse_tool(manager)
            result = await browse_tool("Summarize the top 3 posts on my feed")
    """

    def __init__(
        self,
        data_dir: str = DEFAULT_BROWSER_DATA_DIR,
        stealth_config: Optional[StealthConfig] = None,
    ) -> None:
        """
        Initialize a BrowserManager with an isolated sandbox directory.

        Args:
            data_dir: Path to the directory where all browser session data
                (cookies, localStorage, cache) will be stored. Defaults to
                ``~/.brandmind/browser_data/``. Use a custom path if you need
                multiple isolated browser profiles (e.g., one per social account).
            stealth_config: Anti-detection settings for the browser. If ``None``,
                uses ``StealthConfig()`` defaults (recommended for most users).
        """
        self.data_dir = data_dir
        self.stealth_config = stealth_config or StealthConfig()

        # Resolve the Chrome binary path once at init time.
        # Both setup_login() and get_browser() use this same path to ensure
        # profile format compatibility (same binary = same profile version).
        self._chrome_path: str | None = self._find_chrome_path()

        # Ensure the sandbox directory exists before any browser operation.
        # parents=True handles the full path creation (e.g., ~/.brandmind/).
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)

    async def setup_login(
        self, urls: str | list[str] = "https://www.facebook.com"
    ) -> None:
        """
        Open a visible browser for the user to manually log into a social
        media platform. Session data is automatically persisted for future
        agent browsing sessions.

        This method uses Playwright's ``launch_persistent_context()`` directly
        (not ``browser-use``) because this mode is entirely user-controlled —
        no LLM or AI agent is involved. The user navigates and logs in manually,
        then closes the browser window when done.

        After this method returns, ``is_session_valid()`` should return ``True``
        and ``get_browser()`` can be used for AI agent browsing.

        Args:
            urls: A single URL string or a list of URL strings to open
                for login. Defaults to Facebook. If a list is provided,
                each URL will be opened in a separate tab simultaneously.
                Common values: ``"https://www.instagram.com"``,
                ``"https://www.facebook.com"``.

        Raises:
            playwright.async_api.Error: If Chromium fails to launch (e.g.,
                ``make install-browser`` was not run to download the binary).
        """
        config = self.stealth_config

        # Collect stealth browser args from config
        launch_args = list(config.browser_args)

        # Clean up stale lock files from a previous browser that didn't
        # close cleanly. Without this, launch_persistent_context() will
        # fail with TargetClosedError.
        self._cleanup_stale_locks()

        async with async_playwright() as p:
            # launch_persistent_context() is the Playwright API that saves ALL
            # browser state (cookies, localStorage, cache, IndexedDB) to
            # user_data_dir. On subsequent launches with the same directory,
            # the full session is automatically restored.
            #
            # executable_path: Use System Chrome (same binary that browser-use
            # will use for agent browsing) to ensure profile format compatibility.
            # Without this, Playwright defaults to its bundled Chromium, which
            # creates profiles incompatible with System Chrome.
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.data_dir,
                headless=False,
                # StealthConfig.viewport is Dict[str, int] which is structurally
                # compatible with Playwright's ViewportSize TypedDict.
                # cast() tells mypy they are the same type without runtime cost.
                viewport=cast(ViewportSize, config.viewport),
                args=launch_args,
                ignore_default_args=config.ignore_default_args,
                # user_agent: pass None to let Chrome use its own built-in UA.
                user_agent=config.user_agent,
                # Use System Chrome if found; Playwright falls back to its
                # bundled Chromium when executable_path is None.
                executable_path=self._chrome_path,
            )

            if isinstance(urls, str):
                url_list = [urls]
            else:
                url_list = urls

            # launch_persistent_context automatically opens an initial blank page.
            # We use this existing page for the first URL, then create new pages
            # for any remaining URLs to avoid leaving an empty tab behind.
            pages = context.pages
            first_page = pages[0] if pages else await context.new_page()
            await first_page.goto(url_list[0])

            # Navigate remaining URLs in new tabs
            for url in url_list[1:]:
                page = await context.new_page()
                await page.goto(url)

            # Block until the user closes the browser window.
            # Polling context.pages[] is the simplest cross-platform approach:
            # when the user closes the last tab/window, pages[] becomes empty.
            try:
                while context.pages:
                    await asyncio.sleep(1)
            except Exception:
                # Suppress any cleanup errors (e.g., connection closed)
                pass
            finally:
                # Export cookies as plaintext JSON BEFORE closing the context.
                #
                # WHY: Chrome encrypts cookies using macOS Keychain, and
                # different Chrome launch methods (Playwright vs subprocess)
                # use different Keychain service names. This means cookies
                # saved by Playwright cannot be decrypted by browser-use's
                # Chrome subprocess. By exporting as plaintext JSON, we
                # bypass Keychain entirely — browser-use's
                # StorageStateWatchdog injects them via CDP
                # Network.setCookies.
                try:
                    await context.storage_state(path=self._storage_state_path)
                    logger.info(
                        "Session exported to %s",
                        self._storage_state_path,
                    )
                except Exception as e:
                    logger.warning("Failed to export storage state: %s", e)
                # Closing the context flushes all session data to
                # user_data_dir.
                await context.close()

    def get_browser(self) -> Browser:
        """
        Create and return a ``browser-use`` ``Browser`` instance configured
        for AI agent browsing, using the previously saved login session.

        The returned browser is:
        - **Visible** (``headless=False``) — the user can watch the agent work
        - **Element-highlighting** — interactive elements are visually tagged
          with ``[1]``, ``[2]`` overlays for AI vision
        - **Stealth-configured** — automation flags removed, human-like delays
        - **Session-loaded** — the saved login cookies are automatically restored

        Returns:
            A configured ``Browser`` instance ready to pass to a
            ``browser-use`` ``Agent``.

        Raises:
            RuntimeError: If no valid login session exists in ``data_dir``.
                The user must run ``setup_login()`` (or ``brandmind browser
                setup``) before calling this method.
        """
        if not self.is_session_valid():
            raise RuntimeError(
                "No valid browser session found in "
                f"'{self.data_dir}'. "
                "Run setup_login() (or 'brandmind browser setup') to login first."
            )
        return self._create_browser()

    def _create_browser(self) -> Browser:
        """
        Internal factory method that builds a ``browser-use`` ``Browser``
        instance with the current stealth configuration.

        This is intentionally separate from ``get_browser()`` so that the
        session check and browser construction are cleanly decoupled.
        In the future, if ``patchright`` or ``camoufox`` replaces Playwright
        underneath, only this method needs to change.

        Returns:
            Configured ``Browser`` instance for AI agent control.
        """
        config = self.stealth_config

        # Build constructor kwargs conditionally: only pass user_agent when
        # it is explicitly set. Passing None to browser-use's Browser() could
        # behave differently from omitting the kwarg entirely.
        browser_kwargs: dict = dict(
            headless=False,
            window_size=config.window_size,
            viewport=config.viewport,
            ignore_default_args=config.ignore_default_args,
            args=config.browser_args,
            # Enable element highlighting overlays for AI vision:
            # browser-use tags interactive elements with [1], [2], etc.
            highlight_elements=True,
            wait_between_actions=config.wait_between_actions,
        )
        if config.user_agent:
            browser_kwargs["user_agent"] = config.user_agent

        # Inject session cookies via storage_state JSON file.
        #
        # On macOS, Chrome encrypts cookies using a Keychain service name
        # that varies between launch methods (Playwright vs subprocess).
        # Cookies saved by setup_login() cannot be decrypted by
        # browser-use's Chrome subprocess. storage_state bypasses this
        # entirely: StorageStateWatchdog loads the JSON and injects
        # cookies via CDP Network.setCookies (no Keychain involved).
        ss_path = self._storage_state_path
        if Path(ss_path).exists():
            browser_kwargs["storage_state"] = ss_path

        # IMPORTANT: Do NOT pass user_data_dir or executable_path here.
        #
        # 1. user_data_dir: By omitting this, browser-use creates a temporary
        #    profile that is seeded by `storage_state.json`. If the Agent used
        #    the real `user_data_dir`, its Chrome process would overwrite the
        #    `Cookies` SQLite file under a different macOS Keychain context.
        #    Subsequent calls to `setup_login` (Playwright) would fail to
        #    decrypt those cookies, resulting in session loss and CAPTCHAs.
        #
        # 2. executable_path: browser-use's BrowserProfile._copy_profile()
        #    copies the entire profile to a temp directory when it detects
        #    "chrome". By leaving it undefined, browser-use finds System Chrome
        #    naturally via LocalBrowserWatchdog._find_installed_browser_path()
        #    and skips the slow copying logic.
        return Browser(**browser_kwargs)

    def is_session_valid(self) -> bool:
        """
        Check whether a valid login session exists in the sandbox directory.

        Validity is determined by the presence of Chromium's ``Cookies`` file
        in the ``Default`` profile subdirectory. This file is created (and
        updated) by Chromium whenever cookies are written to the persistent
        context — so its existence is a reliable signal that at least one
        login has occurred.

        Returns:
            ``True`` if the ``Cookies`` file exists in the sandbox directory,
            indicating a prior ``setup_login()`` has completed successfully.
            ``False`` if the sandbox is empty or has been reset.

        Note:
            This check confirms a session *file* exists, not that any specific
            social media session is still valid (cookies may have expired).
            For production use, consider adding a lightweight page-load check
            to verify the social media session is still active.
        """
        # Chromium stores cookies for the default profile at this path.
        # The file is created on first login and persists across browser restarts.
        cookies_file = Path(self.data_dir) / "Default" / "Cookies"
        storage_state_file = Path(self._storage_state_path)
        return cookies_file.exists() or storage_state_file.exists()

    def reset_session(self) -> None:
        """
        Delete all browser data and reset the sandbox to a clean state.

        After calling this method, ``is_session_valid()`` will return ``False``
        and the user must run ``setup_login()`` again to re-establish a session.

        This is useful when:
        - The clone account needs to be changed
        - The session has expired and re-login from scratch is required
        - Debugging or testing fresh browser state

        Warning:
            This is a destructive operation. All cookies, cached data,
            localStorage, and downloaded files in the sandbox will be
            permanently deleted.
        """
        data_path = Path(self.data_dir)
        if data_path.exists():
            # Remove the entire sandbox directory tree
            shutil.rmtree(data_path)
        # Also remove the storage_state.json if it exists outside
        # data_dir (currently it's inside, but be safe)
        ss_path = Path(self._storage_state_path)
        if ss_path.exists():
            ss_path.unlink(missing_ok=True)
        # Recreate the empty directory so subsequent mkdir() calls
        # don't fail
        data_path.mkdir(parents=True, exist_ok=True)

    @property
    def _storage_state_path(self) -> str:
        """Path to the exported storage state JSON file."""
        return str(Path(self.data_dir) / _STORAGE_STATE_FILENAME)

    # ------------------------------------------------------------------
    # Chrome binary discovery
    # ------------------------------------------------------------------

    @staticmethod
    def _find_chrome_path() -> str | None:
        """
        Find the System Chrome executable path.

        Uses the same priority order as ``browser-use``'s
        ``LocalBrowserWatchdog._find_installed_browser_path()`` to ensure
        both ``setup_login()`` and ``get_browser()`` use the exact same
        binary. This eliminates profile format mismatch between Chromium
        versions.

        Priority (macOS):
            1. ``/Applications/Google Chrome.app``
            2. Playwright Chromium (fallback)

        Returns:
            Absolute path to the Chrome executable, or ``None`` if no
            system Chrome is found (Playwright Chromium will be used as
            the fallback).
        """
        system = platform.system()
        patterns: list[str] = []

        if system == "Darwin":  # macOS
            patterns = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "/Applications/Google Chrome Canary.app"
                "/Contents/MacOS/Google Chrome Canary",
                "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            ]
        elif system == "Linux":
            patterns = [
                "/usr/bin/google-chrome-stable",
                "/usr/bin/google-chrome",
                "/usr/local/bin/google-chrome",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/usr/local/bin/chromium",
                "/snap/bin/chromium",
                "/usr/bin/brave-browser",
                # WSL2 Support: Use the Windows host's Chrome if running
                # inside a WSL2 environment.
                "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
                "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe",
                "/mnt/c/Program Files/BraveSoftware/Brave-Browser/"
                "Application/brave.exe",
            ]
        elif system == "Windows":
            local_app_data = os.environ.get("LOCALAPPDATA", "")
            patterns = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                rf"{local_app_data}\Google\Chrome\Application\chrome.exe",
            ]

        for pattern in patterns:
            expanded = Path(pattern).expanduser()
            # Handle wildcard patterns (e.g., playwright versioned dirs)
            if "*" in str(expanded):
                matches = sorted(glob.glob(str(expanded)))
                if matches and Path(matches[-1]).is_file():
                    logger.info("Using Chrome binary: %s", matches[-1])
                    return matches[-1]
            elif expanded.exists() and expanded.is_file():
                logger.info("Using Chrome binary: %s", expanded)
                return str(expanded)

        logger.warning(
            "System Chrome not found. Falling back to Playwright Chromium. "
            "For best social media stealth, install Google Chrome."
        )
        return None

    # ------------------------------------------------------------------
    # Lock file cleanup
    # ------------------------------------------------------------------

    def _cleanup_stale_locks(self) -> None:
        """
        Remove Chromium's ``SingletonLock`` / ``SingletonCookie`` /
        ``SingletonSocket`` files from the sandbox directory.

        These files are created by Chromium when it starts and normally
        deleted on clean shutdown. If the browser crashes or is force-killed
        (common with ``browser-use``'s subprocess management), the locks
        persist and prevent subsequent launches with:
        ``TargetClosedError: Target page, context or browser has been closed``

        This method is safe to call even when no lock files exist.
        """
        data_path = Path(self.data_dir)
        for lock_name in _CHROME_LOCK_FILES:
            lock_file = data_path / lock_name
            if lock_file.exists() or lock_file.is_symlink():
                try:
                    lock_file.unlink()
                    logger.debug("Removed stale lock: %s", lock_file)
                except OSError as e:
                    logger.warning("Failed to remove lock file %s: %s", lock_file, e)
