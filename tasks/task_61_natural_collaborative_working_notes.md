# Task 61: Natural Collaborative Working Notes

## Metadata

- **Epic**: BrandMind Agent UX Reliability
- **Priority**: High
- **Status**: Done; Freeze Regression Passed
- **Team**: Backend / Agent Behavior
- **Related Tasks**: `tasks/task_59.md`, `tasks/task_60.md`
- **Owner Boundary**: Backend-only. Web UI implementation remains Claude Code-owned unless explicitly reassigned.

## Progress Checklist

- [x] Agent Protocol — Read `tasks/task_template.md` and prompt-engineering standards
- [x] Context & Goals — Defined the user-facing behavior target and current gap
- [x] Current Evidence — Recorded live audit numbers from labeled SSE traces
- [x] Product Requirements — Defined expected behavior, anti-behavior, and acceptance criteria
- [x] Test Case Matrix — Drafted labeled scenarios for `should_speak`, `should_not_speak`, and `optional`
- [x] Solution Options — Compared prompt/tool experiment vs deterministic harness options
- [x] Harness Sensitivity Probe Plan — Added light / balanced / strict variants before runtime changes
- [x] Implementation Detail — Updated for Variant B light tool-description slice
- [x] Prompt / Tool Experiment — Variant C failed the pilot gate; stop prompt accumulation
- [x] Isolation Ladder Probe — Separated communication capability from full-agent integration pressure
- [x] Reasoning-Level Probe — Tested `medium` reasoning before checkpoint implementation
- [x] Harness Checkpoint Design — Implemented as non-visible first-hidden-tool checkpoint
- [x] Event-Driven Policy Follow-up — Medium reasoning, continuation contract, and multi-note material-transition policy
- [x] Task Summary — Completed after freeze regression and verification

## Context & Goals

### Problem

BrandMind currently has the backend and Web contract needed to show ordered assistant text and reasoning blocks, including main-agent-authored `share_working_note` messages. The hard-coded progress sidecar and keyword gate have been removed. However, live behavior still does not match the intended UX:

- The agent sometimes stays silent for 50-110 seconds during turns where a human collaborator would say something useful before continuing.
- When the agent does speak, many notes sound like status reports: `Tôi đang chuẩn bị...`, `Tôi đang phân tích...`, `Tôi đang soạn...`.
- Some final answers still open with generic greeting or status preambles, even without a working-note block.

### Target Outcome

BrandMind should behave like a natural strategic collaborator, not like a progress-reporting workflow. When the situation calls for it, the main agent should say a short, useful, user-facing aside before continuing work. The aside should help the user understand the changed framing, constraint, trade-off, finding, blocker, strategy pivot, or milestone handoff, not merely announce that the agent is working.

### Non-Goals

- Do not reintroduce a keyword-triggered progress system.
- Do not add UI-generated assistant text.
- Do not make the agent speak before every tool call or every long turn.
- Do not script exact phrases or force a fixed `message -> thought -> message` rhythm.
- Do not artificially cap a long-running turn to exactly one note if a later material transition genuinely appears.
- Do not edit Web UI files for this feature.

## Current Evidence

### Labeled Live Audit — 2026-05-28 ICT

Sample: 20 live brand-strategy turns across 6 workflows and 6 sessions on `gemini-3-flash`.

| Label | Turns | Working Notes | First Visible >45s | Result |
|---|---:|---:|---:|---|
| `should_not_speak` | 2 | 0 | 0 | 2/2 passed |
| `optional` | 5 | 2 | 0 | 4 acceptable, 1 weak optional note |
| `should_speak` | 13 | 4 | 4 | Recall too low; 3 hard missed-bad-silence failures |

Overall outcomes:

- Working notes appeared in 6/20 turns.
- Outcomes: 2 pass, 4 acceptable, 1 weak optional note, 6 soft misses, 1 low-value status note, 3 missed bad-silence, 3 weak status notes.
- Final responses still had status-like starts in 5/20 and generic greeting/preamble starts in 6/20.

Representative failures:

- `signature_strategy/practical_plan`: elapsed 128.28s, first visible assistant text at 110.36s. A working note existed but arrived too late.
- `resource_constraints/no_discount_small_team`: elapsed 59.60s, first visible at 59.60s, no working note.
- `artifact_work/owner_brief`: elapsed 74.24s, first visible at 64.05s, no working note.
- `pushback_and_ambiguity/ambiguous_brand`: elapsed 53.98s, first visible at 53.97s, no working note.

## Product Requirements

### Core Behavior

The main agent may emit a working note only when the note adds collaborative value. A good note names what changed or what matters about the user's input, a newly discovered finding, a blocker, a strategy pivot, or a milestone handoff, then explains how that affects the next move.

The note should feel like:

> "This detail changes how I am framing the problem."

Not like:

> "I am doing work now."

### Should Speak

The agent should usually produce a short working note when one of these situations is present:

1. **Important new constraint**: The user adds budget, team, owner, timeline, margin, brand-equity, or operational limits that materially change the recommendation.
2. **Correction or pushback**: The user says the agent misunderstood, went too generic, or focused on the wrong layer.
3. **Material trade-off**: The user asks to choose between channels, strategies, risks, or stakeholder priorities.
4. **Likely long wait**: The turn requires research, synthesis, artifact planning, or multi-tool work likely to delay visible answer text beyond 45 seconds.
5. **Ambiguity with risk**: The user gives a broad or ambiguous request where a wrong assumption would waste work.
6. **Expectation management**: The user asks for a large deliverable bundle or urgent output where the agent needs to set the working shape before continuing.
7. **Mid-turn material transition**: The agent discovers something that changes the framing, hits a blocker/uncertainty that affects the path, pivots strategy, or reaches a handoff point before more hidden work.

### Should Not Speak

The agent should not produce a working note when:

1. The turn is a greeting, thanks, or simple low-information opener.
2. The user asks a short concept question that can be answered directly.
3. The note would only say the agent is preparing, checking, searching, drafting, analyzing, or comparing.
4. The note is a greeting, appreciation, motivational phrase, or generic preamble.
5. The note repeats the user request or previews the final answer without adding a decision-relevant framing.
6. A previous note already covered the same point and nothing materially changed.

### Optional

The agent may skip the note when the answer can start promptly and no framing change is needed. Silence is acceptable for simple turns if first visible assistant text arrives quickly. Multiple notes in one long turn are acceptable only when each note corresponds to a distinct material transition; they are failures if they become periodic status updates.

## Timing Requirements

| Scenario | Target |
|---|---|
| Simple turn | First visible assistant text should arrive directly with the answer; no working note required. |
| `should_speak` turn with likely long work | First visible assistant text should arrive before 45 seconds. |
| Working note emitted after 45 seconds | Counts as a timing failure if the user was silent before that point. |
| Turn completes before 45 seconds | Missing a note can be a soft miss, not a hard UX failure, unless the user explicitly corrected the agent. |

## Naturalness Rubric

### Pass

A passing note:

- Is one concise sentence.
- Uses the user's language and relationship tone.
- Anchors to a specific user-provided signal.
- Explains the implication for the next move.
- Does not mention tools, agents, phase names, or implementation mechanics.

Examples:

- "Thông tin doanh thu này đổi trọng tâm bài toán: không chỉ là định vị cho đẹp hơn, mà là tìm lý do khách thử xong không quay lại."
- "Ràng buộc này rất quan trọng: mình phải chọn hướng vừa giữ hình ảnh cao cấp, vừa đủ nhẹ để team 2 người triển khai được."
- "Đúng, vậy mình không nên đi theo hướng đổi mới mạnh; bài toán đúng hơn là mở rộng dịp tiêu dùng mà vẫn bảo toàn cảm giác authentic cho khách cũ."

### Weak

A weak note has some context anchor but still talks like a status report.

Examples:

- "Tôi đang phân tích bài toán giữa retention và acquisition dựa trên nguồn lực mỏng của bạn."
- "Tôi đang hệ thống lại các đầu việc cụ thể cho roadmap tuần tới."

### Fail

A failed note is generic, mechanical, late, or disconnected from the user.

Examples:

- "Tôi đang chuẩn bị khung kế hoạch."
- "Mình sẽ bắt đầu tìm hiểu thương hiệu của bạn nhé."
- "Tôi đang tra cứu các khung lý thuyết từ Kotler và Keller."

## Test Case Matrix

