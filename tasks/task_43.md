# Task 43: Market Research Skill (Phase 1)

## 📌 Metadata

- **Epic**: Brand Strategy — Skills
- **Priority**: Critical (P1 — Phase 1 deep-dive)
- **Estimated Effort**: 1.5 weeks
- **Team**: Backend
- **Related Tasks**: Task 42 (Orchestrator loads this skill), Task 36-37 (search_places, deep_research), Task 40 (analyze_reviews, get_search_autocomplete)
- **Blocking**: Task 46 (E2E Integration)
- **Blocked by**: Task 35 (Skills Setup), Task 42 (Orchestrator — defines phase context)

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals)
- [x] 🛠 [Solution Design](#🛠-solution-design)
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan)
- [x] 📋 [Implementation Detail](#📋-implementation-detail)
    - [x] ✅ [Component 1: Research Methodology Procedures](#component-1-research-methodology-procedures)
    - [x] ✅ [Component 2: Strategic Synthesis Framework](#component-2-strategic-synthesis-framework)
    - [x] ✅ [Component 3: Output Schema & Templates](#component-3-output-schema--templates)
    - [x] ✅ [Component 4: Skill Markdown File](#component-4-skill-markdown-file)
- [ ] 🧪 [Test Cases](#🧪-test-cases)
- [ ] 📝 [Task Summary](#📝-task-summary)

## 🔗 Reference Documentation

- **Blueprint Reference**: `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — Section 4.3 (Skill 2), Section 3.3 (Phase 1)
- **Research Steps**: Blueprint Section 4.3 defines 8 research steps
- **Phase 1 Outputs**: Blueprint Section 3.3 `phase_1_output` schema
- **KG Queries**: Blueprint Section 7.2 (Phase 1 row)

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Phase 1 (Market Intelligence & Research) là phase data-heavy nhất — cần systematic approach
- Blueprint Section 4.3 định nghĩa 8 research steps:
  1. Industry Scan
  2. Local Competitor Mapping
  3. Competitor Brand Analysis
  4. Target Audience Research
  5. Customer Insight Mining
  6. Trend & Opportunity Scanning
  7. [Rebrand] Current Brand Position Research
  8. Strategic Synthesis (CRITICAL — bridges Research → Strategy)
- Step 8 (Strategic Synthesis) là CRITICAL addition từ gap analysis — transforms raw data thành actionable strategy inputs
- Skill available via progressive disclosure; orchestrator instructs agent to read this SKILL.md when entering Phase 1

### Mục tiêu

1. Skill file chứa detailed research procedures cho agent theo dõi step-by-step
2. Strategic Synthesis framework: SWOT, Perceptual Map, Strategic Sweet Spot, Insight Prioritization
3. Output templates matching `phase_1_output` schema
4. KG integration points specified per research step

### Success Metrics / Acceptance Criteria

- **Completeness**: Agent follow 8 research steps systematically
- **Synthesis Quality**: SWOT + Perceptual Map + Sweet Spot analysis produced
- **Tool Usage**: Agent correctly uses search_places, deep_research, analyze_reviews, and delegates social media tasks to social-media-analyst sub-agent via `task(subagent_type="social-media-analyst")`
- **Output**: phase_1_output structured data matches schema

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Skill Markdown + Output Schema**: Skill markdown file chứa step-by-step research procedures. Pydantic output schema validates phase outputs.

### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Skill markdown | `src/shared/src/shared/agent_skills/brand_strategy/market-research/SKILL.md` | Research procedures |
| Output schema | `src/core/src/core/brand_strategy/schemas/phase_1.py` | phase_1_output validation |
| Synthesis helpers | `src/core/src/core/brand_strategy/analysis/synthesis.py` | SWOT, perceptual map support |

------------------------------------------------------------------------

## 📋 Implementation Detail

### Component 1: Research Methodology Procedures

#### Requirement 1 - 8 Research Steps with Tool Mappings
- **Requirement**: Detail each research step with which tools to use and what to look for
- **Implementation**: Embedded in skill markdown (Component 4)
- **Step Details** (from Blueprint Section 4.3):

  **Step 1: Industry Scan**
  - Tools: `deep_research`, `search_web`
  - Searches: "[city] F&B market trends [year]", "[category] industry growth Vietnam"
  - Output: Market size, growth rate, key trends, regulatory changes
  - KG: `"market segmentation criteria methods"`

  **Step 2: Local Competitor Mapping**
  - Tools: `search_places`
  - Action: Find competitors within 2-5km radius
  - Data per competitor: name, address, rating, review count, price level, hours
  - KG: None

  **Step 3: Competitor Brand Analysis**
  - Tools: `crawl_web`, `analyze_reviews`; delegate social media analysis to **social-media-analyst** sub-agent via `task(subagent_type="social-media-analyst")`
  - For top 5: visual identity, messaging, pricing, review sentiment, social strategy
  - KG: `"competitive analysis framework"`

  **Step 4: Target Audience Research**
  - Tools: `deep_research`; delegate social media audience research to **social-media-analyst** sub-agent
  - Segmentation: demographic, psychographic, behavioral, benefit
  - KG: `"psychographic segmentation"`, `"benefit segmentation"`

  **Step 5: Customer Insight Mining**
  - Tools: `analyze_reviews`; delegate social media conversations to **social-media-analyst** sub-agent
  - Focus: negative reviews (unmet needs), social conversations, trending topics
  - Insight formula: "We noticed [observation] because [motivation] which means [implication]"
  - KG: `"customer insight development"`

  **Step 6: Trend & Opportunity Scanning**
  - Tools: `deep_research`, `get_search_autocomplete`
  - Topics: sustainability, technology, health/wellness F&B trends
  - KG: None

  **Step 7: [Rebrand] Current Brand Position** (skip for new_brand)
  - Tools: `analyze_reviews`, `search_web`; delegate social media analysis to **social-media-analyst** sub-agent
  - Analysis: current perception, actual vs intended positioning, competitive position
  - KG: `"brand audit brand inventory"`

  **Step 8: Strategic Synthesis** (CRITICAL bridge)
  - SWOT: Consolidate all research into S/W/O/T
  - Perceptual Map: Plot competitors on 2 meaningful axes → find white space
  - Strategic Sweet Spot: Opportunity (market) meets Capability (business)
  - Insight Prioritization: Rank by strategic value × actionability × evidence strength
  - KG: `"SWOT analysis"`, `"competitive analysis framework"`

- **Acceptance Criteria**:
  - [ ] All 8 steps documented with tool mappings
  - [ ] Rebrand-specific Step 7 conditional
  - [ ] Insight formula provided
  - [ ] KG queries specified per step

### Component 2: Strategic Synthesis Framework

#### Requirement 1 - SWOT + Perceptual Map + Sweet Spot Analysis
- **Requirement**: Python support for strategic synthesis artifacts
- **Implementation**:
  - `src/core/src/core/brand_strategy/analysis/synthesis.py`
  ```python
  from pydantic import BaseModel, Field


  class SWOTAnalysis(BaseModel):
      """SWOT analysis from Phase 1 research."""
      strengths: list[str] = Field(default_factory=list)
      weaknesses: list[str] = Field(default_factory=list)
      opportunities: list[str] = Field(default_factory=list)
      threats: list[str] = Field(default_factory=list)


  class PerceptualMapAxis(BaseModel):
      """An axis on the competitive perceptual map."""
      label: str  # e.g., "Price Level"
      low_label: str  # e.g., "Budget"
      high_label: str  # e.g., "Premium"


  class CompetitorPosition(BaseModel):
      """A competitor's position on the perceptual map."""
      name: str
      x_score: float  # Position on x-axis (0-10)
      y_score: float  # Position on y-axis (0-10)
      notes: str = ""


  class PerceptualMap(BaseModel):
      """Competitive perceptual map."""
      x_axis: PerceptualMapAxis
      y_axis: PerceptualMapAxis
      competitors: list[CompetitorPosition] = Field(default_factory=list)
      white_space: str = ""  # Description of unoccupied positions
      recommended_position: str = ""  # Where our brand should target


  class CustomerInsight(BaseModel):
      """A prioritized customer insight (for Strategic Synthesis scoring)."""
      observation: str
      motivation: str
      implication: str
      strategic_value: int = Field(default=1, ge=1, le=5)  # 1-5
      actionability: int = Field(default=1, ge=1, le=5)  # 1-5
      evidence_strength: int = Field(default=1, ge=1, le=5)  # 1-5
      priority_score: float = 0.0  # Computed by prioritize_insights()


  class StrategicSynthesis(BaseModel):
      """
      Complete strategic synthesis bridging Research → Strategy.

      Combines SWOT, Perceptual Map, Strategic Sweet Spot,
      and Insight Prioritization into actionable strategy inputs.
      """
      swot: SWOTAnalysis = Field(default_factory=SWOTAnalysis)
      perceptual_map: PerceptualMap | None = None
      strategic_sweet_spot: str = ""  # Where opportunity meets capability
      prioritized_insights: list[CustomerInsight] = Field(
          default_factory=list
      )
      key_strategic_questions: list[str] = Field(default_factory=list)

      def prioritize_insights(self) -> None:
          """Calculate priority scores and sort insights."""
          for insight in self.prioritized_insights:
              insight.priority_score = (
                  insight.strategic_value
                  * insight.actionability
                  * insight.evidence_strength
              ) / 125  # Normalize to 0-1
          self.prioritized_insights.sort(
              key=lambda i: i.priority_score, reverse=True
          )
  ```
- **Acceptance Criteria**:
  - [ ] SWOT model captures all 4 categories
  - [ ] Perceptual Map supports 2 custom axes + N competitors
  - [ ] Insight prioritization computes composite score
  - [ ] White space identification for perceptual map

### Component 3: Output Schema & Templates

#### Requirement 1 - Phase 1 Output Pydantic Schema
- **Requirement**: Validate phase 1 outputs match blueprint schema (Section 3.3)
- **Implementation**:
  - `src/core/src/core/brand_strategy/schemas/phase_1.py`
  ```python
  from pydantic import BaseModel, Field

  from core.brand_strategy.analysis.synthesis import StrategicSynthesis


  class CompetitorProfile(BaseModel):
      """Individual competitor profile matching blueprint schema."""
      name: str
      location: str = ""
      category: str = ""
      rating: float | None = None
      review_count: int | None = None
      price_range: str = ""  # Blueprint: price_range (not price_level)
      positioning: str = ""
      strengths: list[str] = Field(default_factory=list)
      weaknesses: list[str] = Field(default_factory=list)
      brand_perception: str = ""  # Blueprint: brand_perception
      social_presence: str = ""  # Blueprint: str (summary), not dict
      key_differentiator: str = ""  # Blueprint: key_differentiator


  class CompetitiveLandscape(BaseModel):
      """Competitive landscape matching blueprint Section 3.3 schema."""
      direct_competitors: list[CompetitorProfile] = Field(
          default_factory=list
      )  # 3-5 competitors
      indirect_competitors: list[CompetitorProfile] = Field(
          default_factory=list
      )  # 2-3 competitors
      competitive_gaps: list[str] = Field(default_factory=list)


  class AudienceSegment(BaseModel):
      """Target audience segment matching blueprint schema."""
      name: str
      demographics: str = ""  # Blueprint: demographics (plural)
      psychographics: str = ""  # Blueprint: psychographics (plural)
      behaviors: str = ""  # Blueprint: behaviors
      jobs_to_be_done: list[str] = Field(default_factory=list)  # Blueprint
      pain_points: list[str] = Field(default_factory=list)  # Blueprint
      desires: list[str] = Field(default_factory=list)  # Blueprint
      size_estimate: str = ""


  class TargetAudience(BaseModel):
      """Target audience with primary/secondary structure per blueprint."""
      primary_segment: AudienceSegment | None = None
      secondary_segment: AudienceSegment | None = None


  class MarketOverview(BaseModel):
      """Market overview matching blueprint Section 3.3 sub-fields."""
      industry_trends: list[str] = Field(default_factory=list)
      category_dynamics: str = ""
      market_size_estimate: str = ""
      growth_direction: str = ""  # growing, stable, declining


  class Phase1CustomerInsight(BaseModel):
      """Customer insight matching blueprint schema."""
      insight: str = ""
      evidence: str = ""
      implication: str = ""


  class Opportunities(BaseModel):
      """Market opportunities matching blueprint schema."""
      market_gaps: list[str] = Field(default_factory=list)
      unmet_needs: list[str] = Field(default_factory=list)
      trend_opportunities: list[str] = Field(default_factory=list)


  class CurrentBrandPosition(BaseModel):
      """Current brand position (rebrand only) per blueprint."""
      actual_perception: str = ""
      position_vs_competitors: str = ""
      perception_gaps: list[str] = Field(default_factory=list)


  class Phase1Output(BaseModel):
      """
      Complete Phase 1 output matching Blueprint Section 3.3 schema.

      Field names match blueprint YAML keys exactly for consistency.
      Uses typed models instead of bare dicts for Pydantic validation.
      """
      market_overview: MarketOverview = Field(
          default_factory=MarketOverview
      )
      competitive_landscape: CompetitiveLandscape = Field(
          default_factory=CompetitiveLandscape
      )  # Blueprint: competitive_landscape (NOT competitor_analysis)
      target_audience: TargetAudience = Field(
          default_factory=TargetAudience
      )
      customer_insights: list[Phase1CustomerInsight] = Field(
          default_factory=list
      )
      opportunities: Opportunities = Field(
          default_factory=Opportunities
      )  # Blueprint: opportunities (NOT trend_analysis)
      strategic_synthesis: StrategicSynthesis = Field(
          default_factory=StrategicSynthesis
      )
      current_brand_position: CurrentBrandPosition | None = None  # Rebrand only
  ```
- **Acceptance Criteria**:
  - [ ] Schema matches blueprint phase_1_output exactly
  - [ ] Validates structured data from agent
  - [ ] Optional fields for rebrand-only data

### Component 4: Skill Markdown File

#### Requirement 1 - Market Research Skill Markdown
- **Requirement**: The SKILL.md file for Phase 1, discovered by DeepAgents SkillsMiddleware (progressive disclosure). Must follow skill-creator best practices: only `name` + `description` in frontmatter, body <500 lines, imperative form, full-width lines.
- **Implementation**:
  - `src/shared/src/shared/agent_skills/brand_strategy/market-research/SKILL.md`

- **Directory Structure**:
  ```
  market-research/
  ├── SKILL.md                             # Core 8-step methodology (~300-400 lines)
  └── references/
      └── output_templates.md              # Phase1Output structured templates
  ```

- **Frontmatter** (only `name` + `description`):
  ```yaml
  ---
  name: market-research
  description: >-
    Systematic 8-step F&B market research methodology for Phase 1.
    Covers industry scan, local competitor mapping, competitor brand analysis,
    target audience research, customer insight mining, trend scanning,
    current brand position research (rebrand only), and strategic synthesis
    (SWOT, perceptual map, strategic sweet spot, insight prioritization).
    Use when the orchestrator enters Phase 1 or when the user asks
    to research a market, analyze competitors, or gather customer insights.
  ---
  ```

- **SKILL.md Body Structure** (~300-400 lines, imperative form, full-width lines):
  ```markdown
  # Market Research — Phase 1

  ## ROLE & OBJECTIVE

  Conduct systematic market intelligence gathering for F&B brand strategy.
  Follow the 8-step methodology below. Each step builds on previous findings — execute sequentially.
  Accumulate all findings for the Strategic Synthesis in Step 8, which bridges Research → Strategy.

  **CORE PRINCIPLE**: BREADTH FIRST, DEPTH WHERE IT MATTERS. Scan wide, then dive deep on signals that affect positioning.

  ## STEP 1: INDUSTRY SCAN

  Establish the macro landscape for the target F&B category and location.

  Use `deep_research` and `search_web` with queries like:
  - "[city] [category] market trends [year]"
  - "[category] industry growth Vietnam"

  Capture: market size, growth rate, key trends, regulatory changes, seasonal patterns.
  Search knowledge graph: `"market segmentation criteria methods"`.

  ## STEP 2: LOCAL COMPETITOR MAPPING

  Use `search_places` to find competitors within 2-5km radius of the target location.

  Collect per competitor: name, address, rating, review count, price level, operating hours.
  Organize into a competitor table. Flag the top 5 by review volume and rating — these are the deep-dive targets for Step 3.

  ## STEP 3: COMPETITOR BRAND ANALYSIS

  For the top 5 competitors from Step 2, conduct deep brand analysis.

  Delegate social media analysis to the **social-media-analyst** sub-agent via `task(subagent_type="social-media-analyst")`. Use `crawl_web` for website/menu, `analyze_reviews` for sentiment.

  Evaluate per competitor: visual identity, core messaging, pricing strategy, review sentiment themes, social engagement rate, content strategy.
  Search knowledge graph: `"competitive analysis framework"`.

  ## STEP 4: TARGET AUDIENCE RESEARCH

  Define audience segments using 4 lenses: demographic, psychographic, behavioral, benefit.

  Use `deep_research` for macro audience data. Delegate social media lifestyle research to the **social-media-analyst** sub-agent.

  Identify primary segment (highest value) and secondary segments.
  Search knowledge graph: `"psychographic segmentation"`, `"benefit segmentation"`.

  ## STEP 5: CUSTOMER INSIGHT MINING

  Mine real customer voices for unmet needs and emotional drivers.

  Use `analyze_reviews` on competitors (especially negative reviews = unmet needs).
  Delegate social media conversation mining to the **social-media-analyst** sub-agent.

  Frame each insight using the formula:
  > "We noticed [observation] because [motivation] which means [implication]"

  Search knowledge graph: `"customer insight development"`.

  ## STEP 6: TREND & OPPORTUNITY SCANNING

  Scan for emerging trends that create strategic opportunities.

  Use `deep_research` for macro trends (sustainability, technology, health/wellness in F&B).
  Use `get_search_autocomplete` to discover what people are searching for in the category.

  Classify each trend: rising / peaking / declining. Flag trends with positioning potential.

  ## STEP 7: CURRENT BRAND POSITION RESEARCH (Rebrand Only)

  **Skip this step for new_brand scope.**

  For existing brands: assess current perception vs intended positioning.

  Use `analyze_reviews` on the brand's own reviews, `search_web` for press/media coverage. Delegate social media brand mention analysis to the **social-media-analyst** sub-agent.

  Document: current brand perception, perception-reality gap, competitive position, equity assets worth preserving.
  Search knowledge graph: `"brand audit brand inventory"`.

  ## STEP 8: STRATEGIC SYNTHESIS (CRITICAL)

  Transform raw research into actionable strategy inputs. This step bridges Phase 1 → Phase 2.

  ### SWOT Analysis
  Consolidate all research into Strengths / Weaknesses / Opportunities / Threats.
  Each item must cite which research step produced the evidence.

  ### Perceptual Map
  Plot top competitors on 2 meaningful axes (choose axes based on what differentiates the market — e.g., Price Level vs Experience Quality, Traditional vs Modern).
  Identify white space = unoccupied positions with audience demand.

  ### Strategic Sweet Spot
  Where market opportunity meets business capability. Cross-reference SWOT opportunities with the business constraints from Phase 0.

  ### Insight Prioritization
  Rank all insights by: strategic value (1-5) × actionability (1-5) × evidence strength (1-5).
  Present top 5 prioritized insights as the foundation for Phase 2 positioning.

  Search knowledge graph: `"SWOT analysis"`, `"competitive analysis framework"`.

  ## OUTPUT FORMAT

  Structure Phase 1 output as: market_overview, competitive_landscape (direct_competitors, indirect_competitors, competitive_gaps), target_audience (primary_segment, secondary_segment), customer_insights (list of insight/evidence/implication), opportunities (market_gaps, unmet_needs, trend_opportunities), strategic_synthesis (swot, perceptual_map, strategic_sweet_spot, prioritized_insights), current_brand_position (rebrand only).
  Read `references/output_templates.md` for the detailed field structure matching Phase1Output schema.
  ```

- **Acceptance Criteria**:
  - [ ] YAML frontmatter has ONLY `name` + `description` (no `metadata`, no `allowed-tools`)
  - [ ] `description` ≤ 1024 chars, includes trigger contexts ("Use when...")
  - [ ] SKILL.md body ≤ 500 lines
  - [ ] Body uses imperative form, full-width lines
  - [ ] All 8 research steps detailed with tool mappings and KG queries
  - [ ] Step 7 clearly marked as rebrand-only (skip for new_brand)
  - [ ] Step 8 Strategic Synthesis covers SWOT, perceptual map, sweet spot, insight prioritization
  - [ ] Output template delegated to reference file

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Skill Loading
- **Purpose**: Verify skill is discovered by SkillsMiddleware and content is readable
- **Steps**:
  1. Use `_list_skills()` to verify market-research appears in discovery
  2. Read `market-research/SKILL.md` via FilesystemBackend
  3. Verify frontmatter parsed correctly (name, description)
  4. Verify body content accessible
- **Expected Result**: Skill object with correct metadata and content
- **Status**: ⏳ Pending

### Test Case 2: Research Steps Coverage
- **Purpose**: Verify agent follows all 8 steps
- **Steps**:
  1. Load skill into agent context
  2. Run Phase 1 for a mock "specialty café in District 3"
  3. Verify all 8 steps attempted
- **Expected Result**: Each step produces data, synthesis completed
- **Status**: ⏳ Pending

### Test Case 3: Phase 1 Output Validation
- **Purpose**: Verify output matches schema
- **Steps**:
  1. Generate mock Phase 1 output
  2. Validate against Phase1Output schema
  3. Check all required fields present
- **Expected Result**: Schema validation passes
- **Status**: ⏳ Pending

### Test Case 4: Rebrand — Step 7 Conditional
- **Purpose**: Verify Step 7 only runs for rebrand scopes
- **Steps**:
  1. Run Phase 1 with scope=NEW_BRAND → Step 7 skipped
  2. Run Phase 1 with scope=FULL_REBRAND → Step 7 executed
- **Expected Result**: Conditional execution correct
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation.

### What Was Implemented

**Components Completed**:
- [ ] [Component 1]: Research Methodology Procedures
- [ ] [Component 2]: Strategic Synthesis Framework
- [ ] [Component 3]: Output Schema & Templates
- [ ] [Component 4]: Skill Markdown File

**Files Created/Modified**:
```
src/shared/src/shared/agent_skills/brand_strategy/
└── market-research/
    ├── SKILL.md                               # Core 8-step methodology (~300-400 lines)
    └── references/
        └── output_templates.md                # Phase1Output field structure

src/core/src/core/brand_strategy/
├── analysis/
│   ├── __init__.py
│   └── synthesis.py                       # SWOT, Perceptual Map, Insights
└── schemas/
    ├── __init__.py
    └── phase_1.py                         # Phase 1 output schema
```

------------------------------------------------------------------------
