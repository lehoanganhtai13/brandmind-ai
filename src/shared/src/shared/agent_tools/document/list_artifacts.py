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
_REQUIRED_PHASE_5_DELIVERABLES = (
    "brand_key_image",
    "documents",
    "presentations",
    "spreadsheets",
)
_MISSING_DELIVERABLE_GUIDANCE = {
    "brand_key_image": "Brand Key one-pager image via creative-studio",
    "documents": "strategy DOCX via document-generator",
    "presentations": "executive PPTX via document-generator",
    "spreadsheets": "KPI XLSX via document-generator",
}


def phase5_deliverable_key(record: dict) -> str | None:
    """Return the Phase 5 deliverable key represented by a manifest record.

    Phase 5 requires a Brand Key image, not any image. Mood boards and
    exploratory visual drafts remain useful artifacts, but they must not
    satisfy or block the Brand Key one-pager deliverable.
    """
    category = record.get("category")
    if category == "images":
        filename = str(
            record.get("filename") or os.path.basename(record.get("path", ""))
        )
        tool_name = record.get("tool")
        if tool_name == "generate_brand_key" or "brand_key" in filename.lower():
            return "brand_key_image"
        return "other_images"
    if category in {"documents", "presentations", "spreadsheets"}:
        return str(category)
    return None


def _active_session_context() -> tuple[str | None, str | None, str | None]:
    """Return ``(session_id, brand_name, current_phase)`` for the active session.

    Mirrors the late-import pattern used by ``append_manifest`` so the
    ``shared`` package never carries a hard compile-time dependency on
    ``core``. Returns ``(None, None, None)`` when no active session is
    set (CLI / unit tests / ad-hoc invocations) — callers handle this
    by falling back to the broader ``"all"`` scope or returning an
    empty listing.
    """
    try:
        from core.brand_strategy.session import (  # type: ignore[import-not-found]
            get_active_session,
        )
    except ImportError:
        return None, None, None
    session = get_active_session()
    if session is None:
        return None, None, None
    return (
        session.session_id,
        session.brand_name or None,
        getattr(session, "current_phase", None),
    )


def _phase_5_missing_deliverables(matches: list[dict]) -> list[str]:
    """Return required Phase 5 deliverables absent from ``matches``."""
    produced_deliverables = {
        deliverable for r in matches if (deliverable := phase5_deliverable_key(r))
    }
    return [
        deliverable
        for deliverable in _REQUIRED_PHASE_5_DELIVERABLES
        if deliverable not in produced_deliverables
    ]


def _phase_5_closure_summary_lines(matches: list[dict]) -> list[str]:
    """Return the Phase 5 closure status before long artifact listings."""
    produced_deliverables = sorted(
        {deliverable for r in matches if (deliverable := phase5_deliverable_key(r))}
    )
    missing_categories = _phase_5_missing_deliverables(matches)

    lines = [
        f"Produced artifact types this session: {', '.join(produced_deliverables)}",
        f"Required Phase 5 deliverables: {', '.join(_REQUIRED_PHASE_5_DELIVERABLES)}",
    ]
    if missing_categories:
        lines.append(f"Missing required categories: {', '.join(missing_categories)}")
        missing_guidance = "; ".join(
            _MISSING_DELIVERABLE_GUIDANCE[category] for category in missing_categories
        )
        lines.append(
            "CLOSURE_STATUS: INCOMPLETE — do not tell the user Phase 5 is "
            "complete or invent paths for missing categories."
        )
        lines.append(
            "NEXT_ACTION_FOR_FINAL_HANDOFF: if the user already asked for the "
            "final deliverable pack, dispatch only these missing deliverables "
            f"now without asking for confirmation: {missing_guidance}. Then "
            'call list_artifacts(scope="current_session") again.'
        )
    else:
        lines.append("Missing required categories: none")
        lines.append(
            "CLOSURE_STATUS: COMPLETE — all required Phase 5 categories "
            "are present in the current session manifest."
        )
    return lines


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

    session_id, brand_name, current_phase = _active_session_context()
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
    current_session_matches: list[dict] = []
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

                if session_id is not None and record.get("session_id") == session_id:
                    current_session_matches.append(record)

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

    if scope != "current_session" and current_phase == "phase_5":
        missing = _phase_5_missing_deliverables(current_session_matches)
        if missing:
            missing_text = ", ".join(missing)
            current_lines = [
                "CURRENT_SESSION_CLOSURE_REQUIRED: historical artifact scopes "
                f"(scope={scope}) cannot satisfy Phase 5 closure while the "
                f"current session is missing: {missing_text}.",
                'Use `list_artifacts(scope="current_session")` as the closure '
                "authority and generate only the missing current-session "
                "deliverables. Do not reuse or report historical paths as the "
                "final deliverable pack for this session.",
                "",
            ]
            current_lines.extend(
                _phase_5_closure_summary_lines(current_session_matches)
            )
            return "\n".join(current_lines)

    if not matches:
        return f"No artifacts found (scope={scope}, category={category})."

    matches.sort(key=lambda r: r.get("generated_at", ""))

    lines = [
        f"Found {len(matches)} artifact(s) (scope={scope}, category={category}):",
        "",
    ]
    if scope == "current_session":
        lines.extend(_phase_5_closure_summary_lines(matches))
        lines.append("")
    elif current_phase == "phase_5":
        lines.extend(
            [
                "HISTORICAL_ARTIFACT_SCOPE: this listing can support historical "
                "reference only. It is not proof of current-session Phase 5 "
                'completion; use `list_artifacts(scope="current_session")` '
                "for closure.",
                "",
            ]
        )

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

    return "\n".join(lines)