| ID | Category | User Message | Expected | Passing Working Note Shape |
|---|---|---|---|---|
| NCWN-01 | Greeting | `Hi xin chào` | `should_not_speak` | No note; answer normally. |
| NCWN-02 | Simple concept | `Brand positioning khác brand identity như nào?` | `should_not_speak` | No note; answer directly. |
| NCWN-03 | Broad kickoff | `Tôi đang muốn phát triển brand strategy cho nhà hàng Chuyện Ba Bữa Signature á` | `optional` | If slow research is needed, briefly explain the evidence check; otherwise answer directly. |
| NCWN-04 | Revenue constraint | `Doanh thu ban đầu 1 tỉ mấy, giờ còn 400-500 triệu/tháng.` | `should_speak` | Name that the problem shifts from attractive positioning to repeat/return behavior. |
| NCWN-05 | Resource constraint | `Owner không muốn giảm giá sâu, team chỉ có tôi và intern.` | `should_speak` | Name the constraint: premium image plus two-person execution capacity. |
| NCWN-06 | User correction | `Khoan, không phải tôi muốn đổi concept hoàn toàn, tôi sợ mất khách Nhật/Hàn cũ.` | `should_speak` | Acknowledge the reframing and move from concept change to controlled extension. |
| NCWN-07 | Trade-off | `Nên ưu tiên retention, KOL hay ads trước?` | `should_speak` | Explain that ads may amplify leakage if repeat is weak; evaluate by risk, not reach. |
| NCWN-08 | Owner brief | `Giúp tôi làm owner brief: vì sao thay đổi, rủi ro, ngân sách, decision gate.` | `should_speak` | Frame the brief around risk control first, then growth. |
| NCWN-09 | Pushback | `Đoạn trước chung chung quá, tôi cần roadmap tuần sau có owner decision và KPI.` | `should_speak` | Acknowledge the correction and switch from broad strategy to decisions, owners, and KPIs. |
| NCWN-10 | Urgent deadline | `Tôi cần phần này trong hôm nay để gửi sếp, nhanh nhưng phải chắc.` | `should_speak` | Prioritize a sendable version over exhaustive completeness. |
| NCWN-11 | Staff script | `Thêm script staff nói với khách tại bàn, đừng quá sales nha.` | `optional` | If used, frame it as guest care, not upsell. |
| NCWN-12 | Artifact bundle | `Chuẩn bị bộ tài liệu cho owner/team đọc, có summary, roadmap, KPI...` | `should_speak` | Split owner decision artifact from team execution artifact. |
| NCWN-13 | Ambiguous new brand | `Tôi có một quán mới, chưa biết nên định vị kiểu gì cho khác biệt.` | `should_speak` | State that the first risk is guessing the competitive frame too early. |
| NCWN-14 | Simple KPI list | `Cho tôi 5 KPI quan trọng nhất để đo chiến dịch kéo khách quay lại.` | `optional` | Usually no note; answer with concise KPI list. |
| NCWN-15 | Strategic risk | `Sếp sợ đổi nhiều quá thì mất khách cũ, không đổi thì khách mới không quay lại.` | `should_speak` | Frame the strategy as preserve-and-evolve, not change-vs-no-change. |

## Metrics And Acceptance Criteria

### Pilot Gate

Run the 15-case matrix above after each prompt/tool experiment.

Required to proceed:

- `should_speak` recall: at least 70%.
- Hard missed-bad-silence: at most 1 case.
- `should_not_speak` over-speak: 0 cases in the core two simple tests.
- Status-like working notes: at most 25% of emitted notes.
- No Web UI regression: ordered blocks still hydrate and stream in order.

### Full Gate

Before calling the feature done:

- Run at least 20 labeled live turns.
- `should_speak` recall should be at least 75%.
- Hard missed-bad-silence should be 0 or 1.
- Status-like notes should be less than 20% of emitted notes.
- Generic final-response preambles should decrease from the baseline 6/20.
- The feature should pass existing unit tests and prompt-bearing ISO smoke.

## Solution Options

| Option | Best When | Wins | Costs / Risks |
|---|---|---|---|
| Harness sensitivity probe | Current evidence shows prompt/tool behavior is the constraint, but strictness level is uncertain | Prevents overfitting to one patch; compares light / balanced / strict on the same cases | Requires more audit effort before claiming success |
| Tool-description-only experiment | Tool selection and tool argument wording are the likely binding surface | Smallest reversible runtime change; tests whether the tool affordance alone can shift behavior | May not reduce generic final-answer preambles |
| Prompt + tool-description experiment | Tool-only improves note selection but final-answer voice remains status-like | Still small and backend-owned; addresses both tool selection and answer openings | Multi-variable if applied first; can become too rule-heavy for chat/Flash-like models |
| Deterministic timer middleware | Prompt experiment fails and long silence remains severe | Can guarantee first visible text before threshold | Risks mechanical text, reintroduces sidecar behavior, harder to make natural |
| Web-only rendering change | Backend emits correct notes but UI hides or misorders them | Keeps agent behavior untouched | Not applicable now; Web order already works |
| Model/profile change | Prompt/tool tuning cannot produce reliable behavior | May improve instruction following | Higher cost, different quality trade-offs, not the current bottleneck |

## Recommended Path

Use a harness sensitivity probe and choose the lightest variant that meets the UX floor:

1. Keep the current backend stream contract; the stream/order layer is not the current bottleneck.
2. Run the same NCWN cases against small harness variants:
   - **Variant A / Baseline**: Current behavior, no new runtime edits.
   - **Variant B / Light**: Refine only the `share_working_note` tool description.
   - **Variant C / Balanced**: Variant B plus a short system-prompt opening guidance if B does not lower generic/status-like final openings enough.
   - **Variant D / Strict**: Add examples or stricter opportunity boundaries only if B/C fail the pilot gate; do not start here.
3. Choose the lightest variant that satisfies the pilot gate. Do not keep extra prompt structure merely because it sounds safer.
4. If recall/timing remains poor after B/C, consider a separate architecture decision for a non-visible wait-state or checkpoint mechanism. Do not reintroduce a visible keyword sidecar as the default fix.

### Harness Sensitivity Rationale

The new harness-engineering note says stricter harnesses are not monotonically safer. A chat/Flash-like model can regress when the harness adds too much process, especially by producing explanatory or status-like prose instead of the desired output. This feature's failure mode is exactly sensitive to that risk: the agent already knows how to speak, but it often speaks in the wrong register (`Tôi đang...`) or speaks too late. Therefore the first runtime slice should be light and measurable, not a combined prompt/tool rewrite.

### Probe Variants

| Variant | Runtime Surfaces | Hypothesis | Kill / Escalation Criterion |
|---|---|---|---|
| A — Baseline | None | Current behavior establishes comparison. | Already below gate; use only as reference. |
| B — Light | `share_working_note` docstring only | Better tool affordance improves `should_speak` recall and note naturalness without over-speaking. | Escalate if `should_speak` recall stays <70%, hard bad silence >1, or final preambles remain the dominant failure. |
| C — Balanced | B + one short `Answer openings` / working-note prompt adjustment | Final answer voice needs a global nudge after tool affordance improves. | Escalate only if B improves tool behavior but final starts stay status-like/generic. |
| D — Strict | B/C + examples or stronger boundaries | The model needs explicit contrastive patterns for this task/model pair. | Use only if C still misses gate and failures are stable; watch over-speaking and mechanical text. |

## Proposed Implementation Surfaces

The first implementation slice should touch only one prompt-bearing backend file:

- `src/core/src/core/brand_strategy/agent_config.py`
  - Variant B: refine `share_working_note` docstring / tool description.

Deferred to Variant C only if the audit shows the tool-only change is insufficient:

- `src/prompts/brand_strategy/system_prompt.py`
  - Refine the `Natural working notes` instruction and final-answer opening guidance with the smallest possible wording change.

Optional follow-up after prompt experiment:

- Add a reusable audit runner under `evaluation/` or `scripts/` if repeated manual SSE auditing becomes too costly.

## Implementation Detail

This section is the pre-apply review surface. Variant B is the first runtime slice. Variant C is intentionally deferred until the Variant B audit shows whether a system-prompt change is necessary.

### Requirement 1 — Variant B: Refine `share_working_note` Tool Description

- **Requirement**: Make the tool description communicate a decision boundary, not a progress-reporting habit. The tool should be selected when the agent can say something decision-relevant before continuing, especially before a likely long wait.

- **Test Specification**:

  ```text
  NCWN-04 / Revenue constraint:
  Input: "Doanh thu ban đầu 1 tỉ mấy, giờ còn 400-500 triệu/tháng."
  Expected: The agent emits a concise note that reframes the problem toward repeat/return behavior, not "I am analyzing revenue."

  NCWN-05 / Resource constraint:
  Input: "Owner không muốn giảm giá sâu, team chỉ có tôi và intern."
  Expected: The agent emits a concise note naming the premium-image + two-person-execution constraint.

  NCWN-01 / Greeting:
  Input: "Hi xin chào"
  Expected: The agent does not call `share_working_note`.
  ```

