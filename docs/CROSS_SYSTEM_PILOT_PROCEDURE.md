# Cross-System Pilot Procedure

> This document specifies how to drive eval pilots across BrandMind, ChatGPT vanilla, and Gemini vanilla so that the B (Strategic Coherence) and C (Strategic Problem-Solving) judges score each system fairly. It implements Phase C of the eval methodology overhaul plan (`eval_methodology_overhaul_plan_2026_05_03.md`). The procedure preserves cross-system fairness by holding the simulated user constant across systems — same persona, same natural behavior pattern, same questions — so any difference in B/C scores reflects what each system delivers to that user, not how the pilot driver primed each system.

## 1. Goal & Scope

The B/C judges evaluate chat transcripts on Strategic Coherence (does the strategy hang together) and Strategic Problem-Solving (does it solve the diagnosed problem within stated constraints). For the thesis to defend "BrandMind delivers strategic substance that vanilla baselines do not", the comparison must hold input constant across systems and let differences in chat output emerge from actual system capability. This document specifies the input-holding discipline: persona behavior, question patterns, follow-up cadence, accept criteria, skip-artifact rule, and per-system execution mechanics.

Cross-system fairness here is a stricter commitment than "use the same rubric on each system". It is also "use the same simulated user behavior on each system". Without the second commitment the rubric scores measure pilot-driver engineering, not system value to the user. Sections 3 through 5 spell out the user-behavior commitment; Sections 6 through 8 spell out the operational commitments (skip-artifact, pitfalls, reproduction).

Out of scope: the persona definitions themselves (already in `evaluation/personas/`), the rubric definitions (in `docs/B_C_JUDGE_METHODOLOGY.md`), and the Phase D-1 / D-2 execution runs (separate docs). This document covers only the procedure for driving any one pilot across the three systems with the same persona.

## 2. Theoretical Foundation

The procedure is grounded in three commitments drawn from `north_star_principles_2026_05_03.md` Section 3 and from the thesis claim layer documented in `docs/B_C_JUDGE_METHODOLOGY.md` Section 1.

**Simulate natural real-world use, not eval-friendly use.** The pilot driver imitates what a real user (the persona) would actually do when sitting down with a brand-strategy assistant. It does not steer the conversation toward the rubric's surfaces. If the persona would naturally ask about visual design rationale, the script asks; if she would not, the script does not — even if the rubric has a B6 criterion that depends on visual rationale appearing in the transcript. The system's score on B6 then reflects whether the system volunteered the rationale to a user who did not know to ask. That is the substantive capability the thesis claims BrandMind has and vanilla does not.

**Hold input constant across systems; let output differences emerge.** The same persona drives BrandMind, ChatGPT vanilla, and Gemini vanilla with the same conversational pattern — same opening, same follow-ups, same acceptance behavior. Any difference in B/C scores therefore reflects what each system produced when given identical user input from identical user mental model. This is the standard fairness commitment in cross-system LLM evaluation; departures from it (e.g. injecting expert-framed elicitation prompts only into the vanilla driving script to "give vanilla a chance" to narrate equivalent reasoning) inflate vanilla scores by simulating an expert user when the target user is junior.

**Preserve the cross-persona signal.** The five personas in `evaluation/personas/` differ in domain expertise, LLM familiarity, role, and natural questioning style. A junior marketing executive (linh) does not ask the same questions as a brand executive (huong). Forcing all five personas to use the same Linh-style script collapses the cross-persona signal that the personalization dimension of the thesis claim depends on. Each persona drives the conversation in the way that persona naturally would; the pilot script is a per-persona artifact, not a one-size-fits-all template.

