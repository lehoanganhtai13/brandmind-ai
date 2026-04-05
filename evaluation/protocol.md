# BrandMind Evaluation Protocol

> This document is the complete guide for running the evaluation.
> Follow it step by step. Anyone with Claude Code and this repository can reproduce the results.

## Prerequisites

- BrandMind system running locally (`uv run brandmind`)
- API keys for 3 judge model providers (configured in environment or litellm)
- Access to ChatGPT and Gemini (web interface via Playwright, or API)

## 3 Systems to Evaluate

| # | System | Setup | Notes |
|---|--------|-------|-------|
| 1 | **BrandMind** | `uv run brandmind` (default config) | Full system with mentoring + personalization |
| 2 | **ChatGPT** | chat.openai.com (Playwright) or OpenAI API | Memory ON (default) — represents typical SME experience |
| 3 | **Gemini** | gemini.google.com (Playwright) or Gemini API | Memory ON (default) — represents typical SME experience |

**Why no ablation?** Mentoring and personalization are not modular components — they are emergent behaviors from the synergy of prompt + workspace + middleware + tools. Removing one creates confounded results (cascading degradation). Instead, the value of each is demonstrated through:
- **Personalization**: Cross-persona analysis — same system, different personas → different agent behavior
- **Mentoring**: Within-session analysis — scaffolding fading, user sophistication growth across phases

**Why baselines with memory ON?** This represents the real experience an SME gets today. Cross-session memory in vanilla chatbots only remembers generic facts — it does NOT provide structured workspace notes, domain-specific user profiling, or progressive scaffolding. The rubric criteria naturally catch these differences.

## 5 Personas

Read persona files in `evaluation/personas/` before each session:
- `linh.md` — Junior marketer, new_brand
- `minh.md` — Cafe owner, full_rebrand
- `thao.md` — Marketing manager, new_brand
- `hai.md` — Pho shop owner, refresh
- `huong.md` — Brand executive, repositioning

## Step-by-Step Protocol

### Step 1: Prepare Output Directory

For each session, create:
```
brandmind-output/eval/{system}_{persona}_{run#}_{date}/
```

Example: `brandmind-output/eval/brandmind_linh_r1_20260401/`

### Step 2: Run Session

1. Read the persona file thoroughly
2. Start the target system
3. Send the initial message (from persona file) and interact in character
4. Follow the persona's behavioral rules throughout
5. Continue until the session naturally concludes (brand strategy completed, or conversation exhausted)

**Per-system specifics:**

| System | How to run | Interaction method | Stop when |
|--------|-----------|-------------------|-----------|
| **BrandMind** | `uv run brandmind` | TUI in terminal | Phase 5 completed or agent wraps up |
| **ChatGPT** | chat.openai.com or OpenAI API | Playwright or API | Agent has covered positioning + identity + implementation, or conversation loops |
| **Gemini** | gemini.google.com or Gemini API | Playwright or API | Same as ChatGPT |

For baselines (ChatGPT/Gemini): use a simple opening prompt like the persona's initial message. Do NOT give them BrandMind's system prompt or phase structure — they should work with whatever they have by default (including their built-in memory if enabled).

### Step 3: Save Artifacts

After each session, save to the output directory:

1. **transcript.json** — Full conversation log (same format for ALL 3 systems):
   ```json
   {
     "persona": "linh",
     "system": "brandmind",
     "run": 1,
     "date": "2026-04-01",
     "turns": [
       {
         "turn": 1,
         "user": "Xin chào, em là marketing executive...",
         "agent": "Chào bạn, rất vui được hỗ trợ..."
       },
       {
         "turn": 2,
         "user": "Dạ để em chia sẻ về nhà hàng...",
         "agent": "Cảm ơn bạn đã chia sẻ chi tiết..."
       }
     ]
   }
   ```

   Notes:
   - **Same format for all 3 systems** — judges receive identical structure
   - Only `turn`, `user`, `agent` — no tool calls, no internal metadata
   - Judges evaluate conversation content as the user experiences it

2. **self_eval.json** — Answer questions from `evaluation/self_eval.md` (immediately after session, still in character)

3. **metadata.json** — Session info:
   ```json
   {
     "system": "brandmind",
     "persona": "linh",
     "run": 1,
     "date": "2026-04-01",
     "total_turns": 35
   }
   ```

### Step 4: Run Judge Evaluation

After ALL sessions are complete:

```bash
uv run python evaluation/judge/run_judges.py --session-dir brandmind-output/eval/brandmind_linh_r1_20260401/
```

This sends the transcript to 3 judge models via litellm and saves:
- `evaluation_results.json` — Per-criterion scores from each judge + Fleiss' Kappa

### Step 5: Aggregate Results

```bash
uv run python evaluation/judge/aggregate.py --eval-dir brandmind-output/eval/
```

Produces the final comparison table across all systems.

## Experiment Matrix

| Persona | BrandMind | ChatGPT | Gemini |
|---------|-----------|---------|--------|
| Linh    | r1, r2    | r1, r2  | r1, r2 |
| Minh    | r1, r2    | r1, r2  | r1, r2 |
| Thảo    | r1, r2    | r1, r2  | r1, r2 |
| Hải     | r1, r2    | r1, r2  | r1, r2 |
| Hương   | r1, r2    | r1, r2  | r1, r2 |

Total: 5 personas x 3 systems x 2 runs = **30 sessions**

## Analysis Methods (replace ablation)

### Cross-Persona Analysis → proves Personalization
Compare BrandMind's behavior across personas with different levels:
- Hải (complete beginner, no jargon) vs Thảo (intermediate, uses marketing terms) → agent should adapt communication level, scaffolding depth, and explanation style
- If scores on P4-G2 (behavior changes), P4-S1 (learning preference), P4-S2 (thinking pattern) are MET → personalization works

### Within-Session Analysis → proves Mentoring
Track progression within each session:
- Scaffolding fading: explanation depth in Phase 0-1 vs Phase 3-4
- User sophistication: compare user's language/thinking at session start vs end
- Mentor-executor ratio: teaching time in early phases vs late phases
- If M2-E1 (adjusts scaffolding), M3-S1 (user sophistication increases) are MET → mentoring works

## Future: Stress-Test Scenarios (Optional)

After standard evaluation, consider running edge-case scenarios to test robustness:

| Scenario | What to Test | How |
|----------|-------------|-----|
| Contradictory Input | User says "premium brand" but "budget = 10 trieu" | Add to persona behavioral rules |
| Ambiguous Brief | User gives vague 1-sentence brief with no details | Use as initial_message variant |
| Scope Creep | User keeps asking about unrelated topics mid-phase | Add to behavioral rules |
| Missing Critical Info | User refuses to share budget or competitors | Add to behavioral rules |
| Budget = 0 | User has no marketing budget at all | Modify Hai persona variant |

These are NOT part of the standard 30-session experiment — run separately if time permits.

## Reproducibility Checklist

- [ ] All persona files read before session
- [ ] Exact model versions recorded in metadata.json
- [ ] Date of each session recorded
- [ ] Vanilla baselines have NO custom instructions
- [ ] Self-eval completed immediately after session (not retroactively)
- [ ] Judge evaluation uses same rubric version for all sessions