- **Implementation**:
  - **File**: `src/core/src/core/brand_strategy/agent_config.py` `[MODIFY]`
  - **Change kind**: Replace `share_working_note` docstring only.
  - **Current block**:

    ```python
    def share_working_note(message: str) -> str:
        """Send one short collaborative aside while the work is underway.

        Use this only when you have something genuinely useful to say to the
        user before continuing: a discovered constraint, a changed
        interpretation, a trade-off that affects the next move, a check that
        prevents wasted work, or context for a wait that would otherwise feel
        confusing. Do not use it as a greeting, opening preamble, routine status
        update, or filler before ordinary thinking/searching/drafting. For a
        greeting or low-information opener, skip this tool and answer normally.
        The note is shown directly in chat, so write it as one natural sentence
        in the user's language and relationship tone; if the user writes
        Vietnamese, the note should be Vietnamese too. Do not start the note
        with a greeting or thanks. Prefer specific substance over generic "I
        will start..." or "I am checking..." phrasing: name what matters about
        the moment, not the mechanics of your work. Do not mention internal
        tools, agents, or implementation details.

        Args:
            message: One concise user-facing sentence in the user's
                language and relationship tone. It should carry real
                collaborative value, not a status report.

        Returns:
            Confirmation that the note was streamed to the user.
        """
        if not message.strip():
            return "No working note sent."
        return "Working note sent."
    ```

  - **Historical code written for Variant B** (superseded by Requirement 5):

    ```python
    def share_working_note(message: str) -> str:
        """Send one short collaborative note before continuing the turn.

        Use this only after the user gives a material signal that changes the
        decision path: a new constraint changes the recommendation, a correction
        changes the frame, a trade-off changes what should be prioritized, a
        risky ambiguity could waste work, or a large deliverable needs a clear
        working frame before a visible wait. The note must state what the user's
        signal means for the next move, not what you are doing. A likely wait by
        itself is not enough; for greetings, broad kickoff messages, simple
        concept questions, or normal onboarding diagnosis, skip this tool and
        answer normally.

        Do not use this for greetings, thanks, motivation, quick answers,
        ordinary thinking, or messages that only say you are preparing,
        checking, searching, drafting, analyzing, comparing, or starting. A
        useful note can be paraphrased as: "Because of this user signal, the
        next move should change in this way." If you cannot state that useful
        implication in one sentence, skip the tool and answer normally.

        Write the note in the user's language and relationship tone. Do not
        mention internal tools, agents, phase names, implementation details, or
        step labels. This earlier one-note turn policy is superseded by
        Requirement 5's event-driven material-transition policy.

        Args:
            message: One concise user-facing sentence that anchors to the
                user's specific constraint, correction, trade-off, ambiguity,
                or wait context and explains why it matters for the next move.

        Returns:
            Confirmation that the note was streamed to the user.
        """
        if not message.strip():
            return "No working note sent."
        return "Working note sent."
    ```

- **Acceptance Criteria**:
  - [ ] Tool selection improves on NCWN `should_speak` cases without over-speaking on greeting/simple concept cases.
  - [ ] Emitted notes state implications, not work mechanics.
  - [ ] Existing unit tests still pass.

### Requirement 2 — Variant C: Refine System Prompt Working-Note And Opening Behavior

- **Requirement**: Only apply this if Variant B improves working-note selection/naturalness but the audit still shows generic or status-like final openings, or if tool-only fails `should_speak` recall/timing. Make the main prompt align with the PRD while keeping the edit short enough to avoid a heavy harness.

- **Test Specification**:

  ```text
  NCWN-08 / Owner brief:
  Input: "Giúp tôi làm owner brief: vì sao thay đổi, rủi ro, ngân sách, decision gate."
  Expected: First visible assistant text should arrive before 45s and frame the owner-brief logic around risk control before growth.

  NCWN-09 / Pushback:
  Input: "Đoạn trước chung chung quá..."
  Expected: The agent acknowledges the correction once and moves directly into concrete decisions/KPIs. It should not re-greet or use a status preamble.

  NCWN-02 / Simple concept:
  Input: "Brand positioning khác brand identity như nào?"
  Expected: The agent answers directly with no working note and no long preamble.
  ```

- **Implementation**:
  - **File**: `src/prompts/brand_strategy/system_prompt.py` `[MODIFY]`
  - **Change kind**: Replace the current `Natural working notes` bullet, add one adjacent `Answer openings` bullet, add one workspace-read ordering exception after C2 showed the workspace-read rule was overriding the working-note sequence, and add one late critical order check after C3 showed the earlier rule still lost to tool habits.
  - **Status**: Applied after Variant B smoke showed clean greeting precision but poor `should_speak` recall/timing; refined through C4 after live evidence.
  - **Current block**:

    ```python
    - **Natural working notes**: `share_working_note(message=...)` is not a progress protocol; it is a way to briefly speak to the user while work is underway when a human collaborator would naturally say something useful before continuing. Use it for a discovered constraint, a changed interpretation, a trade-off that affects the next move, a check that prevents wasted work, or context for a wait that would otherwise feel confusing. Do not use it as a greeting, status report, opening preamble, filler before ordinary thinking/searching/drafting, or substitute for the actual answer; for a greeting or low-information opener, skip the tool and answer normally. The note should be one natural sentence in the user's language and relationship tone, anchored in the specific substance of the moment; if the user writes Vietnamese, the note should be Vietnamese too. Do not start the note with a greeting or thanks. Prefer concrete observations or decision framing over generic "I will start..." / "I am checking..." phrasing: name what matters about the moment, not the mechanics of your work. Do not repeat the request, preview the final answer, or mention internal tools, agents, or step names; after results arrive, continue naturally without replaying the same aside.
    - **F&B-Specialized**: Your recommendations account for F&B realities: location-based competition, sensory branding, menu-as-brand, tight margins, and the importance of in-store experience.
    ```

  - **Full code written for Variant C**:

    ```python
    - **Natural working notes**: `share_working_note(message=...)` is a spoken checkpoint for material-signal turns, not a progress protocol. Use it before hidden work when both conditions are true: the user gave a decision-relevant signal (constraint, correction, trade-off, risky ambiguity, or large deliverable frame), and your next visible answer may be delayed by research, synthesis, artifact planning, or multi-tool work. In those turns, make the working note your first tool call before search/read/task/artifact work; if you cannot state a useful implication yet, skip the note and do not call it later as a retrospective status update. The note must state the implication of the user's signal for the next move. Skip the tool for greetings, broad kickoff messages, simple concept answers, quick KPI lists, ordinary drafting, or any note whose main point is that you are preparing, checking, searching, drafting, analyzing, comparing, starting, or have already looked something up. Write one concise sentence in the user's language and relationship tone. Do not start with a greeting or thanks, do not repeat the request, do not preview the final answer, and do not mention internal tools, agents, phase names, or step names.
    - **Answer openings**: Start each final user-facing answer with the substance the user needs next. When the user opens with business substance rather than a greeting, do not open with a generic greeting; start with the business implication. Do not re-greet the user on ordinary follow-up turns, and do not open with "I am preparing/checking/analyzing..." as a substitute for a working note. If you already sent a working note in the turn, do not replay the same framing again at the start of the final answer; continue from it naturally.
    - **F&B-Specialized**: Your recommendations account for F&B realities: location-based competition, sensory branding, menu-as-brand, tight margins, and the importance of in-store experience.

    ...

    **At session start**: Read `brand_brief.md` first (Executive Summary restores 80% of context), then `working_notes.md` (pending items), then `quality_gates.md` (current gate status). Read `user/profile.md` once for user preferences. Exception: if the user's latest message is a material-signal turn that fits the `share_working_note` conditions and the workspace read will create a visible wait, call `share_working_note` first with the decision implication, then read the workspace.

    ...

    11. WORKING NOTE ORDER CHECK: Before your first workspace read, search, specialist dispatch, or artifact-planning tool in a turn, check the latest user message. If it contains a material constraint, correction, trade-off, risky ambiguity, or large deliverable request and the tool work may delay visible text, either call `share_working_note` first with the business implication or deliberately skip it because no useful implication can be stated yet. Do not call `share_working_note` after the tool work as a status report.
    ```

- **Acceptance Criteria**:
  - [ ] Generic final-answer greeting/preamble starts decrease from the baseline 6/20.
  - [ ] Status-like final starts decrease from the baseline 5/20.
  - [ ] Simple answers still feel warm and helpful, not clipped or robotic.

### Requirement 3 — Run Labeled Pilot Audit

- **Requirement**: Run the NCWN matrix after Variant B before deciding whether Variant C is warranted.

- **Test Specification**:

  ```text
  Run at least the 15 NCWN cases through live SSE on `gemini-3-flash`.
  Parse persisted ordered blocks and first-visible assistant-token latency.
  Score each turn using the PRD labels and naturalness rubric.
  ```

- **Implementation**:
  - Use a temporary local audit script or a short inline Python runner for the probe.
  - Do not add a reusable evaluation script in Variant B unless manual auditing becomes the bottleneck.

- **Acceptance Criteria**:
  - [ ] `should_speak` recall >= 70%.
  - [ ] Hard missed-bad-silence <= 1.
  - [ ] `should_not_speak` over-speak = 0 for NCWN-01 and NCWN-02.
  - [ ] Status-like working notes <= 25% of emitted notes.
  - [ ] Existing focused and project tests pass.

### Requirement 4 — Implemented Slice: Non-Visible Harness Checkpoint

- **Requirement**: After the C4 prompt-only matrix failed, stop prompt accumulation and add a harness checkpoint that preserves main-agent-authored content. The checkpoint must not write visible user text, must not use canned progress templates, and must not reintroduce a keyword-triggered sidecar.