A practical corollary distinguishes the eval-friendly pitfall from the natural-simulation discipline. Eval-friendly driving asks "which persona-side question maximizes the rubric criteria's chance to score?" — the answer often involves expert-framed prompts the persona would not naturally use. Natural-simulation driving asks "what would this persona actually say next given the conversation so far and her own mental model?" — the answer follows from the persona spec, not from the rubric. The two questions converge when the persona is an expert (e.g. huong might naturally ask about visual rationale), and they diverge when the persona is junior (e.g. linh would not). The procedure follows the natural-simulation question in every case.

## 3. Persona-natural-behavior framework

Each persona is characterized along five dimensions that determine her natural conversation pattern. Persona files in `evaluation/personas/` carry the role + business + behavioral rules + initial message; this section adds the cross-system dimensions that determine how she would interact with a generic LLM chat product like ChatGPT or Gemini.

**LLM-knowledge level** — what she knows about how ChatGPT/Gemini work. Low-knowledge users treat the chat as "a smart assistant who can answer anything" with no awareness of prompt engineering, system prompts, or expert prompting techniques; they ask in plain language and follow up only when confused. Medium-knowledge users have some awareness that "asking better questions gets better answers" but rarely use formal prompt patterns; they may push back with a "vì sao?" or "cụ thể hơn" but not with structured elicitation. High-knowledge users (rare in the SME target population) know prompt engineering basics and may use formal patterns.

**Domain expertise** — depth of brand strategy knowledge. A junior marketing executive understands tactical execution but is weak on strategic frameworks; she accepts strategic deliverables without auditing them. A senior marketing manager has frameworks; she pushes back when something does not match what she has done before. A small business owner has no marketing training; she frames questions around business outcomes (sales, customers, costs) rather than marketing concepts. A brand executive has full framework fluency; she audits aggressively.

**Question depth** — basic / intermediate / advanced. Basic = "anh giúp em làm brand strategy được không?" + "vậy quán em nên dùng màu gì?". Intermediate = "positioning này có khác biệt với competitor X không?" + "KPI này đo được gì cụ thể?". Advanced = "trình bày visual design rationale + linkage to brand promise + audience" + "ROI math với CAC vs LTV breakdown".

**Push-back tendency** — passive accept / occasional push-back / active audit. Passive accept = takes the system's first answer and moves on. Occasional push-back = pushes when confused or skeptical. Active audit = challenges every major decision with framework-grounded follow-up.

**Vietnamese register** — junior staff (em xưng "em", anh/chị xưng "anh/chị", casual professional), business owner (em / mình mixed, pragmatic + tactical), executive (mình / tôi, formal + analytical).

The five-dimension framework lets each persona's natural-behavior spec (Section 4) sit at a defined point in the design space, so cross-persona signal is preserved without requiring exhaustive per-persona script authorship.

## 4. Per-persona behavior specs

Each persona's natural conversation behavior across all three systems. The spec is descriptive — it summarizes what the persona file already encodes plus the LLM-knowledge dimension that the persona file does not encode. The pilot driver script for each persona is generated from this spec; no other behavior should appear in the driver.

### 4.1 Linh — junior marketing executive, new_brand

| Dimension | Value |
|---|---|
| LLM knowledge | Low — uses ChatGPT for occasional copywriting help, no prompt engineering awareness |
| Domain expertise | Junior — 1 year tactical experience, weak framework theory |
| Question depth | Basic — "anh giúp em..." + occasional "vậy cụ thể quán em..." |
| Push-back tendency | Passive accept with curious "tại sao?" every 2-3 turns when confused |
| Vietnamese register | Junior staff — "em / anh", casual professional, expressive |

Natural with vanilla: opens with "anh giúp em làm brand strategy được không, em mới làm 1 năm chưa rành lắm". Accepts vanilla's structured output (positioning + channels + KPIs). Asks "tại sao?" when a concept is unfamiliar. Does not ask about visual rationale linkage to brand promise — that framing is not in her vocabulary. Does not audit ROI math. Accepts "đây là brand strategy của em" and moves on.

### 4.2 Minh — cafe owner, full_rebrand

