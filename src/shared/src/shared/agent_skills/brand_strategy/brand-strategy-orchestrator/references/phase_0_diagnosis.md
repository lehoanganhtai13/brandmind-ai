# Phase 0: Business Problem Diagnosis

## Mentor Script

### Opening
"Trước tiên, tôi cần hiểu rõ business context của bạn. Giai đoạn này gọi là 'Brand Problem Diagnosis' — giúp xác định đúng vấn đề trước khi giải quyết. Bạn sẵn sàng trả lời vài câu hỏi chứ?"

### Key Questions
1. Bạn đang kinh doanh F&B gì? (cafe, restaurant, bar, bakery...)
2. Đây là thương hiệu mới hay đã có sẵn?
3. Mục tiêu chính của bạn là gì? (launch mới, rebrand, mở rộng...)
4. Khu vực bạn muốn tập trung?
5. Budget range cho brand strategy?

### Concepts to Explain
- **5W1H framework** — backbone cho phân tích toàn diện: What (kinh doanh gì), Who (cho ai), Where (ở đâu), When (timeline), Why (tại sao cần brand strategy), How (budget/resources)
- **Scope classification** — tại sao xác định đúng scope quan trọng: new brand vs refresh vs reposition vs full rebrand ảnh hưởng toàn bộ workflow phía sau

### Closing
"Dựa trên thông tin bạn chia sẻ, tôi đã có bức tranh rõ ràng về business context. Đây là tóm tắt: {summary}. Bạn confirm và mình sẽ tiến sang nghiên cứu thị trường nhé?"

## Quality Gate

- [ ] **p0_knowledge_verified**: Key concepts verified via KG and/or doc search before applying (scope classification, 5W1H, brand architecture)
- [ ] **p0_problem**: Clear problem statement articulated
- [ ] **p0_scope**: Scope classified (new_brand/refresh/reposition/full_rebrand)
- [ ] **p0_category**: F&B category and concept understood
- [ ] **p0_location**: Target location/market identified
- [ ] **p0_budget**: Budget tier identified for implementation planning
- [ ] **p0_user_confirm**: User confirms understanding and agrees to proceed

**BEFORE proceeding**: Set scope and brand via `report_progress(scope="...", brand_name="...")`, then call `report_progress(advance=True)` to move to the next phase.

## Special: Rebrand Decision Matrix

If user has an existing brand, proactively run the Rebrand Decision Matrix.
Read `references/rebrand_decision_matrix.md` for the full 6-signal scoring system.
