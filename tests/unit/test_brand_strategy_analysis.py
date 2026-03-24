"""Unit tests for Brand Strategy Analysis Models (Tasks 43-45).

Tests synthesis, positioning, naming, messaging, roadmap, and transition models.
"""

from __future__ import annotations

import pytest

from core.brand_strategy.analysis import (
    CompetitorPosition,
    CustomerInsight,
    KellerCriteria,
    NameCandidate,
    NamingProcess,
    PerceptualMap,
    PerceptualMapAxis,
    PointOfDifference,
    PointOfParity,
    PositioningStatement,
    ProductBrandAlignment,
    StressTestResult,
    StrategicSynthesis,
    SWOTAnalysis,
)
from core.brand_strategy.analysis.messaging import (
    AIDAMapping,
    ChannelStrategy,
    ContentPillar,
    CIALDINI_FNB_EXAMPLES,
    DEFAULT_FNB_PILLARS,
    KeyMessage,
    PersuasionApplication,
    ValueProposition,
)
from core.brand_strategy.analysis.roadmap import (
    ImplementationRoadmap,
    KPIDefinition,
    MeasurementPlan,
    RoadmapItem,
)
from core.brand_strategy.analysis.transition import (
    DigitalAsset,
    PhysicalAsset,
    StakeholderEntry,
    TransitionPlan,
)


# ===== Task 43: Synthesis Models =====


class TestSWOTAnalysis:
    def test_defaults(self):
        swot = SWOTAnalysis()
        assert swot.strengths == []
        assert swot.weaknesses == []
        assert swot.opportunities == []
        assert swot.threats == []

    def test_populated(self):
        swot = SWOTAnalysis(
            strengths=["Strong location"],
            weaknesses=["No brand awareness"],
            opportunities=["Growing specialty coffee market"],
            threats=["Major chain nearby"],
        )
        assert len(swot.strengths) == 1
        assert len(swot.threats) == 1


class TestPerceptualMap:
    def test_construction(self):
        pm = PerceptualMap(
            x_axis=PerceptualMapAxis(
                label="Price", low_label="Budget", high_label="Premium"
            ),
            y_axis=PerceptualMapAxis(
                label="Quality", low_label="Basic", high_label="Artisan"
            ),
            competitors=[
                CompetitorPosition(name="Rival A", x_score=3.0, y_score=7.0),
                CompetitorPosition(name="Rival B", x_score=8.0, y_score=5.0),
            ],
            white_space="High-quality affordable segment",
        )
        assert len(pm.competitors) == 2
        assert pm.white_space != ""


class TestCustomerInsightPrioritization:
    def test_prioritize_insights(self):
        synthesis = StrategicSynthesis(
            prioritized_insights=[
                CustomerInsight(
                    observation="Obs A",
                    motivation="Mot A",
                    implication="Imp A",
                    strategic_value=5,
                    actionability=5,
                    evidence_strength=5,
                ),
                CustomerInsight(
                    observation="Obs B",
                    motivation="Mot B",
                    implication="Imp B",
                    strategic_value=1,
                    actionability=1,
                    evidence_strength=1,
                ),
                CustomerInsight(
                    observation="Obs C",
                    motivation="Mot C",
                    implication="Imp C",
                    strategic_value=3,
                    actionability=3,
                    evidence_strength=3,
                ),
            ]
        )
        synthesis.prioritize_insights()

        # Should be sorted by priority_score descending
        scores = [i.priority_score for i in synthesis.prioritized_insights]
        assert scores == sorted(scores, reverse=True)

        # Max score: 5*5*5/125 = 1.0
        assert synthesis.prioritized_insights[0].priority_score == 1.0
        # Min score: 1*1*1/125 = 0.008
        assert synthesis.prioritized_insights[-1].priority_score == pytest.approx(
            0.008, abs=0.001
        )


# ===== Task 44: Positioning Models =====


class TestPointsOfParityAndDifference:
    def test_pop_types(self):
        pop = PointOfParity(
            type="category",
            description="Clean, well-lit space",
        )
        assert pop.type == "category"

    def test_pod_three_gates(self):
        pod = PointOfDifference(
            description="Single-origin Vietnamese coffee",
            desirable=True,
            deliverable=True,
            differentiating=True,
        )
        assert pod.desirable is True
        assert pod.deliverable is True
        assert pod.differentiating is True


class TestStressTest:
    def test_all_pass(self):
        st = StressTestResult(
            competitive_vacancy=True,
            deliverability=True,
            relevance=True,
            defensibility=True,
            budget_feasibility=True,
        )
        assert st.passed is True
        assert st.failed_criteria == []

    def test_partial_fail(self):
        st = StressTestResult(
            competitive_vacancy=True,
            deliverability=False,
            relevance=True,
            defensibility=False,
            budget_feasibility=True,
        )
        assert st.passed is False
        assert "deliverability" in st.failed_criteria
        assert "defensibility" in st.failed_criteria
        assert len(st.failed_criteria) == 2

    def test_all_fail(self):
        st = StressTestResult()
        assert st.passed is False
        assert len(st.failed_criteria) == 5


class TestPositioningStatement:
    def test_template_fields(self):
        ps = PositioningStatement(
            target_audience="Young professionals in HCMC",
            need="a productive workspace with great coffee",
            brand_name="Coffee Lab",
            competitive_frame="specialty café",
            key_pod="data-driven coffee brewing",
            reasons_to_believe="Q-grader certified team",
        )
        assert ps.target_audience != ""
        assert ps.brand_name == "Coffee Lab"


# ===== Task 44: Naming Models =====


