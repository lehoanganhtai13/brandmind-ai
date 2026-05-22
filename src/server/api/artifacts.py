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

import html
import json
import re
from pathlib import Path
from typing import Literal

import mammoth
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

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

_DispositionOverride = Literal["inline", "attachment"]


class ArtifactRef(BaseModel):
    """Public metadata about one artifact recorded in the manifest.

    Mirrors the manifest record's externally-relevant fields. The
    absolute filesystem path is intentionally omitted so the web UI
    never sees server-side layout; the ``download_url`` is the only
    handle clients need to fetch the bytes. ``size_label`` is a
    pre-formatted short string the UI renders directly so clients do
    not need to repeat the unit logic.
    """

    session_id: str
    brand_name: str
    category: ArtifactCategory
    tool: str
    filename: str
    size_bytes: int
    size_label: str
    generated_at: str
    download_url: str


class DocxTocEntry(BaseModel):
    """One heading in the auto-extracted DOCX table of contents.

    Used by the web canvas pane to render a sticky TOC sidebar that
    anchors into the rendered HTML body. The ``anchor`` value matches
    the ``id`` attribute mammoth assigns to the heading element.
    """

    level: int = Field(ge=1, le=6)
    text: str
    anchor: str


class DocxHtmlResponse(BaseModel):
    """Response body for the inline DOCX → HTML render endpoint.

    Carries the rendered HTML body plus an extracted heading outline so
    the web UI can paint both panels without re-parsing the document on
    the client side. ``warnings`` surfaces mammoth's structural notes
    (unrecognised styles, fallback substitutions) for debug surfaces;
    most production renders return an empty list.
    """

    html: str
    toc: list[DocxTocEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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


def _format_size(size_bytes: int) -> str:
    """Render a byte count as a short ``"38 KB"`` / ``"1.2 MB"`` label.

    The canvas pane shows the value alongside the filename so the user
    can tell at a glance which deliverable is heaviest; the unit is
    chosen automatically so the label stays under five characters
    for the common case.

    Args:
        size_bytes (int): Raw byte count from the manifest record.

    Returns:
        label (str): Compact human-readable size such as ``"512 B"``,
        ``"38 KB"``, or ``"1.2 MB"``.
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes // 1024} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


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

    raw_size = record.get("size_bytes", 0) or 0
    size_bytes = int(raw_size) if isinstance(raw_size, int | float | str) else 0
    return ArtifactRef(
        session_id=session_id,
        brand_name=str(record.get("brand_name", "")),
        category=category,  # type: ignore[arg-type]
        tool=str(record.get("tool", "")),
        filename=filename,
        size_bytes=size_bytes,
        size_label=_format_size(size_bytes),
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
def download_artifact(
    session_id: str,
    filename: str,
    disposition: _DispositionOverride | None = Query(
        default=None,
        description=(
            "Optional override for the response ``Content-Disposition`` "
            "header. When omitted the endpoint serves images as "
            "``inline`` and every other category as ``attachment`` — "
            "the defaults that let the in-canvas image viewer render "
            "via ``<img>`` while binary categories still trigger a "
            "download on direct navigation. Set ``attachment`` from a "
            "download chip to force the browser to save the file even "
            "for image categories where the default would be inline; "
            "this is the cross-origin-safe download mechanism because "
            "the header is authoritative even when the HTML5 "
            "``download`` attribute is stripped by the browser. "
            "``inline`` is accepted symmetrically so a future inline "
            "preview surface for documents would not require a "
            "separate endpoint."
        ),
    ),
) -> FileResponse:
    """Stream a single artifact file by ``(session_id, filename)`` lookup.

    The two URL segments are validated as opaque manifest keys and
    never used to construct a filesystem path. The artifact's absolute
    path is read from the manifest record itself and required to
    resolve under ``$BRANDMIND_OUTPUT_DIR`` before serving — this is
    the defense-in-depth check that catches both ``..`` traversal and
    symlinks pointing outside the base. The ``disposition`` query
    parameter is a presentation-layer override only; it does not
    influence which file is served or who may serve it, so the
    security posture is unchanged from the no-param call.

    Args:
        session_id (str): Session identifier from the URL segment.
        filename (str): Artifact basename from the URL segment.
        disposition (_DispositionOverride | None): Optional explicit
            ``Content-Disposition`` type. When ``None`` (default) the
            endpoint falls back to the per-category default — images
            inline, everything else attachment.

    Returns:
        response (FileResponse): Streamed artifact bytes carrying
            ``Content-Disposition`` set to either the explicit
            ``disposition`` query value (when provided) or the
            per-category default — ``inline`` for images so the
            in-canvas ``<img>`` viewer renders without download
            semantics, ``attachment`` for documents / presentations /
            spreadsheets so direct links trigger a download.

    Raises:
        HTTPException 400: ``session_id`` or ``filename`` fails the
            shape-validation regex.
        HTTPException 404: no manifest record matches the
            ``(session_id, filename)`` pair, the manifest path escapes
            the output root, or the file is missing on disk.
        HTTPException 422: ``disposition`` is present but not one of
            the allowed values — FastAPI rejects the request before
            the handler body runs.
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
    if disposition is not None:
        resolved_disposition = disposition
    elif category in _INLINE_CATEGORIES:
        resolved_disposition = "inline"
    else:
        resolved_disposition = "attachment"
    return FileResponse(
        path=file_path,
        filename=filename,
        content_disposition_type=resolved_disposition,
    )


_HEADING_OPEN_RE = re.compile(
    r"<(h[1-6])(\s[^>]*)?>",
    re.IGNORECASE,
)
_ID_ATTR_RE = re.compile(r'\sid="([^"]+)"', re.IGNORECASE)
_TAG_STRIP_RE = re.compile(r"<[^>]+>")
_NON_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify_anchor(text: str, used: set[str]) -> str:
    """Slugify ``text`` into a URL-fragment-safe id with collision suffixes.

    Mammoth does not emit ``id`` attributes on headings by default, so
    the canvas TOC needs to assign its own anchors that the web UI can
    use as fragment targets. Collisions get a numeric suffix so two
    headings with identical text remain navigable.

    Args:
        text (str): Heading inner text after tag stripping.
        used (set[str]): Anchors already assigned during this render;
            mutated with the returned anchor before returning.

    Returns:
        anchor (str): Lowercase slug safe for use as ``id`` and
            ``href`` fragment, e.g. ``"executive-summary-2"``.
    """
    base = _NON_SLUG_RE.sub("-", text.lower()).strip("-") or "heading"
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def _extract_toc(body: str) -> tuple[str, list[DocxTocEntry]]:
    """Inject anchor ids on every heading and return the matching outline.

    Walks the HTML body in document order, finds each ``<hN>`` opening
    tag, captures the inner text up to the closing tag, and assigns
    a slug-based ``id`` (preserving any explicit ``id`` mammoth or a
    custom style map already produced). Returns the rewritten HTML so
    the rendered body's headings carry stable ids that match the TOC
    entries the canvas pane links to.

    Args:
        body (str): Mammoth-rendered HTML body, raw (no outer wrapper).

    Returns:
        rewritten (str): HTML with ``id`` attributes injected on every
            heading.
        toc (list[DocxTocEntry]): Heading outline in document order.
    """
    if not body:
        return "", []

    entries: list[DocxTocEntry] = []
    used_anchors: set[str] = set()
    rewritten_parts: list[str] = []
    cursor = 0

    for match in _HEADING_OPEN_RE.finditer(body):
        tag = match.group(1).lower()
        attrs = match.group(2) or ""
        close_tag = f"</{tag}>"
        close_idx = body.find(close_tag, match.end())
        if close_idx == -1:
            continue
        inner_html = body[match.end() : close_idx]
        text = html.unescape(_TAG_STRIP_RE.sub("", inner_html).strip())
        if not text:
            continue

        existing_id = _ID_ATTR_RE.search(attrs)
        if existing_id is not None:
            anchor = existing_id.group(1)
            used_anchors.add(anchor)
            new_open = match.group(0)
        else:
            anchor = _slugify_anchor(text, used_anchors)
            new_open = f'<{tag}{attrs} id="{anchor}">'

        rewritten_parts.append(body[cursor : match.start()])
        rewritten_parts.append(new_open)
        cursor = match.end()
        entries.append(
            DocxTocEntry(
                level=int(tag[1]),
                text=text,
                anchor=anchor,
            )
        )

    rewritten_parts.append(body[cursor:])
    return "".join(rewritten_parts), entries


@router.get("/artifacts/{session_id}/{filename}/html")
def render_artifact_html(session_id: str, filename: str) -> DocxHtmlResponse:
    """Render a DOCX artifact as sanitised HTML with an extracted TOC.

    Powers the web UI's inline document viewer — the agent's strategy
    DOCX is converted server-side via ``python-mammoth`` so the client
    container stays JS-light and the HTML is identical whether the user
    is on the CLI launch or the Docker deployment. The endpoint reuses
    the same manifest lookup + path-resolution defence as
    :func:`download_artifact` so a path-traversal attempt cannot reach a
    file outside the artifact root.

    Args:
        session_id (str): Session identifier from the URL segment.
        filename (str): DOCX artifact basename from the URL segment.

    Returns:
        response (DocxHtmlResponse): Rendered HTML body, ordered TOC,
            and any structural warnings mammoth surfaced.

    Raises:
        HTTPException 400: ``session_id`` / ``filename`` fail the
            shape-validation regex, or the artifact is not a DOCX.
        HTTPException 404: no manifest record matches, the manifest
            path escapes the output root, or the file is missing on
            disk.
    """
    if not _SESSION_ID_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id")
    if not _FILENAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=400,
            detail="HTML render is only supported for DOCX artifacts",
        )

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

    with file_path.open("rb") as handle:
        result = mammoth.convert_to_html(handle)

    raw_html = result.value or ""
    html_body, toc = _extract_toc(raw_html)
    warnings = [str(msg) for msg in (result.messages or [])]
    return DocxHtmlResponse(html=html_body, toc=toc, warnings=warnings)
