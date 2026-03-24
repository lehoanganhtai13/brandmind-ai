# BrandMind AI — Brand Strategy Skills & Tools Blueprint

> **Scope**: F&B (Food & Beverage) brand strategy development — from business problem diagnosis to pre-implementation deliverables.
>
> **Purpose**: Define the complete skills, tools, sub-agents, and workflow needed for the BrandMind agent to guide users through professional brand strategy development.
>
> **Date**: 2026-02-28
>
> **Status**: Draft — awaiting review

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Research Foundations](#2-research-foundations)
3. [Brand Strategy Workflow — The 6-Phase Process](#3-brand-strategy-workflow--the-6-phase-process)
4. [Skills Architecture](#4-skills-architecture)
5. [Tools Inventory](#5-tools-inventory)
6. [Sub-Agents & Delegation Strategy](#6-sub-agents--delegation-strategy)
7. [Integration: How Skills + KG + Tools Work Together](#7-integration-how-skills--kg--tools-work-together)
8. [Appendix](#8-appendix)

---

## 1. Executive Summary

### 1.1 What This Document Covers

This blueprint defines everything needed for the BrandMind agent to conduct a professional brand strategy engagement for an F&B business — from the initial business problem diagnosis to a complete brand strategy plan ready for implementation.

**Key deliverables defined:**
- **6-Phase Brand Strategy Workflow** (+ conditional Phase 0.5 Brand Equity Audit for existing brands) — refined from the original 5-phase baseline using domain expert input, KG knowledge, and professional marketing frameworks
- **Workflow Branching** — different execution paths for new brand, refresh, repositioning, and full rebrand scenarios
- **4 Skills** — procedural skeletons that guide the agent through each phase
- **17 Tools** (7 existing + 10 new) — the capabilities the agent needs
- **4 Specialized Sub-Agents** — for delegating complex parallel workstreams
- **Integration Model** — how Skills, Knowledge Graph, and Tools work together at runtime

### 1.2 Key Design Principles

1. **"Brand Strategy giải quyết vấn đề kinh doanh"** — Brand is never built in isolation; it solves a specific business problem (revenue, differentiation, market entry, etc.)
2. **5W1H as the thinking spine** — WHO (target), WHY (insight), WHAT (offering/brand), HOW (strategy/tactics), WHERE (channels), WHEN (timeline) — with WHO and WHY as the most critical
3. **Research-first, opinion-last** — Every decision must be grounded in evidence (KG domain knowledge + real-time market data)
4. **Mentor-Execute Loop per phase** — Explain → Execute → Review → Iterate
5. **Stop before implementation** — The output is a comprehensive brand strategy document, NOT the execution of marketing campaigns

### 1.3 Scope Boundary

```
IN SCOPE (this blueprint):                    OUT OF SCOPE:
─────────────────────────                      ─────────────
✅ Business problem diagnosis                  ❌ Campaign execution
✅ Market & competitive research               ❌ Media buying
✅ Target audience definition                  ❌ Social media management
✅ Brand positioning & differentiation         ❌ Website development
✅ Brand identity & personality                ❌ Ongoing brand management
✅ Brand messaging & communication framework   ❌ Sales enablement
✅ Visual identity direction                   ❌ Post-launch optimization
✅ Brand strategy document/report              ❌ Brand valuation/finance
```

---

## 2. Research Foundations

### 2.1 Sources Used

| Source | Type | Key Contribution |
|--------|------|-----------------|
| **Brand Manager Interview** (handwritten notes) | Expert practitioner | Real-world process: 5W1H framework, business-problem-first approach, STP → Insight → Benefit → RTB flow |
| **Knowledge Graph** (27K entities, 30K relationships) | Domain knowledge | Academic frameworks: CBBE Pyramid, Brand Value Chain, Positioning theory, Double Jeopardy, 7 Persuasion Principles |
| **Marketing Skills Repo** (coreyhaines31) | Procedural reference | Skill structures: product-marketing-context, content-strategy, copywriting, competitor-alternatives, marketing-psychology |
| **Keller — Strategic Brand Management** | KG + Doc Library | CBBE model (Salience → Performance/Imagery → Judgments/Feelings → Resonance), brand element selection criteria, brand equity measurement |
| **Kotler — Principles of Marketing** | KG + Doc Library | STDP framework, marketing mix (4Ps), consumer buying behavior, integrated marketing communications |
| **Ries & Trout — Positioning** | KG + Doc Library | Mental positioning, category leadership, ladder in the mind, repositioning strategies |
| **Sharp — How Brands Grow** | KG + Doc Library | Double Jeopardy law, mental & physical availability, distinctive brand assets, penetration over loyalty |
| **Cialdini — Influence** | KG + Doc Library | 7 principles of persuasion (reciprocity, commitment, social proof, authority, liking, scarcity, unity) |

### 2.2 Key Insights from Brand Manager Interview

From the handwritten notes analysis:

**Hình 1 — Business Context Flow:**
```
Chiến lược kinh doanh → Chiến lược Marketing → Chiến lược Brand
     ↓                       ↓
  Doanh thu              Ngành hàng
  Lợi nhuận

  1. Tình hình KD (e.g., café house) dạy sao → Bill, SP, Doanh thu, Lợi nhuận
  2. Sức khỏe thương hiệu: đang làm sao? Chỉ số nào?
  3. Sản phẩm: giá có bị gì?

  → Vấn đề Brand là gì? → Kế hoạch giải quyết!
```

**Core insight**: Brand strategy ALWAYS starts from a **business problem**. The brand manager first understands:
- Current business performance (revenue, profit, transactions)
- Brand health metrics (awareness, perception, loyalty)
- Product/pricing issues

Then identifies: **"Vấn đề Brand là gì?"** (What is the brand problem?) → Creates a plan to solve it.

**Hình 2 — 5W1H Framework:**
```
        HOW (+ HOW MUCH)
  WHAT    WHERE    WHEN
    WHO      WHY
```
Circled together: **WHO** and **WHY** — the two most critical questions. Everything else flows from deeply understanding WHO your customer is and WHY they behave the way they do.

**Hình 3 — Detailed Strategy Flow:**
```
5W1H
├── WHY: Người ta cần suy nghĩ, tư duy
│   └── WHO: B2C → Consumer
│         B2B → Cty, dtc, ngân hàng
├── WHAT: Brand plan cần gì?
│   └── Phát triển thương hiệu (Logo, brand key)
├── WHERE
├── WHEN: To
├── HOW: 
│   ├── Tính cách → Giá trị cốt lõi (Brand Key)
│   └── G → Who + STP
│
├── STP: Segmentation → Targeting → Positioning
│   ├── Đối thủ là ai? (Trực tiếp, Gián tiếp)
│   ├── Insights
│   ├── Benefit: Lý tính / Cảm xúc
│   ├── Tính cách thương hiệu (RTB)
│   ├── Giá trị & tính cách
│   ├── Điểm khác biệt lớn nhất
│   └── Câu chuyện ngắn gọn cuộc sống
│
├── Mô hình AIDA
│
└── CL Truyền thông = CL kênh truyền thông
    ├── Nội dung → Hình ảnh, Video, Infographic
    │   ├── Thông điệp
    │   └── Bartender (content creator)
    ├── Hình thức: HOW, WHAT, WHERE, WHEN, WHO, WHY
    ├── KPI: Đo lường hiệu suất (so sánh)
    │   └── Có chỉ tiêu thì sẽ ∞
    └── Timeline → AI phụ trách
```

### 2.3 Key Frameworks from Knowledge Graph

**From KG Search — Strategic Brand Management Process (Keller):**
1. **Brand Planning** — Brand Positioning Model + Brand Resonance Model + Brand Value Chain
2. **Designing & Implementing** — Brand elements, marketing programs, secondary associations
3. **Measuring & Interpreting** — Brand audits, tracking studies, brand equity measurement
4. **Growing & Sustaining** — Brand architecture, brand portfolio, brand revitalization

**From KG Search — CBBE Pyramid:**
```
        ┌─────────────┐
        │  Resonance   │  ← Brand Relationships (loyalty, community, engagement)
        ├──────┬──────┤
        │Judg- │Feel- │  ← Brand Responses (quality, credibility, warmth, fun)
        │ments │ings  │
        ├──────┼──────┤
        │Perfor│Image-│  ← Brand Meaning (reliability, style, personality)
        │mance │ry    │
        ├──────┴──────┤
        │  Salience    │  ← Brand Identity (awareness, recognition, recall)
        └─────────────┘
```

**From KG Search — Sharp's Growth Laws:**
- Double Jeopardy: Small brands suffer twice (lower penetration AND lower loyalty)
- Growth = Penetration growth (acquiring new buyers), NOT loyalty programs
- Mental Availability: Probability brand comes to mind in buying situation
- Physical Availability: Ease of finding/buying the brand
- Distinctive Brand Assets: Visual/verbal cues that trigger brand recognition without the name

**From KG Search — Cialdini's 7 Principles:**
Reciprocity, Commitment & Consistency, Social Proof, Authority, Liking, Scarcity, Unity — applied to brand messaging to create persuasive communication.

---

## 3. Brand Strategy Workflow — The 6-Phase Process

### 3.0 Why 6 Phases (+ conditional Phase 0.5)?

The original 5-phase baseline from the Vision doc was:
1. Discovery & Research → 2. Positioning → 3. Messaging → 4. Visual Identity → 5. Guidelines & Implementation

After incorporating the Brand Manager's input, KG domain knowledge, professional frameworks, and **rebranding gap analysis** (based on Keller Ch.8/Ch.13 — Brand Audits, Brand Revitalization, Brand Reinforcement), the workflow is refined to:

- **6 core phases** with a new **Phase 0: Business Problem Diagnosis** at the front
- **Conditional Phase 0.5: Brand Equity Audit** — executed ONLY when the business has an existing brand (rebrand/refresh/repositioning cases)
- **Workflow branching** — different execution paths based on `scope` classification
- **Strategic Synthesis step** — bridging Phase 1 research data into Phase 2 strategic decisions
- **Proactive loop triggers** — when the agent should recommend revisiting a previous phase

This reflects the real-world practice that brand strategy must solve a business problem, not exist in isolation.

### 3.1 Overview

```
Phase 0          [Phase 0.5]      Phase 1          Phase 2          Phase 3          Phase 4          Phase 5
BUSINESS         BRAND EQUITY     MARKET           BRAND            BRAND            BRAND            BRAND STRATEGY
PROBLEM          AUDIT            INTELLIGENCE     STRATEGY         IDENTITY &       COMMUNICATION    PLAN &
DIAGNOSIS        (conditional)    & RESEARCH       CORE             EXPRESSION       FRAMEWORK        DELIVERABLES
                                                                                     
"Vấn đề là gì?"  "Brand hiện      "Thị trường      "Ta đứng ở       "Ta trông như     "Ta nói gì &     "Tất cả thành
  + Scope?"       tại sao?"        ntn? Ai là       đâu? Khác        thế nào?"        nói thế nào?"    1 bản kế hoạch"
                  (if existing)    KH? Đối thủ?"    biệt gì?"
                                                                                     
WHO + WHY        WHAT (equity)    WHO + WHERE      WHAT + WHY       HOW              HOW + WHERE      HOW MUCH + WHEN
(Business)       (existing)       (Market)         (Strategy)       (Identity)       (Messaging)      (Plan)
```

#### Workflow Branching by Scope

The `scope` determined in Phase 0 drives which phases and activities are executed:

```
┌─────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│   Scope     │  Phase 0     │  Phase 0.5   │  Phase 1     │  Phase 2     │  Phase 3     │  Phase 4-5   │
├─────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ NEW BRAND   │ Full         │ SKIP         │ Full         │ Full         │ Full         │ Full         │
│ REFRESH     │ Full         │ Light audit  │ Targeted     │ SKIP (keep)  │ Focus here   │ Adapt        │
│ REPOSITION  │ Full         │ Full audit   │ Full         │ Full (pivot) │ Evolve       │ Full         │
│ FULL REBRAND│ Full         │ Full audit   │ Full         │ Full (new)   │ Full (new)   │ Full + Trans.│
└─────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘

Key differences:
- REFRESH: Keep core positioning, update expression (look/feel). Phase 0.5 light audit to identify what to preserve.
- REPOSITION: New strategic direction, same brand identity elements where possible. Full audit to understand current equity.
- FULL REBRAND: Start fresh strategically, but Phase 0.5 audit ensures equity preservation where valuable.
```

### 3.2 Phase 0: Business Problem Diagnosis

**Purpose**: Understand the business context and identify the specific brand problem to solve. Brand strategy is not created in a vacuum — it addresses a real business challenge.

**Mentor Mode**: Explain why brand strategy must start from business context. Ask about the business.

**5W1H Focus**: **WHO** (business owner) + **WHY** (what business problem needs solving)

#### Required Inputs
- User provides business information (guided by agent questions)

#### Key Activities
| # | Activity | Description | KG Search Topics |
|---|----------|-------------|-----------------|
| 0.1 | Business Context Gathering | Understand: business type, location, current status, revenue situation | `"F&B business model types"`, `"business strategy marketing strategy relationship"` |
| 0.2 | Business Health Assessment | Current metrics: revenue, traffic, average transaction, profit margins | `"marketing metrics business performance"` |
| 0.3 | Brand Health Check | Current brand status: awareness, perception, loyalty indicators (if existing brand) | `"brand equity measurement"`, `"brand health metrics"` |
| 0.4 | Product/Service Audit | Menu/offering, pricing, quality perception, competitive pricing | `"product strategy pricing strategy"` |
| 0.5 | Problem Identification | Synthesize: What is the core brand problem? | `"brand revitalization"`, `"brand strategy development"` |

#### Quality Gate — Phase 0 Exit Criteria
- [ ] Business type and context clearly documented
- [ ] Current business performance understood (or "new business" status confirmed)
- [ ] Budget range and resource constraints understood
- [ ] Core brand problem/opportunity clearly articulated as a problem statement
- [ ] Scope classified (new brand / refresh / repositioning / full rebrand) with rationale
- [ ] If existing brand: Rebrand Decision Matrix scored and explained to user
- [ ] User confirms the problem statement and scope are accurate

#### Required Outputs
```yaml
phase_0_output:
  business_profile:
    business_name: str
    business_type: str  # café, restaurant, bar, bakery, etc.
    location: str
    business_stage: str  # new, early, growing, mature, declining
    current_status: str  # brief description
  
  business_metrics:  # null if new business
    monthly_revenue: str | null
    avg_transaction: str | null
    monthly_customers: str | null
    key_challenges: list[str]
  
  brand_status:
    has_existing_brand: bool
    brand_awareness_level: str | null  # unknown, low, medium, high
    current_perception: str | null
    existing_brand_assets: list[str] | null  # logo, name, colors, etc.
  
  budget_and_resources:
    estimated_budget: str  # e.g., "50-100M VND", "unknown"
    internal_capabilities: list[str]  # e.g., ["1 social media person", "chef as content creator"]
    constraints: list[str]  # e.g., ["no design team", "must launch in 2 months"]
    budget_tier: str  # bootstrap (<50M) / starter (50-200M) / growth (200M-1B) / enterprise (>1B)
  
  problem_statement:
    core_problem: str  # "The brand problem is..."
    business_impact: str  # How this affects the business
    desired_outcome: str  # What success looks like
    scope: str  # new_brand / refresh / repositioning / full_rebrand
    scope_rationale: str  # Why this scope was chosen
  
  rebrand_assessment:  # null if scope = "new_brand"
    decision_matrix_scores:  # score per signal
      brand_awareness: int  # 0-2
      brand_associations: int  # 0-2
      market_relevance: int  # 0-2
      competitive_position: int  # 0-2
      business_brand_alignment: int  # 0-2
      crisis_controversy: int  # 0-2
    total_score: int  # 0-12
    recommendation: str  # reinforce / refresh / reposition / full_rebrand / retire
    key_findings: list[str]  # supporting evidence for the recommendation
```

---

### 3.2.5 Phase 0.5: Brand Equity Audit (Conditional)

> **Condition**: This phase is executed ONLY when `scope ∈ {refresh, repositioning, full_rebrand}`. Skip entirely for `scope = "new_brand"`.

**Purpose**: Conduct a comprehensive brand audit (Keller Ch.8) to understand current brand equity — what to preserve, what to evolve, and what to discard. Without this, rebranding risks destroying valuable equity or carrying forward toxic associations.

**Mentor Mode**: Explain the concept of brand equity as an asset. "Before we build something new, we need to fully understand what you already have. Some brand elements may be more valuable than you think — and some may be holding you back."

**5W1H Focus**: **WHAT** (current equity) + **WHY** (what caused current state)

#### Required Inputs
- Phase 0 outputs (business profile, brand status, problem statement, scope)

#### Key Activities
| # | Activity | Description | Tools Used | KG Search Topics |
|---|----------|-------------|-----------|------------------|
| 0.5.1 | Brand Inventory | Catalog ALL current brand elements: name, logo, colors, tagline, packaging, store design, menu design, signage, uniforms, social profiles | `browse_social_media`, `search_web` | `"brand inventory brand audit"`, `"brand elements"` |
| 0.5.2 | Brand Exploratory — Customer Perception | Research how customers actually perceive the brand: reviews, social mentions, sentiment | `search_web`, `browse_social_media`, `analyze_reviews` | `"brand exploratory consumer perception"`, `"brand knowledge structures"` |
| 0.5.3 | Brand Equity Source Identification | Identify WHERE current equity comes from: which associations are strong? Which assets are distinctive? | `search_knowledge_graph` | `"sources of brand equity"`, `"customer-based brand equity"` |
| 0.5.4 | Brand Equity Drain Identification | Identify WHAT is damaging equity: negative associations, outdated elements, confused positioning | `analyze_reviews`, `browse_social_media` | `"brand revitalization"`, `"brand reinforcement"` |
| 0.5.5 | Preserve-Discard Analysis | For each brand element, decide: Preserve (high equity, aligned) / Evolve (has equity, needs update) / Replace (low equity, misaligned) / Remove (negative equity) | — | `"brand element adaptability"`, `"brand migration strategy"` |

#### Preserve-Discard Matrix

For each current brand element, evaluate:

```
                    HIGH current equity          LOW current equity
                ┌──────────────────────────┬──────────────────────────┐
  ALIGNED       │     ✅ PRESERVE           │     🔄 BUILD UP          │
  with new      │  Keep as-is, reinforce    │  Keep direction, invest  │
  strategy      │  (anchor brand migration) │  to strengthen           │
                ├──────────────────────────┼──────────────────────────┤
  NOT ALIGNED   │     ⚡ EVOLVE             │     ❌ REPLACE/REMOVE    │
  with new      │  Careful transition,      │  Low cost to change,     │
  strategy      │  preserve recognition     │  high benefit             │
                └──────────────────────────┴──────────────────────────┘
```

> **KG Reference**: "Brand Element Adaptability: This criterion evaluates a brand element's effectiveness in being refreshed to remain relevant across diverse eras and cultural contexts." — Keller

#### Quality Gate — Phase 0.5 Exit Criteria
- [ ] Complete brand inventory documented (all current brand elements)
- [ ] Customer perception data gathered (reviews, social sentiment)
- [ ] Sources of current brand equity identified
- [ ] Brand equity drains identified
- [ ] Each brand element classified: Preserve / Evolve / Replace / Remove
- [ ] User confirms the audit findings and preserve-discard decisions

#### Required Outputs
```yaml
phase_0_5_output:  # Only produced when scope ≠ "new_brand"
  brand_inventory:
    brand_elements:
      - element: str  # e.g., "Logo", "Brand Name", "Color Palette"
        current_state: str  # description of current state
        age: str  # how long it's been used
        recognition_level: str  # unknown, low, medium, high
        consumer_attachment: str  # none, low, moderate, strong
    marketing_programs:
      - program: str  # e.g., "Instagram content", "loyalty program"
        status: str  # active, inactive, abandoned
        effectiveness: str  # low, medium, high, unknown
  
  brand_perception:
    intended_associations: list[str]  # what the brand TRIES to stand for
    actual_associations: list[str]  # what customers ACTUALLY think/feel
    perception_gap: str  # summary of gap between intended and actual
    sentiment_summary: str  # overall positive, mixed, negative
    key_positive: list[str]  # what customers love
    key_negative: list[str]  # what customers dislike/complain about
  
  equity_assessment:
    equity_sources: list[str]  # what generates positive equity
    equity_drains: list[str]  # what damages equity
    brand_health_score: str  # healthy, stable, declining, critical
  
  preserve_discard_matrix:
    - element: str
      current_equity: str  # high, medium, low
      strategic_alignment: str  # aligned, partially aligned, misaligned
      decision: str  # preserve, evolve, replace, remove
      rationale: str  # why this decision
      transition_risk: str  # low, medium, high (risk of changing this element)
  
  migration_strategy_direction:
    approach: str  # "big bang" (switch overnight) / "phased" (gradual transition) / "inside-out" (internal first)
    transition_narrative: str  # how to explain the change to customers
    critical_assets_to_preserve: list[str]  # non-negotiable elements to keep
    high_priority_changes: list[str]  # most impactful changes to make
```

---

### 3.3 Phase 1: Market Intelligence & Research

**Purpose**: Build comprehensive understanding of the market landscape, competitive environment, and target audience. This is the research foundation for all strategic decisions.

**Mentor Mode**: Explain why research before strategy. Show what we'll investigate and why each matters.

**5W1H Focus**: **WHO** (customers) + **WHERE** (market) + **WHY** (customer motivations)

#### Required Inputs
- Phase 0 outputs (business profile, problem statement)

#### Key Activities
| # | Activity | Description | Tools Used | KG Search Topics |
|---|----------|-------------|-----------|-----------------|
| 1.1 | Industry & Category Analysis | F&B industry trends, category dynamics, market size | `search_web`, `crawl_web` | `"industry analysis competitive strategy"`, `"market segmentation"` |
| 1.2 | Local Market Mapping | Nearby competitors, foot traffic areas, area demographics | `search_places`, `search_web` | `"competitor analysis"`, `"market positioning"` |
| 1.3 | Competitor Deep-Dive | Identify 3-5 direct + 2-3 indirect competitors; analyze their brand, positioning, pricing, reviews, social presence | `search_web`, `crawl_web`, `browse_social_media`, `search_places` | `"competitive advantage"`, `"competitive differentiation"` |
| 1.4 | Target Audience Definition (STP) | Segmentation → Targeting → define primary & secondary audience | `search_web`, `browse_social_media` | `"market segmentation targeting"`, `"consumer behavior"`, `"benefit segmentation"` |
| 1.5 | Customer Insight Mining | WHY do they buy? What are their unmet needs, pain points, desires? | `browse_social_media`, `search_web` | `"consumer buying behavior decision process"`, `"customer insight"` |
| 1.6 | Trend & Opportunity Scanning | Current F&B trends, emerging opportunities, cultural shifts | `search_web`, `deep_research` | `"market trends opportunity"`, `"cultural influence consumer behavior"` |

#### Quality Gate — Phase 1 Exit Criteria
- [ ] At least 3 direct competitors profiled with brand, pricing, positioning, reviews
- [ ] Primary target audience defined with demographics, psychographics, and behaviors
- [ ] At least 3 customer insights articulated (WHY-driven, not WHAT-driven)
- [ ] Market opportunity or gap identified
- [ ] SWOT analysis completed for the business/brand
- [ ] Competitive perceptual map created (positioning axes identified)
- [ ] Strategic sweet spot identified (where opportunity meets capability)
- [ ] [Rebrand only] Current brand’s actual market position documented vs competitors
- [ ] User confirms the research findings and strategic synthesis are accurate

#### Required Outputs
```yaml
phase_1_output:
  market_overview:
    industry_trends: list[str]  # 3-5 key trends
    category_dynamics: str
    market_size_estimate: str | null
    growth_direction: str  # growing, stable, declining, fragmenting
  
  competitive_landscape:
    direct_competitors:  # 3-5
      - name: str
        positioning: str
        price_range: str
        strengths: list[str]
        weaknesses: list[str]
        brand_perception: str
        social_presence: str
        key_differentiator: str
    indirect_competitors: list  # 2-3, same structure
    competitive_gaps: list[str]  # opportunities no one is addressing
  
  target_audience:
    primary_segment:
      demographics: str  # age, gender, income, location
      psychographics: str  # lifestyle, values, interests
      behaviors: str  # buying frequency, occasion, channel
      jobs_to_be_done: list[str]  # JTBD framework
      pain_points: list[str]
      desires: list[str]
    secondary_segment: same_structure | null
  
  customer_insights:  # WHY-driven
    - insight: str  # "Customers feel... because..."
      evidence: str  # source/data backing this
      implication: str  # what this means for our brand
  
  opportunities:
    market_gaps: list[str]
    unmet_needs: list[str]
    trend_opportunities: list[str]
  
  current_brand_position:  # null if scope = "new_brand"
    actual_perception: str  # how market perceives the brand now
    position_vs_competitors: str  # where it sits on the perceptual map
    perception_gaps: list[str]  # gaps vs intended positioning
  
  strategic_synthesis:
    swot:
      strengths: list[str]
      weaknesses: list[str]
      opportunities: list[str]
      threats: list[str]
    perceptual_map:
      axis_x: str  # e.g., "Price (low → high)"
      axis_y: str  # e.g., "Experience (functional → experiential)"
      competitor_positions: list[str]  # "Competitor A: high price, experiential"
      white_space: str  # where the open opportunity is
    strategic_sweet_spot:
      opportunity: str  # which market gap/unmet need
      capability_fit: str  # why the business can deliver on this
      insight_leveraged: str  # which customer insight drives this
    prioritized_insights:  # ranked by strategic impact
      - insight: str
        strategic_value: str  # high, medium, low
        actionability: str  # how directly this drives brand strategy
```

---

### 3.4 Phase 2: Brand Strategy Core

**Purpose**: Define the strategic heart of the brand — positioning, differentiation, value proposition, and brand architecture. This is where WHO and WHY from Phase 1 become WHAT the brand stands for.

**Mentor Mode**: Explain positioning theory (reference KG: Ries & Trout mental positioning, Keller's POPs/PODs, Sharp's distinctiveness). Guide through framework selection.

**5W1H Focus**: **WHAT** (brand stands for) + **WHY** (reason to believe)

#### Required Inputs
- Phase 0 outputs (business profile, problem statement)
- Phase 1 outputs (competitive landscape, target audience, insights)

#### Key Activities
| # | Activity | Description | KG Search Topics |
|---|----------|-------------|-----------------|
| 2.1 | Competitive Frame of Reference | Define the category and competitive set the brand operates within | `"competitive frame of reference"`, `"category positioning"` |
| 2.2 | Points of Parity (POPs) | Identify must-have category associations (table stakes) | `"points of parity brand positioning"` |
| 2.3 | Points of Difference (PODs) | Identify unique, desirable, deliverable differentiators | `"points of differentiation competitive advantage"`, `"unique selling proposition"` |
| 2.4 | Brand Positioning Statement | Craft formal positioning: For [target], [brand] is the [frame] that [POD] because [RTB] | `"brand positioning statement"`, `"value proposition"` |
| 2.5 | Value Mapping | Map: Attribute → Functional Benefit → Emotional Benefit → Customer Outcome | `"benefit ladder brand"`, `"brand value chain"` |
| 2.6 | Brand Essence & Promise | Distill the core brand idea into a single compelling thought | `"brand essence"`, `"brand promise"` |
| 2.7 | Insight-to-Strategy Bridge | Connect customer insights (Phase 1) to strategic decisions | `"customer insight brand strategy"` |

#### Quality Gate — Phase 2 Exit Criteria
- [ ] Clear competitive frame of reference established
- [ ] At least 2-3 meaningful PODs that are desirable, deliverable, and differentiated
- [ ] Positioning statement follows the standard template and is compelling
- [ ] Product-brand alignment verified: product/menu can truthfully deliver on the brand promise
- [ ] Value mapping shows clear Attribute → Benefit → Outcome chain
- [ ] Positioning Stress Test passed (all 5 criteria met; if any fail, iterate)
- [ ] Brand essence can be expressed in 1-2 sentences
- [ ] Strategy clearly addresses the business problem from Phase 0
- [ ] [Rebrand] Positioning change justified vs preserve-discard decisions from Phase 0.5
- [ ] User approves the strategic direction

> **⚠️ Proactive Loop Trigger**: If Positioning Stress Test FAILS on Deliverability or Relevance, the agent MUST recommend revisiting Phase 1 research or Phase 0 problem statement before proceeding.

#### Required Outputs
```yaml
phase_2_output:
  competitive_frame:
    category: str  # "specialty coffee shop in District 1"
    competitive_set: list[str]  # brands we compete against
    category_associations: list[str]  # what customers expect from this category
  
  positioning:
    points_of_parity: list[str]  # must-haves
    points_of_difference: list[str]  # unique differentiators
    positioning_statement: str  # formal statement
    positioning_rationale: str  # why this positioning works
  
  value_architecture:
    attributes: list[str]  # product/service features
    functional_benefits: list[str]  # what they do for customers
    emotional_benefits: list[str]  # how they make customers feel
    customer_outcomes: list[str]  # ultimate value delivered
    reasons_to_believe: list[str]  # proof points (RTB)
  
  brand_essence:
    core_idea: str  # one sentence
    brand_promise: str  # what we promise customers
    brand_mantra: str | null  # 3-5 word brand mantra (Keller)
  
  strategic_alignment:
    problem_addressed: str  # links back to Phase 0 problem
    insight_leveraged: str  # links back to Phase 1 insights
    differentiation_logic: str  # why this strategy wins
  
  product_brand_alignment:
    product_truth: str  # what the product actually delivers
    brand_promise_fit: str  # how product truth supports brand promise
    menu_strategy_direction: str | null  # how menu should reflect positioning (F&B)
    pricing_positioning_fit: str  # how pricing reflects brand positioning
    gap_actions: list[str]  # what product/service changes needed to support brand
  
  positioning_stress_test:
    competitive_vacancy: str  # pass/fail + explanation
    deliverability: str  # pass/fail + explanation
    relevance: str  # pass/fail + explanation
    defensibility: str  # pass/fail + explanation
    budget_feasibility: str  # pass/fail + explanation
    overall_verdict: str  # pass / conditional pass (with required changes) / fail (rework needed)
```

---

### 3.5 Phase 3: Brand Identity & Expression

**Purpose**: Translate the strategic core into tangible brand elements — personality, visual identity direction, and distinctive brand assets. This is HOW the brand manifests in the world.

**Mentor Mode**: Explain Keller's brand element selection criteria (memorable, meaningful, likable, transferable, adaptable, protectable). Reference Sharp's Distinctive Brand Assets.

**5W1H Focus**: **HOW** (the brand looks, sounds, feels)

#### Required Inputs
- Phase 2 outputs (positioning, brand essence, value architecture)

#### Key Activities
| # | Activity | Description | Tools Used | KG Search Topics |
|---|----------|-------------|-----------|-----------------|
| 3.1 | Brand Personality Definition | Define 3-5 human personality traits using the Brand Personality framework (Sincerity, Excitement, Competence, Sophistication, Ruggedness) | — | `"brand personality framework"`, `"brand imagery"` |
| 3.2 | Brand Voice & Tone | Define how the brand communicates: formal/casual, playful/serious, etc. | — | `"brand voice communication style"` |
| 3.3 | Brand Name Evaluation | Evaluate/create brand name against Keller's criteria | `search_web` (check availability) | `"brand name selection criteria"`, `"brand elements"` |
| 3.4 | Visual Identity Direction | Define color psychology, typography direction, imagery style, logo direction | `generate_image` (mood boards, concepts) | `"distinctive brand assets"`, `"brand identity visual"` |
| 3.5 | Distinctive Brand Assets (DBA) Audit | Plan which assets to develop for mental availability (based on Sharp) | — | `"distinctive brand assets mental availability"` |
| 3.6 | Brand Sensory Identity | For F&B: taste profile, aroma, ambient sound/music, tactile (packaging) | `search_web` (reference) | `"sensory marketing brand experience"` |

#### Quality Gate — Phase 3 Exit Criteria
- [ ] Brand personality defined with 3-5 traits and behavioral descriptors
- [ ] Brand voice guidelines with do/don't examples
- [ ] Brand name finalized (new brand: full naming process completed with availability checks; rebrand: keep/rename decision justified)
- [ ] Visual identity direction documented (colors, typography, imagery style)
- [ ] At least 2-3 mood board/concept images generated
- [ ] Distinctive Brand Assets strategy planned (which assets to prioritize)
- [ ] F&B-specific sensory elements considered
- [ ] [Rebrand only] Identity transition plan completed — which elements evolve, which are new
- [ ] User approves the brand expression direction

#### Required Outputs
```yaml
phase_3_output:
  brand_personality:
    archetype: str | null  # e.g., "The Explorer", "The Caregiver"
    traits: list[str]  # 3-5 personality traits
    trait_descriptors:  # for each trait
      - trait: str
        means: str  # what this looks like in practice
        does_not_mean: str  # what to avoid
    brand_character: str  # 2-3 sentence character description
  
  brand_voice:
    tone_spectrum:  # where on the spectrum
      formal_casual: str  # e.g., "casual-leaning"
      playful_serious: str
      bold_understated: str
      technical_accessible: str
    voice_principles: list[str]  # 3-5 communication principles
    voice_examples:
      - context: str
        do: str
        dont: str
  
  visual_identity:
    color_palette:
      primary: list[str]  # hex + meaning
      secondary: list[str]
      accent: list[str]
      color_rationale: str
    typography_direction:
      heading_style: str  # serif, sans-serif, display, handwritten
      body_style: str
      typography_rationale: str
    imagery_style: str  # photography style, illustration style
    logo_direction: str  # description of desired logo concept
    mood_board_images: list[str]  # paths to generated images
  
  distinctive_brand_assets:
    priority_assets: list[str]  # which assets to develop first
    asset_strategy: str  # how to build distinctiveness over time
  
  sensory_identity:  # F&B specific
    taste_profile: str | null
    aroma_identity: str | null
    ambient_experience: str | null
    packaging_direction: str | null
  
  brand_naming:  # detailed for new brands
    naming_strategy: str  # descriptive, suggestive, abstract, founder, etc.
    shortlisted_names:
      - name: str
        availability: str  # domain, social handles, trademark status
        positioning_fit: str  # how well it reinforces positioning
        keller_scores:  # 1-5 per criterion
          memorable: int
          meaningful: int
          likable: int
          transferable: int
          adaptable: int
          protectable: int
    selected_name: str
    selection_rationale: str
  
  identity_transition:  # null if scope = "new_brand"
    elements_preserved: list[str]  # kept as-is from current brand
    elements_evolved: list[str]  # modified/updated
    elements_replaced: list[str]  # newly created
    elements_removed: list[str]  # retired
    visual_bridge_strategy: str  # how old and new visually connect during transition
    dba_continuity_plan: str  # which distinctive assets carry forward
```

---

### 3.6 Phase 4: Brand Communication Framework

**Purpose**: Define WHAT the brand says and HOW it says it — from the core value proposition message to channel-specific communication guidelines. Apply Cialdini's persuasion principles for message effectiveness.

**Mentor Mode**: Explain the communication hierarchy (one-liner → elevator pitch → full story). Reference AIDA model and persuasion principles from KG.

**5W1H Focus**: **HOW** (message delivery) + **WHERE** (channels) + **WHO** (audience per channel)

#### Required Inputs
- Phase 2 outputs (positioning, value architecture)
- Phase 3 outputs (brand personality, voice, visual direction)

#### Key Activities
| # | Activity | Description | Tools Used | KG Search Topics |
|---|----------|-------------|-----------|-----------------|
| 4.1 | Core Value Proposition | One sentence: what you do + for whom + why it matters | — | `"value proposition development"`, `"brand messaging"` |
| 4.2 | Messaging Hierarchy | Key messages ranked: primary message, supporting messages, proof points | — | `"messaging hierarchy"`, `"brand communication"` |
| 4.3 | Message by Audience Segment | Tailor messaging for primary vs secondary audience | — | `"audience segmentation messaging"` |
| 4.4 | Persuasion Layer | Apply Cialdini's principles: which principle(s) best fit each message | — | `"persuasion principles"`, `"social proof authority reciprocity"` |
| 4.5 | AIDA Communication Flow | Map messages to Attention → Interest → Desire → Action stages | — | `"AIDA model"`, `"communication objectives"` |
| 4.6 | Channel Strategy | Which channels, what content type, what frequency | `search_web`, `browse_social_media` | `"integrated marketing communication"`, `"content marketing strategy"` |
| 4.7 | Content Pillar Definition | 3-5 content themes that support the brand positioning | — | `"content strategy pillars"` |
| 4.8 | Storytelling Framework | The brand origin story, customer stories, day-in-the-life narratives | — | `"brand storytelling"`, `"narrative marketing"` |

#### Quality Gate — Phase 4 Exit Criteria
- [ ] Core value proposition is clear, compelling, and differentiated (one sentence)
- [ ] Messaging hierarchy covers primary, secondary, and supporting messages
- [ ] At least 2 Cialdini principles applied to messaging
- [ ] AIDA flow mapped with specific messages per stage
- [ ] Channel strategy defined with content types and frequencies
- [ ] 3-5 content pillars established
- [ ] User approves the communication framework

#### Required Outputs
```yaml
phase_4_output:
  value_proposition:
    one_liner: str  # one sentence
    elevator_pitch: str  # 30-second version
    full_story: str  # 2-3 paragraph version
  
  messaging_hierarchy:
    primary_message: str
    supporting_messages: list[str]  # 3-5
    proof_points: list[str]  # evidence/RTBs
    tagline_options: list[str]  # 2-3 tagline candidates
  
  audience_messaging:
    - segment: str
      key_message: str
      tone_adjustment: str
      primary_channel: str
  
  persuasion_strategy:
    - principle: str  # e.g., "Social Proof"
      application: str  # how it's applied
      message_example: str
  
  aida_framework:
    attention: str  # how we grab attention
    interest: str  # how we build interest
    desire: str  # how we create desire
    action: str  # how we drive action
  
  channel_strategy:
    channels:
      - channel: str  # e.g., "Instagram"
        purpose: str  # e.g., "Brand awareness + community"
        content_types: list[str]
        posting_frequency: str
        audience_match: str
    content_pillars:
      - pillar: str
        description: str
        example_topics: list[str]
  
  brand_story:
    origin_story: str
    customer_story_template: str
    narrative_themes: list[str]
```

---

### 3.7 Phase 5: Brand Strategy Plan & Deliverables

**Purpose**: Compile everything into a professional, actionable brand strategy document. Define KPIs, timeline, and measurement plan. This is the final deliverable — ready for implementation.

**Mentor Mode**: Explain what a professional brand strategy document looks like, how to use it, and what comes next (implementation).

**5W1H Focus**: **HOW MUCH** (KPIs, budget) + **WHEN** (timeline)

#### Required Inputs
- All Phase 0-4 outputs

#### Key Activities
| # | Activity | Description | Tools Used | KG Search Topics |
|---|----------|-------------|-----------|-----------------|
| 5.1 | Strategy Document Compilation | Assemble all phases into a coherent brand strategy document | `generate_document` | `"brand guidelines document"` |
| 5.2 | Brand Key / Brand Pyramid Summary | Create the one-page Brand Key visual summary | `generate_image` | `"brand key framework"`, `"brand pyramid"` |
| 5.3 | KPI Definition | Define measurable brand metrics: awareness, perception, engagement, revenue impact | — | `"brand equity measurement"`, `"brand tracking"` |
| 5.4 | Implementation Roadmap | Phase the implementation: Quick wins (0-3 months), Medium-term (3-6), Long-term (6-12) | — | `"marketing implementation plan"` |
| 5.5 | Measurement Plan | How to track KPIs, what tools to use, review cadence | — | `"brand equity measurement system"`, `"brand audit"` |
| 5.6 | Presentation Deck | Create a summary pitch deck for stakeholder presentation | `generate_presentation` | — |

#### Quality Gate — Phase 5 Exit Criteria
- [ ] Complete brand strategy document generated (PDF or DOCX)
- [ ] Brand Key one-pager included
- [ ] At least 5 KPIs defined with baselines and targets
- [ ] Implementation roadmap with 3 time horizons, tied to budget_tier
- [ ] Each roadmap item categorized as "Must Do" or "Nice to Have"
- [ ] Measurement plan with review cadence
- [ ] [Rebrand only] Transition & change management plan completed
- [ ] [Rebrand only] Stakeholder communication plan defined
- [ ] [Rebrand only] Physical & digital asset changeover checklist with cost estimates
- [ ] User approves the final deliverable

#### Required Outputs
```yaml
phase_5_output:
  brand_strategy_document:
    format: str  # PDF or DOCX
    sections:
      - executive_summary
      - business_context_and_problem
      - market_intelligence
      - brand_strategy_core
      - brand_identity_and_expression
      - communication_framework
      - implementation_roadmap
      - measurement_plan
      - appendices
  
  brand_key_summary:
    visual: str  # path to generated Brand Key image
    components:
      - root_strength: str
      - competitive_environment: str
      - target: str
      - insight: str
      - benefits: str  # functional + emotional
      - values_and_personality: str
      - reasons_to_believe: str
      - discriminator: str
      - brand_essence: str
  
  kpis:
    - metric: str
      baseline: str | null
      target: str
      measurement_method: str
      review_frequency: str
  
  implementation_roadmap:
    budget_tier: str  # from Phase 0
    quick_wins:  # 0-3 months
      - action: str
        owner: str
        priority: str  # must_do / nice_to_have
        estimated_cost: str | null
    medium_term:  # 3-6 months
      - action: str
        owner: str
        priority: str
        estimated_cost: str | null
    long_term:  # 6-12 months
      - action: str
        owner: str
        priority: str
        estimated_cost: str | null
    total_estimated_investment: str  # rough total
    budget_fit_assessment: str  # how well plan fits budget_tier
  
  measurement_plan:
    tracking_tools: list[str]
    review_cadence: str  # monthly, quarterly
    reporting_format: str
  
  transition_plan:  # null if scope = "new_brand"
    approach: str  # big_bang / phased / inside_out
    stakeholder_map:
      - stakeholder: str  # e.g., "employees", "loyal customers"
        impact_level: str  # high, medium, low
        communication_method: str  # how to inform them
        timing: str  # when to inform
    internal_rollout:
      - action: str  # e.g., "Brand values workshop"
        timing: str
        responsible: str
    customer_communication:
      announcement_message: str  # the key message
      channels: list[str]  # email, social, in-store
      tone: str  # how to frame the change
      faq_items: list[str]  # anticipated questions
    physical_changeover:
      - asset: str  # e.g., "Store signage"
        current_state: str
        new_state: str
        estimated_cost: str
        timeline: str
    digital_migration:
      - platform: str  # e.g., "Instagram", "Google Business"
        changes_needed: list[str]
        timeline: str
    transition_timeline:
      pre_launch: list[str]  # preparation steps
      d_day: str  # the rebranding reveal moment
      post_launch: list[str]  # follow-up actions
    risk_mitigation:
      - risk: str
        mitigation: str
```

---

## 4. Skills Architecture

### 4.1 Overview

Four skills are needed, organized by scope:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SKILL ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────┐               │
│  │ SKILL 1: brand-strategy-orchestrator          │ ← MASTER     │
│  │ (Phases 0-5 workflow, quality gates,          │   SKILL      │
│  │  mentor scripts, phase transitions,           │              │
│  │  rebrand decision matrix, proactive loops,    │              │
│  │  workflow branching by scope)                  │              │
│  └───────────┬──────────────────────────────────┘               │
│              │ loads sub-skills per phase                        │
│              ▼                                                   │
│  ┌────────────────────┐  ┌───────────────────┐                  │
│  │ SKILL 2:           │  │ SKILL 3:          │                  │
│  │ market-research     │  │ brand-positioning  │                 │
│  │ (Phase 1 deep-dive, │  │ & identity         │                │
│  │  + brand perception │  │ (Phases 2-3,       │                │
│  │  research for       │  │  + naming process,  │               │
│  │  rebrands)          │  │  + preserve-discard │               │
│  └────────────────────┘  │  for rebrands)      │                │
│                          └───────────────────┘                  │
│                                                                 │
│  ┌────────────────────────────────────────────┐                 │
│  │ SKILL 4: brand-communication & planning     │                │
│  │ (Phases 4-5 messaging, docs, deliverables,  │                │
│  │  + transition & change mgmt for rebrands)   │                │
│  └────────────────────────────────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Skill 1: `brand-strategy-orchestrator` (Master Skill)

**Purpose**: The master workflow skill that controls the entire brand strategy engagement. It defines WHAT phases to execute, WHEN to transition, and HOW to mentor.

**When loaded**: Always loaded when user starts a brand strategy project.

```markdown
# Skill: Brand Strategy Orchestrator
# Version: 2.0
# Scope: Master workflow for F&B brand strategy development
# Handles: New brand, refresh, repositioning, full rebrand

## Overview
You are conducting a professional brand strategy engagement for an F&B business.
Follow the phased process below. For each phase:
1. MENTOR: Explain what we'll do and why
2. EXECUTE: Gather data, analyze, produce outputs
3. REVIEW: Present to user, collect feedback, iterate

## Phase Sequence (with conditional branching)

### Default (New Brand):
Phase 0 → GATE → Phase 1 → GATE → Phase 2 → GATE → Phase 3 → GATE → Phase 4 → GATE → Phase 5 → COMPLETE

### Existing Brand (scope determined in Phase 0):
Phase 0 → Rebrand Decision Matrix → Scope Classification → GATE →
Phase 0.5: Brand Equity Audit → GATE →
Phase 1 (+ existing brand research) → GATE →
Phase 2 (informed by audit) → GATE →
Phase 3 (+ identity transition plan) → GATE →
Phase 4 → GATE →
Phase 5 (+ transition & change management) → COMPLETE

### Scope-Specific Variations:
- REFRESH: Phase 0.5 (light) → Phase 1 (targeted) → SKIP Phase 2 → Phase 3 (focus) → Phase 4 (adapt) → Phase 5
- REPOSITION: Phase 0.5 (full) → Phase 1 (full) → Phase 2 (pivot) → Phase 3 (evolve) → Phase 4 (full) → Phase 5
- FULL REBRAND: Phase 0.5 (full) → Phase 1 (full) → Phase 2 (new) → Phase 3 (new) → Phase 4 (full) → Phase 5 (+ transition)

## Phase Transition Rules
- NEVER skip Phase 0 (always needed for business context)
- Phase 0.5 is CONDITIONAL: only for existing brands (skip for new brands)
- ALWAYS complete the quality gate before moving on
- ALWAYS get user confirmation before transitioning
- If user wants to go back, allow revisiting any previous phase
- Accumulated outputs from previous phases are inputs to current phase

## Mentor Script Templates
[For each phase: opening explanation, key questions to ask, 
 concepts to explain, how to present findings]

## Quality Gate Checklists
[For each phase: exit criteria checklist]

## Context Accumulation
- Maintain a running "Brand Brief" document that grows with each phase
- Each phase adds its section to the brief
- The final brief becomes the Phase 5 input

## KG Integration Points
[For each phase: recommended KG search queries to enrich reasoning]

## Error Handling
- If research yields insufficient data: explain to user, ask for additional context
- If user disagrees with strategic direction: explore alternatives, present trade-offs
- If external tools fail: gracefully degrade, use KG knowledge as fallback

## Proactive Loop Triggers (Agent-Initiated Reworks)
The agent MUST recommend revisiting a previous phase when these conditions are detected:

| Trigger | Detected At | Action |
|---------|------------|--------|
| Positioning Stress Test fails on Deliverability | Phase 2 | → Revisit Phase 0 (product reality) or Phase 1 (re-evaluate opportunities) |
| Positioning Stress Test fails on Relevance | Phase 2 | → Revisit Phase 1 (deeper insight mining) |
| All promising brand names taken (domain + trademark) | Phase 3 | → Adjust positioning angle or naming strategy |
| Visual identity conflicts with positioning | Phase 3 | → Revisit Phase 2 brand essence for clarity |
| Messaging reveals positioning is too abstract to communicate | Phase 4 | → Revisit Phase 2 for sharper positioning |
| Budget cannot support implementation plan | Phase 5 | → Revisit Phase 0 budget or simplify strategy scope |
| [Rebrand] Audit reveals no salvageable equity | Phase 0.5 | → Recommend upgrading scope to "full_rebrand" or "retirement" |
| [Rebrand] Customer backlash risk too high for proposed changes | Phase 3/5 | → Scale back changes, consider phased approach |

When triggering a loop:
1. EXPLAIN to user: what failed, why, and what revisiting will address
2. PROPOSE specific changes to the earlier phase
3. GET user confirmation before revisiting
4. PRESERVE all work done — don't start from scratch
5. After rework, re-validate the trigger condition

## Rebrand Decision Support
When user reports they have an existing brand, the agent PROACTIVELY:
1. Asks diagnostic questions to score the Rebrand Decision Matrix (6 signals × 0-2)
2. Presents the score with explanation for each signal
3. RECOMMENDS a scope (reinforce / refresh / reposition / full_rebrand / retire)
4. Explains trade-offs: cost, risk, time, potential upside
5. Gets user agreement on scope BEFORE proceeding

The agent does NOT wait for user to say "I want to rebrand" — it DIAGNOSES the need.
```

### 4.3 Skill 2: `market-research` (Phase 1 Deep-Dive)

**Purpose**: Detailed procedures for conducting F&B market research. Loaded during Phase 1.

```markdown
# Skill: Market Research for F&B
# Version: 1.0
# Scope: Phase 1 — Market Intelligence & Research

## Research Methodology

### Step 1: Industry Scan
- Search for: "[city] F&B market trends [year]"
- Search for: "[F&B category] industry growth Vietnam"
- Look for: market size, growth rate, key trends, regulatory changes

### Step 2: Local Competitor Mapping
- Use search_places to find competitors within 2-5km radius
- For each competitor:
  - Get: name, address, rating, review count, price level, hours
  - Browse social media for: follower count, engagement, content style
  - Crawl website/menu for: pricing, positioning, offerings

### Step 3: Competitor Brand Analysis
- For top 5 competitors, analyze:
  - Visual identity (logo, colors, imagery style)
  - Messaging (tagline, value proposition, tone)
  - Pricing strategy (premium, mid, budget)
  - Review sentiment (what customers love/hate)
  - Social media strategy (platforms, content types, engagement)

### Step 4: Target Audience Research
- Search for: "[F&B category] customer demographics Vietnam"
- Browse social media groups/communities related to the category
- Analyze competitor reviews for customer language and preferences
- Apply segmentation frameworks:
  - Demographic: age, income, location, occupation
  - Psychographic: lifestyle, values, interests (KG: "psychographic segmentation")
  - Behavioral: frequency, occasion, channel preference
  - Benefit: what they're really seeking (KG: "benefit segmentation")

### Step 5: Customer Insight Mining
- Look for patterns in:
  - Negative reviews of competitors (unmet needs)
  - Social media conversations about the category
  - Trending F&B topics and cultural moments
- Transform observations into insights using the formula:
  "We noticed [observation] because [underlying motivation], 
   which means [implication for our brand]"

### Step 6: Trend & Opportunity Scanning
- Search for: "F&B trends [year]", "[category] innovation"
- Check: sustainability trends, technology adoption, health/wellness
- Identify white space opportunities

### Step 7: [Rebrand only] Current Brand Position Research
- Skip this step if scope = "new_brand"
- Analyze how the EXISTING brand is perceived in the market:
  - Review sentiment analysis (Google Maps, social media)
  - Social media engagement rates and growth trends
  - Brand mention monitoring (search for brand name online)
  - Compare actual positioning vs intended positioning (from Phase 0.5 audit)
  - Map current brand position on the competitive perceptual map

### Step 8: Strategic Synthesis (CRITICAL — bridges Research → Strategy)
- SWOT Analysis: Consolidate ALL research into Strengths, Weaknesses, Opportunities, Threats
- Competitive Perceptual Map: Plot competitors on 2 axes relevant to the category
  - Choose axes that reveal meaningful differences (e.g., Price vs Experience Quality)
  - Identify WHITE SPACE — positions no competitor owns
- Strategic Sweet Spot: Where does OPPORTUNITY (from market) meet CAPABILITY (from business)?
- Insight Prioritization: Rank all customer insights by:
  1. Strategic value (how much this could differentiate us)
  2. Actionability (how directly this drives brand strategy decisions)
  3. Evidence strength (how well-supported by data)

## Output Template
[Structured output matching phase_1_output schema]

## KG Queries for This Phase
- "market segmentation criteria methods"
- "consumer behavior purchase decision"
- "competitive analysis framework"
- "benefit segmentation"
- "customer insight development"
```

### 4.4 Skill 3: `brand-positioning-identity` (Phases 2-3)

**Purpose**: Frameworks and procedures for brand positioning and identity development. Loaded during Phases 2-3.

```markdown
# Skill: Brand Positioning & Identity
# Version: 1.0
# Scope: Phase 2 (Brand Strategy Core) + Phase 3 (Brand Identity & Expression)

## Phase 2: Brand Strategy Core

### Positioning Framework (Keller's model + Ries & Trout)

#### Step 1: Competitive Frame of Reference
- Define: "We compete in the [category] market"
- Identify: Which brands/types are our competitive set?
- KG: "competitive frame of reference points of parity points of difference"

#### Step 2: Points of Parity (POPs)
- Category POPs: What must we have to be considered in this category?
  - For F&B café: good coffee, clean space, reasonable pricing, wifi
- Competitive POPs: What do we need to match from competitors?
  - Negate competitor advantages without copying

#### Step 3: Points of Difference (PODs)
- Test each potential POD against 3 criteria:
  1. DESIRABLE to consumers? (relevant, distinctive, believable)
  2. DELIVERABLE by the brand? (feasible, communicable, sustainable)
  3. DIFFERENTIATING from competitors? (unique, hard to copy)
- KG: "points of differentiation desirable deliverable"

#### Step 4: Positioning Statement
Template: "For [target audience] who [need/want], 
[brand name] is the [competitive frame] that [key POD] 
because [reasons to believe]."

#### Step 5: Value Ladder
Build the ladder:
  Product Attributes (tangible features)
       ↓
  Functional Benefits (what it does for you)
       ↓
  Emotional Benefits (how it makes you feel)
       ↓
  Customer Outcomes (ultimate life value)

#### Step 6: Brand Essence
- Distill everything into 1-2 sentences
- Create brand mantra (3-5 words): [emotional modifier] + [descriptive modifier] + [brand function]
  Example: "Authentic Daily Inspiration" for a specialty café
- KG: "brand essence brand mantra"

#### Step 7: Product-Brand Alignment (F&B Critical)
- "Product Truth": What does the product ACTUALLY deliver? Can we prove it?
- Menu-Positioning Fit: Does the menu composition reinforce the positioning?
  - Premium positioning → menu should reflect craft, quality ingredients, curated selection
  - Community positioning → menu should include shareable items, customization options
- Pricing-Positioning Fit: Does the price level match the positioning?
  - Premium POD + budget pricing = credibility gap
  - Accessibility POD + premium pricing = disconnect
- Service-Brand Fit: Does the service style embody the brand personality?
- Gap Actions: List specific product/service changes needed to support the brand promise

#### Step 8: Positioning Stress Test
Run the 5-criteria validation before finalizing:
1. Competitive Vacancy — check if any competitor already owns this position
2. Deliverability — verify product truth supports the claim
3. Relevance — confirm target audience cares (from Phase 1 insights)
4. Defensibility — assess if this can be sustained when competitors react
5. Budget Feasibility — can this be communicated within the budget_tier?
- ⚠️ If ANY test fails → trigger proactive loop back to Phase 1 or Phase 0

## Phase 3: Brand Identity & Expression

### Brand Personality (Aaker's Framework)
Choose 1-2 primary dimensions and define specific traits:
1. Sincerity (honest, wholesome, cheerful, down-to-earth)
2. Excitement (daring, spirited, imaginative, up-to-date)
3. Competence (reliable, intelligent, successful)
4. Sophistication (upper-class, charming, glamorous)
5. Ruggedness (outdoorsy, tough, masculine)

### Brand Voice Guidelines
Define along spectrums:
- Formal ←→ Casual
- Playful ←→ Serious  
- Bold ←→ Understated
- Technical ←→ Accessible
Create DO and DON'T examples for each.

### Visual Identity Direction
- Color Psychology: Choose colors that align with brand personality
  - Warm (red, orange, yellow) = energy, passion, optimism
  - Cool (blue, green, purple) = trust, calm, creativity
  - Neutral (black, white, gray) = sophistication, simplicity
- Typography: Serif (traditional, trustworthy) vs Sans-serif (modern, clean)
- Imagery: Photography style, illustration style, iconography
- Generate: Mood boards, logo concepts, color palette samples

### Distinctive Brand Assets (Sharp)
Plan which assets to prioritize for building:
1. Color/color combinations
2. Logo/symbol
3. Tagline/slogan
4. Shape/form
5. Character/mascot (if applicable)
6. Sonic/audio (if applicable)
7. Packaging design (for F&B: cup design, bag design, etc.)
- KG: "distinctive brand assets mental availability"

### Brand Naming Process (Detailed — for new brands / full rebrands)
1. Choose naming approach: Descriptive, Suggestive, Abstract, Founder-based, Compound, Foreign-language
2. Generate 10-15 candidates aligned with positioning and essence
3. Linguistic screening: Vietnamese + English compatibility, pronunciation, negative connotations
4. Availability checks: domain, social handles, Vietnam trademark (NOIP)
5. Evaluate top 5 against Keller's 6 criteria (Memorable, Meaningful, Likable, Transferable, Adaptable, Protectable)
6. Present top 3 with rationale to user
- For refreshes/repositions where name = "preserve": skip naming, evaluate tagline changes instead

### [Rebrand only] Identity Transition Planning
1. Reference Phase 0.5 Preserve-Discard Matrix
2. For each EVOLVE element: design the transition (e.g., logo evolution series)
3. For each REPLACE element: create new element aligned with new strategy
4. Visual Bridge: design transitional visual that connects old → new (e.g., "unveiling" concept)
5. DBA Continuity: which distinctive assets carry forward? Plan handover period

## Output Templates
[Structured output matching phase_2_output and phase_3_output schemas]
```

### 4.5 Skill 4: `brand-communication-planning` (Phases 4-5)

**Purpose**: Messaging frameworks, communication strategy, and final deliverable assembly. Loaded during Phases 4-5.

```markdown
# Skill: Brand Communication & Planning
# Version: 1.0
# Scope: Phase 4 (Communication Framework) + Phase 5 (Plan & Deliverables)

## Phase 4: Brand Communication Framework

### Messaging Architecture

#### Layer 1: Core Value Proposition
Formula: "We help [target audience] [achieve outcome] through [unique method/offering]"

#### Layer 2: Key Messages (3-5)
Each supporting the core value proposition from a different angle:
- Functional message (what we do)
- Emotional message (how it feels)
- Differentiating message (why us, not them)
- Credibility message (proof/authority)
- Community message (belonging/identity)

#### Layer 3: Proof Points
For each key message, provide evidence:
- Data/statistics
- Customer testimonials
- Expert endorsements
- Process/methodology
- Heritage/origin story

### Persuasion Integration (Cialdini)
Apply 1-2 primary principles to the messaging strategy:

| Principle | F&B Application Example |
|-----------|------------------------|
| Social Proof | "Join 500+ coffee lovers who start their day with us" |
| Authority | "Our beans are selected by Q-grader certified roasters" |
| Scarcity | "Limited seasonal menu — available this month only" |
| Liking | Community-building, barista-as-brand-ambassador |
| Reciprocity | Free tasting events, generous sampling |
| Commitment | Loyalty program, "your daily ritual" framing |
| Unity | "Part of the neighborhood" identity |

### AIDA Communication Mapping
For each customer touchpoint, define:
- Attention: How do we stop the scroll / catch the eye?
- Interest: What makes them lean in / want to know more?
- Desire: What creates the "I want this" feeling?
- Action: What's the clear next step?

### Channel Strategy (F&B focused)
| Channel | Purpose | Content Type | Frequency |
|---------|---------|-------------|-----------|
| Instagram | Brand awareness, visual storytelling | Photos, Reels, Stories | Daily |
| Facebook | Community, events, promotions | Posts, Events, Groups | 3-5x/week |
| TikTok | Discovery, virality, behind-scenes | Short video | 3-5x/week |
| Google Maps/Reviews | Local discovery, trust | Review responses, photos | Ongoing |
| In-store | Experience, conversion | Signage, menu, packaging | Always |
| Website/App | Information, ordering | Menu, blog, ordering | Always |

### Content Pillars (F&B)
Suggested framework:
1. Product Showcase (40%) — menu items, preparation process, ingredients
2. Behind the Scenes (20%) — team, sourcing, craftsmanship
3. Community & Lifestyle (20%) — customer moments, local events, culture
4. Education & Story (10%) — origin stories, brewing methods, food pairing
5. Promotions & News (10%) — new items, events, special offers

## Phase 5: Brand Strategy Plan & Deliverables

### Document Assembly
Compile all phase outputs into a professional document:

#### Brand Strategy Document Structure
1. Cover Page (brand name, date, prepared by)
2. Executive Summary (1 page)
3. Business Context & Problem Statement (Phase 0)
4. Market Intelligence Summary (Phase 1)
5. Brand Strategy Core (Phase 2)
   - Positioning Statement
   - Value Architecture
   - Brand Essence
6. Brand Identity & Expression (Phase 3)
   - Brand Personality
   - Visual Identity Direction
   - Distinctive Brand Assets Plan
7. Communication Framework (Phase 4)
   - Messaging Hierarchy
   - Channel Strategy
   - Content Pillars
8. Implementation Roadmap
9. KPI & Measurement Plan
10. Appendices (research data, competitor profiles, mood boards)

### Brand Key One-Pager
Create a single-page visual summary:
```
┌─────────────────────────────┐
│         BRAND KEY            │
├─────────────────────────────┤
│ Root Strength:               │
│ Competitive Environment:     │
│ Target:                      │
│ Insight:                     │
│ Benefits: Functional / Emot. │
│ Values & Personality:        │
│ Reasons to Believe:          │
│ Discriminator:               │
│ ═══════════════════════════ │
│ BRAND ESSENCE:               │
└─────────────────────────────┘
```

### KPI Framework
| Category | Metric | Measurement | Frequency |
|----------|--------|-------------|-----------|
| Awareness | Brand recall/recognition | Survey or social mentions | Quarterly |
| Perception | Brand sentiment score | Review analysis, social listening | Monthly |
| Engagement | Social media engagement rate | Platform analytics | Weekly |
| Behavior | Customer acquisition rate | POS/CRM data | Monthly |
| Loyalty | Repeat customer rate | POS data | Monthly |
| Revenue | Revenue per customer | POS data | Monthly |
| Distinctiveness | DBA recognition rate | Survey | Quarterly |

### Implementation Roadmap
| Timeframe | Priority | Actions |
|-----------|----------|---------|
| Month 1-3 | Quick Wins | Brand name finalization, logo creation, social profile setup, menu redesign, staff training on brand voice |
| Month 3-6 | Build | Website launch, content calendar execution, local PR, review management, community engagement |
| Month 6-12 | Scale | Brand partnerships, loyalty program, event marketing, brand tracking first round, optimization |

**Budget-Tier Modifiers**: Adjust roadmap based on Phase 0 budget_tier:
- **Bootstrap (<50M VND)**: Focus on DIY actions — social setup, Canva-based visuals, reuse existing infrastructure. Delay paid activities.
- **Starter (50-200M)**: Professional logo + basic packaging + social content. Selective paid activities.
- **Growth (200M-1B)**: Full professional identity, website, content production, local PR, early paid marketing.
- **Enterprise (>1B)**: Everything in Growth + interior design, professional photography, influencer partnerships, brand events.

### [Rebrand only] Transition & Change Management Plan
This section is ONLY produced when scope ∈ {refresh, repositioning, full_rebrand}:

1. **Stakeholder Communication Plan**: Who to inform, when, how, what message
2. **Internal Rollout**: Employee training on new brand values, voice, behaviors
3. **Customer Communication**: Announcement framing, channels, FAQ
4. **Physical Asset Changeover Checklist**: Signage, menus, packaging, uniforms, interior — with cost estimates per item
5. **Digital Migration Checklist**: Social profiles, Google Business, website, online ordering platforms
6. **Transition Timeline**: Pre-launch → D-Day (rebrand reveal) → Post-launch
7. **Risk Register**: Customer confusion, negative reactions, competitor opportunism — with mitigation strategies

## Output Templates
[Structured output matching phase_4_output and phase_5_output schemas]
```

---

## 5. Tools Inventory

### 5.1 Existing Tools (7)

These tools are already built and available in the codebase:

| # | Tool | Function | Used In Phases |
|---|------|----------|---------------|
| 1 | `search_web` | Multi-provider web search (SearXNG → Perplexity → Tavily → Bing) | 0.5, 1, 4 |
| 2 | `crawl_web` | Deep web content extraction via Crawl4AI | 1, 4 |
| 3 | `browse_social_media` | Authenticated social media research via browser-use agent | 0.5, 1, 3, 4 |
| 4 | `search_knowledge_graph` | KG search for marketing concepts & relationships | 0-5 (all) |
| 5 | `search_document_library` | Hybrid search on marketing textbook passages | 0-5 (all) |
| 6 | `todo_write` | Task management for agent workflow | 0-5 (all) |
| 7 | `tool_search` | Browse tool warehouse to find specialized tools (inventory pattern) | 0-5 (all) |
| 7b | `load_tools` | Equip specific tools into the agent's active set | 0-5 (all) |
| 7c | `unload_tools` | Unequip tools when done to keep context lean | 0-5 (all) |

#### Tools 7/7b/7c: `tool_search` + `load_tools` + `unload_tools` — 3-Tool Inventory Pattern

> **Ref**: Task 47, `docs/langchain/tool_search_langchain.md`

**Problem**: The brand strategy agent has 18+ tools. Loading all tool definitions into the model context simultaneously causes context bloat (~5K-10K tokens) and reduces tool selection accuracy. Anthropic recommends `defer_loading` when agents have > 10 tools.

**Solution**: `ToolSearchMiddleware` — a LangChain `AgentMiddleware` with a game inventory pattern (browse → equip → use → unequip):

- **Core tools** (always visible): `search_knowledge_graph`, `search_document_library`, `search_web`, `crawl_web`, `deep_research` (5 tools)
- **Loadable tools** (via inventory workflow): 11 specialized tools in 5 categories
- **Meta tools** (always visible, from middleware): `tool_search`, `load_tools`, `unload_tools` (3 tools)
- **Other middleware tools** (always visible): `todo_write`, `task` (2 tools)
- **Initial visibility**: 10 tools (44% reduction from 18+)

**Category Catalog** (searchable via `tool_search`):

| Category | Tools | Description |
|----------|-------|-------------|
| `local_market` | `search_places` | Local business/competitor mapping |
| `social_media` | `browse_social_media`, `analyze_social_profile` | Social media research & analysis |
| `customer_analysis` | `analyze_reviews`, `get_search_autocomplete` | Customer perception & search behavior |
| `image_generation` | `generate_image`, `generate_brand_key` | Visual asset creation |
| `document_export` | `generate_document`, `generate_presentation`, `generate_spreadsheet`, `export_to_markdown` | Document/report generation |

**Agent flow** (inventory pattern — like a game warehouse):
```
Model call 1: Agent sees core tools + tool_search + load_tools + unload_tools
              System prompt includes: "## Tool Warehouse" catalog with inventory workflow

→ Agent needs to generate an image
→ Agent calls: tool_search("generate image")                    ← BROWSE (read-only)
→ Agent reviews results, THINKS about what it needs
→ Agent calls: load_tools(["generate_image"])                   ← EQUIP

Model call 2: Agent now sees core tools + generate_image
→ Agent calls: generate_image(prompt="...", template="mood_board")  ← USE
→ Agent finishes image work
→ Agent calls: unload_tools(["generate_image"])                 ← UNEQUIP (put back)

Model call 3: Agent is back to core tools only (context stays lean for next phase)
```

**Key design: Agent autonomy** — The agent decides what to load and when to unload. `tool_search` is read-only (browse, not auto-load). This gives the agent control over its own context, critical for long multi-phase conversations where Phase 1 tools (search_places) aren't needed in Phase 3-5.

**Implementation**: `src/shared/src/shared/agent_middlewares/tool_search/`

```python
@tool
def tool_search(query: str) -> str:
    """Search the tool warehouse for specialized capabilities.

    You start with core research tools only. Use this to BROWSE the catalog and
    see what specialized tools are available. This does NOT load tools — after
    reviewing results, use load_tools() to equip the ones you need.

    Workflow: tool_search → review results → load_tools → use → unload_tools
    """

@tool
def load_tools(tool_names: list[str], runtime: ToolRuntime) -> str:
    """Load (equip) specific tools into your active set.

    After using tool_search() to find tools, call this to make them available. Loaded
    tools will appear in your tool list on the next action.
    """

@tool
def unload_tools(tool_names: list[str], runtime: ToolRuntime) -> str:
    """Unload (unequip) tools from your active set.

    Call this when you're done with specific tools to keep your context clean. Like putting
    items back in the warehouse — you can always load them again later if needed.
    """
```

**Middleware pattern** (follows LangChain `AgentMiddleware` API):
- `wrap_model_call`: Filters `request.tools` to core + meta + loaded only; injects catalog on first call
- `wrap_tool_call`: Intercepts `load_tools` → adds valid names to `request.state["loaded_tools"]`; intercepts `unload_tools` → removes names from state; `tool_search` passes through (read-only, no state change)
- `tools = [tool_search, load_tools, unload_tools]`: 3 inventory tools always available
- `ToolRuntime`: Auto-injected by LangChain, invisible to LLM, gives load/unload access to current state for validation

**Integration with agent factory** (Task 46):
```python
from shared.agent_middlewares.tool_search import create_tool_search_middleware

tool_search_middleware = create_tool_search_middleware(all_tools=tools)

agent = create_agent(
    model=model,
    tools=tools,
    middleware=[
        tool_search_middleware,  # BEFORE skills_middleware
        skills_middleware,
        sub_agent_middleware,
        ...
    ],
)
```

### 5.2 New Tools Needed (10)

| # | Tool | Purpose | Phase(s) | Implementation | Cost | Priority |
|---|------|---------|----------|---------------|------|----------|
| 8 | `search_places` | Search local businesses via Google Places API (New) | 1 | REST API wrapper | **Free** (under $200/mo GCP credit) | 🔴 High |
| 9 | `deep_research` | Deep research via Perplexity Sonar API or multi-step search+crawl pipeline | 1, 4 | Perplexity API wrapper OR custom search→crawl→summarize chain | **Free** (Perplexity trial credits) | 🔴 High |
| 10 | `generate_image` | Generate brand assets, mood boards, logos via Gemini image generation | 3, 5 | `google-genai` SDK — Gemini 2.0 Flash (free) or 3.1 Flash Image (~$0.05/img) | **Free** (gemini-2.0-flash) or **~$0.05/image** | 🔴 High |
| 11 | `generate_document` | Generate PDF/DOCX brand strategy documents | 5 | `fpdf2` (PDF) + `python-docx` (DOCX) | **Free** (open-source) | 🔴 High |
| 12 | `generate_presentation` | Generate PPTX pitch deck for brand strategy | 5 | `python-pptx` | **Free** (open-source) | 🟡 Medium |
| 13 | `analyze_reviews` | Aggregate and analyze customer reviews from Google Maps, social media | 1 | Custom: `search_places` reviews + sentiment analysis via Gemini | **Free** (Gemini API) | 🟡 Medium |
| 14 | `get_search_autocomplete` | Get Google autocomplete suggestions for keyword/topic research | 1, 4 | REST API: `suggestqueries.google.com/complete/search` | **Free** (unofficial) | 🟡 Medium |
| 15 | `analyze_social_profile` | Analyze a social media profile's brand strategy (content, engagement, positioning) | 1 | Custom: `browse_social_media` + structured analysis prompt | **Free** | 🟡 Medium |
| 16 | `generate_brand_key` | Generate the Brand Key one-pager visual | 5 | `generate_image` with structured template prompt | **Free** | 🟢 Low |
| 17 | `export_to_markdown` | Export structured data to well-formatted markdown | 0-5 | Pure Python string formatting | **Free** | 🟢 Low |

### 5.3 Tool Details — New Tools

#### Tool 8: `search_places`

```python
async def search_places(
    query: str,
    location: str | None = None,
    radius_meters: int = 5000,
    max_results: int = 20,
) -> str:
    """
    Search for local businesses using Google Places API (New).
    
    Use this tool to find competitors, map the local market, and 
    understand the competitive landscape in a specific area.
    
    Args:
        query: Search query (e.g., "specialty coffee shop")
        location: Location center (e.g., "District 1, Ho Chi Minh City")
        radius_meters: Search radius in meters (default 5km)
        max_results: Max results (default 20)
    
    Returns:
        Formatted list of businesses with: name, address, rating, 
        review count, price level, opening hours, reviews summary
    """
```

**Implementation notes:**
- Use `POST https://places.googleapis.com/v1/places:searchText`
- FieldMask: `places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.priceLevel,places.reviews,places.reviewSummary,places.currentOpeningHours,places.websiteUri,places.delivery,places.dineIn,places.takeout`
- Geocode `location` string to lat/lng using Places API or hardcode major VN cities
- Parse and format results into readable markdown
- **Requires**: Google Cloud API key with Places API enabled
- **Cost**: ~$0.04/request — with $200/mo free credit = ~5,000 requests/month free

#### Tool 9: `deep_research`

```python
async def deep_research(
    topic: str,
    context: str | None = None,
    depth: str = "standard",  # "quick" | "standard" | "comprehensive"
) -> str:
    """
    Conduct deep research on a topic using Perplexity AI or multi-step
    search pipeline.
    
    Use for complex research questions that need synthesis from multiple 
    sources, not simple fact lookups.
    
    Args:
        topic: Research question or topic
        context: Additional context to guide the research
        depth: Research depth level
    
    Returns:
        Comprehensive research summary with sources
    """
```

**Implementation notes:**
- **Option A (preferred)**: Perplexity API with `sonar` model — single API call, returns structured answer with citations
- **Option B (fallback)**: Multi-step pipeline: `search_web` (3-5 queries) → `crawl_web` (top results) → Gemini summarization
- **Cost**: Perplexity free tier provides trial credits sufficient for personal use

#### Tool 10: `generate_image`

```python
async def generate_image(
    prompt: str,
    style: str | None = None,
    aspect_ratio: str = "1:1",
    size: str = "1K",
    reference_images: list[str] | None = None,
) -> str:
    """
    Generate brand-related images using Gemini image generation.
    
    Use for: mood boards, logo concepts, color palette visualizations,
    brand asset drafts, packaging mockups.
    
    Args:
        prompt: Detailed description of the image to generate
        style: Style modifier (e.g., "minimalist", "vintage", "modern")
        aspect_ratio: Image aspect ratio (1:1, 16:9, 4:3, 9:16, etc.)
        size: Image size (512, 1K, 2K, 4K)
        reference_images: Paths to reference images for style consistency
    
    Returns:
        Path to saved image file + description
    """
```

**Implementation notes:**
- Use `google-genai` SDK (already a dependency via google-generativeai)
- Model: `gemini-2.0-flash` (free tier) for draft images; `gemini-3.1-flash-image-preview` for higher quality
- Save to `data/generated_assets/[session_id]/`
- Include brand context in prompt for consistency
- **Vietnamese language support**: ✅ (vi-VN is a supported locale)

#### Tool 11: `generate_document`

```python
async def generate_document(
    content: dict,
    format: str = "pdf",  # "pdf" | "docx"
    template: str = "brand_strategy",
    output_path: str | None = None,
) -> str:
    """
    Generate a professional brand strategy document.
    
    Args:
        content: Structured content dict with sections
        format: Output format (pdf or docx)
        template: Document template to use
        output_path: Custom output path
    
    Returns:
        Path to generated document
    """
```

**Implementation notes:**
- **PDF**: Use `fpdf2` — pure Python, no external dependencies
  - Custom branded headers/footers
  - Table of contents generation
  - Image embedding (mood boards, Brand Key visual)
  - Table formatting for competitor analysis, KPIs
- **DOCX**: Use `python-docx`
  - Professional styling with custom fonts and colors
  - Section headings, bullet lists, tables
  - Image embedding
  - Can be further edited by user in Word/Google Docs

#### Tool 12: `generate_presentation`

```python
async def generate_presentation(
    content: dict,
    template: str = "brand_strategy",
    output_path: str | None = None,
) -> str:
    """
    Generate a PPTX brand strategy presentation.
    
    Args:
        content: Structured content with slide definitions
        template: Presentation template
        output_path: Custom output path
    
    Returns:
        Path to generated .pptx file
    """
```

**Implementation notes:**
- Use `python-pptx`
- Pre-designed slide layouts: title, content, comparison, image, chart
- 10-15 slide deck covering executive summary through implementation roadmap
- Brand colors applied from Phase 3 output

### 5.4 Cost Summary

| Category | Tools | Cost |
|----------|-------|------|
| **Free (no API key)** | `generate_document`, `generate_presentation`, `generate_brand_key`, `export_to_markdown`, `get_search_autocomplete` | $0 |
| **Free (existing API keys)** | `search_web`, `crawl_web`, `browse_social_media`, `search_knowledge_graph`, `search_document_library`, `deep_research` (Perplexity trial), `analyze_reviews`, `analyze_social_profile` | $0 |
| **Free tier** | `generate_image` (gemini-2.0-flash), `search_places` ($200/mo GCP credit) | $0 (within limits) |
| **Low cost** | `generate_image` (gemini-3.1-flash-image, ~$0.05/img) | ~$1-2 per full project |

**Total cost per brand strategy project: $0 — $2** (depending on image quality preference)

### 5.5 New Dependencies Required

| Package | Purpose | License | Size |
|---------|---------|---------|------|
| `fpdf2` | PDF generation | LGPL v3 | Lightweight |
| `python-docx` | DOCX generation | MIT | Lightweight |
| `python-pptx` | PPTX generation | MIT | Lightweight |
| `google-genai` | Gemini image generation SDK | Apache 2.0 | Already partially present |

All are free, open-source, and lightweight.

---

## 6. Sub-Agents & Delegation Strategy

### 6.1 Overview

Following the Claude Code pattern from the Vision doc — main agent CAN do everything but SELECTIVELY delegates for context efficiency:

```
┌──────────────────────────────────────────────────────────────────┐
│                    MAIN AGENT (Brand Manager)                     │
│  Model: Gemini 2.5 Flash / Gemini 3 Flash                        │
│                                                                   │
│  Core Tools (always loaded):                                      │
│  • search_knowledge_graph   • search_document_library             │
│  • search_web               • crawl_web                           │
│  • todo_write               • tool_search                         │
│  • deep_research                                                  │
│                                                                   │
│  Loadable Tools (via tool_search):                                │
│  • generate_image           • generate_document                   │
│  • generate_presentation    • search_places                       │
│  • browse_social_media      • analyze_reviews                     │
│  • get_search_autocomplete  • analyze_social_profile              │
│  • generate_brand_key       • export_to_markdown                  │
│                                                                   │
│  Delegation: "task" tool → sub-agents                             │
└──────────────┬──────────┬──────────┬──────────┬─────────────────┘
               │          │          │          │
               ▼          ▼          ▼          ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Market   │  │ Social   │  │ Creative │  │ Document │
│ Research │  │ Media    │  │ Studio   │  │ Generator│
│ Agent    │  │ Analyst  │  │ Agent    │  │ Agent    │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### 6.2 Sub-Agent 1: Market Research Agent

**Purpose**: Handle data-heavy research tasks that would pollute main agent's context.

**When to delegate**: 
- Competitor deep-dive analysis (multiple businesses)
- Local market mapping with search_places
- Trend research requiring multiple web searches

**Model**: Gemini 2.5 Flash Lite (cost-efficient for data gathering)

**Pre-loaded Tools**: `search_web`, `crawl_web`, `search_places`, `get_search_autocomplete`, `deep_research`, `analyze_reviews`

**Task Interface**:
```python
{
    "task": "Research the competitive landscape for specialty coffee shops in District 1, HCMC",
    "instructions": "Find top 5 competitors. For each: brand positioning, pricing, rating, reviews summary, social presence. Return structured analysis.",
    "context": {
        "business_type": "specialty coffee shop",
        "location": "District 1, Ho Chi Minh City",
        "business_name": "user's business name"
    },
    "expected_output": "Structured competitor analysis with 5 entries"
}
```

### 6.3 Sub-Agent 2: Social Media Analyst

**Purpose**: Handle social media research tasks requiring browser automation.

**When to delegate**:
- Analyzing competitor social media profiles
- Mining customer conversations on social platforms
- Gathering social trend data

**Model**: Gemini 3 Flash Preview (needed for browser-use vision)

**Pre-loaded Tools**: `browse_social_media`, `analyze_social_profile`

**Task Interface**:
```python
{
    "task": "Analyze Instagram profiles of 3 competitors: @competitor1, @competitor2, @competitor3",
    "instructions": "For each: content strategy analysis, engagement rate estimation, brand voice assessment, visual identity analysis, top performing content themes",
    "context": { "brand_category": "specialty coffee" },
    "expected_output": "Comparative social media brand analysis"
}
```

### 6.4 Sub-Agent 3: Creative Studio Agent

**Purpose**: Handle creative asset generation (images, visual concepts).

**When to delegate**:
- Generating mood boards (multiple images)
- Creating logo concept variations
- Color palette visualization
- Brand Key visual generation

**Model**: Gemini 3.1 Flash Image Preview (best for image generation quality)

**Pre-loaded Tools**: `generate_image`, `generate_brand_key`

**Task Interface**:
```python
{
    "task": "Generate a mood board for a modern Vietnamese specialty coffee brand",
    "instructions": "Create 4 images: (1) Interior atmosphere mood, (2) Brand color palette visualization, (3) Logo concept - minimalist, (4) Packaging concept - coffee cup. Style: modern, warm, artisanal. Colors: earth tones with teal accent.",
    "context": {
        "brand_personality": "Sophisticated yet approachable, modern craft",
        "color_direction": "earth tones (warm brown, cream) + teal accent",
        "imagery_style": "minimalist, warm natural lighting, artisanal craft"
    },
    "expected_output": "4 image files + description of each"
}
```

### 6.5 Sub-Agent 4: Document Generator Agent

**Purpose**: Handle document assembly — converting structured strategy data into professional deliverables.

**When to delegate**:
- Generating the final brand strategy PDF/DOCX
- Creating the pitch deck presentation
- Compiling the Brand Key one-pager

**Model**: Gemini 2.5 Flash Lite (text-focused, cost-efficient)

**Pre-loaded Tools**: `generate_document`, `generate_presentation`, `export_to_markdown`

**Task Interface**:
```python
{
    "task": "Generate the final brand strategy document",
    "instructions": "Compile all phase outputs into a professional PDF. Include: cover page, TOC, all 6 sections, mood board images, Brand Key visual, KPI table, implementation roadmap.",
    "context": {
        "phase_outputs": { ... all accumulated phase data ... },
        "brand_colors": ["#8B6914", "#F5F0E8", "#2A9D8F"],
        "brand_name": "brand name",
        "format": "pdf"
    },
    "expected_output": "Path to generated PDF file"
}
```

### 6.6 Delegation Decision Matrix

```
┌───────────────────────────────────────────────────────────────────┐
│                  DELEGATION DECISION MATRIX                        │
├───────────────────┬──────────┬──────────────────────────────────┤
│ Task Type         │ Delegate?│ Reason                           │
├───────────────────┼──────────┼──────────────────────────────────┤
│ KG search         │ ❌ No    │ Core reasoning, keep in context  │
│ Doc search        │ ❌ No    │ Core reasoning, keep in context  │
│ Single web search │ ❌ No    │ Quick, contextual                │
│ Deep research     │ ❌ No    │ Often needs main agent judgment  │
│ Strategic analysis│ ❌ No    │ Core brand strategy reasoning    │
│ Mentor explanation│ ❌ No    │ Direct user interaction          │
│ User Q&A          │ ❌ No    │ Direct user interaction          │
│                   │          │                                  │
│ Multi-competitor  │ ✅ Yes   │ Data-heavy, predictable pattern  │
│   research        │  → MRA   │                                  │
│ Social media      │ ✅ Yes   │ Browser automation, specialized  │
│   analysis        │  → SMA   │                                  │
│ Image generation  │ ✅ Yes   │ Specialized model, many images   │
│   (batch)         │  → CSA   │                                  │
│ Document assembly │ ✅ Yes   │ Mechanical, pollutes context     │
│                   │  → DGA   │                                  │
│                   │          │                                  │
│ Single image gen  │ 🔄 Maybe │ Simple → main; Complex → CSA    │
│ Single social     │ 🔄 Maybe │ Quick check → main; Deep → SMA  │
│   browse          │          │                                  │
└───────────────────┴──────────┴──────────────────────────────────┘
```

---

## 7. Integration: How Skills + KG + Tools Work Together

### 7.1 Runtime Flow Example

**Scenario**: User wants to build a brand for a new specialty café in District 3, HCMC.

```
1. User: "Tôi muốn xây dựng thương hiệu cho quán café specialty mới"

2. Main Agent loads: brand-strategy-orchestrator skill
   → Enters Phase 0

3. Phase 0 (Business Problem Diagnosis):
   [MENTOR] Explains the process, asks about the business
   [USER provides info: new business, specialty café, District 3, ...]
   [AGENT synthesizes problem statement]
   [QUALITY GATE] ✅ All Phase 0 criteria met
   [USER confirms] → Move to Phase 1

4. Phase 1 (Market Intelligence):
   [AGENT loads: market-research skill]
   [MENTOR] Explains what research we'll do
   
   [DELEGATE → Market Research Agent]:
     - search_places("specialty coffee", "District 3, HCMC")
     - search_web("specialty coffee market Vietnam 2026")
     - For each competitor: crawl_web(website), search_web(reviews)
     → Returns: structured competitor analysis
   
   [DELEGATE → Social Media Analyst]:
     - browse_social_media("Analyze top 3 specialty coffee Instagram pages in HCMC")
     → Returns: social media competitive analysis
   
   [MAIN AGENT: KG search]
     - search_knowledge_graph("market segmentation criteria methods")
     - search_knowledge_graph("consumer behavior coffee purchasing")
     - search_document_library("target audience F&B segmentation")
     → Uses KG knowledge to enrich analysis framework
   
   [MAIN AGENT: Synthesize all inputs into Phase 1 output]
   [PRESENT to user with mentor-style explanation]
   [QUALITY GATE] ✅ All Phase 1 criteria met
   [USER feedback → iterate if needed] → Move to Phase 2

5. Phase 2-3 (Strategy + Identity):
   [AGENT loads: brand-positioning-identity skill]
   [KG SEARCH]: positioning frameworks, CBBE, brand elements
   [MAIN AGENT: Strategic reasoning and positioning decisions]
   
   [DELEGATE → Creative Studio Agent]:
     - generate_image(mood boards, logo concepts, color palettes)
     → Returns: visual assets
   
   [Continue through phases...]

6. Phase 5 (Deliverables):
   [DELEGATE → Document Generator Agent]:
     - generate_document(all_phase_outputs, format="pdf")
     - generate_presentation(summary, format="pptx")
     → Returns: final deliverable files
   
   [MAIN AGENT: Present final deliverables to user]
```

### 7.2 KG Integration Points by Phase

| Phase | KG Search Purpose | Example Queries |
|-------|------------------|----------------|
| 0 | Validate business problem framing + rebrand decision support | `"brand strategy business problem"`, `"brand health metrics"`, `"brand revitalization"` |
| 0.5 | Guide brand equity audit (rebrand only) | `"brand audit brand inventory"`, `"brand equity sources"`, `"brand element adaptability"`, `"brand migration strategy"` |
| 1 | Enrich research methodology + strategic synthesis | `"market segmentation"`, `"competitor analysis framework"`, `"consumer behavior"`, `"SWOT analysis"` |
| 2 | Ground positioning in theory + stress test | `"brand positioning points of parity"`, `"competitive differentiation"`, `"brand essence"`, `"product brand alignment"` |
| 3 | Guide identity decisions + naming | `"brand personality framework"`, `"distinctive brand assets"`, `"brand elements criteria"`, `"brand name selection"` |
| 4 | Strengthen messaging | `"persuasion principles"`, `"AIDA model"`, `"integrated marketing communication"` |
| 5 | Validate measurement + transition strategy | `"brand equity measurement"`, `"brand tracking"`, `"brand audit"`, `"brand migration strategy"` |

### 7.3 Context Window Management

The skills are designed to be loaded on-demand to keep the context clean:

```
Phase 0: [orchestrator skill] + [core tools]
Phase 0.5: [orchestrator skill] + [core tools] (rebrand only — audit procedures embedded in orchestrator)
Phase 1: [orchestrator skill] + [market-research skill] + [core tools]
Phase 2-3: [orchestrator skill] + [brand-positioning-identity skill] + [core tools]
Phase 4-5: [orchestrator skill] + [brand-communication-planning skill] + [core tools]
```

Previous phase OUTPUTS are kept in context (structured data), but the sub-skills for completed phases can be unloaded.

---

## 8. Appendix

### 8.1 F&B-Specific Considerations

The workflow is designed with F&B specifics built in:

| F&B-Specific Element | Where It Appears |
|---------------------|-----------------|
| **Location-based competition** | Phase 1: search_places for local mapping |
| **Sensory branding** | Phase 3: taste, aroma, ambient, tactile identity |
| **Menu as brand expression** | Phase 2 + 3: product-brand alignment, product naming, menu design direction |
| **In-store experience** | Phase 3 + 4: touchpoint design, staff as brand ambassadors |
| **Review management** | Phase 0.5 + 1: existing perception research; Phase 5: KPI tracking |
| **Seasonal/limited offerings** | Phase 4: scarcity principle in messaging |
| **Visual-heavy social media** | Phase 4: Instagram/TikTok-first channel strategy |
| **Local community** | Phase 4: unity principle, community content pillar |
| **Google Maps prominence** | Phase 1 + 5: search_places, review strategy |
| **Product IS the Brand** | Phase 2: product-brand alignment — F&B product quality/taste must embody brand promise |
| **Physical rebrand costs** | Phase 5: signage, menus, packaging, uniforms, interior — transition plan must budget these |
| **Budget sensitivity** | Phase 0 + 5: F&B margins are tight; budget discovery early, budget-tier implementation |
| **Existing customer base** | Phase 0.5: preserve-discard analysis must weigh loyal customer expectations |
| **Staff as brand ambassadors** | Phase 5: transition plan includes internal rollout & training for service consistency |

### 8.2 Frameworks Reference Table

| Framework | Source | Phase Applied |
|-----------|--------|--------------|
| **STDP** (Segmentation, Targeting, Differentiation, Positioning) | Kotler | Phase 1-2 |
| **CBBE Pyramid** (Salience → Performance/Imagery → Judgments/Feelings → Resonance) | Keller | Phase 2-3, 5 |
| **Brand Resonance Model** | Keller | Phase 2 |
| **Brand Value Chain** | Keller | Phase 5 |
| **Brand Element Selection Criteria** (Memorable, Meaningful, Likable, Transferable, Adaptable, Protectable) | Keller | Phase 3 |
| **Positioning: Ladder in the Mind** | Ries & Trout | Phase 2 |
| **Double Jeopardy Law** | Sharp | Phase 1 (market analysis) |
| **Mental & Physical Availability** | Sharp | Phase 3, 5 |
| **Distinctive Brand Assets** | Sharp | Phase 3 |
| **7 Principles of Persuasion** | Cialdini | Phase 4 |
| **AIDA Model** | — | Phase 4 |
| **5W1H Framework** | Brand Manager | Phase 0-5 (thinking spine) |
| **Brand Key** | Unilever model (industry standard) | Phase 5 |
| **JTBD (Jobs to Be Done)** | Christensen | Phase 1 |
| **Porter's Five Forces** | Porter | Phase 1 |
| **Aaker's Brand Personality** | Aaker | Phase 3 |
| **Rebrand Decision Matrix** | BrandMind (derived from Keller Ch.13) | Phase 0 |
| **Preserve-Discard Matrix** | BrandMind (derived from Keller Ch.8, Ch.13) | Phase 0.5 |
| **Brand Audit** (Inventory + Exploratory) | Keller Ch.8 | Phase 0.5 |
| **Brand Revitalization** | Keller Ch.13 | Phase 0.5, 2 |
| **Brand Reinforcement** | Keller Ch.13 | Phase 0.5, 2 |
| **SWOT Analysis** | General strategy | Phase 1 (strategic synthesis) |
| **Perceptual Mapping** | Marketing strategy (Kotler) | Phase 1-2 |
| **Positioning Stress Test** (5 criteria) | BrandMind (derived from Ries & Trout, Keller) | Phase 2 |

### 8.3 Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Google Places API price increase | Fallback: search_web for local business data |
| Gemini image gen quality insufficient for logos | Note: generated images are DIRECTION, not final assets. Professional designer needed for production logos |
| Social media platform blocks browser automation | Fallback: search_web for public social data; note limitation to user |
| pytrends dead, no trend data | Alternative: Google Autocomplete (free), Perplexity search for trends |
| KG doesn't have F&B-specific knowledge | Agent combines KG marketing frameworks with real-time web research |
| User provides insufficient information | Skill includes guided questions; agent asks follow-ups |
| Context window overflow | Phase-based skill loading + sub-agent delegation + context editing middleware |
| **Rebrand equity loss** | Phase 0.5 preserve-discard matrix; gradual migration strategy; identity transition plan |
| **Stakeholder resistance to rebrand** | Phase 5 stakeholder map + internal rollout with rationale communication |
| **Rebrand scope creep** | Phase 0 scope classification locks scope; proactive loop triggers if misalignment detected |
| **Physical changeover costs exceed budget** | Phase 5 budget-tier implementation (must_do vs nice_to_have); phased rollout |
| **Customer confusion during transition** | Phase 5 transition timeline + customer communication plan + visual bridge strategy |

### 8.4 Implementation Priority

```
Priority 1 (Required for MVP):
├── brand-strategy-orchestrator skill (v2.0 with workflow branching)
├── market-research skill (with strategic synthesis)
├── brand-positioning-identity skill (with product-brand alignment + naming process)
├── brand-communication-planning skill (with budget-tier modifiers)
├── search_places tool
├── deep_research tool
└── generate_document tool (PDF)

Priority 2 (Enhanced experience):
├── generate_image tool
├── generate_presentation tool
├── analyze_reviews tool
├── Market Research sub-agent
├── Creative Studio sub-agent
└── generate_brand_key tool

Priority 3 (Polish):
├── get_search_autocomplete tool
├── analyze_social_profile tool
├── Social Media Analyst sub-agent
├── Document Generator sub-agent
└── export_to_markdown tool

Note: Rebrand-specific capabilities (Phase 0.5 Brand Equity Audit,
Rebrand Decision Matrix, Preserve-Discard Matrix, Identity Transition
Planning, Transition & Change Management) are embedded within Priority 1
skills — no separate implementation needed.
```

---

*This blueprint covers both new brand creation AND rebranding (refresh/reposition/full rebrand) scenarios end-to-end. After approval, the next step is implementing the skills and tools in priority order, followed by system prompt creation.*
