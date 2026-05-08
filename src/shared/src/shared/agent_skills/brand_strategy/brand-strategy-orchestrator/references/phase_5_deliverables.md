# Phase 5: Strategy Plan & Deliverables

## Orchestrator Guidance

This phase continues with the `brand-communication-planning` sub-skill.
Document assembly delegates to `document-generator` sub-agent.

### Mentor Script

#### Opening
"Giai đoạn cuối — tổng hợp tất cả thành deliverables chuyên nghiệp. Mình sẽ đi qua từng deliverable một, bắt đầu với Brand Key one-pager — tóm gọn toàn bộ strategy lên 1 trang. Sẵn sàng chưa?"

#### Delivery Sequence
Present ONE deliverable per response. After each, get user feedback before proceeding to the next. The four deliverables are four files the user will hand stakeholders — KPI Framework and Implementation Roadmap are CONTENT that lives inside DOCX/PPTX/XLSX, not standalone files.

1. **Brand Key one-pager (image)** — 9-component visual synthesis on one page (creative-studio dispatch)
2. **Strategy document (DOCX)** — Phase 0 → 5 narrative across 10 sections, with KPI Framework summary and Implementation Roadmap embedded as content sections (document-generator DOCX dispatch)
3. **Executive presentation (PPTX)** — 10–12 slides for the boss meeting (document-generator PPTX dispatch)
4. **KPI tracking spreadsheet (XLSX)** — ≥5 metrics in 4-anchor format plus Monthly Tracking sheet seeded with the 0-3 / 3-6 / 6-12 month roadmap content (document-generator XLSX dispatch)

The 4-file split is BrandMind's product convention for a junior marketer's stakeholder meeting (one-pager for desk reference, document for read-through, deck for the meeting, spreadsheet for ongoing tracking) — it is not a literature-canonical taxonomy. Walk the user through each file's design rationale in chat as you present it.

#### Concepts to Explain
- **Brand Key Model** — one-pager tóm tắt toàn bộ brand strategy (canonical Unilever 9-component model): Root Strengths, Competitive Environment, Target, Insight, Benefits, Values, Beliefs & Personality, Reasons to Believe, Discriminator, Brand Essence
- **KPI Framework** — đo lường brand strategy bằng metrics cụ thể spanning awareness / consideration / preference / loyalty / advocacy / revenue. Mỗi metric khi present trong chat phải có 4 anchor: method (cách đo), baseline (giá trị hiện tại hoặc "no data — measure pre-launch"), target+date (giá trị cụ thể với deadline), cadence (weekly / monthly / quarterly). Render dạng `<Metric>: method = …, current = …, target = … by …, cadence = …` để sếp có thể hỏi "số này lấy ở đâu?" / "đang cải thiện không?" / "đến khi nào?" — đều answer được khi cả 4 anchor visible. 5 metrics đủ 4 anchor mạnh hơn 10 metrics thiếu anchor. (4-anchor là BrandMind operationalize SMART goals + Keller brand-tracking-study cadence trong *Strategic Brand Management* Ch 8, không phải framework bên thứ ba.)
- **Implementation Roadmap** — 3 time horizons: Quick Wins (0-3 months), Foundation Building (3-6 months), Scale & Optimize (6-12 months)

### Delegation Pattern

1. YOU write the Phase 5 section into `brand_brief.md` BEFORE any dispatch — KPI table per `<Metric>: method = …, current = …, target = … by …, cadence = …`, the 3-phase rollout (0-3 / 3-6 / 6-12 months), immediate next steps. The harness injects this file into each sub-agent's first turn, so the substance must be in the file before you dispatch.
2. Delegate Brand Key one-pager (image) to `creative-studio` sub-agent.
3. Delegate Strategy DOCX to `document-generator` sub-agent — single dispatch, DOCX only.
4. Delegate Executive PPTX to `document-generator` sub-agent — single dispatch, deck only.
5. Delegate KPI XLSX to `document-generator` sub-agent — single dispatch, spreadsheet only. **Why split into three document-generator dispatches**: when one dispatch packages all three formats together, the sub-agent reliably produces the first artifact in full but content quality degrades on the later ones (empty trailing slides, empty secondary sheets). Splitting trades modest extra latency for deterministic per-artifact quality.
6. YOU echo the 9-component Brand Key as plain text in the chat reply (the image complements the transcript, it does not replace it), narrate per-artifact design rationale before each dispatch (Brand Key 9-component mapping, DOCX 10-section arc, PPTX 10–12 slide audience flow, KPI 4-anchor selection reasoning), then call `list_artifacts(scope="current_session")` and confirm four categories (`images / documents / presentations / spreadsheets`) before declaring Phase 5 complete.

### Roadmap Structure (budget-tier aware)

*Note: this 3-phase rollout cadence (Quick Wins / Foundation Building / Scale & Optimize) is a pragmatic 12-month F&B SME launch convention — distinct from McKinsey's Three Horizons of Growth (H1/H2/H3 spanning years for innovation portfolio balance).*

**Quick Wins (Month 1-3)**:
- Brand name registration
- Logo and visual identity finalization
- Social media profile setup
- Basic collateral (business cards, menu)

**Foundation Building (Month 3-6)**:
- Website launch
- Content calendar execution
- Initial marketing campaigns
- Staff brand training

**Scale & Optimize (Month 6-12)**:
- Performance review and optimization
- Advanced marketing channels
- Partnership and collaboration
- Brand experience refinement

## Quality Gate

- [ ] **p5_knowledge_verified**: Key concepts verified via KG and/or doc search before applying (Brand Key model, KPI metrics, implementation roadmap, brand measurement)
- [ ] **p5_document**: Complete brand strategy document generated (PDF/DOCX)
- [ ] **p5_brand_key**: Brand Key one-pager included
- [ ] **p5_kpis**: At least 5 KPIs defined with baselines and targets
- [ ] **p5_roadmap**: Implementation roadmap with 3 time horizons, tied to budget_tier
- [ ] **p5_roadmap_priority**: Each roadmap item categorized Must Do / Nice to Have
- [ ] **p5_measurement**: Measurement plan with review cadence
- [ ] **p5_transition**: [Rebrand only] Transition & change management plan completed
- [ ] **p5_stakeholder**: [Rebrand only] Stakeholder communication plan defined

**On completion**: Call `report_progress(advance=True)` to mark strategy as complete.
