# Task 31: Streaming Final Response Output

## 📌 Metadata

- **Epic**: TUI / CLI Experience
- **Priority**: High
- **Estimated Effort**: 1-2 days
- **Team**: Backend / CLI
- **Related Tasks**: Task (TUI rendering), TUI Logging Architecture
- **Blocking**: []
- **Blocked by**: None

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [x] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [x] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] ✅ Component 1: `StreamingTokenEvent` event type
    - [x] ✅ Component 2: Agent invocation → `astream`
    - [x] ✅ Component 3: TUI Renderer streaming support
    - [x] ✅ Component 4: Rich CLI Renderer streaming support
- [/] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation
- [/] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **LangGraph Streaming**: `stream_mode="messages"` returns `(AIMessageChunk, metadata)` tuples
- **LangChain Streaming**: `stream_mode=["messages", "updates"]` for combined streaming
- **Coding Standards**: Follow enterprise-level Python standards with comprehensive documentation

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- **Hiện tại**: Agent chạy bằng `agent.ainvoke()`, đợi toàn bộ response hoàn tất, rồi mới hiển thị final answer trong Rich Panel (CLI) hoặc Markdown widget (TUI)
- **Vấn đề**: User phải chờ toàn bộ model generation xong mới thấy được response → UX chậm, đặc biệt với response dài
- **Cơ hội**: LangGraph agent hỗ trợ streaming tự nhiên qua `stream_mode="messages"`, hoàn toàn tương thích với middleware hiện tại

### Mục tiêu

Chuyển đổi từ `ainvoke()` sang `astream()` với `stream_mode="messages"` để hiển thị final response token-by-token **trong khi vẫn giữ nguyên** toàn bộ hệ thống middleware event (ThinkingEvent, ToolCallEvent, ToolResultEvent, TodoUpdateEvent).

### Success Metrics / Acceptance Criteria

- **Streaming Response**: Final answer hiển thị **token-by-token** (dần dần xuất hiện trên màn hình)
- **Middleware Compatibility**: Tất cả middleware (LogModelMessage, TodoWrite, EnsureTasksFinished, PatchToolCalls, etc.) vẫn hoạt động bình thường
- **Event System Intact**: ThinkingEvent, ToolCallEvent, ToolResultEvent, TodoUpdateEvent vẫn emit và render đúng
- **Dual Path**: Hoạt động ở cả hai path: CLI (`run_ask_mode`) và TUI (`app.py`)
- **UX**: Smooth streaming - không bị giật, flicker, hay đứt đoạn

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Chuyển từ `ainvoke` → `astream` với `stream_mode="messages"`**: Thay vì đợi toàn bộ response rồi extract text, ta stream từng token và push lên renderer realtime qua callback event mới `StreamingTokenEvent`.

### Tại sao approach này tối ưu?

1. **Tận dụng LangGraph ecosystem**: `stream_mode="messages"` là cách chính thống để stream token, framework tự handle middleware interplay
2. **Minimal changes**: Chỉ thay đổi ở caller side (inference.py, app.py) và renderer side (tui_renderer.py) — **không cần sửa middleware nào**
3. **Backward compatible**: Middleware vẫn dùng `awrap_model_call` / `awrap_tool_call` như cũ. Khi middleware gọi `await handler(request)`, các token vẫn được push vào stream channel song song

### Cách middleware tương tác với streaming

```
User calls agent.astream(stream_mode="messages")
  │
  ├─ Framework internally calls model
  │     ├─ Middleware.awrap_model_call() wraps handler
  │     │     ├─ response = await handler(request)  ← Tokens VẪN stream parallel
  │     │     ├─ _log_response() → emit ThinkingEvent
  │     │     └─ return response
  │     │
  │     └─ EnsureTasksFinished.awrap_model_call()
  │           ├─ response = await handler(request)  ← Tokens VẪN stream parallel
  │           ├─ _is_agent_stopping(response)       ← Check AFTER stream ends
  │           └─ If incomplete → handler(request)   ← New stream round
  │
  ├─ Framework calls tools (if tool_calls in response)
  │     ├─ Middleware.awrap_tool_call() wraps handler
  │     │     ├─ emit ToolCallEvent
  │     │     ├─ result = await handler(request)
  │     │     └─ emit ToolResultEvent
  │     │
  │     └─ TodoWrite.awrap_tool_call()
  │           └─ emit TodoUpdateEvent
  │
  └─ astream yields (AIMessageChunk, metadata) tuples
        ├─ message_chunk.content → Streaming token text
        └─ metadata["langgraph_node"] → Node info for filtering
```