- **Problem to Solve**:
  - The model still starts hidden workspace/tool chains before a working note on some material-signal turns.
  - Prompt ordering helped but did not reliably beat workspace-read/tool habits.
  - The checkpoint should affect process order, not note wording: the main agent still decides the actual `share_working_note(message=...)` content.

- **Implemented Mechanism**:
  - Added `WorkingNoteCheckpointMiddleware` in `src/core/src/core/brand_strategy/working_notes.py`.
  - Inserted it in `create_brand_strategy_agent()` after phase-state reminders and before content check, evidence, workspace, sub-agent, todo, and retry middlewares.
  - The middleware intercepts the first hidden tool call in a user turn when no `share_working_note` call has been authored yet.
  - It returns a non-visible `ToolMessage` with a turn-scoped `NCWN_WORKING_NOTE_CHECKPOINT:<session_id>:<turn_index>` marker. The marker is only for model state/history detection; it must never be surfaced to the user.
  - The model then chooses between two actions: call `share_working_note(message=...)` with its own concise implication sentence, or retry the original hidden tool if the user message has no useful decision-relevant implication.
  - The checkpoint uses message-history markers, not only custom state flags, because the first real LangChain probe showed custom top-level `request.state` flags did not reliably persist into the next model step.
  - Same-step parallel hidden tools may each be paused before the model sees the marker, but once the checkpoint marker is in state history hidden tools proceed normally. This avoids loops while keeping the gate deterministic at the first hidden-work boundary.
  - The checkpoint itself does not classify with user keywords and does not generate the note text. The semantic decision remains with the main agent.

- **Guardrails**:
  - Do not block greetings, simple concepts, short KPI lists, or ordinary direct answers.
  - Do not generate the note text in middleware.
  - Do not use fixed Vietnamese/English templates.
  - Limit to one checkpoint per user turn to avoid loops.
  - Record deterministic tests for: greeting no checkpoint, material constraint checkpoint, existing working note no checkpoint, retry proceeds.

- **Implementation Adjustment After Live Smoke**:
  - Initial checkpoint wording was too permissive (`decide whether...`) and live API still skipped the note on `NCWN-04` revenue constraint.
  - The checkpoint was tightened into a communication gate: if the latest user message contains a concrete metric, operating constraint, correction, strategic trade-off, risky ambiguity, stakeholder/deadline pressure, or large deliverable frame, the model should call `share_working_note` unless it genuinely cannot state a decision-relevant implication.
  - A second live failure exposed a conflict in the `share_working_note` docstring: it told the model to skip broad kickoff / normal onboarding, which suppressed the `NCWN-13` risky-ambiguity case. The docstring now distinguishes broad kickoff with no decision risk from new-brand openers where uncertainty about positioning, differentiation, target customers, or concept direction makes a wrong assumption costly.

### Requirement 5 — Event-Driven Working Notes And Medium Reasoning Follow-up

- **Requirement**: Align the production policy with the clarified target: visible collaborative asides are not a fixed one-per-turn preface. They are event-driven checkpoints that may appear at the first hidden-work boundary or later in the same long-running turn only when a new material transition appears. The preferred explicit mechanism is `share_working_note`, but ordinary assistant text before hidden work can also satisfy the UX if it is a useful visible aside rather than a final-answer replay.

- **Problem to Solve**:
  - The earlier contract still implied "at most one note per turn," which conflicts with long-running work where new findings, blockers, pivots, or milestone handoffs can emerge after the first note.
  - Successful early notes were sometimes followed by final answers that re-greeted, reintroduced the role, or repeated the same framing. This created a rough handoff between the note and the answer.
  - Live smoke showed the model can also speak useful ordinary assistant text before hidden work without calling `share_working_note`; the continuation rule must cover both paths.
  - The model allocation was still set to `thinking_level="high"`, even though the user wants the default main-agent behavior tested at `medium` for speed/quality balance and reduced over-thinking.

- **Implementation Surfaces**:
  - `src/core/src/core/brand_strategy/model_profiles.py`: change the default main-agent `thinking_level` from `high` to `medium`.
  - `src/core/src/core/brand_strategy/agent_config.py`: update `share_working_note` so its docstring permits multiple notes only for distinct material transitions and its tool result tells the model to continue from the visible note rather than greet/restate/repeat it.
  - `src/prompts/brand_strategy/system_prompt.py`: update the Natural Working Notes, Answer Openings, session-start workspace exception, Phase 0 first-answer wording, and critical order check to match the event-driven policy.
  - `tests/unit/test_brand_strategy_model_profiles.py`: update the default profile expectation to `medium`.

- **Acceptance Criteria**:
  - [x] Default `gemini-3.5-flash` main-agent profile resolves with `thinking_level == "medium"`.
  - [x] The tool description no longer says "at most one note per turn" and instead permits later notes only for new material findings, blockers, pivots, or milestone handoffs.
  - [x] The tool result includes continuation guidance so the next visible answer should continue from the note rather than replaying it.
  - [x] Prompt text keeps the behavior event-driven, not timer-driven or status-report-driven, and covers both `share_working_note` notes and ordinary visible asides before hidden work.
  - [x] Focused unit/static checks pass.
  - [x] Targeted live smoke checks that at least one material-signal kickoff still gets an early note and a simple greeting does not over-speak.

## Test Execution Log

### Existing Baseline Audit

- **Purpose**: Establish whether current behavior matches target UX.
- **Status**: Completed.
- **Result**: Failed target. `should_speak` recall was 4/13; hard missed-bad-silence appeared in 3/13 `should_speak` turns.

### Next Pilot Audit

- **Purpose**: Validate Variant B light tool-description experiment against the NCWN matrix.
- **Status**: In progress.
- **Expected Result**: Meets Pilot Gate or produces a clear failure signature for Variant C.

### Variant B1 Smoke — 2026-05-29 ICT

- **Purpose**: Validate the first light tool-description edit before spending time on the full matrix.
- **Status**: Failed early; full matrix was not run on B1.
- **Cases run**:
  - `NCWN-01` greeting: over-spoke with a status-like note, `Tôi sẽ bắt đầu...`; elapsed 20.18s, first visible 15.56s.
  - `NCWN-04` revenue constraint: emitted a working-note candidate, but it arrived late at 55.82s and was status-like (`Tôi đã tìm hiểu sơ bộ...`).
  - `NCWN-08` owner brief: no working note; first visible at 62.86s.
- **Interpretation**: The phrase "next work chunk may keep the user waiting" was too broad and let greetings/broad kickoff/onboarding trigger the tool. Variant B2 keeps the same single runtime surface but tightens the boundary: wait alone is not enough; the user must provide a material signal or large deliverable frame.

### Variant B2 Smoke — 2026-05-29 ICT

- **Purpose**: Validate the refined light tool-description boundary after B1.
- **Status**: Failed recall/timing; escalated to Variant C.
- **Cases run**:
  - `NCWN-01` greeting: passed precision; no working-note candidate; elapsed 13.83s.
  - `NCWN-04` revenue constraint: no working note; first visible at 96.94s.
  - `NCWN-08` owner brief: no working note; first visible at 41.06s.
- **Interpretation**: Tool-only can prevent the bad greeting note but does not create enough `should_speak` recall. The next smallest change is a short system-prompt nudge that says material-signal turns should use the tool before hidden work, while keeping the greeting/simple-turn exclusions.

### Variant C1 Smoke — 2026-05-29 ICT

- **Purpose**: Validate the first balanced tool + system prompt nudge.
- **Status**: Partially improved but failed timing/naturalness; refined to C2.
- **Cases run**:
  - `NCWN-01` greeting: passed precision; no working-note candidate; elapsed 11.61s.
  - `NCWN-04` revenue constraint: working-note candidate appeared, but first visible was 50.73s and the note still used status phrasing (`tôi đang xác lập...`).
  - `NCWN-08` owner brief: no working-note candidate; elapsed 27.95s, so this was a soft miss rather than a hard silence failure.
- **Interpretation**: The model understood that material-signal turns may need a note, but it still called the note after hidden work and wrote it as retrospective activity. C2 keeps the same surfaces but makes ordering explicit: when the note is warranted, it should be the first tool call before search/read/task work, otherwise skip it rather than sending a late status update.

### Variant C2 Smoke — 2026-05-29 ICT

- **Purpose**: Validate explicit first-tool-call ordering.
- **Status**: Failed timing; refined to C3.
- **Cases run**:
  - `NCWN-01` greeting: passed precision; no working-note candidate; elapsed 18.30s.
  - `NCWN-04` revenue constraint: working-note candidate appeared, but first visible was 67.08s; tool order showed workspace reads before the note.
  - `NCWN-08` owner brief: no working-note candidate; first visible at 78.54s.
- **Interpretation**: The first-tool-call instruction was being overridden by the later session-start workspace-read rule. C3 adds a narrow exception at the workspace-read rule itself so the prompt surfaces no longer conflict.

### Variant C3 Smoke — 2026-05-29 ICT

