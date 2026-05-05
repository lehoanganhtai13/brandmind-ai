# Evaluation Methodology Summary
## Luận văn Thạc sĩ Ứng dụng

**Đề tài**: Personalized Multi-Agent Mentor for Brand Strategy Development cho F&B SMEs in Vietnam.

**Target user**: Junior marketer (~1 năm kinh nghiệm) làm trong F&B SME — người thiếu kinh nghiệm, không nắm quy trình tổng quát, dù có nhiều AI tools nhưng không biết dùng cái nào cho cái nào.

**Core concept**: Agent cùng user phát triển brand strategy theo hướng mentor — Cognitive Apprenticeship arc (Modeling → Coaching → Scaffolding → Articulation → Genuine Inquiry, Collins/Brown/Holum 1991) + Socratic Partnership tone (Neenan 2008). Senior executor narrates design rationale before delegating to specialists.

**3 trục đánh giá đa-tầng**:
- Strategy Quality (Q): chất lượng chiến lược thương hiệu
- Mentor Quality (M): chất lượng dẫn dắt
- Personalization (P): mức độ cá nhân hoá theo persona

**Updated 2026-05-05** sau eval methodology overhaul: thêm B (Strategic Coherence) + C (Strategic Problem-Solving) judges để đánh giá per-dimension chuyên sâu.

---

## 1. Baselines

### External Baselines (cross-system fairness commitment)
- **ChatGPT (memory ON, default config)** — đại diện cho trải nghiệm thực tế phổ biến của SME khi tiếp cận AI hiện tại. Memory ON vì đó là default, không cố tình nerf baseline.
- **Gemini (memory ON, default config)** — tương tự.
- **Driving methodology**: cùng disciplined-script persona-driver gửi identical messages đến BrandMind và 2 vanilla baselines. Cross-system fairness commitment chi tiết tại `docs/CROSS_SYSTEM_PILOT_PROCEDURE.md`.

### Tại sao không Ablation Baselines?
Mentoring và personalization của BrandMind **không phải modular components** — chúng là emergent behaviors từ synergy của prompt + workspace + middleware + tools. Ablation (bỏ từng component) tạo confounded results (cascading degradation). Thay vào đó:
- **Personalization**: Cross-persona analysis — cùng system, khác persona → khác behavior agent
- **Mentoring**: Within-session analysis — scaffolding fading + user sophistication growth across phases

### Bảng kết quả final (per persona): 3 systems
| # | System | Mục đích so sánh |
|---|---|---|
| 1 | BrandMind (full system) | Target system với mentoring + personalization |
| 2 | ChatGPT vanilla (memory ON) | External baseline #1 |
| 3 | Gemini vanilla (memory ON) | External baseline #2 |

5 personas × 3 systems × 2 runs = **30 sessions** matrix (per `evaluation/protocol.md`).

---

## 2. Evaluation Framework — multi-judge architecture

### 2.1 Chat rubric — 3-judge cross-judge panel

**3 SOTA judges**: Claude Sonnet 4.6, Gemini 3.1 Pro, GPT 5.4. Đọc conversation transcripts sau session, chấm theo rubric 104 criteria + 10 anti-patterns (`docs/BRANDMIND_EVAL_RUBRIC.md`).

**Calibrated**: judges đã được calibrated qua golden-anchor methodology (`docs/JUDGE_CALIBRATION_METHODOLOGY.md`). Phase 4 hold-out validation: Claude 100% / Gemini 90.9% / GPT 100% alignment vs golden, cross-judge Kappa 0.319 → 0.592 (Fair → Moderate).

**Combined chat dimension**:
- Q (Strategy Quality, 50% weight)
- M (Mentor Quality, 30% weight)
- P (Personalization, 20% weight)
- **Quality gate**: Q < 7 → cap chat overall ≤ 6.0

### 2.2 B (Strategic Coherence) judge — single LLM per dimension

**12 criteria** đánh giá internal consistency của brand strategy parts: từ Phase 0 problem statement đến Phase 5 deliverables. Đặc biệt **B7** (DOCX dispatch design rationale visible in chat) và **B8** (PPTX dispatch design rationale visible in chat) đo per-artifact narration tại Phase 5 closure surface.

**Single Gemini 3.1 Pro judge** (Path X architecture) — không cross-judge averaging vì subjective reasonableness của coherence không cần multi-judge consensus. Synthetic isolation test 50/60 = 83.3% kill gate PASS với golden anchors. Detail tại `docs/B_C_JUDGE_METHODOLOGY.md`.

### 2.3 C (Strategic Problem-Solving) judge — single LLM per dimension

**10 criteria** đánh giá external effectiveness — strategy có thực sự solve diagnosed problem không. Bao gồm C6 (risk/contingency), C8 (budget/break-even math), C9 (stakeholder defensibility) — những criteria quan trọng cho thesis claim về substantive differentiation.

**Single judge**, synthetic isolation test 41/50 = 82.0% kill gate PASS.

