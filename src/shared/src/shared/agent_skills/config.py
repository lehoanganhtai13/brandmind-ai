"""Configuration for Agent Skills using DeepAgents built-in SkillsMiddleware.

Provides factory functions to create pre-configured SkillsMiddleware
instances for different agent domains. Uses progressive disclosure pattern:
agent sees skill name + description in system prompt, reads full SKILL.md
on-demand via FilesystemMiddleware.

Architecture (with workspace):
    CompositeBackend
    ├── default: skills FilesystemBackend (read-only, virtual_mode=True)
    │   └── brand-strategy-orchestrator/SKILL.md, market-research/SKILL.md, ...
    ├── route "/workspace/" → workspace FilesystemBackend (read-write)
    │   └── ~/.brandmind/projects/{session_id}/workspace/
    └── route "/user/" → user FilesystemBackend (read-write)
        └── ~/.brandmind/user/

Architecture (without workspace — backward compatible):
    FilesystemBackend (read-only, virtual_mode=True)
    └── brand-strategy-orchestrator/SKILL.md, ...

Usage:
    from shared.agent_skills import create_brand_strategy_skills_middleware

    # With workspace (normal brand strategy session)
    skills_mw, fs_mw = create_brand_strategy_skills_middleware(
        workspace_dir="/path/to/workspace",
        user_dir="/path/to/user",
    )

    # Without workspace (backward compatible, tests)
    skills_mw, fs_mw = create_brand_strategy_skills_middleware()
"""

from pathlib import Path
from typing import Literal, cast

from deepagents.backends.composite import CompositeBackend
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


def create_brand_strategy_skills_middleware(
    workspace_dir: str | None = None,
    user_dir: str | None = None,
) -> tuple[SkillsMiddleware, FilesystemMiddleware]:
    """Create SkillsMiddleware + FilesystemMiddleware for brand strategy agent.

    When workspace_dir and user_dir are provided, creates a CompositeBackend
    that routes paths to three separate backends:
    - Default (no prefix): skills directory (read-only)
    - "/workspace/": project workspace notes (read-write)
    - "/user/": global user profile (read-write)

    When not provided, falls back to skills-only backend (backward compatible).

    Args:
        workspace_dir: Path to project workspace directory on disk.
            When provided, enables read-write access via "/workspace/" prefix.
        user_dir: Path to global user profile directory on disk.
            When provided, enables read-write access via "/user/" prefix.

    Returns:
        Tuple of (SkillsMiddleware, FilesystemMiddleware).

    Raises:
        FileNotFoundError: If brand strategy skills directory does not exist.
    """
    if not _BRAND_STRATEGY_SKILLS_DIR.exists():
        raise FileNotFoundError(
            f"Brand strategy skills directory not found: {_BRAND_STRATEGY_SKILLS_DIR}"
        )

    # Skills backend: always present, read-only
    skills_backend = FilesystemBackend(
        root_dir=str(_BRAND_STRATEGY_SKILLS_DIR),
        virtual_mode=True,
    )

    # Determine backend: CompositeBackend if workspace provided, else skills-only
    backend: CompositeBackend | FilesystemBackend
    if workspace_dir and user_dir:
        workspace_backend = FilesystemBackend(
            root_dir=workspace_dir,
            virtual_mode=True,
        )
        user_backend = FilesystemBackend(
            root_dir=user_dir,
            virtual_mode=True,
        )
        backend = CompositeBackend(
            default=skills_backend,
            routes={
                "/workspace/": workspace_backend,
                "/user/": user_backend,
            },
        )
        logger.info(
            f"CompositeBackend configured: skills (read-only) + "
            f"workspace ({workspace_dir}) + user ({user_dir})"
        )
    else:
        backend = skills_backend
        logger.info(
            "Skills-only backend configured (no workspace). "
            f"Skills dir: {_BRAND_STRATEGY_SKILLS_DIR}"
        )

    # SkillsMiddleware: scans for SKILL.md, injects metadata into system prompt
    skills_middleware = SkillsMiddleware(
        backend=backend,
        sources=["/"],
    )

    # FilesystemMiddleware: provides read_file, write_file, edit_file, etc.
    fs_middleware = FilesystemMiddleware(
        backend=backend,
        tool_token_limit_before_evict=None,
    )

    # Patch grep tool for virtual_mode glob bug (deepagents<=0.3.12)
    _patch_grep_virtual_glob(fs_middleware)

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