| Dimension | Value |
|---|---|
| LLM knowledge | Low — has heard of ChatGPT but uses it rarely, may try once for brand work |
| Domain expertise | Non-marketer — small business owner, frames everything around revenue + customer count |
| Question depth | Basic — "làm sao tăng khách?" + "tốn bao nhiêu tiền?" |
| Push-back tendency | Pragmatic push-back on cost + feasibility, passive on framework |
| Vietnamese register | Business owner — "em / mình / tôi" mixed, tactical + pragmatic |

Natural with vanilla: opens with the business problem in colloquial language ("quán em mới được 2 năm, doanh thu giảm 20% mấy tháng nay, em muốn rebrand"). Asks about cost + execution feasibility ("cái này tốn bao nhiêu?", "ai làm được cái đó?"). Does not engage with archetype frameworks; if the system uses one, she may say "anh giải thích lại đi em không hiểu". Accepts strategy presented as revenue plan; rejects strategy that is too abstract or expensive.

### 4.3 Thao — marketing manager, new_brand

| Dimension | Value |
|---|---|
| LLM knowledge | Medium — uses ChatGPT regularly for brainstorming + copy + research, knows "ask better questions" |
| Domain expertise | Senior marketer — has run campaigns + knows STP/4P/positioning frameworks |
| Question depth | Intermediate — "positioning này khác biệt với competitor X như thế nào?", "KPI này đo gì?" |
| Push-back tendency | Occasional push-back when an answer doesn't match her experience |
| Vietnamese register | Senior staff / mid-management — "mình / em" mixed, professional confident |

Natural with vanilla: opens with both business and marketing context ("brand đang launch, target office workers Q1, em đã làm market research"). Probes positioning differentiation, channel mix logic, KPI causality at intermediate level. Pushes back when a recommendation conflicts with her past experience ("hồi em làm campaign tương tự, channel TikTok không hiệu quả với segment này"). Stops short of demanding visual design rationale or full ROI math — those are not in her usual deliverable scope.

### 4.4 Hai — pho shop owner, refresh

| Dimension | Value |
|---|---|
| LLM knowledge | Low — uses ChatGPT once or twice, treats it like Google with conversation |
| Domain expertise | Non-marketer — small shop owner, framework awareness near zero |
| Question depth | Basic — "khách ít, làm sao đông lên?" |
| Push-back tendency | Pragmatic push-back on local feasibility ("khu em không có người làm cái đó") |
| Vietnamese register | Small business owner — "em / mình / tui" relaxed, short responses |

Natural with vanilla: opens in colloquial language ("quán phở em mở 8 năm, gần đây có 2 quán phở mới mở cách 300m, khách giảm dần"). Responses are short and concrete, often skipping framework discussion. Asks about visible action ("vậy em phải làm gì?") rather than concept. Accepts simple plans; rejects plans that name skills or vendors she does not have access to in her area.

### 4.5 Huong — brand executive, repositioning

| Dimension | Value |
|---|---|
| LLM knowledge | Medium-high — uses ChatGPT + Gemini regularly for strategic work, knows context engineering basics |
| Domain expertise | Senior brand professional — Aaker, Keller, Trout-Ries, Sharp DBA, full framework fluency |
| Question depth | Advanced — pushes for visual rationale, ROI math, sếp Q&A defense, competitive positioning vs named players |
| Push-back tendency | Active audit — challenges most strategic recommendations with framework-grounded follow-up |
| Vietnamese register | Executive — "mình / tôi" formal, analytical |

Natural with vanilla: opens with executive context ("đang tái định vị brand X, segment Y, vs competitor Z, ngân sách tier A, deadline B"). Asks for visual rationale linkage ("color palette logic và linkage to brand promise như thế nào?"), KPI methodology depth ("baseline + target + cadence + linkage to problem"), ROI math ("CAC vs LTV ratio?"), stakeholder defense ("sếp board sẽ hỏi câu nào và mình defend ra sao?"). Pushes back when answers are surface-level ("thiếu strategic ground, anh trình bày thêm Aaker brand identity prism mapping được không?"). Accepts answers only when they are framework-grounded and defendable to her board.

