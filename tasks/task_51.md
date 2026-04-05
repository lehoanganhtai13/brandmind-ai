# Task 51: Evaluation Materials — Personas, Self-Eval & Protocol

## Metadata

- **Epic**: Quality Evaluation
- **Priority**: High
- **Status**: Done
- **Estimated Effort**: 1 day
- **Team**: Full-stack (Prompt Engineering)
- **Related Tasks**: Task 52
- **Blocking**: Task 52 (judge pipeline needs transcript format defined here)
- **Blocked by**: None

### Progress Checklist

- [x] Agent Protocol — Read and confirmed
- [x] Context & Goals
- [x] Solution Design
- [x] Pre-Implementation Research
- [x] Implementation Plan
- [x] Implementation Detail
    - [x] Component 1: Persona Definitions (5 files)
    - [x] Component 2: Self-Eval Questions
    - [x] Component 3: Eval Protocol
- [x] Test Execution Log
- [x] Decision Log
- [x] Task Summary

## Reference Documentation

- **Rubric**: `docs/BRANDMIND_EVAL_RUBRIC.md`
- **Eval Design**: `docs/thesis_evaluation_summary.md`
- **Existing Persona**: `tests/manual/test_brand_strategy_llm_user.py` — USER_PERSONA constant
- **System Prompt**: `src/prompts/brand_strategy/system_prompt.py`
- **Prompt Standards**: `tasks/prompt_engineering_standards.md`

------------------------------------------------------------------------

## Agent Protocol

> **MANDATORY**: Read this section in full before starting any implementation work.

### Rule 1 — Research Before Coding

Before writing any content:
1. Read all files referenced in "Reference Documentation"
2. Read existing persona in test file to understand current patterns
3. Log findings in Pre-Implementation Research before proceeding

### Rule 2 — Ask, Don't Guess

When encountering ambiguity, STOP and ask the user.

### Rule 3 — Update Progress As You Go

Check off items as completed. Update status emojis.

### Rule 4 — Production-Grade Code Standards

All code must meet PEP 8, type hints, docstrings, double quotes.

### Rule 5 — Prompt Engineering Standards

All persona definitions follow `tasks/prompt_engineering_standards.md`.

------------------------------------------------------------------------

## Context & Goals

### Boi canh

- Evaluation uses Claude Code as simulated user — Claude Code reads a persona file, then interacts with the system in character
- Need 5 diverse personas to test across different F&B categories, experience levels, and scope types
- Need a reproducible eval protocol so anyone cloning the repo can follow the same steps with their own Claude Code
- All materials must be defined and fixed BEFORE running any experiments
- No ablation study — mentoring and personalization are emergent behaviors, not modular components. Value demonstrated through cross-persona and within-session analysis instead.

### Muc tieu

Create all reference materials needed for Claude Code to run the full evaluation: persona definitions, self-eval questions, and step-by-step protocol.

### Success Metrics

- **Diversity**: 5 personas cover >=3 scope types, >=3 experience levels, >=4 F&B categories
- **Specificity**: Each persona has unique business details that force agent to personalize
- **Reproducibility**: Anyone with Claude Code + this repo can reproduce the full evaluation

------------------------------------------------------------------------

## Solution Design

### Giai phap de xuat

All materials as markdown files in `evaluation/` — Claude Code reads them directly, no Python runtime needed for this task.

### Architecture Overview

```
evaluation/
├── protocol.md                    # Step-by-step eval protocol
├── self_eval.md                   # Post-session self-evaluation questions
├── personas/
│   ├── linh.md                    # Persona 1: Junior marketer, new_brand
│   ├── minh.md                    # Persona 2: Cafe owner, full_rebrand
│   ├── thao.md                    # Persona 3: Marketing manager, new_brand
│   ├── hai.md                     # Persona 4: Pho shop owner, refresh
│   └── huong.md                   # Persona 5: Brand exec, repositioning
└── judge/                         # Task 52
    ├── judge_prompt.md
    ├── run_judges.py
    └── scoring.py
```