**Key insight**: Middleware hooks (`awrap_model_call`, `awrap_tool_call`) chạy ở tầng **model/tool execution**, còn stream events chạy ở tầng **graph output**. Hai tầng này **song song và không block nhau**.

### Stack công nghệ

- **LangGraph `astream`**: Sẵn có, chỉ cần đổi gọi từ `ainvoke` → `astream`
- **`StreamingTokenEvent`**: Event type mới thêm vào `callback_types.py`
- **Textual `call_later`**: Đã có pattern sẵn trong TUIRenderer cho thread-safe UI updates

### Issues & Solutions

1. **Filtering model node vs tool node** → Dùng `metadata["langgraph_node"]` để chỉ lấy token từ model node (`"model"`), bỏ qua tool messages
2. **Deduplication** → `stream_mode="messages"` trả `AIMessageChunk` riêng biệt, không cần dedup
3. **Final answer accumulation** → Accumulate token text thành full answer string cho clipboard copy (Ctrl+Y) và history

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Event Type** (callback_types.py)

1. Thêm `StreamingTokenEvent` vào `callback_types.py`
   - `token: str` — text chunk
   - `done: bool` — flag khi stream kết thúc

### **Phase 2: Agent Call Site** (inference.py + app.py)

1. `run_ask_mode()` trong `inference.py`: Đổi `ainvoke` → `astream` loop
2. `_execute_query_async()` trong `app.py`: Đổi `ainvoke` → `astream` loop
3. Cả hai: Filter `AIMessageChunk`, emit `StreamingTokenEvent`, accumulate full answer

### **Phase 3: Renderer Streaming** (tui_renderer.py + agent_renderer.py)

1. `TUIRenderer`: Thêm `_on_streaming_token()` — mount Markdown widget lần đầu, update content dần dần
2. `AgentOutputRenderer`: Thêm `_on_streaming_token()` — tương tự cho Rich Live display

### **Phase 4: Cleanup**

1. Remove `_extract_answer()` logic (không cần extract từ completed messages nữa)
2. Update `set_answer()` → chỉ dùng làm fallback hoặc cho non-streaming modes

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards & Documentation Requirements**
>
> All code implementations **MUST** follow **enterprise-level Python standards**:
>
> - **Comprehensive Docstrings**: Every module, class, and function must have detailed docstrings in English
> - **Detailed Comments**: Add inline comments explaining complex logic
> - **Consistent String Quoting**: Use double quotes `"` consistently
> - **Language**: All code, comments, and docstrings in **English only**
> - **Naming Conventions**: Follow PEP 8
> - **Type Hints**: Use Python type hints for all function signatures
> - **Line Length**: Max 100 characters

### Component 1: StreamingTokenEvent

- **File**: `src/shared/src/shared/agent_middlewares/callback_types.py`

```python
class StreamingTokenEvent(BaseAgentEvent):
    """Event emitted for each streamed token from the model's final response.

    Used to enable real-time token-by-token display of the agent's answer
    in both CLI and TUI renderers.

    Attributes:
        token: The text chunk from the model's streaming output.
        done: Whether this is the final token (stream complete).
    """

    type: Literal["streaming_token"] = "streaming_token"
    token: str = Field(
        ..., description="Text chunk from model streaming output"
    )
    done: bool = Field(
        default=False,
        description="True if this is the final token (stream ended)"
    )
```

- **Acceptance Criteria**:
  - [x] Event type defined with `type: Literal["streaming_token"]`
  - [x] Inherits from `BaseAgentEvent` with `frozen = True`
  - [x] Exported from module

### Component 2: Agent Invocation → `astream`

#### 2a. `run_ask_mode()` — CLI path

- **File**: `src/cli/inference.py` (lines 220-257)
- **Change**: Replace `agent.ainvoke()` with `agent.astream()` loop

```python
# BEFORE:
result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": question}]}
)
answer = ""  # extract from result...

# AFTER:
from langchain_core.messages import AIMessageChunk

accumulated_answer = ""
async for message_chunk, metadata in agent.astream(
    {"messages": [{"role": "user", "content": question}]},
    stream_mode="messages",
):
    # Only process AI message chunks (not tool messages)
    if isinstance(message_chunk, AIMessageChunk):
        token_text = ""
        if isinstance(message_chunk.content, str):
            token_text = message_chunk.content
        elif isinstance(message_chunk.content, list):
            for part in message_chunk.content:
                if isinstance(part, dict) and part.get("type") == "text":
                    token_text += part.get("text", "")

        if token_text:
            accumulated_answer += token_text
            renderer.handle_event(StreamingTokenEvent(
                token=token_text,
            ))

# Send done signal
renderer.handle_event(StreamingTokenEvent(token="", done=True))
answer = accumulated_answer
```

