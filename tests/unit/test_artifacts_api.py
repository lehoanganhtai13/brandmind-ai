"""Unit tests for the artifact-serving API endpoints.

Covers manifest parsing, session filtering, response shape, path-
traversal defense (URL regex + manifest containment), and file
streaming. Uses FastAPI's ``TestClient`` against ``create_app()`` and
a per-test temporary ``BRANDMIND_OUTPUT_DIR`` so the manifest path
resolution and containment check operate inside an isolated tree.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.main import create_app


@pytest.fixture
def output_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Path]:
    """Point ``BRANDMIND_OUTPUT_DIR`` at a clean per-test directory.

    ``_base_dir()`` re-reads the environment on every call, so the
    monkeypatch propagates into the lazy lookups performed inside the
    request handlers. The output root is a sub-directory of
    ``tmp_path`` so tests can place files outside it to verify the
    containment defense.
    """
    root = tmp_path / "brandmind-output"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(root))
    yield root


@pytest.fixture
def client(output_root: Path) -> Iterator[TestClient]:
    """FastAPI TestClient bound to the temporary output directory."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def _write_manifest(
    output_root: Path, records: list[dict[str, object]]
) -> None:
    """Write one JSONL line per record to the manifest file."""
    manifest = output_root / ".manifest.jsonl"
    with manifest.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def _stub_artifact(output_root: Path, category: str, filename: str) -> Path:
    """Create a small binary file under ``<category>/brand/`` and return it."""
    target = output_root / category / "brand" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"FAKE_BINARY_PAYLOAD")
    return target


class TestListSessionArtifacts:
    """Behavior of ``GET /api/v1/sessions/{session_id}/artifacts``."""

    def test_returns_empty_when_manifest_missing(
        self, client: TestClient
    ) -> None:
        resp = client.get("/api/v1/sessions/abc123/artifacts")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_filters_by_session_id(
        self, client: TestClient, output_root: Path
    ) -> None:
        path_a = _stub_artifact(output_root, "documents", "a.docx")
        path_b = _stub_artifact(output_root, "documents", "b.docx")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "a.docx",
                    "path": str(path_a),
                    "size_bytes": 100,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                },
                {
                    "session_id": "s_beta",
                    "brand_name": "Beta",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "b.docx",
                    "path": str(path_b),
                    "size_bytes": 200,
                    "generated_at": "2026-05-16T10:01:00+07:00",
                },
            ],
        )

        resp = client.get("/api/v1/sessions/s_alpha/artifacts")
        assert resp.status_code == 200
        payload = resp.json()
        assert len(payload) == 1
        assert payload[0]["session_id"] == "s_alpha"
        assert payload[0]["filename"] == "a.docx"
        assert payload[0]["download_url"] == "/api/v1/artifacts/s_alpha/a.docx"

    def test_skips_unknown_categories_and_malformed_lines(
        self, client: TestClient, output_root: Path
    ) -> None:
        path_doc = _stub_artifact(output_root, "documents", "ok.docx")
        manifest = output_root / ".manifest.jsonl"
        manifest.write_text(
            json.dumps(
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "ok.docx",
                    "path": str(path_doc),
                    "size_bytes": 100,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            )
            + "\n"
            + "this-is-not-json\n"
            + json.dumps(
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "scratch",
                    "tool": "some_tool",
                    "filename": "x.txt",
                    "path": str(output_root / "scratch" / "x.txt"),
                    "size_bytes": 0,
                    "generated_at": "2026-05-16T10:02:00+07:00",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        resp = client.get("/api/v1/sessions/s_alpha/artifacts")
        assert resp.status_code == 200
        payload = resp.json()
        assert len(payload) == 1
        assert payload[0]["category"] == "documents"

    def test_rejects_invalid_session_id_shape(
        self, client: TestClient
    ) -> None:
        resp = client.get("/api/v1/sessions/abc..123/artifacts")
        assert resp.status_code == 400

    def test_orders_by_generated_at_ascending(
        self, client: TestClient, output_root: Path
    ) -> None:
        path_a = _stub_artifact(output_root, "documents", "early.docx")
        path_b = _stub_artifact(output_root, "documents", "late.docx")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "late.docx",
                    "path": str(path_b),
                    "size_bytes": 1,
                    "generated_at": "2026-05-16T11:00:00+07:00",
                },
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "early.docx",
                    "path": str(path_a),
                    "size_bytes": 1,
                    "generated_at": "2026-05-16T09:00:00+07:00",
                },
            ],
        )
        resp = client.get("/api/v1/sessions/s_alpha/artifacts")
        names = [item["filename"] for item in resp.json()]
        assert names == ["early.docx", "late.docx"]