class TestKellerCriteria:
    def test_total_score(self):
        kc = KellerCriteria(
            memorable=4,
            meaningful=3,
            likable=5,
            transferable=2,
            adaptable=4,
            protectable=3,
        )
        assert kc.total_score == 21

    def test_zero_scores(self):
        kc = KellerCriteria()
        assert kc.total_score == 0


class TestNamingProcess:
    def test_skipped_for_refresh(self):
        np = NamingProcess(
            skipped=True,
            skip_reason="Brand name kept for REFRESH scope",
        )
        assert np.skipped is True

    def test_full_process(self):
        np = NamingProcess(
            naming_approach="descriptive",
            candidates=[
                NameCandidate(name="Coffee Lab"),
                NameCandidate(name="Brew Station"),
            ],
            selected_name="Coffee Lab",
        )
        assert len(np.candidates) == 2
        assert np.selected_name == "Coffee Lab"


# ===== Task 45: Messaging Models =====


class TestValueProposition:
    def test_three_levels(self):
        vp = ValueProposition(
            one_liner="Where coffee meets science",
            elevator_pitch="We combine data-driven brewing with artisan craft...",
            full_story="Coffee Lab was born from...",
        )
        assert vp.one_liner != ""
        assert vp.elevator_pitch != ""
        assert vp.full_story != ""


class TestCialdiniExamples:
    def test_all_principles_present(self):
        expected = {
            "social_proof",
            "authority",
            "scarcity",
            "liking",
            "reciprocity",
            "commitment",
            "unity",
        }
        assert set(CIALDINI_FNB_EXAMPLES.keys()) == expected

    def test_fnb_pillars_sum_to_100(self):
        total = sum(p.percentage for p in DEFAULT_FNB_PILLARS)
        assert total == 100


class TestChannelStrategy:
    def test_construction(self):
        cs = ChannelStrategy(
            channel="Instagram",
            purpose="Visual brand storytelling",
            content_types=["reels", "stories", "posts"],
            posting_frequency="5x/week",
        )
        assert cs.channel == "Instagram"
        assert len(cs.content_types) == 3


# ===== Task 45: Roadmap Models =====


class TestImplementationRoadmap:
    def test_budget_modifier_bootstrap(self):
        roadmap = ImplementationRoadmap(
            quick_wins=[
                RoadmapItem(action="Set up social media", priority="must_do"),
                RoadmapItem(action="Run paid ads campaign", priority="must_do"),
                RoadmapItem(action="Hire influencer", priority="must_do"),
            ],
        )
        roadmap.apply_budget_modifier("bootstrap")
        priorities = {item.action: item.priority for item in roadmap.quick_wins}
        assert priorities["Set up social media"] == "must_do"
        assert priorities["Run paid ads campaign"] == "nice_to_have"
        assert priorities["Hire influencer"] == "nice_to_have"

    def test_budget_modifier_enterprise(self):
        roadmap = ImplementationRoadmap(
            quick_wins=[
                RoadmapItem(action="Set up social media", priority="nice_to_have"),
                RoadmapItem(action="Run paid ads campaign", priority="nice_to_have"),
            ],
        )
        roadmap.apply_budget_modifier("enterprise")
        for item in roadmap.quick_wins:
            assert item.priority == "must_do"

    def test_budget_modifier_starter_no_change(self):
        """Starter tier doesn't auto-downgrade or upgrade."""
        roadmap = ImplementationRoadmap(
            quick_wins=[
                RoadmapItem(action="Run paid ads", priority="must_do"),
            ],
        )
        roadmap.apply_budget_modifier("starter")
        assert roadmap.quick_wins[0].priority == "must_do"


# ===== Task 45: Transition Models =====


class TestTransitionPlan:
    def test_estimate_cost_no_assets(self):
        plan = TransitionPlan()
        assert "No cost" in plan.estimate_total_changeover_cost()

    def test_estimate_cost_single_range(self):
        plan = TransitionPlan(
            physical_changeover=[
                PhysicalAsset(
                    asset="Signage",
                    estimated_cost="5-10M VND",
                ),
            ]
        )
        result = plan.estimate_total_changeover_cost()
        assert "5-10M VND" in result
        assert "1 items" in result

    def test_estimate_cost_multiple_assets(self):
        plan = TransitionPlan(
            physical_changeover=[
                PhysicalAsset(asset="Signage", estimated_cost="5-10M"),
                PhysicalAsset(asset="Menu boards", estimated_cost="2-3M"),
            ]
        )
        result = plan.estimate_total_changeover_cost()
        assert "7-13M VND" in result
        assert "2 items" in result

    def test_estimate_cost_billion_multiplier(self):
        plan = TransitionPlan(
            physical_changeover=[
                PhysicalAsset(asset="Interior", estimated_cost="1-2B VND"),
            ]
        )
        result = plan.estimate_total_changeover_cost()
        # 1B = 1000M, 2B = 2000M
        assert "1000-2000M" in result

    def test_stakeholder_map(self):
        plan = TransitionPlan(
            stakeholder_map=[
                StakeholderEntry(
                    stakeholder="Employees",
                    impact_level="high",
                    communication_method="Town hall meeting",
                    timing="2 weeks before launch",
                ),
            ]
        )
        assert len(plan.stakeholder_map) == 1
        assert plan.stakeholder_map[0].impact_level == "high"

    def test_digital_migration(self):
        plan = TransitionPlan(
            digital_migration=[
                DigitalAsset(
                    platform="Instagram",
                    changes_needed=["Update profile", "New bio"],
                ),
            ]
        )
        assert len(plan.digital_migration) == 1
