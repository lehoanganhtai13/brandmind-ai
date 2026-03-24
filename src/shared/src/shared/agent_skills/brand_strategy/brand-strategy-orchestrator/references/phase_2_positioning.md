# Phase 2: Brand Strategy Core

## Orchestrator Guidance

This phase delegates to the `brand-positioning-identity` sub-skill.
Your role: ensure positioning is grounded in Phase 1 research, stress test the result.

### Mentor Script

#### Opening
"Đây là giai đoạn quan trọng nhất — Brand Positioning. Giống như khi bạn chọn vị trí trên bản đồ. Mình sẽ dùng insights từ nghiên cứu thị trường để tìm 'sweet spot' — chỗ mà brand của bạn vừa khác biệt, vừa có giá trị cho khách hàng."

#### Concepts to Explain
- **Positioning** — vị trí thương hiệu trong tâm trí khách hàng. Không phải bạn nói bạn là gì, mà khách hàng NGHĨ bạn là gì
- **POPs/PODs** — Points of Parity (điều phải có để cạnh tranh) vs Points of Difference (điều làm bạn khác biệt)
- **Value Ladder** — từ thuộc tính sản phẩm -> lợi ích functional -> lợi ích emotional -> kết quả cuối cùng
- **Brand Essence** — 3-5 từ tóm gọn bản chất thương hiệu

### Stress Test (5 Criteria)
After positioning is drafted, stress test against:
1. **Deliverability**: Can the product/service actually deliver this promise?
2. **Relevance**: Does the target audience actually care about this?
3. **Differentiation**: Is this meaningfully different from competitors?
4. **Credibility**: Will people believe this claim?
5. **Sustainability**: Can this positioning be maintained long-term?

If any criterion fails -> PROACTIVE LOOP TRIGGER fires.

## Quality Gate

- [ ] **p2_knowledge_verified**: Key concepts verified via KG and/or doc search before applying (positioning statement, POPs/PODs, value ladder, brand essence, stress test criteria)
- [ ] **p2_positioning**: Positioning statement complete (target, frame, POD, RTB)
- [ ] **p2_pops_pods**: Points of Parity and Difference defined
- [ ] **p2_value_ladder**: Value ladder built (attributes -> functional -> emotional -> outcome)
- [ ] **p2_essence**: Brand essence / mantra articulated
- [ ] **p2_product_alignment**: Product-brand alignment checked (menu, pricing, service fit)
- [ ] **p2_stress_test**: Positioning stress test passed (5 criteria)

**BEFORE proceeding**: Call `report_progress(advance=True)` to move to the next phase in sequence.
