"""Integration tests for Brand Strategy Skills Infrastructure (Task 35).

Tests SkillsMiddleware creation and SKILL.md file availability.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shared.agent_skills import create_brand_strategy_skills_middleware


EXPECTED_SKILLS = [
    "brand-strategy-orchestrator",
    "market-research",
    "brand-positioning-identity",
    "brand-communication-planning",
]

SKILLS_BASE = (
    Path(__file__).parent.parent.parent
    / "src"
    / "shared"
    / "src"
    / "shared"
    / "agent_skills"
    / "brand_strategy"
)


class TestSkillFiles:
    """Test that all SKILL.md files exist and have correct structure."""

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_md_exists(self, skill_name):
        skill_file = SKILLS_BASE / skill_name / "SKILL.md"
        assert skill_file.exists(), f"Missing: {skill_file}"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_md_has_frontmatter(self, skill_name):
        """SKILL.md should have YAML frontmatter with name + description."""
        skill_file = SKILLS_BASE / skill_name / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        assert content.startswith("---"), f"{skill_name}/SKILL.md missing YAML frontmatter"
        # Should have closing frontmatter
        second_dash = content.find("---", 3)
        assert second_dash > 0, f"{skill_name}/SKILL.md frontmatter not closed"
        # Should have name field
        frontmatter = content[3:second_dash]
        assert "name:" in frontmatter, f"{skill_name}/SKILL.md missing name field"
        assert "description:" in frontmatter, (
            f"{skill_name}/SKILL.md missing description field"
        )

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_md_body_not_empty(self, skill_name):
        """SKILL.md body should have meaningful content."""
        skill_file = SKILLS_BASE / skill_name / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        # Body starts after second ---
        second_dash = content.find("---", 3)
        body = content[second_dash + 3 :].strip()
        assert len(body) > 100, (
            f"{skill_name}/SKILL.md body too short: {len(body)} chars"
        )


class TestSkillsMiddleware:
    """Test SkillsMiddleware factory."""

    def test_create_middleware(self):
        """Factory should return a (SkillsMiddleware, FilesystemMiddleware) tuple."""
        result = create_brand_strategy_skills_middleware()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_skills_middleware_has_backend(self):
        """SkillsMiddleware should have backend configured."""
        skills_mw, _ = create_brand_strategy_skills_middleware()
        assert hasattr(skills_mw, "backend") or hasattr(skills_mw, "_backend")

    def test_filesystem_middleware_has_tools(self):
        """FilesystemMiddleware should provide read_file tool."""
        _, fs_mw = create_brand_strategy_skills_middleware()
        tool_names = {t.name for t in fs_mw.tools}
        assert "read_file" in tool_names


class TestSkillReferences:
    """Test that reference files exist for skills that need them."""

    def test_market_research_has_output_templates(self):
        ref = SKILLS_BASE / "market-research" / "references" / "output_templates.md"
        assert ref.exists()

    def test_positioning_has_references(self):
        refs_dir = SKILLS_BASE / "brand-positioning-identity" / "references"
        assert (refs_dir / "output_templates.md").exists()
        assert (refs_dir / "naming_process.md").exists()
        assert (refs_dir / "identity_transition.md").exists()

    def test_communication_has_references(self):
        refs_dir = SKILLS_BASE / "brand-communication-planning" / "references"
        assert (refs_dir / "output_templates.md").exists()
        assert (refs_dir / "transition_plan.md").exists()
        assert (refs_dir / "deliverable_assembly.md").exists()
