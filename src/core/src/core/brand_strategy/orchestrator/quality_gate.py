"""Quality gate engine for brand strategy phase transitions.

Validates per-phase exit criteria before the agent advances.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class GateItem(BaseModel):
    """A single quality gate criterion."""

    id: str
    description: str
    passed: bool = False
    evidence: str = ""
    required: bool = True
    scope_filter: list[str] | None = None  # None = all scopes


class QualityGateResult(BaseModel):
    """Result of a quality gate evaluation."""

    phase: str
    passed: bool
    items: list[GateItem] = Field(default_factory=list)
    missing_items: list[str] = Field(default_factory=list)
    pass_rate: float = 0.0


# Quality gate definitions per phase (from Blueprint Sections 3.1-3.7)
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
            id="p0_location",
            description="Target location/market identified",
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
            description=(
                "Brand Inventory completed (visual, verbal, experiential audit)"
            ),
            scope_filter=["refresh", "repositioning", "full_rebrand"],
        ),
        GateItem(
            id="p05_perception",
            description=(
                "Current brand perception assessed (reviews, social, customer voice)"
            ),
            scope_filter=["refresh", "repositioning", "full_rebrand"],
        ),
        GateItem(
            id="p05_equity",
            description=(
                "Brand equity sources identified (what to keep, evolve, discard)"
            ),
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
            description=(
                "Competitive perceptual map created with white space identified"
            ),
        ),
        GateItem(
            id="p1_synthesis",
            description=(
                "Strategic synthesis completed (sweet spot + prioritized insights)"
            ),
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
            description=(
                "Value ladder built (attributes -> functional -> emotional -> outcome)"
            ),
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
            description=(
                "Brand name finalized"
                " (new: full process; rebrand: keep/rename justified)"
            ),
        ),
        GateItem(
            id="p3_visual",
            description=(
                "Visual identity direction documented (colors, typography, imagery)"
            ),
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
            description=(
                "Implementation roadmap with 3 time horizons, tied to budget_tier"
            ),
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
    """Validates quality gate criteria for phase transitions.

    Each phase has required criteria that must pass before advancing.
    Scope-filtered items are only required for specific scopes.
    """

    def evaluate(
        self,
        phase: str,
        scope: str,
        completed_items: list[str],
    ) -> QualityGateResult:
        """Evaluate the quality gate for a given phase.

        Args:
            phase: Phase identifier (e.g., "phase_0", "phase_1").
            scope: Brand scope string (e.g., "new_brand", "refresh").
            completed_items: List of GateItem IDs that have been satisfied.

        Returns:
            QualityGateResult with pass/fail status and details.
        """
        applicable = self.get_checklist(phase, scope)
        if not applicable:
            return QualityGateResult(phase=phase, passed=True, pass_rate=1.0)

        missing: list[str] = []
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

    def get_checklist(self, phase: str, scope: str) -> list[GateItem]:
        """Get applicable gate items for a phase and scope.

        Args:
            phase: Phase identifier.
            scope: Brand scope string.

        Returns:
            List of GateItem copies applicable to this phase/scope.
        """
        gate_items = QUALITY_GATES.get(phase, [])
        applicable: list[GateItem] = []
        for item in gate_items:
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

        Args:
            phase: Phase identifier.
            scope: Brand scope string.
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