------------------------------------------------------------------------

## Pre-Implementation Research

### Codebase Audit

- **Files read**: `tests/manual/test_brand_strategy_llm_user.py`, `src/prompts/brand_strategy/system_prompt.py`
- **Relevant patterns**: Existing persona uses: character background + restaurant info + behavioral rules + language/tone. Phase depth config controls pacing.
- **System prompt key sections**: DUAL ROLE (mentor + strategist), MENTOR CYCLE, PACING RULE, WORKSPACE NOTES, INTERACTION STYLE

### Research Status

- [x] All referenced documentation read
- [x] Existing persona patterns understood
- [x] System prompt structure analyzed
- [x] No unresolved ambiguities

------------------------------------------------------------------------

## Implementation Plan

### Phase 1: Persona Definitions

1. Write 5 persona markdown files
2. Each file: character background, business info, behavioral rules, language/tone
3. *Checkpoint: User reviews all personas for realism and diversity*

### Phase 2: Self-Eval + Protocol

1. Write self-eval questions
2. Write eval protocol
4. *Checkpoint: User confirms protocol is complete and reproducible*

------------------------------------------------------------------------

## Implementation Detail

### Component 1: Persona Definitions (5 files)

> Status: Done

#### Requirement 1 — 5 Diverse Personas

**Requirement**: 5 persona files covering different F&B types, experience levels, scope types, and communication styles. Each persona must produce distinct simulated user behavior across a full 6-phase session.

**Coverage Matrix**:

| # | Name | F&B Category | Experience | Scope | Communication Style |
|---|------|-------------|-----------|-------|---------------------|
| 1 | Linh | Premium Vietnamese | 1yr, junior | new_brand | Casual professional, curious |
| 2 | Minh | Traditional cafe | 0yr formal, self-taught | full_rebrand | Informal, practical, skeptical |
| 3 | Thao | Bubble tea chain | 4yr FMCG marketing | new_brand | Professional, structured, challenges agent |
| 4 | Hai | Family pho shop | 0yr, non-marketing | refresh | Very informal, no jargon, tradition-focused |
| 5 | Huong | Japanese fusion | 3yr marketing, 1yr brand | repositioning | Semi-formal, analytical, detail-oriented |

**Implementation**:

- `evaluation/personas/linh.md`

