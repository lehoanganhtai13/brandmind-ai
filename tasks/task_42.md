# Task 42: Brand Strategy Orchestrator Skill (v2.0)

## 📌 Metadata

- **Epic**: Brand Strategy — Skills
- **Priority**: Critical (P1 — Master skill)
- **Estimated Effort**: 2 weeks
- **Team**: Backend
- **Related Tasks**: Task 35 (Skills setup — directory structure + SkillsMiddleware config), Tasks 43-45 (sub-skills referenced by this)
- **Blocking**: Tasks 43, 44, 45 (sub-skills depend on orchestrator structure), Task 46 (E2E)
- **Blocked by**: Task 35 (Skills Directory Setup + SkillsMiddleware Config)

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals)
- [x] 🛠 [Solution Design](#🛠-solution-design)
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan)
- [x] 📋 [Implementation Detail](#📋-implementation-detail)
    - [x] ✅ [Component 1: Phase State Machine](#component-1-phase-state-machine)
    - [x] ✅ [Component 2: Quality Gate Engine](#component-2-quality-gate-engine)
    - [x] ✅ [Component 3: Mentor Script Templates](#component-3-mentor-script-templates)
    - [x] ✅ [Component 4: Rebrand Decision Matrix & Workflow Branching](#component-4-rebrand-decision-matrix--workflow-branching)
    - [x] ✅ [Component 5: Proactive Loop Triggers](#component-5-proactive-loop-triggers)
    - [x] ✅ [Component 6: Context Accumulation & Brand Brief](#component-6-context-accumulation--brand-brief)
    - [x] ✅ [Component 7: Skill Markdown File](#component-7-skill-markdown-file)
- [ ] 🧪 [Test Cases](#🧪-test-cases)
- [ ] 📝 [Task Summary](#📝-task-summary)

## 🔗 Reference Documentation

- **Blueprint Reference**: `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — Section 4.2 (Skill 1 definition), Section 3.1-3.7 (All phases), Section 7.3 (Context management)
- **Skills System**: Task 35 — directory structure + DeepAgents SkillsMiddleware (progressive disclosure)
- **Existing Skill Format**: `.agent/skills/` — markdown-based skill files with YAML frontmatter
- **Phase Definitions**: Blueprint Sections 3.1 (Phase 0) through 3.7 (Phase 5)

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Blueprint Section 4.2 định nghĩa `brand-strategy-orchestrator` là **Master Skill** — always loaded khi user bắt đầu brand strategy project
- Skill này control toàn bộ workflow: phase sequencing, quality gates, mentor mode, rebrand branching, proactive loops
- Version 2.0 (upgraded from 1.0 trong blueprint revision) bao gồm:
  - Workflow branching theo scope (new brand vs refresh vs reposition vs full rebrand)
  - Rebrand Decision Matrix (6 signals × 0-2 scoring)
  - Proactive Loop Triggers (agent-initiated rework conditions)
  - Budget-tier awareness
  - Phase 0.5 conditional execution
- Skill format: `SKILL.md` file trong thư mục riêng, loaded bởi DeepAgents built-in `SkillsMiddleware` (Task 35 setup)
- Skill content available on-demand qua progressive disclosure: agent thấy listing trong system prompt, đọc full SKILL.md khi cần

### Mục tiêu

1. Phase State Machine: Quản lý phase transitions, conditional branching
2. Quality Gate Engine: Checklist validation trước khi chuyển phase
3. Mentor Scripts: Template cho agent giải thích/hướng dẫn user mỗi phase
4. Rebrand Decision Matrix: Scoring system để xác định scope
5. Proactive Loop Triggers: Conditions auto-propose revisiting phases
6. Context Accumulation: Brand Brief document grows through phases
7. Skill Markdown File: The actual SKILL.md file discovered by SkillsMiddleware

### Success Metrics / Acceptance Criteria

- **Workflow**: Agent follows phased process correctly cho cả new brand và rebrand
- **Quality**: Không skip quality gate — mỗi phase phải pass checklist
- **Mentoring**: Agent giải thích tự nhiên, educate user about branding concepts
- **Rebrand**: Score matrix correctly identifies scope (refresh/reposition/full rebrand)
- **Proactive**: Agent detects stress test failures → proposes loop back
- **Integration**: Sub-skills (43, 44, 45) available via progressive disclosure; orchestrator skill instructs agent to read relevant sub-skill per phase

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Dual-Layer Architecture**:

**Layer 1 — Skill Markdown File** (`brand-strategy-orchestrator.md`): Loaded vào agent context as system instructions. Contains the complete workflow guide, mentor scripts, quality gates, decision matrices. This is what the agent "reads" and follows.

**Layer 2 — Python Support Module** (`orchestrator.py`): Pydantic models for phase state, quality gate validation, Brand Brief accumulation. Called by the agent through tools or middleware to track workflow state.

```
┌─────────────────────────────────────────────┐
│     Skill Markdown (loaded to context)       │
│  - Phase sequence & branching rules          │
│  - Mentor script templates                   │
│  - Quality gate checklists                   │
│  - Rebrand Decision Matrix                   │
│  - Proactive loop trigger conditions         │
│  - KG integration queries per phase          │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│     Python Support Module                    │
│  - PhaseState model (current phase, scope)   │
│  - QualityGateResult (pass/fail + items)     │
│  - BrandBrief accumulator (phase outputs)    │
│  - RebrandDecisionMatrix (scoring)           │
│  - ProactiveLoopDetector (trigger logic)     │
└─────────────────────────────────────────────┘
```

### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Orchestrator skill file | `src/shared/src/shared/agent_skills/brand_strategy/brand-strategy-orchestrator/SKILL.md` | Skill markdown |
| Phase state models | `src/core/src/core/brand_strategy/orchestrator/phase_state.py` | State management |
| Quality gate engine | `src/core/src/core/brand_strategy/orchestrator/quality_gate.py` | Gate validation |
| Brand brief manager | `src/core/src/core/brand_strategy/orchestrator/brand_brief.py` | Context accumulation |
| Rebrand matrix | `src/core/src/core/brand_strategy/orchestrator/rebrand_matrix.py` | Decision support |
| Proactive loop detector | `src/core/src/core/brand_strategy/orchestrator/proactive_loops.py` | Loop triggers |

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Data Models & State Management**
1. PhaseState Pydantic model (current phase, scope, history)
2. Workflow branching logic per scope type

### **Phase 2: Quality Gates & Rebrand Matrix**
1. Quality gate engine with per-phase checklists
2. Rebrand Decision Matrix scoring system

### **Phase 3: Mentor Scripts & Proactive Loops**
1. Mentor script templates per phase
2. Proactive loop trigger conditions

### **Phase 4: Brand Brief & Skill File Assembly**
1. Brand Brief accumulator
2. Assemble complete skill markdown file

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards**: Enterprise-level Python, comprehensive docstrings, type hints.

### Component 1: Phase State Machine

#### Requirement 1 - Phase State Model & Transitions
- **Requirement**: Track workflow state: current phase, scope, transition history
- **Implementation**:
  - `src/core/src/core/brand_strategy/orchestrator/phase_state.py`
  ```python
  from enum import Enum
  from datetime import datetime

  from pydantic import BaseModel, Field


  class BrandScope(str, Enum):
      """Brand strategy engagement scope."""
      NEW_BRAND = "new_brand"
      REFRESH = "refresh"
      REPOSITIONING = "repositioning"
      FULL_REBRAND = "full_rebrand"


  class Phase(str, Enum):
      """Brand strategy workflow phases."""
      PHASE_0 = "phase_0"           # Business Problem Diagnosis
      PHASE_0_5 = "phase_0_5"       # Brand Equity Audit (rebrand only)
      PHASE_1 = "phase_1"           # Market Intelligence
      PHASE_2 = "phase_2"           # Brand Strategy Core
      PHASE_3 = "phase_3"           # Brand Identity & Expression
      PHASE_4 = "phase_4"           # Communication Framework
      PHASE_5 = "phase_5"           # Brand Strategy Plan
      COMPLETED = "completed"


  class PhaseTransition(BaseModel):
      """Record of a phase transition."""
      from_phase: Phase
      to_phase: Phase
      timestamp: datetime = Field(default_factory=datetime.now)
      gate_passed: bool = True
      notes: str = ""


  class PhaseState(BaseModel):
      """
      Tracks the brand strategy workflow state.

      Manages current phase, scope classification, transition
      history, and phase-specific configuration.

      Phase sequences per scope (from Blueprint Section 4.2):
          NEW_BRAND:
              0 → 1 → 2 → 3 → 4 → 5
          REFRESH:
              0 → 0.5 (light) → 1 (targeted) → SKIP 2 → 3 → 4 → 5
          REPOSITIONING:
              0 → 0.5 (full) → 1 (full) → 2 (pivot) → 3 → 4 → 5
          FULL_REBRAND:
              0 → 0.5 (full) → 1 (full) → 2 (new) → 3 (new) → 4 → 5 (+ transition)
      """
      current_phase: Phase = Phase.PHASE_0
      scope: BrandScope | None = None  # Determined in Phase 0
      budget_tier: str | None = None   # Determined in Phase 0
      transition_history: list[PhaseTransition] = Field(default_factory=list)
      loopback_count: int = 0  # Number of proactive reworks
      session_id: str = ""

      def get_next_phase(self) -> Phase | None:
          """Determine the next phase based on the current scope.

          Looks up the phase sequence for the current scope and returns
          the phase immediately following the current one.

          Returns:
              The next Phase in the sequence, Phase.COMPLETED if at
              the end, or None if scope is unset or phase not found.
          """
          if self.current_phase == Phase.COMPLETED:
              return None
          sequence = self.get_phase_sequence()
          if not sequence:
              return None
          try:
              current_idx = sequence.index(self.current_phase)
          except ValueError:
              return None
          next_idx = current_idx + 1
          if next_idx >= len(sequence):
              return Phase.COMPLETED
          return sequence[next_idx]

      def get_phase_sequence(self) -> list[Phase]:
          """Get the ordered phase sequence for the current scope.

          Each scope type has a different phase sequence (e.g., REFRESH
          skips Phase 2, NEW_BRAND skips Phase 0.5).

          Returns:
              Ordered list of Phase enums for the current scope,
              or an empty list if scope is not yet set.
          """
          phase_sequences = {
              BrandScope.NEW_BRAND: [
                  Phase.PHASE_0, Phase.PHASE_1, Phase.PHASE_2,
                  Phase.PHASE_3, Phase.PHASE_4, Phase.PHASE_5,
              ],
              BrandScope.REFRESH: [
                  Phase.PHASE_0, Phase.PHASE_0_5, Phase.PHASE_1,
                  Phase.PHASE_3, Phase.PHASE_4, Phase.PHASE_5,
              ],
              BrandScope.REPOSITIONING: [
                  Phase.PHASE_0, Phase.PHASE_0_5, Phase.PHASE_1,
                  Phase.PHASE_2, Phase.PHASE_3, Phase.PHASE_4,
                  Phase.PHASE_5,
              ],
              BrandScope.FULL_REBRAND: [
                  Phase.PHASE_0, Phase.PHASE_0_5, Phase.PHASE_1,
                  Phase.PHASE_2, Phase.PHASE_3, Phase.PHASE_4,
                  Phase.PHASE_5,
              ],
          }
          return phase_sequences.get(self.scope, [])

      def advance(self, gate_passed: bool = True, notes: str = "") -> Phase:
          """Advance to the next phase in the workflow.

          Records a PhaseTransition in the history and updates
          current_phase. Scope must be set (via Phase 0) before
          calling this method.

          Args:
              gate_passed: Whether the quality gate was satisfied.
              notes: Optional notes about the transition.

          Returns:
              The new current Phase after advancing.

          Raises:
              ValueError: If scope is not set or workflow is complete.
          """
          if self.scope is None:
              raise ValueError("Cannot advance: scope not set yet (complete Phase 0 first)")
          next_phase = self.get_next_phase()
          if next_phase is None:
              raise ValueError(f"Cannot advance from {self.current_phase.value}: workflow complete")
          transition = PhaseTransition(
              from_phase=self.current_phase,
              to_phase=next_phase,
              gate_passed=gate_passed,
              notes=notes,
          )
          self.transition_history.append(transition)
          self.current_phase = next_phase
          return self.current_phase

      def loopback(self, target_phase: Phase, reason: str) -> Phase:
          """Loop back to a previous phase for proactive rework.

          Records a LOOPBACK transition and increments the loopback
          counter. The target phase must exist in the current scope's
          sequence and must precede the current phase.

          Args:
              target_phase: The earlier Phase to return to.
              reason: Explanation of why the loopback is needed.

          Returns:
              The new current Phase (same as target_phase).

          Raises:
              ValueError: If target_phase is not in the sequence or
                  is not before the current phase.
          """
          sequence = self.get_phase_sequence()
          if target_phase not in sequence:
              raise ValueError(
                  f"Cannot loop back to {target_phase.value}: not in current scope sequence"
              )
          current_idx = sequence.index(self.current_phase)
          target_idx = sequence.index(target_phase)
          if target_idx >= current_idx:
              raise ValueError(
                  f"Cannot loop back to {target_phase.value}: must be before current phase {self.current_phase.value}"
              )
          transition = PhaseTransition(
              from_phase=self.current_phase,
              to_phase=target_phase,
              gate_passed=False,
              notes=f"LOOPBACK: {reason}",
          )
          self.transition_history.append(transition)
          self.current_phase = target_phase
          self.loopback_count += 1
          return self.current_phase

      def is_rebrand(self) -> bool:
          """Check if the current scope involves rebranding.

          Returns:
              True if scope is REFRESH, REPOSITIONING, or FULL_REBRAND.
          """
          return self.scope in {
              BrandScope.REFRESH,
              BrandScope.REPOSITIONING,
              BrandScope.FULL_REBRAND,
          }
  ```
- **Acceptance Criteria**:
  - [ ] Correct phase sequence for all 4 scopes
  - [ ] Phase 0.5 conditional for rebrand scopes only
  - [ ] Phase 2 skipped for refresh scope
  - [ ] Loopback records history and increments counter

### Component 2: Quality Gate Engine

#### Requirement 1 - Per-Phase Quality Gate Checklists
- **Requirement**: Validate phase exit criteria before advancing (from Blueprint Sections 3.1-3.7)
- **Implementation**:
  - `src/core/src/core/brand_strategy/orchestrator/quality_gate.py`
  ```python
  from pydantic import BaseModel, Field


  class GateItem(BaseModel):
      """A single quality gate criterion."""
      id: str
      description: str
      passed: bool = False
      evidence: str = ""  # How this was satisfied
      required: bool = True
      scope_filter: list[str] | None = None  # None = all scopes


  class QualityGateResult(BaseModel):
      """Result of a quality gate evaluation."""
      phase: str
      passed: bool
      items: list[GateItem] = Field(default_factory=list)
      missing_items: list[str] = Field(default_factory=list)
      pass_rate: float = 0.0


  # Quality gate definitions per phase (from Blueprint)
  QUALITY_GATES: dict[str, list[GateItem]] = {
      "phase_0": [
          GateItem(
              id="p0_problem",
              description="Clear problem statement articulated",
          ),
          GateItem(
              id="p0_scope",
              description="Scope classified (new_brand/refresh/reposition/full_rebrand)",
          ),
          GateItem(
              id="p0_category",
              description="F&B category and concept understood",
          ),
          GateItem(
              id="p0_budget",
              description="Budget tier identified for implementation planning",
          ),
          GateItem(
              id="p0_user_confirm",
              description="User confirms understanding and agrees to proceed",
          ),
      ],
      "phase_0_5": [
          GateItem(
              id="p05_inventory",
              description="Brand Inventory completed (visual, verbal, experiential audit)",
              scope_filter=["refresh", "repositioning", "full_rebrand"],
          ),
          GateItem(
              id="p05_perception",
              description="Current brand perception assessed (reviews, social, customer voice)",
              scope_filter=["refresh", "repositioning", "full_rebrand"],
          ),
          GateItem(
              id="p05_equity",
              description="Brand equity sources identified (what to keep, evolve, discard)",
              scope_filter=["refresh", "repositioning", "full_rebrand"],
          ),
          GateItem(
              id="p05_preserve_discard",
              description="Preserve-Discard Matrix completed with user alignment",
              scope_filter=["refresh", "repositioning", "full_rebrand"],
          ),
      ],
      "phase_1": [
          GateItem(
              id="p1_competitors",
              description="At least 3 direct competitors profiled",
          ),
          GateItem(
              id="p1_audience",
              description="Target audience defined with psychographic + behavioral data",
          ),
          GateItem(
              id="p1_insights",
              description="At least 3 actionable customer insights identified",
          ),
          GateItem(
              id="p1_swot",
              description="SWOT analysis completed with market data support",
          ),
          GateItem(
              id="p1_perceptual_map",
              description="Competitive perceptual map created with white space identified",
          ),
          GateItem(
              id="p1_synthesis",
              description="Strategic synthesis completed (sweet spot + prioritized insights)",
          ),
      ],
      "phase_2": [
          GateItem(
              id="p2_positioning",
              description="Positioning statement complete (target, frame, POD, RTB)",
          ),
          GateItem(
              id="p2_pops_pods",
              description="Points of Parity and Difference defined",
          ),
          GateItem(
              id="p2_value_ladder",
              description="Value ladder built (attributes → functional → emotional → outcome)",
          ),
          GateItem(
              id="p2_essence",
              description="Brand essence / mantra articulated",
          ),
          GateItem(
              id="p2_product_alignment",
              description="Product-brand alignment checked (menu, pricing, service fit)",
          ),
          GateItem(
              id="p2_stress_test",
              description="Positioning stress test passed (5 criteria)",
          ),
      ],
      "phase_3": [
          GateItem(
              id="p3_personality",
              description="Brand personality defined (archetype + traits with do/don't)",
          ),
          GateItem(
              id="p3_voice",
              description="Brand voice guidelines with do/don't examples",
          ),
          GateItem(
              id="p3_naming",
              description="Brand name finalized (new: full process; rebrand: keep/rename justified)",
          ),
          GateItem(
              id="p3_visual",
              description="Visual identity direction documented (colors, typography, imagery)",
          ),
          GateItem(
              id="p3_mood_boards",
              description="At least 2-3 mood board/concept images generated",
          ),
          GateItem(
              id="p3_dba",
              description="Distinctive Brand Assets strategy planned",
          ),
          GateItem(
              id="p3_transition",
              description="[Rebrand only] Identity transition plan completed",
              scope_filter=["refresh", "repositioning", "full_rebrand"],
          ),
      ],
      "phase_4": [
          GateItem(
              id="p4_value_prop",
              description="Core value proposition is clear, compelling, differentiated",
          ),
          GateItem(
              id="p4_messaging",
              description="Messaging hierarchy (primary, secondary, supporting)",
          ),
          GateItem(
              id="p4_cialdini",
              description="At least 2 Cialdini principles applied to messaging",
          ),
          GateItem(
              id="p4_aida",
              description="AIDA flow mapped with specific messages per stage",
          ),
          GateItem(
              id="p4_channels",
              description="Channel strategy defined with content types and frequencies",
          ),
          GateItem(
              id="p4_pillars",
              description="3-5 content pillars established",
          ),
      ],
      "phase_5": [
          GateItem(
              id="p5_document",
              description="Complete brand strategy document generated (PDF/DOCX)",
          ),
          GateItem(
              id="p5_brand_key",
              description="Brand Key one-pager included",
          ),
          GateItem(
              id="p5_kpis",
              description="At least 5 KPIs defined with baselines and targets",
          ),
          GateItem(
              id="p5_roadmap",
              description="Implementation roadmap with 3 time horizons, tied to budget_tier",
          ),
          GateItem(
              id="p5_roadmap_priority",
              description="Each roadmap item categorized Must Do / Nice to Have",
          ),
          GateItem(
              id="p5_measurement",
              description="Measurement plan with review cadence",
          ),
          GateItem(
              id="p5_transition",
              description="[Rebrand only] Transition & change management plan completed",
              scope_filter=["refresh", "repositioning", "full_rebrand"],
          ),
          GateItem(
              id="p5_stakeholder",
              description="[Rebrand only] Stakeholder communication plan defined",
              scope_filter=["refresh", "repositioning", "full_rebrand"],
          ),
      ],
  }


  class QualityGateEngine:
      """
      Validates quality gate criteria for phase transitions.

      Each phase has a set of required criteria. All required
      criteria must pass before the agent can advance to the
      next phase.

      Scope-filtered items are only required for specific scopes
      (e.g., rebrand-only items skipped for new brands).
      """

      def evaluate(
          self,
          phase: str,
          scope: str,
          completed_items: list[str],
      ) -> QualityGateResult:
          """Evaluate the quality gate for a given phase.

          Checks each applicable gate item against the list of completed
          item IDs. All required items must pass for the gate to pass.

          Args:
              phase: Phase identifier (e.g., "phase_0", "phase_1").
              scope: Brand scope string (e.g., "new_brand", "refresh").
              completed_items: List of GateItem IDs that have been satisfied.

          Returns:
              QualityGateResult with pass/fail status, individual item
              results, missing items list, and overall pass rate.
          """
          applicable = self.get_checklist(phase, scope)
          if not applicable:
              return QualityGateResult(phase=phase, passed=True, pass_rate=1.0)

          missing = []
          for item in applicable:
              item.passed = item.id in completed_items
              if not item.passed and item.required:
                  missing.append(item.description)

          total_required = sum(1 for item in applicable if item.required)
          passed_required = total_required - len(missing)
          pass_rate = passed_required / total_required if total_required > 0 else 1.0

          return QualityGateResult(
              phase=phase,
              passed=len(missing) == 0,
              items=applicable,
              missing_items=missing,
              pass_rate=pass_rate,
          )

      def get_checklist(
          self, phase: str, scope: str
      ) -> list[GateItem]:
          """Get the applicable gate items for a phase and scope.

          Filters out items whose scope_filter does not include the
          current scope. Returns deep copies to avoid mutating globals.

          Args:
              phase: Phase identifier (e.g., "phase_0").
              scope: Brand scope string (e.g., "new_brand").

          Returns:
              List of GateItem copies applicable to this phase/scope.
          """
          gate_items = QUALITY_GATES.get(phase, [])
          applicable = []
          for item in gate_items:
              # Deep copy to avoid mutating the global definitions
              item_copy = item.model_copy()
              if item_copy.scope_filter is None or scope in item_copy.scope_filter:
                  applicable.append(item_copy)
          return applicable

      def format_checklist(
          self,
          phase: str,
          scope: str,
          completed_items: list[str] | None = None,
      ) -> str:
          """Format the quality gate checklist as markdown.

          Produces a human-readable checklist with [x]/[ ] status
          indicators, suitable for injection into the agent context.

          Args:
              phase: Phase identifier (e.g., "phase_1").
              scope: Brand scope string (e.g., "new_brand").
              completed_items: Optional list of completed GateItem IDs.

          Returns:
              Markdown-formatted checklist string.
          """
          items = self.get_checklist(phase, scope)
          if not items:
              return f"No quality gate defined for {phase}."
          completed = set(completed_items or [])
          lines = [f"## Quality Gate: {phase}\n"]
          for item in items:
              status = "[x]" if item.id in completed else "[ ]"
              req_tag = "" if item.required else " _(optional)_"
              lines.append(f"- {status} **{item.id}**: {item.description}{req_tag}")
          return "\n".join(lines)
  ```
- **Acceptance Criteria**:
  - [ ] All phases have correct gate criteria matching blueprint
  - [ ] Scope filtering works (rebrand items skipped for new brand)
  - [ ] Partial pass shows which items are missing
  - [ ] Formatted checklist readable by agent

### Component 3: Mentor Script Templates

#### Requirement 1 - Per-Phase Mentor Scripts
- **Requirement**: Templates guiding how agent explains and educates user at each phase
- **Implementation**:
  - Embedded in the skill markdown file (Component 7)
  - Structure per phase:
  ```python
  MENTOR_SCRIPTS: dict[str, dict] = {
      "phase_0": {
          "opening": (
              "Trước tiên, tôi cần hiểu rõ business context của bạn. "
              "Giai đoạn này gọi là 'Brand Problem Diagnosis' — "
              "giúp xác định đúng vấn đề trước khi giải quyết. "
              "Bạn sẵn sàng trả lời vài câu hỏi chứ?"
          ),
          "key_questions": [
              "Bạn đang kinh doanh F&B gì? (café, restaurant, bar, bakery...)",
              "Đây là thương hiệu mới hay đã có sẵn?",
              "Mục tiêu chính của bạn là gì? (launch mới, rebrand, mở rộng...)",
              "Khu vực bạn muốn tập trung?",
              "Budget range cho brand strategy?",
          ],
          "concepts_to_explain": [
              "5W1H framework — backbone cho phân tích toàn diện",
              "Scope classification — tại sao xác định đúng scope quan trọng",
          ],
          "closing": (
              "Dựa trên thông tin bạn chia sẻ, tôi đã có bức tranh rõ ràng "
              "về business context. Đây là tóm tắt: {summary}. "
              "Bạn confirm và mình sẽ tiến sang nghiên cứu thị trường nhé?"
          ),
      },
      # ... similar for phases 0.5, 1, 2, 3, 4, 5
  }
  ```
- **Acceptance Criteria**:
  - [ ] Each phase has opening, questions, concepts, closing scripts
  - [ ] Vietnamese language natural and professional
  - [ ] Concepts referenced are available in KG

### Component 4: Rebrand Decision Matrix & Workflow Branching

#### Requirement 1 - Rebrand Decision Matrix
- **Requirement**: Scoring system from Blueprint Section 3.1 for diagnosing rebrand need
- **Implementation**:
  - `src/core/src/core/brand_strategy/orchestrator/rebrand_matrix.py`
  ```python
  from pydantic import BaseModel, Field


  class RebrandSignal(BaseModel):
      """A signal in the Rebrand Decision Matrix."""
      name: str
      question: str  # Question to ask user
      score: int = 0  # 0, 1, or 2
      evidence: str = ""


  class RebrandDecisionResult(BaseModel):
      """Result of the Rebrand Decision Matrix scoring."""
      signals: list[RebrandSignal] = Field(default_factory=list)
      total_score: int = 0
      max_score: int = 12  # 6 signals × 2
      recommended_scope: str = ""
      explanation: str = ""


  class RebrandDecisionMatrix:
      """
      Diagnoses rebrand need using 6 diagnostic signals.

      From Blueprint Section 3.1 — Phase 0:
      The agent PROACTIVELY scores when user has existing brand.

      Signals (each scored 0-2):
      1. Brand-Market Misalignment
      2. Competitive Erosion
      3. Audience Disconnect
      4. Internal Fragmentation
      5. Reputation Damage
      6. Strategic Pivot

      Scoring:
      0-3  → REINFORCE (no rebrand needed)
      4-6  → REFRESH (minor updates)
      7-9  → REPOSITION (strategic shift)
      10-12 → FULL REBRAND (start fresh)
      """

      SIGNALS = [
          RebrandSignal(
              name="Brand-Market Misalignment",
              question=(
                  "Brand positioning no longer fits market reality? "
                  "(0=still relevant, 1=somewhat outdated, 2=completely misaligned)"
              ),
          ),
          RebrandSignal(
              name="Competitive Erosion",
              question=(
                  "Competitors have eroded your differentiation? "
                  "(0=still unique, 1=some overlap, 2=no clear difference)"
              ),
          ),
          RebrandSignal(
              name="Audience Disconnect",
              question=(
                  "Target audience has shifted or brand no longer resonates? "
                  "(0=strong connection, 1=weakening, 2=disconnected)"
              ),
          ),
          RebrandSignal(
              name="Internal Fragmentation",
              question=(
                  "Brand identity inconsistent across touchpoints? "
                  "(0=consistent, 1=some gaps, 2=fragmented)"
              ),
          ),
          RebrandSignal(
              name="Reputation Damage",
              question=(
                  "Brand has negative associations? "
                  "(0=positive perception, 1=some concerns, 2=significant damage)"
              ),
          ),
          RebrandSignal(
              name="Strategic Pivot",
              question=(
                  "Business model or strategy changing significantly? "
                  "(0=stable, 1=evolving, 2=major pivot)"
              ),
          ),
      ]

      def score(
          self, signal_scores: dict[str, int]
      ) -> RebrandDecisionResult:
          """Score the rebrand decision matrix.

          Maps each signal name to a 0-2 score, computes the total,
          and returns a scope recommendation based on score ranges.

          Args:
              signal_scores: Dict mapping signal names to integer
                  scores (0=no issue, 1=moderate, 2=severe).

          Returns:
              RebrandDecisionResult with scored signals, total score,
              recommended scope, and explanation.
          """
          scored_signals = []
          for signal in self.SIGNALS:
              signal_copy = signal.model_copy()
              raw_score = signal_scores.get(signal.name, 0)
              signal_copy.score = max(0, min(2, raw_score))
              scored_signals.append(signal_copy)

          total = sum(s.score for s in scored_signals)
          recommended_scope, explanation = self.interpret_score(total)

          return RebrandDecisionResult(
              signals=scored_signals,
              total_score=total,
              recommended_scope=recommended_scope,
              explanation=explanation,
          )

      def get_diagnostic_questions(self) -> list[str]:
          """Get the 6 diagnostic questions for the agent to ask the user.

          Returns:
              List of formatted question strings, each prefixed with
              the signal name in bold.
          """
          return [
              f"**{signal.name}**: {signal.question}"
              for signal in self.SIGNALS
          ]

      def interpret_score(self, total: int) -> tuple[str, str]:
          """Map total score to a scope recommendation with explanation.

          Args:
              total: Sum of all signal scores (0-12 range).

          Returns:
              Tuple of (scope_string, explanation_string) where scope
              is one of: reinforce, refresh, repositioning, full_rebrand.
          """
          if total <= 3:
              return (
                  "reinforce",
                  f"Score {total}/12: Brand fundamentals are sound. "
                  "Focus on strengthening current positioning rather than rebranding.",
              )
          elif total <= 6:
              return (
                  "refresh",
                  f"Score {total}/12: Core brand is viable but expression needs updating. "
                  "Keep strategic foundation, refresh visual identity and messaging.",
              )
          elif total <= 9:
              return (
                  "repositioning",
                  f"Score {total}/12: Significant strategic gaps detected. "
                  "Brand needs repositioning — new target, new POD, or new value proposition.",
              )
          else:
              return (
                  "full_rebrand",
                  f"Score {total}/12: Multiple critical signals indicate comprehensive overhaul needed. "
                  "Recommend starting fresh with full rebrand process.",
              )
  ```
- **Acceptance Criteria**:
  - [ ] 6 signals correctly defined
  - [ ] Score ranges map to correct scopes
  - [ ] Agent can use diagnostic questions naturally
  - [ ] Result includes explanation of each signal

### Component 5: Proactive Loop Triggers

#### Requirement 1 - Trigger Conditions for Phase Rework
- **Requirement**: Implement loop-back conditions from Blueprint Section 4.2 table
- **Implementation**:
  - `src/core/src/core/brand_strategy/orchestrator/proactive_loops.py`
  ```python
  from pydantic import BaseModel


  class LoopTrigger(BaseModel):
      """A condition that triggers revisiting a previous phase."""
      id: str
      detected_at: str  # Phase where detected
      target_phase: str  # Phase to revisit
      condition: str     # What to check
      action: str        # What to do when triggered
      scope_filter: list[str] | None = None


  PROACTIVE_TRIGGERS = [
      LoopTrigger(
          id="stress_deliverability",
          detected_at="phase_2",
          target_phase="phase_0",
          condition="Positioning stress test fails on Deliverability",
          action="Revisit Phase 0 (product reality) or Phase 1 (re-evaluate opportunities)",
      ),
      LoopTrigger(
          id="stress_relevance",
          detected_at="phase_2",
          target_phase="phase_1",
          condition="Positioning stress test fails on Relevance",
          action="Revisit Phase 1 (deeper insight mining)",
      ),
      LoopTrigger(
          id="naming_blocked",
          detected_at="phase_3",
          target_phase="phase_2",
          condition="All promising brand names taken (domain + trademark)",
          action="Adjust positioning angle or naming strategy",
      ),
      LoopTrigger(
          id="visual_conflict",
          detected_at="phase_3",
          target_phase="phase_2",
          condition="Visual identity conflicts with positioning",
          action="Revisit Phase 2 brand essence for clarity",
      ),
      LoopTrigger(
          id="messaging_abstract",
          detected_at="phase_4",
          target_phase="phase_2",
          condition="Messaging reveals positioning is too abstract to communicate",
          action="Revisit Phase 2 for sharper positioning",
      ),
      LoopTrigger(
          id="budget_overrun",
          detected_at="phase_5",
          target_phase="phase_0",
          condition="Budget cannot support implementation plan",
          action="Revisit Phase 0 budget or simplify strategy scope",
      ),
      LoopTrigger(
          id="audit_no_equity",
          detected_at="phase_0_5",
          target_phase="phase_0",
          condition="Audit reveals no salvageable equity",
          action="Recommend upgrading scope to full_rebrand or retirement",
          scope_filter=["refresh", "repositioning", "full_rebrand"],
      ),
      LoopTrigger(
          id="backlash_risk",
          detected_at="phase_5",
          target_phase="phase_3",
          condition="Transition plan reveals high customer backlash risk for proposed changes",
          action="Scale back identity changes, consider phased approach",
          scope_filter=["refresh", "repositioning", "full_rebrand"],
      ),
  ]


  class ProactiveLoopDetector:
      """
      Detects conditions that should trigger revisiting a previous phase.

      When a trigger fires, the agent should:
      1. EXPLAIN what failed and why
      2. PROPOSE specific changes
      3. GET user confirmation
      4. PRESERVE all existing work
      5. After rework, RE-VALIDATE the trigger condition
      """

      # Maps trigger IDs to context keys that indicate the trigger has fired.
      # Each value is either a single key or a tuple of (key, expected_value).
      TRIGGER_CONTEXT_KEYS: dict[str, str] = {
          "stress_deliverability": "stress_test_deliverability_failed",
          "stress_relevance": "stress_test_relevance_failed",
          "naming_blocked": "naming_all_blocked",
          "visual_conflict": "visual_conflicts_with_positioning",
          "messaging_abstract": "messaging_too_abstract",
          "budget_overrun": "budget_exceeds_plan",
          "audit_no_equity": "no_salvageable_equity",
          "backlash_risk": "backlash_risk_high",
      }

      def check_triggers(
          self,
          current_phase: str,
          scope: str,
          context: dict,
      ) -> list[LoopTrigger]:
          """Check if any proactive loop triggers should fire.

          Scans all defined triggers, filtering by current phase and
          scope, then checks the context dict for matching condition keys.

          Args:
              current_phase: Phase where detection occurs (e.g., "phase_2").
              scope: Brand scope string (e.g., "new_brand").
              context: Dict of context flags (e.g., {"stress_test_deliverability_failed": True}).

          Returns:
              List of LoopTrigger objects whose conditions are met.
          """
          fired = []
          for trigger in PROACTIVE_TRIGGERS:
              # Phase must match
              if trigger.detected_at != current_phase:
                  continue
              # Scope filter: None means all scopes
              if trigger.scope_filter is not None and scope not in trigger.scope_filter:
                  continue
              # Check context for the trigger condition
              context_key = self.TRIGGER_CONTEXT_KEYS.get(trigger.id)
              if context_key and context.get(context_key):
                  fired.append(trigger)
          return fired

      # Human-readable phase labels for structured output.
      _PHASE_LABELS: dict[str, str] = {
          "phase_0": "Phase 0 — Business Problem Diagnosis",
          "phase_0_5": "Phase 0.5 — Brand Equity Audit",
          "phase_1": "Phase 1 — Market Intelligence",
          "phase_2": "Phase 2 — Brand Positioning",
          "phase_3": "Phase 3 — Brand Identity",
          "phase_4": "Phase 4 — Communication Framework",
          "phase_5": "Phase 5 — Strategy Plan & Deliverables",
      }

      def format_trigger_explanation(
          self, trigger: LoopTrigger
      ) -> dict:
          """Format a fired trigger into structured data for the agent.

          Returns a dict with the trigger details. The agent (LLM) uses
          this structured data to compose a natural-language explanation
          in the user's language (Vietnamese by default). This avoids
          hardcoding user-facing text in Python and lets the agent adapt
          tone and phrasing to the conversation context.

          Args:
              trigger: The LoopTrigger that fired.

          Returns:
              Dict with keys: trigger_id, condition, recommended_action,
              target_phase (human-readable label), detected_at_phase,
              and a guidance note for the agent.
          """
          target_label = self._PHASE_LABELS.get(
              trigger.target_phase, trigger.target_phase
          )
          detected_label = self._PHASE_LABELS.get(
              trigger.detected_at, trigger.detected_at
          )
          return {
              "trigger_id": trigger.id,
              "condition": trigger.condition,
              "recommended_action": trigger.action,
              "target_phase": target_label,
              "detected_at_phase": detected_label,
              "agent_guidance": (
                  "Explain this trigger to the user in their language. "
                  "Frame it positively — early adjustment prevents waste "
                  "in later phases. Ask for user confirmation before "
                  "looping back."
              ),
          }
  ```
- **Acceptance Criteria**:
  - [ ] All 8 triggers from blueprint defined
  - [ ] Scope filtering works
  - [ ] Trigger format includes actionable explanation

### Component 6: Context Accumulation & Brand Brief

#### Requirement 1 - Brand Brief That Grows Through Phases
- **Requirement**: Accumulated document of phase outputs that serves as input to subsequent phases
- **Implementation**:
  - `src/core/src/core/brand_strategy/orchestrator/brand_brief.py`
  ```python
  from pathlib import Path
  from typing import ClassVar

  from pydantic import BaseModel, Field


  class BrandBrief(BaseModel):
      """
      Accumulated brand strategy document that grows with each phase.

      Each phase adds its outputs to the brief.
      Subsequent phases read previous sections as input.
      The complete brief becomes Phase 5's document assembly input.

      Structure matches the Blueprint's required outputs per phase.
      """
      session_id: str = ""
      brand_name: str = ""
      scope: str = ""
      budget_tier: str = ""

      # Phase outputs (populated as phases complete)
      # Use typed Pydantic models from task 43-45 schemas when available.
      # During accumulation, phase outputs are stored as dicts (from
      # model_dump()) for serialization flexibility. Type validation
      # happens at phase completion via the typed PhaseNOutput models.
      phase_0_output: dict = Field(default_factory=dict)
      phase_0_5_output: dict | None = None  # Rebrand only
      phase_1_output: dict = Field(default_factory=dict)   # → Phase1Output schema (task 43)
      phase_2_output: dict = Field(default_factory=dict)   # → Phase2Output schema (task 44)
      phase_3_output: dict = Field(default_factory=dict)   # → Phase3Output schema (task 44)
      phase_4_output: dict = Field(default_factory=dict)   # → Phase4Output schema (task 45)
      phase_5_output: dict = Field(default_factory=dict)   # → Phase5Output schema (task 45)

      # Generated assets
      generated_images: list[str] = Field(default_factory=list)
      generated_documents: list[str] = Field(default_factory=list)

      # Valid phase output attribute names on this model.
      _PHASE_FIELDS: ClassVar[list[str]] = [
          "phase_0_output", "phase_0_5_output", "phase_1_output",
          "phase_2_output", "phase_3_output", "phase_4_output",
          "phase_5_output",
      ]

      def add_phase_output(
          self, phase: str, output: dict
      ) -> None:
          """Add or update the output for a completed phase.

          Stores the output dict in the corresponding typed field
          (e.g., phase="phase_1" → self.phase_1_output).

          Args:
              phase: Phase identifier (e.g., "phase_0", "phase_1").
              output: Dict of phase output data (typically from
                  PhaseNOutput.model_dump()).

          Raises:
              ValueError: If phase key is not a valid phase identifier.
          """
          field_name = f"{phase}_output"
          if field_name not in self._PHASE_FIELDS:
              raise ValueError(
                  f"Invalid phase key '{phase}'. "
                  f"Expected one of: {[f.replace('_output', '') for f in self._PHASE_FIELDS]}"
              )
          setattr(self, field_name, output)

      def get_context_for_phase(self, phase: str) -> dict:
          """Get accumulated outputs from all prior phases as context.

          Collects all completed phase outputs that precede the given
          phase in the workflow sequence, plus brand metadata.

          Args:
              phase: The target phase that needs prior context
                  (e.g., "phase_2" returns phase_0 and phase_1 outputs).

          Returns:
              Dict with keys: brand_name, scope, budget_tier, and
              prior_phases (dict mapping phase IDs to their outputs).
          """
          # Ordered list of phases; each phase gets all outputs before it
          phase_order = [
              "phase_0", "phase_0_5", "phase_1", "phase_2",
              "phase_3", "phase_4", "phase_5",
          ]
          context: dict = {
              "brand_name": self.brand_name,
              "scope": self.scope,
              "budget_tier": self.budget_tier,
              "prior_phases": {},
          }
          for p in phase_order:
              if p == phase:
                  break
              output = getattr(self, f"{p}_output", None)
              if output:
                  context["prior_phases"][p] = output
          return context

      def get_executive_summary(self) -> str:
          """Generate an executive summary from all completed phase outputs.

          Produces a markdown-formatted summary with brand metadata,
          per-phase summaries, and asset counts.

          Returns:
              Markdown string suitable for display or document inclusion.
          """
          sections = []
          sections.append(f"# Brand Strategy Brief: {self.brand_name or 'TBD'}")
          sections.append(f"**Scope**: {self.scope or 'TBD'} | **Budget**: {self.budget_tier or 'TBD'}\n")

          phase_labels = {
              "phase_0": "Business Problem Diagnosis",
              "phase_0_5": "Brand Equity Audit",
              "phase_1": "Market Intelligence & Research",
              "phase_2": "Brand Strategy Core",
              "phase_3": "Brand Identity & Expression",
              "phase_4": "Communication Framework",
              "phase_5": "Strategy Plan & Deliverables",
          }
          for phase_key, label in phase_labels.items():
              output = getattr(self, f"{phase_key}_output", None)
              if output:
                  # Extract summary field if present, otherwise note completion
                  summary = output.get("summary", output.get("executive_summary", "Completed"))
                  sections.append(f"## {label}\n{summary}\n")

          if self.generated_images:
              sections.append(f"**Generated Images**: {len(self.generated_images)} assets")
          if self.generated_documents:
              sections.append(f"**Generated Documents**: {len(self.generated_documents)} files")

          return "\n".join(sections)

      def to_document_content(self) -> dict:
          """Convert the brief to structured content for document generation.

          Produces the data structure expected by Task 39's
          generate_document tool, with metadata, per-section content,
          generated asset references, and an executive summary.

          Returns:
              Dict with keys: metadata, sections, assets, and
              executive_summary.
          """
          return {
              "metadata": {
                  "brand_name": self.brand_name,
                  "scope": self.scope,
                  "budget_tier": self.budget_tier,
                  "session_id": self.session_id,
              },
              "sections": {
                  "business_diagnosis": self.phase_0_output,
                  "brand_equity_audit": self.phase_0_5_output or {},
                  "market_intelligence": self.phase_1_output,
                  "brand_strategy_core": self.phase_2_output,
                  "brand_identity": self.phase_3_output,
                  "communication_framework": self.phase_4_output,
                  "strategy_plan": self.phase_5_output,
              },
              "assets": {
                  "images": self.generated_images,
                  "documents": self.generated_documents,
              },
              "executive_summary": self.get_executive_summary(),
          }

      def save(self, path: str) -> None:
          """Save the brief to a JSON file.

          Creates parent directories if they don't exist.

          Args:
              path: File path for the JSON output.
          """
          file_path = Path(path)
          file_path.parent.mkdir(parents=True, exist_ok=True)
          file_path.write_text(
              self.model_dump_json(indent=2), encoding="utf-8"
          )

      @classmethod
      def load(cls, path: str) -> "BrandBrief":
          """Load a brief from a JSON file.

          Args:
              path: File path to read from.

          Returns:
              BrandBrief instance populated from the JSON data.

          Raises:
              FileNotFoundError: If the file does not exist.
          """
          file_path = Path(path)
          return cls.model_validate_json(file_path.read_text(encoding="utf-8"))
  ```
- **Acceptance Criteria**:
  - [ ] Phase outputs correctly accumulated
  - [ ] Context for each phase includes relevant prior outputs
  - [ ] Serializable to/from JSON for persistence
  - [ ] Converts to document template format

### Component 7: Skill Markdown File

#### Requirement 1 - Complete Orchestrator Skill Markdown
- **Requirement**: The actual SKILL.md file discovered by DeepAgents SkillsMiddleware (Task 35). Must follow skill-creator best practices: only `name` + `description` in frontmatter, body <500 lines, progressive disclosure via reference files, imperative form.
- **Implementation**:
  - `src/shared/src/shared/agent_skills/brand_strategy/brand-strategy-orchestrator/SKILL.md`
  - This file IS the skill content that gets loaded into agent context
  - Body contains core workflow navigation + phase summaries (the "what & when")
  - Detailed phase content (mentor scripts, quality gate items, KG queries) lives in reference files — loaded on-demand per phase transition

- **Directory Structure**:
  ```
  brand-strategy-orchestrator/
  ├── SKILL.md                             # Core workflow (~350-450 lines)
  └── references/
      ├── phase_0_diagnosis.md             # Mentor script + quality gate + KG queries
      ├── phase_0_5_equity_audit.md        # Rebrand-only audit procedures
      ├── phase_1_research.md              # Research phase guidance (delegates to market-research skill)
      ├── phase_2_positioning.md           # Positioning phase guidance (delegates to brand-positioning-identity skill)
      ├── phase_3_identity.md              # Identity phase guidance (delegates to brand-positioning-identity skill)
      ├── phase_4_communication.md         # Communication guidance (delegates to brand-communication-planning skill)
      ├── phase_5_deliverables.md          # Deliverables guidance (delegates to brand-communication-planning skill)
      └── rebrand_decision_matrix.md       # 6-signal scoring matrix + interpretation
  ```

  > **⚠️ Reference file access**: The SKILL.md instructs the agent to `read_file` specific reference files per phase transition (e.g., "Read `references/phase_1_research.md` before starting Phase 1"). This relies on `FilesystemBackend` (Task 35) providing `read_file` capability to the agent. The reference files are stored within the skill directory and accessible via the backend's virtual path. Verify that `SkillsMiddleware` + `FilesystemBackend` expose these nested files to the agent.

- **Frontmatter** (only `name` + `description` per skill-creator spec):
  ```yaml
  ---
  name: brand-strategy-orchestrator
  description: >-
    Master workflow orchestrating 6-phase F&B brand strategy development.
    Covers new brand creation, refresh, repositioning, and full rebrand.
    Manages phase sequencing, quality gates, mentor-mode conversations,
    rebrand scope diagnosis, and proactive loop-back triggers.
    Use when user asks to build a brand strategy, create a brand,
    rebrand an existing business, or develop brand positioning.
    Always load this skill first — it delegates to sub-skills per phase.
  ---
  ```

- **SKILL.md Body Structure** (~350-450 lines, imperative form, full-width lines):
  ```markdown
  # Brand Strategy Orchestrator

  ## ROLE & OBJECTIVE

  You are BrandMind's master strategist orchestrating a 6-phase brand strategy process for F&B businesses in Vietnam.
  Operate in mentor mode — guide the user through each phase with questions, concepts, and structured outputs.
  Accumulate context in a Brand Brief that grows richer with every phase.

  **CORE PRINCIPLE**: GUIDE, DON'T DICTATE. Ask → Listen → Synthesize → Validate → Advance.

  ## PHASE SEQUENCES

  Determine scope first (Phase 0), then follow the matching sequence:

  | Scope | Sequence |
  |-------|----------|
  | new_brand | 0 → 1 → 2 → 3 → 4 → 5 |
  | refresh | 0 → 0.5 → 1 → 3 → 4 → 5 |
  | repositioning | 0 → 0.5 → 1 → 2 → 3 → 4 → 5 |
  | full_rebrand | 0 → 0.5 → 1 → 2 → 3 → 4 → 5 |

  Refresh skips Phase 2 (positioning stays, only expression changes).

  ## PHASE OVERVIEW

  ### Phase 0: Business Problem Diagnosis
  Conduct a structured interview to understand the business context, goals, and constraints.
  Determine brand scope (new_brand vs rebrand). For existing brands, run the Rebrand Decision Matrix.
  Read `references/phase_0_diagnosis.md` for mentor script and quality gate.

  ### Phase 0.5: Brand Equity Audit (Rebrand Only)
  Assess what brand equity exists to preserve. Identify assets with recognition value.
  Map current brand perception vs intended positioning.
  Read `references/phase_0_5_equity_audit.md` for audit procedures.

  ### Phase 1: Market Intelligence & Research
  Delegate to `market-research` skill for the 8-step research methodology.
  Read `references/phase_1_research.md` for orchestrator-level guidance, then load the sub-skill.

  ### Phase 2: Brand Strategy Core
  Delegate to `brand-positioning-identity` skill for positioning framework.
  Read `references/phase_2_positioning.md` for orchestrator-level guidance, then load the sub-skill.

  ### Phase 3: Brand Identity & Expression
  Delegate to `brand-positioning-identity` skill for identity expression.
  Read `references/phase_3_identity.md` for orchestrator-level guidance, then load the sub-skill.

  ### Phase 4: Communication Framework
  Delegate to `brand-communication-planning` skill for messaging architecture.
  Read `references/phase_4_communication.md` for orchestrator-level guidance, then load the sub-skill.

  ### Phase 5: Strategy Plan & Deliverables
  Delegate to `brand-communication-planning` skill for deliverable assembly.
  Read `references/phase_5_deliverables.md` for orchestrator-level guidance, then load the sub-skill.

  ## QUALITY GATES

  Every phase ends with a quality gate — a checklist of criteria that must pass before advancing.
  If any item fails, address the gap before proceeding.
  Each phase reference file contains its specific gate items.

  General gate protocol:
  1. Review all gate items for the current phase
  2. Mark each as pass/fail with evidence
  3. If all pass → advance to next phase in sequence
  4. If any fail → address gaps, re-evaluate, then re-check

  ## PROACTIVE LOOP TRIGGERS

  Monitor these conditions continuously. If detected, loop back to the indicated phase:

  | Trigger | Detected At | Loop To | Action |
  |---------|------------|---------|--------|
  | stress_deliverability | Phase 2 | Phase 0 | Product truth cannot support positioning claim — revisit business model |
  | stress_relevance | Phase 2 | Phase 1 | Target audience does not care about this position — revisit research |
  | naming_blocked | Phase 3 | Phase 2 | No viable name fits the positioning — soften constraints |
  | visual_conflict | Phase 3 | Phase 2 | Visual direction contradicts positioning — realign |
  | messaging_abstract | Phase 4 | Phase 2-3 | Messages lack concreteness — revisit identity |
  | budget_overrun | Phase 5 | Phase 0 | Implementation exceeds stated budget — revisit constraints |
  | audit_no_equity | Phase 0.5 | Phase 0 | No meaningful equity found — recommend new_brand scope instead |
  | backlash_risk | Phase 5 | Phase 3 | Transition plan reveals high backlash risk — revisit identity changes |

  ## REBRAND DECISION MATRIX

  Use in Phase 0 when user has an existing brand. Score 6 signals (0-2 each):
  Read `references/rebrand_decision_matrix.md` for full matrix details.

  Score ranges → recommended scope:
  - 0-3: Reinforce (no rebrand needed, strengthen current brand)
  - 4-6: Refresh (keep core, update expression)
  - 7-9: Repositioning (shift strategic position)
  - 10-12: Full Rebrand (comprehensive overhaul)

  ## PHASE TRANSITION PROTOCOL

  When transitioning to a new phase:
  1. Verify the current phase's quality gate passes
  2. Update the Brand Brief with current phase outputs
  3. Read the reference file for the next phase
  4. Load the relevant sub-skill if the phase delegates:
     - Phase 1 → `market-research`
     - Phase 2-3 → `brand-positioning-identity`
     - Phase 4-5 → `brand-communication-planning`
  5. Brief the user on what comes next and what you need from them

  ## MENTOR MODE PROTOCOL

  For every phase interaction:
  1. **Open**: Explain phase purpose and what you will explore together
  2. **Ask**: Pose 3-5 questions, one at a time, with explanations of marketing concepts in Vietnamese
  3. **Synthesize**: Summarize what you learned, highlight key insights
  4. **Validate**: Present your synthesis, ask user to confirm or adjust
  5. **Gate**: Run quality gate, address gaps, then advance

  Explain marketing jargon in plain Vietnamese. Use analogies from F&B.
  Never assume — always confirm with the user before locking decisions.

  ## ERROR HANDLING

  - If a tool call fails, explain what happened and suggest alternatives
  - If a sub-skill is unavailable, use the reference file content as fallback
  - If the user wants to skip a phase, warn about downstream impact but respect their choice
  - If research yields insufficient data, explicitly state the gap and propose how to fill it
  ```

- **Reference Files**: Each ~50-150 lines. Contains phase-specific mentor scripts (Vietnamese), quality gate checklist items (from Component 2's QUALITY_GATES data), KG query recommendations, and orchestrator-level guidance. Implementer writes these using content from Components 2, 3, and the blueprint.

- **Acceptance Criteria**:
  - [ ] YAML frontmatter has ONLY `name` + `description` (no `metadata`, no `allowed-tools`)
  - [ ] `description` ≤ 1024 chars, includes trigger contexts ("Use when...")
  - [ ] SKILL.md body ≤ 500 lines
  - [ ] Body uses imperative form, full-width lines
  - [ ] Reference files created for all phases + rebrand matrix
  - [ ] Phase transition protocol delegates to sub-skills correctly
  - [ ] Proactive loop triggers table complete (8 triggers)
  - [ ] Rebrand decision matrix scoring summarized, detail in reference file
  - [ ] Quality gate protocol described generically; per-phase items in reference files
  - [ ] Mentor mode protocol described once; per-phase scripts in reference files

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: New Brand Workflow
- **Purpose**: Verify phase sequence for new brand
- **Steps**:
  1. Create PhaseState with scope=NEW_BRAND
  2. Advance through all phases
  3. Verify sequence: 0 → 1 → 2 → 3 → 4 → 5
- **Expected Result**: Phase 0.5 skipped, 6 transitions
- **Status**: ⏳ Pending

### Test Case 2: Full Rebrand Workflow
- **Purpose**: Verify phase sequence for full rebrand
- **Steps**:
  1. Create PhaseState with scope=FULL_REBRAND
  2. Advance through all phases
  3. Verify sequence: 0 → 0.5 → 1 → 2 → 3 → 4 → 5
- **Expected Result**: Phase 0.5 included, 7 transitions
- **Status**: ⏳ Pending

### Test Case 3: Refresh Skips Phase 2
- **Purpose**: Verify refresh scope skips Phase 2
- **Steps**:
  1. Create PhaseState with scope=REFRESH
  2. Advance through phases
  3. Verify Phase 2 is not in sequence
- **Expected Result**: Sequence: 0 → 0.5 → 1 → 3 → 4 → 5
- **Status**: ⏳ Pending

### Test Case 4: Rebrand Decision Matrix Scoring
- **Purpose**: Verify matrix correctly classifies scope
- **Steps**:
  1. Score all signals at 0 → should recommend "reinforce"
  2. Score total 5 → should recommend "refresh"
  3. Score total 8 → should recommend "reposition"
  4. Score total 11 → should recommend "full_rebrand"
- **Expected Result**: Correct scope per score range
- **Status**: ⏳ Pending

### Test Case 5: Proactive Loop Trigger
- **Purpose**: Verify loop trigger fires correctly
- **Steps**:
  1. At Phase 2, set stress test "Deliverability" = failed
  2. Check triggers → should fire "stress_deliverability"
  3. Verify target phase is Phase 0
- **Expected Result**: Trigger with correct target and explanation
- **Status**: ⏳ Pending

### Test Case 6: Quality Gate — Phase 1 Partial Pass
- **Purpose**: Verify quality gate blocks when items missing
- **Steps**:
  1. Evaluate Phase 1 gate with only 3 of 6 items
  2. Verify gate fails
  3. Check missing items list
- **Expected Result**: passed=False, missing_items lists 3 unchecked criteria
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation.

### What Was Implemented

**Components Completed**:
- [ ] [Component 1]: Phase State Machine
- [ ] [Component 2]: Quality Gate Engine
- [ ] [Component 3]: Mentor Script Templates
- [ ] [Component 4]: Rebrand Decision Matrix & Workflow Branching
- [ ] [Component 5]: Proactive Loop Triggers
- [ ] [Component 6]: Context Accumulation & Brand Brief
- [ ] [Component 7]: Skill Markdown File

**Files Created/Modified**:
```
src/core/src/core/brand_strategy/
├── __init__.py
└── orchestrator/
    ├── __init__.py
    ├── phase_state.py             # Phase state machine
    ├── quality_gate.py            # Quality gate engine
    ├── rebrand_matrix.py          # Rebrand decision matrix
    ├── proactive_loops.py         # Proactive loop triggers
    └── brand_brief.py             # Brand Brief accumulator

src/shared/src/shared/agent_skills/brand_strategy/
└── brand-strategy-orchestrator/
    ├── SKILL.md                   # Core workflow (~350-450 lines)
    └── references/
        ├── phase_0_diagnosis.md
        ├── phase_0_5_equity_audit.md
        ├── phase_1_research.md
        ├── phase_2_positioning.md
        ├── phase_3_identity.md
        ├── phase_4_communication.md
        ├── phase_5_deliverables.md
        └── rebrand_decision_matrix.md
```

------------------------------------------------------------------------
