# Phase 0.5: Brand Equity Audit (Rebrand Only)

## Mentor Script

### Opening
"Trước khi thay đổi bất kỳ điều gì, mình cần hiểu thương hiệu hiện tại có gì đáng giữ. Đây gọi là 'Brand Equity Audit' — kiểm kê tài sản thương hiệu. Giống như khi renovate nhà, bạn cần biết bức tường nào chịu lực trước khi đập."

### Key Questions
1. Logo/visual identity hiện tại — khách hàng có nhận ra ngay không?
2. Slogan/tagline — có ai nhớ không? Có gắn với brand không?
3. Trải nghiệm nào ở quán được khách hàng nhắc đến nhiều nhất?
4. Điều gì bạn TỰ HÀO nhất về thương hiệu hiện tại?
5. Điều gì bạn MUỐN THAY ĐỔI nhất?

### Concepts to Explain
- **Brand Equity** — giá trị vô hình mà thương hiệu tạo ra. Ví dụ: khi khách sẵn sàng trả cao hơn 20k cho ly cafe vì tên quán, đó là brand equity
- **Preserve-Discard Matrix** — phân loại tài sản thương hiệu thành: GIỮ (có equity cao), TIẾN HÓA (adapt nhưng giữ essence), BỎ (không còn phù hợp)

### Closing
"Dựa trên audit, đây là những tài sản thương hiệu đáng giữ lại: {preserve_list}. Và đây là những gì nên thay đổi: {discard_list}. Bạn đồng ý không?"

## Quality Gate

- [ ] **p05_knowledge_verified**: Key concepts verified via KG and/or doc search before applying (brand equity, brand audit, preserve-discard matrix)
- [ ] **p05_inventory**: Brand Inventory completed (visual, verbal, experiential audit)
- [ ] **p05_perception**: Current brand perception assessed (reviews, social, customer voice)
- [ ] **p05_equity**: Brand equity sources identified (what to keep, evolve, discard)
- [ ] **p05_preserve_discard**: Preserve-Discard Matrix completed with user alignment

**BEFORE proceeding**: Call `report_progress(advance=True)` to move to the next phase in sequence.

## Audit Procedure

### Brand Inventory (3 dimensions)
1. **Visual**: Logo, colors, typography, imagery, signage, packaging, uniforms
2. **Verbal**: Name, tagline, tone of voice, key messages, menu descriptions
3. **Experiential**: Service style, ambiance, music, scent, customer journey touchpoints

### Perception Assessment
- Use `deep_research` and `scrape_web_content` to gather customer sentiment from review platforms
- Use `analyze_social_profile` to assess online brand perception
- Use `search_web` for press mentions and third-party reviews

### Preserve-Discard Matrix
| Asset | Recognition | Equity | Action |
|-------|-----------|--------|--------|
| (each asset) | High/Medium/Low | Positive/Neutral/Negative | Keep/Evolve/Discard |
