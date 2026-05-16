"""Artifact-serving endpoints for the BrandMind web UI.

Two stateless endpoints exposing the artifact manifest produced by the
brand-strategy workflow:

* ``GET /sessions/{session_id}/artifacts`` — list every artifact
  recorded in ``$BRANDMIND_OUTPUT_DIR/.manifest.jsonl`` for the given
  session, as structured metadata the web UI uses to populate its
  artifact panel.
* ``GET /artifacts/{session_id}/{filename}`` — stream a single artifact
  file by manifest lookup. The URL path segments are validated as
  opaque keys (never used to construct a filesystem path), and the
  file the manifest points at is resolved and required to stay under
  the configured output root before serving. These two checks together
  defeat path-traversal attempts (``..``, absolute paths, symlinks
  escaping the base).

Stateless by design — no active session, no SessionManager
dependency — so the web UI can browse historical session artifacts
even when the brand-strategy agent is not running.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from shared.agent_tools.document._output_path import _base_dir, _manifest_path

router = APIRouter(tags=["artifacts"])

_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
# Filename must start with a word character (Unicode-aware via ``\w``) so leading
# ``.`` or ``-`` cannot smuggle a traversal token. Body chars allow Unicode word
# characters, ``.``, ``-`` so Vietnamese diacritics in real brand-name-derived
# filenames (e.g. ``brand_key_an_privée.jpeg``) are accepted while ``/`` and
# control characters remain blocked.
_FILENAME_RE = re.compile(
    r"^\w[\w.\-]*\.(docx|pptx|xlsx|png|jpg|jpeg|webp)$",
    re.UNICODE,
)
_INLINE_CATEGORIES = {"images"}

ArtifactCategory = Literal["documents", "presentations", "spreadsheets", "images"]


class ArtifactRef(BaseModel):
    """Public metadata about one artifact recorded in the manifest.

    Mirrors the manifest record's externally-relevant fields. The
    absolute filesystem path is intentionally omitted so the web UI
    never sees server-side layout; the ``download_url`` is the only
    handle clients need to fetch the bytes.
    """

    session_id: str
    brand_name: str
    category: ArtifactCategory
    tool: str
    filename: str
    size_bytes: int
    generated_at: str
    download_url: str


def _iter_manifest_records() -> list[dict[str, object]]:
    """Read every parseable record from the artifact manifest.

    Manifest writes are best-effort and append-only; malformed lines
    are skipped without raising so a single corrupt line never blanks
    out the artifact panel. Returns an empty list when the manifest
    file does not exist yet (no artifacts have ever been produced).

    Returns:
        records (list[dict[str, object]]): One dict per valid JSONL
            line, preserving file order.
    """
    manifest_file = Path(_manifest_path())
    if not manifest_file.is_file():
        return []

    records: list[dict[str, object]] = []
    with manifest_file.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def _record_to_ref(record: dict[str, object]) -> ArtifactRef | None:
    """Project a manifest record into an ``ArtifactRef`` for the API.

    Returns ``None`` when the record is missing required fields or the
    ``category`` value falls outside the four supported artifact types
    — those records exist on disk but cannot be surfaced through the
    web UI's typed schema.

    Args:
        record (dict[str, object]): One parsed JSONL line from the
            manifest.

    Returns:
        ref (ArtifactRef | None): The typed projection, or ``None``
            when the record cannot be safely surfaced.
    """
    category = record.get("category")
    if category not in {"documents", "presentations", "spreadsheets", "images"}:
        return None

    session_id = str(record.get("session_id", ""))
    filename = str(record.get("filename", ""))
    if not session_id or not filename:
        return None

    return ArtifactRef(
        session_id=session_id,
        brand_name=str(record.get("brand_name", "")),
        category=category,  # type: ignore[arg-type]
        tool=str(record.get("tool", "")),
        filename=filename,
        size_bytes=int(record.get("size_bytes", 0) or 0),
        generated_at=str(record.get("generated_at", "")),
        download_url=f"/api/v1/artifacts/{session_id}/{filename}",
    )


def _find_manifest_record(session_id: str, filename: str) -> dict[str, object] | None:
    """Return the latest manifest record matching the key pair.

    Reads the manifest top-to-bottom and keeps the last match, so if a
    tool ever re-emits the same filename for the same session the
    freshest entry wins. Returns ``None`` when no record matches.

    Args:
        session_id (str): Session identifier from the URL.
        filename (str): Artifact basename from the URL.

    Returns:
        record (dict[str, object] | None): The latest matching record,
            or ``None`` when no match exists.
    """
    latest: dict[str, object] | None = None
    for record in _iter_manifest_records():
        if str(record.get("session_id", "")) != session_id:
            continue
        if str(record.get("filename", "")) != filename:
            continue
        latest = record
    return latest


@router.get("/sessions/{session_id}/artifacts")
def list_session_artifacts(session_id: str) -> list[ArtifactRef]:
    """List every artifact recorded for ``session_id`` in the manifest.

    Returns an empty list (HTTP 200) when the session has no manifest
    entries — there is no concept of "session not found" here, since
    the manifest is the only state this endpoint reads and an unknown
    session id is indistinguishable from a session that produced
    nothing. Records sort by ``generated_at`` ascending so the UI can
    render them in production order without re-sorting.

    Args:
        session_id (str): The session identifier as recorded in the
            manifest. Validated against a strict regex to reject path
            traversal attempts.

    Returns:
        refs (list[ArtifactRef]): Zero or more typed artifact
            references, ordered oldest to newest.

    Raises:
        HTTPException 400: ``session_id`` fails the shape-validation
            regex.
    """
    if not _SESSION_ID_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id")

    refs: list[ArtifactRef] = []
    for record in _iter_manifest_records():
        if str(record.get("session_id", "")) != session_id:
            continue
        ref = _record_to_ref(record)
        if ref is not None:
            refs.append(ref)
    refs.sort(key=lambda r: r.generated_at)
    return refs


@router.get("/artifacts/{session_id}/{filename}")
def download_artifact(session_id: str, filename: str) -> FileResponse:
    """Stream a single artifact file by ``(session_id, filename)`` lookup.

    The two URL segments are validated as opaque manifest keys and
    never used to construct a filesystem path. The artifact's absolute
    path is read from the manifest record itself and required to
    resolve under ``$BRANDMIND_OUTPUT_DIR`` before serving — this is
    the defense-in-depth check that catches both ``..`` traversal and
    symlinks pointing outside the base.

    Args:
        session_id (str): Session identifier from the URL segment.
        filename (str): Artifact basename from the URL segment.

    Returns:
        response (FileResponse): Streamed artifact bytes. ``images``
            are served with ``inline`` content disposition so they
            render in ``<img>`` tags; every other category uses the
            FastAPI default ``attachment`` disposition so direct links
            trigger a download.

    Raises:
        HTTPException 400: ``session_id`` or ``filename`` fails the
            shape-validation regex.
        HTTPException 404: no manifest record matches the
            ``(session_id, filename)`` pair, the manifest path escapes
            the output root, or the file is missing on disk.
    """
    if not _SESSION_ID_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id")
    if not _FILENAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    record = _find_manifest_record(session_id, filename)
    if record is None:
        raise HTTPException(status_code=404, detail="Artifact not found")

    file_path = Path(str(record.get("path", ""))).resolve()
    base = Path(_base_dir()).resolve()
    try:
        file_path.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=404, detail="Artifact not found")

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Artifact file missing on disk")

    category = str(record.get("category", ""))
    disposition = "inline" if category in _INLINE_CATEGORIES else "attachment"
    return FileResponse(
        path=file_path,
        filename=filename,
        content_disposition_type=disposition,
    )