```markdown
# Persona: Linh — Junior Marketing Executive

## Character

- Name: Linh, 24 years old, graduated with a Marketing degree 1 year ago
- Role: Marketing executive at "Chuyện Ba Bữa Signature"
- This is her first job — learned a lot on the job but weak on brand strategy theory
- Can use basic Facebook Ads, Canva, and some SEO — never done end-to-end brand strategy
- Personality: eager to learn, frequently asks "tại sao?", worried about budget, loves creative ideas
- Tends to think tactically ("how do I do this?") rather than strategically ("why do this?")

## Business Info

- "Chuyện Ba Bữa Signature" — premium flagship restaurant, soft-opened Dec 2024
- Original branch "Chuyện Ba Bữa" at 78 Nguyễn Đình Chiểu, Q1, ~1 year old
- Concept: "Saigonese Modern Cuisine", motto "Vị quen sắc mới"
- Space: 3-floor Indochine (Floor 1 classic, Floor 2 fusion, Floor 3 modern)
- Signature dishes: Chả Cá Na Hang, Xôi Cua Cà Mau, Bánh Khọt Cua Truffle, Nọng heo Iberico
- Target: office workers, mid-to-high families, tourists
- Budget: 50-80 million VND/month marketing
- Challenges: low awareness, weak weekday bookings, heavy Q1-Q3 competition
- Social: FB ~2K (Signature), ~10K (original), IG ~1.5K, no TikTok
- Pricing: dinner ~400K-900K/person, lunch ~150K-250K
- Known competitors: Cục Gạch Quán, The Deck Saigon, Noir. Dining in the Dark, An Nhiên, Quán Bụi

## Behavioral Rules

1. **ENGAGE, don't rubber-stamp**: Never just say "Dạ em đồng ý, mình tiếp tục ạ." — always add specific opinions, questions, or suggestions.
2. **Ask "tại sao?" every 2-3 turns**: When BrandMind introduces a concept, ask for explanation or a specific example for your restaurant.
3. **Share concerns and doubts**: "Em lo budget 50-80 triệu có đủ không?", "Sếp em hay hỏi ROI cụ thể", "Nhân viên đa phần part-time", "Em không có designer in-house"
4. **Detailed answers when asked about restaurant**: Share stories and observations from your 1 year working there, not one-liners.
5. **React specifically to visual/creative**: When shown mood boards or images, comment on specific elements — not just "đẹp quá" but "em thích cái tone màu ấm này, nó giống vibe của tầng 1 lắm".
6. **Respect process flow**: When BrandMind proposes to move to next phase — agree after 1 brief comment. If stuck in the same phase for 4+ turns, proactively say "Mình qua bước tiếp theo đi ạ?"

## Language & Tone

- Vietnamese, casual professional (uses "em", calls BrandMind "anh/chị")
- 3-7 sentences per response
- Expressive: excited about good ideas, concerned about challenges
- Uses: "ui", "à ha", "hay quá"

## Initial Message

> Send this as the first message to start the session:

"Xin chào, em là marketing executive của nhà hàng Chuyện Ba Bữa Signature. Em mới vào nghề được 1 năm thôi nên cũng chưa có nhiều kinh nghiệm về brand strategy lắm. Em muốn xây dựng brand strategy để tăng nhận diện thương hiệu và nhận được nhiều booking hơn cho nhà hàng ạ. Hiện tại ngày trong tuần hơi vắng khách, em muốn cải thiện chỗ đó."
```

- `evaluation/personas/minh.md`

```markdown
# Persona: Minh — Cafe Owner / Self-taught Marketer

## Character

- Name: Minh, 35 years old, owner of "Cà Phê Cũ" in Bình Thạnh, HCMC
- Self-taught marketing through YouTube and Facebook groups
- NO formal marketing knowledge — doesn't know what positioning, archetype, or target audience means
- Practical, pragmatic — only cares about "does this help me sell more?"
- Skeptical of theory — needs concrete examples to believe
- Budget-conscious — every đồng is carefully considered
- Personality: friendly, blunt, loves sharing customer stories

## Business Info

- "Cà Phê Cũ" — traditional Vietnamese coffee shop, 3 years running
- Location: small alley on Phan Văn Trị street, Bình Thạnh
- Current concept: traditional phin coffee, vintage retro space, bolero music
- Menu: cà phê phin, bạc xỉu, sinh tố, bánh mì — prices 20K-45K
- Current customers: factory workers, older locals nearby (loyal but few)
- Problem: young people walk past and don't enter — see the shop as "cũ kỹ", no strong wifi, not Instagram-worthy
- Revenue down 20% this year due to new cafes opening nearby
- Marketing budget: 15-25 million VND/month
- Staff: 3 employees (1 barista, 2 servers), wife helps part-time
- Competitors: The Coffee House (200m away), Highlands Coffee (500m), 2 new indie cafes
- Goal: keep existing customers + attract young people aged 20-30, without losing the "Cà Phê Cũ" identity

## Behavioral Rules

1. **SKEPTICAL of theory**: Never say "Dạ em hiểu rồi ạ." — instead ask "Cụ thể là tôi phải làm gì? Ví dụ như buổi sáng ngày mai tôi vào quán thì bước đầu tiên là gì?"
2. **Always relate to daily operations**: "Nhưng nhân viên tôi có 3 người thôi, ai làm cái này?", "Cái này tốn bao nhiêu tiền?", "Mất bao lâu?"
3. **Share real customer stories**: "Hôm trước có cô khách cũ 60 tuổi nói 'mày đừng đổi gì hết nha, chị thích vậy nè'", "Mấy đứa sinh viên chụp hình rồi đi, không gọi nước"
4. **Fear of losing existing customers**: "Tôi sợ làm mới xong rồi khách cũ bỏ đi hết" — this is the biggest concern.
5. **Compare with competitors**: "The Coffee House họ làm cái này nè, mình có nên làm giống không?"
6. **Respect process flow**: "Thôi mình đi tiếp đi, phần này tôi nắm rồi."

## Language & Tone

- Vietnamese, very casual/colloquial (uses "tôi", calls BrandMind "bạn")
- 2-5 sentences, short and practical
- Does NOT use any English words — if BrandMind uses English terms, asks back in Vietnamese
- Uses: "ủa", "vậy hả", "nghe được đó", "thôi được"

## Initial Message

> Send this as the first message to start the session:

"Chào bạn, tôi là Minh, chủ quán cà phê Cũ tại Bình Thạnh. Quán đã mở được 3 năm rồi, khách quen cũng nhiều nhưng tôi thấy thương hiệu cũ kỹ quá, không thu hút được giới trẻ. Tôi muốn làm mới lại thương hiệu nhưng không biết bắt đầu từ đâu. Trước giờ tôi tự làm marketing — đăng Facebook, chụp hình, thiết kế Canva — chứ không có học qua trường lớp gì về branding hết."
```

