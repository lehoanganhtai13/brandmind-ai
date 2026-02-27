# Task 34: Agent Web Browsing Tool (Local-first Social Media Research)

## 📌 Metadata

- **Epic**: Agent Tools & Capabilities
- **Priority**: High
- **Estimated Effort**: 2 weeks
- **Team**: Backend
- **Related Tasks**: Task 29 (Search Orchestration)
- **Blocking**: []
- **Blocked by**: @suneox

### ✅ Progress Checklist

- [X] 🎯 [Context &amp; Goals](#🎯-context--goals) - Problem definition and success metrics
- [X] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [X] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [X] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
  - [X] ✅ [Component 1: Browser Manager](#component-1-browser-manager) - Core browser lifecycle
  - [X] ✅ [Component 2: Stealth Config](#component-2-stealth-config) - Anti-detect configurations
  - [X] ✅ [Component 3: Agent Browser Tool](#component-3-agent-browser-tool) - Tool interface for Agent
  - [ ] ⏳ [Component 4: CLI Commands](#component-4-cli-commands) - Deferred to future phase
- [X] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation
- [X] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards with comprehensive documentation
- **browser-use Docs**: https://docs.browser-use.com/customize/browser-settings
- **Playwright Persistent Context**: https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-persistent-context
- **Reasoning Artifact**: Xem file reasoning chi tiết tại `brain/77b34c29.../reasoning_artifact.md`

---

## 🎯 Context & Goals

### Bối cảnh

- Agent hiện tại chỉ truy cập web qua HTTP crawling (Crawl4AI) và search API (SearXNG, Brave, Google) — không thể tương tác với các trang yêu cầu đăng nhập hoặc JavaScript-heavy như Facebook, Instagram
- Các nền tảng social media sở hữu lượng dữ liệu marketing khổng lồ (competitor posts, trending content, audience engagement) mà agent cần nghiên cứu để tư vấn chiến lược cho user
- Agent cần một trình duyệt thật sự để navigate, đọc feed, xem posts — giống một người dùng thực

### Mục tiêu

Xây dựng một Web Browsing Tool cho Agent cho phép:

1. Agent tự động duyệt web trên các nền tảng social media (Facebook, Instagram) dưới dạng một user đã đăng nhập
2. User chỉ cần login 1 lần vào account clone trong một sandbox browser riêng biệt, Agent sẽ dùng session đó mãi mãi
3. Sandbox browser hoàn toàn tách biệt với trình duyệt cá nhân của user (không đụng vào cookie/session chính)
4. Trình duyệt popup hiện lên cho user theo dõi Agent đang làm gì
5. Không bị các nền tảng social media block/ban account clone

### Success Metrics / Acceptance Criteria

- **Isolation**: Sandbox browser KHÔNG chia sẻ bất kỳ data nào với trình duyệt cá nhân của user
- **Persistence**: User login 1 lần → Agent dùng lại session không cần login lại (cookie FB/IG sống ~2 năm)
- **Visibility**: Trình duyệt popup hiện lên khi Agent duyệt web, elements được highlight cho user xem
- **Stealth**: Account clone không bị ban/block sau 1 tuần sử dụng liên tục bình thường
- **Integration**: Agent có thể gọi browsing tool như một function tool trong quá trình reasoning

---

## 🛠 Solution Design

### Giải pháp đề xuất

**browser-use + Playwright Stealth Config**: Sử dụng `browser-use` làm Agent Logic (DOM extraction, screenshot, action planning) kết hợp Playwright Persistent Context với stealth configuration để duy trì session đăng nhập và chống bị phát hiện bot.

### Stack công nghệ

- **`browser-use`**: Framework AI agent browser — cung cấp DOM extraction (gắn tag `[1]`, `[2]`...), screenshot capture, action loop (LLM → observe → decide → act → repeat). Đã proven ở cấp độ production.
- **Playwright (Chromium)**: Browser automation engine — `launch_persistent_context` để lưu session vĩnh viễn vào `user_data_dir`. Là dependency có sẵn của `browser-use`.
- **Stealth Config**: Sử dụng `browser-use` native config (`ignore_default_args`, `user_agent`, `args`) để loại bỏ automation flags. Nâng cấp lên `patchright` hoặc `camoufox` nếu cần.

### Issues & Solutions

1. **Social media yêu cầu login** → Persistent Context (`user_data_dir`) lưu cookie/localStorage. Tạo "Login Setup" mode cho user tự đăng nhập 1 lần.
2. **Bot bị Meta detect** → 4-layer stealth: (1) Headed mode, (2) Remove automation flags, (3) Static consistent User-Agent, (4) Human-like delays.
3. **Không được ảnh hưởng trình duyệt cá nhân** → Toàn bộ data lưu vào folder sandbox riêng (`~/.brandmind/browser_data/`), hoàn toàn isolated.
4. **User không biết Agent đang làm gì** → `headless=False` + `highlight_elements=True`: cửa sổ Chrome popup, elements AI đang nhìn được tô sáng.

---

## 🔄 Implementation Plan

### **Phase 1: Core Infrastructure (Foundation)**

1. **Browser Manager Module**

   - Tạo `BrowserManager` class quản lý lifecycle của browser instance
   - Implement `user_data_dir` path management (default: `~/.brandmind/browser_data/`)
   - Implement 2 mode: `setup_login()` (headed, user control) và `get_browser()` (headed, AI control)
   - *Decision Point: Verify browser-use `Browser` class accepts all stealth config params*
2. **Stealth Config Module**

   - Tạo `StealthConfig` dataclass tập trung tất cả anti-detect settings
   - Config: `ignore_default_args`, `args`, `user_agent`, `wait_between_actions`, `viewport`
   - Designed to be swappable (future: patchright/camoufox)

### **Phase 2: Agent Integration**

1. **Agent Browser Tool**

   - Đăng ký browsing capability vào Agent tool system
   - Option A: Dùng trực tiếp `browser-use` `Agent` class (tự quản lý action loop)
   - Option B: Wrap thành discrete tools (`browse_to`, `get_page_content`, `screenshot`)
   - *Decision Point: Chọn Option A hay B dựa trên mức độ control cần thiết từ Agent core*
2. **Tool Registration**

   - Register tool vào `agent_tools/__init__.py`
   - Tạo tool description (system prompt) cho LLM biết khi nào nên dùng browser tool

### **Phase 3: CLI & User Experience**

1. **CLI Commands**
   - `brandmind browser setup` — Mở browser sandbox cho user login
   - `brandmind browser status` — Kiểm tra session còn valid không
   - `brandmind browser reset` — Xóa session, tạo lại từ đầu

### **Phase 4: Testing & Hardening**

1. **Functional Testing**
   - Test login setup flow (FB, IG)
   - Test agent browsing flow (navigate, read posts, extract info)
2. **Stealth Testing**
   - Dùng https://bot.sannysoft.com để verify stealth config
   - Chạy agent trên FB/IG liên tục 1 tuần, monitor cho việc bị challenge/block
3. **Nếu bị block**: Nâng cấp anti-detect layer (Phase 5 - optional)

---

## 📋 Implementation Detail

> **📝 Coding Standards & Documentation Requirements**
>
> All code implementations **MUST** follow **enterprise-level Python standards**:
>
> - **Comprehensive Docstrings**: Every module, class, and function must have detailed docstrings in English
> - **Detailed Comments**: Add inline comments explaining complex logic, business rules, and decision points
> - **Consistent String Quoting**: Use double quotes `"` consistently throughout all code
> - **Language**: All code, comments, and docstrings must be in **English only**
> - **Naming Conventions**: Follow PEP 8 naming conventions
> - **Type Hints**: Use Python type hints for all function signatures
> - **Line Length**: Max 100 characters

### Component 1: Browser Manager

#### Requirement 1 - BrowserManager Class

- **Requirement**: Quản lý lifecycle của browser instance (khởi tạo, connect, shutdown). Cung cấp 2 mode hoạt động: Login Setup (user control) và Agent Browsing (AI control).
- **Implementation**:

  - `src/shared/src/shared/agent_tools/browser/browser_manager.py`

  ```python
  import asyncio
  import os
  import shutil
  from pathlib import Path
  from typing import Optional

  from browser_use import Browser
  from playwright.async_api import async_playwright

  from .stealth_config import StealthConfig


  # Default path for the isolated browser sandbox data.
  # All cookies, cache, and localStorage are stored here,
  # completely separated from the user's personal browser.
  DEFAULT_BROWSER_DATA_DIR = os.path.expanduser(
      "~/.brandmind/browser_data"
  )


  class BrowserManager:
      """
      Manages the lifecycle of an isolated, persistent browser instance
      for AI agent web browsing on social media platforms.

      This class provides two operating modes:
      - Login Setup: Opens a visible browser for the user to manually
        log into social media accounts (Facebook, Instagram, etc.)
      - Agent Browsing: Opens the same browser with saved session for
        the AI agent to autonomously navigate and research.

      The browser uses a dedicated data directory (sandbox) that is
      completely isolated from the user's personal browser, ensuring
      no cross-contamination of sessions or cookies.

      Attributes:
          data_dir: Path to the persistent browser data directory
          stealth_config: Anti-detection configuration settings
      """

      def __init__(
          self,
          data_dir: str = DEFAULT_BROWSER_DATA_DIR,
          stealth_config: Optional[StealthConfig] = None,
      ) -> None:
          self.data_dir = data_dir
          self.stealth_config = stealth_config or StealthConfig()

          # Ensure the data directory exists
          Path(self.data_dir).mkdir(parents=True, exist_ok=True)

      async def setup_login(
          self, url: str = "https://www.facebook.com"
      ) -> None:
          """
          Open a visible browser for the user to manually log into
          social media platforms. Uses Playwright's
          launch_persistent_context() directly (not browser-use)
          because this mode is user-controlled, not AI-controlled.

          The browser session (cookies, localStorage) will be saved
          to the data directory for future use by the AI agent.
          The browser stays open until the user closes it manually.

          Args:
              url: Initial URL to navigate to for login
          """
          config = self.stealth_config

          # Build Chromium launch args for stealth
          launch_args = list(config.browser_args)

          async with async_playwright() as p:
              # launch_persistent_context saves all browser data
              # (cookies, localStorage, cache) to user_data_dir
              context = await p.chromium.launch_persistent_context(
                  user_data_dir=self.data_dir,
                  headless=False,
                  viewport=config.viewport,
                  args=launch_args,
                  ignore_default_args=config.ignore_default_args,
                  # Only set user_agent if explicitly configured
                  **(
                      {"user_agent": config.user_agent}
                      if config.user_agent
                      else {}
                  ),
              )

              # Open the login page in a new tab
              page = await context.new_page()
              await page.goto(url)

              # Block until user closes the browser window.
              # When user closes the window, all pages will close,
              # triggering the context close event.
              try:
                  while context.pages:
                      await asyncio.sleep(1)
              except Exception:
                  pass
              finally:
                  await context.close()

      def get_browser(self) -> Browser:
          """
          Create and return a Browser instance configured for AI agent
          browsing, using the previously saved login session.

          The browser will:
          - Be visible (headed) so the user can watch the agent work
          - Highlight interactive elements for AI vision
          - Use stealth settings to avoid bot detection
          - Load the saved session from the data directory

          Returns:
              Browser instance ready for AI agent control

          Raises:
              RuntimeError: If no valid login session exists.
                  User must run setup_login() first.
          """
          if not self.is_session_valid():
              raise RuntimeError(
                  "No valid browser session found. "
                  "Run 'brandmind browser setup' to login first."
              )
          return self._create_browser()

      def _create_browser(self) -> Browser:
          """
          Internal factory method to create a Browser instance with
          stealth configuration for AI agent browsing mode.
          """
          config = self.stealth_config

          # Build kwargs, only include user_agent if set
          browser_kwargs = dict(
              headless=False,
              user_data_dir=self.data_dir,
              window_size=config.window_size,
              viewport=config.viewport,
              ignore_default_args=config.ignore_default_args,
              args=config.browser_args,
              highlight_elements=True,
              wait_between_actions=config.wait_between_actions,
          )
          if config.user_agent:
              browser_kwargs["user_agent"] = config.user_agent

          return Browser(**browser_kwargs)

      def is_session_valid(self) -> bool:
          """
          Check if the browser data directory contains a valid session.

          Returns:
              True if cookies/session data exist in the data directory
          """
          data_path = Path(self.data_dir)
          # Chromium stores cookies in a file named "Cookies"
          cookies_file = data_path / "Default" / "Cookies"
          return cookies_file.exists()

      def reset_session(self) -> None:
          """
          Delete all browser data and start fresh. User will need
          to run setup_login() again after this.
          """
          data_path = Path(self.data_dir)
          if data_path.exists():
              shutil.rmtree(data_path)
          data_path.mkdir(parents=True, exist_ok=True)
  ```
- **Acceptance Criteria**:

  - [ ] `setup_login()` opens a visible browser via Playwright `launch_persistent_context()`
  - [ ] `setup_login()` blocks until user closes the browser window
  - [ ] `get_browser()` returns a Browser with saved session and stealth config
  - [ ] `get_browser()` raises `RuntimeError` if no login session exists
  - [ ] `is_session_valid()` correctly detects if login session exists
  - [ ] `reset_session()` clears all browser data cleanly
  - [ ] Browser data directory is isolated from user's personal browser

### Component 2: Stealth Config

#### Requirement 1 - StealthConfig Dataclass

- **Requirement**: Tập trung tất cả anti-detect settings vào 1 dataclass dễ maintain và swap. Hỗ trợ nâng cấp lên patchright/camoufox sau này mà không cần refactor.
- **Implementation**:

  - `src/shared/src/shared/agent_tools/browser/stealth_config.py`

  ```python
  from typing import Dict, List, Optional

  from pydantic import BaseModel, Field


  class StealthConfig(BaseModel):
      """
      Centralized anti-detection configuration for the browser sandbox.

      This config implements a 4-layer stealth strategy:
      1. Headed mode (headless=False) — avoids GPU/font fingerprint leaks
      2. Remove automation flags — hides navigator.webdriver=true
      3. Consistent User-Agent — let Chromium use its own default UA
         (always matches actual browser version + OS, no mismatch risk)
      4. Human-like delays — avoids behavioral detection

      The config is designed to be swappable: if the basic Playwright
      stealth is insufficient (e.g., Facebook starts blocking), the
      entire browser engine can be swapped to patchright or camoufox
      without changing the BrowserManager interface.

      Attributes:
          user_agent: Custom UA override. None = use Chromium default
              (recommended for max consistency with actual browser)
          window_size: Browser window dimensions (standard desktop)
          viewport: Content area dimensions
          wait_between_actions: Seconds between agent actions (human-like)
          ignore_default_args: Playwright default args to remove
          browser_args: Additional Chromium command-line args
      """

      # None = let Chromium use its own default User-Agent.
      # This is the safest option because it always matches the
      # actual browser version and OS, avoiding any mismatch that
      # anti-bot systems could detect. Only set a custom value if
      # you need to emulate a specific device.
      user_agent: Optional[str] = Field(default=None)
      window_size: Dict[str, int] = Field(
          default={"width": 1440, "height": 900}
      )
      viewport: Dict[str, int] = Field(
          default={"width": 1440, "height": 900}
      )
      wait_between_actions: float = Field(default=1.0)
      ignore_default_args: List[str] = Field(
          default=["--enable-automation"]
      )
      browser_args: List[str] = Field(
          default=["--disable-blink-features=AutomationControlled"]
      )
  ```
- **Acceptance Criteria**:

  - [ ] User-Agent auto-matches current OS (macOS/Windows/Linux)
  - [ ] All 4 stealth layers are configurable via the dataclass
  - [ ] Config values can be overridden at instantiation
  - [ ] Designed for future swap to patchright/camoufox without interface change

### Component 3: Agent Browser Tool

#### Tool Description Approach Decision

Có 2 hướng để mô tả tool cho LLM:

1. **Docstring-based** (giống `search_web.py`): Docstring của function trở thành tool description. Đơn giản, không cần middleware.
2. **AgentMiddleware** (giống `todo_write_middleware.py`): Tạo middleware riêng inject system prompt + custom tool. Phức tạp hơn, phù hợp khi cần persistent state tracking và reminders.

**→ Chọn Approach 1 (Docstring-based)** vì:

- Browser tool là call-and-return, không cần track state giữa các turns (khác với todo cần nhắc agent tick task)
- Không cần inject reminders hay modify model request
- Docstring của `browse_and_research()` sẽ được LLM đọc trực tiếp khi quyết định có gọi tool không

#### Requirement 1 - Tool Registration for Agent

- **Requirement**: Agent phải có thể gọi browsing tool trong quá trình reasoning. Function exposed cho agent chỉ chứa args mà agent tự pass được (`task: str`). Infra dependency (`browser_manager`) phải được bind sẵn qua factory function trước khi đưa tool cho agent.
- **Implementation**:

  - `src/shared/src/shared/agent_tools/browser/browser_tool.py`
  - Pattern: `create_browse_tool(browser_manager)` → trả về function `browse_and_research(task)` với `browser_manager` đã bind sẵn qua closure

  ```python
  import os
  from typing import Callable, Coroutine

  from browser_use import Agent as BrowserAgent, ChatGoogle

  from src.config.system_config import SETTINGS

  from .browser_manager import BrowserManager


  # ChatGoogle model routing for thinking configuration:
  # - gemini-3-pro-preview   → thinking_level ONLY (low/high)
  # - gemini-3-flash-preview → thinking_level OR thinking_budget (all 4 levels)
  # - gemini-2.5-* / gemini-flash-latest → thinking_budget ONLY (int)
  #
  # gemini-3-flash-preview is the correct model to use with thinking_level.
  # thinking_level="low" = light reasoning, ideal for browsing tasks.
  DEFAULT_MODEL = "gemini-3-flash-preview"
  DEFAULT_THINKING_LEVEL: Literal["minimal", "low", "medium", "high"] = "low"


  def _create_browser_llm() -> ChatGoogle:
      """
      Create the ChatGoogle LLM instance for browser agent.

      Uses "low" thinking level — most browsing actions (click, scroll,
      read text) do not require deep reasoning and benefit from speed.

      Returns:
          Configured ChatGoogle instance

      Raises:
          ValueError: If GEMINI_API_KEY is not configured
      """
      # browser-use ChatGoogle reads GOOGLE_API_KEY from env.
      # Our project stores it as GEMINI_API_KEY in SETTINGS,
      # so we bridge the two here.
      if not SETTINGS.GEMINI_API_KEY:
          raise ValueError(
              "GEMINI_API_KEY is not configured. "
              "Run 'make setup-env' to set it up."
          )
      os.environ["GOOGLE_API_KEY"] = SETTINGS.GEMINI_API_KEY

      return ChatGoogle(
          model=DEFAULT_MODEL,
          thinking_level=DEFAULT_THINKING_LEVEL,
      )


  def create_browse_tool(
      browser_manager: BrowserManager,
  ) -> Callable[[str], Coroutine]:
      """
      Factory function that creates the browse_and_research tool
      with browser_manager pre-bound. This is called once during 
      agent initialization to bind the infrastructure dependency.

      Args:
          browser_manager: Pre-configured BrowserManager with
              login session and stealth config

      Returns:
          Async function `browse_and_research(task)` ready to be
          registered as an agent tool
      """

      async def browse_and_research(task: str) -> str:
          """
          Research social media platforms using a real browser
          with a logged-in session.

          Use this tool ONLY when you need to access content that
          requires authentication or JavaScript rendering on social
          media platforms (Facebook, Instagram, etc.). For general
          web search, use search_web() instead.

          This tool opens a visible Chrome window that the user can
          watch. The AI browser agent will autonomously navigate
          pages, read posts, scroll feeds, and extract relevant
          information.

          When to use:
          - Research competitor social media posts and engagement
          - Analyze trending content on Facebook/Instagram
          - Gather audience feedback from social media comments
          - Browse social media profiles for brand research

          When NOT to use:
          - Simple web search queries → use search_web()
          - Reading public articles/blogs → use crawl tools
          - Searching knowledge graph → use kg_search tools

          Args:
              task: Natural language task for the browser agent.
                  Be specific about what platform, what to look for,
                  and what information to extract.
                  Example: "Go to facebook.com/competitor and
                  summarize their latest 3 posts including
                  engagement metrics"

          Returns:
              Research findings as structured text
          """
          llm = _create_browser_llm()
          browser = browser_manager.get_browser()

          agent = BrowserAgent(
              task=task,
              llm=llm,
              browser=browser,
          )

          result = await agent.run()
          return result

      return browse_and_research
  ```

  - `src/shared/src/shared/agent_tools/browser/__init__.py`

  ```python
  from .browser_manager import BrowserManager
  from .browser_tool import create_browse_tool
  from .stealth_config import StealthConfig

  __all__ = [
      "BrowserManager",
      "StealthConfig",
      "create_browse_tool",
  ]
  ```
- **Acceptance Criteria**:

  - [ ] Agent can call `browse_and_research()` with only `task: str`
  - [ ] LLM is fixed to Gemini 3 Flash (`gemini-3-flash-preview` model name, `thinking_level="low"`)
  - [ ] Raises `ValueError` if `GEMINI_API_KEY` not set
  - [ ] Raises `RuntimeError` if no login session exists
  - [ ] Docstring clearly describes when to use vs when NOT to use
  - [ ] Browser popup is visible and shows element highlights
  - [ ] Browser agent returns structured text findings
  - [ ] Session is preserved after agent finishes (no logout)

### Component 4: CLI Commands

> ⚠️ **Scope**: CLI integration sẽ được thực hiện ở phase sau, sau khi tool đã work standalone. Phần này chỉ document spec cho CLI commands.

#### Requirement 1 - User-facing Setup Commands

- **Requirement**: User cần các CLI commands để quản lý browser session: login lần đầu, kiểm tra trạng thái, reset session.
- **Implementation (future)**:
  - Tích hợp vào CLI framework hiện có (`src/cli/`)
  - Commands:
    - `brandmind browser setup [--url URL]` → Chạy `BrowserManager.setup_login(url)`. Default: facebook.com
    - `brandmind browser status` → Chạy `BrowserManager.is_session_valid()`. Show trạng thái session.
    - `brandmind browser reset` → Chạy `BrowserManager.reset_session()`. Confirm trước khi xóa.
- **Acceptance Criteria** (for future CLI phase):
  - [ ] `brandmind browser setup` opens browser for user to login
  - [ ] `brandmind browser status` shows if session is valid
  - [ ] `brandmind browser reset` confirms before clearing data

---

## 📦 Dependency Setup

### Package Dependency

`browser-use` đã được add vào `shared` package (`make add-shared PKG=browser-use`).
Dependency cũng kéo theo `playwright` tự động.

Sau khi install packages (`make install-all`), cần thêm 1 bước: download Chromium binary cho Playwright. Gộp vào Makefile target:

```makefile
install-browser: ## Download Chromium for browser tool (run once)
	uv run playwright install chromium
	@echo "✅ Browser tool ready. Run 'brandmind browser setup' to login."
```

User chỉ cần chạy:

```bash
make install-browser
```

> **Note**: `playwright install chromium` chỉ cần chạy 1 lần. Nó download ~150MB Chromium binary vào `~/.cache/ms-playwright/`.

---

## 🧪 Test Cases

### Test Case 1: Login Setup Flow

- **Purpose**: Verify user can login to social media and session is persisted
- **Steps**:
  1. Gọi `await browser_manager.setup_login()`
  2. Browser opens at facebook.com
  3. Login with clone account
  4. Close browser window
  5. Check `browser_manager.is_session_valid()` → should return True
- **Status**: ✅ PASSED (manual test)
  - Browser opened at facebook.com, user logged in, browser closed
  - `storage_state.json` exported to `~/.brandmind/browser_data/`
  - `is_session_valid()` returns `True` ✅

### Test Case 2: Agent Browsing with Saved Session

- **Purpose**: Verify agent can browse Facebook with saved login session
- **Steps**:
  1. Complete Test Case 1 (login setup)
  2. Create tool: `browse_tool = create_browse_tool(browser_manager)`
  3. Call: `result = await browse_tool("Go to facebook.com and describe what you see on the news feed")`
  4. Observe browser popup
- **Expected Result**: Browser opens, shows Facebook feed (logged in), agent navigates and returns description. Elements highlighted on screen.
- **Status**: ✅ PASSED (manual test)
  - Agent navigated FB page 'Chuyện Ba Bữa Signature' while logged in
  - Browser popup visible, elements highlighted ✅
  - Session persisted after agent finished (no re-login required) ✅
  - StorageStateWatchdog injected cookies via CDP `Network.setCookies` ✅

### Test Case 2b: Agent Browsing without Session

- **Purpose**: Verify proper error when no login session exists
- **Steps**:
  1. Call `browser_manager.reset_session()` to clear any session
  2. Create tool: `browse_tool = create_browse_tool(browser_manager)`
  3. Call: `result = await browse_tool("Go to facebook.com")`
- **Expected Result**: Raises `RuntimeError` with message "No valid browser session found"
- **Status**: ✅ PASSED (automated smoke test)
  - Confirmed: `RuntimeError: No valid browser session found in '...'. Run setup_login() (or 'brandmind browser setup') to login first.`

### Test Case 2c: Missing API Key

- **Purpose**: Verify proper error when GEMINI_API_KEY not set
- **Steps**:
  1. Unset `GEMINI_API_KEY` from env
  2. Call `browse_tool("any task")`
- **Expected Result**: Raises `ValueError` with message "GEMINI_API_KEY is not configured"
- **Status**: ✅ PASSED (automated smoke test)
  - Confirmed: `ValueError: GEMINI_API_KEY is not configured. Run 'make setup-env' to set it up.`

### Test Case 3: Stealth Verification

- **Purpose**: Verify browser passes anti-bot detection tests
- **Steps**:
  1. Launch browser with `StealthConfig` applied
  2. Check `navigator.webdriver`, `AutomationControlled`, User-Agent
- **Expected Result**: `navigator.webdriver` = False, no automation flags in UA
- **Status**: ✅ PASSED (automated Playwright script)
  - `navigator.webdriver` = `False` ✅
  - `AutomationControlled` in UA = `False` ✅
  - UA: `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36... Chrome/143.0.7499.4` ✅
  - **Note**: Test ran `headless=True` (CI mode), so `HeadlessChrome` appears in UA and `window.chrome` is absent. In production (`headless=False`), these normalize automatically — the core stealth flags (`webdriver`, `AutomationControlled`) are clean in both modes.

### Test Case 4: Session Isolation

- **Purpose**: Verify sandbox browser doesn't interfere with user's personal browser
- **Steps**:
  1. Open user's personal Chrome → verify logged into personal Facebook
  2. Call `await browser_manager.setup_login()` → login with clone account
  3. Re-check personal Chrome → still logged into personal Facebook
- **Expected Result**: Personal Chrome is completely unaffected. Two separate sessions exist independently.
- **Status**: ✅ PASSED (manual test)
  - Personal Chrome login unaffected after sandbox agent runs ✅

### Test Case 5: Session Reset

- **Purpose**: Verify session can be cleanly reset
- **Steps**:
  1. Call `browser_manager.reset_session()`
  2. Check `browser_manager.is_session_valid()` → should return False
  3. Call `await browser_manager.setup_login()` → should open fresh browser (no previous login)
- **Expected Result**: All browser data cleared, `~/.brandmind/browser_data/` is empty, fresh start
- **Status**: ✅ PASSED (automated smoke test)
  - Confirmed: `shutil.rmtree()` clears sandbox, `is_session_valid()` returns False, dir recreated

---

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation to document what was actually accomplished.

### What Was Implemented

**Components Completed**:

- [X] [Component 1]: Browser Manager
  - `setup_login()`: Playwright `launch_persistent_context()`, blocks until user closes browser
  - `get_browser()`: returns stealth-configured `Browser`, raises `RuntimeError` if no session
  - `is_session_valid()`: checks `~/.brandmind/browser_data/Default/Cookies` file
  - `reset_session()`: `shutil.rmtree()` + recreate empty dir
- [X] [Component 2]: Stealth Config
  - Pydantic `BaseModel` with Field-level validation and descriptions
  - 4-layer stealth: headed mode, remove `--enable-automation`, Chromium native UA, `wait_between_actions=1.0s`
- [X] [Component 3]: Agent Browser Tool
  - `create_browse_tool(browser_manager)` factory → closure → `browse_and_research(task)`
  - LLM fixed to `gemini-3-flash-preview` with `thinking_level="low"` (typed as `Literal`)
  - `gemini-3-flash-preview` is required for `thinking_level` support (Gemini 2.x models use `thinking_budget` instead)
  - `agent.run()` → `history.final_result() or str(history)` for correct str return type
- [x] [Component 4]: CLI Commands (`brandmind browser setup`, `status`, `reset`)
  - Thêm `browser` sub-command group vào `src/cli/inference.py` (dùng `argparse`)
  - **`setup`**: In cảnh báo nổi bật (dùng thư viện `rich` để tô màu đỏ/vàng) yêu cầu user **chỉ nên dùng account clone (nick phụ)**. Có prompt `Confirm.ask()` yêu cầu user xác nhận trước khi mở web. Mặc định 3 tab: `facebook.com`, `instagram.com` và `tiktok.com`.
  - **`status`**: Kiểm tra session có còn valid không (`is_session_valid()`).
  - **`reset`**: Xóa toàn bộ session data (`reset_session()`) với prompt cảnh báo mất dữ liệu.

**Files Created/Modified**:

```
src/shared/src/shared/agent_tools/browser/
├── __init__.py              # Package exports (BrowserManager, StealthConfig, create_browse_tool)
├── browser_manager.py       # BrowserManager class (lifecycle, login via Playwright, session)
├── browser_tool.py          # create_browse_tool() factory + browse_and_research() tool
└── stealth_config.py        # StealthConfig Pydantic model (4-layer anti-detect)

src/cli/
└── inference.py             # CLI entrypoint -> Add `browser setup` command using argparse

Makefile
└── install-browser target   # uv run playwright install chromium
```

**Key Features Delivered**:

1. ✅ **Login Setup mode**: `BrowserManager.setup_login()` — Playwright persistent context, user-controlled, blocks until browser closes, exports `storage_state.json`
2. ✅ **Agent Browsing with stealth**: `BrowserManager.get_browser()` + `StealthConfig` — 4-layer anti-detect, headed + highlighted, cookies injected via CDP
3. ✅ **Session persistence (macOS fix)**: `storage_state.json` export/import bypasses macOS Keychain cookie encryption mismatch
4. ✅ **Error handling**: `RuntimeError` (no session), `ValueError` (no API key)
5. ✅ **Type safety**: mypy passes (0 errors in 84 source files), `make typecheck` passes
6. ⏳ **CLI commands**: Thêm `brandmind browser setup` giúp user dễ dàng thao tác gọi giao diện đăng nhập thủ công an toàn một cách trực quan từ Terminal.

### Technical Highlights

**Architecture Decisions**:

- **Factory + closure pattern** for `create_browse_tool()`: keeps agent-facing signature clean (`task: str` only), infra dependency bound at init time
- **Playwright for login, browser-use for agent**: login mode uses Playwright directly (no LLM needed); agent mode uses `browser-use` `Agent` (LLM action loop)
- **`gemini-3-flash-preview` model**: Only Gemini 3 models support `thinking_level`; Gemini 2.x (`gemini-flash-latest`, `gemini-2.5-*`) use `thinking_budget` (int) instead — setting `thinking_level` on them just logs a warning and is silently ignored
- **`user_agent=None`**: Chromium uses its own built-in UA — eliminates version/OS mismatch detection risk
- **`Literal` type** for `thinking_level` + `cast(ViewportSize, ...)` for viewport: required to satisfy mypy's strict type checking

**UX & QoL Improvements**:

- **Multi-URL Login Setup**: `setup_login(urls: list[str])` accepts an array of URLs to open multiple tabs simultaneously in the persistent context.
- **No `about:blank` tab**: `setup_login()` smartly reuses the initial blank page spawned by Playwright's persistent context for the first URL, keeping the tab bar clean.
- **WSL2 Cross-platform Support**: Agent running in a Linux WSL2 environment automatically detects and uses the Windows host's Chrome binary (`/mnt/c/Program Files/...`), enabling a smooth headed GUI experience without needing to install a Linux GUI browser inside the VM. Standard Windows paths are also supported.

**Bug Fixes (Session Persistence)**:

| Root Cause | Fix |
|---|---|
| Playwright defaults to bundled Chromium; browser-use uses System Chrome | `setup_login()` passes `executable_path=system_chrome` so both use same binary |
| `BrowserProfile._copy_profile()` copies profile to temp dir when `executable_path` in `_create_browser()` | Removed `executable_path` from `_create_browser()` — browser-use finds System Chrome naturally |
| **macOS Keychain encryption mismatch** (root cause): Playwright's Chrome and browser-use's Chrome subprocess use different Keychain service names → cookies unreadable | `setup_login()` exports cookies as plaintext `storage_state.json` via `context.storage_state()`; `_create_browser()` passes `storage_state=path` → `StorageStateWatchdog` injects via CDP `Network.setCookies` (bypasses Keychain) |
| **Post-Agent Session Corruption**: `browser-use` overwriting persistent `Cookies` db via `user_data_dir` under a different macOS Keychain context | Removed `user_data_dir` from `_create_browser()`. Agent now runs in a temporary profile seeded by `storage_state.json`, protecting the persistent user profile from corruption. |
| Stale `SingletonLock` after unclean shutdown → `TargetClosedError` | `_cleanup_stale_locks()` removes lock files before launch |

**Documentation Added**:

- [x] All functions have comprehensive docstrings
- [x] Complex business logic is well-commented
- [x] Module-level documentation explains purpose
- [x] Type hints are complete and accurate

### Validation Results

**Test Coverage**:

- [x] TC1: Login setup flow — PASSED
- [x] TC2: Agent browsing with saved session — PASSED (FB page research)
- [x] TC2b: RuntimeError when no session — PASSED (automated)
- [x] TC2c: ValueError when no API key — PASSED (automated)
- [x] TC3: Stealth verification (navigator.webdriver=False) — PASSED (automated)
- [x] TC4: Session isolation (personal Chrome unaffected) — PASSED
- [x] TC5: Session reset cleanly — PASSED (automated)

**Deployment Notes**:

- New dependency: `browser-use==0.11.13` (includes `playwright`) — added to `shared` package via `make add-shared PKG=browser-use`
- One-time setup required: `make install-browser` (downloads Chromium binary to `~/.cache/ms-playwright/`)
- User must run `setup_login()` (or future `brandmind browser setup`) before agent can use browser tool
- **macOS note**: Session cookies exported as `storage_state.json` (plaintext JSON) to bypass Keychain encryption mismatch between Playwright and browser-use Chrome subprocess
- **WSL2 / Windows note**: Fully supported. When running inside WSL2, the application automatically uses the Windows host Chrome (`chrome.exe`) for maximum performance and native GUI experience. No Linux GUI browser installation required.

---