The huong-natural-behavior overlaps with what the eval-friendly elicitation script would have looked like for vanilla. This is not coincidence — it reflects that an expert user does naturally elicit the substance the rubric measures. The cross-persona signal that separates huong's expected vanilla score from linh's expected vanilla score is exactly the signal the rubric is designed to capture: vanilla can produce strategic substance when an expert user knows to ask, and cannot when a junior user does not. Forcing linh's persona to ask huong's questions would erase this signal.

## 5. Standardized driving script

The pilot driver runs each persona through the brand-strategy session in a standardized arc: opening message → phase 0 problem framing → phase 1 research follow-up → phase 2 positioning + identity → phase 3 communication + KPI → close. The arc structure is identical across systems for the same persona; only the per-persona behavior changes the per-turn message content.

### 5.1 Arc per session

| Turn | Persona action | Vanilla expected behavior | BrandMind expected behavior |
|---|---|---|---|
| 1 | Initial message (from persona file) | Acknowledge + ask diagnostic questions | Phase 0 framing + 5W1H questions |
| 2–3 | Answer diagnostic + share business context | Synthesize into positioning + identity | Phase 1 research + advance to Phase 2 |
| 4–6 | Per-persona engagement (curious / pragmatic / probe) | Provide structured deliverables (positioning + archetype + channels + KPIs) | Per-phase Mentor Cycle with native rationale narration |
| 7–8 | Per-persona accept / push-back | Iterate or close | Advance phase or close |
| 9 | Per-persona close acknowledgement | "Đây là strategy của em" or equivalent | Phase 5 close + dispatch trigger (skipped per Section 6) |

The vanilla "expected behavior" column is what the LLM is likely to do given a standard user flow; it is not a script the pilot driver imposes. The persona simply asks her natural questions and accepts what comes back.

### 5.2 Per-persona script files

Each persona's script lives at `evaluation/pilot_scripts/<persona>.md` (to be authored as part of Phase D-1 #7 + Phase D-2 execution; the spec for each script is in Section 4 above). Each script file lists the per-turn user messages with branching for different system responses, but the branching always preserves the persona's natural behavior.

The script must NOT contain prompts the persona would not write. If the script ever needs to add a question to elicit a rubric criterion, that is a signal the persona spec is wrong, not that the script needs more elicitation injected — revise the persona dimensions instead. This rule is the operational form of the "natural simulation, not eval-driven driving" commitment.

## 6. Skip-artifact-generation rule

For all eval pilots in Phase D-1 + Phase D-2, artifact generation is skipped. BrandMind sessions stop at Phase 5 closure narration without dispatching to creative-studio or document-generator. Vanilla sessions stop when the system has presented its strategy in chat without being asked to "create the deliverable file".

The rationale is mechanical, not optimization: the B and C judges do not read artifact content (`coherence_judge.py` and `problem_solving_judge.py` only read `transcript.json` user/agent fields per source code). Artifact bytes are not in the judge input. Skipping artifact generation therefore mathematically cannot affect judge scores; the only effect is reducing pilot wall-clock time and token spend.

Verification of the no-effect property is rationale-based rather than empirical — the judge code is open-source and auditable, and the absence of artifact-reading code is verifiable by `grep` or by reading the `_format_transcript_for_judge` and `_load_transcript_data` functions. An empirical run comparing transcripts with and without artifact generation would not surface a difference because the judges receive identical input bytes either way; the empirical run would only confirm what the source code already proves.

The skip-rule applies specifically to eval pilots driven for B/C judging. It does not apply to system smoke tests (`make eval-smoke`) or to Tier 1 artifact production verification (`evaluation/artifact_audit.py`) which both require artifacts to exist.

## 7. Common pitfalls + safeguards