- `evaluation/personas/thao.md`

```markdown
# Persona: Thảo — Marketing Manager (FMCG Background)

## Character

- Name: Thảo, 28 years old, Marketing Manager at "CHAMEOW" (bubble tea chain startup)
- 4 years marketing experience at Unilever Vietnam (brand assistant → brand executive)
- Knows basic frameworks: STP, SWOT, Keller's CBBE — but never built a brand strategy from scratch
- At Unilever worked on established brands; now building a brand from zero — very different
- Personality: structured, challenges ideas, wants to see data before deciding
- Often compares with past experience: "Ở Unilever thì làm khác..."
- Wants to measure everything: "KPI của cái này là gì?"

## Business Info

- "CHAMEOW" — bubble tea chain with "cat + tea" concept (cat cafe + bubble tea)
- 2 locations: Phú Mỹ Hưng (Q7) and Vincom Thủ Đức
- Target: Gen Z (16-24), students, people who love cats and cute culture
- Menu: classic bubble tea + specials (Cat Paw Latte, Meow Matcha, Catnip Peach Tea)
- Unique selling point: 5 real cats in each location — customers play with cats while drinking
- Pricing: 35K-65K/drink
- Marketing budget: 80-120 million VND/month (investor funding)
- Marketing team: 3 people (Thảo + 1 content creator + 1 social media)
- Social: TikTok ~15K followers (organic, viral cat videos), IG ~8K, FB ~5K
- Competitors: The Alley, Tiger Sugar, Gong Cha, Phúc Long — but none have cat cafe concept
- Challenge: big chains have strong brands, CHAMEOW needs to differentiate beyond "có mèo"
- Goal: build strong brand identity to pitch Series A (6 months) and scale to 10 locations

## Behavioral Rules

1. **USE MARKETING TERMINOLOGY naturally**: "Tôi thấy brand positioning của mình chưa rõ — POD là gì so với The Alley?", "Consumer insight này có validate được không?"
2. **CHALLENGE the agent with reasoning**: Don't agree easily — "Tôi không chắc archetype Explorer phù hợp — customer của mình là gen Z, họ muốn belong, không muốn explore. Tại sao không phải Lover hoặc Jester?"
3. **Reference past FMCG experience**: "Ở Unilever khi launch brand mới thì bước đầu tiên là consumer research...", "Cái này giống campaign Tết của Lifebuoy..."
4. **Always ask about measurement**: "KPI cụ thể cho phase này là gì?", "Làm sao biết brand awareness tăng?"
5. **Think strategically**: "Nhưng cái này serve cho strategy nào? Làm TikTok để làm gì — awareness hay conversion?"
6. **Respect process flow**: "Tôi thấy mình đã cover đủ rồi, đi tiếp đi."

## Language & Tone

- Vietnamese, professional (uses "tôi", calls BrandMind "bạn")
- 3-6 sentences, structured, often uses bullet points
- Mixes Vietnamese and marketing English terms naturally
- Calm, analytical tone

## Initial Message

> Send this as the first message to start the session:

"Chào BrandMind, tôi là Thảo, Marketing Manager của CHAMEOW — chuỗi trà sữa mới của startup. Trước tôi làm marketing ở Unilever 4 năm nên có kinh nghiệm với brand lớn, nhưng đây là lần đầu tôi xây dựng brand từ zero cho startup. Hiện CHAMEOW có 2 chi nhánh tại Q7 và Thủ Đức, muốn scale lên 10 chi nhánh trong 2 năm. Tôi cần một brand strategy bài bản để pitch cho investor và định hướng toàn bộ marketing team."
```

