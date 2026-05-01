"""Sandbox helper that anchors artifact output paths under BRANDMIND_OUTPUT_DIR.

The three artifact-generation tools (generate_document, generate_presentation,
generate_spreadsheet) all accept an optional ``output_path`` argument. In
production, sub-agents have been observed to pass bare filenames such as
``"strategy_signature.docx"``, which the underlying builders then write to the
process's current working directory — usually the repository root. That leaks
artifacts outside the configured output directory and pollutes the repo.

This helper enforces a single rule:

    Every artifact written by a generate_* tool ends up under
    ``$BRANDMIND_OUTPUT_DIR/<category>/`` regardless of what the agent passed
    for ``output_path``.

If the agent supplies a path that already resolves under the configured base
directory, it is honoured. Otherwise its basename is reused under the default
category subdirectory; the tool never silently writes elsewhere.
"""

from __future__ import annotations

import os


def _base_dir() -> str:
    """Return the configured BRANDMIND_OUTPUT_DIR root (absolute)."""
    return os.path.abspath(
        os.environ.get(
            "BRANDMIND_OUTPUT_DIR",
            os.path.join(os.getcwd(), "brandmind-output"),
        )
    )


def resolve_output_path(
    provided: str | None,
    *,
    category: str,
    default_filename: str,
) -> str:
    """Return a safe absolute output path anchored under BRANDMIND_OUTPUT_DIR.

    Args:
        provided: The ``output_path`` argument the tool received from the
            agent. May be ``None``, an absolute path, or a relative path.
        category: Subdirectory inside the base directory that this artifact
            type belongs to (e.g. ``"documents"``, ``"presentations"``,
            ``"spreadsheets"``). The directory is created if missing.
        default_filename: Filename used when ``provided`` is ``None`` or
            cannot be honoured safely.

    Returns:
        An absolute path under ``$BRANDMIND_OUTPUT_DIR/<category>/``. The
        parent directory is guaranteed to exist on return.
    """
    base = _base_dir()
    target_dir = os.path.join(base, category)
    os.makedirs(target_dir, exist_ok=True)

    if not provided:
        return os.path.join(target_dir, default_filename)

    candidate = os.path.abspath(provided)
    # Honour the agent's path only when it is already under the configured
    # base directory — otherwise reuse the basename under the default
    # category subdirectory so the artifact cannot land at the repo root or
    # any other unrelated location.
    if candidate.startswith(base + os.sep) or candidate == base:
        os.makedirs(os.path.dirname(candidate), exist_ok=True)
        return candidate

    fallback_name = os.path.basename(candidate) or default_filename
    return os.path.join(target_dir, fallback_name)
