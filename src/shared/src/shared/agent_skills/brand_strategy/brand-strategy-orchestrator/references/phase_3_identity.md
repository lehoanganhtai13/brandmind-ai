# Phase 3: Brand Identity & Expression

## Orchestrator Guidance

This phase continues with the `brand-positioning-identity` sub-skill.
Visual asset generation delegates to `creative-studio` sub-agent.

### Mentor Script

#### Opening
"Positioning đã xong, giờ mình sẽ 'mặc áo' cho thương hiệu. Giai đoạn này là Brand Identity — personality, voice, visual. Giống như một người — sau khi biết bạn là ai (positioning), giờ cần biết bạn nói năng, ăn mặc, hành xử ra sao."

#### Concepts to Explain
- **Brand Archetype** — 12 archetype (Hero, Creator, Caregiver...) giúp brand có personality nhất quán. Ví dụ: Starbucks = Explorer, McDonald's = Innocent
- **Brand Voice** — cách brand 'nói chuyện'. Ví dụ: formal vs casual, playful vs serious, expert vs friend
- **Distinctive Brand Assets (DBA)** — assets mà người ta nhận ra brand mà không cần đọc tên: logo shape, color, jingle, mascot, font

### Delegation Pattern
1. YOU define personality, voice, naming with user
2. Delegate mood board generation to `creative-studio` sub-agent
3. Delegate logo concept directions to `creative-studio` sub-agent
4. Delegate color palette visualization to `creative-studio` sub-agent
5. YOU validate visual direction against positioning

## Quality Gate

- [ ] **p3_knowledge_verified**: Key concepts verified via KG and/or doc search before applying (brand archetype, personality dimensions, distinctive brand assets, brand naming criteria)
- [ ] **p3_personality**: Brand personality defined (archetype + traits with do/don't)
- [ ] **p3_voice**: Brand voice guidelines with do/don't examples
- [ ] **p3_naming**: Brand name finalized (new: full process; rebrand: keep/rename justified)
- [ ] **p3_visual**: Visual identity direction documented (colors, typography, imagery)
- [ ] **p3_mood_boards**: At least 2-3 mood board/concept images generated
- [ ] **p3_dba**: Distinctive Brand Assets strategy planned
- [ ] **p3_transition**: [Rebrand only] Identity transition plan completed

**BEFORE proceeding**: Call `report_progress(advance=True)` to move to the next phase in sequence.
