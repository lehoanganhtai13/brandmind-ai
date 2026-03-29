"""Workspace filesystem management for BrandMind agent persistent memory.

Manages the ~/.brandmind/ directory structure where the brand strategy agent
stores persistent workspace notes — markdown files that survive context
compression and session boundaries.

Architecture:
    ~/.brandmind/
    ├── user/
    │   └── profile.md              ← Global user profile (cross-project)
    ├── projects/
    │   └── {session_id}/
    │       ├── project.json        ← Project metadata
    │       └── workspace/
    │           ├── brand_brief.md  ← SOAP + Progressive Summarization + Golden Thread
    │           ├── working_notes.md ← GTD Inbox + Observations + Reflections
    │           └── quality_gates.md ← Phase checklist + Thread Check
    └── index.json                  ← Project registry for discovery

Design reference: docs/BRANDMIND_WORKSPACE_NOTES_RESEARCH.md (v3.1)

Usage:
    from shared.workspace import ensure_project_workspace

    workspace_dir, user_dir = ensure_project_workspace(
        session_id="abc123",
        brand_name="Cafe Saigon",
    )
    # workspace_dir = Path("~/.brandmind/projects/abc123/workspace")
    # user_dir = Path("~/.brandmind/user")
"""

import json
from datetime import datetime
from pathlib import Path

from loguru import logger

# ============================================================================
# Constants
# ============================================================================

BRANDMIND_HOME = Path.home() / ".brandmind"
"""Root directory for all BrandMind persistent data."""


# ============================================================================
# File Templates
# ============================================================================
# Each template defines the initial structure for a workspace file.
# Templates follow the v3 "Thinking Tool" design from the research doc.
# Agent fills these in progressively — they are NOT data dumps.

BRAND_BRIEF_TEMPLATE = """\
# Brand Brief

## Executive Summary
_Updated each phase. 2-3 sentences capturing the entire strategy state._
_Read this first for instant context restoration._

[Not yet started — will be filled after Phase 0 diagnosis.]

## Golden Thread
_Single chain linking ALL major decisions back to the foundational problem._

Problem → [Phase 0] → ... → [Current Phase]

---

## Phase 0: Business Problem Diagnosis (CURRENT)

### S — What user told us
_User's goals, constraints, preferences, opinions._

### O — What we found
_Research data, metrics, competitive intelligence._

### A — What we concluded
_Agent's analysis, insights, interpretations. Cite evidence: "Based on [O1]..."_
_Include: Alternatives considered + why rejected._

### P — What's next
_Immediate next steps, pending decisions, open questions._
"""

WORKING_NOTES_TEMPLATE = """\
# Working Notes

## Inbox
_Unprocessed items — review at phase transition. Capture anything not yet triaged._

## User Interaction Patterns
_Observations about how this user works. Update at each phase transition._
- Learning speed: [Fast/Medium/Slow at grasping concepts]
- Decision style: [Needs data first / Goes with gut / Wants options]
- Engagement level: [Asks deep questions / Accepts quickly / Challenges often]
- Knowledge gaps: [What topics need more explanation]
- Strengths: [What user already understands well]

## Pending Questions
_Questions posed to user awaiting response. Decisions needing user input._

## Ideas & Hypotheses
_Creative ideas, potential directions, parked suggestions from user._

## Session Reflections
_After each session: what worked, what didn't, user patterns, one lesson._
"""

QUALITY_GATES_TEMPLATE = """\
# Quality Gates

## Phase 0: Business Problem Diagnosis

### Gate Checklist
- [ ] Problem statement clearly defined
- [ ] Scope classified (new_brand / refresh / repositioning / full_rebrand)
- [ ] Brand category and location identified
- [ ] Budget tier understood
- [ ] User confirmed diagnosis

### Thread Check
- Does this phase's output frame the problem clearly? [Pending]
- Will the problem statement guide Phase 1 research direction? [Pending]

### Readiness Assessment
- Confidence: [Pending]
- Known gaps: [None yet]
- Risks: [None yet]
"""

