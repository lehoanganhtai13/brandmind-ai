# BrandMind AI — Thesis Overview

> **Đề tài**: BrandMind — Hệ thống Personalized Multi-Agent AI Mentor hỗ trợ xây dựng chiến lược thương hiệu cho doanh nghiệp F&B vừa và nhỏ
>
> **English**: BrandMind — A Personalized Multi-Agent AI Mentor for Brand Strategy Development in SME F&B Businesses

---

## Update 2026-05-05 — current state pointer

Tài liệu này được khởi tạo 2026-04-05 và cập nhật điểm đến 2026-05-05. Phần lớn các chương về **Bối cảnh, Vấn đề, Câu hỏi nghiên cứu, Đề xuất giải pháp, và Core Components** vẫn phản ánh đúng kiến trúc và triết lý sản phẩm hiện tại. Tuy nhiên các phần **Evaluation methodology** và **Empirical findings** đã được nâng cấp đáng kể trong giai đoạn Eval Methodology Overhaul (2026-05-03 → 2026-05-05) và sẽ được trình bày chi tiết hơn ở các tài liệu chuyên đề.

**Đọc các tài liệu chuyên đề sau (research-paper style) để có dữ liệu định lượng và phát hiện thực nghiệm cập nhật**:

- **`docs/THESIS_FINDINGS.md`** — 3 phát hiện thực nghiệm chính trình bày theo kiểu research paper:
  1. Layer separation in prompt design — identity surface vs action surface — empirically validated (Phase A v1 vs Phase A v2 trên 7 pilot Linh)
  2. Action-surface restatement at on-demand skill is load-bearing reinforcement (bisect r14 vs r14b chứng minh -0.53 combined regression khi removed)
  3. Persona-driver methodology contamination biases personalization rubrics upward (disciplined script discipline được promote vào canonical surface)

- **`docs/THESIS_RESULTS.md`** — bảng điểm 7 pilot Linh đầy đủ, B7/B8 verdict comparison, criterion-level analysis B + C dimensions, defendable thesis claims (3 ✅ verified + 1 ⚠️ honest-negative + 1 ❓ pending), trade-offs và limitations

- **`docs/thesis_evaluation_summary.md`** — eval methodology summary cập nhật: 3-judge cross-judge calibrated chat rubric + B (Strategic Coherence single-LLM) + C (Strategic Problem-Solving single-LLM) + self-eval triangulation + N=3 trial protocol + combined formula `0.30·chat + 0.30·B + 0.30·C + 0.10·self_eval`

- **`docs/B_C_JUDGE_METHODOLOGY.md`** — B và C judge design (criteria, anchors, isolation tests)

- **`docs/JUDGE_CALIBRATION_METHODOLOGY.md`** — chat rubric calibration với golden-anchor methodology (Kappa 0.319 → 0.592 Fair → Moderate)

- **`docs/CROSS_SYSTEM_PILOT_PROCEDURE.md`** — cross-system fairness commitment (Phase C natural-user-scenario rule, anti-elicitation pattern)

### Headline finding (anchor cho thesis defense)

Phase A v2 surgical edit at the Phase 5 dispatch surface (commit `7a66d50`) lifted **B7** (DOCX dispatch design rationale visible in chat) from FLAT-INCOHERENT × 6 prior pilots to PARTIAL × 3 trials, và **B8** (PPTX dispatch design rationale visible in chat) from FLAT-INCOHERENT × 6 to FULL COHERENT × 3 trials, on the r15 v2 disciplined-script Linh pilot. Combined score r15 v2 = 7.18 (best disciplined methodology). B mean 9.25 = highest of any pilot in the series.

Empirically validates layer separation principle: identity-level edit (Phase A v1) at top of system prompt was insufficient × 6 pilots; action-surface edit (Phase A v2) directly before each `task()` dispatch achieved the lift.

### What's still open (post-thesis-overview update)