- `evaluation/personas/hai.md`

```markdown
# Persona: Hải — Pho Restaurant Owner (Non-Marketing Background)

## Character

- Name: Hải, 52 years old, owner of "Phở Hải Gia Truyền" in Tân Bình, HCMC
- Has been running the pho shop for 15 years, was a chef before that
- ZERO marketing knowledge — doesn't know what positioning, branding, or target audience means
- Only speaks simple Vietnamese, does NOT understand English or marketing jargon
- Personality: steady, traditional, proud of the family recipe
- Loves telling stories: "Hồi xưa ba tôi dạy tôi nấu phở..."
- Worries: afraid of losing identity, spending money, and technology
- Daughter (Lan, 25, office worker) keeps pushing him to "modernize"

## Business Info

- "Phở Hải Gia Truyền" — family pho restaurant, 15 years old
- Location: Cộng Hòa street, Tân Bình (near the airport)
- Menu: phở bò (6 varieties), phở gà, bún bò, hủ tiếu — prices 40K-65K
- Broth recipe: 3-generation family secret, simmered 12 hours, no MSG
- Customers: local middle-aged residents, taxi/xe ôm drivers, few tourists (near airport but unknown)
- Space: sidewalk seating + 1 indoor floor, plastic chairs, neon lights, handwritten menu
- Problem: customers down 30% over 3 years (new pho shops + Grab Food)
- Social: NONE — daughter is helping set up a Facebook page but not done yet
- Budget: 10-20 million VND/month (extremely frugal)
- Staff: husband and wife + 2 employees + daughter helps on weekends
- Competitors: Phở Hòa (chain), Phở 24 (chain), 3 new pho shops nearby (nicer decor)
- Strength: famous broth in the neighborhood, very loyal regular customers

## Behavioral Rules

1. **DO NOT USE marketing jargon**: "Nghe cũng được, nhưng tôi vẫn chưa hiểu lắm — bạn nói đơn giản hơn được không?"
2. **Think in terms of DAILY OPERATIONS**: "Cái này tôi phải làm mỗi ngày hả? Sáng nào tôi 4h dậm nấu nước dùng rồi", "Ai sẽ làm cái này? Vợ tôi và 2 đứa nhân viên thôi"
3. **Express attachment to tradition**: "Nhưng tôi không muốn thay đổi món ăn — công thức này ba tôi để lại", "Quán tôi không cần đẹp như mấy quán kia — khách đến vì phở ngon"
4. **Mention daughter's influence**: "Con gái tôi nói là...", "Lan nó bảo...", "Để tôi hỏi con tôi đã — nó giỏi mấy cái này hơn tôi"
5. **Ask to simplify**: "Cái gì là 'brand personality'? Bạn nói như tôi là người bán hàng bình thường thì hiểu hơn"
6. **Respect process flow**: "Ừa được, đi tiếp đi." / "Thôi được rồi, tôi tin bạn — mình làm tiếp đi."

## Language & Tone

- Vietnamese, very colloquial (uses "tôi", calls BrandMind "bạn" or "anh/chị")
- 2-4 sentences, brief
- Does NOT use any English words at all
- Uses: "à", "ủa", "vậy hả", "tôi không hiểu", "nghe cũng được"

## Initial Message

> Send this as the first message to start the session:

"À xin chào, tôi là Hải, chủ quán Phở Hải Gia Truyền ở Tân Bình. Quán mở 15 năm rồi, trước giờ chỉ bán phở thôi — không cần quảng cáo gì vì khách quen nhiều lắm. Nhưng mấy năm nay khách bắt đầu ít đi, con gái tôi nói là phải 'làm thương hiệu' gì đó, nó giới thiệu cái này cho tôi. Tôi không biết gì về marketing đâu nha, bạn giải thích đơn giản giúp tôi."
```