- **Purpose**: Validate the workspace-read exception.
- **Status**: Mixed; refined to C4 as the final prompt-only probe.
- **Cases run**:
  - `NCWN-01` greeting: passed precision; no working-note candidate; elapsed 23.75s.
  - `NCWN-04` revenue constraint: working-note candidate improved in content and first visible at 44.01s, but tool order still showed workspace reads before the note.
  - `NCWN-08` owner brief: working-note candidate appeared but was late at 73.15s and status-like (`Tôi đang tổng hợp...`).
- **Interpretation**: The workspace exception improved one material-signal case but still did not reliably beat the workspace-read habit. C4 adds one late critical order check at the bottom of the prompt. If C4 still fails timing/order, prompt-only should be treated as insufficient and the next plan should move to a harness-level checkpoint rather than more prompt accumulation.

### Variant C4 Matrix Audit — 2026-05-29 ICT

- **Purpose**: Run the full NCWN matrix after the final prompt-only order check.
- **Status**: Failed pilot gate; prompt-only should not be pushed further.
- **Artifact**: `/tmp/brandmind_ncwn_c4_audit.json`.
- **Summary**:
  - Total cases: 15.
  - `should_speak`: 10 cases; working-note candidates in 6/10 (`60%`, below the `70%` pilot gate).
  - Hard silence/timing failures: 2 (`NCWN-08`, `NCWN-12`), above the `<=1` pilot gate.
  - `should_not_speak` over-speak: 0/2, meets gate.
  - Emitted notes: 8; status-like notes: 4 (`50%`, above the `<=25%` pilot gate).
  - Outcomes: 6 pass, 2 weak optional status, 2 weak status note, 2 hard silence, 2 soft miss, 1 acceptable.
- **Representative remaining failures**:
  - `NCWN-08` owner brief: no working note; first visible at 80.34s.
  - `NCWN-12` artifact bundle: no working note; first visible at 127.56s.
  - `NCWN-04` revenue constraint: working note arrived early but still used status phrasing in the full matrix sample (`mình đang đối chiếu...`).
  - `NCWN-07` trade-off: structurally pass, but note was in English despite a Vietnamese user message.
- **Interpretation**: The light/balanced prompt/tool probe improved some behavior, especially avoiding greeting over-speak, but it did not create a reliable instinct. The current bottleneck is no longer wording alone; the agent's hidden tool/workspace habit can still delay or suppress working notes on high-opportunity turns. The next experiment should be a non-visible harness checkpoint that preserves main-agent-authored note content while preventing the first hidden tool chain from starting silently in material-signal turns.

### Isolation Ladder Probe — 2026-05-30 ICT

- **Purpose**: Test whether the failure is a Gemini communication capability ceiling or an integration/harness pressure failure in the full BrandMind agent.
- **Status**: Completed as a diagnostic probe; no production code was changed.
- **Artifacts**:
  - `/tmp/brandmind_ncwn_isolation_ladder_20260530_074501.json`
  - `/tmp/brandmind_ncwn_lite_workspace_probe_20260530_080227.json`
  - `/tmp/brandmind_ncwn_full_prompt_fake_tools_20260530_081110.json`
- **Probe stack**:
  1. **Communication-only**: same model profile, no tools, only a structured note-vs-answer decision.
  2. **Minimal tool-order**: `share_working_note` plus one dummy `hidden_work` tool.
  3. **BrandMind-lite**: concise BrandMind role and F&B strategy framing, `share_working_note` plus `hidden_work`.
  4. **Workspace-conflict**: BrandMind-lite plus fake workspace/search tools and a workspace-read-first rule with the working-note exception.
  5. **Full-prompt fake-tool catalog**: current full BrandMind system prompt plus fake versions of the main tool surface (`ls`, `read_file`, `write_todos`, `task`, KG/doc search, artifacts, generators, `report_progress`, and `share_working_note`) on high-signal cases.
- **Results**:

| Probe | Cases | `should_speak` Recall | Clean Pass Rate | `should_not` Over-speak | Status-like Rate | Key Failures |
|---|---:|---:|---:|---:|---:|---|
| Communication-only | 15 | 8/10 = 80% | 7/10 = 70% | 0/2 | 1/9 = 11% | Missed NCWN-07 trade-off and NCWN-13 ambiguous new brand |
| Minimal tool-order | 15 | 6/10 = 60% | 5/10 = 50% | 0/2 | 1/7 = 14% | Missed NCWN-07, NCWN-08, NCWN-12, NCWN-13 |
| BrandMind-lite | 15 | 9/10 = 90% | 9/10 = 90% | 0/2 | 0/10 = 0% | Missed NCWN-13 only; still over-used `hidden_work` on simple turns |
| Workspace-conflict | 15 | 9/10 = 90% | 9/10 = 90% | 0/2 | 0/10 = 0% | Missed NCWN-13 only; workspace-read rule alone did not reproduce the full failure |
| Full prompt + fake tools | 8 high-signal cases | 1/6 = 17% | 1/6 = 17% | 0/2 | 0/1 = 0% | Missed NCWN-04, NCWN-07, NCWN-08, NCWN-12, NCWN-13 |

- **Interpretation**:
  - Gemini 3.5 Flash is not incapable of the behavior. Under a concise communication/BrandMind-lite prompt, it can produce natural Vietnamese working notes with high recall and good naturalness.
  - The workspace-read rule by itself is not the binding constraint. A simplified workspace/search setup still preserved note-before-tool behavior on 9/10 `should_speak` cases.
  - The failure reappears when the full BrandMind prompt and broad tool catalog are present: the model starts with `ls`, `read_file`, KG/doc search, `write_todos`, or artifact checks and skips `share_working_note` on most high-opportunity cases.
  - Current binding constraint: full-agent prompt/tool-catalog pressure and middleware-shaped action habits overwhelm the softer communication policy. This is a Layer 2 integration/harness issue, not a proven Layer 1 model capability ceiling.
  - The next fix should not add more prompt text. It should add a narrow, non-visible first-hidden-tool checkpoint in the full harness, or reduce the full-agent context/tool pressure. The checkpoint remains the smaller and more reversible experiment.

### Medium Reasoning Probe — 2026-05-30 ICT

- **Purpose**: Test the hypothesis that `gemini-3.5-flash` may follow the natural working-note policy better at `thinking_level="medium"` than `high`, because medium may reduce unnecessary over-thinking/tool-chain inertia.
- **Status**: Completed as a diagnostic probe; no production code was changed.
- **Artifact**: `/tmp/brandmind_ncwn_full_prompt_fake_tools_medium_20260530_131440.json`.
- **Baseline compared**: `/tmp/brandmind_ncwn_full_prompt_fake_tools_20260530_081110.json` (`thinking_level="high"`) using the same high-signal full-prompt fake-tool catalog.
- **Results**:

| Reasoning Level | Cases | `should_speak` Recall | Clean Pass Rate | Wrong-Order Notes | Mean Tool Count | Mean Elapsed |
|---|---:|---:|---:|---:|---:|---:|
| High | 8 | 1/6 = 17% | 1/6 = 17% | 0 | 6.50 | 45.71s |
| Medium | 8 | 3/6 = 50% | 1/6 = 17% | 2 | 7.38 | 49.23s |

- **Interpretation**:
  - Medium improved raw working-note recall, but not the UX-correct metric. Two of the additional notes appeared only after multiple hidden tools, so they still fail the timeline requirement.
  - Medium did not reduce tool-chain pressure in this probe. Mean tool count and elapsed time were slightly worse, and the medium run still chose `ls`, `read_file`, KG/doc search, `write_todos`, and even an `edit_file`-shaped call under the broad prompt/tool pressure.
  - Medium remains worth testing later for overall cost/latency or strategy quality, but it does not replace the need for a first-hidden-tool checkpoint for this feature.
  - Current next lever: design the non-visible checkpoint because it directly targets the failure that medium did not fix: note timing/order before the first hidden tool chain.

### Checkpoint Fake-Tool Probe — 2026-05-30 ICT

- **Purpose**: Validate the non-visible checkpoint against the high-signal full-prompt fake-tool setup before restarting a live server.
- **Status**: Passed structurally; one content weakness was tightened before live smoke.
- **Artifact**: `/tmp/brandmind_ncwn_checkpoint_probe_20260530_151615.json`.
- **Summary**:
  - Total cases: 8.
  - `should_speak`: 6 cases; clean pass rate 5/6 (`83.3%`).
  - `should_not_speak`: 2 cases; over-speak 0/2.
  - Emitted notes: 5; status-like notes 0 by the simple status-pattern detector.
  - Mean checkpoint count: 1.0.
- **Representative result**:
  - `NCWN-04` revenue constraint: note was authored before hidden work.
  - `NCWN-08` owner brief: same-step parallel hidden tools were paused until the model authored a note; no hidden tool executed before the note.
  - `NCWN-12` artifact bundle: structurally passed but wrote a weak data-checking note. The checkpoint text was tightened so large deliverable notes must describe the audience/decision/risk shape instead of saying the agent needs to check files, data, sources, or context.
  - `NCWN-13` ambiguous new brand: missed in this fake-tool probe, so it remained a live smoke watchpoint.