The procedure has documented pitfalls because each one was identified during Phase C design as a temptation that would compromise cross-system fairness. The safeguards are operational rules that prevent the pitfall.

**Pitfall — Eval-friendly driving.** The rubric has criteria the persona would not naturally exercise (e.g. linh would not ask for visual rationale linkage). The temptation is to inject expert-framed elicitation prompts into the persona's script "to give the system a chance to score" on those criteria. **Safeguard**: the persona spec is the source of truth for what the persona says; if the script ever needs a prompt that conflicts with the spec, revise the spec or accept the rubric score that emerges from natural behavior. Never inject elicitation prompts after spec is written.

**Pitfall — Cross-system asymmetric scripting.** The temptation is to write different scripts for BrandMind vs vanilla under the rationale that each system "needs different prompts to surface its capability". This collapses fairness — the system difference becomes confounded with the script difference. **Safeguard**: the same persona script is consumed by all three system drivers. System differences emerge in the output, not the input.

**Pitfall — Unconscious eval contamination during driver authoring.** The author of the per-persona script knows the rubric criteria and may unconsciously write persona turns that hit the criteria, even when intending natural behavior. **Safeguard**: author scripts before reading the rubric; if reading the rubric is unavoidable, run a self-review pass asking "would this exact turn appear if I had never seen the rubric?" — delete any turn that fails this test.

**Pitfall — System-side inducement.** During execution, when a system responds in a way that does not advance the conversation (e.g. asks back-and-forth questions instead of presenting), the temptation is to "help" the system by paraphrasing the persona's question more clearly. This is also a form of eval-friendly driving. **Safeguard**: persona repeats the original question or moves on per persona's natural patience level; the system's failure to advance is itself part of the comparison.

**Pitfall — Persona drift across runs.** Running the same persona pilot twice may produce different driver behavior if the author is improvising. **Safeguard**: persona scripts are authored once, checked into `evaluation/pilot_scripts/`, and re-used across runs. Changes to scripts require single-concern commits with rationale.

## 8. Reproduction commands

Pilot execution differs by system on transport but is identical on persona script.

### 8.1 BrandMind pilot

```bash
# Activate venv + start server
source .venv/bin/activate
brandmind serve &  # or: uv run brandmind

# Wait for ready
curl http://localhost:8000/api/v1/health

# Drive pilot via existing pilot driver against persona script
python evaluation/eval_session.py \
  --persona linh \
  --system brandmind \
  --output-dir brandmind-output/eval/brandmind_linh_<run>_<date>/

# Score with B + C judges
uv run --env-file environments/.env python evaluation/judge/coherence_judge.py \
  --session-dir brandmind-output/eval/brandmind_linh_<run>_<date>/
uv run --env-file environments/.env python evaluation/judge/problem_solving_judge.py \
  --session-dir brandmind-output/eval/brandmind_linh_<run>_<date>/
```

### 8.2 ChatGPT vanilla pilot

```bash
# Drive via Playwright with user-provided login
python evaluation/eval_session.py \
  --persona linh \
  --system chatgpt \
  --browser-profile <user-chatgpt-profile> \
  --output-dir brandmind-output/eval/chatgpt_linh_<run>_<date>/

# Score with same B + C judges (rubric is system-agnostic)
uv run --env-file environments/.env python evaluation/judge/coherence_judge.py \
  --session-dir brandmind-output/eval/chatgpt_linh_<run>_<date>/
uv run --env-file environments/.env python evaluation/judge/problem_solving_judge.py \
  --session-dir brandmind-output/eval/chatgpt_linh_<run>_<date>/
```

### 8.3 Gemini vanilla pilot