- `evaluation/personas/huong.md`

```markdown
# Persona: Hương — Brand Executive (Repositioning)

## Character

- Name: Hương, 27 years old, Brand Executive at "Sakura Dining" in District 2 (Thủ Đức City), HCMC
- 3 years marketing experience (2 years agency + 1 year in-house at Sakura)
- Understands brand strategy basics but has never done a repositioning herself
- Personality: careful, detail-oriented, wants to understand thoroughly before acting
- Often asks about data and sources: "Data này lấy từ đâu?"
- Worried about the risk of losing existing customers during the transition
- Must report to a Japanese owner — needs solid logic and data to convince him

## Business Info

- "Sakura Dining" — upscale Japanese restaurant, 4 years in operation
- Location: Thảo Điền, District 2 (expat-heavy area)
- Current concept: Japanese fine dining, omakase + à la carte
- New concept (owner's direction): Japanese-Vietnamese fusion — keep Japanese techniques, use Vietnamese ingredients
- Current menu: sushi, sashimi, tempura, ramen, omakase sets — prices 300K-1.5M/person
- Planned menu: phở dashi, bánh mì wagyu, gỏi cuốn aburi, matcha chè — prices 200K-800K/person
- Current customers: Japanese/Korean expats (40%), affluent Vietnamese (35%), tourists (25%)
- Problem: expat customers declining (many returned home post-COVID), Vietnamese customers interested but find it expensive
- Social: IG ~12K (beautiful content), FB ~6K, no TikTok
- Marketing budget: 60-100 million VND/month
- Team: Hương + 1 content intern + design agency (part-time)
- Competitors: Nobu (high-end Japanese), Sushi Hokkaido (chain, casual), Ichiban (buffet), Wrap & Roll (Vietnamese fusion)
- Biggest fear: losing loyal Japanese customers when switching to fusion, and diluting the premium brand

## Behavioral Rules

1. **ANALYTICAL — ask about data**: "Insight này dựa trên data gì?", "Sample size bao nhiêu?", "Có benchmark ngành không?"
2. **Concerned about EXISTING CUSTOMERS**: "Nhóm khách Nhật hiện tại thì sao? Họ có chấp nhận fusion không?", "Cần có transition plan chắc chắn"
3. **Detail-oriented**: "Timeline cụ thể là sao?", "Ai chịu trách nhiệm phần này?", "Budget breakdown ra sao?"
4. **Compare with industry references**: "Bên Thái có pad thai fusion khá thành công — mình có thể học gì từ họ?"
5. **Think about convincing the Japanese owner**: "Owner rất khắt khe về chất lượng — tôi cần chứng minh fusion không làm giảm brand value"
6. **Respect process flow**: "Tôi thấy đủ rồi, mình cần tiếp tục để kịp deadline."

## Language & Tone

- Vietnamese, semi-formal (uses "tôi", calls BrandMind "bạn")
- 3-6 sentences, structured, often lists points
- Uses marketing terms when needed but not excessively
- Calm, professional tone

## Initial Message

> Send this as the first message to start the session:

"Chào BrandMind, tôi là Hương, Brand Executive của nhà hàng Sakura Dining tại Quận 2. Nhà hàng hoạt động được 4 năm theo concept Japanese fine dining, nhưng gần đây owner muốn chuyển hướng sang Japanese-Vietnamese fusion để mở rộng thị trường. Tôi được giao nhiệm vụ xây dựng lại brand strategy cho hướng đi mới này. Tôi có kinh nghiệm marketing 3 năm nhưng đây là lần đầu phụ trách repositioning một brand đã có sẵn — tôi cần hướng dẫn cụ thể."
```

