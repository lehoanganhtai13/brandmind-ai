"""Brand Strategy Orchestrator — state management and quality gates.

Provides PhaseState, QualityGateEngine, BrandBrief, RebrandDecisionMatrix,
and ProactiveLoopDetector for the brand strategy workflow.
"""

from core.brand_strategy.orchestrator.brand_brief import BrandBrief
from core.brand_strategy.orchestrator.phase_state import (
    BrandScope,
    Phase,
    PhaseState,
    PhaseTransition,
)
from core.brand_strategy.orchestrator.proactive_loops import (
    LoopTrigger,
    ProactiveLoopDetector,
)
from core.brand_strategy.orchestrator.quality_gate import (
    QualityGateEngine,
    QualityGateResult,
)
from core.brand_strategy.orchestrator.rebrand_matrix import (
    RebrandDecisionMatrix,
    RebrandDecisionResult,
)

__all__ = [
    "BrandBrief",
    "BrandScope",
    "LoopTrigger",
    "Phase",
    "PhaseState",
    "PhaseTransition",
    "ProactiveLoopDetector",
    "QualityGateEngine",
    "QualityGateResult",
    "RebrandDecisionMatrix",
    "RebrandDecisionResult",
]
