"""Agent Skills configuration and setup.

Provides factory functions for creating SkillsMiddleware instances
that leverage DeepAgents' built-in progressive disclosure pattern.

Skills are organized as directories containing SKILL.md files with
YAML frontmatter (per Agent Skills spec: https://agentskills.io).
"""

from shared.agent_skills.config import (
    create_brand_strategy_skills_middleware,
)

__all__ = [
    "create_brand_strategy_skills_middleware",
]