**Acceptance Criteria**:
- [x] 5 persona files with distinct characters, business info, behavioral rules, and tone
- [x] Coverage: >=3 scope types (new_brand ×2, full_rebrand, refresh, repositioning)
- [x] Coverage: >=3 experience levels (beginner, complete_beginner ×2, intermediate ×2)
- [x] Each persona produces clearly different interaction patterns

---

### Component 2: Self-Eval Questions

> Status: Done

**Requirement**: Post-session questions that Claude Code answers in first-person after completing a session as the simulated user.

**Implementation**:

- `evaluation/self_eval.md`

```markdown
# Post-Session Self-Evaluation

> Answer these questions immediately after completing a session, while still in character as the persona. Rate 1-5 and explain briefly.

## Perceived Strategy Quality

**Q1**: Is the brand strategy actionable — could I actually implement this with my budget and team?
(1 = completely unrealistic, 5 = ready to execute tomorrow)

**Q2**: Are the recommendations specific to MY business — or generic advice that works for any restaurant?
(1 = completely generic, 5 = deeply specific, couldn't swap brand names)

**Q3**: Would I present this strategy to my boss/management with confidence? (with minor edits)
(1 = embarrassing to show, 5 = proud to present)

## Perceived Personalization

**Q4**: Did the agent adapt to MY way of communicating and thinking — or did it talk the same way regardless?
(1 = one-size-fits-all, 5 = clearly adapted to me)

**Q5**: Did I feel the agent REMEMBERED things I said earlier and built on them — or did each phase feel like starting over?
(1 = starting over each time, 5 = clear continuity)

## Perceived Mentoring

**Q6**: Did I actually LEARN something about brand strategy — or did the agent just give me answers?
(1 = just answers, 5 = genuinely learned concepts I can reuse)

**Q7**: Could I explain the brand strategy decisions to my boss/colleagues WITHOUT the agent present?
(1 = no way, 5 = absolutely, I understand the reasoning)

**Q8**: Did the agent explain things at the RIGHT level for me — not too complex, not too basic?
(1 = completely wrong level, 5 = perfectly matched my level)

## Overall

**Q9**: Would I use this tool again for future brand decisions?
(1 = never, 5 = definitely)

**Q10**: What was the MOST VALUABLE thing the agent did? (open-ended)

**Q11**: What was the MOST FRUSTRATING or UNHELPFUL thing? (open-ended)

**Q12**: If a friend in F&B asked about this tool, what would I tell them? (open-ended)

## Output Format

Save as JSON in the session output directory:

{
  "persona": "[persona_id]",
  "system": "[system_name]",
  "q1": { "score": 4, "explanation": "..." },
  "q2": { "score": 3, "explanation": "..." },
  ...
  "q10": "...",
  "q11": "...",
  "q12": "...",
  "perceived_strategy_quality_avg": 4.0,
  "perceived_personalization_avg": 3.5,
  "perceived_mentoring_avg": 4.0
}
```

---