class TestDownloadArtifact:
    """Behavior of ``GET /api/v1/artifacts/{session_id}/{filename}``."""

    def test_streams_valid_artifact(
        self, client: TestClient, output_root: Path
    ) -> None:
        path = _stub_artifact(output_root, "documents", "strategy.docx")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "strategy.docx",
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_alpha/strategy.docx")
        assert resp.status_code == 200
        assert resp.content == b"FAKE_BINARY_PAYLOAD"

    def test_inline_disposition_for_images(
        self, client: TestClient, output_root: Path
    ) -> None:
        path = _stub_artifact(output_root, "images", "brand_key.png")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "images",
                    "tool": "generate_brand_key",
                    "filename": "brand_key.png",
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_alpha/brand_key.png")
        assert resp.status_code == 200
        assert "inline" in resp.headers.get("content-disposition", "")

    def test_attachment_disposition_for_pptx(
        self, client: TestClient, output_root: Path
    ) -> None:
        path = _stub_artifact(output_root, "presentations", "deck.pptx")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "presentations",
                    "tool": "generate_presentation",
                    "filename": "deck.pptx",
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_alpha/deck.pptx")
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("content-disposition", "")

    def test_404_when_session_id_unknown(
        self, client: TestClient, output_root: Path
    ) -> None:
        path = _stub_artifact(output_root, "documents", "strategy.docx")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "strategy.docx",
                    "path": str(path),
                    "size_bytes": 1,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_unknown/strategy.docx")
        assert resp.status_code == 404

    def test_404_when_filename_not_in_manifest(
        self, client: TestClient, output_root: Path
    ) -> None:
        path = _stub_artifact(output_root, "documents", "real.docx")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "real.docx",
                    "path": str(path),
                    "size_bytes": 1,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_alpha/forged.docx")
        assert resp.status_code == 404

    def test_400_on_traversal_filename(self, client: TestClient) -> None:
        resp = client.get("/api/v1/artifacts/s_alpha/..passwd")
        assert resp.status_code == 400

    def test_400_on_unsafe_extension(self, client: TestClient) -> None:
        resp = client.get("/api/v1/artifacts/s_alpha/script.sh")
        assert resp.status_code == 400

    def test_400_on_invalid_session_id(self, client: TestClient) -> None:
        resp = client.get("/api/v1/artifacts/bad..sid/file.docx")
        assert resp.status_code == 400

    def test_404_when_manifest_path_escapes_base(
        self,
        client: TestClient,
        output_root: Path,
        tmp_path: Path,
    ) -> None:
        outside = tmp_path / "outside-evil" / "evil.docx"
        outside.parent.mkdir(parents=True, exist_ok=True)
        outside.write_bytes(b"SECRET")
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "evil.docx",
                    "path": str(outside),
                    "size_bytes": outside.stat().st_size,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_alpha/evil.docx")
        assert resp.status_code == 404

    def test_404_when_file_missing_on_disk(
        self, client: TestClient, output_root: Path
    ) -> None:
        phantom = output_root / "documents" / "brand" / "phantom.docx"
        phantom.parent.mkdir(parents=True, exist_ok=True)
        _write_manifest(
            output_root,
            [
                {
                    "session_id": "s_alpha",
                    "brand_name": "Alpha",
                    "category": "documents",
                    "tool": "generate_document",
                    "filename": "phantom.docx",
                    "path": str(phantom),
                    "size_bytes": 0,
                    "generated_at": "2026-05-16T10:00:00+07:00",
                }
            ],
        )
        resp = client.get("/api/v1/artifacts/s_alpha/phantom.docx")
        assert resp.status_code == 404