- **Cross-persona generalization** (Task #82) — pilots Minh / Thảo / Hải / Hương trên Phase A v2 stack chưa drive
- **Cross-system vanilla baselines** (Task #83) — ChatGPT + Gemini comparison via Playwright, **thesis-critical**
- **C-dimension lift** (C6 risk / C8 ROI math / C9 stakeholder defensibility) — Phase A v2 không touched, future work

### Updated thesis claims (replaces older quantitative aspirations)

| # | Claim | Status |
|---|---|---|
| 1 | "BrandMind narrates per-artifact design rationale at the Phase 5 dispatch surface" | ✅ verified (B7/B8 lift) |
| 2 | "Layer separation in prompt design — identity vs action surface — empirically validated" | ✅ verified (Phase A v1 vs v2) |
| 3 | "Action-surface restatement at on-demand skill is load-bearing reinforcement, not redundant duplication" | ✅ verified (bisect r14 vs r14b) |
| 4 | "Combined Overall ≥ 7.5 cross-judge" | ⚠️ NOT achieved on disciplined methodology (r15 v2 = 7.18). Per north-star honest-measurement update, fair-measured 6.0–6.5 acceptable; thesis pivots to B/C dimension lift + cross-system delta |
| 5 | "BrandMind delivers strategic substance vanilla LLMs cannot" | ❓ untested (vanilla baselines pending Task #83) |

---

## 1. Bối cảnh & Vấn đề

Ngành F&B Việt Nam có hơn 540,000 cơ sở nhưng tỷ lệ đóng cửa trong 2 năm đầu lên đến 60%. Một nguyên nhân chính: doanh nghiệp vừa và nhỏ thiếu chiến lược thương hiệu bài bản.

Họ đối mặt với nghịch lý: **cần** chiến lược chuyên nghiệp để cạnh tranh, nhưng **không đủ** ngân sách cho consultant (50-200 triệu VND/dự án) và nhân sự marketing thường là junior — thiếu kiến thức nền tảng.

### Khoảng trống với các giải pháp hiện tại

Thị trường đang bùng nổ AI tools cho marketing — content generators, SEO optimizers, social media schedulers, brand voice analyzers. Nhưng hầu hết **đều thiết kế cho người đã có kinh nghiệm**:

- Senior marketer hay brand manager biết mình cần gì → dùng AI tool như **force multiplier** — tăng tốc công việc họ đã biết cách làm
- Junior marketer chưa nắm được bức tranh lớn → được cho tool mạnh nhưng **không biết dùng cái nào, vào lúc nào, cho mục đích gì** → tool trở nên vô nghĩa

Các giải pháp hiện tại đều miss điều này:

- **AI chatbot tổng quát** (ChatGPT, Gemini) — tư vấn chung chung, không có structured workflow, không dạy người dùng
- **AI marketing tools** (Jasper, Copy.ai, etc.) — point solutions cho từng task cụ thể, không có quy trình end-to-end, assume người dùng biết khi nào cần dùng tool nào
- **Template chiến lược** — điền vào chỗ trống mà không hiểu lý do
- **Khóa học online** — dạy lý thuyết nhưng không áp dụng vào doanh nghiệp cụ thể

**Nhận định then chốt**: Vấn đề không phải thiếu công cụ — mà là thiếu **người hướng dẫn**. Junior marketer cần một mentor biết dẫn dắt qua quy trình, dạy tại sao dùng framework nào vào lúc nào, đồng thời áp dụng ngay vào doanh nghiệp của họ. BrandMind giải quyết đúng khoảng trống này.

---

## 2. Câu hỏi nghiên cứu

| # | Câu hỏi |
|---|---------|
| **RQ1** | Multi-agent AI system có thể tạo brand strategy ở mức chất lượng chuyên nghiệp cho F&B SME không? |
| **RQ2** | Cùng hệ thống đó có thể đồng thời đóng vai trò mentor — giúp junior marketer hiểu "tại sao" đằng sau mỗi strategic decision không? |
| **RQ3** | Hệ thống có thể personalize — adapt theo trình độ, cách học, cách làm việc, và business context cụ thể của từng user không? |
| **RQ4** | Làm thế nào để duy trì behavioral consistency của LLM xuyên suốt long-running multi-phase session — khi context bị compressed, user dẫn lệch hướng, và agent phải phối hợp nhiều sub-agents? |

---

## 3. Nghiên cứu liên quan & Khoảng trống

### Multi-Agent Systems

AutoGen (Wu et al., 2023) và MetaGPT (Hong et al., 2023) chứng minh specialized agents phối hợp tốt hơn general-purpose agent trên complex tasks. Tuy nhiên, các hệ thống này focus vào **productivity** — hoàn thành task nhanh hơn. Chưa có hệ thống nào thiết kế để **vừa execute vừa mentor** người dùng.

### RAG & Knowledge Graph

RAG (Lewis et al., 2020) giảm hallucination bằng cách ground vào verified knowledge. GraphRAG (Microsoft, 2024) bổ sung khả năng nắm bắt **relationships** giữa các concepts. Brand strategy đòi hỏi cả hai: relationships giữa frameworks (graph) lẫn original passages từ textbooks (vector).

### AI Tutoring

Bloom's 2 Sigma Problem (1984): one-on-one tutoring hiệu quả hơn 2 standard deviations so với classroom instruction. MathTutorBench (2024) phát hiện **Expertise-Pedagogy Gap**: LLM giỏi solve problems nhưng không giỏi teach. Các AI tutoring systems hiện tại chủ yếu cho STEM — chưa có cho business strategy, lĩnh vực không có đáp án đúng-sai rõ ràng.

### Personalization trong AI Systems

Nghiên cứu về personalization trong AI cho thấy: **perceived personalization** (user cảm nhận được rằng hệ thống hiểu mình) drives satisfaction mạnh hơn actual personalization (Tran et al., 2015). Điều này có nghĩa: agent không chỉ cần personalize — mà phải **làm cho user thấy** mình đang được personalize ("Based on what you told me about X...").

Các AI tutoring systems hiện tại personalize chủ yếu theo **difficulty level** (adaptive learning). Nhưng consulting context cần personalize nhiều chiều hơn: business context (industry, budget, competitors), user profile (experience level, learning style, communication preferences), và interaction patterns (tactical vs strategic thinker, fast vs slow absorber). Chưa có hệ thống nào address đầy đủ multi-dimensional personalization này.

### Context Engineering & Harness Engineering

Đây là nền tảng lý thuyết trọng tâm của nghiên cứu. Ba khái niệm này tạo thành hierarchy:

| Layer | Câu hỏi | Scope |
|---|---|---|
| **Prompt Engineering** (2023) | "Hỏi LLM như thế nào?" | Viết system prompt, instruction text |
| **Context Engineering** (2025) | "Cho LLM thấy gì khi hỏi?" | Toàn bộ context window: tools, docs, memory, examples |
| **Harness Engineering** (2026) | "Thiết kế toàn bộ môi trường ra sao?" | Guardrails, feedback loops, middleware, lifecycle management |

Mỗi layer bao trùm layer trước đó: Prompt ⊂ Context ⊂ Harness.

**Prompt Engineering** (Anthropic, OpenAI, 2023-24) focus vào instruction text — cách viết system prompt hiệu quả. Đây là lớp cơ bản nhất.

**Context Engineering** (Tobi Lutke/Shopify, Andrej Karpathy, Anthropic, 2025) mở rộng scope: không chỉ prompt mà là **toàn bộ tokens mà LLM nhìn thấy** — system instructions, tool definitions, retrieved documents, conversation history, examples, memory. Anthropic gọi đây là "nghệ thuật cung cấp tập hợp tokens tối thiểu nhưng đủ signal để maximize xác suất kết quả mong muốn." Context engineering bao gồm:

- **Attention budget** — mỗi token tiêu tốn attention có giới hạn (transformer O(n²)), context phải được coi là tài nguyên hữu hạn
- **Just-in-time retrieval** — agent chỉ load data khi cần, không dump hết vào context
- **Progressive disclosure** — tiết lộ thông tin dần, không cho agent thấy mọi thứ cùng lúc
- **Compaction** — tóm tắt conversation khi gần limit, giữ lại thông tin kiến trúc
- **Structured note-taking** — agent ghi chú ra external storage ngoài context window

**Harness Engineering** (Mitchell Hashimoto, OpenAI Codex, 2026) mở rộng thêm: không chỉ context window mà là **toàn bộ hệ thống xung quanh agent** — middleware stack, mechanical enforcement (không chỉ dựa vào prompt mà dùng code constraints), automated feedback loops, state management, observability. Context engineering giúp agent **nghĩ tốt**. Harness engineering ngăn toàn bộ hệ thống **trôi lệch khỏi mục tiêu**.

**Khoảng trống**: Các framework (Deep Agents, LangGraph) cung cấp **primitives** — middleware API, backend protocol, tool interface. Nhưng chưa có nghiên cứu nào hệ thống hóa: **failure mode nào cần giải pháp nào?** Khi combine nhiều solutions, chúng interact ra sao? BrandMind đóng góp bằng cách mapping cụ thể: failure mode → solution → measured outcome.

---

## 4. Đề xuất giải pháp

### 4.1 Ý tưởng cốt lõi: Mentor-Execute Loop

Khác với approach truyền thống (dạy xong rồi làm, hoặc làm xong rồi giao), BrandMind áp dụng **Mentor-Execute Loop** cho mỗi phase:

| Khóa học online | Consultant | BrandMind |
|---|---|---|
| Dạy 6 phase → Tự áp dụng (thường fail) | Làm 6 phase → Giao output (user không học được gì) | Cho MỖI phase: **EXPLAIN → DO → PRESENT → CHECK**. User VỪA có strategy VỪA hiểu TẠI SAO |

### 4.2 Personalization — Nguyên tắc thiết kế xuyên suốt

BrandMind không chỉ tạo brand strategy chung chung rồi gắn tên doanh nghiệp vào — mà **personalize ở mọi tầng**:

- **Strategy level** — Recommendations dựa trên dữ liệu thực của doanh nghiệp cụ thể: competitors tại cùng khu vực, target audience thực tế, budget constraints, market dynamics của thành phố đó. Agent được thiết kế để research real-time data (web search, social media, browser) thay vì dựa vào generic knowledge.
- **Mentoring level** — Agent adapt cách dạy theo user's level: junior marketer cần giải thích chi tiết hơn, user có kinh nghiệm được hỏi ý kiến nhiều hơn. Workspace memory lưu user profile (role, experience, communication style, working patterns) để maintain consistency xuyên session.
- **Interaction level** — Agent theo dõi interaction patterns (user nghĩ tactical hay strategic? hỏi nhiều hay ít? absorb nhanh hay chậm?) qua working notes → adapt pacing, depth, và cách present information cho phù hợp.

Personalization không phải 1 feature riêng lẻ — nó là kết quả của nhiều core components phối hợp:

| Component | Vai trò trong personalization |
|-----------|------------------------------|
| **Workspace memory** (5.6) | Lưu user profile (trình độ, cách học, working style) → agent nhớ user là ai |
| **Scaffolded mentoring** (5.5) | Adapt giải thích theo user's level, fading khi user thành thục hơn |
| **Scoped multi-agent** (5.1) | Sub-agents research business-specific data (competitors tại cùng khu vực, market dynamics) |
| **Domain-specific tooling** (5.3) | Tools chuyên dụng cho marketing → recommendations dựa trên real data, không phải LLM guessing |
| **Quality gates** (5.2) | Đảm bảo output specific cho doanh nghiệp đó — không generic |

### 4.3 Kiến trúc tổng quan

Hệ thống tổ chức thành 3 tầng, mỗi tầng có vai trò riêng:

**1. Tầng Interaction** — giao tiếp với user, điều phối workflow, mentor + execute. Gồm main orchestrator agent chạy 6-phase brand strategy process với Mentor-Execute Loop. Agent giao tiếp bằng tiếng Việt, dẫn dắt user qua từng bước.

**2. Tầng Execution** — thu thập real-time data, tạo creative deliverables. Gồm 4 specialized sub-agents (market research, social media analysis, creative studio, document generation) + web intelligence tools (search, scrape, browser automation). Sub-agents chỉ báo cáo dữ liệu — không ra quyết định chiến lược.

**3. Tầng Knowledge** — cung cấp verified marketing knowledge, duy trì strategic memory. Gồm Knowledge Graph (27K entities, 30K relationships từ 5 marketing textbooks) + persistent workspace files (SOAP notes, Golden Thread) sống sót qua context compression.

**Harness** bao bọc cả 3 tầng — middleware stack kiểm soát behavior của agent qua mỗi turn: quản lý tool visibility, enforce phase progression, trigger auto-save, compress context, log events.

---

## 5. Core Components

BrandMind được cấu thành từ nhiều thành phần kỹ thuật cộng hưởng với nhau. Không thành phần nào đứng một mình — chúng phối hợp để tạo ra hệ thống hoàn chỉnh:

- **Scoped Multi-Agent System** — phân rã task phức tạp thành specialized agents
- **Harness Engineering** — đảm bảo behavioral consistency qua long sessions (chiếm phần lớn engineering effort)
- **Domain-Specific Tooling & Agent Skills** — bộ công cụ mô phỏng workflow marketing thực tế
- **Hybrid RAG** — cung cấp verified marketing knowledge từ authoritative sources
- **Scaffolded Mentoring** — dạy user tư duy chiến lược, không chỉ giao output
- **SOAP Workspace Memory** — duy trì strategic coherence khi context bị compressed

### 5.1 Scoped Multi-Agent System

1 orchestrator agent + 4 specialized sub-agents, mỗi agent có scope boundary rõ ràng:

| Agent | Scope | Boundary |
|-------|-------|----------|
| **Orchestrator** (main) | Strategic decisions + mentoring | Là agent DUY NHẤT ra strategic decisions |
| Market Research | Business data, competitors, trends | KHÔNG social media, KHÔNG recommend |
| Social Media Analyst | Facebook, Instagram, TikTok | KHÔNG strategy, chỉ report observations |
| Creative Studio | Images, mood boards, brand key visual | KHÔNG strategy, chỉ execute creative brief |
| Document Generator | PDF, slides, spreadsheets | KHÔNG strategy, chỉ format content |

Principle: sub-agents là **data specialists** — chỉ report. Orchestrator **synthesizes và decides**. Scoped delegation ngăn hallucination do agent tổng quát đoán mò ngoài expertise.

### 5.2 Harness Engineering

Tất cả components trên sẽ vô nghĩa nếu agent không duy trì được **behavioral consistency** qua session dài. Harness engineering đảm bảo điều đó — và chiếm phần lớn engineering effort của hệ thống.

#### Vấn đề: LLM failure modes trong long-running sessions

LLM có khả năng ngôn ngữ vượt trội, nhưng khi chạy session kéo dài nhiều giờ qua 6 phases, nó biểu hiện hàng loạt **predictable failure modes**:

| Failure Mode | Biểu hiện |
|-------------|-----------|
| **Phase skipping** | Bỏ qua market research, nhảy thẳng sang logo design — LLM ưu tiên "xong nhanh" |
| **Workflow drift** | Sau 20+ turns, quên đang ở phase nào, bị user dẫn dắt lệch hướng |
| **Context decay** | Khi compress conversation cũ, mất strategic details → decisions sau mâu thuẫn trước |
| **Tool overload** | 24 tools cùng lúc → chọn sai tool hoặc không biết tool nào phù hợp |
| **Knowledge fabrication** | Trình bày marketing framework sai hoặc trộn nhiều nguồn |
| **Premature stopping** | "Mệt" sau nhiều turns → dừng khi còn tasks chưa xong |
| **Scope creep** | Sub-agent (chỉ nên collect data) lại đưa ra strategic recommendations |

#### Giải pháp: Harness as behavioral guardrails

> Harness engineering không cải thiện LLM — mà **kiểm soát môi trường xung quanh nó** để mỗi failure mode bị ngăn chặn bởi một cơ chế cụ thể.

Tương tự hệ thống điều khiển tên lửa: không cải thiện động cơ, mà dùng sensors + trajectory correction liên tục để tên lửa đi đúng hướng. Framework (Deep Agents) cung cấp building blocks. Harness engineering là cách **thiết kế và compose** chúng.

**Bao gồm cả 3 layers** của hierarchy:
- **Prompt engineering**: System prompt với dual persona (strategist + mentor), knowledge verification principle, pacing rules
- **Context engineering**: Progressive tool disclosure, just-in-time skill loading, workspace notes as external memory, auto-save trước compression, attention budget management
- **Harness engineering**: Middleware stack enforcing behavior mechanically (advance-only phase gates, task completion guards, scoped sub-agent delegation, malformed call auto-fix)

#### Failure Mode → Solution Mapping

Đây là đóng góp cốt lõi — mapping cụ thể giữa từng failure mode và giải pháp:

| Failure Mode | Solution | Mechanism |
|---|---|---|
| **Phase skipping** (nhảy Phase 1 → 5) | Advance-only mechanism (code-enforced) | MECHANICAL: agent gọi "advance" → hệ thống xác định next phase; agent không thể chỉ định nhảy đến phase khác |
| **Premature advancing** (tiến phase khi chưa xong) | Quality gates (prompt-enforced, 49 gates across 7 phases) | BEHAVIORAL: system prompt + phase reference liệt kê checklist cụ thể. VD Phase 1: "≥3 competitors profiled", "SWOT completed", "user confirmed" |
| **Workflow drift** (mất phương hướng) | Planning mechanism + phase reference skills | Todo list bắt buộc; item #1 = current phase; nhắc nhở khi lệch |
| **Context decay** (mất chi tiết sau nén) | 3-layer memory safety net | Auto-save trigger (65%) → Compression (80%) → Workspace files tồn tại ngoài context window |
| **Tool overload** (24 tools quá nhiều) | Progressive disclosure (search → load → use → unload) | Ẩn specialized tools; chỉ hiện khi agent chủ động tìm kiếm |
| **Knowledge fabrication** (bịa framework) | Knowledge verification + Hybrid RAG từ 5 textbooks | PHẢI search TRƯỚC KHI trình bày |
| **Premature stopping** (dừng sớm) | Task completion guard | Detect agent muốn dừng → check pending tasks → inject reminder (3×) |
| **Scope creep** (vượt phạm vi) | Scoped delegation + state isolation | Sub-agent: chỉ REPORT, không RECOMMEND; không thấy parent state |

#### Cross-layer interaction

Các mechanisms không hoạt động độc lập — chúng **phối hợp** tạo reliable behavior:

**Phase transition** (6 mechanisms cùng tham gia): Planning mechanism xác nhận todos completed → Quality gate xác định next phase + inject workspace update reminder → Phase reference skills cung cấp hướng dẫn phase mới → Workspace memory ghi SOAP + update Golden Thread → Progressive disclosure swap tools → Planning mechanism tạo todos mới.

**Context approaching limit** (chuỗi cứu hộ): Auto-save trigger (65%) nhắc agent ghi workspace files → Agent saves SOAP + inbox → Compression (80%) nén conversation cũ → Chi tiết mất NHƯNG workspace files tồn tại bên ngoài → Agent đọc lại files → Khôi phục toàn bộ strategic context. Đây là vấn đề LLM thuần không giải quyết được.

#### Design principles

| Principle | Giải thích |
|-----------|------------|
| **Single responsibility** | Mỗi mechanism giải quyết đúng 1 failure mode — dễ test, replace, debug |
| **Composable, order-dependent** | Mechanisms compose được, nhưng thứ tự quan trọng (auto-save PHẢI trước compression) |
| **Fail-safe** | Mechanism hỏng → agent vẫn chạy, chỉ mất guardrail đó — không crash |
| **Context injection** | Mechanism không sửa agent code, chỉ inject text vào context → agent "nghe" hướng dẫn |
| **Backend-agnostic** | Agent không biết files lưu ở đâu — cùng logic chạy với virtual storage (test) hoặc real filesystem (production) |

---

### 5.3 Domain-Specific Tooling & Agent Skills

BrandMind không chỉ chat về strategy — nó được trang bị **bộ công cụ chuyên dụng mô phỏng lại toàn bộ workflow mà marketer thực sự làm hàng ngày**. Mỗi agent được trang bị đúng tools phù hợp cho scope của nó:

| Marketing Activity | Tool | Agent sử dụng |
|---|---|---|
| Research thị trường, xu hướng, đối thủ | Web search (multi-provider fallback), deep research (multi-step synthesis), web scraping | Market Research |
| Audit social media đối thủ (FB, IG, TikTok) | Social profile analyzer, browser automation | Social Media Analyst |
| Phát hiện ngôn ngữ khách hàng tìm kiếm | Search autocomplete extraction | Market Research |
| Tạo mood board, logo concept, color palette | Image generation (với templates chuyên dụng: mood_board, logo_concept, packaging, interior) | Creative Studio |
| Chỉnh sửa lặp lại hình ảnh đã tạo | Image editing (iterative refinement) | Creative Studio |
| Tạo Brand Key one-pager visual | Brand Key generator (9 components infographic) | Creative Studio |
| Xuất PDF/DOCX chiến lược, slide pitch deck | Document & presentation generator | Document Generator |
| Tạo bảng KPI tracking, competitor matrix | Spreadsheet generator (pre-built templates) | Document Generator |
| Tra cứu marketing frameworks (Keller, Kotler...) | Knowledge Graph search + Document library search | Tất cả agents |

Bên cạnh tools, mỗi phase có **agent skill** (reference file) hướng dẫn methodology cụ thể. Ví dụ: Phase 1 skill mô tả quy trình 8 bước nghiên cứu thị trường, Phase 2 skill hướng dẫn xây dựng positioning statement theo framework Keller, Phase 3 skill dùng Aaker's Brand Personality Dimensions + Byron Sharp's Distinctive Brand Assets. Agent đọc skill khi bắt đầu mỗi phase → biết cần làm gì, dùng tool nào, quality gates nào phải pass.

Điểm quan trọng: tools và skills được thiết kế **cho nhau** — skill nói "nghiên cứu top 3-5 đối thủ trong khu vực" → agent có sẵn tools để search, scrape, analyze. Không có gap giữa methodology (skill) và capability (tools).

### 5.4 Hybrid RAG (Knowledge Graph + Vector Search)

Knowledge Graph từ 5 marketing textbooks (Kotler, Keller, Ries & Trout, Byron Sharp, Cialdini) — 27,143 entities, 30,448 relationships. Dual retrieval:

- **Graph search** — "bản đồ" relationships giữa frameworks (Point of Difference liên hệ positioning thế nào)
- **Vector search** — "câu chuyện đầy đủ" từ original passages (tại sao, ví dụ, exceptions)

System principle: LLM **không được** present unverified knowledge. Phải search trước, dùng sau.

### 5.5 Scaffolded Mentoring

Dựa trên Vygotsky's Zone of Proximal Development — học hiệu quả nhất khi nội dung nằm trong vùng "khó vừa đủ để cần support." Scaffold (giàn giáo) được dựng lên để hỗ trợ, rồi tháo dần khi người học đứng được. BrandMind thực hiện lifecycle này qua 4 cơ chế:

1. **Dựng scaffold** (Explain before execute) — Agent dạy concept trước khi apply. Ví dụ: giải thích "positioning" là gì, tại sao quan trọng → rồi mới xây positioning cho user's business. Không explain trước mà execute luôn thì user chỉ nhận output mà không hiểu — giống consultant, không phải mentor.

2. **Verify scaffold hoạt động** (Check real understanding) — Sau khi explain, agent kiểm tra user thực sự hiểu hay chỉ gật đại. Không hỏi "Hiểu chưa?" (rhetorical — ai cũng gật) mà hỏi "Theo bạn hướng nào phù hợp hơn cho business của bạn?" — buộc user apply kiến thức vừa học.

3. **Kiểm soát tốc độ** (Pacing) — Một step mỗi turn, không dump 5 frameworks trong 1 message. Cognitive overload = scaffold sụp. User cần thời gian absorb trước khi tiến tiếp.

4. **Tháo scaffold dần** (Fading) — Phase 0 giải thích rất chi tiết (user mới, cần nhiều support). Phase 3-4 ngắn gọn hơn (user đã quen). Phase 5 chủ yếu hỏi user's opinion (user đã hiểu). Nếu không fade thì user bị phụ thuộc — không đạt mục tiêu "tự giải thích strategy cho boss được."

### 5.6 SOAP Workspace Memory

**Vấn đề cần giải quyết**: Brand strategy session kéo dài nhiều giờ qua 6 phases. LLM có context window giới hạn — khi conversation dài, hệ thống phải compress (tóm tắt) messages cũ để giải phóng space. Quá trình compress này mất đi chi tiết chiến lược quan trọng → decisions ở Phase 4 có thể mâu thuẫn với Phase 1 vì agent "quên" research findings.

**Giải pháp**: Agent ghi chú ra **external files nằm ngoài context window** — files này không bị ảnh hưởng bởi compression. Format ghi chú lấy cảm hứng từ y khoa (SOAP notes — ngành cũng cần track patient progress qua nhiều lần khám):

- **S** (Subjective) — User's opinions, preferences, concerns
- **O** (Objective) — Research data, competitor findings, verified facts
- **A** (Assessment) — Agent's strategic analysis, key decisions made
- **P** (Plan) — Next steps, open questions

**Cách apply trong BrandMind**: Sau mỗi phase, agent ghi 1 SOAP entry vào workspace file. Khi context bị compressed, agent đọc lại file → khôi phục toàn bộ strategic context mà không cần nhớ conversation cũ. Ngoài ra, agent duy trì **Golden Thread** — một dòng tóm tắt chuỗi quyết định xuyên suốt từ Phase 0 problem → Phase hiện tại. Golden Thread đảm bảo mọi decision đều trace back được về vấn đề gốc, ngăn strategy drift khi context bị mất.

Ngoài SOAP và Golden Thread, workspace còn lưu **user profile** (role, experience level, communication preferences, working style) — đây là nền tảng cho personalization. Agent đọc profile khi bắt đầu session → biết user là ai → adapt mentoring style phù hợp. Profile persist across sessions, nên lần tương tác sau agent không cần hỏi lại.

Hiệu quả: trong test, agent hoạt động qua 28 turns với 43 workspace operations — sau mỗi lần compression, agent đọc lại workspace files và tiếp tục consistent mà không mâu thuẫn với decisions trước đó.

---

## 6. Brand Strategy Workflow

6 phases (+0.5 cho rebrand), mỗi phase áp dụng Mentor-Execute Loop:

| Phase | Tên | Key Deliverables | Quality Gates |
|-------|-----|-----------------|---------------|
| 0 | Business Problem Diagnosis | Problem statement, scope, budget | 7 |
| 0.5 | Brand Equity Audit* | Preserve-Discard Matrix | 5 |
| 1 | Market Intelligence | ≥3 competitors, SWOT, insights, perceptual map | 7 |
| 2 | Brand Positioning | Positioning statement, POPs/PODs, stress test | 7 |
| 3 | Brand Identity | Personality, voice, visual direction, mood boards | 8 |
| 4 | Communication Framework | Value proposition, Cialdini, AIDA, channels | 7 |
| 5 | Strategy Plan & Deliverables | Brand Key, KPIs, roadmap, strategy document | 8 |

*Phase 0.5 chỉ cho rebrand.* Tổng cộng **49 quality gates** — mỗi gate phải pass trước khi advance.

Theoretical foundations: Keller (CBBE Pyramid), Kotler (STP), Ries & Trout (Positioning), Byron Sharp (Distinctive Brand Assets), Cialdini (7 Principles of Persuasion).

---

## 7. Evaluation Framework

Evaluation rubric đầy đủ tại `docs/BRANDMIND_EVAL_RUBRIC.md`. Dưới đây là tổng quan.

### Core philosophy

Rubric được thiết kế để trả lời **một câu hỏi duy nhất**: *"Nếu agent pass evaluation này, liệu real user có nhận được brand strategy ở mức chuyên nghiệp — đủ tốt để chuyên viên cấp cao duyệt và approve không?"*

Rủi ro lớn nhất: evaluation score cao nhưng real user thấy kém — benchmark đẹp trên giấy nhưng vô nghĩa thực tế. Mọi design decision trong rubric đều hướng đến loại bỏ rủi ro này.

### Rubric design

**3 chiều đánh giá độc lập** — vì agent có thể giỏi ở chiều này nhưng kém ở chiều khác (VD: strategy tốt nhưng không dạy user hiểu):

| Dimension | Weight | Core Question |
|-----------|--------|---------------|
| **Strategy Quality** | 50% | Output solve vấn đề thật? Specific? Actionable trong budget? |
| **Mentoring Quality** | 30% | User hiểu WHY và tự explain cho boss được? |
| **Personalization** | 20% | Agent adapt theo user's level, business context, và cách làm việc? |

Weights phản ánh priority: Quality là nền tảng (50%) — output kém thì mentoring và personalization vô nghĩa. Mentoring là differentiator của BrandMind vs AI tools khác (30%). Personalization là defense chống generic output (20%). Quality < 7/10 → overall capped ở 6/10.

**104 binary criteria theo 3 tầng** — dựa trên CheckEval (Lee et al., 2024) cho thấy binary decomposition (ĐẠT/KHÔNG ĐẠT) có độ nhất quán giữa giám khảo cao nhất:

| Tầng | Vai trò | Count | Score impact |
|------|---------|-------|-------------|
| **Gate** | Yêu cầu tối thiểu — 1 gate fail → capped 5/10 | 32 | Nền tảng |
| **Standard** | Chất lượng chuyên nghiệp | 47 | All pass = **8/10 (TARGET)** |
| **Excellence** | Vượt mong đợi | 25 | All pass = 10/10 |

Kèm **10 anti-patterns** — hành vi xấu bị trừ 0.5 điểm mỗi lần (đồng ý vô điều kiện, bịa research, tư vấn generic, reveal answer trước khi teach, ...).

### Anti-gaming — đảm bảo rubric predict real-world

Mỗi criterion được thiết kế để **output generic không thể pass**:

- **Substitution test** — swap brand name trong output → advice không đổi → KHÔNG ĐẠT
- **Evidence-based judging** — mỗi judgment phải trích dẫn evidence cụ thể từ transcript, không cho điểm theo cảm tính
- **Failure-defined** — mỗi criterion có mô tả "Common Failure" để calibrate giám khảo: khi không chắc ĐẠT hay KHÔNG → đối chiếu với failure description

### Evaluation pipeline

Thiết kế 2 tầng, lấy cảm hứng từ Agent-as-a-Judge (Zhuge et al., ICML 2025):

**Tầng 1 — Quantitative (Simulation):**
1. **Simulated user** (Claude Code) đóng vai junior marketer với persona chi tiết, tương tác với 5 systems (BrandMind full + 2 ablation + ChatGPT vanilla + Gemini vanilla)
2. **3 SOTA model judges** (Claude Sonnet, Gemini Pro, GPT — từ 3 providers độc lập) đọc conversation logs và chấm theo rubric
3. Simulated user đánh giá **perceived metrics** (first-person); judges đánh giá **objective metrics** (third-person) → tách biệt subjective vs objective
4. **Inter-rater agreement** (Fleiss' Kappa) giữa 3 judges → đo reliability. Chỗ bất đồng = finding thú vị + signal rubric cần refine.

**Tầng 2 — Qualitative (Real user case study, nếu mời được):**
5. 2 real users (khác level) dùng cùng system → chứng minh personalization adapt theo level
6. Survey 10 câu + phỏng vấn sâu 20-30 phút
7. **Validation metric**: Pearson correlation giữa rubric score và human survey mean — target r ≥ 0.7 → **confirm rubric predict real-world experience**

**Tại sao dùng 3 SOTA models thay vì train judge agent riêng**: Rubric đã encode toàn bộ evaluation logic. 3 models cross-validate → loại single-model bias. Inter-rater agreement cung cấp reliability metric. Không cần training/distillation overhead — effort tập trung vào rubric quality.

| Score | Real-world equivalent |
|-------|----------------------|
| 9–10 | Experienced brand consultant level |
| **8–8.9 (TARGET)** | **Output đủ tốt để chuyên viên cấp cao duyệt qua và approve — chỉ cần minor adjustments** |
| 7–7.9 | Useful starting point, cần refinement |
| < 7 | Cần significant rework |

---

## 8. Kết quả sơ bộ

| Test | Result | Finding |
|------|--------|---------|
| E2E Session (28 turns, Phase 0→4) | ✅ | Agent duy trì SOAP notes, Golden Thread consistent, 43 workspace operations |
| Phase tracking (chatty user) | ✅ | Agent KHÔNG premature advance dù user liên tục hỏi off-topic |
| Workspace recovery (sau compression) | ✅ | Khôi phục strategic context từ persistent files thành công |
| Knowledge verification | ⚠️ | KG search tăng (1→6 calls/session), document search vẫn underutilized |

**Real output sample** (premium restaurant tại HCMC): Agent xác định "premium location nhưng low weekday traffic", đề xuất Golden Thread "Premium location + Modern Saigonese → Prestige & Professional positioning cho office segment", phát hiện insight "table-side Truffle service tạo Free Media opportunity qua customer photos."

---

## 9. Đóng góp

| # | Contribution | Novelty |
|---|-------------|---------|
| **1** | **BrandMind** — hệ thống multi-agent AI mentor hoàn chỉnh cho brand strategy, kết hợp synergistically: multi-agent delegation, harness engineering, hybrid RAG, scaffolded mentoring, persistent memory, quality-gated workflow | Đầu tiên kết hợp strategy execution + mentoring trong cùng hệ thống cho business domain |
| **2** | **Harness engineering methodology** — systematic mapping: LLM failure modes → middleware solutions, chứng minh combining primitives đúng cách tạo reliable behavior cho long-running sessions | Kỹ thuật trọng tâm chiếm phần lớn engineering effort |
| 3 | **Mentor-Execute Loop** — combine execution + scaffolded mentoring per phase | Approach mới cho AI trong business strategy (chỉ có cho STEM trước đó) |
| 4 | **Multi-dimensional personalization** — adapt theo user's level, business context, learning style, working patterns qua workspace memory + scaffolded mentoring + business-specific research | Vượt xa adaptive difficulty (chỉ 1 chiều) của AI tutoring hiện tại |
| 5 | **SOAP workspace memory** — persistent strategic memory surviving context compression | Golden Thread maintains cross-phase coherence + user profile enables personalization |
| 6 | **3-dimension evaluation rubric** — 97 criteria + anti-gaming | Quality + Mentoring + Personalization |

**Practical significance**: BrandMind là proof-of-concept cho một pattern rộng hơn — AI mentor cho specialized consulting domains (finance, legal, healthcare). Các kỹ thuật (đặc biệt harness engineering và Mentor-Execute Loop) có thể reuse cho bất kỳ domain nào cần AI vừa execute vừa mentor qua long sessions.

**Technique — Theoretical foundation:**

| Technique | Foundation |
|-----------|-----------|
| Harness engineering | Context Engineering (Anthropic, 2025), Middleware Pattern, AOP |
| Multi-agent delegation | Task Decomposition (Wu et al., 2023), scoped specialization |
| Hybrid RAG | GraphRAG (Microsoft, 2024), Dense+BM25 hybrid retrieval |
| Scaffolded mentoring | Vygotsky ZPD, Bloom's Taxonomy, Fading Scaffolding |
| SOAP workspace memory | Medical documentation standard, Progressive Summarization |
| Quality-gated workflow | Stage-Gate (Cooper, 1990), advance-only enforcement |
| Multi-dimensional personalization | Perceived Personalization (Tran et al., 2015), Adaptive Learning, User Modeling |
| 3-dimension evaluation | CheckEval binary decomposition, Agent-as-a-Judge (ICML 2025) |

---

## 10. Giới hạn & Hướng phát triển

**Giới hạn**: Chưa có formal evaluation trên large sample; phụ thuộc LLM quality; chỉ tested F&B tại HCMC; static knowledge base (5 textbooks).

**Hướng phát triển**: (1) Hoàn thành 4-step evaluation pipeline; (2) Implicit memory — remember user characteristics across sessions; (3) Extend sang consulting domains khác.

---

## Tài liệu tham khảo

- Anthropic (2025). "Effective Context Engineering for AI Agents." *Engineering Blog*
- Anthropic (2025). "Advanced Tool Use for AI Agents." *Engineering Blog*
- Hashimoto, M. (2026). "Harness Engineering." *mitchh.com*
- Lutke, T. (2025). "Context Engineering." *X/Twitter*
- Wu, Q. et al. (2023). "AutoGen: Multi-Agent Conversation." *arXiv:2308.08155*
- Hong, S. et al. (2023). "MetaGPT: Multi-Agent Collaborative Framework." *arXiv:2308.00352*
- Lewis, P. et al. (2020). "Retrieval-Augmented Generation." *NeurIPS 2020*
- Edge, D. et al. (2024). "GraphRAG: Query-Focused Summarization." *Microsoft Research*
- Bloom, B.S. (1984). "The 2 Sigma Problem."
- Vygotsky, L.S. (1978). *Mind in Society.*
- Liu, N.F. et al. (2023). "Lost in the Middle: How Language Models Use Long Contexts."
- Packer, C. et al. (2023). "MemGPT: LLMs as Operating Systems."
- Tran, T.P. (2015). "Personalized ads on Facebook: An effective marketing tool for online marketers." *Journal of Retailing and Consumer Services*
- Zhuge, M. et al. (2025). "Agent-as-a-Judge." *ICML 2025*
- Lee, J. et al. (2024). "CheckEval: Robust LLM Evaluation via Checklist."
- Keller, K.L. (2013). *Strategic Brand Management.*
- Kotler, P. & Armstrong, G. (2018). *Principles of Marketing.*
- Ries, A. & Trout, J. (2001). *Positioning: The Battle for Your Mind.*
- Sharp, B. (2010). *How Brands Grow.*
- Cialdini, R. (2021). *Influence: The Psychology of Persuasion.*
