# Task 24: Improved CLI Output with Rich Live Display

## 📌 Metadata

- **Epic**: Marketing AI Assistant
- **Priority**: High
- **Estimated Effort**: 1 week
- **Team**: Backend
- **Related Tasks**: Task 23 (Inference CLI)
- **Blocking**: []
- **Blocked by**: @suneox

### ✅ Progress Checklist

- [ ] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [ ] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [ ] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [ ] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [ ] ⏳ [Component 1](#component-1-middleware-callback-system) - Middleware Callback System
    - [ ] ⏳ [Component 2](#component-2-rich-live-renderer) - Rich Live Renderer
    - [ ] ⏳ [Component 3](#component-3-thinking-display) - Thinking Display (● prefix)
    - [ ] ⏳ [Component 4](#component-4-tool-call-display) - Tool Call Display (collapsible)
    - [ ] ⏳ [Component 5](#component-5-todo-display) - Todo Display (strikethrough)
    - [ ] ⏳ [Component 6](#component-6-log-capture-system) - **Log Capture System** (internal function logs)
    - [ ] ⏳ [Component 7](#component-7-cli-integration) - CLI Integration
- [ ] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation
- [ ] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **Rich Live Display**: https://rich.readthedocs.io/en/latest/live.html
- **Reference UI**: Claude Code output style
- **Existing CLI**: `src/cli/inference.py`
- **Middleware**: `src/shared/src/shared/agent_middlewares/log_model_message/`

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Đã implement brandmind CLI với 3 modes (ask, search-kg, search-docs) trong Task 23
- Khi chạy `brandmind ask`, logs từ middleware interrupt spinner display:
  ```
  ⠼ Thinking...2025-12-16 14:19:52.100 | INFO | shared.database_clients...
  ⠹ Thinking...2025-12-16 14:20:00.632 | INFO | core.retrieval.kg_retriever...
  ```
- Agent thinking, tool calls, tool results hiện ra lộn xộn
- Cần render output đẹp hơn giống Claude Code style

### Mục tiêu

Improve output của 3 modes hiện tại (ask, search-kg, search-docs) với:
1. **Model thinking**: ● bullet point prefix, distinct styling
2. **Tool call visualization**: Input params, truncated results preview
3. **Todo tracking**: In-progress (green), completed (strikethrough)
4. **Clean output**: Logs không interrupt display, rendered inline

> **Scope**: Chỉ improve rendering cho existing one-shot modes. Full TUI chat mode sẽ là Task 25.

### Success Metrics / Acceptance Criteria

- **UX**: Output không bị interrupt bởi random logs
- **Visualization**: Thinking, tool calls, todos rendered đúng format
- **Compatibility**: Backward compatible - modes vẫn chạy như cũ

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Rich Live Display + Middleware Callback**: Sử dụng Rich Live để render real-time updates trong same terminal area, với callback từ middleware để stream events.

### Stack công nghệ

- **Rich**: Already installed, dùng `Live`, `Panel`, `Tree`, `Text` for rendering
- **Không cần Textual**: Vì đây là one-shot commands, không cần full TUI

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    brandmind ask -q "..."                       │
│                                                                 │
│  ╭──────────────────────── 🎯 Question ────────────────────╮    │
│  │ What is 4P in marketing?                                │    │
│  ╰─────────────────────────────────────────────────────────╯    │
│                                                                 │
│  ● Model is thinking...                                         │
│    My approach: First query KG for conceptual understanding...  │
│                                                                 │
│  🔧 search_knowledge_graph                                      │
│     └─ query: "4P marketing mix"                                │
│     ✓ Results: [3 entities, 5 relationships]                    │
│                                                                 │
│  📋 Todos                                                       │
│     ☐ Query Knowledge Graph                    [in_progress]    │
│     ☒ Synthesize answer                        [completed]      │
│                                                                 │
│  ╭──────────────────────── 📝 Answer ──────────────────────╮    │
│  │ The 4P Marketing Mix consists of...                     │    │
│  ╰─────────────────────────────────────────────────────────╯    │
└─────────────────────────────────────────────────────────────────┘
```

### Issues & Solutions

1. **Log interrupt spinner** → Middleware callback thay vì logger.info()
2. **Long tool results** → Truncate preview, show summary counts
3. **Real-time updates** → Rich `Live` context manager với `update()`

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Middleware Callback System**
1. **Define callback types**
   - Create `callback_types.py` với event TypedDict definitions
   - AgentEvent union type: thinking, tool_call, tool_result, todo_update

2. **Update LogModelMessageMiddleware**
   - Add `callback: Callable | None` parameter
   - When callback present, call it instead of logger.info()

### **Phase 2: Rich Live Renderer**
1. **Create AgentOutputRenderer class**
   - Manages Rich `Live` display
   - Receives events from middleware callback
   - Builds dynamic renderable (Group of panels/trees)

### **Phase 3: CLI Integration**
1. **Update run_ask_mode**
   - Create renderer instance
   - Pass callback to middleware
   - Use `with Live():` context around agent execution

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards**: All code in English, proper docstrings, type hints.

### Component 1: Middleware Callback System

#### Requirement 1 - Callback Type Definition
- **Requirement**: Define callback interface cho agent events using Pydantic BaseModel inheritance
- **Design Pattern**: Base class `BaseAgentEvent` với subclasses cho từng event type
- **Implementation**:
  - `src/shared/src/shared/agent_middlewares/callback_types.py`
  ```python
  """
  Callback type definitions for agent middleware output integration.
  
  Uses Pydantic BaseModel inheritance for type-safe, extensible event types.
  All events inherit from BaseAgentEvent for consistent type annotation.
  """
  from typing import Any, Callable, Literal

  from pydantic import BaseModel, Field


  class BaseAgentEvent(BaseModel):
      """
      Base class for all agent events.
      
      All specific event types inherit from this class, enabling
      consistent type annotation: `def handle(event: BaseAgentEvent)`
      """
      type: str = Field(..., description="Event type discriminator")
      
      class Config:
          """Pydantic config."""
          frozen = True  # Immutable events


  class ThinkingEvent(BaseAgentEvent):
      """Event emitted when model produces thinking content."""
      type: Literal["thinking"] = "thinking"
      content: str = Field(..., description="Model thinking content")


  class ToolCallEvent(BaseAgentEvent):
      """Event emitted when tool is called."""
      type: Literal["tool_call"] = "tool_call"
      tool_name: str = Field(..., description="Name of the tool being called")
      arguments: dict[str, Any] = Field(
          default_factory=dict,
          description="Tool call arguments"
      )


  class ToolResultEvent(BaseAgentEvent):
      """Event emitted when tool returns result."""
      type: Literal["tool_result"] = "tool_result"
      tool_name: str = Field(..., description="Name of the tool")
      result: str = Field(..., description="Tool execution result")


  class TodoUpdateEvent(BaseAgentEvent):
      """Event emitted when todo list changes."""
      type: Literal["todo_update"] = "todo_update"
      todos: list[dict[str, Any]] = Field(
          default_factory=list,
          description="Current todo list state"
      )


  # Type alias for callback function
  # Uses base class for polymorphism - can receive any event type
  AgentCallback = Callable[[BaseAgentEvent], None]
  ```
- **Acceptance Criteria**:
  - [ ] BaseAgentEvent base class defined
  - [ ] All event types inherit from BaseAgentEvent
  - [ ] AgentCallback uses BaseAgentEvent for type annotation
  - [ ] Compatible with existing middleware

#### Requirement 2 - Update LogModelMessageMiddleware
- **Requirement**: Add callback parameter
- **Implementation**:
  - Modify `log_message_middleware.py`
  - Add `callback: AgentCallback | None = None` to `__init__`
  - In `_log_response()`: if callback, emit thinking event
  - In `wrap_tool_call()`: emit tool_call and tool_result events
  - Fallback to loguru when callback=None (backward compatible)
- **Acceptance Criteria**:
  - [ ] callback=None → logs to loguru (backward compatible)
  - [ ] callback set → calls callback instead

---

### Component 2: Rich Live Renderer

#### Requirement 1 - AgentOutputRenderer Class
- **Requirement**: Class để manage Rich Live display với real-time updates
- **Implementation**:
  - `src/cli/agent_renderer.py`
  ```python
  """
  Rich-based renderer for agent output visualization.
  
  Provides Claude Code-style real-time feedback during agent execution,
  including thinking blocks, tool calls, and todo tracking.
  """
  from rich.console import Console, Group
  from rich.live import Live
  from rich.panel import Panel
  from rich.text import Text
  from rich.tree import Tree

  from shared.agent_middlewares.callback_types import AgentEvent


  class AgentOutputRenderer:
      """
      Renders agent events in real-time using Rich Live display.
      
      Handles thinking blocks with ● prefix, tool calls as trees,
      and todo lists with status-based styling.
      """
      
      def __init__(self, console: Console | None = None):
          """Initialize renderer with optional console instance."""
          self.console = console or Console()
          self._thinking: str | None = None
          self._tool_calls: list[dict] = []
          self._todos: list[dict] = []
          self._live: Live | None = None
      
      def start(self) -> None:
          """Start the live display."""
          self._live = Live(
              self._build_display(),
              console=self.console,
              refresh_per_second=4,
          )
          self._live.start()
      
      def stop(self) -> None:
          """Stop the live display."""
          if self._live:
              self._live.stop()
      
      def __enter__(self):
          self.start()
          return self
      
      def __exit__(self, *args):
          self.stop()
      
      def handle_event(self, event: BaseAgentEvent) -> None:
          """
          Process agent event and update display.
          
          Args:
              event: Agent event instance (ThinkingEvent, ToolCallEvent, etc.)
          """
          # Use isinstance for type checking with Pydantic models
          if isinstance(event, ThinkingEvent):
              self._thinking = event.content
          elif isinstance(event, ToolCallEvent):
              self._tool_calls.append({
                  "name": event.tool_name,
                  "args": event.arguments,
                  "result": None,
              })
          elif isinstance(event, ToolResultEvent):
              # Find matching tool call and add result
              for tc in reversed(self._tool_calls):
                  if tc["name"] == event.tool_name and tc["result"] is None:
                      tc["result"] = event.result
                      break
          elif isinstance(event, TodoUpdateEvent):
              self._todos = event.todos
          
          # Refresh display
          if self._live:
              self._live.update(self._build_display())
      
      def _build_display(self) -> Group:
          """Build Rich renderable from current state."""
          elements = []
          
          # Thinking block with ● prefix
          if self._thinking:
              thinking_text = Text()
              thinking_text.append("● ", style="bold magenta")
              content = self._thinking[:500]
              if len(self._thinking) > 500:
                  content += "..."
              thinking_text.append(content, style="dim")
              elements.append(thinking_text)
          
          # Tool calls as trees
          for tc in self._tool_calls:
              tree = Tree(f"[bold cyan]🔧 {tc['name']}[/]")
              for key, val in tc["args"].items():
                  val_str = str(val)[:80]
                  tree.add(f"[dim]{key}:[/] {val_str}")
              if tc["result"]:
                  # Show truncated preview
                  result_preview = tc["result"][:200]
                  if len(tc["result"]) > 200:
                      result_preview += f"... (+{len(tc['result'])-200} chars)"
                  tree.add(f"[green]✓[/] {result_preview}")
              elements.append(tree)
          
          # Todo list with status colors
          if self._todos:
              todo_text = Text("📋 Todos\n", style="bold")
              for todo in self._todos:
                  status = todo.get("status", "pending")
                  content = todo.get("content", "")
                  if status == "completed":
                      todo_text.append("   ☒ ", style="green")
                      todo_text.append(content + "\n", style="strike dim")
                  elif status == "in_progress":
                      todo_text.append("   ☐ ", style="bold green")
                      todo_text.append(content + "\n", style="bold green")
                  else:
                      todo_text.append(f"   ☐ {content}\n", style="dim")
              elements.append(todo_text)
          
          if not elements:
              return Text("[dim]Processing...[/]")
          
          return Group(*elements)
  ```
- **Acceptance Criteria**:
  - [ ] Thinking displayed với ● prefix
  - [ ] Tool calls show name + args as tree
  - [ ] Todos show với status colors
  - [ ] Live updates work without flicker

---

### Component 3: Thinking Display

- **Requirement**: Model thinking hiển thị với ● prefix giống Claude Code
- **Implementation**: Handled in `AgentOutputRenderer._build_display()`
  - ● magenta bold bullet point
  - Dim gray text for content
  - Truncated if > 500 chars
- **Acceptance Criteria**:
  - [ ] ● prefix visible
  - [ ] Distinct from other output

---

### Component 4: Tool Call Display

- **Requirement**: Tool calls shown as tree với args và result preview
- **Implementation**: Rich `Tree` widget trong `_build_display()`
  - Tool name as tree root với 🔧 icon
  - Args as child nodes
  - Result preview (truncated) với ✓ icon
- **Acceptance Criteria**:
  - [ ] Tree structure renders correctly
  - [ ] Long results truncated với "+X chars" indicator

---

### Component 5: Todo Display

- **Requirement**: Todos với different styles per status
- **Implementation**:
  - `in_progress`: Bold green với ☐
  - `completed`: Strikethrough dim với ☒
  - `pending`: Default dim với ☐
- **Acceptance Criteria**:
  - [ ] Correct styling per status
  - [ ] Updates when middleware emits todo_update

---

### Component 6: Log Capture System with Contextvars

> **Problem**: Internal logs từ function code (FalkorDB, kg_retriever, local_search, etc.) được output trực tiếp qua loguru, không qua middleware callback.
>
> **Solution**: Sử dụng Python `contextvars` để automatic track logs thuộc tool nào.
>
> **Example logs cần capture**:
> ```
> 2025-12-16 14:19:52 | INFO | shared.database_clients...falkordb.client:52 - Connected to FalkorDB
> 2025-12-16 14:20:00 | INFO | core.retrieval.kg_retriever:120 - Decomposed: 2 local, 4 global
> 2025-12-16 14:20:01 | INFO | core.retrieval.local_search:131 - Starting local search
> ```

#### Requirement 1 - Tool Context Variable
- **Requirement**: Define contextvars để track current tool đang được execute
- **Implementation**:
  - `src/cli/tool_context.py`
  ```python
  """
  Context variable for tracking current tool execution.
  
  Uses Python's contextvars to automatically track which tool is currently
  executing. This context propagates through all async calls, allowing
  loguru logs to be automatically grouped by their originating tool.
  
  How it works:
  1. Middleware sets current_tool when tool starts
  2. All nested async calls inherit this context
  3. Custom loguru sink reads current_tool to route logs
  4. Middleware resets context when tool finishes
  """
  from contextvars import ContextVar
  from typing import Optional

  # Context variable to track which tool is currently executing
  # None means no tool is active (logs go to "Other" category)
  current_tool: ContextVar[Optional[str]] = ContextVar(
      "current_tool",
      default=None,
  )


  def get_current_tool() -> Optional[str]:
      """Get the name of the currently executing tool, if any."""
      return current_tool.get()


  def set_current_tool(tool_name: str) -> object:
      """
      Set the current tool context.
      
      Returns a token that must be used to reset the context.
      
      Args:
          tool_name: Name of the tool being executed
          
      Returns:
          Token for resetting context via current_tool.reset(token)
      """
      return current_tool.set(tool_name)


  def reset_current_tool(token: object) -> None:
      """Reset the tool context using the token from set_current_tool."""
      current_tool.reset(token)  # type: ignore
  ```
- **Acceptance Criteria**:
  - [ ] ContextVar defined and importable
  - [ ] Works across async calls

---

#### Requirement 2 - Update LogModelMessageMiddleware with Hooks
- **Requirement**: Add optional hooks để inject context tracking behavior (Dependency Inversion)
- **Key Principle**: Middleware KHÔNG import từ `cli/`. Thay vào đó, CLI inject hooks vào middleware.
- **Implementation**:
  - Modify `src/shared/src/shared/agent_middlewares/log_model_message/log_message_middleware.py`
  ```python
  from typing import Callable, Optional
  
  # Type aliases for hooks
  ToolStartHook = Callable[[str], object]  # (tool_name) -> token
  ToolEndHook = Callable[[object], None]   # (token) -> None
  
  class LogModelMessageMiddleware(AgentMiddleware):
      """
      Middleware that logs model thinking and reasoning messages.
      
      Supports optional hooks for tool context tracking without
      importing from specific modules (Dependency Inversion).
      """
      
      def __init__(
          self,
          *,
          callback: AgentCallback | None = None,
          # New hooks for context tracking (injected from CLI)
          on_tool_start: Optional[ToolStartHook] = None,
          on_tool_end: Optional[ToolEndHook] = None,
          # Existing parameters...
          log_thinking: bool = True,
          log_text_response: bool = True,
          log_tool_calls: bool = True,
          log_tool_results: bool = True,
          truncate_thinking: int = 0,
          truncate_tool_results: int = 500,
          exclude_tools: list[str] | None = None,
      ):
          super().__init__()
          self.callback = callback
          self.on_tool_start = on_tool_start
          self.on_tool_end = on_tool_end
          # ... existing init ...
      
      async def awrap_tool_call(
          self,
          request: ToolCallRequest,
          handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
      ) -> ToolMessage | Command:
          """
          Wrap tool call with context tracking and logging.
          
          If on_tool_start/on_tool_end hooks are provided, they will be called
          to manage context (e.g., for log routing via contextvars).
          """
          tool_name = request.tool_call.get("name", "unknown_tool")
          tool_args = request.tool_call.get("args", {})
          
          # Skip excluded tools
          if tool_name in self.exclude_tools:
              return await handler(request)
          
          # Emit tool_call event via callback (using Pydantic model)
          if self.callback:
              from shared.agent_middlewares.callback_types import ToolCallEvent
              self.callback(ToolCallEvent(
                  tool_name=tool_name,
                  arguments=tool_args,
              ))
          elif self.log_tool_calls:
              logger.info(f"🔧 Tool Call: {tool_name}")
          
          # Call on_tool_start hook if provided (for context tracking)
          token = None
          if self.on_tool_start:
              token = self.on_tool_start(tool_name)
          
          try:
              # Execute tool - all nested calls can use context
              result = await handler(request)
              
              # Emit tool_result event (using Pydantic model)
              if self.callback and hasattr(result, "text"):
                  from shared.agent_middlewares.callback_types import ToolResultEvent
                  self.callback(ToolResultEvent(
                      tool_name=tool_name,
                      result=result.text or "",
                  ))
              elif self.log_tool_results and hasattr(result, "text"):
                  content = result.text
                  if content and self.truncate_tool_results > 0:
                      if len(content) > self.truncate_tool_results:
                          content = content[:self.truncate_tool_results] + "..."
                  logger.info(f"🔨 Tool Result [{tool_name}]:\n{content}")
              
              return result
              
          except Exception as e:
              logger.error(f"❌ Tool Error [{tool_name}]: {e}")
              raise
          finally:
              # Call on_tool_end hook if provided
              if self.on_tool_end and token is not None:
                  self.on_tool_end(token)
  ```
- **Acceptance Criteria**:
  - [ ] Middleware emits Pydantic event instances, not dicts
  - [ ] Hooks are optional - backward compatible
  - [ ] Context managed via injected hooks

---

#### Requirement 3 - Smart Log Capture Sink
- **Requirement**: Custom loguru sink routes logs based on current_tool context
- **Implementation**:
  - `src/cli/log_capture.py`
  ```python
  """
  Smart log capture with automatic tool-based routing.
  
  Uses contextvars to automatically determine which tool a log belongs to,
  routing it to the appropriate section in the output renderer.
  """
  from contextlib import contextmanager
  from typing import Callable, Dict, List, Optional

  from loguru import logger

  from cli.tool_context import get_current_tool


  class SmartLogCapture:
      """
      Captures loguru logs and routes them based on tool context.
      
      Logs emitted during tool execution are grouped with that tool.
      Logs emitted outside tool execution go to "other_logs".
      
      Attributes:
          tool_logs: Dict mapping tool_name -> list of log messages
          other_logs: List of logs not belonging to any tool
      """
      
      def __init__(
          self,
          on_tool_log: Callable[[str, str], None],  # (tool_name, message)
          on_other_log: Callable[[str], None],       # (message)
      ):
          """
          Initialize log capture with routing callbacks.
          
          Args:
              on_tool_log: Called when log belongs to a tool: (tool_name, message)
              on_other_log: Called when log doesn't belong to any tool
          """
          self._on_tool_log = on_tool_log
          self._on_other_log = on_other_log
          self._handler_id: Optional[int] = None
          self.tool_logs: Dict[str, List[str]] = {}
          self.other_logs: List[str] = []
      
      def _sink(self, message) -> None:
          """
          Custom loguru sink that routes logs based on context.
          
          Checks current_tool context to determine routing.
          """
          record = message.record
          
          # Format log message: module:function - message
          formatted = (
              f"{record['name'].split('.')[-1]}:{record['function']} - "
              f"{record['message']}"
          )
          
          # Check which tool is currently executing
          current_tool = get_current_tool()
          
          if current_tool:
              # Log belongs to a tool - route to tool section
              if current_tool not in self.tool_logs:
                  self.tool_logs[current_tool] = []
              self.tool_logs[current_tool].append(formatted)
              self._on_tool_log(current_tool, formatted)
          else:
              # No tool context - route to other section
              self.other_logs.append(formatted)
              self._on_other_log(formatted)
      
      def start(self) -> None:
          """Start capturing logs."""
          self._handler_id = logger.add(
              self._sink,
              level="INFO",
              format="{message}",
              filter=lambda record: record["level"].name != "DEBUG",
          )
      
      def stop(self) -> None:
          """Stop capturing logs and restore default handler."""
          if self._handler_id is not None:
              logger.remove(self._handler_id)
              self._handler_id = None
      
      def __enter__(self):
          self.start()
          return self
      
      def __exit__(self, *args):
          self.stop()
      
      def get_logs_for_tool(self, tool_name: str) -> List[str]:
          """Get all logs captured for a specific tool."""
          return self.tool_logs.get(tool_name, [])
      
      def clear(self) -> None:
          """Clear all captured logs."""
          self.tool_logs.clear()
          self.other_logs.clear()
  ```
- **Acceptance Criteria**:
  - [ ] Logs with tool context routed to on_tool_log
  - [ ] Logs without context routed to on_other_log
  - [ ] Context manager works with async code

---

#### Requirement 4 - Update AgentOutputRenderer
- **Requirement**: Display logs inline với tool calls (Claude Code style)
- **Implementation**:
  - Update `src/cli/agent_renderer.py`
  ```python
  """
  Rich-based renderer for agent output visualization.
  
  Provides Claude Code-style real-time feedback during agent execution,
  including thinking blocks, tool calls with inline logs, and todo tracking.
  """
  from rich.console import Console, Group
  from rich.live import Live
  from rich.panel import Panel
  from rich.text import Text
  from rich.tree import Tree
  from typing import Any, Dict, List, Optional

  from shared.agent_middlewares.callback_types import AgentEvent


  class AgentOutputRenderer:
      """
      Renders agent events in real-time using Rich Live display.
      
      Features:
      - Thinking blocks with ● prefix
      - Tool calls as trees with inline logs
      - Todo list with status-based styling
      - Other logs in separate section
      """
      
      def __init__(self, console: Console | None = None):
          """Initialize renderer."""
          self.console = console or Console()
          self._thinking: str | None = None
          self._tool_calls: List[Dict[str, Any]] = []
          self._tool_logs: Dict[str, List[str]] = {}  # tool_name -> logs
          self._other_logs: List[str] = []
          self._todos: List[Dict[str, Any]] = []
          self._live: Live | None = None
      
      def start(self) -> None:
          """Start the live display."""
          self._live = Live(
              self._build_display(),
              console=self.console,
              refresh_per_second=4,
          )
          self._live.start()
      
      def stop(self) -> None:
          """Stop the live display."""
          if self._live:
              self._live.stop()
      
      def __enter__(self):
          self.start()
          return self
      
      def __exit__(self, *args):
          self.stop()
      
      def handle_event(self, event: AgentEvent) -> None:
          """Process agent event from middleware callback."""
          event_type = event["type"]
          
          if event_type == "thinking":
              self._thinking = event["content"]
          elif event_type == "tool_call":
              self._tool_calls.append({
                  "name": event["tool_name"],
                  "args": event["arguments"],
                  "result": None,
                  "done": False,
              })
          elif event_type == "tool_result":
              for tc in reversed(self._tool_calls):
                  if tc["name"] == event["tool_name"] and not tc["done"]:
                      tc["result"] = event["result"]
                      tc["done"] = True
                      break
          elif event_type == "todo_update":
              self._todos = event["todos"]
          
          self._refresh()
      
      def add_tool_log(self, tool_name: str, message: str) -> None:
          """Add log message for a specific tool (from SmartLogCapture)."""
          if tool_name not in self._tool_logs:
              self._tool_logs[tool_name] = []
          self._tool_logs[tool_name].append(message)
          self._refresh()
      
      def add_other_log(self, message: str) -> None:
          """Add log message not belonging to any tool."""
          self._other_logs.append(message)
          self._refresh()
      
      def _refresh(self) -> None:
          """Refresh the live display."""
          if self._live:
              self._live.update(self._build_display())
      
      def _build_display(self) -> Group:
          """Build Rich renderable from current state."""
          elements = []
          
          # === Thinking block with ● prefix ===
          if self._thinking:
              thinking_text = Text()
              thinking_text.append("● ", style="bold magenta")
              content = self._thinking[:500]
              if len(self._thinking) > 500:
                  content += "..."
              thinking_text.append(content, style="dim")
              elements.append(thinking_text)
          
          # === Tool calls with inline logs ===
          for tc in self._tool_calls:
              tool_name = tc["name"]
              
              # Build tree for tool call
              if tc["done"]:
                  header = f"[bold green]✓[/] [bold cyan]{tool_name}[/]"
              else:
                  header = f"[bold yellow]⟳[/] [bold cyan]{tool_name}[/]"
              
              tree = Tree(header)
              
              # Add arguments
              for key, val in tc["args"].items():
                  val_str = str(val)[:60]
                  if len(str(val)) > 60:
                      val_str += "..."
                  tree.add(f"[dim]{key}:[/] {val_str}")
              
              # Add inline logs for this tool (Claude Code style)
              tool_logs = self._tool_logs.get(tool_name, [])
              if tool_logs:
                  logs_branch = tree.add("[dim]📋 Logs:[/]")
                  for log in tool_logs[-5:]:  # Show last 5 logs
                      logs_branch.add(f"[dim]{log}[/]")
                  if len(tool_logs) > 5:
                      logs_branch.add(f"[dim italic]... +{len(tool_logs)-5} more[/]")
              
              # Add result preview if done
              if tc["done"] and tc["result"]:
                  result_preview = tc["result"][:150]
                  if len(tc["result"]) > 150:
                      result_preview += f"... (+{len(tc['result'])-150} chars)"
                  tree.add(f"[green]Result:[/] {result_preview}")
              
              elements.append(tree)
          
          # === Todo list with status styling ===
          if self._todos:
              todo_text = Text("\n📋 Todos\n", style="bold")
              for todo in self._todos:
                  status = todo.get("status", "pending")
                  content = todo.get("content", "")
                  if status == "completed":
                      todo_text.append("   ☒ ", style="green")
                      todo_text.append(content + "\n", style="strike dim")
                  elif status == "in_progress":
                      todo_text.append("   ☐ ", style="bold green")
                      todo_text.append(content + "\n", style="bold green")
                  else:
                      todo_text.append(f"   ☐ {content}\n", style="dim")
              elements.append(todo_text)
          
          # === Other logs (not belonging to any tool) ===
          if self._other_logs:
              other_text = Text("\n📋 Other Logs\n", style="bold dim")
              for log in self._other_logs[-3:]:  # Show last 3
                  other_text.append(f"   {log}\n", style="dim")
              if len(self._other_logs) > 3:
                  other_text.append(
                      f"   ... +{len(self._other_logs)-3} more\n",
                      style="dim italic"
                  )
              elements.append(other_text)
          
          if not elements:
              return Text("[dim]Processing...[/]")
          
          return Group(*elements)
  ```
- **Acceptance Criteria**:
  - [ ] Logs displayed under their respective tool call trees
  - [ ] Other logs displayed in separate section
  - [ ] Real-time updates work

---

### Component 7: CLI Integration

#### Requirement 1 - Update create_qa_agent
- **Requirement**: Accept callback AND hooks để pass to middleware
- **Implementation**:
  - Modify `src/cli/inference.py` `create_qa_agent()`:
  ```python
  from typing import Callable, Optional
  from shared.agent_middlewares.callback_types import AgentCallback
  
  # Type aliases matching middleware hooks
  ToolStartHook = Callable[[str], object]
  ToolEndHook = Callable[[object], None]
  
  def create_qa_agent(
      callback: AgentCallback | None = None,
      on_tool_start: Optional[ToolStartHook] = None,
      on_tool_end: Optional[ToolEndHook] = None,
  ):
      """
      Create Q&A Agent with optional event callback and context hooks.
      
      Args:
          callback: Event callback for middleware events
          on_tool_start: Hook called when tool starts, returns token
          on_tool_end: Hook called when tool ends, takes token
      """
      # ... existing setup ...
      
      log_message_middleware = LogModelMessageMiddleware(
          callback=callback,
          on_tool_start=on_tool_start,    # Inject hook
          on_tool_end=on_tool_end,         # Inject hook
          log_thinking=True,
          log_text_response=False,
          log_tool_calls=True,
          log_tool_results=True,
          truncate_thinking=1000,
          truncate_tool_results=1000,
      )
      
      # ... rest of agent creation ...
  ```

#### Requirement 2 - Update run_ask_mode
- **Requirement**: Integrate renderer, SmartLogCapture, và inject hooks
- **Implementation**:
  ```python
  async def run_ask_mode(question: str, verbose: bool = False) -> None:
      """
      Run Q&A mode with Rich Live output and smart log routing.
      
      Uses contextvars to automatically route internal logs to tools.
      Hooks are injected into middleware following Dependency Inversion.
      """
      from cli.agent_renderer import AgentOutputRenderer
      from cli.log_capture import SmartLogCapture
      from cli.tool_context import set_current_tool, reset_current_tool
      
      # Show question
      console.print(Panel(
          f"[bold cyan]{question}[/bold cyan]",
          title="🎯 Question",
          border_style="cyan",
      ))
      
      # Create renderer
      renderer = AgentOutputRenderer(console)
      
      # Create smart log capture with routing callbacks
      log_capture = SmartLogCapture(
          on_tool_log=renderer.add_tool_log,
          on_other_log=renderer.add_other_log,
      )
      
      with renderer, log_capture:
          # Create agent with:
          # - callback: for middleware events (thinking, tool_call, tool_result)
          # - on_tool_start/end: for context tracking (logs routing)
          agent = create_qa_agent(
              callback=renderer.handle_event,
              on_tool_start=set_current_tool,    # Inject hook
              on_tool_end=reset_current_tool,     # Inject hook
          )
          result = await agent.ainvoke({
              "messages": [{"role": "user", "content": question}]
          })
          answer = extract_answer(result)
      
      # Show final answer
      console.print(Panel(
          Markdown(answer),
          title="📝 Answer",
          border_style="green",
          padding=(1, 2),
      ))
  ```
- **Acceptance Criteria**:
  - [ ] Hooks injected from CLI, not imported in middleware
  - [ ] Tool logs displayed inline với tool call trees
  - [ ] Backward compatible - hooks are optional

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Ask Mode with Renderer
- **Purpose**: Verify improved ask mode output
- **Steps**:
  1. Run `brandmind ask -q "What is 4P?"`
  2. Observe: ● thinking appears
  3. Observe: 🔧 tool call tree
  4. Observe: Final answer panel
- **Expected Result**: Clean, non-interrupted output
- **Status**: ⏳ Pending

### Test Case 2: Todo Tracking Display
- **Purpose**: Verify todo status rendering
- **Steps**:
  1. Ask complex question với multiple steps
  2. Observe todo list updates
  3. See in_progress = green bold
  4. See completed = strikethrough
- **Expected Result**: Correct styling
- **Status**: ⏳ Pending

### Test Case 3: Backward Compatibility
- **Purpose**: Verify modes work when callback=None
- **Steps**:
  1. Ensure search-kg and search-docs still work
  2. They don't use callback, should log normally
- **Expected Result**: Existing behavior unchanged
- **Status**: ⏳ Pending

### Test Case 4: Long Tool Results
- **Purpose**: Verify truncation works
- **Steps**:
  1. Ask question that returns long KG result
  2. Observe result preview is truncated
  3. See "+X chars" indicator
- **Expected Result**: Clean truncated preview
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

### Implementation Status: ✅ COMPLETE

**Components Completed**:
- [x] [Component 1]: Middleware Callback System
- [x] [Component 2]: Rich Live Renderer
- [x] [Component 3]: Thinking Display
- [x] [Component 4]: Tool Call Display
- [x] [Component 5]: Todo Display
- [x] [Component 6]: Log Capture System
- [x] [Component 7]: CLI Integration

**Files Created/Modified**:
```
src/
├── shared/src/shared/agent_middlewares/
│   ├── callback_types.py                    # NEW: Event type definitions
│   │   ├── BaseAgentEvent (Pydantic base)
│   │   ├── ThinkingEvent
│   │   ├── ToolCallEvent
│   │   ├── ToolResultEvent
│   │   ├── TodoUpdateEvent
│   │   └── ModelLoadingEvent               # Shows spinner during model latency
│   │
│   └── log_model_message/
│       └── log_message_middleware.py        # MODIFIED
│           ├── Added callback: AgentCallback parameter
│           ├── Added on_tool_start/on_tool_end hooks (Dependency Inversion)
│           └── Emits ModelLoadingEvent before/after model calls
│
└── cli/
    ├── tool_context.py                      # NEW: ContextVar for tool tracking
    ├── agent_renderer.py                    # NEW: Rich Live renderer (291 lines)
    │   ├── Chronological _events list (thinking & tools interleaved)
    │   ├── Deduplication logic (prevents history replay duplicates)
    │   ├── Thinking content rendered as Markdown
    │   ├── Tool calls as Tree with inline logs
    │   ├── ModelLoadingEvent → "Thinking..." spinner
    │   ├── Todo footer with colors:
    │   │   ├── Pending: normal white
    │   │   ├── In-progress: lavender (#afafff)
    │   │   └── Completed: dim strikethrough
    │   └── Uses vertical_overflow='visible'
    │
    ├── log_capture.py                       # NEW: SmartLogCapture with routing
    └── inference.py                         # MODIFIED: Use renderer + SmartLogCapture
```

### Key Implementation Details

1. **Event Deduplication**
   - Thinking: Checks if content is prefix/continuation of existing block
   - Tools: Checks identical (name + args) to prevent history replay

2. **Chronological Display**
   - Single `_events` list maintains order: thinking → tool → thinking → tool...
   - Events rendered in order of occurrence

3. **ModelLoadingEvent**
   - Emitted before/after `awrap_model_call`
   - Shows "Thinking..." spinner during API latency

4. **Known Limitations**
   - Frame trail in scrollback when using `vertical_overflow='visible'`
   - Strikethrough doesn't render on Mac Terminal.app (use iTerm2/VS Code)

### Future Enhancement: Task 25

Full interactive TUI mode với Textual:
- Full-screen alternate buffer (no scrollback pollution)
- `/mode` command switching (ask, search-kg, search-docs, chat)
- Session history within app
- Keyboard shortcuts

------------------------------------------------------------------------