### 2.4 Self-evaluation — first-hand persona experience

Persona-driver (Claude Code đóng vai Linh / Minh / Thảo / Hải / Hương) self-evaluate ngay sau session, in character, theo canonical schema `scores_1_to_10` với 3 dimensions. Capture perceived experience không derivable từ transcript alone (xem `evaluation/self_eval.md`).

### 2.5 Combined score formula

```
combined = 0.30 · chat + 0.30 · B + 0.30 · C + 0.10 · self_eval
```

- Chat (calibrated, capped) covers 104-criterion conversation quality
- B + C cover dimension-specific outputs (coherence, problem-solving)
- Self-eval triangulates perceived experience

### 2.6 N=3 trial protocol cho B + C judges

B và C judges chạy 3 trials per pilot trên cùng transcript. Trial mean ± std measures determinism: B mean std ≤ 0.5, C mean std ≤ 0.5 = stable signal (per Phase D-1 #6 viability gate).

### 2.7 Decision gate (post-D-1 #6 calibration)

**stability_ok**: B mean trial std ≤ 0.5 AND C mean trial std ≤ 0.5
**range_ok**: 5.0 ≤ combined ≤ 8.5 (principled range per formula structure)
**cluster_spread**: informational only, not a hard gate (cross-pilot variation is interpretive)

Detail orchestration script: `evaluation/judge/run_methodology_overhaul.py`.

---

## 3. Persona-driver — 5 personas

Persona files: `evaluation/personas/{linh,minh,thao,hai,huong}.md`.

| Persona | Role | Scope | Level |
|---|---|---|---|
| Linh | Marketing executive, 1 năm kinh nghiệm | new_brand | Junior |
| Minh | Cafe owner | full_rebrand | F&B owner, no marketing background |
| Thảo | Marketing manager | new_brand | Intermediate |
| Hải | Phở shop owner | refresh | Complete beginner, no marketing jargon |
| Hương | Brand executive | repositioning | Senior, strategic vocab |

### Persona-as-outsider driving discipline

Persona là **first-time user from outside** BrandMind, không phải system's builder. Even seasoned personas (Hương, Thảo) using BrandMind for the first time KHÔNG biết: internal phase names (`phase_0`), middleware terms (`dispatch sub-agents`, `task()`), theorist names at-once, framework names trước khi agent introduces, file-format technical names.

**Discipline rules** (canonical at `CLAUDE.md` § Persona-as-Outsider Driving Discipline):
1. Echo-back rule: persona dùng framework term CHỈ SAU khi agent cite trong prior turn
2. Vietnamese-natural deliverable names ("file chiến lược / slide cho sếp / bảng KPI / Brand Key tóm tắt")
3. Tactical questions từ outsider view
4. Never speak system-internal terms
5. Pre-write turn-by-turn script với explicit AVOID list trước khi drive

**Methodology disclosure**: r10–r14b pilots driven under contaminated methodology (persona-driver leaked jargon). r15 v2 onwards under disciplined methodology. Detail và implications: `docs/THESIS_FINDINGS.md` § Finding 3.

---

## 4. Pilot procedure (per pilot)

1. Pre-flight: Milvus up + workspace cleanup + server kill+restart
2. Init session dir: `brandmind-output/eval/{system}_{persona}_{run}_{date}/`
3. Drive persona theo pre-written disciplined script (~9 turns Phase 0→5)
4. Save 4 mandatory artefacts:
   - `transcript.json` — full turn-by-turn (same format all 3 systems)
   - `metadata.json` — system + persona + run + date + turn stats + agent state at pilot
   - `self_eval.json` — canonical `scores_1_to_10` schema, parses non-zero
   - `evaluation_results.json` — chat-rubric output (BrandMind only)
5. Run methodology overhaul: `evaluation/judge/run_methodology_overhaul.py --pilots <pilot> --n-trials 3`
6. Compare to baseline + decide next step

**4-artefact mandatory rule** at `CLAUDE.md` § Eval Pilot Driving Discipline. Skipping self-eval = permanent 0.10-weight gap, không back-fill được.

---

## 5. Key empirical findings

Detail tại `docs/THESIS_FINDINGS.md` (research-paper style, 3 findings) và `docs/THESIS_RESULTS.md` (7-pilot score table + per-criterion analysis).

**Headline**: Phase A v2 surgical edit at Phase 5 dispatch surface (commit `7a66d50`) lifted **B7** (DOCX dispatch narration) from FLAT-INCOHERENT × 6 prior pilots to PARTIAL × 3 trials, và **B8** (PPTX dispatch narration) to FULL COHERENT × 3 trials, on r15 v2 disciplined-script pilot. r15 v2 combined 7.18 (best disciplined methodology).

**Bisect attribution chain** validated layer separation principle empirically: identity-level edit (Phase A v1) insufficient × 6 pilots; action-surface edit (Phase A v2) achieved lift in 1 pilot.

---

## 6. Reproducibility

- **Exact model versions**: BrandMind agent uses `gemini-3-flash-preview` thinking=high. Judges are `claude-sonnet-4.6` (Anthropic), `gemini-3.1-pro-preview` (Google), `gpt-5.4` (OpenAI), all temperature 1.0 via LiteLLM proxy
- **Calibrated rubric version**: Step 4-bis Phase 4 validated (commit `663b41f`). Methodology doc at `docs/JUDGE_CALIBRATION_METHODOLOGY.md`
- **Disciplined persona scripts**: pre-written per pilot, archived in `brandmind-output/eval/<pilot>/build_transcript.py` (USER_MESSAGES list)
- **Date stamping**: each pilot folder named with date; metadata.json includes ISO timestamp
- **Replay**: chạy lại methodology overhaul script trên existing transcripts cho B/C judges (chat rubric calibrated re-run yêu cầu cache invalidation per Concern #1 fix in commit `b120474`)

---

## 7. Limitations + future work

### Limitations
- **Methodology contamination on r10-r14b**: 6 pilots jargon-contaminated, results indicative không apples-to-apples vs vanilla baselines (Phase D-2 #9). Disciplined r15 v2 + future runs là baseline thesis claim
- **Single Linh persona** for r15 v2: cross-persona generalization (Task #82) chưa verified
- **No vanilla baseline data yet** (Task #83): thesis claim "BrandMind delivers strategic substance vanilla LLMs cannot" awaits comparison
- **Real user case study** không pursued: simulation-only thesis, real user validation acknowledged as future work
- **C-dimension flat across pilots**: Phase A v2 specifically targets B7/B8, không touched C-criteria (C6 risk / C8 ROI math / C9 stakeholder defensibility) — separate lever for future work
- **Combined plateau ~7.0–7.5 disciplined**: per north-star honest-measurement update, fair-measured 6.0–6.5 acceptable; thesis claim pivots to B/C lift + cross-system delta thay vì chasing chat 7.5 absolute

### Future work
1. Cross-persona pilots (Task #82) — Minh, Thảo, Hải, Hương on r15 v2 stack
2. Cross-system vanilla baselines (Task #83) — ChatGPT + Gemini via Playwright, thesis-critical
3. C-dimension lift levers (Phase A v3 or M-7-F architectural fallback) — for C6 / C8 / C9 improvement
4. Real-user case study with 2-3 actual junior marketers — Tier 2 qualitative validation
5. Necessary condition determinism (Task #43) — smoke n≥3 cross-scope artifact production

---

## 8. Justify với hội đồng

> "Đây là luận văn Thạc sĩ Ứng dụng giải quyết bài toán đặc thù: junior marketers ở F&B SMEs Việt Nam thiếu mentoring + personalization khi tiếp cận AI tools hiện tại. BrandMind là multi-agent system với mentoring + personalization là emergent behaviors. Vì các khía cạnh này không phải modular components, ablation baselines tạo confounded results — thay vào đó, baselines được thiết kế là vanilla LLM (ChatGPT, Gemini) đại diện cho cách phổ biến SME hiện đang dùng AI."
>
> "Evaluation sử dụng calibrated 3-judge cross-judge panel cho chat rubric (104 criteria, calibrated với golden-anchor methodology, Kappa 0.592 Moderate), bổ sung bởi 2 single-LLM-per-dimension judges (B Strategic Coherence + C Strategic Problem-Solving) cho chuyên sâu coherence và problem-solving. Combined score formula tích hợp 4 inputs (chat 0.30 + B 0.30 + C 0.30 + self-eval 0.10) cho holistic assessment. Cross-system fairness committed via disciplined persona-driver script identical across 3 systems."
>
> "Empirical evidence từ 7-pilot Linh series (r10–r15 v2) verifies layer separation principle empirically: Phase A v2 surgical edit at action surface (Phase 5 dispatch templates) lifted B7+B8 dispatch narration from FLAT-INCOHERENT × 6 prior pilots to PARTIAL/COHERENT, while equivalent identity-surface edit (Phase A v1) was insufficient. Bisect attribution methodology validates dedup-vs-no-dedup contribution (-0.53 combined regression on dedup). Cross-persona generalization và cross-system vanilla comparison là remaining work."

---

## 9. References

- `docs/THESIS_FINDINGS.md` — research findings detail
- `docs/THESIS_RESULTS.md` — full pilot score table + per-criterion analysis
- `docs/B_C_JUDGE_METHODOLOGY.md` — B + C judge framework
- `docs/JUDGE_CALIBRATION_METHODOLOGY.md` — chat rubric calibration
- `docs/CROSS_SYSTEM_PILOT_PROCEDURE.md` — cross-system fairness procedure
- `docs/BRANDMIND_EVAL_RUBRIC.md` — 104 chat-rubric criteria + 10 anti-patterns
- `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — F&B brand strategy domain framework
- `evaluation/protocol.md` — pilot procedure step-by-step
- `evaluation/self_eval.md` — canonical self-eval schema
