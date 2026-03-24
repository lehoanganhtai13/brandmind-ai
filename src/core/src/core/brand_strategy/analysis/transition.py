"""Rebrand transition and change management models.

Only produced when scope is refresh, repositioning, or full_rebrand.
Covers 7 areas from Blueprint Section 4.5.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field


class StakeholderEntry(BaseModel):
    """A stakeholder in the communication plan."""

    stakeholder: str
    impact_level: str  # high, medium, low
    communication_method: str
    timing: str
    key_message: str = ""


class PhysicalAsset(BaseModel):
    """A physical asset in the changeover checklist."""

    asset: str
    current_state: str = ""
    new_state: str = ""
    estimated_cost: str = ""
    timeline: str = ""


class DigitalAsset(BaseModel):
    """A digital platform migration item."""

    platform: str
    changes_needed: list[str] = Field(default_factory=list)
    timeline: str = ""


class TransitionPlan(BaseModel):
    """Complete transition & change management plan for rebrands."""

    approach: str = ""  # big_bang, phased, inside_out

    stakeholder_map: list[StakeholderEntry] = Field(default_factory=list)
    internal_rollout: list[str] = Field(default_factory=list)
    customer_announcement: str = ""
    customer_channels: list[str] = Field(default_factory=list)
    customer_tone: str = ""
    customer_faq: list[dict[str, Any]] = Field(default_factory=list)
    physical_changeover: list[PhysicalAsset] = Field(default_factory=list)
    digital_migration: list[DigitalAsset] = Field(default_factory=list)
    pre_launch_steps: list[str] = Field(default_factory=list)
    d_day: str = ""
    post_launch_steps: list[str] = Field(default_factory=list)
    risk_mitigation: list[dict[str, Any]] = Field(default_factory=list)

    def estimate_total_changeover_cost(self) -> str:
        """Sum estimated costs from physical changeovers."""
        total_min = 0.0
        total_max = 0.0
        items_with_cost = 0

        for asset in self.physical_changeover:
            if not asset.estimated_cost:
                continue
            numbers = re.findall(r"[\d,.]+", asset.estimated_cost)
            if not numbers:
                continue
            items_with_cost += 1
            values = [float(n.replace(",", "")) for n in numbers]

            multiplier = 1.0
            cost_str = asset.estimated_cost
            if re.search(r"\d\s*[bB]\b", cost_str) or ("tỷ" in cost_str):
                multiplier = 1_000
            elif (
                re.search(r"\d\s*[mM]\b", cost_str)
                or "triệu" in cost_str
                or "trieu" in cost_str.lower()
            ):
                multiplier = 1

            if len(values) >= 2:
                total_min += values[0] * multiplier
                total_max += values[1] * multiplier
            else:
                total_min += values[0] * multiplier
                total_max += values[0] * multiplier

        if items_with_cost == 0:
            return "No cost estimates available."

        if total_min == total_max:
            return f"{total_min:.0f}M VND ({items_with_cost} items estimated)"
        return (
            f"{total_min:.0f}-{total_max:.0f}M VND ({items_with_cost} items estimated)"
        )