- **Interpretation**: The checkpoint changed ordering in the fake full-prompt harness without generating visible text itself. The remaining risk was semantic skip behavior in the production stack, so live API smoke remained required before treating the slice as working.

### Checkpoint Live Smoke — 2026-05-30 ICT

- **Purpose**: Verify actual backend streaming behavior on a sidecar `brandmind serve` process using `gemini-3.5-flash`, not just fake tools.
- **Server**: `BRANDMIND_HOME=/tmp/brandmind_ncwn_sidecar_home BRANDMIND_HOST=127.0.0.1 BRANDMIND_PORT=8018 uv run brandmind serve`.
- **Status**: Passed the targeted checkpoint-smoke set after two scoped fixes; broader 15/20-turn matrix remains pending.
- **Cases run after final checkpoint/docstring edits**:

| Case | Expected | Result | First Token | First Hidden Tool | Notes |
|---|---|---|---:|---:|---|
| `LIVE-01` greeting | `should_not_speak` | Pass precision | 36.06s | 9.75s | No working note; no marker leak. Latency came from workspace/search behavior, not NCWN over-speak. |
| `LIVE-02` simple concept | `should_not_speak` | Pass precision | 38.07s | 8.89s | No working note; direct answer after KG/doc search; no marker leak. |
| `LIVE-04` revenue constraint | `should_speak` | Pass | 6.86s | 8.54s | Note named the >50% revenue drop implication before hidden work; no marker leak. |
| `LIVE-05` resource constraint | `should_speak` | Pass | 6.65s | 6.65s | Note named premium-image and two-person execution constraint; no marker leak. Rounded timestamps are equal, but event order showed first token before the first hidden tool. |
| `LIVE-08` owner brief | `should_speak` | Pass | 6.30s | 8.11s | Note framed the brief as a strategic anchor for risk/budget/decision gates; no marker leak. |
| `LIVE-13R` ambiguous new brand | `should_speak` | Pass after docstring conflict fix | 17.00s | 21.39s | Note framed the risk of choosing the wrong competitive reference frame; no marker leak. |

- **Failed intermediate live probes and fixes**:
  - First live `NCWN-04` after checkpoint implementation failed: first visible text at 81.95s after hidden tools. Fix: tightened the checkpoint from optional advisory wording to a material-signal communication gate.
  - `NCWN-13` then failed: first visible text at 71.86s after hidden tools. Fix: removed the prompt-surface conflict where `share_working_note` treated broad kickoff / normal onboarding as a blanket skip condition.
- **Residual issue**:
  - Several final answers still re-open with a generic greeting or role introduction after a successful working note. The checkpoint solves first-visible timing/order, but final-response opening voice still needs a separate follow-up if the product target includes eliminating repeated greetings in first substantive turns.

### Event-Driven Policy Follow-up — 2026-05-31 ICT

- **Purpose**: Apply the approved final policy: medium main-agent reasoning, event-driven working notes instead of one-note-per-turn, continuation guidance after a visible note, and prompt coverage for ordinary assistant-text asides before hidden work.
- **Status**: Implemented and passed targeted verification. Broader 15/20-turn matrix remains the feature-completion gate.
- **Code/test changes**:
  - Default `BrandStrategyMainModelProfile.thinking_level` changed from `high` to `medium`.
  - `share_working_note` docstring now permits later notes only for distinct material transitions: new findings, blockers, strategy pivots, or milestone handoffs.
  - `share_working_note` return text now reminds the model to continue from the visible note and not greet/restate/repeat it.
  - System prompt now treats working notes as material-transition checkpoints and extends the continuation rule to both `share_working_note` notes and ordinary assistant-text asides before hidden work.
  - Task PRD updated so the target is event-driven natural collaboration, not a fixed `message -> thought -> message` rhythm.
- **Focused verification**:
  - `uv run pytest tests/unit/test_brand_strategy_model_profiles.py tests/unit/test_working_note_checkpoint_middleware.py tests/unit/test_streaming_bridge.py -q` → `56 passed, 1 warning`.
  - `uv run ruff check ...` on changed backend/test files → passed.
  - `uv run ruff check --ignore E501 src/prompts/brand_strategy/system_prompt.py` → passed.
  - `uv run mypy src/core/src/core/brand_strategy/model_profiles.py src/core/src/core/brand_strategy/agent_config.py src/core/src/core/brand_strategy/working_notes.py tests/unit/test_brand_strategy_model_profiles.py tests/unit/test_working_note_checkpoint_middleware.py --ignore-missing-imports` → passed.
  - `git diff --check` → passed.
- **Live sidecar smoke**:
  - Server: `BRANDMIND_HOME=/tmp/brandmind_ncwn_event_policy_home2 BRANDMIND_HOST=127.0.0.1 BRANDMIND_PORT=8018 uv run brandmind serve`.
  - `LIVE-SIGNATURE-R2`: first visible text at `18.69s`, first hidden tool at `22.47s`, no checkpoint marker leak. Server log confirmed `share_working_note` carried the visible Signature/parent-brand implication before hidden work; final answer continued into market findings without re-greeting.
  - `LIVE-REVENUE-R2`: first visible text at `7.64s`, first hidden tool at `9.45s`, no checkpoint marker leak. The opening correctly framed the >50% revenue drop before hidden work; the later answer still repeated some revenue framing, so broader matrix should still score continuation smoothness.
  - Earlier same-run `LIVE-GREETING`: no `share_working_note`, no marker leak; first visible at `27.99s`. It passed no-over-speak for the working-note feature, though the greeting answer remains broader than ideal onboarding polish.
- **Interpretation**:
  - The backend now supports both mechanisms: explicit `share_working_note` and ordinary assistant text before hidden work. This better matches the product goal of natural interaction rather than forcing every aside through a visible tool pattern.
  - The remaining risk is qualitative, not structural: final-answer continuation can still replay part of the initial aside in some cases. This should be evaluated in the broader live matrix before declaring the feature done.

### Broader Matrix And Assumption-Risk Follow-up — 2026-05-31 ICT

- **Purpose**: Verify the event-driven policy against the 15-case NCWN matrix using the real backend and `gemini-3.5-flash` at the new default `thinking_level="medium"`.
- **Server**: `BRANDMIND_HOME=/tmp/brandmind_ncwn_matrix_20260531_home BRANDMIND_HOST=127.0.0.1 BRANDMIND_PORT=8018 uv run brandmind serve`.
- **Matrix artifact**: `/tmp/brandmind_ncwn_matrix_20260531.json`.
- **Raw matrix summary**:
  - Total cases: 15.
  - Automatic verdicts: 8 pass, 6 weak, 1 fail.
  - `should_speak` clean pass rate by strict automatic scoring: 5/10 (`50%`).
  - Hard bad-silence failures in `should_speak`: 1 (`NCWN-13` ambiguous new brand).
  - `should_not_speak` over-speak: 0/2.
  - Status-like pre-tool notes by simple detector: 3 (`NCWN-06`, `NCWN-09`, `NCWN-12`), though manual review found `NCWN-06` and `NCWN-09` were useful implication notes with mildly future-oriented wording rather than true progress reports.
  - Marker leaks: 0.
- **Key observations**:
  - Constraint and trade-off turns now mostly work: `NCWN-04`, `NCWN-05`, `NCWN-07`, `NCWN-08`, and `NCWN-10` emitted early implication-bearing notes between 7-9s.
  - `NCWN-03` broad named-brand kickoff was still weak: no early note, first visible at 118.92s after hidden research. The prompt said broad kickoff can be skipped, but this case carried source-verification risk because it named a real restaurant.
  - `NCWN-13` ambiguous new brand was the only hard failure: first hidden tool at 8.93s, first visible at 64.55s, and the answer opened with a generic greeting/praise. The checkpoint let the model skip because the prompt did not teach that missing facts can still produce an assumption-risk note.
  - `NCWN-12` artifact bundle had an early note, but the note opened with "tôi sẽ xây dựng...", which is closer to a future-work report than the desired implication-first voice.
  - `NCWN-14` simple KPI list remained a latency issue: no working note was appropriate, but the model still did hidden retrieval and first visible text arrived at 77.42s.
- **Patch applied after matrix**:
  - `src/core/src/core/brand_strategy/agent_config.py`: `share_working_note` docstring now says missing facts can be a valid assumption-risk note and asks for implication-first phrasing rather than first-person future-work reporting.
  - `src/core/src/core/brand_strategy/working_notes.py`: checkpoint reminder now says lack of facts is not a reason to stay silent when the latest message has business substance; the model should name the assumption risk before continuing hidden work.
  - `src/prompts/brand_strategy/system_prompt.py`: Natural Working Notes, session-start exception, and critical order check now include assumption-risk semantics. A narrow Direct-answer fast path was also added for simple concept/KPI/list requests.
  - `tests/unit/test_working_note_checkpoint_middleware.py`: checkpoint content test now asserts the assumption-risk reminder is present.