```bash
# Drive via Playwright with user-provided login
python evaluation/eval_session.py \
  --persona linh \
  --system gemini \
  --browser-profile <user-gemini-profile> \
  --output-dir brandmind-output/eval/gemini_linh_<run>_<date>/

# Score with same B + C judges
uv run --env-file environments/.env python evaluation/judge/coherence_judge.py \
  --session-dir brandmind-output/eval/gemini_linh_<run>_<date>/
uv run --env-file environments/.env python evaluation/judge/problem_solving_judge.py \
  --session-dir brandmind-output/eval/gemini_linh_<run>_<date>/
```

The Playwright pilot driver for vanilla baselines is itself a Phase D-2 prerequisite (currently not built). For Phase D-1 #6 (re-score r10–r13) the driver is not needed because the transcripts already exist; for Phase D-1 #7 (fresh BrandMind pilot post Phase A) only the BrandMind pilot path applies.

## 9. Outputs + downstream usage

The procedure produces, per pilot run:

- `transcript.json` — turn-by-turn user/agent messages, the source of truth for B + C judge input
- `metadata.json` — persona id, system id, run number, date, system version (commit hash for BrandMind, model id + UI snapshot date for vanilla), driver-script-version
- `self_eval.json` — pilot driver's first-hand assessment of the session, parallel triangulation per `feedback_self_assess_after_session.md`
- `coherence_judge.json` and `problem_solving_judge.json` — B and C judge verdicts per criterion + scores

Downstream uses:

- **Phase D-1 #6** — re-score r10–r13 BrandMind transcripts with B + C judges; transcripts already exist (not driven by this procedure) but the scoring step uses the same judges this procedure assumes. Outputs feed the methodology-overhaul comparison report.
- **Phase D-1 #7** — fresh BrandMind pilot for linh persona post Phase A behaviour-verify; uses BrandMind path only.
- **Phase D-2 #8** — cross-persona pilot for minh, thao, hai, huong on BrandMind; scales the BrandMind path to the four other personas.
- **Phase D-2 #9** — vanilla baseline pilots on ChatGPT + Gemini for all five personas; activates the Playwright path for the first time.

The combined-score formula (`evaluation/judge/run_methodology_overhaul.py` per `resume_cue_2026_05_03_eval_overhaul.md` draft) is `0.30 * chat_process_avg + 0.30 * B_score + 0.30 * C_score + 0.10 * self_eval_avg`. The chat_process_avg comes from the existing 3-judge pipeline applied to the same transcript; B_score and C_score come from this procedure's outputs; self_eval_avg comes from the parallel triangulation.

## 10. References

Primary procedure artifacts (in this repository):

- `evaluation/personas/*.md` — five persona definitions (character + business + behavioral rules + initial message)
- `evaluation/protocol.md` — pre-existing eval protocol for the chat rubric (this document is the cross-system layer)
- `evaluation/eval_session.py` — pilot driver harness (BrandMind path complete; vanilla path Phase D-2 prerequisite)
- `evaluation/judge/coherence_judge.py` — B Strategic Coherence judge
- `evaluation/judge/problem_solving_judge.py` — C Strategic Problem-Solving judge
- `docs/B_C_JUDGE_METHODOLOGY.md` — B/C judge design + isolation test results
- `docs/JUDGE_CALIBRATION_METHODOLOGY.md` — chat rubric calibration methodology (parallel methodology for the surface-behavior layer)

Project context (referenced for grounding):

- `eval_methodology_overhaul_plan_2026_05_03.md` — A-D plan; this document implements Phase C
- `north_star_principles_2026_05_03.md` — eval philosophy + cross-system fairness commitment + honest-measurement target
- `feedback_self_assess_after_session.md` — self-eval triangulation discipline
- `feedback_dont_drift_plan.md` — plan-discipline reminder

Commit history:

- `200e361` — B/C judge anchoring strengthening (final B-judge alignment 51/60 = 85.0%)
- `8abfdf7` — B/C methodology doc
- `ab8effa` — Phase B Step 3 (C judge)
- `23406c1` — Phase B Step 2 (B judge)

Tasks:

- Task #71 — this Phase C procedure document (completed)