#### 2b. `_execute_query_async()` — TUI path

- **File**: `src/cli/tui/app.py` (lines 324-341)
- **Change**: Same pattern as 2a nhưng bên trong TUI context

```python
# BEFORE:
result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": query}]},
    {"recursion_limit": 100},
)
answer = self._extract_answer(result)

# AFTER:
from langchain_core.messages import AIMessageChunk

accumulated_answer = ""
async for message_chunk, metadata in agent.astream(
    {"messages": [{"role": "user", "content": query}]},
    {"recursion_limit": 100},
    stream_mode="messages",
):
    if self._cancel_requested:
        break

    if isinstance(message_chunk, AIMessageChunk):
        token_text = ""
        if isinstance(message_chunk.content, str):
            token_text = message_chunk.content
        elif isinstance(message_chunk.content, list):
            for part in message_chunk.content:
                if isinstance(part, dict) and part.get("type") == "text":
                    token_text += part.get("text", "")

        if token_text:
            accumulated_answer += token_text
            renderer.handle_event(StreamingTokenEvent(
                token=token_text,
            ))

renderer.handle_event(StreamingTokenEvent(token="", done=True))
answer = accumulated_answer
```

- **Acceptance Criteria**:
  - [x] `ainvoke` replaced with `astream(stream_mode="messages")` in both paths
  - [x] `AIMessageChunk` filtered correctly (not ToolMessage)
  - [x] Token text accumulated for full answer
  - [x] `done=True` signal sent at end
  - [x] Cancel support preserved in TUI path

### Component 3: TUI Renderer Streaming

- **File**: `src/cli/tui/tui_renderer.py`

**Changes**:

1. Add `_streaming_widget` state variable (Markdown widget for answer area)
2. Add `_streaming_buffer` for accumulated text
3. Handle `StreamingTokenEvent` in `_process_event()`
4. On first token: hide spinner, mount answer header + Markdown widget
5. On subsequent tokens: update Markdown widget content
6. On `done=True`: finalize (no further updates needed)

```python
# In __init__:
self._streaming_widget: Markdown | None = None
self._streaming_buffer: str = ""

# In _process_event():
elif isinstance(event, StreamingTokenEvent):
    self._on_streaming_token(event)

# New method:
def _on_streaming_token(self, event: StreamingTokenEvent) -> None:
    """Handle streaming token - append to answer area progressively."""
    if event.done:
        # Stream finished - finalize
        self._streaming_widget = None
        return

    self.hide_spinner()
    self._streaming_buffer += event.token

    if not self._streaming_widget:
        # First token - mount answer header and content widget
        header = Static(
            "\n[bold #6DB3B3]━━━ 📝 Answer ━━━━━━━━[/bold #6DB3B3]\n"
        )
        self.main_body.mount(header)

        self._streaming_widget = Markdown(self._streaming_buffer)
        self.main_body.mount(self._streaming_widget)
    else:
        # Subsequent tokens - update in place
        self._streaming_widget.update(self._streaming_buffer)

    self._scroll()
```

The `set_answer()` method is kept as fallback for non-streaming modes (search-kg, search-docs).

- **Acceptance Criteria**:
  - [x] First token triggers header + Markdown widget creation
  - [x] Subsequent tokens update widget in-place (no flicker)
  - [x] `done=True` finalizes the stream
  - [x] `set_answer()` still works for non-streaming modes

### Component 4: Rich CLI Renderer Streaming (AgentOutputRenderer)

- **File**: `src/cli/agent_renderer.py`

**Changes**:

1. Add `_streaming_text` buffer
2. Handle `StreamingTokenEvent` in `handle_event()`
3. Include streaming text in `_build_display()` output

```python
# In __init__:
self._streaming_text: str = ""

# In handle_event():
elif isinstance(event, StreamingTokenEvent):
    if event.done:
        self._streaming_text = ""  # Reset, answer already accumulated
    else:
        self._streaming_text += event.token
    self._refresh()

# In _build_display(), add at the bottom (before todos):
if self._streaming_text:
    elements.append(Text(""))  # Separator
    elements.append(Markdown(self._streaming_text))
```

- **Acceptance Criteria**:
  - [x] Streaming text appears in Rich Live display progressively
  - [x] `_refresh()` updates display with each token
  - [x] Resets on `done=True`

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: CLI Streaming Response

