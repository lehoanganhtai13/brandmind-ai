"""Brand naming process models.

6-step naming process with Keller's 6 Brand Element Selection Criteria.
"""

from __future__ import annotations

from typing import Any

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
        return sum(
            [
                self.memorable,
                self.meaningful,
                self.likable,
                self.transferable,
                self.adaptable,
                self.protectable,
            ]
        )


class NameCandidate(BaseModel):
    """A brand name candidate under evaluation."""

    name: str
    naming_approach: str = ""
    availability: dict[str, Any] = Field(default_factory=dict)
    positioning_fit: str = ""
    keller_scores: KellerCriteria = Field(default_factory=KellerCriteria)
    linguistic_notes: str = ""
    shortlisted: bool = False
    selected: bool = False


class NamingProcess(BaseModel):
    """Complete naming process result (6 steps).

    Steps:
    1. Choose naming approach
    2. Generate 10-15 candidates
    3. Linguistic screening (VN + EN)
    4. Availability checks (domain, social, trademark)
    5. Evaluate top 5 against Keller's 6 criteria
    6. Present top 3 to user with rationale
    """

    naming_approach: str = ""
    candidates: list[NameCandidate] = Field(default_factory=list)
    shortlisted: list[NameCandidate] = Field(default_factory=list)
    selected_name: str = ""
    selection_rationale: str = ""
    skipped: bool = False
    skip_reason: str = ""
