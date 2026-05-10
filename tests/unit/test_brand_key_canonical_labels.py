"""Regression tests for Brand Key canonical component labels."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME_SURFACES = (
    _REPO_ROOT / "src/prompts/brand_strategy/system_prompt.py",
    _REPO_ROOT / "src/prompts/brand_strategy/generate_brand_key.py",
    _REPO_ROOT / "src/shared/src/shared/agent_tools/image/generate_brand_key.py",
    (
        _REPO_ROOT
        / "src/shared/src/shared/agent_skills/brand_strategy/"
        "brand-communication-planning/references/deliverable_assembly.md"
    ),
)


def test_brand_key_runtime_surfaces_use_canonical_labels() -> None:
    """Keep runtime prompt surfaces aligned on the canonical Brand Key labels."""
    for path in _RUNTIME_SURFACES:
        text = path.read_text(encoding="utf-8")

        has_canonical_values_label = (
            "Values, Beliefs & Personality" in text
            or "VALUES, BELIEFS & PERSONALITY" in text
        )

        assert has_canonical_values_label, str(path)
        assert "Values & Personality" not in text, str(path)
        assert "VALUES & PERSONALITY" not in text, str(path)
        assert "Root Strengths" in text or "ROOT STRENGTHS" in text, str(path)
        assert "ROOT STRENGTH (" not in text, str(path)