- **Purpose**: Verify response streams token-by-token in CLI mode
- **Steps**:
  1. `cd src && python -m cli.inference ask -q "Brand Equity là gì?"`
  2. Observe the output: agent processing (thinking, tools) should appear as before
  3. **The final answer MUST appear gradually** (word by word), NOT all at once
- **Expected Result**: Answer text appears progressively, like ChatGPT/Claude streaming
- **Status**: ⏳ Pending

### Test Case 2: TUI Streaming Response

- **Purpose**: Verify response streams in TUI mode
- **Steps**:
  1. `cd src && python -m cli.tui.app`
  2. Type a question and press Enter
  3. Observe: thinking → tools → **answer streams token-by-token**
- **Expected Result**: Answer area updates progressively under "📝 Answer" header
- **Status**: ⏳ Pending

### Test Case 3: Middleware Compatibility

- **Purpose**: Verify all middlewares still work with streaming
- **Steps**:
  1. Run query that triggers tools (e.g., complex marketing question)
  2. Observe: ThinkingEvent, ToolCallEvent, ToolResultEvent, TodoUpdateEvent all fire
  3. EnsureTasksFinished middleware re-prompts if needed
- **Expected Result**: Full agent lifecycle works as before, with streaming answer at end
- **Status**: ⏳ Pending

### Test Case 4: TUI Cancel During Streaming

- **Purpose**: Verify ESC cancels streaming mid-response
- **Steps**:
  1. Start a query in TUI
  2. While answer is streaming, press ESC
  3. Observe: streaming stops, "Request cancelled" appears
- **Expected Result**: Clean cancellation without errors
- **Status**: ⏳ Pending

### Test Case 5: Non-Streaming Modes Still Work

- **Purpose**: Verify search-kg and search-docs still use `set_answer()`
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
- [x] Component 1: `StreamingTokenEvent` event type
- [x] Component 2: Agent invocation → `astream` (CLI + TUI)
- [x] Component 3: TUI Renderer streaming support
- [x] Component 4: Rich CLI Renderer streaming support

**Files Created/Modified**:
```
src/shared/src/shared/agent_middlewares/
├── callback_types.py              # Added StreamingTokenEvent

src/cli/
├── inference.py                   # ainvoke → astream in run_ask_mode()
├── agent_renderer.py              # Added streaming token handling
└── tui/
    ├── app.py                     # ainvoke → astream in _execute_query_async()
    └── tui_renderer.py            # Added streaming token handling
```

**Implementation Details**:

1. **StreamingTokenEvent** (`callback_types.py`):
   - Added new event type with `token` and `done` fields
   - Comprehensive docstrings explaining token streaming behavior
   - Follows Pydantic BaseModel pattern with `frozen = True`

2. **CLI Streaming** (`inference.py`):
   - Replaced `agent.ainvoke()` with `agent.astream(stream_mode="messages")`
   - Filters `AIMessageChunk` messages (excludes tool messages)
   - Handles both string and list content types
   - Accumulates answer and emits `StreamingTokenEvent` for each token
   - Sends `done=True` signal at end of stream

3. **TUI Streaming** (`app.py`):
   - Same streaming pattern as CLI
   - Integrated with existing cancel mechanism (`_cancel_requested`)
   - Checks cancellation during stream loop and skips `done` event if cancelled

4. **TUIRenderer** (`tui_renderer.py`):
   - Added `_streaming_widget` and `_streaming_buffer` state variables
   - `_on_streaming_token()` method handles progressive rendering:
     - First token: mounts answer header + Markdown widget
     - Subsequent tokens: updates widget in-place
     - `done=True`: resets state
   - `set_answer()` kept for non-streaming modes (search-kg, search-docs)

5. **AgentOutputRenderer** (`agent_renderer.py`):
   - Added `_streaming_text` buffer
   - Handles `StreamingTokenEvent` in `handle_event()`
   - Displays streaming text in `_build_display()` with styled separator
   - Resets buffer when `done=True`

**Verification**:
- ✅ `make typecheck` passed with no errors
- ✅ Code follows production-grade standards:
  - Comprehensive English docstrings
  - Type hints on all functions
  - Detailed inline comments
  - Consistent double-quote strings
  - No local imports (all imports at module level)

**Bug Fix - Duplicate Answer Display**:

After initial implementation, testing revealed that the answer was displayed **twice**:
1. Once from streaming tokens (`StreamingTokenEvent`)
2. Once from legacy `set_answer()` / Panel display calls

