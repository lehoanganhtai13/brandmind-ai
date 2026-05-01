"""list_artifacts tool — query produced artifacts via the manifest.

The orchestrator cannot meaningfully ``read_file`` binary artifacts
(DOCX/PPTX/XLSX) and the sub-agent's ``FILE saved`` confirmation lives
inside the sub-agent's own context, not the main agent's. This tool
closes the gap: it reads the append-only JSONL manifest written by
:func:`shared.agent_tools.document._output_path.append_manifest` and
returns a structured listing of artifacts the orchestrator can use to
verify what the current session has produced before declaring Phase 5
complete.
"""

from __future__ import annotations

import json
import os
from typing import Literal

from loguru import logger

from ._output_path import _base_dir, _manifest_path

_VALID_SCOPES = ("current_session", "current_brand", "all")
_VALID_CATEGORIES = ("documents", "presentations", "spreadsheets", "images", "all")


def _active_session_context() -> tuple[str | None, str | None]:
    """Return ``(session_id, brand_name)`` of the active session, if any.

    Mirrors the late-import pattern used by ``append_manifest`` so the
    ``shared`` package never carries a hard compile-time dependency on
    ``core``. Returns ``(None, None)`` when no active session is set
    (CLI / unit tests / ad-hoc invocations) — callers handle this by
    falling back to the broader ``"all"`` scope or returning an empty
    listing.
    """
    try:
        from core.brand_strategy.session import (  # type: ignore[import-not-found]
            get_active_session,
        )
    except ImportError:
        return None, None
    session = get_active_session()
    if session is None:
        return None, None
    return session.session_id, session.brand_name or None


def list_artifacts(
    scope: Literal["current_session", "current_brand", "all"] = "current_session",
    category: Literal[
        "documents", "presentations", "spreadsheets", "images", "all"
    ] = "all",
) -> str:
    """Inspect artifact files produced by the artifact-generation tools.

    Use when verifying which deliverable files have been produced — at
    Phase 5 closure to confirm all four artifact categories
    (``images`` for the Brand Key, ``documents`` for the strategy
    write-up, ``presentations`` for the executive deck,
    ``spreadsheets`` for KPI tracking) are present, mid-session to
    check what is already done before re-dispatching, or any time the
    user asks for a status of generated files.

    Do NOT use this to read artifact bodies (binary files cannot be
    read meaningfully — describe contents from the conversation's
    tool-result messages instead) and do NOT use it to plan future
    content (that lives in ``/workspace/``).

    Args:
        scope: ``"current_session"`` (default) returns artifacts
            produced in this conversation only — the answer Phase 5
            closure should consult. ``"current_brand"`` returns the
            full history for the active brand across sessions, useful
            when the user asks "what have we produced for this brand
            so far". ``"all"`` returns every recorded artifact.
        category: Filter by artifact type, or ``"all"`` for every type.

    Returns:
        Human-readable listing — one artifact per line with brand,
        category, filename, generation timestamp, size in KB, and the
        absolute filesystem path the user can open in
        Word/PowerPoint/Excel/Finder. Returns
        ``"No artifacts found"`` (with the active filter) when the
        manifest has no matching records.
    """
    if scope not in _VALID_SCOPES:
        return f"Invalid scope '{scope}'. Valid scopes: {', '.join(_VALID_SCOPES)}."
    if category not in _VALID_CATEGORIES:
        return (
            f"Invalid category '{category}'. "
            f"Valid categories: {', '.join(_VALID_CATEGORIES)}."
        )

    manifest_file = _manifest_path()
    if not os.path.exists(manifest_file):
        return (
            f"No artifacts found (scope={scope}, category={category}). "
            f"Manifest does not exist yet — no artifact has been produced "
            f"under {_base_dir()}."
        )

    session_id, brand_name = _active_session_context()
    if scope == "current_session" and session_id is None:
        return (
            "No active brand strategy session — cannot resolve "
            "scope='current_session'. Re-run with scope='all' or "
            "scope='current_brand' if you only need a global listing."
        )
    if scope == "current_brand" and not brand_name:
        return (
            "Active session has no brand_name set yet — cannot resolve "
            "scope='current_brand'. Set brand_name via "
            "report_progress(brand_name=...) first, or use "
            "scope='all' for a global listing."
        )

    matches: list[dict] = []
    try:
        with open(manifest_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if category != "all" and record.get("category") != category:
                    continue

                if scope == "current_session":
                    if record.get("session_id") != session_id:
                        continue
                elif scope == "current_brand":
                    if record.get("brand_name") != brand_name:
                        continue

                matches.append(record)
    except OSError as exc:
        logger.error(f"list_artifacts: failed to read manifest: {exc}")
        return f"Failed to read manifest at {manifest_file}: {exc}"

    if not matches:
        return f"No artifacts found (scope={scope}, category={category})."

    matches.sort(key=lambda r: r.get("generated_at", ""))

    lines = [
        f"Found {len(matches)} artifact(s) (scope={scope}, category={category}):",
        "",
    ]
    for record in matches:
        size_kb = record.get("size_bytes", 0) / 1024
        lines.append(
            f"- [{record.get('category', '?')}] "
            f"{record.get('filename', '?')}\n"
            f"    brand: {record.get('brand_name', '?')}\n"
            f"    generated_at: {record.get('generated_at', '?')}\n"
            f"    size: {size_kb:.1f} KB\n"
            f"    path: {record.get('path', '?')}"
        )

    if scope == "current_session":
        # Surface category coverage explicitly so the orchestrator can
        # check Phase 5 closure without re-parsing the listing.
        produced_categories = sorted({r.get("category", "?") for r in matches})
        lines.append("")
        lines.append(
            f"Categories produced this session: {', '.join(produced_categories)}"
        )

    return "\n".join(lines)
