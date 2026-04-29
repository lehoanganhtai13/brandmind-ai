# M-1 Findings — Why Tier 1 Artifact Production Fails

## Executive summary

BrandMind's main agent never dispatches the deliverable-producing tools
(`generate_brand_key`, `generate_document`, `generate_presentation`,
`generate_spreadsheet`) during a complete brand-strategy session. Phase 5
advances and the session closes purely on the strength of chat text. The
underlying causes span four layers — system prompt language, sub-agent
prompts, content-check spec scope, and skill text — but only two of
them carry root-cause weight. The rest amplify the failure.

**Tier 1 health observed (`evaluation/artifact_audit.py` on r6 baseline):**

```
brand_key_produced       = False
strategy_doc_produced    = False
kpi_xlsx_produced        = False
presentation_produced    = False
workspace_brief_covers_all_phases = False
```

Sub-agent dispatch in r6: `creative-studio: 1` (description requested
mood-board direction, not Brand Key compilation), `document-generator:
0`, `market-research: 1`, `social-media-analyst: 1`.
Deliverable tool calls in r6: **0 across all four tools**.

## Architecture audit

### Tool ownership (correct, but partly inconsistent with prompt)

`agent_config.py:255-282`:

| Layer | Tools |
|---|---|
| Main agent | `search_*`, `browse_and_research`, `deep_research`, `analyze_social_profile`, `get_search_autocomplete`, `generate_image`, `edit_image`, `export_to_markdown`, `report_progress` |
| `creative-studio` sub-agent | `generate_image`, `edit_image`, `generate_brand_key` |
| `document-generator` sub-agent | `generate_document`, `generate_presentation`, `generate_spreadsheet`, `export_to_markdown` |

The split is structurally clean — heavy generators live behind sub-agents
that own a generate→evaluate→refine quality loop. The main agent has no
direct path to `generate_brand_key` / `generate_document` /
`generate_presentation` / `generate_spreadsheet`; the only path is
`task(subagent_type="creative-studio" | "document-generator", …)`.

### Sub-agent prompts (read-only)

- `prompts/brand_strategy/subagents/creative_studio.py`
  - Heavy emphasis on mood boards, logo concept directions, color
    palette visualizations, and a closing reminder that *"All generated
    images are DIRECTION DRAFTS"*.
  - `generate_brand_key` mentioned **once** at line 52: `"Brand Key
    visual — Use generate_brand_key with the structured data from the
    main agent's brief."` No instruction telling the sub-agent to
    distinguish between mood-board briefs and Brand Key briefs.
- `prompts/brand_strategy/subagents/document_generator.py`
  - Behaviour controlled by what the main agent sends. The prompt is
    explicit about output contract (file path + ToC), but it does not
    list the four canonical deliverables a Phase 5 close requires.
  - Defensive instruction at line 38–39: *"Handle gaps honestly —
    include the section header with a clear placeholder"*. When the
    dispatch is partial, the sub-agent will return a partial document
    rather than refuse — but it still calls a generator tool. So a
    correctly-dispatched call should still produce a file.

### Main system prompt (Phase 5 section)

`prompts/brand_strategy/system_prompt.py:130-144`:

- Lists actions including *"Brand Strategy Document assembly (PDF/DOCX
  — 10 sections)"*, *"Executive Presentation (PPTX — key slides)"*,
  *"Brand Key one-pager (generate_brand_key tool)"*.
- Delegation guidance: *"Use Document Generator sub-agent for PDF/PPTX
  production."* — soft "Use", no MUST, no concrete dispatch template.
- Quality Gate: *"All deliverables generated, user satisfied."* —
  closure depends on user satisfaction, not on artifact existence.

`prompts/brand_strategy/system_prompt.py:184-186` (tool inventory
section):

- Lists `generate_brand_key`, `generate_document`,
  `generate_presentation`, `generate_spreadsheet` under
  *"Specialized Tools (load via `tool_search` → `load_tools` when
  needed)"*.
- This is **misleading**. These tools are sub-agent-only; the main
  agent cannot satisfy `load_tools(["generate_brand_key"])`. The
  inventory section invites the agent to attempt direct loading,
  silently fail or fall back to text-only Phase 5.

### Content-check phase_5 spec

`core/brand_strategy/content_check.py` `PHASE_DELIVERABLE_SPECS["phase_5"]`:

- Validates the **textual** presence of the Brand Key 9 components,
  KPI framework, and 3-horizon implementation roadmap.
- Does NOT inspect recent `ToolMessage`s for file paths or artifact
  callbacks. Phase 5 advance succeeds when the agent has *talked
  about* the deliverables, regardless of whether any file was written.

### Skill (`brand-communication-planning`)

- `SKILL.md:140-142` instructs the agent to *"Delegate document
  generation to the document-generator sub-agent via
  `task(subagent_type="document-generator")`"* and *"Delegate Brand
  Key visual to the creative-studio sub-agent via
  `task(subagent_type="creative-studio")`"*. Correct delegation
  pattern.
- BUT line 142 also says: *"Use `generate_spreadsheet` for KPI
  tracking templates (XLSX)"* — without the delegation framing. The
  main agent does not have access to that tool, so following this
  literally fails silently.
- `references/deliverable_assembly.md` — provides full structure for
  the strategy doc (10 sections), Brand Key one-pager (9 components),
  presentation deck (10–12 slides). All correctly tied to the
  delegation pattern.

