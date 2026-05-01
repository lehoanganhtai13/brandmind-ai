"""Sandbox + manifest helpers for artifact-output paths.

Two responsibilities:

* :func:`resolve_output_path` — anchors every artifact written by the
  four generation tools (``generate_document``,
  ``generate_presentation``, ``generate_spreadsheet``,
  ``export_to_markdown``) under
  ``$BRANDMIND_OUTPUT_DIR/<category>/<brand_slug>/<timestamp>_<filename>``.
  Per-brand subdirectories keep one brand's artifacts together; the
  timestamp prefix prevents collisions across repeated runs. Paths
  outside the configured base are redirected back into the per-brand
  subdir so bare filenames cannot land at the repo root.
* :func:`append_manifest` — append-only JSONL writer for
  ``$BRANDMIND_OUTPUT_DIR/.manifest.jsonl``. Each record carries
  session id, brand, category, tool, filename, absolute path, size, and
  timestamp. The orchestrator reads it through the ``list_artifacts``
  tool to verify what the current session has produced.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any


def _base_dir() -> str:
    """Return the absolute path of the artifact-output root.

    Reads ``BRANDMIND_OUTPUT_DIR``, falling back to
    ``<cwd>/brandmind-output`` so an unconfigured server still writes
    under the repository workspace instead of leaking to the process
    cwd.
    """
    return os.path.abspath(
        os.environ.get(
            "BRANDMIND_OUTPUT_DIR",
            os.path.join(os.getcwd(), "brandmind-output"),
        )
    )


def _slugify_brand(brand_name: str) -> str:
    """Normalise ``brand_name`` into a filesystem-friendly subdir name.

    Collapses any run of non-ASCII-alphanumeric characters (spaces,
    diacritics, punctuation) into a single hyphen so brand inputs
    produce a stable subdir key. Falls back to ``"brand"`` when the
    result is empty so artifacts always land in some per-brand subdir.
    """
    if not brand_name:
        return "brand"
    slug = re.sub(r"[^A-Za-z0-9_]+", "-", brand_name.strip().lower()).strip("-")
    return slug or "brand"


def _timestamp() -> str:
    """Return a sortable timestamp suffix for artifact filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def resolve_output_path(
    provided: str | None,
    *,
    category: str,
    brand_name: str,
    default_filename: str,
) -> str:
    """Return a safe absolute output path for an artifact.

    Layout:
        ``$BRANDMIND_OUTPUT_DIR/<category>/<brand_slug>/<timestamp>_<filename>``

    Per-brand subdirectories preserve the user's cross-session workspace
    (artifacts for one brand stay together, never co-mingle with another
    brand's files). The timestamp prefix prevents collisions across
    repeated runs for the same brand and produces a chronologically
    sortable history the user can browse in Finder/Explorer.

    Args:
        provided: The ``output_path`` argument the tool received from
            the agent. May be ``None``, an absolute path, or a relative
            path. When ``None`` the tool produces a fresh
            timestamp+brand-slug path. When supplied and already under
            ``$BRANDMIND_OUTPUT_DIR``, the value is honoured as-is. When
            supplied but outside the base, the basename is reused under
            the default category+brand subdirectory.
        category: Subdirectory inside the base directory that this
            artifact type belongs to (``"documents"``, ``"presentations"``,
            ``"spreadsheets"``, ``"images"``).
        brand_name: Brand identifier used to derive the per-brand
            subdirectory. Empty / falsy values fall back to ``"brand"``.
        default_filename: Filename the tool would emit if the agent did
            not pass ``output_path``. The timestamp prefix is added on
            top of this name.

    Returns:
        An absolute path. The parent directory is guaranteed to exist
        on return.
    """
    base = _base_dir()
    brand_slug = _slugify_brand(brand_name)
    target_dir = os.path.join(base, category, brand_slug)
    os.makedirs(target_dir, exist_ok=True)

    if not provided:
        return os.path.join(target_dir, f"{_timestamp()}_{default_filename}")

    candidate = os.path.abspath(provided)
    # Honour the agent's path only when it is already under the
    # configured base directory — otherwise reuse the basename under
    # the default category+brand subdirectory so the artifact cannot
    # land at the repo root or any other unrelated location.
    if candidate.startswith(base + os.sep) or candidate == base:
        os.makedirs(os.path.dirname(candidate), exist_ok=True)
        return candidate

    fallback_name = os.path.basename(candidate) or default_filename
    return os.path.join(target_dir, f"{_timestamp()}_{fallback_name}")


def _manifest_path() -> str:
    """Return the absolute path of the manifest JSONL file."""
    return os.path.join(_base_dir(), ".manifest.jsonl")


def _current_session_id() -> str:
    """Return the active session id, or ``"unbound"`` when none is set.

    Uses a late import so ``shared`` does not take a compile-time
    dependency on ``core``; CLI / unit-test / ad-hoc callers without an
    active session get the sentinel ``"unbound"`` and the manifest
    still records every artifact.
    """
    try:
        from core.brand_strategy.session import (  # type: ignore[import-not-found]
            get_active_session,
        )
    except ImportError:
        return "unbound"
    session = get_active_session()
    if session is None:
        return "unbound"
    return session.session_id


def append_manifest(
    *,
    brand_name: str,
    category: str,
    tool: str,
    path: str,
) -> None:
    """Record one artifact production in the append-only JSONL manifest.

    Each line carries ``session_id``, ``brand_name``, ``category``,
    ``tool``, ``filename``, absolute ``path``, ``size_bytes``, and
    ISO-8601 ``generated_at``. The :func:`list_artifacts` tool consumes
    this file so the orchestrator can answer "what has the current
    session produced" without filesystem-level visibility into the
    output directory. Manifest writes are best-effort: an OSError is
    swallowed so the user-facing artifact delivery is never blocked by
    a provenance failure.

    Args:
        brand_name: User-supplied brand identifier; recorded verbatim
            so the manifest keeps the original (the on-disk subdir
            uses the slugified form).
        category: One of ``"documents"``, ``"presentations"``,
            ``"spreadsheets"``, ``"images"``.
        tool: Name of the producing tool (e.g. ``"generate_document"``).
        path: Absolute filesystem path the artifact was written to.
    """
    record: dict[str, Any] = {
        "session_id": _current_session_id(),
        "brand_name": brand_name,
        "category": category,
        "tool": tool,
        "filename": os.path.basename(path),
        "path": path,
        "size_bytes": os.path.getsize(path) if os.path.exists(path) else 0,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    manifest_file = _manifest_path()
    os.makedirs(os.path.dirname(manifest_file), exist_ok=True)
    try:
        with open(manifest_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        # Provenance is best-effort: a missing manifest line never
        # blocks artifact delivery. The agent's user-facing message
        # already names the file produced.
        return