- **Targeted rerun artifact**: `/tmp/brandmind_ncwn_targeted_20260531.json`.
- **Targeted rerun results after assumption-risk patch**:
  - `NCWN-03R` broad named-brand kickoff: first visible 9.59s, first hidden tool 14.08s, early note framed parent-brand vs independent-brand risk; no marker leak.
  - `NCWN-12R` artifact bundle: first visible 8.27s, first hidden tool 10.52s, early note framed internal communication + owner/KPI shape without first-person future-work status; no marker leak.
  - `NCWN-13R` ambiguous new brand: first visible 8.14s, first hidden tool 10.06s, early note named the risk of positioning before knowing the F&B model; no marker leak. This directly fixed the matrix hard failure.
  - `NCWN-14R` simple KPI list: still weak before the fast-path patch, first visible 54.57s after hidden retrieval and no note.
  - `NCWN-15R` strategic risk: first visible 6.95s, first hidden tool 8.37s, early note framed preserve-vs-improve risk; no marker leak.
- **Fast-path probe after adding Direct-answer fast path**:
  - Artifact: `/tmp/brandmind_ncwn_fastpath_20260531.json`.
  - `NCWN-02F` concept question still used KG/doc retrieval and first visible text arrived at 37.33s; no over-speak and no marker leak, but the prompt alone did not stop hidden retrieval.
  - `NCWN-14F` KPI list improved below the 45s visible-latency threshold at 40.91s, but still used `search_document_library` and opened with a greeting/praise. This is acceptable for NCWN timing but not a full direct-answer/tool-use fix.
- **Focused verification after patches**:
  - `uv run pytest tests/unit/test_working_note_checkpoint_middleware.py tests/unit/test_brand_strategy_model_profiles.py tests/unit/test_streaming_bridge.py -q` -> `56 passed, 1 warning`.
  - `uv run pytest tests/unit/test_working_note_checkpoint_middleware.py -q` -> `6 passed`.
  - `uv run ruff check src/core/src/core/brand_strategy/agent_config.py src/core/src/core/brand_strategy/working_notes.py tests/unit/test_working_note_checkpoint_middleware.py tests/unit/test_brand_strategy_model_profiles.py tests/unit/test_streaming_bridge.py` -> passed.
  - `uv run ruff check --ignore E501 src/prompts/brand_strategy/system_prompt.py` -> passed.
- **Interpretation**:
  - The core NCWN failure is now much narrower: the checkpoint plus assumption-risk language makes material-signal turns speak early and naturally in the cases that previously failed.
  - The remaining issue is adjacent but distinct: simple/direct requests still tend to trigger hidden theory retrieval before visible answers, and the answer can open with a generic greeting/praise. That is a direct-answer/tool-use policy problem, not the same as NCWN `should_speak` recall.
  - Do not add more broad working-note prompt text for the direct-answer issue. The next slice should isolate why retrieval/tool pressure overrides the fast path, then decide whether to adjust retrieval policy, evidence middleware, or add a deterministic direct-answer gate.

### Stale Project Index And Sufficiency-First Follow-up — 2026-06-01 ICT

- **Purpose**: Fix the live behavior where deleted test chats still influenced later sessions through stale project-index metadata, then reduce the prompt conflict that made simple/direct user requests trigger hidden KG/doc retrieval even when the current context was enough.
- **Root cause #1**:
  - The web delete dialog correctly sent `delete_workspace=true` when "Also clear this chat's saved progress" was checked.
  - `SessionManager.delete_session()` deleted the persisted chat and workspace directory, but did not remove the matching row from `~/.brandmind/index.json`.
  - `ProactiveContextBuilder._find_prior_projects()` trusted the index row even when `~/.brandmind/projects/{session_id}/workspace` no longer existed, so later sessions could receive "related prior project memory" from a ghost registry entry.
- **Backend cleanup patch**:
  - Added `shared.workspace.remove_project_from_index(session_id, brandmind_home=...)` to prune only the deleted project row while preserving other project registry entries.
  - `SessionManager.delete_session()` now calls that helper only when the effective delete decision removes saved workspace progress. Deleting chat history while keeping saved progress still preserves the index row.
  - `ProactiveContextBuilder._find_prior_projects()` now requires a real prior workspace directory and a substantive workspace excerpt before returning a prior match. Template-only and ghost registry rows no longer become source-backed memory.
- **Root cause #2**:
  - The prompt already had a Direct-answer fast path, but lower prompt sections contradicted it with stronger wording such as "Whenever..." verification and "When in doubt, SEARCH."
  - That made simple concept/KPI/list turns drift toward hidden retrieval even when the answer could be useful from the visible conversation and general strategy knowledge.
- **Sufficiency-first prompt patch**:
  - Added a "Sufficiency-first tool policy" to make the first decision "is the current context enough for the next useful user-facing move?"
  - Reframed KG/doc tools as decision/source-defense tools, not default prerequisites for simple explanations.
  - Rewrote the Knowledge Verification Principle so source-humble direct answers are allowed for simple explanations/lists/tactical advice, while decision-grade, route-changing, durable, external-current, or stakeholder-defensible claims still require verification.
  - Updated Phase 0 diagnosis quality gate so KG/doc verification applies when concepts determine scope, brand architecture, or stakeholder-defensible diagnosis; sparse openings should not block on source lookup.
- **Focused verification**:
  - `uv run pytest tests/unit/test_workspace_home.py tests/unit/test_server.py::TestSessionManager tests/unit/test_proactive_context_middleware.py tests/unit/test_prompt_surface_hygiene.py -q` -> `59 passed, 1 warning`.
  - `uv run ruff check src/shared/src/shared/workspace/__init__.py src/server/services/session_manager.py src/shared/src/shared/agent_middlewares/proactive_context/middleware.py tests/unit/test_workspace_home.py tests/unit/test_server.py tests/unit/test_proactive_context_middleware.py tests/unit/test_prompt_surface_hygiene.py` -> passed.
  - `uv run ruff check --ignore E501 src/prompts/brand_strategy/system_prompt.py src/shared/src/shared/agent_skills/brand_strategy/brand-strategy-orchestrator/references/phase_0_diagnosis.md` -> passed.
  - `uv run mypy src/shared/src/shared/workspace/__init__.py src/server/services/session_manager.py src/shared/src/shared/agent_middlewares/proactive_context/middleware.py --ignore-missing-imports` -> passed.
  - Manual line-length audit over changed non-prompt Python/test files -> no output.
  - `git diff --check` -> passed.
- **Residual validation needed**:
  - Because `system_prompt.py` and a runtime skill reference changed, run the project prompt-bearing ISO before calling this follow-up complete: restart `brandmind serve`, verify health, then run at least one direct-answer/simple-KPI or concept turn and one deleted-project-index regression smoke.
  - Expected live behavior after the patch: deleted saved-progress chats should not appear as prior project memory, simple direct turns should be more likely to answer from current context first, and named/public/route-changing facts should still verify before being treated as public truth.

### Freeze Regression — 2026-06-01 ICT

- **Purpose**: Close the NCWN behavior slice after user live testing showed `medium` reasoning improved latency and naturalness.
- **Server reset**:
  - `uv run brandmind serve --stop` -> detached server stopped.
  - `make brandmind-reset-home` -> reset `/Users/lehoanganhtai/.brandmind`, preserving browser data.
  - `uv run brandmind serve --detach` -> server started with health endpoint at `http://127.0.0.1:8000/api/v1/health`.
  - `nc -z localhost 19530` -> Milvus reachable.
- **Regression artifact**: `/tmp/brandmind_ncwn_freeze_regression_20260601.json`.
- **Cases**:

| Case | Label | Result | First Visible | First Hidden Tool | Notes |
|---|---|---:|---:|---:|---|
| `REG-01` greeting | `should_not_speak` | Pass | 15.62s | none | No working-note over-speak. |
| `REG-02` simple concept | `should_not_speak` | Pass | 9.82s | none | Direct answer, no hidden retrieval. |
| `REG-03` simple KPI list | optional/direct | Pass | 21.54s | none | No hidden retrieval; still opened with a longer greeting/praise, which is voice polish rather than an NCWN blocker. |
| `REG-04` Signature kickoff | `should_speak` | Weak | 13.33s | 13.32s | Useful market-context note, but timing was effectively same-step with first hidden tool. |
| `REG-05` revenue constraint | `should_speak` | Pass | 7.34s | 8.76s | Early implication note before hidden work. |
| `REG-06` resource constraint | `should_speak` | Pass | 5.69s | 7.63s | Early implication note before hidden work. |
| `REG-07` ambiguous new brand | `should_speak` | Pass | 8.79s | 11.54s | Early assumption-risk note before hidden work. |
| `REG-08` strategic risk | `should_speak` | Pass | 9.99s | 11.80s | Early preserve-vs-change framing before hidden work. |
| `REG-09` channel trade-off | `should_speak` | Pass | 9.07s | 10.51s | Early budget/trade-off framing before hidden work. |