### Observed agent behaviour in r6

From `server.log` debug stream:

- T8 (06:56:35) — main agent dispatched `creative-studio` with
  description: *"Dựa trên các thông tin sau, hãy tạo một bản định
  hướng hình ảnh (Visual Direction) và Moodboard cho nhà hàng "Chuyện
  Ba Bữa Signature":\n1. Định vị: ...\n2. 3 Tính từ cốt lõi: ..."*.
  The description asked for a mood board, not the Brand Key. The
  sub-agent dutifully generated 2 mood images (`generated_*.jpeg`,
  visible in `brandmind-output/images/`). It **never** called
  `generate_brand_key`.
- No turn dispatched `document-generator`. Phase 5 closed with text
  alone.

## FMEA — failure mode prioritization

| ID | Failure mode | Severity | Likelihood | Detectability | RPN | Notes |
|---|---|---:|---:|---:|---:|---|
| F-A | Phase 5 system prompt uses soft "Use ... sub-agent" — no MUST | High | Always | Low (visible in prompt) | High | Root |
| F-B | Tool inventory section advertises generators as `load_tools`-able to main agent | High | Always | Low | High | Misleads tool selection |
| F-C | content-check `phase_5` spec validates text only, not artifacts | High | Always | Low | High | Allows advance without files |
| F-D | Main agent's `task()` description is free-form; no Phase-5 dispatch template | Medium | Frequent | Medium | Medium | Lets agent ask for "moodboard" instead of Brand Key |
| F-E | `creative-studio` prompt biased toward direction drafts; Brand Key mentioned once | Medium | Frequent | Low | Medium | Even on Brand Key briefs, sub-agent may default to mood |
| F-F | `brand-communication-planning/SKILL.md:142` text instructs main agent to call `generate_spreadsheet` directly | Low | Always | Low | Low | Causes silent skip for KPI artifact only |
| F-G | Workspace notes are not synced with chat content (Phase 2 / Phase 5 missing in r6) | Low | Frequent | Low | Low | Doesn't block artifacts; pollutes resume |

The top-3 RPN failures (F-A, F-B, F-C) all sit on the orchestrator
boundary — main agent prompt + content-check gate. Sub-agent prompts
(F-D, F-E) are amplifiers; if the main agent dispatches with the right
description and the gate enforces artifact return, the sub-agent
defaults are visible enough to fix in a follow-up if needed.

## Recommended M-2 lever (single)

Apply the skill's **bottom-up rule**: validate sub-agents in isolation
before touching the orchestrator. We have no isolation harness for
sub-agents, so the practical equivalent is to send a **controlled
dispatch test** with a complete Phase-5 brief — i.e. force the main
agent to supply the right description and observe whether
`creative-studio` and `document-generator` actually produce files.

Three concrete options:

| Option | Lever | Pro | Con |
|---|---|---|---|
| 1 | Tighten content-check `phase_5` spec to require artifact `file_path` in recent `ToolMessage`s before advance | Mechanical enforcement; agent must dispatch | Doesn't tell agent **how**; risk of fail-loop |
| 2 | Promote Phase 5 system prompt actions from soft "Use ..." to MUST + concrete dispatch templates for both sub-agents | Tells agent intent + how | If agent ignores prompt, no enforcement |
| 3 | Both | Redundant — gate catches if prompt fails | Two changes at once breaks single-lever discipline |

Per single-lever discipline, **Option 2 first**. Rationale:
- It is the upstream cause (prompt soft language) — Option 1 (gate) is
  downstream enforcement that only forces retries.
- A clear MUST + dispatch template is reversible (single file edit) and
  cheap to test (one canary pilot).
- Kill criterion is well-defined: pilot artifact_audit must move from
  0/5 to ≥3/5 health, otherwise abandon Option 2 and try Option 1
  (M-2-prime).

If Option 2 alone produces ≥3/5 health → continue. If exactly 0
artifacts after pilot → root cause is not prompt language; M-2-prime
becomes Option 1 (gate at content-check) with Option 2 reverted.

## Open items for later milestones

- **F-B (tool inventory misleading)** — fix scheduled for M-2 alongside
  Option 2 prompt change because it is in the same file and the
  one-lever rule allows fixing the prompt holistically. If counted as
  a separate lever, defer to M-7-prep alongside other prompt cleanups.
- **F-E (creative-studio bias)** — defer until M-2 pilot data shows
  whether main-agent dispatch alone is sufficient. If sub-agent still
  defaults to mood despite explicit Brand Key brief, fix at M-2-bis.
- **F-F (`brand-communication-planning` skill `generate_spreadsheet`
  text)** — defer to M-2 fix because skill text and prompt language
  belong in the same change set if both touch the KPI path.
- **F-G (workspace persistence)** — out of scope for Tier 1. Address at
  M-7+ as a process-rule prompt fix.

## Verification plan for M-2

1. Apply Option 2 — system prompt Phase 5 mandate + dispatch template +
   tool inventory cleanup.
2. Pilot Linh repositioning (or new_brand) one full session.
3. Run `evaluation/artifact_audit.py --session-dir <pilot>` — record
   Tier 1 health.
4. Pass criterion: health ≥ 3/5 with at least Brand Key OR Strategy
   doc produced.
5. Fail criterion: health < 3/5 → revert Option 2, switch M-2-prime
   to Option 1 (content-check gate).
