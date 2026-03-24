---
name: brand-communication-planning
description: >-
  Messaging architecture, channel strategy, deliverable assembly, and
  implementation planning for Phases 4-5. Phase 4: value proposition,
  messaging hierarchy, Cialdini persuasion principles for F&B, AIDA
  mapping, channel strategy, content pillars, and brand storytelling.
  Phase 5: strategy document assembly, Brand Key one-pager, KPI
  framework, implementation roadmap with budget-tier modifiers, and
  transition/change management planning (rebrand scopes only).
  Use when the orchestrator enters Phase 4 or Phase 5, or when the user
  asks about messaging, communication strategy, brand deliverables,
  implementation planning, or rebrand transition.
---

# Brand Communication & Planning — Phases 4-5

## ROLE & OBJECTIVE

Transform the brand strategy and identity (from Phases 2-3) into concrete communication frameworks (Phase 4) and professional deliverables with an actionable implementation plan (Phase 5).
Phase 4 answers "WHAT do we say and WHERE?" — Phase 5 answers "HOW do we package and execute this?"

**CORE PRINCIPLE**: STRATEGY WITHOUT EXECUTION IS HALLUCINATION. Every recommendation must have a concrete next step, a responsible owner, and a success metric.

---

# PHASE 4: COMMUNICATION FRAMEWORK

## VALUE PROPOSITION

Craft the core value proposition at 3 levels of detail:
1. **One-liner**: single sentence — the brand promise in its most compressed form
2. **Elevator pitch**: 30-second version — problem, solution, differentiation
3. **Full story**: 2-3 paragraphs — complete narrative with proof points

Ground every level in the positioning statement from Phase 2.

Search knowledge graph: `"value proposition development"`.

## MESSAGING HIERARCHY

Build 3-5 key messages, one for each type:
- **Functional**: what the product delivers (concrete, provable)
- **Emotional**: how the customer feels (aspirational, resonant)
- **Differentiating**: why us over competitors (unique, defensible)
- **Credibility**: why the audience should believe us (evidence, authority)
- **Community**: the tribe the customer joins (belonging, identity)

Each message must have 2-3 proof points grounded in Phase 1 research or Phase 0 business facts.

Search knowledge graph: `"brand messaging"`, `"messaging hierarchy"`.

## PERSUASION INTEGRATION (Cialdini x F&B)

Map at least 2 of Cialdini's 7 principles to concrete F&B messaging:

| Principle | F&B Application Example |
|-----------|------------------------|
| Social Proof | "Join 500+ coffee lovers who start their day with us" |
| Authority | "Beans selected by Q-grader certified roasters" |
| Scarcity | "Limited seasonal menu — available this month only" |
| Liking | Community-building, barista-as-brand-ambassador |
| Reciprocity | Free tasting events, generous sampling |
| Commitment | Loyalty program, "your daily ritual" framing |
| Unity | "Part of the neighborhood" identity |

Select principles that align with the brand personality from Phase 3. Provide concrete message examples for this specific brand.

Search knowledge graph: `"Cialdini persuasion principles"`, `"persuasion marketing"`.

## AIDA COMMUNICATION MAPPING

Map the customer journey through Attention -> Interest -> Desire -> Action:
- **Attention**: what grabs the target audience first (visual, hook, placement)
- **Interest**: what builds curiosity and engagement (story, content, experience)
- **Desire**: what creates want (emotional connection, social proof, aspiration)
- **Action**: what drives the conversion (CTA, offer, accessibility)

Map each AIDA stage to specific channels and content types.

Search knowledge graph: `"AIDA model"`.

## CHANNEL STRATEGY (F&B-Focused)

Recommend platforms based on F&B audience behavior in Vietnam:

| Channel | Purpose | Content Types |
|---------|---------|---------------|
| Instagram | Visual brand building, product showcase | Reels, stories, carousel posts |
| Facebook | Community, promotions, local reach | Posts, events, groups, ads |
| TikTok | Viral reach, younger audience | Short-form video, trends, BTS |
| Google Maps/Business | Discovery, reviews, local SEO | Photos, reviews, Q&A, posts |
| In-store | Direct experience, conversion | Menu, signage, packaging, ambiance |
| Website | Information hub, ordering | Menu, story, blog, online ordering |

Define posting frequency and audience match per channel. Prioritize 2-3 channels based on budget tier and target audience.

Search knowledge graph: `"integrated marketing communication"`.

## CONTENT PILLARS

Establish 5 content pillars with allocation:

| Pillar | % | Focus |
|--------|---|-------|
| Product Showcase | 40% | Menu items, preparation, ingredients |
| Behind the Scenes | 20% | Team, sourcing, craftsmanship |
| Community & Lifestyle | 20% | Customer moments, local events |
| Education & Story | 10% | Origin stories, brewing methods |
| Promotions & News | 10% | New items, events, offers |

Adjust percentages based on brand personality and channel strategy.

Search knowledge graph: `"content strategy pillars"`.

## BRAND STORYTELLING

Craft the brand origin story following narrative structure:
1. The world before (problem or gap in the market)
2. The insight (what the founder/team discovered)
3. The creation (how the brand was born)
4. The promise (what the brand commits to)
5. The invitation (how the customer becomes part of the story)

Also create a customer story template for user-generated content.

## PHASE 4 QUALITY GATE

Verify before advancing: value proposition at 3 levels, 3-5 key messages with proof points, 2+ Cialdini applications, AIDA mapping complete, channel strategy defined, content pillars allocated, brand story drafted.

---

# PHASE 5: STRATEGY PLAN & DELIVERABLES

## DOCUMENT ASSEMBLY

Compile all phase outputs into professional deliverables.
Read `references/deliverable_assembly.md` for the 10-section document structure, Brand Key one-pager format, and presentation assembly instructions.

Delegate document generation to the **document-generator** sub-agent via `task(subagent_type="document-generator")`.
Delegate Brand Key visual to the **creative-studio** sub-agent via `task(subagent_type="creative-studio")`.
Use `generate_spreadsheet` for KPI tracking templates (XLSX).

Search knowledge graph: `"brand guidelines document"`, `"brand key framework"`.

## KPI FRAMEWORK

Define 5+ measurable brand metrics across 7 categories:

| Category | Example Metric | Measurement Method |
|----------|---------------|-------------------|
| Awareness | Brand recall rate | Survey, social mentions |
| Perception | Brand sentiment score | Review analysis, social listening |
| Engagement | Social engagement rate | Platform analytics |
| Behavior | Store visit frequency | POS data, loyalty program |
| Loyalty | Repeat customer rate | POS data, app data |
| Revenue | Average ticket size | POS data |
| Distinctiveness | DBA recognition | Customer survey |

Set baseline (current or "no data"), target (6-12 month goal), and review frequency per metric.

Search knowledge graph: `"brand equity measurement"`, `"brand equity measurement system"`.

## IMPLEMENTATION ROADMAP

Build a 3-horizon roadmap:
- **Quick wins** (0-3 months): high-impact, low-effort actions to launch immediately
- **Medium-term** (3-6 months): sustained brand-building activities
- **Long-term** (6-12 months): strategic investments for brand equity

Tag each item as `must_do` or `nice_to_have`. Apply budget-tier modifiers:

| Tier | Budget (VND) | Focus |
|------|-------------|-------|
| Bootstrap | <50M | DIY, social setup, Canva, content reuse |
| Starter | 50-200M | Professional logo, basic packaging, selective paid |
| Growth | 200M-1B | Full identity system, website, content strategy, local PR |
| Enterprise | >1B | Everything + interior design, professional photography, influencer, events |

Lower budget tiers delay paid activities and prioritize organic/DIY approaches.

Search knowledge graph: `"marketing implementation plan"`.

## TRANSITION & CHANGE MANAGEMENT (Rebrand Only)

**Skip entirely for new_brand scope.** Only produce for refresh, repositioning, or full_rebrand.

Read `references/transition_plan.md` for the complete 7-area transition framework:
1. Stakeholder communication plan
2. Internal rollout
3. Customer communication
4. Physical asset changeover (with cost estimates)
5. Digital migration
6. Transition timeline (pre-launch -> D-Day -> post-launch)
7. Risk register with mitigations

## PHASE 5 QUALITY GATE

Verify before completing: strategy document generated, Brand Key one-pager created, 5+ KPIs defined, roadmap covers 3 horizons aligned to budget tier, transition plan complete (rebrand only), measurement plan with review cadence.

## OUTPUT FORMAT

Structure Phase 4 output as: value_proposition, messaging_hierarchy, audience_messaging, persuasion_strategy, aida_framework, channel_strategy, brand_story.
Structure Phase 5 output as: brand_strategy_document, brand_key_summary, kpis, implementation_roadmap, measurement_plan, transition_plan (rebrand only).
Read `references/output_templates.md` for detailed field structures matching Phase4Output and Phase5Output schemas.