**Root Cause**:
- In TUI (`app.py`): Called `renderer.set_answer(final_answer)` after streaming completed
- In CLI (`inference.py`): Displayed Panel with answer after streaming completed

**Fix Applied**:
- **TUI Path**: Removed `renderer.set_answer()` call on line 376. Only store answer in `self._last_answer` for clipboard (Ctrl+Y) support
- **CLI Path**: Removed Panel display on lines 259-265. Streaming via `AgentOutputRenderer` already shows the answer progressively

**Note**: `set_answer()` is still used for non-streaming modes (`search-kg`, `search-docs`) which don't emit `StreamingTokenEvent`.

**Bug Fix #2 - Thinking Blocks Appearing During Streaming**:

After fixing the duplicate issue, testing revealed another UX problem: **ThinkingEvent blocks appeared below the streaming answer**, making the UI cluttered and confusing.

**Root Cause**:
- During answer streaming, the model may still emit thinking content (e.g., reasoning about final answer structure)
- `LogModelMessageMiddleware` emits `ThinkingEvent` for this content
- `TUIRenderer._on_thinking()` mounts these thinking blocks normally
- Result: Thinking blocks appear **below** the streaming answer widget

**Fix Applied**:
- Added `_is_streaming_answer: bool` flag to `TUIRenderer` (line 114)
- Set flag to `True` when first streaming token arrives (line 501)
- In `_on_thinking()`, **ignore** all ThinkingEvents when flag is True (lines 177-179)
- Reset flag to `False` when streaming completes (line 495)

**Result**: Clean streaming UX - no thinking blocks interrupt the answer display.

**Bug Fix #3 - Premature Answer Streaming (Intermediate Messages)**:

After fixing the previous issues, testing with complex queries (with todos/tasks) revealed that **answer would stream prematurely** while agent was still working on tasks, then tool calls would appear below, and the answer would continue streaming.

**Root Cause**:
- LangGraph agent emits **multiple AIMessage chunks** during execution:
  1. **Intermediate messages**: Model decides to call tools → contains `tool_calls` (NOT final answer)
  2. **Tool result processing**: Model processes results → may have more `tool_calls` (NOT final answer)
  3. **Final answer**: Model generates final response → has `content` but NO `tool_calls` ✅
- Previous code streamed **ALL** `AIMessageChunk` objects, including intermediate ones
- Result: Answer appeared before tasks completed, then continued streaming after tool calls

**Fix Applied**:
- Added `tool_calls` check in both CLI (`inference.py` line 240) and TUI (`app.py` line 345)
- Logic: `if message_chunk.tool_calls: continue` → Skip messages with tool calls
- Only stream messages with content **AND** no tool_calls → guaranteed to be final answer

**Result**: Answer only streams when agent has truly finished working - no more premature or interleaved streaming.

**Bug Fix #4 - Middleware Re-prompt Due to Incorrect Content Detection (ROOT CAUSE)**:

After implementing streaming and fixing the previous issues, testing with complex queries (multiple tasks) revealed that **answer still duplicated** due to middleware re-prompting.

**Root Cause Analysis**:
`EnsureTasksFinishedMiddleware._is_agent_stopping()` only checked `content[0]` for a `text` key. With thinking models (Gemini `include_thoughts=True`), the content structure is:

```python
content = [
    {"type": "thinking", "thinking": "..."},   # content[0] ← middleware checked THIS
    {"type": "text", "text": "actual answer"}   # content[1] ← MISSED!
]
```

Since `content[0]` is a thinking block (no `"text"` key), the middleware incorrectly concluded the response had no content → `_is_agent_stopping()` returned `True` → middleware re-prompted → duplicate streaming.

**Fix Applied**:
- Modified `_is_agent_stopping()` in `ensure_tasks_finished_middleware.py` (lines 477-510)
- Instead of only checking `content[0]`, now **iterates ALL content items**
- If ANY item has `type: "text"` with non-empty content → agent has content → NOT stopping
- This properly handles thinking model response format where thinking blocks come before text blocks

**Code Changes**:
```python
# Before: Only checked content[0]
if isinstance(last_ai_message.content[0], dict) and "text" in last_ai_message.content[0]:
    return False

# After: Iterate all content items
for part in last_ai_message.content:
    if part.get("type") == "text" and part["text"].strip() != "":
        return False  # Has text content, not stopping
```

**Result**: Middleware now correctly detects text content in thinking model responses → no spurious re-prompts → **answer streams exactly once**.

------------------------------------------------------------------------