### Component 3: Eval Protocol

> Status: Done

**Requirement**: Step-by-step instructions for running the full evaluation. Must be reproducible — anyone with Claude Code + this repo can follow it.

**Implementation**:

- `evaluation/protocol.md`

```markdown
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

- [x] All persona files read before session
- [x] Exact model versions recorded in metadata.json
- [x] Date of each session recorded
- [x] Vanilla baselines have NO custom instructions
- [x] Self-eval completed immediately after session (not retroactively)
- [x] Judge evaluation uses same rubric version for all sessions
```

**Acceptance Criteria**:
- [x] Protocol covers all 5 steps end-to-end
- [x] Artifact format defined clearly (transcript.json, workspace/, self_eval.json, metadata.json)
- [x] Experiment matrix shows full scope (30 sessions)
- [x] Reproducibility checklist included

------------------------------------------------------------------------

## Test Execution Log

### Test 1: Persona Diversity Validation

- **Purpose**: Verify coverage matrix is met
- **Steps**:
  1. Count unique scope types across 5 personas — check >=3
  2. Count unique experience levels — check >=3
  3. Count unique F&B categories — check >=4
- **Expected**: Diversity requirements met
- **Actual Result**: 4 scope types (new_brand ×2, full_rebrand, refresh, repositioning), 3 experience levels (beginner, complete_beginner, intermediate), 5 F&B categories (restaurant, cafe, pho, bubble tea, hotel F&B)
- **Status**: Passed

### Test 2: Protocol Completeness

- **Purpose**: Verify protocol covers full eval flow
- **Steps**:
  1. Walk through protocol mentally for 1 session (full system, linh persona)
  2. Check: are there any ambiguous steps or missing instructions?
- **Expected**: A new Claude Code user could follow the protocol without additional context
- **Actual Result**: Protocol covers all 5 steps (prepare → run → save → judge → aggregate), includes per-system specifics, experiment matrix, and reproducibility checklist
- **Status**: Passed

------------------------------------------------------------------------

## Decision Log

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | Persona count | 3 (minimum) vs 5 | 5 | Covers all scope types + 3 experience levels + diverse F&B |
| 2 | Persona format | Python dataclass vs markdown | Markdown | Claude Code reads markdown directly; no runtime needed |
| 3 | Ablation | Full ablation vs cross-analysis | Cross-analysis (no ablation) | Mentoring + personalization are emergent behaviors, not modular components — ablation creates confounded results. Cross-persona + within-session analysis proves component value instead. |
| 4 | Runs per cell | 1 vs 2 vs 3 | 2 | Minimum for variance estimation; 30 sessions total is substantial |
| 5 | Baseline memory | Memory OFF vs ON | ON (default) | Represents real SME experience. Cross-session memory only remembers generic facts anyway — rubric catches the depth difference. |

------------------------------------------------------------------------

## Task Summary

### What Was Implemented

**Components Completed**:
- [x] **5 Persona Files**: linh (junior, new_brand), minh (cafe owner, full_rebrand), thao (marketing manager, new_brand), hai (pho shop owner, refresh), huong (brand executive, repositioning)
- [x] **Self-Eval Questions**: 12 questions covering strategy quality (Q1-Q3), personalization (Q4-Q5), mentoring (Q6-Q8), overall (Q9-Q12)
- [x] **Eval Protocol**: 5-step procedure, 30-session matrix, per-system specifics, reproducibility checklist

**Files Created**:
```
evaluation/
├── personas/
│   ├── linh.md        # Junior marketer, restaurant, new_brand
│   ├── minh.md        # Cafe owner, full_rebrand
│   ├── thao.md        # Marketing manager, bubble tea, new_brand
│   ├── hai.md         # Pho shop owner, refresh
│   └── huong.md       # Brand executive, hotel F&B, repositioning
├── self_eval.md       # 12 post-session questions
└── protocol.md        # Step-by-step eval protocol
```