USER_PROFILE_TEMPLATE = """\
# User Profile

## Identity
- Role: [To be discovered]
- Industry expertise: [To be discovered]
- Language: [To be discovered]

## Communication Preferences
_How user prefers to interact — concise vs detailed, data-driven vs intuitive._

## Constraints
_Budget, timeline, team size, tools available, boss expectations._

## Working Style
_Decision speed, risk tolerance, preference for options vs recommendations._
"""


# ============================================================================
# Public API
# ============================================================================


def ensure_project_workspace(
    session_id: str,
    brand_name: str | None = None,
) -> tuple[Path, Path] | tuple[None, None]:
    """Create or verify the workspace directory structure for a project.

    Idempotent: safe to call multiple times. Never overwrites existing files.
    Creates directories and template files only if they don't already exist.

    Args:
        session_id: Unique session identifier used as project directory name.
        brand_name: Optional brand name for metadata (stored in project.json
            and index.json for human readability, not used for directory naming).

    Returns:
        Tuple of (workspace_dir, user_dir) paths if successful.
        Returns (None, None) if directory creation fails (e.g., permission error).

    Example:
        >>> ws_dir, user_dir = ensure_project_workspace("abc123", "Cafe Saigon")
        >>> ws_dir
        PosixPath('/Users/you/.brandmind/projects/abc123/workspace')
    """
    try:
        # Global directories
        user_dir = BRANDMIND_HOME / "user"
        user_dir.mkdir(parents=True, exist_ok=True)

        # Project directories
        project_dir = BRANDMIND_HOME / "projects" / session_id
        workspace_dir = project_dir / "workspace"
        workspace_dir.mkdir(parents=True, exist_ok=True)

        # Initialize template files (never overwrite existing)
        _write_if_absent(workspace_dir / "brand_brief.md", BRAND_BRIEF_TEMPLATE)
        _write_if_absent(workspace_dir / "working_notes.md", WORKING_NOTES_TEMPLATE)
        _write_if_absent(workspace_dir / "quality_gates.md", QUALITY_GATES_TEMPLATE)
        _write_if_absent(user_dir / "profile.md", USER_PROFILE_TEMPLATE)

        # Project metadata
        _write_project_json(project_dir, session_id, brand_name)

        # Update global index
        _update_index(session_id, brand_name)

        logger.info(
            f"Workspace ready: {workspace_dir} (brand={brand_name or 'unnamed'})"
        )
        return workspace_dir, user_dir

    except PermissionError:
        logger.warning(
            f"Permission denied creating workspace at {BRANDMIND_HOME}. "
            "Workspace notes will not be available this session."
        )
        return None, None
    except OSError as e:
        logger.warning(
            f"Failed to create workspace at {BRANDMIND_HOME}: {e}. "
            "Workspace notes will not be available this session."
        )
        return None, None


# ============================================================================
# Internal Helpers
# ============================================================================


def _write_if_absent(path: Path, content: str) -> None:
    """Write content to file only if file does not already exist.

    This ensures idempotency — calling ensure_project_workspace() multiple
    times never overwrites user or agent edits to workspace files.
    """
    if not path.exists():
        path.write_text(content, encoding="utf-8")
        logger.debug(f"Created template: {path.name}")


def _write_project_json(
    project_dir: Path,
    session_id: str,
    brand_name: str | None,
) -> None:
    """Write or update project.json metadata file.

    Updates brand_name if it changed (e.g., set during Phase 0).
    Other fields are write-once.
    """
    meta_path = project_dir / "project.json"
    if meta_path.exists():
        existing = json.loads(meta_path.read_text(encoding="utf-8"))
        # Update brand_name if newly provided
        if brand_name and existing.get("brand_name") != brand_name:
            existing["brand_name"] = brand_name
            existing["updated_at"] = datetime.now().isoformat()
            meta_path.write_text(
                json.dumps(existing, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
    else:
        meta = {
            "session_id": session_id,
            "brand_name": brand_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        meta_path.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def _update_index(session_id: str, brand_name: str | None) -> None:
    """Update the global project index at ~/.brandmind/index.json.

    Index maps session_id to brand_name for human discoverability.
    """
    index_path = BRANDMIND_HOME / "index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        index = {"projects": {}}

    index["projects"][session_id] = {
        "brand_name": brand_name,
        "updated_at": datetime.now().isoformat(),
    }

    index_path.write_text(
        json.dumps(index, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
