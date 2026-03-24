"""Brand Brief — accumulated document that grows through phases.

Each phase adds its outputs. Subsequent phases read prior sections as
context. The complete brief becomes Phase 5's document assembly input.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, Field


class BrandBrief(BaseModel):
    """Accumulated brand strategy document that grows with each phase.

    Structure matches the Blueprint's required outputs per phase.
    Phase outputs are stored as dicts for serialization flexibility.
    """

    session_id: str = ""
    brand_name: str = ""
    scope: str = ""
    budget_tier: str = ""

    # Phase outputs (populated as phases complete)
    phase_0_output: dict[str, Any] = Field(default_factory=dict)
    phase_0_5_output: dict[str, Any] | None = None  # Rebrand only
    phase_1_output: dict[str, Any] = Field(default_factory=dict)
    phase_2_output: dict[str, Any] = Field(default_factory=dict)
    phase_3_output: dict[str, Any] = Field(default_factory=dict)
    phase_4_output: dict[str, Any] = Field(default_factory=dict)
    phase_5_output: dict[str, Any] = Field(default_factory=dict)

    # Generated assets
    generated_images: list[str] = Field(default_factory=list)
    generated_documents: list[str] = Field(default_factory=list)

    _PHASE_FIELDS: ClassVar[list[str]] = [
        "phase_0_output",
        "phase_0_5_output",
        "phase_1_output",
        "phase_2_output",
        "phase_3_output",
        "phase_4_output",
        "phase_5_output",
    ]

    def add_phase_output(self, phase: str, output: dict[str, Any]) -> None:
        """Add or update the output for a completed phase.

        Args:
            phase: Phase identifier (e.g., "phase_0", "phase_1").
            output: Dict of phase output data.

        Raises:
            ValueError: If phase key is not valid.
        """
        field_name = f"{phase}_output"
        if field_name not in self._PHASE_FIELDS:
            valid = [f.replace("_output", "") for f in self._PHASE_FIELDS]
            raise ValueError(f"Invalid phase key '{phase}'. Expected one of: {valid}")
        setattr(self, field_name, output)

    def get_context_for_phase(self, phase: str) -> dict[str, Any]:
        """Get accumulated outputs from all prior phases as context.

        Args:
            phase: The target phase that needs prior context.

        Returns:
            Dict with brand metadata and prior phase outputs.
        """
        phase_order = [
            "phase_0",
            "phase_0_5",
            "phase_1",
            "phase_2",
            "phase_3",
            "phase_4",
            "phase_5",
        ]
        context: dict[str, Any] = {
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

        Returns:
            Markdown string suitable for display or document inclusion.
        """
        sections: list[str] = []
        sections.append(f"# Brand Strategy Brief: {self.brand_name or 'TBD'}")
        sections.append(
            f"**Scope**: {self.scope or 'TBD'} | "
            f"**Budget**: {self.budget_tier or 'TBD'}\n"
        )

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
                summary = output.get(
                    "summary", output.get("executive_summary", "Completed")
                )
                sections.append(f"## {label}\n{summary}\n")

        if self.generated_images:
            sections.append(
                f"**Generated Images**: {len(self.generated_images)} assets"
            )
        if self.generated_documents:
            sections.append(
                f"**Generated Documents**: {len(self.generated_documents)} files"
            )

        return "\n".join(sections)

    def to_document_content(self) -> dict[str, Any]:
        """Convert the brief to structured content for document generation.

        Returns:
            Dict compatible with Task 39's generate_document tool.
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
        """Save the brief to a JSON file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str) -> BrandBrief:
        """Load a brief from a JSON file."""
        file_path = Path(path)
        return cls.model_validate_json(file_path.read_text(encoding="utf-8"))
