# Task 45: Brand Communication & Planning Skill (Phases 4-5)

## 📌 Metadata

- **Epic**: Brand Strategy — Skills
- **Priority**: Critical (P1 — Messaging, deliverables, transition planning)
- **Estimated Effort**: 1.5 weeks
- **Team**: Backend
- **Related Tasks**: Task 42 (Orchestrator), Task 44 (Phase 3 output → Phase 4 input), Task 39 (Document Gen tools)
- **Blocking**: Task 46 (E2E Integration)
- **Blocked by**: Task 35 (Skills Setup), Task 42 (Orchestrator), Task 39 (Document Gen Suite)

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals)
- [x] 🛠 [Solution Design](#🛠-solution-design)
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan)
- [x] 📋 [Implementation Detail](#📋-implementation-detail)
    - [x] ✅ [Component 1: Messaging Architecture Framework](#component-1-messaging-architecture-framework)
    - [x] ✅ [Component 2: Channel Strategy & Content Pillars](#component-2-channel-strategy--content-pillars)
    - [x] ✅ [Component 3: Deliverable Assembly Framework (Phase 5)](#component-3-deliverable-assembly-framework)
    - [x] ✅ [Component 4: Transition & Change Management (Rebrand)](#component-4-transition--change-management)
    - [x] ✅ [Component 5: Output Schemas](#component-5-output-schemas)
    - [x] ✅ [Component 6: Skill Markdown File](#component-6-skill-markdown-file)
- [ ] 🧪 [Test Cases](#🧪-test-cases)
- [ ] 📝 [Task Summary](#📝-task-summary)

## 🔗 Reference Documentation

- **Blueprint Reference**: `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — Section 4.5 (Skill 4), Sections 3.6-3.7 (Phases 4-5)
- **Phase 4 Activities**: Blueprint Section 3.6 — Value Proposition, Messaging, Persuasion, AIDA, Channels, Content Pillars, Story
- **Phase 5 Activities**: Blueprint Section 3.7 — Document Assembly, Brand Key, KPIs, Roadmap, Measurement, Presentation
- **Transition Plan**: Blueprint Section 3.7 `phase_5_output.transition_plan` (rebrand only)
- **Budget-Tier Modifiers**: Blueprint Section 4.5 — Bootstrap/Starter/Growth/Enterprise

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Phase 4 (Communication Framework): Define WHAT brand says and HOW — messaging hierarchy, persuasion, channels
- Phase 5 (Strategy Plan & Deliverables): Compile everything into professional deliverables + implementation roadmap
- Skill available via progressive disclosure; orchestrator instructs agent to read this SKILL.md when entering Phase 4
- Key frameworks applied:
  - Cialdini's 7 Persuasion Principles (Phase 4)
  - AIDA Model (Phase 4)
  - Brand Key framework (Phase 5)
  - Budget-Tier Implementation Modifiers (Phase 5)
- Rebrand additions:
  - Transition & Change Management Plan (Phase 5 only for rebrand scopes)
  - Stakeholder Communication Plan
  - Physical & Digital Asset Changeover Checklists with cost estimates

### Mục tiêu

1. Messaging Architecture: Core value proposition → messaging hierarchy → proof points
2. Persuasion Integration: Map Cialdini principles to F&B messaging
3. Channel Strategy: F&B-focused platform recommendations with content types
4. Deliverable Assembly: Orchestrate document/presentation generation tools
5. Implementation Roadmap: 3 time horizons × budget-tier modifiers
6. Transition Plan: Stakeholder, internal, customer, physical, digital changeover (rebrand)
7. KPI Framework: Measurable brand metrics

### Success Metrics / Acceptance Criteria

- **Messaging**: Clear value proposition + 3-5 key messages with proof points
- **Persuasion**: At least 2 Cialdini principles applied with F&B examples
- **Channels**: Platform strategy with content types and frequencies
- **Deliverables**: PDF/DOCX strategy document + PPTX deck generated
- **Roadmap**: 3 time horizons, each item tagged must_do/nice_to_have, aligned to budget_tier
- **Transition**: Complete plan for rebrand scopes (stakeholder, asset changeover, timeline)
- **KPIs**: 5+ metrics with measurement methods and review cadence

------------------------------------------------------------------------

## 🛠 Solution Design

### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Skill markdown | `src/shared/src/shared/agent_skills/brand_strategy/brand-communication-planning/SKILL.md` | Skill file |
| Phase 4 output schema | `src/core/src/core/brand_strategy/schemas/phase_4.py` | Messaging validation |
| Phase 5 output schema | `src/core/src/core/brand_strategy/schemas/phase_5.py` | Deliverable validation |
| Messaging models | `src/core/src/core/brand_strategy/analysis/messaging.py` | Value prop, messaging, persuasion |
| Roadmap builder | `src/core/src/core/brand_strategy/analysis/roadmap.py` | Implementation roadmap |
| Transition planner | `src/core/src/core/brand_strategy/analysis/transition.py` | Rebrand transition plan |

------------------------------------------------------------------------

## 📋 Implementation Detail

### Component 1: Messaging Architecture Framework

#### Requirement 1 - Value Proposition + Messaging Hierarchy + Persuasion
- **Requirement**: Structured messaging framework from Blueprint Section 4.5 Phase 4
- **Implementation**:
  - `src/core/src/core/brand_strategy/analysis/messaging.py`
  ```python
  from pydantic import BaseModel, Field


  class ValueProposition(BaseModel):
      """Core value proposition at 3 levels."""
      one_liner: str = ""  # One sentence
      elevator_pitch: str = ""  # 30-second version
      full_story: str = ""  # 2-3 paragraph version


  class KeyMessage(BaseModel):
      """A key message in the messaging hierarchy."""
      type: str  # functional, emotional, differentiating, credibility, community
      message: str = ""
      proof_points: list[str] = Field(default_factory=list)


  class PersuasionApplication(BaseModel):
      """Application of a Cialdini persuasion principle."""
      principle: str  # social_proof, authority, scarcity, liking, reciprocity, commitment, unity
      application: str = ""  # How it's applied for this brand
      message_example: str = ""  # Concrete message example
      f_and_b_example: str = ""  # F&B-specific example


  class AIDAMapping(BaseModel):
      """AIDA communication flow mapping."""
      attention: str = ""  # How we grab attention
      interest: str = ""  # How we build interest
      desire: str = ""  # How we create desire
      action: str = ""  # How we drive action


  # Cialdini mappings for F&B (from Blueprint Section 4.5)
  CIALDINI_FNB_EXAMPLES = {
      "social_proof": "Join 500+ coffee lovers who start their day with us",
      "authority": "Beans selected by Q-grader certified roasters",
      "scarcity": "Limited seasonal menu — available this month only",
      "liking": "Community-building, barista-as-brand-ambassador",
      "reciprocity": "Free tasting events, generous sampling",
      "commitment": "Loyalty program, 'your daily ritual' framing",
      "unity": "'Part of the neighborhood' identity",
  }
  ```
- **Acceptance Criteria**:
  - [ ] Value proposition at 3 levels (one-liner, elevator, full)
  - [ ] 5 message types with proof points
  - [ ] Cialdini principles mapped to F&B examples
  - [ ] AIDA flow per customer touchpoint

### Component 2: Channel Strategy & Content Pillars

#### Requirement 1 - F&B Channel Strategy
- **Requirement**: Platform-specific strategy from Blueprint Section 4.5
- **Implementation**: Models in `src/core/src/core/brand_strategy/analysis/messaging.py` (same file as Component 1)
  ```python
  class ChannelStrategy(BaseModel):
      """Channel with strategy definition."""
      channel: str  # Instagram, Facebook, TikTok, Google Maps, In-store, Website
      purpose: str
      content_types: list[str] = Field(default_factory=list)
      posting_frequency: str = ""
      audience_match: str = ""


  class ContentPillar(BaseModel):
      """A content pillar in the content strategy."""
      pillar: str
      percentage: int = 0  # % of content mix
      description: str = ""
      example_topics: list[str] = Field(default_factory=list)


  # Default F&B content pillars (from Blueprint Section 4.5)
  DEFAULT_FNB_PILLARS = [
      ContentPillar(
          pillar="Product Showcase", percentage=40,
          description="Menu items, preparation, ingredients",
      ),
      ContentPillar(
          pillar="Behind the Scenes", percentage=20,
          description="Team, sourcing, craftsmanship",
      ),
      ContentPillar(
          pillar="Community & Lifestyle", percentage=20,
          description="Customer moments, local events, culture",
      ),
      ContentPillar(
          pillar="Education & Story", percentage=10,
          description="Origin stories, brewing methods, food pairing",
      ),
      ContentPillar(
          pillar="Promotions & News", percentage=10,
          description="New items, events, special offers",
      ),
  ]
  ```
- **Acceptance Criteria**:
  - [ ] 6 channels defined with purpose and content types
  - [ ] 5 content pillars with percentage allocation
  - [ ] F&B-specific recommendations

### Component 3: Deliverable Assembly Framework (Phase 5)

#### Requirement 1 - Document Assembly + KPIs + Roadmap
- **Requirement**: Phase 5 compilation orchestration from Blueprint Section 4.5
- **Implementation**:
  - `src/core/src/core/brand_strategy/analysis/roadmap.py`
  ```python
  from pydantic import BaseModel, Field


  class RoadmapItem(BaseModel):
      """An action in the implementation roadmap."""
      action: str
      owner: str = ""
      priority: str = "must_do"  # must_do | nice_to_have
      estimated_cost: str | None = None
      timeline: str = ""


  class ImplementationRoadmap(BaseModel):
      """
      Implementation roadmap with 3 time horizons.

      Budget-tier modifiers from Blueprint Section 4.5:
      - Bootstrap (<50M VND): DIY, social setup, Canva, reuse
      - Starter (50-200M): Pro logo, basic packaging, selective paid
      - Growth (200M-1B): Full identity, website, content, local PR
      - Enterprise (>1B): Everything + interior, photo, influencer, events
      """
      budget_tier: str = ""  # bootstrap, starter, growth, enterprise
      quick_wins: list[RoadmapItem] = Field(default_factory=list)  # 0-3 months
      medium_term: list[RoadmapItem] = Field(default_factory=list)  # 3-6 months
      long_term: list[RoadmapItem] = Field(default_factory=list)  # 6-12 months
      total_estimated_investment: str = ""
      budget_fit_assessment: str = ""

      def apply_budget_modifier(self, budget_tier: str) -> None:
          """
          Adjust roadmap items based on budget tier.

          Logic:
          - Bootstrap (<50M VND): Mark paid activities as nice_to_have,
            move to medium/long-term. Prioritize DIY, organic, free tools.
          - Starter (50-200M): Keep core paid items, defer advanced ones.
          - Growth (200M-1B): Keep most items as-is.
          - Enterprise (>1B): Everything is must_do.

          Args:
              budget_tier: One of "bootstrap", "starter", "growth", "enterprise"
          """
          self.budget_tier = budget_tier
          if budget_tier == "bootstrap":
              # Downgrade paid activities to nice_to_have
              for horizon in [self.quick_wins, self.medium_term, self.long_term]:
                  for item in horizon:
                      if any(
                          kw in item.action.lower()
                          for kw in ["paid", "ads", "influencer", "pr agency",
                                     "photography", "professional"]
                      ):
                          item.priority = "nice_to_have"
          elif budget_tier == "enterprise":
              for horizon in [self.quick_wins, self.medium_term, self.long_term]:
                  for item in horizon:
                      item.priority = "must_do"


  class KPIDefinition(BaseModel):
      """A brand KPI definition."""
      category: str  # awareness, perception, engagement, behavior, loyalty, revenue, distinctiveness
      metric: str
      baseline: str | None = None
      target: str = ""
      measurement_method: str = ""
      review_frequency: str = ""  # weekly, monthly, quarterly


  class MeasurementPlan(BaseModel):
      """Brand measurement plan."""
      kpis: list[KPIDefinition] = Field(default_factory=list)
      tracking_tools: list[str] = Field(default_factory=list)
      review_cadence: str = ""  # monthly, quarterly
      reporting_format: str = ""
  ```
- **Acceptance Criteria**:
  - [ ] 3 time horizons with must_do/nice_to_have tagging
  - [ ] Budget-tier modifier adjusts recommendations
  - [ ] 7 KPI categories from blueprint (awareness through distinctiveness)
  - [ ] Measurement plan with tools and cadence

### Component 4: Transition & Change Management

#### Requirement 1 - Rebrand Transition Plan (Conditional)
- **Requirement**: Complete transition plan produced ONLY for rebrand scopes — Blueprint Section 3.7 & Section 4.5
- **Implementation**:
  - `src/core/src/core/brand_strategy/analysis/transition.py`
  ```python
  import re

  from pydantic import BaseModel, Field


  class StakeholderEntry(BaseModel):
      """A stakeholder in the communication plan."""
      stakeholder: str  # employees, loyal customers, suppliers, media
      impact_level: str  # high, medium, low
      communication_method: str
      timing: str
      key_message: str = ""


  class PhysicalAsset(BaseModel):
      """A physical asset in the changeover checklist."""
      asset: str  # signage, menus, packaging, uniforms, interior
      current_state: str = ""
      new_state: str = ""
      estimated_cost: str = ""
      timeline: str = ""


  class DigitalAsset(BaseModel):
      """A digital platform migration item."""
      platform: str  # Instagram, Google Business, website, ordering apps
      changes_needed: list[str] = Field(default_factory=list)
      timeline: str = ""


  class TransitionPlan(BaseModel):
      """
      Complete transition & change management plan for rebrands.

      Only produced when scope ∈ {refresh, repositioning, full_rebrand}.
      Covers 7 areas from Blueprint Section 4.5.
      """
      approach: str = ""  # big_bang, phased, inside_out

      # 1. Stakeholder Communication
      stakeholder_map: list[StakeholderEntry] = Field(
          default_factory=list
      )

      # 2. Internal Rollout
      internal_rollout: list[str] = Field(default_factory=list)
      # List of rollout steps

      # 3. Customer Communication
      customer_announcement: str = ""
      customer_channels: list[str] = Field(default_factory=list)
      customer_tone: str = ""
      customer_faq: list[dict] = Field(default_factory=list)
      # Each: {question, answer}

      # 4. Physical Asset Changeover
      physical_changeover: list[PhysicalAsset] = Field(
          default_factory=list
      )

      # 5. Digital Migration
      digital_migration: list[DigitalAsset] = Field(
          default_factory=list
      )

      # 6. Transition Timeline (blueprint: pre_launch, d_day, post_launch)
      pre_launch_steps: list[str] = Field(default_factory=list)
      d_day: str = ""  # Launch date plan
      post_launch_steps: list[str] = Field(default_factory=list)

      # 7. Risk Mitigation (blueprint: risk_mitigation)
      risk_mitigation: list[dict] = Field(default_factory=list)
      # Each: {risk: str, mitigation: str}

      def estimate_total_changeover_cost(self) -> str:
          """Sum estimated costs from physical changeovers."""
          total_min = 0
          total_max = 0
          items_with_cost = 0

          for asset in self.physical_changeover:
              if not asset.estimated_cost:
                  continue
              # Parse cost strings like "5-10M VND", "2M VND", "50-100M"
              numbers = re.findall(r"[\d,.]+", asset.estimated_cost)
              if not numbers:
                  continue
              items_with_cost += 1
              values = [float(n.replace(",", "")) for n in numbers]

              # Detect M (million) or B (billion) multiplier
              # Use regex anchored to digits to avoid false positives
              # (e.g., "b" in "about", "rebrand")
              multiplier = 1
              cost_str = asset.estimated_cost
              if re.search(r"\d\s*[bB]\b", cost_str) or "tỷ" in cost_str:
                  multiplier = 1_000
              elif re.search(r"\d\s*[mM]\b", cost_str) or "triệu" in cost_str or "trieu" in cost_str.lower():
                  multiplier = 1

              if len(values) >= 2:
                  total_min += values[0] * multiplier
                  total_max += values[1] * multiplier
              else:
                  total_min += values[0] * multiplier
                  total_max += values[0] * multiplier

          if items_with_cost == 0:
              return "No cost estimates available for physical assets."

          if total_min == total_max:
              return f"{total_min:.0f}M VND ({items_with_cost} items estimated)"
          return (
              f"{total_min:.0f}-{total_max:.0f}M VND "
              f"({items_with_cost} items estimated)"
          )
  ```
- **Acceptance Criteria**:
  - [ ] 7 transition areas from blueprint covered
  - [ ] Physical assets with cost estimates
  - [ ] Digital migration per platform
  - [ ] Timeline: pre-launch → D-Day → post-launch
  - [ ] Risk register with mitigations
  - [ ] Only produced for rebrand scopes (null for new_brand)

### Component 5: Output Schemas

#### Requirement 1 - Phase 4 and Phase 5 Output Schemas
- **Implementation**:
  - `src/core/src/core/brand_strategy/schemas/phase_4.py`
  ```python
  from pydantic import BaseModel, Field

  from core.brand_strategy.analysis.messaging import (
      AIDAMapping,
      ChannelStrategy,
      ContentPillar,
      KeyMessage,
      PersuasionApplication,
      ValueProposition,
  )


  class MessagingHierarchy(BaseModel):
      """Messaging hierarchy per blueprint."""
      primary_message: str = ""
      supporting_messages: list[KeyMessage] = Field(
          default_factory=list
      )
      proof_points: list[str] = Field(default_factory=list)
      tagline_options: list[str] = Field(
          default_factory=list
      )  # Blueprint: tagline_options


  class ChannelStrategyOutput(BaseModel):
      """Channel strategy output per blueprint."""
      channels: list[ChannelStrategy] = Field(default_factory=list)
      content_pillars: list[ContentPillar] = Field(
          default_factory=list
      )  # Blueprint nests content_pillars inside channel_strategy


  class BrandStory(BaseModel):
      """Brand storytelling per blueprint."""
      origin_story: str = ""
      customer_story_template: str = ""  # Blueprint: customer_story_template
      narrative_themes: list[str] = Field(default_factory=list)


  class Phase4Output(BaseModel):
      """Phase 4 output matching Blueprint Section 3.6 schema.

      Uses typed models instead of bare dicts.
      """
      value_proposition: ValueProposition = Field(
          default_factory=ValueProposition
      )
      messaging_hierarchy: MessagingHierarchy = Field(
          default_factory=MessagingHierarchy
      )
      audience_messaging: list[dict] = Field(default_factory=list)
      persuasion_strategy: list[PersuasionApplication] = Field(
          default_factory=list
      )
      aida_framework: AIDAMapping = Field(
          default_factory=AIDAMapping
      )
      channel_strategy: ChannelStrategyOutput = Field(
          default_factory=ChannelStrategyOutput
      )  # Includes content_pillars
      brand_story: BrandStory = Field(default_factory=BrandStory)
  ```

  - `src/core/src/core/brand_strategy/schemas/phase_5.py`
  ```python
  from pydantic import BaseModel, Field

  from core.brand_strategy.analysis.roadmap import (
      ImplementationRoadmap,
      KPIDefinition,
      MeasurementPlan,
  )
  from core.brand_strategy.analysis.transition import TransitionPlan


  class BrandStrategyDocument(BaseModel):
      """Generated strategy document per blueprint."""
      format: str = "pdf"  # pdf, docx
      file_path: str = ""  # Path to generated file
      sections: list[str] = Field(default_factory=list)


  class BrandKeyComponents(BaseModel):
      """Brand Key 9 components per blueprint."""
      root_strength: str = ""
      competitive_environment: str = ""
      target: str = ""
      insight: str = ""
      benefits: str = ""
      values_and_personality: str = ""
      reasons_to_believe: str = ""
      discriminator: str = ""
      brand_essence: str = ""


  class BrandKeySummary(BaseModel):
      """Brand Key one-pager per blueprint."""
      visual: str = ""  # Path to Brand Key image
      components: BrandKeyComponents = Field(
          default_factory=BrandKeyComponents
      )


  class Phase5Output(BaseModel):
      """Phase 5 output matching Blueprint Section 3.7 schema.

      Uses typed models instead of bare dicts.
      """
      brand_strategy_document: BrandStrategyDocument = Field(
          default_factory=BrandStrategyDocument
      )
      brand_key_summary: BrandKeySummary = Field(
          default_factory=BrandKeySummary
      )
      kpis: list[KPIDefinition] = Field(
          default_factory=list
      )  # Uses typed model (NOT list[dict])
      implementation_roadmap: ImplementationRoadmap = Field(
          default_factory=ImplementationRoadmap
      )
      measurement_plan: MeasurementPlan = Field(
          default_factory=MeasurementPlan
      )
      transition_plan: TransitionPlan | None = None  # Rebrand only
  ```

- **Acceptance Criteria**:
  - [ ] Match blueprint YAML schemas exactly
  - [ ] transition_plan optional (None for new brands)

### Component 6: Skill Markdown File

#### Requirement 1 - Brand Communication & Planning Skill Markdown
- **Requirement**: SKILL.md file for Phases 4-5, discovered by DeepAgents SkillsMiddleware (progressive disclosure). Must follow skill-creator best practices: only `name` + `description` in frontmatter, body <500 lines, imperative form, full-width lines. Split transition planning and deliverable assembly details into reference files.
- **Implementation**:
  - `src/shared/src/shared/agent_skills/brand_strategy/brand-communication-planning/SKILL.md`

- **Directory Structure**:
  ```
  brand-communication-planning/
  ├── SKILL.md                             # Core messaging + planning (~350-450 lines)
  └── references/
      ├── transition_plan.md               # Rebrand transition & change management (7 areas)
      ├── deliverable_assembly.md           # Document structure + Brand Key + presentation assembly
      └── output_templates.md              # Phase4Output + Phase5Output field structures
  ```

- **Frontmatter** (only `name` + `description`):
  ```yaml
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
  ```

- **SKILL.md Body Structure** (~350-450 lines, imperative form, full-width lines):
  ```markdown
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

  ## PERSUASION INTEGRATION (Cialdini × F&B)

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

  Map the customer journey through Attention → Interest → Desire → Action:
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

  Adjust percentages based on brand personality and channel strategy. The agent already knows content marketing basics — focus on brand-specific adaptations.

  Search knowledge graph: `"content strategy pillars"`.

  ## BRAND STORYTELLING

  Craft the brand origin story following narrative structure:
  1. The world before (problem or gap in the market)
  2. The insight (what the founder/team discovered)
  3. The creation (how the brand was born)
  4. The promise (what the brand commits to)
  5. The invitation (how the customer becomes part of the story)

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
  6. Transition timeline (pre-launch → D-Day → post-launch)
  7. Risk register with mitigations

  ## PHASE 5 QUALITY GATE

  Verify before completing: strategy document generated, Brand Key one-pager created, 5+ KPIs defined with measurement methods, roadmap covers 3 horizons aligned to budget tier, transition plan complete (rebrand only), presentation deck assembled.

  ## OUTPUT FORMAT

  Structure Phase 4 output as: value_proposition, messaging_hierarchy, audience_messaging, persuasion_strategy, aida_framework, channel_strategy, brand_story.
  Structure Phase 5 output as: brand_strategy_document, brand_key_summary, kpis, implementation_roadmap, measurement_plan, transition_plan (rebrand only).
  Read `references/output_templates.md` for detailed field structures matching Phase4Output and Phase5Output schemas.
  ```

- **Reference Files**:
  - `references/transition_plan.md` (~100-150 lines): Complete 7-area transition framework for rebrands. Stakeholder map (stakeholder × impact × method × timing × message), physical asset changeover checklist with cost estimates (signage, menus, packaging, uniforms, interior), digital migration per platform, transition timeline (pre-launch/D-Day/post-launch), risk register template.
  - `references/deliverable_assembly.md` (~80-120 lines): 10-section strategy document outline, Brand Key one-pager format (root strength, competitive environment, target, insight, benefits, values, reasons to believe, discriminator, brand essence), executive presentation deck structure (10-12 slides).
  - `references/output_templates.md` (~60-80 lines): Phase4Output + Phase5Output field structures matching Pydantic schemas.

- **Acceptance Criteria**:
  - [ ] YAML frontmatter has ONLY `name` + `description` (no `metadata`, no `allowed-tools`)
  - [ ] `description` ≤ 1024 chars, includes trigger contexts ("Use when...")
  - [ ] SKILL.md body ≤ 500 lines
  - [ ] Body uses imperative form, full-width lines
  - [ ] Phase 4: value proposition, messaging hierarchy, Cialdini with F&B examples, AIDA, channels, content pillars, storytelling
  - [ ] Phase 5: document assembly delegated to reference, KPIs with 7 categories, roadmap with budget tiers
  - [ ] Transition plan delegated to reference file (7 areas, only for rebrand scopes)
  - [ ] Deliverable assembly delegated to reference file (10-section document, Brand Key, presentation)
  - [ ] Output templates delegated to reference file
  - [ ] Budget-tier modifiers clear and actionable

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Messaging Hierarchy
- **Purpose**: Verify messaging hierarchy complete
- **Steps**:
  1. Provide Phase 2-3 outputs
  2. Generate Phase 4 messaging
  3. Verify: value proposition (3 levels) + key messages (3-5) + proof points
- **Expected Result**: Complete messaging hierarchy with clarity test
- **Status**: ⏳ Pending

### Test Case 2: Cialdini Application
- **Purpose**: Verify persuasion principles applied
- **Steps**:
  1. Run Phase 4 for a specialty café brand
  2. Verify at least 2 Cialdini principles applied
  3. Each has F&B-specific message example
- **Expected Result**: 2+ persuasion applications with concrete examples
- **Status**: ⏳ Pending

### Test Case 3: Budget-Tier Roadmap
- **Purpose**: Verify roadmap adjusts to budget tier
- **Steps**:
  1. Generate roadmap with budget_tier="bootstrap"
  2. Generate roadmap with budget_tier="enterprise"
  3. Compare: bootstrap should have fewer paid items, more DIY
- **Expected Result**: Meaningful difference in recommendations per tier
- **Status**: ⏳ Pending

### Test Case 4: Rebrand Transition Plan
- **Purpose**: Verify transition plan for full rebrand
- **Steps**:
  1. Run Phase 5 with scope=FULL_REBRAND
  2. Verify transition plan has all 7 areas
  3. Verify physical_changeover has cost estimates
- **Expected Result**: Complete transition plan with costs and timeline
- **Status**: ⏳ Pending

### Test Case 5: New Brand — No Transition Plan
- **Purpose**: Verify transition plan skipped for new brands
- **Steps**:
  1. Run Phase 5 with scope=NEW_BRAND
  2. Verify transition_plan is None
- **Expected Result**: phase_5_output.transition_plan is None
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation.

### What Was Implemented

**Components Completed**:
- [ ] [Component 1]: Messaging Architecture Framework
- [ ] [Component 2]: Channel Strategy & Content Pillars
- [ ] [Component 3]: Deliverable Assembly Framework
- [ ] [Component 4]: Transition & Change Management
- [ ] [Component 5]: Output Schemas
- [ ] [Component 6]: Skill Markdown File

**Files Created/Modified**:
```
src/shared/src/shared/agent_skills/brand_strategy/
└── brand-communication-planning/
    ├── SKILL.md                           # Core messaging + planning (~350-450 lines)
    └── references/
        ├── transition_plan.md             # Rebrand transition (7 areas, costs, timeline)
        ├── deliverable_assembly.md        # Document structure, Brand Key, presentation
        └── output_templates.md            # Phase4Output + Phase5Output fields

src/core/src/core/brand_strategy/
├── analysis/
│   ├── messaging.py                       # Value prop, messaging, persuasion
│   ├── roadmap.py                         # Implementation roadmap + budget
│   └── transition.py                      # Rebrand transition planner
└── schemas/
    ├── phase_4.py                         # Phase 4 output schema
    └── phase_5.py                         # Phase 5 output schema
```

------------------------------------------------------------------------