- **Summary**:
  - Total: 9 cases.
  - Results: 8 pass, 1 weak, 0 fail.
  - `should_speak`: 6/6 pass-or-weak; 5/6 clean pass.
  - Hard failures: 0.
  - `should_not_speak` over-speak: 0.
  - Marker leaks: 0.
  - Per-case workspace delete failures: 0.
- **Delete cleanup shape correction**:
  - The initial regression helper checked the index as a list, while the current BrandMind index is a dict keyed by session id.
  - A separate dict-aware smoke at `/tmp/brandmind_delete_cleanup_smoke_20260601.json` verified the real delete path: workspace existed before delete, index row existed before delete, `DELETE ...?delete_workspace=true` returned `204`, workspace was removed, and the dict index row was removed.
- **Interpretation**:
  - NCWN is now good enough to freeze for product iteration. The remaining issues are adjacent quality targets, not blockers for this feature.
  - The next higher-ROI BrandMind target is artifact delivery quality: generated PPTX/XLSX/Brand Key artifacts should match the conversation language, local market context, and visual quality expectations instead of drifting into English or generic layouts.

### Final Verification — 2026-06-01 ICT

- `uv run pytest tests/unit/test_brand_strategy_model_profiles.py tests/unit/test_working_note_checkpoint_middleware.py tests/unit/test_streaming_bridge.py tests/unit/test_workspace_home.py tests/unit/test_server.py::TestSessionManager tests/unit/test_proactive_context_middleware.py tests/unit/test_prompt_surface_hygiene.py -q` -> `115 passed, 1 warning`.
- `uv run ruff format --check ...` on changed non-prompt Python/test files -> passed.
- `uv run ruff check ...` on changed non-prompt Python/test files -> passed.
- `uv run ruff check --ignore E501 src/prompts/brand_strategy/system_prompt.py src/shared/src/shared/agent_skills/brand_strategy/brand-strategy-orchestrator/references/phase_0_diagnosis.md` -> passed.
- `uv run mypy src/core/src/core/brand_strategy/agent_config.py src/core/src/core/brand_strategy/model_profiles.py src/core/src/core/brand_strategy/working_notes.py src/server/services/session_manager.py src/server/streaming/bridge.py src/shared/src/shared/agent_middlewares/proactive_context/middleware.py src/shared/src/shared/workspace/__init__.py --ignore-missing-imports` -> passed.
- `uv run bandit -r src/ -s B101,B603 -ll` -> no medium/high issues identified.
- `git diff --check` -> passed.
- Manual line-length audit over changed non-prompt Python/test files -> no output.
- `uv run python - <<'PY' ...` delete-cleanup smoke -> dict index row removed after `delete_workspace=true`.

## Decision Log

| # | Decision | Options Considered | Choice Made | Rationale |
|---|---|---|---|---|
| 1 | Feature name | Progress update vs working note vs collaborative aside | Natural Collaborative Working Notes | The target is natural collaboration, not progress reporting. |
| 2 | Initial optimization surface | Prompt/tool vs middleware vs Web UI | Prompt/tool first | Current evidence points to main-agent decision behavior, not stream or UI failure. |
| 3 | Scoring method | Rule-based only vs LLM judge vs hybrid | Hybrid | Rule-based metrics catch timing/structure; human judgment labels opportunity and naturalness for small samples. |
| 4 | Timing threshold | No threshold vs 30s vs 45s vs 60s | 45s | Matches observed UX pain without forcing notes on normal short turns. |
| 5 | Prompt strictness | Single combined patch vs light/balanced/strict probe | Harness sensitivity probe | New harness-engineering guidance shows stricter prompts can regress chat/Flash-like models; choose the lightest passing variant. |
| 6 | First runtime slice | Tool only vs tool + system prompt | Tool only | Keeps one variable isolated; system prompt changes are deferred until evidence shows they are needed. |
| 7 | Variant B1 failure response | Escalate to system prompt vs refine same tool surface | Refine tool surface to B2 first | B1 failed due a specific over-broad wait clause; fixing that clause preserves one-variable isolation. |
| 8 | Variant B2 failure response | Keep tuning tool description vs apply short system-prompt nudge | Apply Variant C | Tool-only fixed greeting precision but failed `should_speak` recall and timing; the next bottleneck is global turn-policy awareness. |
| 9 | Variant C1 failure response | Add content examples vs specify sequencing | Specify sequencing | Failure was late/retrospective tool use, not lack of example wording. Process ordering is the smaller fix. |
| 10 | Variant C2 failure response | Add more examples vs resolve prompt-order conflict | Add workspace-read exception | Live tool order showed workspace reads before notes, so the conflict was in the harness/process instructions rather than note wording. |
| 11 | Variant C3 failure response | Keep adding prose vs add one recency-positioned rule | Add final critical order check | C3 improved content but not order; a bottom-positioned order check is the last prompt-only probe before harness escalation. |
| 12 | Variant C4 result | Keep prompt tuning vs harness checkpoint | Stop prompt tuning; design harness checkpoint | Full matrix failed recall, timing, and status-like gates. More prompt text would likely add complexity without reliable control. |
| 13 | Isolation ladder result | Treat as model ceiling vs integration pressure | Treat as full-agent integration pressure | Communication-only and BrandMind-lite probes passed enough to show capability exists; full prompt + fake catalog reproduced the failure, so the next lever is harness/context/tool pressure. |
| 14 | Medium reasoning result | Change model profile first vs checkpoint first | Keep checkpoint first for NCWN | Medium increased raw note recall but did not improve clean pass rate or reduce tool-chain pressure; checkpoint targets the remaining ordering failure directly. |
| 15 | Checkpoint implementation shape | Middleware-generated visible text vs non-visible model checkpoint | Non-visible checkpoint | Preserves main-agent authored content while forcing the communication decision before hidden work starts. |
| 16 | Checkpoint state tracking | Custom request state only vs message-history marker | Message-history marker | Real probe showed custom top-level state flags can be dropped between model steps; a turn-scoped marker in history persisted and avoided repeated checkpoint loops. |
| 17 | Live failure response | Add more prompt examples vs tighten the actual conflicting decision surfaces | Tighten checkpoint gate, then tool docstring conflict | Live evidence showed the model could still skip material signals and then skipped risky ambiguity because the tool description called broad kickoff/normal onboarding a skip. Fixing the conflicting surfaces was smaller than adding more examples. |
| 18 | Main-agent reasoning effort | Keep `high` vs switch default to `medium` | Switch default main-agent profile to `medium` | User priority shifted toward speed/quality balance and avoiding over-thinking; prior probe showed medium alone was insufficient for ordering, but it is still the desired default allocation after the checkpoint exists. |
| 19 | Note frequency policy | One note per turn vs one note per material transition | One note per material transition | Long-running work may discover new findings, blockers, pivots, or handoff points. The target is natural collaboration, not an artificial cap or a timer. |
| 20 | Visible-aside mechanism | Require `share_working_note` for every aside vs accept ordinary assistant text when it appears before hidden work | Accept both, keep `share_working_note` as explicit mechanism | Live smoke showed useful assistant text can appear before the first hidden tool. Treating that as valid preserves native model behavior and avoids overfitting the product to a tool pattern. |
| 21 | Missing-facts behavior | Let the model skip notes when facts are missing vs treat missing facts as assumption risk | Treat missing facts as assumption risk when business substance exists | The broader matrix hard failure (`NCWN-13`) happened because the agent could not yet state the answer, so it silently started hidden work. The corrected behavior is to name the risk of guessing the wrong frame before doing hidden work. |
| 22 | Simple/direct request latency | Keep tuning NCWN note policy vs isolate retrieval/tool-use pressure | Isolate retrieval/tool-use pressure separately | The Direct-answer fast path did not fully stop KG/doc retrieval on simple concept/KPI turns. More working-note prose would not solve that; the next slice should target retrieval policy or middleware behavior. |
| 23 | Deleted chat saved-progress cleanup | Delete chat file only vs delete workspace plus index row when checkbox is enabled | Delete the index row only when saved workspace progress is removed | Keeping the row when progress is kept preserves reusable memory; keeping it after workspace deletion creates ghost prior-project context. |
| 24 | Direct-answer tool policy | Keep "When in doubt, SEARCH" vs sufficiency-first routing | Sufficiency-first routing | Simple concept/KPI/list turns need useful visible answers from current context; tool verification remains for route-changing, durable, public-current, or stakeholder-defensible claims. |

## Task Summary

Checkpoint v1 plus the event-driven policy, assumption-risk follow-up, stale-index cleanup, sufficiency-first tool policy, and `medium` main-agent reasoning are implemented and verified. The final freeze regression passed with 8 pass, 1 weak, 0 fail across the selected high-signal cases, no hard silence, no marker leaks, no `should_not_speak` over-speak, and no delete-cleanup failures. NCWN should now be treated as frozen unless a future regression shows a concrete failure. Remaining adjacent work belongs in new targets: artifact delivery quality, evidence/claim calibration, and occasional final-answer voice polish on simple/direct turns.
