"""Configuration for Agent Skills using DeepAgents built-in SkillsMiddleware.

Provides factory functions to create pre-configured SkillsMiddleware
instances for different agent domains. Uses progressive disclosure pattern:
agent sees skill name + description in system prompt, reads full SKILL.md
on-demand via FilesystemMiddleware.

Architecture:
    SkillsMiddleware (built-in from DeepAgents)
    └── FilesystemBackend (local filesystem access, virtual_mode=True)
        └── sources: ["/"]
            ├── brand-strategy-orchestrator/SKILL.md
            ├── market-research/SKILL.md
            ├── brand-positioning-identity/SKILL.md
            └── brand-communication-planning/SKILL.md
    FilesystemMiddleware (same backend)
    └── Provides read_file, ls, glob, grep tools for reading SKILL.md

Usage:
    from shared.agent_skills import create_brand_strategy_skills_middleware

    skills_mw, fs_mw = create_brand_strategy_skills_middleware()
    agent = create_agent(
        model=model,
        middleware=[fs_mw, skills_mw, ...],
    )
"""

from pathlib import Path
from typing import Literal, cast

from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.filesystem import (
    GREP_TOOL_DESCRIPTION,
    FilesystemMiddleware,
    FilesystemState,
)
from deepagents.middleware.skills import SkillsMiddleware
from langchain.tools import ToolRuntime, tool
from langchain_core.tools import BaseTool, StructuredTool
from loguru import logger

# Base path for all agent skills
_AGENT_SKILLS_DIR = Path(__file__).parent

# Brand strategy skills source path
_BRAND_STRATEGY_SKILLS_DIR = _AGENT_SKILLS_DIR / "brand_strategy"


def create_brand_strategy_skills_middleware() -> tuple[
    SkillsMiddleware, FilesystemMiddleware
]:
    """Create SkillsMiddleware + FilesystemMiddleware for brand strategy skills.

    Both middlewares share the same FilesystemBackend (virtual_mode=True,
    read-only). SkillsMiddleware injects skill names + descriptions into
    the system prompt. FilesystemMiddleware provides the read_file tool
    so the agent can actually read SKILL.md content on demand.

    Returns:
        Tuple of (SkillsMiddleware, FilesystemMiddleware).

    Raises:
        FileNotFoundError: If brand strategy skills directory does not exist.
    """
    if not _BRAND_STRATEGY_SKILLS_DIR.exists():
        raise FileNotFoundError(
            f"Brand strategy skills directory not found: {_BRAND_STRATEGY_SKILLS_DIR}"
        )

    # FilesystemBackend with virtual_mode=True for safe read-only access
    backend = FilesystemBackend(
        root_dir=str(_BRAND_STRATEGY_SKILLS_DIR),
        virtual_mode=True,
    )

    # SkillsMiddleware: scans for SKILL.md, injects metadata into system prompt
    skills_middleware = SkillsMiddleware(
        backend=backend,
        sources=["/"],
    )

    # FilesystemMiddleware: provides read_file tool so agent can read SKILL.md
    fs_middleware = FilesystemMiddleware(
        backend=backend,
        tool_token_limit_before_evict=None,
    )

    # Patch grep tool: FilesystemBackend virtual_mode doesn't strip leading /
    # from glob patterns before passing to ripgrep (deepagents<=0.3.12 bug).
    _patch_grep_virtual_glob(fs_middleware)

    logger.info(
        "Brand strategy SkillsMiddleware configured. "
        f"Skills dir: {_BRAND_STRATEGY_SKILLS_DIR}"
    )

    return skills_middleware, fs_middleware


def _patch_grep_virtual_glob(fs_middleware: FilesystemMiddleware) -> None:
    """Patch grep tool to strip leading / from glob patterns.

    deepagents<=0.3.12 passes glob directly to ripgrep without resolving
    virtual paths, so /brand-strategy-orchestrator/*.md won't match.
    """
    original_grep = None
    for t in fs_middleware.tools:
        if t.name == "grep":
            original_grep = t
            break

    if original_grep is None:
        return

    _original_func = cast(StructuredTool, original_grep).func

    @tool(description=GREP_TOOL_DESCRIPTION)
    def grep(
        pattern: str,
        runtime: ToolRuntime[None, FilesystemState],
        path: str | None = None,
        glob: str | None = None,
        output_mode: Literal[
            "files_with_matches", "content", "count"
        ] = "files_with_matches",
    ) -> str:
        """Search for pattern in files (with virtual glob fix)."""
        if glob and glob.startswith("/"):
            glob = glob.lstrip("/")
        assert _original_func is not None
        return _original_func(
            pattern=pattern,
            runtime=runtime,
            path=path,
            glob=glob,
            output_mode=output_mode,
        )

    tools_list = cast(list[BaseTool], fs_middleware.tools)
    for i, t in enumerate(tools_list):
        if t.name == "grep":
            tools_list[i] = grep
            break
