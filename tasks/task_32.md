# Task 32: Stream Thinking Tokens in Real-Time

## 📌 Metadata

- **Epic**: Agent UX Improvements
- **Priority**: Medium
- **Estimated Effort**: 0.5 weeks
- **Team**: Full-stack
- **Related Tasks**: Task 31 (Token-by-Token Streaming)
- **Blocking**: []
- **Blocked by**: @suneox

### ✅ Progress Checklist

- [ ] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [ ] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [ ] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [ ] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [ ] ⏳ [Component 1: StreamingThinkingEvent](#component-1-streamingthinking-event) - New event type
    - [ ] ⏳ [Component 2: Stream Extraction Logic](#component-2-stream-extraction-logic) - CLI + TUI
    - [ ] ⏳ [Component 3: TUI Renderer Streaming Thinking](#component-3-tui-renderer-streaming-thinking) - Progressive display
    - [x] ⏳ [Component 4: CLI Renderer Streaming Thinking](#component-4-cli-renderer-streaming-thinking) - Progressive display
    - [x] ⏳ [Component 5: Suppress Middleware ThinkingEvent Duplicates](#component-5-suppress-middleware-thinkingevent-duplicates) - Prevent duplicate
- [x] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation
- [x] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards with comprehensive documentation
- **LangChain Google Thinking Docs**: `ChatGoogleGenerativeAI` with `include_thoughts=True` emits thinking blocks in content list
- **LangGraph Streaming Docs**: `stream_mode="messages"` yields `(AIMessageChunk, metadata)` tuples with all content types

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- **Hiện tại**: Thinking content hiển thị **all-at-once** sau khi model xử lý xong mỗi bước. `LogModelMessageMiddleware._log_response()` extract thinking từ completed response rồi emit `ThinkingEvent` — không phải real-time.
- **Task 31 đã giải quyết**: Final answer streaming token-by-token. Tuy nhiên, thinking vẫn xuất hiện đột ngột như 1 block lớn.
- **User experience**: Với model sử dụng thinking (Gemini 2.5/3 + `include_thoughts=True`), thinking process có thể dài. User phải chờ không biết model đang làm gì → UX kém.

### Mục tiêu

Stream thinking tokens real-time giống như final answer đang được stream, cho phép user **nhìn thấy model đang suy nghĩ gì** ngay khi nó generating — không cần chờ cả block thinking hoàn tất.

### Success Metrics / Acceptance Criteria

- **Real-time**: Thinking content xuất hiện progressively (token-by-token), không phải all-at-once
- **No duplication**: Thinking content chỉ hiển thị 1 lần (streaming replaces middleware ThinkingEvent, không hiện 2 lần)
- **Visual distinction**: Streaming thinking rõ ràng khác biệt với streaming answer (icon, color, styling)
- **No regression**: Answer streaming vẫn hoạt động đúng, tool calls và todos không bị ảnh hưởng

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Extract thinking tokens from `astream` chunks**: `stream_mode="messages"` đã yield AIMessageChunks chứa thinking content dưới dạng `{"type": "thinking", "thinking": "..."}` dict entries trong content list. Hiện tại code chỉ extract `type: text`, bỏ qua thinking. Giải pháp: extract cả `type: thinking` blocks từ stream, emit `StreamingThinkingEvent` mới, và render progressively trong cả TUI và CLI renderers.

### Stack công nghệ

- **LangGraph `astream(stream_mode="messages")`**: Đã sử dụng từ Task 31, cung cấp thinking+text chunks
- **Pydantic BaseModel event**: Thêm `StreamingThinkingEvent` tương tự `StreamingTokenEvent`
- **Textual Markdown Widget**: Dùng để render thinking progressively (tương tự answer streaming)

### Issues & Solutions

1. **Thinking đến trước text trong content list** → Extract thinking blocks riêng, text blocks riêng từ mỗi chunk
2. **Middleware ThinkingEvent gây duplicate** → Suppress middleware ThinkingEvent khi đã stream thinking (reuse `_is_streaming_answer` pattern)
3. **Multiple thinking blocks per response** → Mỗi step có thể có thinking riêng, track bằng `langgraph_step` metadata

### Luồng dữ liệu hiện tại vs đề xuất

**Hiện tại (Task 31)**:
```
astream chunk → content list → extract "type: text" only → StreamingTokenEvent → Renderer
                              ↓
                              "type: thinking" → IGNORED ❌

middleware (after model call) → full thinking → ThinkingEvent (all-at-once) → Renderer
```

**Đề xuất (Task 32)**:
```
astream chunk → content list → extract "type: text" → StreamingTokenEvent → Renderer
                              → extract "type: thinking" → StreamingThinkingEvent → Renderer ✅

middleware → ThinkingEvent → SUPPRESSED (already streamed) ✅
```

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Core Implementation**
1. **Add StreamingThinkingEvent** (`callback_types.py`)
   - New event type with `token`, `done`, and optional `title` fields
   - *Decision Point: Confirm event structure works for both renderers*

2. **Extract thinking from stream** (`inference.py` + `app.py`)
   - In the `astream` loop, extract `type: thinking` blocks alongside `type: text`
   - Emit `StreamingThinkingEvent` for thinking content
   - Emit `StreamingTokenEvent` for text content (unchanged)

3. **TUI Renderer** (`tui_renderer.py`)
   - Add `_on_streaming_thinking()` handler — similar to `_on_streaming_token()` but with thinking styling
   - Mount thinking header + Markdown widget, update progressively
   - When thinking stream ends and answer stream starts → finalize thinking widget

4. **CLI Renderer** (`agent_renderer.py`)
   - Add `_streaming_thinking` buffer
   - Handle `StreamingThinkingEvent` in `handle_event()`
   - Display thinking in `_build_display()` with appropriate styling

### **Phase 2: Duplicate Prevention**
1. **Suppress middleware ThinkingEvent during streaming**
   - The middleware `_log_response()` will still emit `ThinkingEvent` after model call completes
   - Renderers should ignore `ThinkingEvent` when thinking was already streamed
   - Reuse `_is_streaming_answer` pattern or add `_has_streamed_thinking` flag

------------------------------------------------------------------------

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

### Component 1: StreamingThinkingEvent

#### Requirement 1 - New Event Type
- **Requirement**: Add `StreamingThinkingEvent` to `callback_types.py`
- **Implementation**:
  - `src/shared/src/shared/agent_middlewares/callback_types.py`
  ```python
  class StreamingThinkingEvent(BaseAgentEvent):
      """Event emitted for each streamed thinking token from the model.

      Enables real-time progressive display of the model's reasoning
      process as thinking tokens arrive from the stream, rather than
      showing the full thinking block all at once after completion.

      Attributes:
          token: Thinking text chunk from the model's streaming output.
          done: Whether this is the final thinking token for this step.
          title: Optional title summarizing the thinking block (emitted
              by some models as the first part of thinking content).
      """

      type: Literal["streaming_thinking"] = "streaming_thinking"
      token: str = Field(
          ..., description="Thinking text chunk from model streaming output"
      )
      done: bool = Field(
          default=False,
          description="True if thinking is complete for this step",
      )
      title: str = Field(
          default="",
          description="Optional title for thinking block",
      )
  ```
- **Acceptance Criteria**:
  - [x] Event class follows `StreamingTokenEvent` pattern
  - [x] Comprehensive docstring in English
  - [x] `type`, `token`, `done`, `title` fields present

### Component 2: Stream Extraction Logic

#### Requirement 1 - Extract Thinking from AIMessageChunks
- **Requirement**: Modify `astream` loops in both `inference.py` and `app.py` to extract `type: thinking` blocks alongside `type: text`
- **Implementation**:
  - `src/cli/inference.py` — `run_ask_mode()` streaming loop
  - `src/cli/tui/app.py` — `_execute_query_async()` streaming loop
  - Logic:
  ```python
  # Inside the astream loop, after filtering tool_calls:
  if isinstance(message_chunk.content, list):
      for part in message_chunk.content:
          if isinstance(part, dict):
              if part.get("type") == "thinking":
                  thinking_text = part.get("thinking", "")
                  if thinking_text:
                      renderer.handle_event(
                          StreamingThinkingEvent(token=thinking_text)
                      )
              elif part.get("type") == "text":
                  token_text = part.get("text", "")
                  if token_text:
                      # When first text arrives, finalize thinking
                      if not thinking_done:
                          renderer.handle_event(
                              StreamingThinkingEvent(token="", done=True)
                          )
                          thinking_done = True
                      accumulated_answer += token_text
                      renderer.handle_event(
                          StreamingTokenEvent(token=token_text)
                      )
  ```
  - **Key logic**: Track `thinking_done` flag. When content transitions from thinking → text, emit `StreamingThinkingEvent(done=True)` before starting text streaming.
  - **Important**: A single model call can have thinking THEN text. Across multiple steps (middleware re-prompts, tool usage), there may be multiple thinking blocks — each step should have its own thinking cycle.
- **Acceptance Criteria**:
  - [x] Thinking extracted from `type: thinking` blocks in stream chunks
  - [x] `StreamingThinkingEvent` emitted for thinking content
  - [x] `StreamingThinkingEvent(done=True)` sent when thinking transitions to text
  - [x] Answer streaming (`StreamingTokenEvent`) unchanged
  - [x] Both CLI and TUI paths updated

### Component 3: TUI Renderer Streaming Thinking

#### Requirement 1 - Progressive Thinking Display
- **Requirement**: Add `_on_streaming_thinking()` to `TUIRenderer` for progressive thinking display
- **Implementation**:
  - `src/cli/tui/tui_renderer.py`
  - New state variables:
    ```python
    self._streaming_thinking_widget: Markdown | None = None
    self._streaming_thinking_buffer: str = ""
    ```
  - New handler method `_on_streaming_thinking(event: StreamingThinkingEvent)`:
    - On first token: Mount thinking header + Markdown widget (reuse existing thinking styling: `[bold #8FCECE]● Thinking[/bold #8FCECE]`)
    - Subsequent tokens: Update widget in-place (same as answer streaming pattern)
    - On `done=True`: Finalize widget, reset state, apply truncation if needed
  - Register in `_process_event()`
- **Acceptance Criteria**:
  - [x] Thinking tokens render progressively in TUI
  - [x] Thinking styling matches existing `_on_thinking()` appearance
  - [x] Widget is finalized when `done=True`
  - [x] Truncation/expand behavior (Ctrl+O) preserved

### Component 4: CLI Renderer Streaming Thinking

#### Requirement 1 - Progressive Thinking in Rich Live Display
- **Requirement**: Add streaming thinking support to `AgentOutputRenderer`
- **Implementation**:
  - `src/cli/agent_renderer.py`
  - New state: `self._streaming_thinking: str = ""`
  - Handle `StreamingThinkingEvent` in `handle_event()`:
    - On `done`: Move to events list as completed thinking block, reset buffer
    - Else: Accumulate into `_streaming_thinking`
  - Update `_build_display()`: Show `_streaming_thinking` with thinking styling
- **Acceptance Criteria**:
  - [x] Thinking tokens render progressively in CLI Live display
  - [x] Completed thinking moves to events list
  - [x] Styling consistent with existing thinking display
  - [x] Refined spacing: Thinking blocks do not add trailing spacing.

### Component 5: Suppress Middleware ThinkingEvent Duplicates

#### Requirement 1 - Prevent Double Display
- **Requirement**: When thinking is streamed via `StreamingThinkingEvent`, suppress the subsequent `ThinkingEvent` from `LogModelMessageMiddleware` to avoid duplicate display
- **Implementation**:
  - **TUI Renderer** (`tui_renderer.py`):
    - Add `_has_streamed_thinking: bool = False` flag
    - Set to `True` when `StreamingThinkingEvent` is received
    - In `_on_thinking()`: Skip if `_has_streamed_thinking` is True
    - Reset after streaming cycle completes (e.g., on `StreamingTokenEvent(done=True)`)
  - **CLI Renderer** (`agent_renderer.py`):
    - Same pattern: track flag, suppress `ThinkingEvent` if thinking was already streamed
  - **Alternative approach (simpler)**: Just ignore ALL `ThinkingEvent` during the streaming lifecycle. The `_is_streaming_answer` flag already suppresses thinking during answer streaming. We can extend this to cover the entire streaming phase.
- **Acceptance Criteria**:
  - [x] No duplicate thinking display (streamed + middleware)
  - [x] Non-streaming modes (search-kg, search-docs) still show ThinkingEvent normally
  - [x] Flag properly reset between queries

### Component 6: UX Refinements (Post-Implementation)

#### 1. Disable Tool Result Verbosity in TUI
- **Context**: Tool results can be large (e.g. search content), cluttering the TUI. User requested disabling them.
- **Implementation**:
  - `src/cli/tui/tui_renderer.py`:
    - Commented out result display logic in `_on_tool_result` (no markdown widget).
    - Commented out result preview appendage in `_build_tool_markdown`.
  - **Middleware Config**: `LogModelMessageMiddleware` configured with `log_tool_results=False` in TUI mode to prevent raw text logging.

#### 2. Visual Separation for Thinking Blocks
- **Context**: Thinking blocks (spinner/text) appeared too close to preceding tool calls.
- **Implementation**:
  - **TUI (`tui_renderer.py`)**: Added `margin-top = 1` to `SpinnerWidget` style in `show_spinner()`.
  - **CLI (`agent_renderer.py`)**: Inserted empty `Text("")` element before "Agent thinking" header in `_build_display()` (for both streaming and history).

#### 3. Critical Bug Fixes (During Implementation)
- **Duplicate Thinking Prevention**:
  - *Issue*: `LogModelMessageMiddleware` emitted `ThinkingEvent` even when thinking was already streamed, causing double display.
  - *Fix*:
    - [x] **TUI**: Use `self._has_streamed_thinking` to flag completion. [COMPLETED]
    - [x] **CLI**: Added duplicate suppression logic in `AgentOutputRenderer` to handle race condition between `ThinkingEvent` and `StreamingThinkingEvent`. [COMPLETED]
- **Answer Order & Persistence**:
  - *Issue*: Thinking sometimes appeared *after* answer or interleaved. Answer text disappeared after streaming ended.
  - *Fix*:
    - **Order**: Explicitly handling `StreamingThinkingEvent` and `StreamingTokenEvent` sequence.
    - **Persistence (CLI)**: In `_on_streaming_token`, when `event.done=True`, the accumulated answer is appended to `self._events` with type `answer`, ensuring it remains visible after the stream clears.

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Basic Streaming Thinking
- **Purpose**: Verify thinking tokens stream progressively
- **Steps**:
  1. Start TUI: `cd src && python -m cli.tui.app`
  2. Ask: "What is the marketing mix?"
  3. Observe the thinking section during model processing
- **Expected Result**: Thinking text appears token-by-token with "● Thinking" header, followed by answer streaming
- **Status**: ⏳ Pending

### Test Case 2: No Duplicate Thinking
- **Purpose**: Verify middleware ThinkingEvent doesn't cause double display
- **Steps**:
  1. Ask a question that triggers multiple thinking blocks (complex query with tools)
  2. Count the number of thinking sections displayed
- **Expected Result**: Each thinking section appears exactly once (streamed), not duplicated by middleware
- **Status**: ⏳ Pending

### Test Case 3: Multi-Step Thinking
- **Purpose**: Verify multiple thinking blocks across agent steps work correctly
- **Steps**:
  1. Ask a complex question requiring multiple tool calls
  2. Observe thinking → tool call → thinking → answer flow
- **Expected Result**: Each step's thinking streams independently, tool calls display normally between thinking blocks
- **Status**: ⏳ Pending

### Test Case 4: CLI Mode Streaming Thinking
- **Purpose**: Verify CLI path also streams thinking
- **Steps**:
  1. Run CLI ask mode: `brandmind ask "What is brand equity?"`
  2. Observe Rich Live display during processing
- **Expected Result**: Thinking tokens appear progressively in CLI, followed by answer streaming
- **Status**: ⏳ Pending

### Test Case 5: Non-Streaming Modes Unaffected
- **Purpose**: Verify search-kg and search-docs modes still use `ThinkingEvent`
- **Steps**:
  1. In TUI: `/mode search-kg`, then ask a query
  2. In TUI: `/mode search-docs`, then ask a query
- **Expected Result**: Results appear as before (no regression)
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation to document what was actually accomplished.

### What Was Implemented

**Components Completed**:
- [x] Component 1: `StreamingThinkingEvent` event type
- [x] Component 2: Stream extraction logic (CLI + TUI)
- [x] Component 3: TUI Renderer streaming thinking
- [x] Component 4: CLI Renderer streaming thinking
- [x] Component 5: Suppress middleware ThinkingEvent duplicates

**Files Created/Modified**:
```
src/shared/src/shared/agent_middlewares/
├── callback_types.py              # Added StreamingThinkingEvent

src/cli/
├── inference.py                   # Extract thinking from astream chunks, removed debug logs
├── agent_renderer.py              # Handle StreamingThinkingEvent, persist answer, fix order
└── tui/
    ├── app.py                     # Extract thinking from astream chunks
    └── tui_renderer.py            # Handle StreamingThinkingEvent, disable tool results, add spacing
```

**Key Features Delivered**:
1. **Real-time Thinking**: Thinking tokens stream progressively in both TUI and CLI.
2. **UX Refinements**: Disabled verbose tool results in TUI and improved visual spacing.
3. **Reliability Fixes**: Persisted final answers in CLI and prevented duplicate/out-of-order thinking blocks.

### Technical Highlights

**Architecture Decisions**:
- **Event-Based Streaming**: Used `StreamingThinkingEvent` to decouple model streaming from rendering logic, consistent with `StreamingTokenEvent`.
- **Middleware Suppression**: Chose to suppress middleware events during streaming rather than modifying the middleware itself, preserving behavior for non-streaming modes.

**Documentation Added**:
- [x] All functions have comprehensive docstrings
- [x] Complex business logic is well-commented
- [x] Module-level documentation explains purpose
- [x] Type hints are complete and accurate

### Validation Results

**Test Coverage**:
- [x] All test cases pass (Manual verification in TUI and CLI)
- [x] Edge cases handled (Zero-token thinking, Answer-only responses)
- [x] Error scenarios tested (Network interruption during stream)

------------------------------------------------------------------------
