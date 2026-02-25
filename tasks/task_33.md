# Task 33: Improve Todo Plan Adherence & Stop Check Duplicate Prevention

## 📌 Metadata

- **Epic**: Agent Reliability & UX
- **Priority**: High
- **Estimated Effort**: 1 week
- **Team**: Backend
- **Related Tasks**: Task 31 (Streaming), Task 32 (Thinking Streaming)
- **Blocking**: []
- **Blocked by**: @suneox

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [x] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [x] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] ✅ [Component 1: Stop Check Prompt Rework](#component-1-stop-check-prompt-rework) - Smarter re-prompt
    - [x] ✅ [Component 2: Todo System Prompt Refinement](#component-2-todo-system-prompt-refinement) - Plan adherence
    - [x] ✅ [Component 3: EnsureTasksFinished Middleware Logic Fix](#component-3-ensuretasksfinished-middleware-logic-fix) - Context-aware re-prompt
    - [x] ✅ [Component 4: TodoWrite Reminder Enhancement](#component-4-todowrite-reminder-enhancement) - Better state reminders
- [ ] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation
- [ ] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards with comprehensive documentation
- **LangChain Middleware Order**: `wrap_model_call` hooks nest like function calls — first middleware wraps outermost, last middleware is closest to model. ([Docs](https://docs.langchain.com/oss/python/langchain/middleware/custom))
- **Current middleware order in `inference.py`**: `[context_edit, msg_summary, todo, patch, log_message, retry, stop_check]`

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

Hai vấn đề chính đang xảy ra khi agent chạy ở mode "ask" trong TUI:

**Vấn đề 1: Agent không bám theo todo plan đã lập**
- Agent lập xong danh sách task (vd: 4 bước) nhưng khi thực thi, nó có thể:
  - **Case A**: Dừng giữa chừng mà không hoàn thành hết các task trong plan
  - **Case B**: Làm xong hết các bước thực chất nhưng KHÔNG gọi `write_todos` để tick các task đã hoàn thành → todos state vẫn ở `pending`/`in_progress` → stop check middleware can thiệp sai

**Vấn đề 2: Duplicate final answer khi stop check can thiệp**
- Agent đặt task cuối cùng là "Tổng hợp câu trả lời" (synthesize final answer)
- Agent hoàn thành bước đó (generate answer) nhưng chưa tick `completed` cho task cuối
- Agent muốn STOP → `EnsureTasksFinishedMiddleware` can thiệp: "Mày còn task chưa xong!"
- Agent **generate lại toàn bộ final answer** thay vì chỉ gọi `write_todos` để tick task → **Duplicate answer**
- Nguyên nhân gốc: re-prompt của stop check **không mang theo context rằng agent đã generate answer rồi**, và prompt cũng không hướng dẫn agent là nếu đã xong rồi thì chỉ cần tick task thôi

### Root Cause Analysis

#### 1. Middleware Execution Order & Interaction

Thứ tự middleware hiện tại trong `inference.py`:
```python
middleware=[
    context_edit_middleware,    # Outermost wrap
    msg_summary_middleware,
    todo_middleware,            # ← Injects system prompt + reminder
    patch_middleware,
    log_message_middleware,
    retry_middleware,
    stop_check_middleware,      # ← Innermost wrap (closest to model)
]
```

Theo LangChain docs, `wrap_model_call` nesting nghĩa là:
```
context_edit(msg_summary(todo(patch(log_message(retry(stop_check(MODEL)))))))
```

→ **`stop_check` wraps gần model nhất** — khi model trả về response, `stop_check` check TRƯỚC rồi mới đến `log_message`, `todo`, v.v.

→ **Vấn đề**: Khi `stop_check` phát hiện agent muốn dừng và inject re-prompt rồi gọi `handler(request)` lại, LLM response mới này cũng được `stop_check` xử lý tiếp — nhưng lúc đó `todo_middleware` ở outer layer đã inject system prompt 1 lần rồi. Tuy nhiên, response mới nhất (chứa final answer agent vừa sinh ra) **KHÔNG nằm trong `request.messages`** vì `stop_check` chỉ append `SystemMessage` re-prompt vào messages, còn response cũ (chứa answer) bị discard.

#### 2. Prompt Gaps

- **`STOP_CHECK_CRITICAL_REMINDER`**: Chỉ nói "hãy tiếp tục làm" nhưng KHÔNG nói "nếu bạn đã làm xong rồi nhưng quên tick, hãy gọi `write_todos` để tick thôi, KHÔNG LÀM LẠI"
- **`WRITE_TODOS_SYSTEM_PROMPT`**: Có quy tắc "IMMEDIATE COMPLETION - mark as completed as soon as done" nhưng chưa đủ mạnh để prevent agent quên, và chưa đề cập rằng task cuối cùng (loại "tổng hợp/trả lời") nên được tick TRƯỚC khi generate answer hoặc KHÔNG nên nằm trong todo list
- **`TODO_REMINDER_TEMPLATE`**: Reminder sau mỗi `write_todos` chỉ nhắc "continue working on current task" mà không nhắc lại plan tổng thể

#### 3. Missing Previous Response in Re-prompt Context

Khi `stop_check` detect agent muốn dừng:
```python
# Line 326-331 of ensure_tasks_finished_middleware.py
for attempt in range(self.max_reminders):
    re_prompt = self._generate_re_prompt(incomplete_tasks)
    request.messages.append(SystemMessage(content=re_prompt))
    current_response = await handler(request)  # ← Previous response LOST
```

`current_response` (chứa answer agent vừa generate) được gán lại nhưng response CŨ **không được append vào `request.messages`**. Vì vậy khi model được gọi lại, nó KHÔNG biết nó đã trả lời rồi → generate lại.

### Mục tiêu

1. Agent bám sát todo plan đã lập: mark tasks `completed` ngay khi xong, không bỏ sót
2. Khi stop check can thiệp, agent KHÔNG duplicate công việc đã làm — chỉ tick task hoặc làm task còn thiếu
3. Giữ sự tự do cho agent trong việc lên plan — chỉ hướng dẫn chặt hơn về task management discipline
4. Prompts không conflict lẫn nhau giữa `TodoWriteMiddleware` và `EnsureTasksFinishedMiddleware`

### Success Metrics / Acceptance Criteria

- **Plan Adherence**: Agent tick `completed` cho mỗi task ngay sau khi hoàn thành (không bỏ sót > 1 task liên tiếp)
- **No Duplicate Answer**: Khi stop check can thiệp, agent chỉ gọi `write_todos` để update status, KHÔNG generate lại nội dung đã có
- **Task Quality**: Agent vẫn tự do lên plan phù hợp, không bị ép theo template cố định
- **No Regression**: Streaming (token + thinking), tool calls, TUI rendering hoạt động bình thường

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Multi-layered approach**: Kết hợp cải thiện prompt + logic middleware để agent vừa được hướng dẫn tốt hơn về task management discipline, vừa được cung cấp context đầy đủ khi bị re-prompt.

### Issues & Solutions

1. **Agent quên tick task sau khi hoàn thành** →
   - Cải thiện `WRITE_TODOS_SYSTEM_PROMPT` và `WRITE_TODOS_TOOL_DESCRIPTION` thêm quy tắc rõ ràng hơn: **"Sau khi sử dụng tool hoặc hoàn thành 1 phần công việc, NGAY LẬP TỨC gọi `write_todos` để cập nhật — mark `completed` cho task vừa xong, mark `in_progress` cho task kế tiếp"**
   - Thêm quy tắc: **"Task cuối cùng trong plan KHÔNG NÊN là việc generate/synthesize final answer cho user vì đó là hành vi tự nhiên của agent khi hoàn thành tất cả research tasks — nó sẽ xảy ra tự động sau khi tất cả tasks đã completed"**

2. **Stop check re-prompt gây duplicate answer** →
   - Sửa `EnsureTasksFinishedMiddleware`: khi detect agent stopping, **append response cũ (chứa answer) vào `request.messages` dưới dạng AIMessage** TRƯỚC khi append re-prompt SystemMessage → Model sẽ thấy nó đã trả lời rồi
   - Sửa `STOP_CHECK_CRITICAL_REMINDER`: Thêm câu **"If you have already completed work but forgot to update your todo list, call `write_todos` to mark tasks as `completed` — DO NOT redo any work you have already finished"**

3. **TodoWrite reminder không nhắc plan tổng thể** →
   - Cải thiện `TODO_REMINDER_TEMPLATE` nhắc agent check lại plan: **"Review your full plan above. Mark any completed tasks immediately. Then proceed to the next pending task."**

4. **Conflict giữa `TODO_REMINDER_FINAL_CONFIRMATION` (todo_system_prompt) và `STOP_CHECK_FINAL_CONFIRMATION` (stop_check_prompts)** →
   - Hai prompt này gần như giống nhau, gây potential confusion khi cả hai inject vào cùng lúc
   - Giải quyết: Phân vai rõ — `TODO_REMINDER_FINAL_CONFIRMATION` chỉ nhắc "all done, give final summary" khi được gọi từ `write_todos` tool response. `STOP_CHECK_FINAL_CONFIRMATION` chỉ activate khi agent stop mà todos đã completed nhưng chưa output gì cho user

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Prompt Improvements (Lowest Risk)**
1. **Refine `STOP_CHECK_CRITICAL_REMINDER`** (`stop_check_prompts.py`)
   - Add instruction to NOT redo completed work
   - Add instruction to just call `write_todos` if work was done but not tracked
   - *Decision Point: Test with same question to verify reduced duplication*

2. **Refine `WRITE_TODOS_SYSTEM_PROMPT` & `WRITE_TODOS_TOOL_DESCRIPTION`** (`todo_system_prompt.py`)
   - Strengthen "mark completed immediately" rule
   - Add rule about NOT including "synthesize/write final answer" as last task
   - Add rule about calling `write_todos` after EVERY significant action (tool call completion, research step done)

3. **Refine `TODO_REMINDER_TEMPLATE`** (`todo_system_prompt.py`)
   - Add "review full plan and mark completed tasks" instruction
   - Remove redundancy with `STOP_CHECK_CRITICAL_REMINDER`

4. **Resolve overlap between `TODO_REMINDER_FINAL_CONFIRMATION` and `STOP_CHECK_FINAL_CONFIRMATION`**
   - Clarify distinct roles for each prompt

### **Phase 2: Middleware Logic Fix (Medium Risk)**
1. **Fix re-prompt context in `EnsureTasksFinishedMiddleware`**
   - When detecting premature stop, extract text/thinking content from model's response
   - Append that content as an AIMessage to `request.messages` before adding re-prompt
   - This ensures model sees its own previous output and won't regenerate it

2. **Optional: Add `write_todos` call count tracking**
   - Track how many times `write_todos` was called in the session
   - If agent has > 3 pending tasks and 0 `write_todos` calls after initial plan, inject a mid-session reminder

### **Phase 3: Testing & Validation**
1. Run `brandmind ask -q "cách để cải thiện brand equity nhất là khi re-branding?"` multiple times
2. Verify: no duplicate answers, tasks get completed, plan adherence
3. Test edge cases: simple questions (should skip todo), complex multi-tool questions

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

### Component 1: Stop Check Prompt Rework

#### Requirement 1 - Smarter `STOP_CHECK_CRITICAL_REMINDER`
- **Requirement**: Re-prompt phải hướng dẫn model chính xác: phân biệt "quên tick task" vs "cần làm thêm công việc thật sự"
- **Implementation**:
  - `src/prompts/task_management/stop_check_prompts.py`
  - Sửa `STOP_CHECK_CRITICAL_REMINDER`:
  ```python
  STOP_CHECK_CRITICAL_REMINDER = """
  <system_critical_reminder>
  You attempted to stop working, but your todo list is NOT finished.

  Current Status:
  - Tasks in progress: {{in_progress_count}}
  - Tasks pending: {{pending_count}}

  {{next_task_instruction}}

  IMPORTANT — Read carefully before acting:
  1. CHECK if you have ALREADY completed any of these tasks but forgot to
     call '{{write_todos_function_name}}' to update their status.
     → If YES: Call '{{write_todos_function_name}}' NOW to mark them
       as 'completed'. DO NOT redo work you have already finished.
  2. If there are tasks you truly have NOT started yet → work on them.
  3. If you just finished a task → call '{{write_todos_function_name}}'
     to mark it 'completed' and set the next task 'in_progress'.

  You MUST continue until ALL tasks are marked 'completed'.
  This is a mandatory instruction, not optional.
  </system_critical_reminder>
  """
  ```

#### Requirement 2 - Refine `STOP_CHECK_FINAL_CONFIRMATION`
- **Requirement**: Khi tất cả tasks đã completed, prompt phải rõ ràng hơn — chỉ yêu cầu final summary nếu agent CHƯA output gì
- **Implementation**:
  - Giữ nguyên hoặc simplify — prompt này chỉ fire khi `len(todos) > 0` và tất cả đã `completed` nhưng agent stop mà không có text output
  - Nếu agent đã output final answer rồi thì stop check middleware sẽ KHÔNG can thiệp (vì `_is_agent_stopping` return `False` khi có text content)
- **Acceptance Criteria**:
  - [ ] `STOP_CHECK_CRITICAL_REMINDER` clearly distinguishes "forgot to tick" vs "need more work"
  - [ ] No conflicting instructions with Todo reminders

### Component 2: Todo System Prompt Refinement

#### Requirement 1 - Strengthen Task Completion Discipline
- **Requirement**: Prompt phải enforce quy tắc gọi `write_todos` ngay sau mỗi bước hoàn thành
- **Implementation**:
  - `src/prompts/task_management/todo_system_prompt.py`
  - Thêm quy tắc vào `WRITE_TODOS_SYSTEM_PROMPT`:
  ```
  4. **CALL AFTER EVERY STEP:** After EACH significant action (tool call
     completed, research done, analysis finished), IMMEDIATELY call
     `{{write_todos_function_name}}` to update task statuses. Do not
     wait until the end to batch multiple status changes.
  5. **NO "FINAL ANSWER" TASK:** Do NOT create a task for "synthesize
     final answer" or "write final response" or similar. Providing the
     final answer to the user is your NATURAL behavior after completing
     all research/analysis tasks — it should NOT be a tracked task.
     Your last tracked task should be the last ACTIONABLE step
     (e.g., "Identify specific strategies from Chapter 13").
  ```

#### Requirement 2 - Better Tool Description Guidance
- **Requirement**: Tool description phải nhấn mạnh task plan chỉ nên chứa actionable research/analysis steps
- **Implementation**:
  - `src/prompts/task_management/todo_system_prompt.py`
  - Thêm vào `WRITE_TODOS_TOOL_DESCRIPTION` phần `## Task Planning Best Practices`:
  ```
  ## Task Planning Best Practices
  - Tasks should be ACTIONABLE research or analysis steps
  - Do NOT include tasks that describe your natural output behavior
    (e.g., "write final answer", "synthesize response", "present findings")
  - The final answer will be generated naturally after all tasks complete
  - Example good plan:
    1. "Research brand equity components via Knowledge Graph" ← actionable
    2. "Search document library for rebranding strategies" ← actionable
    3. "Identify specific tactics from Chapter X" ← actionable
  - Example BAD plan:
    1. "Research brand equity" ← actionable ✓
    2. "Search documents" ← actionable ✓
    3. "Synthesize final answer for user" ← NOT actionable, remove ✗
  ```
- **Acceptance Criteria**:
  - [ ] System prompt includes "call after every step" rule
  - [ ] System prompt includes "no final answer task" rule
  - [ ] Tool description includes task planning examples

### Component 3: EnsureTasksFinished Middleware Logic Fix

#### Requirement 1 - Preserve Previous Response in Re-prompt Context
- **Requirement**: Khi stop check phát hiện agent muốn dừng có task chưa xong, phải append response CŨ của agent vào `request.messages` trước khi gọi lại model, để model thấy output nó đã tạo ra
- **Implementation**:
  - `src/shared/src/shared/agent_middlewares/stop_check/ensure_tasks_finished_middleware.py`
  - Sửa logic trong cả `wrap_model_call` và `awrap_model_call`:
  ```python
  # BEFORE (current code):
  for attempt in range(self.max_reminders):
      re_prompt = self._generate_re_prompt(incomplete_tasks)
      request.messages.append(SystemMessage(content=re_prompt))
      current_response = await handler(request)

  # AFTER (fixed code):
  for attempt in range(self.max_reminders):
      # Preserve agent's previous response so model knows what it already did
      previous_ai_content = self._extract_response_content(current_response)
      if previous_ai_content:
          from langchain_core.messages import AIMessage
          request.messages.append(AIMessage(content=previous_ai_content))

      re_prompt = self._generate_re_prompt(incomplete_tasks)
      request.messages.append(SystemMessage(content=re_prompt))
      current_response = await handler(request)
  ```
  - Thêm helper method `_extract_response_content`:
  ```python
  def _extract_response_content(self, response: ModelResponse) -> str:
      """
      Extract text content from model response for context preservation.

      When the stop check middleware needs to re-prompt the model,
      the previous response content must be preserved in the message
      history so the model knows what it already generated and avoids
      duplicating its output.

      Args:
          response: The model response to extract content from

      Returns:
          str: Extracted text content, or empty string if none found
      """
      if not hasattr(response, "result"):
          return ""

      result = response.result
      if not result or len(result) == 0:
          return ""

      last_ai_message = result[-1]
      if not last_ai_message or not hasattr(last_ai_message, "content"):
          return ""

      content = last_ai_message.content
      if isinstance(content, str):
          return content
      elif isinstance(content, list):
          text_parts = []
          for part in content:
              if isinstance(part, dict) and part.get("type") == "text":
                  text_parts.append(part.get("text", ""))
          return "\n".join(text_parts)
      return ""
  ```
- **Acceptance Criteria**:
  - [ ] Previous model response is appended as AIMessage before re-prompt
  - [ ] Model sees its own output and doesn't regenerate it
  - [ ] Works for both sync and async paths
  - [ ] Method handles edge cases (empty response, list content, thinking blocks)

#### Requirement 2 - Same fix for Final Confirmation path
- **Requirement**: Apply same context preservation for the "all tasks completed but no output" path
- **Implementation**: Same pattern as Requirement 1 but in the `else` branch (lines 368-413 / async equivalent)
- **Acceptance Criteria**:
  - [ ] Final confirmation path also preserves previous response

### Component 4: TodoWrite Reminder Enhancement

#### Requirement 1 - State Change Reminder includes Plan Review
- **Requirement**: `TODO_REMINDER_TEMPLATE` phải nhắc agent review toàn bộ plan, không chỉ focus vào current task
- **Implementation**:
  - `src/prompts/task_management/todo_system_prompt.py`
  - Sửa `TODO_REMINDER_TEMPLATE`:
  ```python
  TODO_REMINDER_TEMPLATE = """
  <system-reminder>
  Your todo list has been updated. DO NOT mention this explicitly to the
  user. Here is the current state of your plan:
  {{todos_json}}

  You MUST continue working.
  Your current active task is: **"{{current_task_content}}"**
  (status: {{current_task_status}})

  REMINDER: After completing each task, IMMEDIATELY call `write_todos`
  to mark it as 'completed' and set the next task to 'in_progress'.
  Do not wait — update your task list right away.
  </system-reminder>"""
  ```
- **Acceptance Criteria**:
  - [ ] Reminder explicitly instructs immediate status update
  - [ ] Current task clearly highlighted
  - [ ] No redundancy with stop check prompts

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Plan Adherence — Tasks Get Completed
- **Purpose**: Verify agent marks tasks as `completed` after each step
- **Steps**:
  1. Run: `brandmind ask -q "cách để cải thiện brand equity nhất là khi re-branding?"`
  2. Observe the Todos panel in TUI output
  3. After each tool call (SearchKG, SearchDocs), check if agent calls `write_todos` to update status
- **Expected Result**: After each tool call, agent calls `write_todos` to mark the corresponding task as `completed` and advance the next to `in_progress`. All tasks should show ~~strikethrough~~ (completed) by the end.
- **Status**: ✅ Pass (Gemini 3 Flash + Pro), ⚠️ Flaky (Gemini 2.5 Flash — occasionally still creates synthesize task but self-corrects)

### Test Case 2: No Duplicate Final Answer
- **Purpose**: Verify agent doesn't generate answer twice when stop check intervenes
- **Steps**:
  1. Run: `brandmind ask -q "cách để cải thiện brand equity nhất là khi re-branding?"`
  2. Scroll through the full output
  3. Check if answer content appears only once
- **Expected Result**: Answer section appears exactly once. If stop check intervenes, agent should call `write_todos` to tick remaining tasks, NOT regenerate the answer.
- **Status**: ✅ Pass (Gemini 3 Flash + Pro), ⚠️ Flaky (Gemini 2.5 Flash — rare regeneration due to middleware injection)

### Test Case 3: No "Synthesize" Task in Plan
- **Purpose**: Verify agent's plan doesn't include "synthesize final answer" type tasks
- **Steps**:
  1. Run: `brandmind ask -q "điểm khác biệt giữa brand image và brand identity?"`
  2. Observe the initial todo plan created by agent
- **Expected Result**: All tasks in the plan are actionable (search, analyze, identify). No task like "Tổng hợp câu trả lời" or "Synthesize final answer".
- **Status**: ✅ Pass (Gemini 3 Flash consistently 3+ tasks, all actionable)

### Test Case 4: Simple Question — No Todo Created
- **Purpose**: Verify simple questions bypass todo system entirely
- **Steps**:
  1. Run: `brandmind ask -q "brand equity là gì?"`
  2. Check if todo list is created
- **Expected Result**: Agent answers directly without creating a todo plan (since it's a simple, single-step question)
- **Status**: ⏳ Pending

### Test Case 5: Task Granularity — Decomposition by Sub-Problems
- **Purpose**: Verify agent decomposes tasks by sub-problems/aspects, not by tools
- **Steps**:
  1. Run a complex multi-aspect question
  2. Check if task list has 3+ specific tasks (not just 1 per tool)
- **Expected Result**: Each task focuses on ONE specific aspect of the question. No compound tasks with "and" connecting multiple actions.
- **Status**: ✅ Pass (Gemini 3 Flash), ⚠️ Partial (Gemini 3 Pro — tends to create 2 tasks but self-corrects mid-execution)

------------------------------------------------------------------------

## 📝 Task Summary

### What Was Implemented

**Components Completed**:
- [x] [Component 1]: Stop Check Prompt Rework
- [x] [Component 2]: Todo System Prompt Refinement
- [x] [Component 3]: EnsureTasksFinished Middleware Logic Fix
- [x] [Component 4]: TodoWrite Reminder Enhancement
- [x] [Component 5]: Prompt Generalization & Gemini Optimization (added during optimization pass)
- [x] [Component 6]: Confirmation Prompt Conflict Resolution (added during optimization pass)
- [x] [Component 7]: Loguru Race Condition Fix (added during optimization pass)

**Files Created/Modified**:
```
src/prompts/task_management/
├── stop_check_prompts.py           # Smarter CRITICAL_REMINDER, ghost-only FINAL_CONFIRMATION
└── todo_system_prompt.py           # Decomposition-first heuristic, conflict-free confirmations

src/shared/src/shared/agent_tools/todo/
└── todo_write_middleware.py         # Removed banned-words filter, nudge threshold adjusted

src/shared/src/shared/agent_middlewares/stop_check/
└── ensure_tasks_finished_middleware.py  # Context preservation in re-prompt

src/cli/
└── log_capture.py                   # Race condition fix for loguru handler removal
```

**Key Features Delivered**:
1. **Context-Aware Re-prompt**: Stop check preserves agent's previous output in message history.
2. **Smarter Prompts**: Agent clearly understands it should tick tasks if work is done vs redo work.
3. **No Final Answer Task**: Plan only contains actionable steps; "synthesize final answer" is excluded.
4. **Decomposition-First Heuristic**: `WRITE_TODOS_TOOL_DESCRIPTION` teaches model to decompose by sub-problems, not by tools. Includes compound task detection ("and" test).
5. **Removed Banned Words Filter**: Eliminated hardcoded filter in `todo_write_middleware.py`, relying on prompt-driven organic self-reflection via `PLAN_CHECK_NUDGE`.
6. **Confirmation Prompt Separation**: `TODO_REMINDER_FINAL_CONFIRMATION` → brief "verify & answer" (proactive). `STOP_CHECK_FINAL_CONFIRMATION` → ghost-recovery only (reactive). No more conflicting "your work is NOT finished" language.
7. **Loguru Fix**: `try/except ValueError` around `logger.remove()` in `SmartLogCapture.stop()` to handle race conditions.

### Technical Highlights

**Architecture Decisions**:
- [Decision 1]: Preserve previous AI response as `AIMessage` in re-prompt context via `_extract_response_content` helper.
- [Decision 2]: Prompt-first approach — solve adherence via instruction, not hardcoded filtering.
- [Decision 3]: Decompose by **sub-problems** not **tools** — root cause of models creating 1-2 tasks was prompt signals biasing toward minimization.
- [Decision 4]: Separate confirmation responsibility — `TODO_REMINDER` (proactive, fires in tool response) vs `STOP_CHECK` (reactive, fires on ghost detection) to prevent double-prompting that caused answer regeneration.

**Root Cause Analyses**:

1. **Task count minimization** (Pro creates only 2 tasks): Competing signals in prompt — strong specific threshold ("1-2 steps → skip") overrode weak vague instruction ("break down"). Fix: removed ceiling language, added explicit decomposition-first principle.
2. **Answer regeneration**: `TODO_REMINDER` said "your work is NOT finished" and `STOP_CHECK` said "continue with additional information" — both fired sequentially, causing model to re-generate/expand its answer. Fix: separated roles and removed "continue" language.
3. **Pro vs Flash behavior difference**: Larger models have stronger priors and optimize for efficiency (fewer tasks), while smaller models follow instructions more literally. Not a bug — inherent model characteristic.

**Model Compatibility Notes**:
- **Gemini 3 Flash**: Best adherence to task decomposition (consistently 3+ tasks), follows instructions literally, recommended as primary model
- **Gemini 3 Pro**: Tends to create 2 broad tasks but self-corrects mid-execution via plan updates. Strong reasoning compensates for loose planning.
- **Gemini 2.5 Flash**: Occasionally creates "synthesize" tasks (self-corrects), rare regeneration issue with middleware injection. Superseded by Gemini 3 Flash.

**Documentation Added**:
- [x] All functions have comprehensive docstrings
- [x] Complex business logic is well-commented
- [x] Module-level documentation explains purpose
- [x] Type hints are complete and accurate

### Validation Results

**Test Coverage**:
- [x] Plan adherence: Gemini 3 Flash ✅, Gemini 3 Pro ✅ (self-corrects)
- [x] No duplicate answer: Gemini 3 Flash ✅, Gemini 3 Pro ✅
- [x] No synthesize task: Gemini 3 Flash ✅ (consistent)
- [x] Task granularity: Gemini 3 Flash ✅ (3+ tasks), Gemini 3 Pro ⚠️ (2 tasks but works)
- [ ] Simple question bypass: Pending
- [x] Loguru ValueError fix: Verified


------------------------------------------------------------------------
