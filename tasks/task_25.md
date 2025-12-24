# Task 25: Interactive TUI with Textual Framework

## 📌 Metadata

- **Epic**: Marketing AI Assistant
- **Priority**: High
- **Estimated Effort**: 1.5 weeks
- **Team**: Backend
- **Related Tasks**: Task 24 (CLI Output Renderer)
- **Blocking**: []
- **Blocked by**: @suneox

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [x] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [x] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] [Component 1](#component-1-textual-app-foundation) - TUI App Foundation ✅
    - [x] [Component 2](#component-2-banner-welcome-screen) - Banner & Welcome Screen ✅
    - [x] [Component 3](#component-3-input-bar-with-slash-commands) - Input Bar ✅ (Tab/Enter, popup styling, command history)
    - [x] [Component 4](#component-4-request-card-collapsible-logs) - Request Card ✅
    - [x] [Component 5](#component-5-agent-renderer-integration) - TUIRenderer (append-style output) ✅
    - [x] [Component 6](#component-6-modern-ui-styling) - Modern UI Styling ✅
    - [x] [Component 7](#component-7-tui-enhancements) - TUI Enhancements ✅ (ESC cancel, status bar, TUI as default CLI)
- [x] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases validated ✅
- [x] 📝 [Task Summary](#📝-task-summary) - Final implementation summary ✅

## 🔗 Reference Documentation

- **Textual Framework**: https://textual.textualize.io/
- **Gemini CLI Reference**: See UI screenshot - hierarchical slash commands, rounded containers
- **Task 24**: `tasks/task_24.md` - Reuse AgentOutputRenderer logic
- **Existing CLI**: `src/cli/inference.py`, `src/cli/agent_renderer.py`
- **Banner**: `test.py` - BRANDMIND_AI_ASCII logo

------------------------------------------------------------------------

## 🎯 Context &amp; Goals

### Bối cảnh

- Task 24 đã implement Rich Live display cho one-shot CLI commands
- Output animation/logs hoạt động tốt nhưng bị "trailing frame" trong scrollback
- Cần full-screen TUI (alternate buffer) để giải quyết vấn đề này
- User muốn UI giống Gemini CLI: banner, slash commands, rounded corners

### Mục tiêu

Implement full interactive TUI với Textual framework:
1. **Banner**: Logo "BRANDMIND AI" khi khởi động (giống Gemini CLI)
2. **Slash Commands**: `/mode`, `/clear`, `/quit` với hierarchical suggestions
3. **Collapsible Logs**: Giới hạn vài dòng, `Ctrl+O` để expand
4. **Modern UI**: Rounded corners, no 90s-style sharp boxes
5. **Reuse Task 24**: Giữ nguyên animation/log rendering logic

### Success Metrics / Acceptance Criteria

- **UX**: Full-screen TUI, no scrollback pollution
- **Navigation**: Slash commands work với hierarchical suggestions
- **Logs**: Collapsible với `Ctrl+O` to expand
- **Styling**: Rounded corners, Gemini CLI-like aesthetic
- **Backward Compatibility**: One-shot modes (`brandmind ask`, etc.) vẫn hoạt động

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Textual TUI App**: Full-screen alternate buffer app với custom widgets, reusing Task 24's AgentOutputRenderer logic for event rendering.

### Stack công nghệ

- **Textual**: Full TUI framework với widgets, CSS styling, event handling
- **Rich** (via Textual): Textual sử dụng Rich internally
- **Reuse**: `AgentOutputRenderer` logic từ Task 24, `SmartLogCapture`, callback system

### Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ╭────────────────────────────────────────────────────────────────────────╮ │
│ │                                                                        │ │
│ │  ██████╗ ██████╗  █████╗ ███╗   ██╗██████╗                             │ │
│ │  ██╔══██╗██╔══██╗██╔══██╗████╗  ██║██╔══██╗  ... BRANDMIND AI ...      │ │
│ │  ██████╔╝██████╔╝███████║██╔██╗ ██║██║  ██║                            │ │
│ │  ...                                                                   │ │
│ │                                                                        │ │
│ ╰────────────────────────────────────────────────────────────────────────╯ │
│                                                                            │
│  ╭─ Request: "What is 4P in marketing?" ─────────────────────────────────╮ │
│  │ ● Agent thinking                                                      │ │
│  │   Analyzing... (Ctrl+O to expand)                                     │ │
│  │ ✓ search_knowledge_graph                                              │ │
│  │   └─ query: "4P marketing"                                            │ │
│  │   └─ 📋 Logs: [2 lines] (Ctrl+O to expand)                            │ │
│  ╰───────────────────────────────────────────────────────────────────────╯ │
│                                                                            │
│  ╭─ 📝 Answer ───────────────────────────────────────────────────────────╮ │
│  │ The 4P Marketing Mix consists of...                                   │ │
│  ╰───────────────────────────────────────────────────────────────────────╯ │
│                                                                            │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ > /mode                                                                │ │
│ │   ┌────────────────────────────────────────────┐                       │ │
│ │   │ ask          Interactive Q&amp;A               │                       │ │
│ │   │ search-kg    Search Knowledge Graph        │                       │ │
│ │   │ search-docs  Search Documents              │                       │ │
│ │   └────────────────────────────────────────────┘                       │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

### Issues &amp; Solutions

1. **Trailing frames** → Textual uses alternate buffer (no scrollback)
2. **Slash command hierarchy** → Custom autocomplete widget with levels
3. **Log expansion** → `Collapsible` widget with `Ctrl+O` binding
4. **Rounded corners** → Textual CSS: `border: round green;`

### 🎨 Design System

> **Philosophy**: Modern, professional dark theme based on **BrandMind AI brand colors** - Teal Mint primary with Coral Orange accents.

#### Brand Colors (from Logo)

![BrandMind AI Logo](/Users/mac/.gemini/antigravity/brain/d3f3263f-a154-4935-94ed-367e66061228/uploaded_image_1766375894854.png)

| Role | Color Name | Hex Code | Source |
|------|------------|----------|--------|
| **Primary** | Teal Mint | `#6DB3B3` | Background & suit |
| **Accent** | Coral Orange | `#E8834A` | Tie accent |
| **Highlight** | Soft Pink | `#F0A0A0` | Ears detail |
| **Outline** | Dark Navy | `#2D3748` | Outline strokes |

#### Full TUI Color Palette

| Role | Color Name | Hex Code | Usage |
|------|------------|----------|-------|
| **Background** | Deep Space | `#0d1117` | Main screen background |
| **Surface** | Carbon | `#161b22` | Cards, panels, containers |
| **Surface Hover** | Slate | `#21262d` | Hover states, popups |
| **Border** | Charcoal | `#30363d` | Subtle borders |
| **Border Focus** | Teal Mint | `#6DB3B3` | Focused input/selected items |
| **Primary** | Teal Mint | `#6DB3B3` | Primary accents, banner, queries |
| **Secondary** | Light Teal | `#8FCECE` | Success states, ✓ icons |
| **Accent** | Coral Orange | `#E8834A` | Tool calls, highlights, interactive |
| **Warning** | Soft Orange | `#D69E5A` | In-progress states |
| **Error** | Rose | `#E85A5A` | Error messages |
| **Text Primary** | Cloud White | `#e6edf3` | Main content text |
| **Text Secondary** | Silver | `#8b949e` | Descriptions, hints |
| **Text Muted** | Storm Gray | `#6e7681` | Timestamps, collapsed text |

#### Typography

| Element | Style | Color |
|---------|-------|-------|
| Banner Logo | ASCII Art | `#6DB3B3` (Teal Mint) |
| Card Title | Bold | `#e6edf3` (Cloud White) |
| Query Text | Normal | `#6DB3B3` (Teal Mint) |
| Thinking Header | Bold + ● bullet | `#8FCECE` (Light Teal) |
| Thinking Content | Normal/Dim | `#8b949e` (Silver) |
| Tool Name | Bold | `#E8834A` (Coral Orange) ⭐ |
| Tool Args | Normal | `#8b949e` (Silver) |
| Tool Result | Normal | `#6DB3B3` (Teal Mint) |
| Logs (collapsed) | Italic | `#6e7681` (Storm Gray) |
| Answer Text | Normal | `#e6edf3` (Cloud White) |
| Input Placeholder | Italic | `#6e7681` (Storm Gray) |
| Slash Commands | Normal | `#e6edf3` (Cloud White) |
| Command Descriptions | Normal | `#8b949e` (Silver) |

#### Visual Hierarchy

```
╭─ Card Border: round, 1px, Charcoal (#30363d) ───────────────────────╮
│                                                                     │
│  [Query Text - Teal Mint (#6DB3B3)]                                 │
│                                                                     │
│  ● Thinking... [Light Teal (#8FCECE) Bold]                          │
│    [Thinking content - Silver dim]                                  │
│                                                                     │
│  ✓ search_knowledge_graph [Coral Orange (#E8834A) Bold]             │
│    └─ query: "4P marketing" [Silver]                                │
│    └─ 📋 [3 logs] (Ctrl+O) [Storm Gray Italic]                      │
│                                                                     │
│  ╭─ Answer Border: round, 1px, Teal Mint ──────────────────────────╮│
│  │ 📝 [Answer content - Cloud White]                               ││
│  ╰─────────────────────────────────────────────────────────────────╯│
╰─────────────────────────────────────────────────────────────────────╯
```

#### CSS Variables (Textual)

```tcss
/* BrandMind AI Brand Colors */
$background: #0d1117;
$surface: #161b22;
$surface-hover: #21262d;
$border: #30363d;
$border-focus: #6DB3B3;      /* Teal Mint */
$primary: #6DB3B3;           /* Teal Mint - from logo background */
$secondary: #8FCECE;         /* Light Teal */
$accent: #E8834A;            /* Coral Orange - from logo tie */
$warning: #D69E5A;           /* Soft Orange */
$error: #E85A5A;             /* Rose */
$text: #e6edf3;
$text-secondary: #8b949e;
$text-muted: #6e7681;
```

#### Icon Set

| Icon | Usage | Color |
|------|-------|-------|
| ● | Thinking indicator | `$secondary` (#8FCECE Light Teal) |
| ✓ | Completed tool call | `$primary` (#6DB3B3 Teal Mint) |
| ⟳ | In-progress tool call | `$accent` (#E8834A Coral Orange) |
| 📋 | Logs section | `$text-muted` (#6e7681) |
| 📝 | Answer section | `$primary` (#6DB3B3) |
| ❌ | Error/failed | `$error` (#E85A5A) |
| 🔧 | Tool call (alternative) | `$accent` (#E8834A Coral Orange) |

#### Animation &amp; Transitions

- **Spinner**: Dots animation while "Thinking..." (green color)
- **Collapsible**: Smooth slide animation 150ms
- **Popup**: Fade in 100ms
- **Focus ring**: 2px glow effect với `$border-focus`

#### Responsive Behavior

- **Min width**: 80 columns (terminal standard)
- **Max content width**: 120 columns (readability)
- **Log truncation**: 100 chars collapsed, full on expand
- **Tool arg truncation**: 60 chars
- **Result preview**: 150 chars

#### ⚡ Performance & Responsiveness (Critical)

> **Goal**: Zero perceived lag. UI must respond instantly to user input.

##### Problem Scenarios to Avoid

| Scenario | Bad UX | Target |
|----------|--------|--------|
| User presses Enter | 2-3s before anything shows | < 50ms spinner appears |
| Agent thinking | UI frozen | Continuous animation |
| Tool execution | No feedback | Real-time log streaming |
| Long response | Blocking | Progressive rendering |

##### Solution Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      MAIN UI THREAD                              │
│  - Input handling (< 16ms response)                              │
│  - Render updates (60 FPS target)                                │
│  - Widget interactions                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │ post_message() / call_later()
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TEXTUAL WORKER THREAD                         │
│  - Agent execution (async)                                       │
│  - LLM API calls                                                 │
│  - Database queries                                              │
│  - Callback events → UI updates                                  │
└─────────────────────────────────────────────────────────────────┘
```

##### Implementation Patterns

1. **Immediate Feedback on Enter**
```python
async def on_input_bar_submit(self, event: InputBar.Submit) -> None:
    query = event.value.strip()
    
    # Step 1: INSTANT UI update (< 16ms)
    card = RequestCard(query)
    await self.mount(card)
    card.show_spinner()  # Show "Thinking..." immediately
    
    # Step 2: Run agent in background worker (non-blocking)
    self.run_worker(
        self._execute_agent(query, card),
        name="agent_worker",
        exclusive=True,
    )
```

2. **Textual Worker Pattern (Non-blocking)**
```python
from textual.worker import Worker, WorkerState

@work(exclusive=True, thread=True)
async def _execute_agent(self, query: str, card: RequestCard) -> None:
    """Run agent in background - UI stays responsive."""
    agent = create_qa_agent(
        callback=lambda e: self.call_from_thread(card.handle_event, e)
    )
    result = await agent.ainvoke({"messages": [...]})
    self.call_from_thread(card.set_answer, result)
```

3. **Real-time Event Streaming**
```python
def handle_event(self, event: BaseAgentEvent) -> None:
    """Called from worker thread - updates UI immediately."""
    # Use post_message for thread-safe UI updates
    self.post_message(AgentEventMessage(event))

async def on_agent_event_message(self, message: AgentEventMessage) -> None:
    """Process on main thread - safe to update widgets."""
    self._update_display(message.event)
```

4. **Debounced Rendering (Prevent Flickering)**
```python
class RequestCard(Widget):
    def __init__(self):
        self._pending_refresh = False
        self._last_refresh = 0
    
    def request_refresh(self) -> None:
        """Debounce refreshes to max 30 FPS."""
        now = time.monotonic()
        if now - self._last_refresh > 0.033:  # 30 FPS
            self.refresh()
            self._last_refresh = now
```

##### Performance Checklist

- [ ] **Input → Spinner**: < 50ms (user perceives instant)
- [ ] **Spinner animation**: 60 FPS (smooth dots)
- [ ] **Event → UI update**: < 100ms (real-time feeling)
- [ ] **No UI freeze**: Agent runs in worker thread
- [ ] **No memory leak**: Workers properly cancelled on exit
- [ ] **Scroll performance**: Virtualized for long outputs

##### Key Textual APIs for Performance

| API | Purpose |
|-----|---------|
| `run_worker()` | Run async task without blocking UI |
| `@work(thread=True)` | Decorator for background tasks |
| `call_from_thread()` | Thread-safe UI updates from worker |
| `post_message()` | Async message passing to widgets |
| `refresh()` with debounce | Prevent excessive re-renders |
| `call_later()` | Schedule delayed UI updates |

## 🔄 Implementation Plan

### **Phase 1: Core TUI Foundation**
1. **Create Textual App Class**
   - `src/cli/tui/app.py` - Main BrandMindApp
   - Alternate buffer, proper CSS loading
   - Basic layout: Header (banner), Body (scrollable), Footer (input)

2. **Banner Widget**
   - `src/cli/tui/widgets/banner.py`
   - Display BRANDMIND_AI_ASCII from `banner.py` (new file)
   - Teal Mint (`#6DB3B3`) styling from brand logo

### **Phase 2: Input &amp; Commands**
1. **Input Bar with Slash Commands**
   - `src/cli/tui/widgets/input_bar.py`
   - Custom autocomplete với hierarchical levels
   - `/` triggers suggestion popup (no border frame)
   - Enter on suggestion completes to full form (e.g., `/mode`)

2. **Slash Command System**
   - Level 1: `/mode`, `/clear`, `/quit`
   - Level 2: `/mode ask`, `/mode search-kg`, `/mode search-docs`
   - Fuzzy matching: typing "mo" filters to "mode"

### **Phase 3: Request Cards &amp; Output**
1. **Request Card Widget**
   - `src/cli/tui/widgets/request_card.py`
   - Rounded border container
   - Collapsible sections: Thinking, Tool Calls, Logs
   - `Ctrl+O` toggles expand/collapse

2. **Integrate AgentOutputRenderer Logic**
   - Port chronological event rendering from Task 24
   - Keep deduplication logic, markdown rendering
   - Adapt for Textual widgets instead of Rich Live

### **Phase 4: Agent Integration &amp; Polishing**
1. **Connect Agent Execution**
   - Wire `create_qa_agent()` to TUI
   - Stream events to RequestCard via callback
   - Show answer in separate styled panel

2. **Modern UI Polish**
   - CSS with rounded corners everywhere
   - Consistent color scheme (Gemini CLI-inspired)
   - Mode indicator in status bar

------------------------------------------------------------------------

## 📋 Implementation Detail

&gt; **📝 Coding Standards**: All code in English, proper docstrings, type hints.

### Component 1: Textual App Foundation

#### Requirement 1 - Main App Class
- **Requirement**: Create main TUI application with proper layout
- **Implementation**:
  - `src/cli/tui/app.py`
  ```python
  """
  BrandMind TUI Application.
  
  Full-screen interactive terminal interface using Textual framework.
  Features Gemini CLI-inspired design with banner, slash commands,
  and collapsible request cards.
  """
  from textual.app import App, ComposeResult
  from textual.containers import Container, ScrollableContainer, Vertical
  from textual.widgets import Footer, Header
  
  from cli.tui.widgets.banner import BannerWidget
  from cli.tui.widgets.input_bar import InputBar
  from cli.tui.widgets.request_card import RequestCard
  
  
  class BrandMindApp(App):
      """
      Main BrandMind TUI application.
      
      Layout:
      - Banner (top): Logo display on startup
      - Body (middle): Scrollable request/response cards
      - Input (bottom): Text input with slash command support
      """
      
      CSS_PATH = "styles.tcss"
      BINDINGS = [
          ("ctrl+o", "toggle_expand", "Expand/Collapse"),
          ("ctrl+c", "quit", "Quit"),
      ]
      
      def __init__(self):
          super().__init__()
          self.current_mode = "ask"
          self.show_banner = True
      
      def compose(self) -> ComposeResult:
          """Compose app layout."""
          yield Header()
          with ScrollableContainer(id="main-body"):
              if self.show_banner:
                  yield BannerWidget()
          yield InputBar(id="input-bar")
          yield Footer()
      
      def action_toggle_expand(self) -> None:
          """Toggle expand/collapse on focused request card."""
          focused = self.focused
          if isinstance(focused, RequestCard):
              focused.toggle_expand()
      
      async def on_input_bar_submit(self, event: InputBar.Submit) -> None:
          """Handle user input submission."""
          text = event.value.strip()
          if text.startswith("/"):
              await self._handle_command(text)
          else:
              await self._handle_query(text)
      
      async def _handle_command(self, command: str) -> None:
          """Handle slash commands."""
          parts = command.split()
          cmd = parts[0].lower()
          
          if cmd == "/quit":
              self.exit()
          elif cmd == "/clear":
              self._clear_body()
          elif cmd == "/mode" and len(parts) > 1:
              self.current_mode = parts[1]
              # Update status bar
  
      async def _handle_query(self, query: str) -> None:
          """Execute query in current mode."""
          # Create new RequestCard
          # Run agent with callback to update card
          pass
  ```
- **Acceptance Criteria**:
  - [ ] App starts in alternate buffer
  - [ ] Banner visible on startup
  - [ ] Basic layout renders correctly

---

### Component 2: Banner &amp; Welcome Screen

#### Requirement 1 - Banner Widget
- **Requirement**: Display BRANDMIND AI logo on startup
- **Implementation**:
  - `src/cli/tui/widgets/banner.py`
  ```python
  """
  Banner widget displaying the BRANDMIND AI logo.
  
  Styled with gradient cyan/green colors similar to Gemini CLI aesthetic.
  """
  from textual.widgets import Static
  
  BRANDMIND_AI_ASCII = """
  ██████╗ ██████╗  █████╗ ███╗   ██╗██████╗
  ██╔══██╗██╔══██╗██╔══██╗████╗  ██║██╔══██╗
  ██████╔╝██████╔╝███████║██╔██╗ ██║██║  ██║
  ██╔══██╗██╔══██╗██╔══██║██║╚██╗██║██║  ██║
  ██████╔╝██║  ██║██║  ██║██║ ╚████║██████╔╝
  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝
  
  ███╗   ███╗██╗███╗   ██╗██████╗      █████╗ ██╗
  ████╗ ████║██║████╗  ██║██╔══██╗    ██╔══██╗██║
  ██╔████╔██║██║██╔██╗ ██║██║  ██║    ███████║██║
  ██║╚██╔╝██║██║██║╚██╗██║██║  ██║    ██╔══██║██║
  ██║ ╚═╝ ██║██║██║ ╚████║██████╔╝    ██║  ██║██║
  ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝     ╚═╝  ╚═╝╚═╝
  """
  
  
  class BannerWidget(Static):
      """Banner widget showing the BRANDMIND AI logo."""
      
      DEFAULT_CSS = """
      BannerWidget {
          text-align: center;
          color: $primary;  /* Teal Mint #6DB3B3 */
          padding: 1;
      }
      """
      
      def __init__(self):
          super().__init__(BRANDMIND_AI_ASCII)
  ```
- **Acceptance Criteria**:
  - [ ] Logo displays centered with Teal Mint (`#6DB3B3`) coloring
  - [ ] Banner can be hidden after first query

---

### Component 3: Input Bar with Slash Commands

#### Requirement 1 - Hierarchical Slash Command Autocomplete
- **Requirement**: Input with popup suggestions when typing `/`
- **Implementation**:
  - `src/cli/tui/widgets/input_bar.py`
  ```python
  """
  Input bar with hierarchical slash command autocomplete.
  
  Pressing "/" shows available commands at current level.
  Typing filters suggestions. Enter completes the selection.
  """
  from textual.widgets import Input
  from textual.containers import Vertical
  from textual.message import Message
  from textual.widgets import Static
  
  
  # Command hierarchy definition
  SLASH_COMMANDS = {
      "mode": {
          "description": "Change operation mode",
          "subcommands": {
              "ask": "Interactive Q&amp;A with agent",
              "search-kg": "Search Knowledge Graph directly",
              "search-docs": "Search Document Library directly",
          }
      },
      "clear": {
          "description": "Clear conversation history",
          "subcommands": {}
      },
      "quit": {
          "description": "Exit the application",
          "subcommands": {}
      },
  }
  
  
  class SuggestionPopup(Static):
      """
      Popup widget showing command suggestions.
      
      No border frame - clean list like Gemini CLI.
      """
      
      DEFAULT_CSS = """
      SuggestionPopup {
          background: $surface;
          padding: 0 1;
          layer: popup;
      }
      """
      
      def __init__(self, suggestions: list[tuple[str, str]]):
          lines = "\n".join(
              f"{name:<20} {desc}" for name, desc in suggestions
          )
          super().__init__(lines)
  
  
  class InputBar(Input):
      """
      Input bar with slash command support.
      
      Features:
      - "/" triggers command popup
      - Hierarchical navigation (/ -> /mode -> /mode ask)
      - Fuzzy filtering as user types
      """
      
      class Submit(Message):
          """Submitted input message."""
          def __init__(self, value: str):
              super().__init__()
              self.value = value
      
      def __init__(self, **kwargs):
          super().__init__(placeholder="> Type message or / for commands", **kwargs)
          self._popup: SuggestionPopup | None = None
          self._current_level: list[str] = []
      
      async def on_input_changed(self, event: Input.Changed) -> None:
          """Show/update suggestions as user types."""
          value = event.value
          
          if value.startswith("/"):
              await self._show_suggestions(value[1:])
          elif self._popup:
              await self._hide_popup()
      
      async def _show_suggestions(self, query: str) -> None:
          """Show filtered suggestions for current query."""
          parts = query.split()
          
          if not parts:
              # Top level - show all commands
              suggestions = [
                  (cmd, data["description"]) 
                  for cmd, data in SLASH_COMMANDS.items()
              ]
          elif len(parts) == 1 and parts[0] in SLASH_COMMANDS:
              # Show subcommands
              cmd_data = SLASH_COMMANDS[parts[0]]
              suggestions = [
                  (sub, desc) 
                  for sub, desc in cmd_data["subcommands"].items()
              ]
          else:
              # Filter by prefix
              prefix = parts[-1].lower()
              if len(parts) == 1:
                  suggestions = [
                      (cmd, data["description"]) 
                      for cmd, data in SLASH_COMMANDS.items()
                      if cmd.startswith(prefix)
                  ]
              else:
                  # Filter subcommands
                  parent = parts[0]
                  if parent in SLASH_COMMANDS:
                      suggestions = [
                          (sub, desc)
                          for sub, desc in SLASH_COMMANDS[parent]["subcommands"].items()
                          if sub.startswith(prefix)
                      ]
                  else:
                      suggestions = []
          
          if suggestions:
              if self._popup:
                  await self._popup.remove()
              self._popup = SuggestionPopup(suggestions)
              await self.mount(self._popup)
      
      async def action_submit(self) -> None:
          """Handle Enter key - complete or submit."""
          # If popup visible and single match, complete it
          # Otherwise submit the full value
          self.post_message(self.Submit(self.value))
          self.value = ""
  ```
- **Acceptance Criteria**:
  - [ ] "/" shows top-level commands
  - [ ] Typing filters suggestions
  - [ ] Enter on suggestion completes to full form
  - [ ] No border frame on suggestion popup

---

### Component 4: Request Card (Collapsible Logs)

#### Requirement 1 - Collapsible Request/Response Card
- **Requirement**: Card container with expandable sections for logs
- **Implementation**:
  - `src/cli/tui/widgets/request_card.py`
  ```python
  """
  Request card widget with collapsible sections.
  
  Displays query, thinking, tool calls, logs, and answer.
  Logs are collapsed by default, expanded with Ctrl+O.
  """
  from textual.widgets import Static, Collapsible
  from textual.containers import Vertical
  from textual.reactive import reactive
  
  
  class RequestCard(Static):
      """
      Card displaying a single request/response cycle.
      
      Features:
      - Rounded border (via CSS)
      - Collapsible thinking/logs sections
      - Ctrl+O toggles expand state
      """
      
      DEFAULT_CSS = """
      RequestCard {
          border: round $primary;
          padding: 1;
          margin: 1 0;
      }
      
      RequestCard .thinking {
          color: $text-muted;
      }
      
      RequestCard .tool-name {
          color: $accent;
          text-style: bold;
      }
      """
      
      is_expanded: reactive[bool] = reactive(False)
      
      def __init__(self, query: str, **kwargs):
          super().__init__(**kwargs)
          self.query = query
          self._thinking = ""
          self._tool_events = []
          self._answer = ""
      
      def compose(self):
          """Compose card contents."""
          yield Static(f"[bold]Q:[/] {self.query}", classes="query-header")
          
          with Collapsible(title="● Thinking...", collapsed=not self.is_expanded):
              yield Static(id="thinking-content", classes="thinking")
          
          yield Vertical(id="tools-container")
          
          yield Static(id="answer-content")
      
      def toggle_expand(self) -> None:
          """Toggle expanded/collapsed state."""
          self.is_expanded = not self.is_expanded
          # Update collapsible states
          for collapsible in self.query(Collapsible):
              collapsible.collapsed = not self.is_expanded
      
      def update_thinking(self, content: str) -> None:
          """Update thinking section."""
          thinking = self.query_one("#thinking-content", Static)
          # Show truncated unless expanded
          if not self.is_expanded and len(content) > 100:
              content = content[:100] + "... (Ctrl+O to expand)"
          thinking.update(content)
      
      def add_tool_event(self, name: str, args: dict, logs: list[str] = None):
          """Add tool call with optional logs."""
          container = self.query_one("#tools-container", Vertical)
          
          # Build tool display - use Coral Orange for tool name
          tool_text = f"[bold #E8834A]✓ {name}[/]\n"
          for k, v in args.items():
              tool_text += f"  {k}: {str(v)[:60]}\n"
          
          if logs:
              if self.is_expanded:
                  for log in logs:
                      tool_text += f"  📋 {log}\n"
              else:
                  tool_text += f"  📋 [{len(logs)} logs] (Ctrl+O to expand)\n"
          
          container.mount(Static(tool_text))
      
      def set_answer(self, answer: str) -> None:
          """Set final answer."""
          answer_widget = self.query_one("#answer-content", Static)
          # Use Teal Mint for answer header
          answer_widget.update(f"\n[bold #6DB3B3]📝 Answer:[/]\n{answer}")
  ```
- **Acceptance Criteria**:
  - [ ] Rounded border displays correctly
  - [ ] Thinking/logs collapsed by default
  - [ ] `Ctrl+O` expands to show full content
  - [ ] Multiple logs show count when collapsed

---

### Component 5: Agent Renderer Integration

#### Requirement 1 - Port AgentOutputRenderer Logic
- **Requirement**: Reuse Task 24's rendering logic within Textual
- **Implementation**:
  - `src/cli/tui/agent_handler.py`
  - Port key logic from `src/cli/agent_renderer.py`:
    - Event deduplication (thinking, tool calls)
    - Chronological ordering
    - Markdown rendering for thinking content
    - Log routing via SmartLogCapture
  - Adapt to update RequestCard widgets instead of Rich Live
- **Acceptance Criteria**:
  - [ ] Events render in chronological order
  - [ ] Deduplication prevents history replay duplicates
  - [ ] Logs route correctly to tool sections

---

### Component 6: Modern UI Styling

#### Requirement 1 - Textual CSS with Design System
- **Requirement**: Apply design system colors and modern aesthetic
- **Implementation**:
  - `src/cli/tui/styles.tcss`
  ```tcss
  /* ============================================
     BrandMind TUI - Design System Stylesheet
     Gemini CLI-inspired dark theme
     ============================================ */
  
  /* === CSS Variables (Design System Colors) === */
  /* BrandMind AI Brand Colors - from logo */
  $background: #0d1117;
  $surface: #161b22;
  $surface-hover: #21262d;
  $border: #30363d;
  $border-focus: #6DB3B3;      /* Teal Mint */
  $primary: #6DB3B3;           /* Teal Mint - from logo background */
  $secondary: #8FCECE;         /* Light Teal */
  $accent: #E8834A;            /* Coral Orange - from logo tie */
  $warning: #D69E5A;           /* Soft Orange */
  $error: #E85A5A;             /* Rose */
  $text: #e6edf3;
  $text-secondary: #8b949e;
  $text-muted: #6e7681;
  
  /* === Global Screen === */
  Screen {
      background: $background;
      color: $text;
  }
  
  /* === Header Bar === */
  Header {
      background: $surface;
      color: $primary;
      border-bottom: solid $border;
      dock: top;
      height: 1;
  }
  
  /* === Footer Bar === */
  Footer {
      background: $surface;
      color: $text-secondary;
      border-top: solid $border;
  }
  
  /* === Main Body Scrollable Area === */
  #main-body {
      height: 1fr;
      padding: 1 2;
      background: $background;
  }
  
  /* === Banner Widget === */
  BannerWidget {
      text-align: center;
      color: $primary;
      margin: 1 0 2 0;
      padding: 1;
  }
  
  /* === Input Bar at Bottom === */
  #input-bar {
      dock: bottom;
      width: 100%;
      margin: 0 2;
      border: round $border;
      background: $surface;
      padding: 0 1;
  }
  
  #input-bar:focus {
      border: round $border-focus;
  }
  
  /* === Request Card (Main Container) === */
  RequestCard {
      border: round $border;
      background: $surface;
      padding: 1;
      margin: 1 0;
  }
  
  RequestCard:focus {
      border: round $border-focus;
  }
  
  /* Card Elements */
  .query-header {
      color: $primary;
      text-style: bold;
      margin-bottom: 1;
  }
  
  .thinking-header {
      color: $accent;
      text-style: bold;
  }
  
  .thinking-content {
      color: $text-secondary;
      margin-left: 2;
  }
  
  .tool-name {
      color: $primary;
      text-style: bold;
  }
  
  .tool-args {
      color: $text-secondary;
      margin-left: 2;
  }
  
  .tool-result {
      color: $secondary;
      margin-left: 2;
  }
  
  .tool-logs {
      color: $text-muted;
      text-style: italic;
      margin-left: 2;
  }
  
  /* === Answer Panel (nested in card) === */
  .answer-panel {
      border: round $secondary;
      background: $surface;
      padding: 1;
      margin-top: 1;
  }
  
  .answer-header {
      color: $secondary;
      text-style: bold;
  }
  
  .answer-content {
      color: $text;
  }
  
  /* === Suggestion Popup (Slash Commands) === */
  SuggestionPopup {
      background: $surface-hover;
      color: $text;
      padding: 0 1;
      border: none;
      layer: popup;
  }
  
  .suggestion-item {
      color: $text;
      padding: 0 1;
  }
  
  .suggestion-item:hover {
      background: $border;
  }
  
  .suggestion-description {
      color: $text-secondary;
  }
  
  /* === Collapsible Sections === */
  Collapsible {
      background: transparent;
      border: none;
      padding: 0;
  }
  
  Collapsible > CollapsibleTitle {
      color: $text-secondary;
      text-style: italic;
  }
  
  /* === Status Indicators === */
  .status-success {
      color: $secondary;
  }
  
  .status-warning {
      color: $warning;
  }
  
  .status-error {
      color: $error;
  }
  
  /* === Spinner (Thinking) === */
  LoadingIndicator {
      color: $secondary;
  }
  
  /* === Keyboard Hint === */
  .hint {
      color: $text-muted;
      text-style: italic;
  }
  ```
- **Acceptance Criteria**:
  - [x] Rounded corners on all containers
  - [x] Gemini CLI-inspired color scheme
  - [x] Clean, modern aesthetic

---

### Component 7: TUI Enhancements

#### Requirement 1 - TUI as Default CLI Mode
- **Requirement**: Running `brandmind` without arguments launches interactive TUI
- **Implementation**:
  - Modified `src/cli/inference.py`:
    - `main()` checks `sys.argv` length before `asyncio.run()`
    - If no args, directly imports and calls `run_tui()` from `cli.tui.app`
    - Avoids nested event loop issues
  - Updated CLI help text and docstring to reflect new behavior
- **Acceptance Criteria**:
  - [x] `brandmind` launches TUI
  - [x] `brandmind ask`, `brandmind search-kg`, etc. still work as before
  - [x] Help shows TUI as default mode

#### Requirement 2 - Query Cancellation (ESC Key)
- **Requirement**: ESC key cancels running query immediately
- **Implementation**:
  - Added `Binding("escape", "cancel_query", ...)` to app bindings
  - `action_cancel_query()` in `BrandMindApp`:
    - Sets `_cancel_requested` flag
    - Calls `_current_future.cancel()` to stop async task
    - Calls `workers.cancel_all()` to stop Textual workers
    - Calls `renderer.cancel()` to ignore subsequent events
  - Added cancellation checks throughout `_execute_query_async()`
  - Added `_cancelled` flag in `TUIRenderer` to ignore events after cancel
- **Acceptance Criteria**:
  - [x] ESC immediately stops running query
  - [x] No stale "thinking" or answers appear after cancellation
  - [x] "Request cancelled" message shown

#### Requirement 3 - Status Bar with Mode Indicator
- **Requirement**: Show current mode and ESC hint at bottom
- **Implementation**:
  - Added `Static` widget with id `status-bar` in `compose()`
  - Shows: `Mode: ask │ ESC to cancel`
  - Updates when mode changes via `/mode` command
  - Styled with dim text in `styles.tcss`
- **Acceptance Criteria**:
  - [x] Status bar visible above input
  - [x] Updates when mode changes
  - [x] ESC hint visible

#### Requirement 4 - Command History (Arrow Keys)
- **Requirement**: Up/Down arrows navigate command history
- **Implementation**:
  - Added `_history`, `_history_index`, `_current_input` to `InputBar`
  - `action_history_prev()` / `action_history_next()` navigate history
  - `_add_to_history()` stores commands, removes duplicates
  - Prioritizes history navigation over suggestion popup when browsing
- **Acceptance Criteria**:
  - [x] Up arrow shows previous command
  - [x] Down arrow returns to newer/current input
  - [x] Duplicates removed from history

#### Requirement 5 - Persistent Background Event Loop
- **Requirement**: Milvus client requires stable event loop across queries
- **Implementation**:
  - Created `BrandMindApp._bg_loop` as class-level persistent event loop
  - Background thread runs `run_forever()` for the loop
  - Queries submitted via `asyncio.run_coroutine_threadsafe()`
  - Returns `Future` that can be cancelled for proper cleanup
- **Acceptance Criteria**:
  - [x] Multiple queries work without event loop errors
  - [x] Cancellation properly interrupts running queries
  - [x] No "event loop already running" errors

------------------------------------------------------------------------

## 🧪 Test Cases


### Test Case 1: TUI Startup & Banner
- **Purpose**: Verify app starts with banner displayed
- **Steps**:
  1. Run `brandmind` (no args)
  2. Observe banner appears with colored logo
  3. Input bar is focused at bottom
- **Expected Result**: Full-screen TUI with banner and input ready
- **Status**: ✅ Passed

### Test Case 2: Slash Command Navigation
- **Purpose**: Verify hierarchical slash commands work
- **Steps**:
  1. Type "/" - observe top-level suggestions appear
  2. Type "mo" - observe filtering to "mode"
  3. Press Tab/Enter - observe "/mode" completed
  4. Type " " - observe subcommands (ask, search-kg, search-docs)
- **Expected Result**: Hierarchical navigation works, no border on popup
- **Status**: ✅ Passed

### Test Case 3: Collapsible Logs
- **Purpose**: Verify Ctrl+O expand/collapse
- **Steps**:
  1. Submit a query that triggers tool calls with logs
  2. Observe logs shown in collapsed state
  3. Press Ctrl+O - observe full logs appear
  4. Press Ctrl+O again - observe collapse back
- **Expected Result**: Toggle expand/collapse works
- **Status**: ✅ Passed

### Test Case 4: Agent Query Execution
- **Purpose**: Verify agent runs and streams output
- **Steps**:
  1. In TUI, type "What is 4P in marketing?"
  2. Observe spinner appears immediately
  3. Observe tool calls render in order
  4. Observe final answer displayed with Markdown
- **Expected Result**: Streaming output with spinner, tools, and Markdown answer
- **Status**: ✅ Passed

### Test Case 5: Mode Switching
- **Purpose**: Verify /mode command changes behavior
- **Steps**:
  1. Run `/mode search-kg`
  2. Observe status bar updates
  3. Submit a query
  4. Verify only KG search is used (no agent loop)
- **Expected Result**: Mode affects execution behavior, status bar reflects change
- **Status**: ✅ Passed

### Test Case 6: Query Cancellation (ESC)
- **Purpose**: Verify ESC key cancels running query
- **Steps**:
  1. Submit a query
  2. While spinner is showing, press ESC
  3. Observe "Request cancelled" message
  4. Submit a new query
- **Expected Result**: Query stops immediately, no stale output appears later
- **Status**: ✅ Passed

### Test Case 7: Command History
- **Purpose**: Verify Up/Down arrow history navigation
- **Steps**:
  1. Submit several queries/commands
  2. Press Up arrow - observe previous command appears
  3. Press Up again - observe older command
  4. Press Down - observe newer command
- **Expected Result**: History navigation works, duplicates removed
- **Status**: ✅ Passed

------------------------------------------------------------------------

## 📝 Task Summary

### What Was Implemented

**Components Completed**:
- [x] [Component 1]: TUI App Foundation - `BrandMindApp` with layout, bindings, worker threads
- [x] [Component 2]: Banner & Welcome Screen - ASCII logo with Teal Mint styling
- [x] [Component 3]: Input Bar - Slash commands, Tab completion, command history (Up/Down)
- [x] [Component 4]: Request Card - Collapsible logs, Ctrl+O expand/collapse
- [x] [Component 5]: TUIRenderer - Streaming output with spinner, tool displays, Markdown answers
- [x] [Component 6]: Modern UI Styling - Brand colors, rounded corners, Gemini CLI aesthetic
- [x] [Component 7]: TUI Enhancements - ESC cancellation, status bar, TUI as default CLI

**Files Created/Modified**:
```
src/cli/tui/
├── __init__.py               # Module exports
├── app.py                    # Main BrandMindApp class with worker pattern
├── styles.tcss               # Textual CSS with brand colors
├── tui_renderer.py           # TUIRenderer (append-style output)
├── agent_handler.py          # Agent configuration wrapper
└── widgets/
    ├── __init__.py           # Widget exports
    ├── banner.py             # BRANDMIND AI ASCII logo
    ├── input_bar.py          # Slash commands + history navigation
    └── request_card.py       # Collapsible request/response card

src/cli/inference.py          # Modified: TUI as default, CLI modes as subcommands
pyproject.toml                # Added banner.py to ruff exclude
```

**Key Features Delivered**:
1. **Full-screen TUI**: Alternate buffer, no scrollback pollution
2. **Gemini CLI-style**: Banner, slash commands, rounded corners
3. **Collapsible Logs**: Ctrl+O expand/collapse
4. **TUI as Default**: `brandmind` launches TUI, subcommands for CLI modes
5. **Query Cancellation**: ESC immediately stops running query
6. **Command History**: Up/Down arrows navigate previous commands
7. **Status Bar**: Shows current mode and ESC hint
8. **Persistent Event Loop**: Milvus-compatible async architecture

------------------------------------------------------------------------
