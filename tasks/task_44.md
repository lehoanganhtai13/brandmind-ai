# Task 44: Brand Positioning & Identity Skill (Phases 2-3)

## 📌 Metadata

- **Epic**: Brand Strategy — Skills
- **Priority**: Critical (P1 — Positioning, identity, naming)
- **Estimated Effort**: 1.5 weeks
- **Team**: Backend
- **Related Tasks**: Task 42 (Orchestrator), Task 43 (Phase 1 output → Phase 2 input), Task 38 (generate_image for mood boards)
- **Blocking**: Task 46 (E2E Integration)
- **Blocked by**: Task 35 (Skills Setup), Task 42 (Orchestrator)

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals)
- [x] 🛠 [Solution Design](#🛠-solution-design)
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan)
- [x] 📋 [Implementation Detail](#📋-implementation-detail)
    - [x] ✅ [Component 1: Positioning Framework (Phase 2)](#component-1-positioning-framework)
    - [x] ✅ [Component 2: Identity Expression Framework (Phase 3)](#component-2-identity-expression-framework)
    - [x] ✅ [Component 3: Naming Process & Preserve-Discard](#component-3-naming-process--preserve-discard)
    - [x] ✅ [Component 4: Output Schemas](#component-4-output-schemas)
    - [x] ✅ [Component 5: Skill Markdown File](#component-5-skill-markdown-file)
- [ ] 🧪 [Test Cases](#🧪-test-cases)
- [ ] 📝 [Task Summary](#📝-task-summary)

## 🔗 Reference Documentation

- **Blueprint Reference**: `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — Section 4.4 (Skill 3), Sections 3.4-3.5 (Phases 2-3)
- **Phase 2 Activities**: Blueprint Section 3.4 — 8 steps (Frame of Reference → Stress Test)
- **Phase 3 Activities**: Blueprint Section 3.5 — Personality, Voice, Visual, Naming, DBA
- **Phase 2 Outputs**: Blueprint Section 3.4 `phase_2_output` schema
- **Phase 3 Outputs**: Blueprint Section 3.5 `phase_3_output` schema

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Phase 2 (Brand Strategy Core) = the strategic heart: positioning, value architecture, brand essence
- Phase 3 (Brand Identity & Expression) = creative execution: personality, voice, visual, naming
- Blueprint Section 4.4 combines these into one skill vì Phase 3 builds directly on Phase 2 outputs
- Key frameworks:
  - Keller's CBBE + Ries & Trout positioning (Phase 2)
  - Aaker's Brand Personality + Sharp's DBA (Phase 3)
- Critical additions from gap analysis:
  - **Product-Brand Alignment** (F&B — menu/pricing/service fit)
  - **Positioning Stress Test** (5 criteria with proactive loop triggers)
  - **Naming Process** (6-step detailed process with availability checks)
  - **Preserve-Discard Matrix** (rebrand identity transition)

### Mục tiêu

1. Positioning Framework: 8-step process from Competitive Frame → Stress Test
2. Identity Expression: Personality, voice, visual direction, DBA strategy
3. Naming Process: Candidate generation, screening, evaluation (Keller's 6 criteria)
4. Rebrand support: Preserve-discard → identity transition planning
5. Output schemas matching blueprint

### Success Metrics / Acceptance Criteria

- **Positioning**: Statement follows template, POPs/PODs clearly defined
- **Product-Brand Fit**: F&B-specific alignment checked (menu, pricing, service)
- **Stress Test**: 5 criteria validated, proactive loop triggers if fails
- **Naming**: For new brands: full 6-step process; for rebrands: keep/rename justified
- **Visual**: Mood boards generated, color/typography direction documented
- **DBA**: Distinctive Brand Assets strategy with priority ordering

------------------------------------------------------------------------

## 🛠 Solution Design

### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Skill markdown | `src/shared/src/shared/agent_skills/brand_strategy/brand-positioning-identity/SKILL.md` | Skill file |
| Phase 2 output schema | `src/core/src/core/brand_strategy/schemas/phase_2.py` | Positioning validation |
| Phase 3 output schema | `src/core/src/core/brand_strategy/schemas/phase_3.py` | Identity validation |
| Positioning models | `src/core/src/core/brand_strategy/analysis/positioning.py` | POPs, PODs, stress test |
| Naming evaluator | `src/core/src/core/brand_strategy/analysis/naming.py` | Keller's 6 criteria |

------------------------------------------------------------------------

## 📋 Implementation Detail

### Component 1: Positioning Framework

#### Requirement 1 - 8-Step Positioning Process with Stress Test
- **Requirement**: Implement the positioning framework from Blueprint Section 4.4 Phase 2
- **Implementation**:
  - `src/core/src/core/brand_strategy/analysis/positioning.py`
  ```python
  from pydantic import BaseModel, Field


  class PointOfParity(BaseModel):
      """A Point of Parity (POP)."""
      type: str  # "category" or "competitive"
      description: str
      evidence: str = ""


  class PointOfDifference(BaseModel):
      """A Point of Difference (POD)."""
      description: str
      desirable: bool = False    # Relevant, distinctive, believable?
      deliverable: bool = False  # Feasible, communicable, sustainable?
      differentiating: bool = False  # Unique, hard to copy?
      evidence: str = ""


  # NOTE: ValueLadder is superseded by ValueArchitecture in Phase2Output
  # (phase_2.py). ValueArchitecture adds reasons_to_believe and uses
  # "attributes" instead of "product_attributes". Do NOT define ValueLadder
  # separately — use ValueArchitecture as the single canonical model.


  class ProductBrandAlignment(BaseModel):
      """F&B Product-Brand Alignment check."""
      product_truth: str = ""  # What product ACTUALLY delivers
      menu_positioning_fit: str = ""  # Does menu reinforce positioning?
      pricing_positioning_fit: str = ""  # Price vs positioning match?
      service_brand_fit: str = ""  # Service style embodies personality?
      gap_actions: list[str] = Field(default_factory=list)


  class StressTestResult(BaseModel):
      """Positioning Stress Test (5 criteria)."""
      competitive_vacancy: bool = False  # No competitor owns this position
      deliverability: bool = False  # Product truth supports the claim
      relevance: bool = False  # Target audience cares
      defensibility: bool = False  # Can be sustained
      budget_feasibility: bool = False  # Communicable within budget
      notes: dict[str, str] = Field(default_factory=dict)
      overall_verdict: str = ""  # Blueprint: overall pass/fail summary

      @property
      def passed(self) -> bool:
          """All 5 criteria must pass."""
          return all([
              self.competitive_vacancy,
              self.deliverability,
              self.relevance,
              self.defensibility,
              self.budget_feasibility,
          ])

      @property
      def failed_criteria(self) -> list[str]:
          """List criteria that failed."""
          criteria = {
              "competitive_vacancy": self.competitive_vacancy,
              "deliverability": self.deliverability,
              "relevance": self.relevance,
              "defensibility": self.defensibility,
              "budget_feasibility": self.budget_feasibility,
          }
          return [k for k, v in criteria.items() if not v]


  class PositioningStatement(BaseModel):
      """
      Complete positioning statement.

      Template: "For [target] who [need], [brand] is the [frame]
      that [POD] because [RTB]."
      """
      target_audience: str = ""
      need: str = ""
      brand_name: str = ""
      competitive_frame: str = ""
      key_pod: str = ""
      reasons_to_believe: str = ""
      full_statement: str = ""
      brand_essence: str = ""  # 1-2 sentences
      brand_mantra: str = ""  # 3-5 words
  ```
- **Acceptance Criteria**:
  - [ ] POPs classified as category or competitive
  - [ ] PODs validated against 3 criteria (desirable, deliverable, differentiating)
  - [ ] Value ladder flows from attributes to outcomes
  - [ ] Product-Brand Alignment has F&B-specific checks
  - [ ] Stress test requires ALL 5 criteria pass

### Component 2: Identity Expression Framework

#### Requirement 1 - Personality, Voice, Visual, DBA Models
- **Requirement**: Models for Phase 3 identity components from Blueprint Section 4.4
- **Implementation**: Embedded in Phase 3 output schema (Component 4)
- **Key Elements**:
  - **Brand Personality** (Aaker's 5 dimensions): Each trait with "means" + "does_not_mean"
  - **Brand Voice**: 4-spectrum scale (formal↔casual, playful↔serious, bold↔understated, technical↔accessible) + DO/DON'T examples
  - **Visual Direction**: Color (with psychology rationale), typography, imagery style, logo direction
  - **Sensory Identity** (F&B): taste, aroma, ambient, packaging
  - **Distinctive Brand Assets** (Sharp): Priority ordered assets to develop

- **Acceptance Criteria**:
  - [ ] Personality traits have descriptors (means/doesn't mean)
  - [ ] Voice spectrum quantified
  - [ ] Color choices linked to psychology
  - [ ] DBA priority strategy defined

### Component 3: Naming Process & Preserve-Discard

#### Requirement 1 - Brand Naming Process (6 Steps)
- **Requirement**: Detailed naming process from Blueprint Section 4.4
- **Implementation**:
  - `src/core/src/core/brand_strategy/analysis/naming.py`
  ```python
  from pydantic import BaseModel, Field


  class KellerCriteria(BaseModel):
      """Keller's 6 Brand Element Selection Criteria (each 1-5)."""
      memorable: int = 0
      meaningful: int = 0
      likable: int = 0
      transferable: int = 0
      adaptable: int = 0
      protectable: int = 0

      @property
      def total_score(self) -> int:
          return sum([
              self.memorable, self.meaningful, self.likable,
              self.transferable, self.adaptable, self.protectable,
          ])


  class NameCandidate(BaseModel):
      """A brand name candidate under evaluation."""
      name: str
      naming_approach: str = ""  # descriptive, suggestive, abstract, etc.
      availability: dict = Field(default_factory=dict)  # domain, social, trademark
      positioning_fit: str = ""
      keller_scores: KellerCriteria = Field(
          default_factory=KellerCriteria
      )
      linguistic_notes: str = ""  # VN + EN compatibility, pronunciation
      shortlisted: bool = False
      selected: bool = False


  class NamingProcess(BaseModel):
      """
      Complete naming process result (6 steps from Blueprint).

      Steps:
      1. Choose naming approach
      2. Generate 10-15 candidates
      3. Linguistic screening (VN + EN)
      4. Availability checks (domain, social, trademark)
      5. Evaluate top 5 against Keller's 6 criteria
      6. Present top 3 to user with rationale
      """
      naming_approach: str = ""  # descriptive, suggestive, abstract, etc.
      candidates: list[NameCandidate] = Field(default_factory=list)
      shortlisted: list[NameCandidate] = Field(default_factory=list)
      selected_name: str = ""
      selection_rationale: str = ""
      skipped: bool = False  # True for refresh/reposition keeping name
      skip_reason: str = ""
  ```

#### Requirement 2 - Preserve-Discard Matrix (Rebrand Only)
- **Requirement**: Identity transition framework from Blueprint Section 4.4
- **Implementation**: Embedded in Phase 3 output schema
  ```python
  class PreserveDiscardItem(BaseModel):
      """An element in the Preserve-Discard Matrix."""
      element: str  # e.g., "Brand name", "Logo", "Color palette"
      current_state: str = ""
      action: str = ""  # "preserve", "evolve", "replace", "remove"
      rationale: str = ""
      equity_value: str = ""  # high, medium, low


  class IdentityTransition(BaseModel):
      """Identity transition plan for rebrands."""
      preserve_discard_items: list[PreserveDiscardItem] = Field(
          default_factory=list
      )
      elements_preserved: list[str] = Field(default_factory=list)
      elements_evolved: list[str] = Field(default_factory=list)
      elements_replaced: list[str] = Field(default_factory=list)
      elements_removed: list[str] = Field(default_factory=list)
      visual_bridge_strategy: str = ""
      dba_continuity_plan: str = ""
  ```

- **Acceptance Criteria**:
  - [ ] 6-step naming process supported
  - [ ] Keller's 6 criteria scored per candidate
  - [ ] Availability fields for domain, social, trademark
  - [ ] Preserve-Discard with 4 action types
  - [ ] Skip naming for refresh scope

### Component 4: Output Schemas

#### Requirement 1 - Phase 2 and Phase 3 Output Pydantic Schemas
- **Implementation**:
  - `src/core/src/core/brand_strategy/schemas/phase_2.py`
  ```python
  from pydantic import BaseModel, Field

  from core.brand_strategy.analysis.positioning import (
      PointOfParity,
      PointOfDifference,
      ProductBrandAlignment,
      StressTestResult,
  )


  class CompetitiveFrame(BaseModel):
      """Competitive frame of reference per blueprint."""
      category: str = ""
      competitive_set: list[str] = Field(default_factory=list)
      category_associations: list[str] = Field(default_factory=list)


  class Positioning(BaseModel):
      """Positioning block per blueprint Section 3.4."""
      points_of_parity: list[PointOfParity] = Field(default_factory=list)
      points_of_difference: list[PointOfDifference] = Field(
          default_factory=list
      )
      positioning_statement: str = ""  # Full statement text
      positioning_rationale: str = ""  # Why this position works


  class ValueArchitecture(BaseModel):
      """Value architecture (blueprint name) = value ladder."""
      attributes: list[str] = Field(default_factory=list)
      functional_benefits: list[str] = Field(default_factory=list)
      emotional_benefits: list[str] = Field(default_factory=list)
      customer_outcomes: list[str] = Field(default_factory=list)
      reasons_to_believe: list[str] = Field(default_factory=list)


  class BrandEssenceBlock(BaseModel):
      """Brand essence block per blueprint."""
      core_idea: str = ""  # 1-2 sentence brand soul
      brand_promise: str = ""  # What brand commits to
      brand_mantra: str = ""  # 3-5 words


  class StrategicAlignment(BaseModel):
      """Insight-to-Strategy Bridge (Blueprint Activity 2.7)."""
      problem_addressed: str = ""  # Links to Phase 0
      insight_leveraged: str = ""  # Links to Phase 1
      differentiation_logic: str = ""


  class Phase2Output(BaseModel):
      """Phase 2 output matching Blueprint Section 3.4 schema.

      Uses typed models matching blueprint YAML structure.
      """
      competitive_frame: CompetitiveFrame = Field(
          default_factory=CompetitiveFrame
      )
      positioning: Positioning = Field(default_factory=Positioning)
      value_architecture: ValueArchitecture = Field(
          default_factory=ValueArchitecture
      )  # Blueprint: value_architecture (NOT value_ladder)
      brand_essence: BrandEssenceBlock = Field(
          default_factory=BrandEssenceBlock
      )
      strategic_alignment: StrategicAlignment = Field(
          default_factory=StrategicAlignment
      )  # Blueprint Activity 2.7 — Insight-to-Strategy Bridge
      product_brand_alignment: ProductBrandAlignment = Field(
          default_factory=ProductBrandAlignment
      )
      positioning_stress_test: StressTestResult = Field(
          default_factory=StressTestResult
      )  # Blueprint: positioning_stress_test (NOT stress_test)
  ```
  
  - `src/core/src/core/brand_strategy/schemas/phase_3.py`
  ```python
  # NOTE: IdentityTransition and PreserveDiscardItem from Component 3
  # are defined IN THIS FILE (above Phase3Output), not in a separate module.
  # They are "embedded in Phase 3 output schema" per the spec.

  from pydantic import BaseModel, Field

  from core.brand_strategy.analysis.naming import NamingProcess


  class TraitDescriptor(BaseModel):
      """A single brand trait with what it means and doesn't mean."""
      trait: str = ""
      means: str = ""
      does_not_mean: str = ""


  class VoiceExample(BaseModel):
      """A do/don't example for brand voice."""
      do: str = ""
      dont: str = ""


  class ColorPalette(BaseModel):
      """Brand color palette."""
      primary: str = ""
      secondary: str = ""
      accent: str = ""
      rationale: str = ""


  class DistinctiveBrandAssets(BaseModel):
      """Distinctive brand assets per blueprint."""
      priority_assets: list[str] = Field(default_factory=list)
      asset_strategy: str = ""


  class SensoryIdentity(BaseModel):
      """Sensory identity for F&B brands."""
      taste_profile: str = ""
      aroma_signature: str = ""
      ambient_experience: str = ""
      packaging_tactile: str = ""


  class BrandPersonality(BaseModel):
      """Brand personality per blueprint (Aaker's 5 dimensions)."""
      archetype: str = ""
      traits: list[str] = Field(default_factory=list)
      trait_descriptors: list[TraitDescriptor] = Field(default_factory=list)
      brand_character: str = ""  # 1-paragraph character description


  class BrandVoice(BaseModel):
      """Brand voice per blueprint."""
      tone_spectrum: dict[str, int] = Field(default_factory=dict)
      # Keys: formal_casual, playful_serious, bold_understated, technical_accessible
      # Values: 1-10 scale
      voice_principles: list[str] = Field(default_factory=list)
      voice_examples: list[VoiceExample] = Field(default_factory=list)


  class VisualIdentity(BaseModel):
      """Visual identity direction per blueprint."""
      color_palette: ColorPalette = Field(default_factory=ColorPalette)
      typography_direction: str = ""
      imagery_style: str = ""
      logo_direction: str = ""
      mood_board_images: list[str] = Field(default_factory=list)
      # File paths from generate_image


  class Phase3Output(BaseModel):
      """Phase 3 output matching Blueprint Section 3.5 schema.

      Uses typed models instead of bare dicts for validation.
      """
      brand_personality: BrandPersonality = Field(
          default_factory=BrandPersonality
      )
      brand_voice: BrandVoice = Field(default_factory=BrandVoice)
      visual_identity: VisualIdentity = Field(
          default_factory=VisualIdentity
      )
      distinctive_brand_assets: DistinctiveBrandAssets = Field(
          default_factory=DistinctiveBrandAssets
      )
      sensory_identity: SensoryIdentity | None = None
      brand_naming: NamingProcess = Field(
          default_factory=NamingProcess
      )  # Uses typed model (NOT bare dict)
      identity_transition: IdentityTransition | None = None  # Rebrand only
  ```

- **Acceptance Criteria**:
  - [ ] Schemas match blueprint YAML definitions exactly
  - [ ] Rebrand-only fields are Optional

### Component 5: Skill Markdown File

#### Requirement 1 - Brand Positioning & Identity Skill Markdown
- **Requirement**: SKILL.md file for Phases 2-3, discovered by DeepAgents SkillsMiddleware (progressive disclosure). Must follow skill-creator best practices: only `name` + `description` in frontmatter, body <500 lines, imperative form, full-width lines. Split Phase 2 and Phase 3 content into reference files.
- **Implementation**:
  - `src/shared/src/shared/agent_skills/brand_strategy/brand-positioning-identity/SKILL.md`

- **Directory Structure**:
  ```
  brand-positioning-identity/
  ├── SKILL.md                             # Core navigation + key frameworks (~350-450 lines)
  └── references/
      ├── naming_process.md                # 6-step naming procedure + Keller's criteria
      ├── identity_transition.md           # Preserve-Discard matrix + rebrand identity planning
      └── output_templates.md              # Phase2Output + Phase3Output field structures
  ```

- **Frontmatter** (only `name` + `description`):
  ```yaml
  ---
  name: brand-positioning-identity
  description: >-
    Brand positioning and identity expression frameworks for Phases 2-3.
    Phase 2: competitive frame of reference, POPs/PODs, value ladder,
    positioning statement, brand essence/mantra, product-brand alignment,
    and positioning stress test with loop-back triggers.
    Phase 3: brand personality (Aaker), voice spectrum, visual identity
    direction, distinctive brand assets (Sharp), sensory identity, and
    brand naming (Keller's 6 criteria).
    Use when the orchestrator enters Phase 2 or Phase 3, or when the user
    asks about positioning, brand identity, naming, or visual direction.
  ---
  ```

- **SKILL.md Body Structure** (~350-450 lines, imperative form, full-width lines):
  ```markdown
  # Brand Positioning & Identity — Phases 2-3

  ## ROLE & OBJECTIVE

  Build a defensible brand position (Phase 2) and translate it into a complete identity system (Phase 3) for F&B businesses.
  Phase 2 answers "WHAT position do we own?" — Phase 3 answers "HOW does that position look, sound, and feel?"
  Use Phase 1 research outputs as the evidence base for every decision.

  **CORE PRINCIPLE**: EVERY IDENTITY CHOICE MUST TRACE BACK TO A STRATEGIC INSIGHT. Never design in a vacuum.

  **SCOPE NOTE**: If the orchestrator indicates Phase 2 is skipped (REFRESH scope), proceed directly to Phase 3 below. REFRESH scope skips positioning — only identity elements are updated.

  ---

  # PHASE 2: BRAND STRATEGY CORE

  ## STEP 1: COMPETITIVE FRAME OF REFERENCE

  Define the category or set of alternatives the brand competes against.
  Use Phase 1's competitor analysis to identify the relevant competitive set.
  The frame determines which POPs are mandatory and where PODs are possible.

  Search knowledge graph: `"competitive frame of reference"`, `"points of parity"`.

  ## STEP 2: POINTS OF PARITY (POPs)

  Identify must-have associations to be a credible player in the frame.
  - Category POPs: what any brand in this category must deliver (e.g., freshness for a bakery)
  - Competitive POPs: negate a competitor's POD so it's no longer an advantage

  ## STEP 3: POINTS OF DIFFERENCE (PODs)

  Identify unique associations the brand can own. Each POD must pass 3 gates:
  - Desirable: relevant, distinctive, believable to the target audience
  - Deliverable: feasible, communicable, sustainable by the business
  - Differentiating: unique, hard for competitors to copy

  Search knowledge graph: `"points of difference"`, `"brand differentiation"`.

  ## STEP 4: VALUE LADDER

  Build the value chain from product → outcome:
  1. Product Attributes → 2. Functional Benefits → 3. Emotional Benefits → 4. Customer Outcomes

  Ensure each rung connects logically to the next. F&B example: "Single-origin beans" → "Rich, complex flavor" → "Feeling of discovery" → "Daily ritual of self-reward."

  ## STEP 5: POSITIONING STATEMENT

  Craft using the template:
  > "For [target audience] who [need/opportunity], [brand] is the [competitive frame] that [key POD] because [reasons to believe]."

  Also distill:
  - Brand Essence: 1-2 sentences capturing the soul of the brand
  - Brand Mantra: 3-5 words (emotional modifier + descriptive modifier + brand function)

  ## STEP 6: PRODUCT-BRAND ALIGNMENT (F&B-Specific)

  Verify the positioning is grounded in what the product actually delivers:
  - Product truth: what does the product objectively deliver?
  - Menu-positioning fit: does the menu reinforce the claimed position?
  - Pricing-positioning fit: does the price point match the positioning tier?
  - Service-brand fit: does the service style embody the brand personality?

  Document gaps and required actions for each misalignment.

  ## STEP 7: INSIGHT-TO-STRATEGY BRIDGE (Blueprint Activity 2.7)

  Connect Phase 1 customer insights to strategic positioning decisions.
  For each key positioning choice, document:
  - Which business problem it addresses (from Phase 0)
  - Which customer insight it leverages (from Phase 1)
  - The differentiation logic (why this creates competitive advantage)

  This creates the `strategic_alignment` output block — ensuring strategy is grounded in evidence, not assumption.

  ## STEP 8: POSITIONING STRESS TEST

  Validate the positioning against 5 criteria. ALL must pass:
  1. **Competitive vacancy**: no competitor currently owns this position
  2. **Deliverability**: the product truth supports the claim
  3. **Relevance**: the target audience cares about this position
  4. **Defensibility**: the position can be sustained over time
  5. **Budget feasibility**: the position is communicable within the stated budget

  If any criterion fails → trigger the appropriate proactive loop (see orchestrator):
  - Deliverability fails → loop to Phase 0 (revisit business model)
  - Relevance fails → loop to Phase 1 (revisit research)

  ## STEP 9: PHASE 2 QUALITY GATE

  Verify before advancing: competitive frame defined, POPs/PODs listed, positioning statement crafted, value architecture complete, product-brand alignment checked, stress test passed, strategic alignment documented (insight-to-strategy bridge).

  ---

  # PHASE 3: BRAND IDENTITY & EXPRESSION

  ## BRAND PERSONALITY (Aaker's 5 Dimensions)

  Select 3-5 personality traits. For each trait, define:
  - "This means..." (positive manifestation)
  - "This does NOT mean..." (boundary)

  Search knowledge graph: `"brand personality dimensions"`, `"Aaker brand personality"`.

  ## BRAND VOICE

  Define voice on 4 spectra (rate 1-10):
  - Formal ↔ Casual
  - Playful ↔ Serious
  - Bold ↔ Understated
  - Technical ↔ Accessible

  Provide DO and DON'T examples for each spectrum position.

  ## VISUAL IDENTITY DIRECTION

  Establish visual direction (not final design — direction for designers):
  - Color palette: primary + secondary + accent, each with psychology rationale
  - Typography direction: serif/sans-serif, weight, personality match
  - Imagery style: photography vs illustration, mood, subjects
  - Logo direction: wordmark/symbol/combination, style attributes

  Delegate mood board generation to the **creative-studio** sub-agent via `task(subagent_type="creative-studio")` with a brief describing the desired visual direction, colors, and mood.
  Search knowledge graph: `"color psychology branding"`, `"visual identity system"`.

  ## SENSORY IDENTITY (F&B-Specific)

  Define the multi-sensory brand experience:
  - Taste profile alignment (flavor identity)
  - Aroma signature
  - Ambient experience (music, lighting, spatial)
  - Packaging tactile qualities

  ## DISTINCTIVE BRAND ASSETS (Sharp's DBA Strategy)

  Identify and prioritize brand assets for distinctiveness:
  Priority order: color → logo → tagline → font → character/mascot → sound/jingle.
  Each asset must be: unique (not confused with competitors), famous (recognized by target).

  ## BRAND NAMING

  For new_brand scope: run the full 6-step naming process.
  For refresh/repositioning: evaluate whether name changes are needed.
  For full_rebrand: full naming process unless strong equity exists.

  Use `search_web` for domain and social handle availability checks during the naming process.
  Read `references/naming_process.md` for the detailed 6-step procedure with Keller's 6 criteria evaluation.

  ## IDENTITY TRANSITION (Rebrand Only)

  **Skip for new_brand scope.**

  Build the Preserve-Discard Matrix: for each brand element (name, logo, colors, voice, etc.), decide: preserve / evolve / replace / remove — with rationale and equity assessment.

  Read `references/identity_transition.md` for the full matrix structure and visual bridge strategy.

  ## PHASE 3 QUALITY GATE

  Verify before advancing: personality defined, voice guidelines complete, visual direction documented with mood boards, DBA strategy set, naming resolved, identity transition planned (rebrand).

  ## OUTPUT FORMAT

  Structure Phase 2 output as: competitive_frame (category, competitive_set, category_associations), positioning (points_of_parity, points_of_difference, positioning_statement, positioning_rationale), value_architecture (attributes, functional_benefits, emotional_benefits, customer_outcomes, reasons_to_believe), brand_essence (core_idea, brand_promise, brand_mantra), strategic_alignment (problem_addressed, insight_leveraged, differentiation_logic), product_brand_alignment, positioning_stress_test.
  Structure Phase 3 output as: brand_personality, brand_voice, visual_identity, distinctive_brand_assets, sensory_identity, brand_naming, identity_transition (rebrand only).
  Read `references/output_templates.md` for detailed field structures matching Phase2Output and Phase3Output schemas.
  ```

- **Reference Files**:
  - `references/naming_process.md` (~80-120 lines): 6-step naming procedure (choose approach → generate 10-15 candidates → linguistic screening VN+EN → availability checks domain/social/trademark → evaluate top 5 against Keller's 6 criteria → present top 3 with rationale). Includes criteria descriptions and scoring guidance.
  - `references/identity_transition.md` (~60-80 lines): Preserve-Discard Matrix structure (element × action with rationale/equity_value), visual bridge strategy, DBA continuity plan.
  - `references/output_templates.md` (~60-80 lines): Phase2Output + Phase3Output field structures matching Pydantic schemas.

- **Acceptance Criteria**:
  - [ ] YAML frontmatter has ONLY `name` + `description` (no `metadata`, no `allowed-tools`)
  - [ ] `description` ≤ 1024 chars, includes trigger contexts ("Use when...")
  - [ ] SKILL.md body ≤ 500 lines
  - [ ] Body uses imperative form, full-width lines
  - [ ] Phase 2: 8-step positioning process with F&B product-brand alignment and stress test
  - [ ] Phase 3: personality, voice, visual, DBA, sensory, naming, identity transition
  - [ ] Naming process delegated to reference file (detailed 6 steps + Keller's criteria)
  - [ ] Identity transition delegated to reference file (Preserve-Discard matrix)
  - [ ] Output templates delegated to reference file
  - [ ] Stress test failure clearly links to proactive loop triggers in orchestrator

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Positioning Statement Generation
- **Purpose**: Verify positioning statement follows template
- **Steps**:
  1. Provide Phase 1 output (competitors, audience, insights)
  2. Run Phase 2 process
  3. Verify statement: "For [target] who [need], [brand] is [frame] that [POD] because [RTB]"
- **Expected Result**: Complete, specific positioning statement
- **Status**: ⏳ Pending

### Test Case 2: Stress Test Failure → Proactive Loop
- **Purpose**: Verify stress test failure triggers loop back
- **Steps**:
  1. Set positioning that fails deliverability (product can't support claim)
  2. Run stress test → should fail
  3. Agent should propose revisiting Phase 0 or Phase 1
- **Expected Result**: StressTestResult.passed = False, loop trigger fired
- **Status**: ⏳ Pending

### Test Case 3: Brand Naming — New Brand
- **Purpose**: Verify full naming process for new brand
- **Steps**:
  1. Run naming with scope=NEW_BRAND
  2. Verify 10+ candidates generated
  3. Verify top 5 scored against Keller's 6 criteria
  4. Verify top 3 presented with rationale
- **Expected Result**: NamingProcess with candidates, scores, selection
- **Status**: ⏳ Pending

### Test Case 4: Refresh — Naming Skipped
- **Purpose**: Verify naming skipped for refresh scope
- **Steps**:
  1. Run with scope=REFRESH, existing name preserved
  2. Verify naming process skipped
- **Expected Result**: NamingProcess.skipped = True
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation.

### What Was Implemented

**Components Completed**:
- [ ] [Component 1]: Positioning Framework
- [ ] [Component 2]: Identity Expression Framework
- [ ] [Component 3]: Naming Process & Preserve-Discard
- [ ] [Component 4]: Output Schemas
- [ ] [Component 5]: Skill Markdown File

**Files Created/Modified**:
```
src/shared/src/shared/agent_skills/brand_strategy/
└── brand-positioning-identity/
    ├── SKILL.md                           # Core positioning + identity (~350-450 lines)
    └── references/
        ├── naming_process.md              # 6-step naming + Keller's criteria
        ├── identity_transition.md         # Preserve-Discard matrix + visual bridge
        └── output_templates.md            # Phase2Output + Phase3Output fields

src/core/src/core/brand_strategy/
├── analysis/
│   ├── positioning.py                     # POPs, PODs, stress test, value ladder
│   └── naming.py                          # Naming process, Keller's criteria
└── schemas/
    ├── phase_2.py                         # Phase 2 output schema
    └── phase_3.py                         # Phase 3 output schema
```

------------------------------------------------------------------------
