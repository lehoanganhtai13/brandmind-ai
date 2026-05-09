"""Export BrandMind parsed book chunks into HippoRAG custom corpus format.

HippoRAG custom corpora use a JSON array of objects with ``title``, ``text``,
and ``idx`` fields. BrandMind needs more source traceability than HippoRAG's
minimal format, so this exporter writes two files:

1. A HippoRAG corpus JSON file for indexing.
2. A metadata sidecar keyed by the same stable source IDs.

Business context:
    The benchmark must compare BrandMind and HippoRAG on the same five marketing
    books. Stable source IDs are required so QA and retrieval metrics can report
    whether a system found the supporting source chunks, not just whether the
    final answer sounded correct.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

CANONICAL_BOOK_DIRS = (
    "How_Brands_Grow_What_Marketers_Dont_Know_20260206_171611",
    "Influence_New_and_Expanded_The_Psychology_of_Persuasion_20260206_172109",
    "Kotler_and_Armstrong_Principles_of_Marketing_20251123_193123",
    "Positioning_The_Battle_for_Your_Mind_20260206_170800",
    "Strategic_Brand_Management_20260206_164738",
)


@dataclass(frozen=True)
class HippoRagCorpusRecord:
    """One passage in HippoRAG custom corpus format."""

    title: str
    text: str
    idx: int


@dataclass(frozen=True)
class SourceMetadata:
    """Traceability metadata for one exported BrandMind chunk.

    Args:
        source_id: Stable benchmark source identifier.
        book_slug: Stable slug derived from the parsed document directory name.
        book_dir: Original parsed document directory name.
        chunk_id: Chunk identifier from BrandMind's parser.
        pages: Page numbers recorded by the parser.
        source: Source field from chunk metadata.
        original_document: Original document name from chunk metadata.
        author: Author field from chunk metadata.
        section_summary: Parser-generated section summary.
        word_count: Parser-reported word count if available.
    """

    source_id: str
    book_slug: str
    book_dir: str
    chunk_id: str
    pages: list[int]
    source: str
    original_document: str
    author: str
    section_summary: str
    word_count: int | None


def slugify(value: str) -> str:
    """Convert a parsed document directory name into a stable lowercase slug.

    Args:
        value: Directory name or source string.

    Returns:
        A lowercase slug containing only letters, digits, and underscores.
    """

    normalized = re.sub(r"_[0-9]{8}_[0-9]{6}$", "", value)
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", normalized)
    return normalized.strip("_").lower()


def normalize_pages(raw_pages: object) -> list[int]:
    """Normalize parser page metadata into a list of integers.

    Args:
        raw_pages: Page metadata from a parsed chunk.

    Returns:
        A sorted list of integer page numbers. Invalid values are ignored.
    """

    if raw_pages is None:
        return []
    if isinstance(raw_pages, int):
        return [raw_pages]
    if isinstance(raw_pages, list):
        pages = []
        for page in raw_pages:
            if isinstance(page, int):
                pages.append(page)
            elif isinstance(page, str) and page.isdigit():
                pages.append(int(page))
        return sorted(set(pages))
    if isinstance(raw_pages, str) and raw_pages.isdigit():
        return [int(raw_pages)]
    return []


def load_chunks(chunks_path: Path) -> list[dict[str, object]]:
    """Load and validate a BrandMind ``chunks.json`` file.

    Args:
        chunks_path: Path to a parsed document ``chunks.json`` file.

    Returns:
        The list of chunk dictionaries.

    Raises:
        ValueError: If the file does not contain a ``chunks`` list.
    """

    payload = json.loads(chunks_path.read_text(encoding="utf-8"))
    chunks = payload.get("chunks")
    if not isinstance(chunks, list):
        raise ValueError(f"Expected a chunks list in {chunks_path}.")
    return chunks


def iter_book_chunk_paths(parsed_root: Path) -> Iterable[Path]:
    """Yield canonical five-book chunk paths in deterministic order.

    Args:
        parsed_root: Root directory containing parsed document folders.

    Yields:
        Paths to canonical ``chunks.json`` files.

    Raises:
        FileNotFoundError: If a canonical book folder is missing ``chunks.json``.
    """

    for book_dir in CANONICAL_BOOK_DIRS:
        chunks_path = parsed_root / book_dir / "chunks.json"
        if not chunks_path.exists():
            raise FileNotFoundError(f"Missing canonical chunks file: {chunks_path}")
        yield chunks_path


def build_records(
    parsed_root: Path,
) -> tuple[list[HippoRagCorpusRecord], dict[str, SourceMetadata]]:
    """Build HippoRAG corpus records and source metadata from parsed chunks.

    Args:
        parsed_root: Root directory containing parsed document folders.

    Returns:
        A pair of corpus records and metadata keyed by source ID.
    """

    records: list[HippoRagCorpusRecord] = []
    metadata_by_source_id: dict[str, SourceMetadata] = {}

    for chunks_path in iter_book_chunk_paths(parsed_root):
        book_dir = chunks_path.parent.name
        book_slug = slugify(book_dir)
        chunks = load_chunks(chunks_path)

        for chunk in chunks:
            chunk_id = str(chunk.get("chunk_id", "")).strip()
            content = str(chunk.get("content", "")).strip()
            raw_metadata = chunk.get("metadata", {})
            chunk_metadata = raw_metadata if isinstance(raw_metadata, dict) else {}

            if not chunk_id:
                raise ValueError(f"Chunk without chunk_id in {chunks_path}.")
            if not content:
                raise ValueError(
                    f"Chunk {chunk_id} in {chunks_path} has empty content."
                )

            source_id = f"{book_slug}::{chunk_id}"
            if source_id in metadata_by_source_id:
                raise ValueError(f"Duplicate source_id generated: {source_id}")

            record = HippoRagCorpusRecord(
                title=source_id,
                text=content,
                idx=len(records),
            )
            records.append(record)

            word_count = chunk_metadata.get("word_count")
            metadata_by_source_id[source_id] = SourceMetadata(
                source_id=source_id,
                book_slug=book_slug,
                book_dir=book_dir,
                chunk_id=chunk_id,
                pages=normalize_pages(chunk_metadata.get("pages")),
                source=str(chunk_metadata.get("source", "")),
                original_document=str(chunk_metadata.get("original_document", "")),
                author=str(chunk_metadata.get("author", "")),
                section_summary=str(chunk_metadata.get("section_summary", "")),
                word_count=word_count if isinstance(word_count, int) else None,
            )

    return records, metadata_by_source_id


def write_json(path: Path, payload: object) -> None:
    """Write pretty JSON with UTF-8 encoding.

    Args:
        path: Output path.
        payload: JSON-serializable payload.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def export_corpus(parsed_root: Path, corpus_path: Path, metadata_path: Path) -> None:
    """Export five-book corpus and source metadata files.

    Args:
        parsed_root: Root directory containing parsed documents.
        corpus_path: Output path for HippoRAG corpus JSON.
        metadata_path: Output path for metadata sidecar JSON.
    """

    records, metadata_by_source_id = build_records(parsed_root)
    write_json(corpus_path, [asdict(record) for record in records])
    write_json(
        metadata_path,
        {
            "total_records": len(records),
            "canonical_book_dirs": list(CANONICAL_BOOK_DIRS),
            "sources": {
                source_id: asdict(metadata)
                for source_id, metadata in metadata_by_source_id.items()
            },
        },
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for corpus export."""

    parser = argparse.ArgumentParser(
        description="Export BrandMind five-book chunks to HippoRAG corpus format.",
    )
    parser.add_argument(
        "--parsed-root",
        type=Path,
        default=Path("data/parsed_documents"),
        help="Root directory containing parsed document folders.",
    )
    parser.add_argument(
        "--corpus-output",
        type=Path,
        default=Path(".codex/benchmarks/hipporag/corpus/marketing_5books_corpus.json"),
        help="Output HippoRAG corpus JSON path.",
    )
    parser.add_argument(
        "--metadata-output",
        type=Path,
        default=Path(
            ".codex/benchmarks/hipporag/corpus/marketing_5books_metadata.json"
        ),
        help="Output source metadata JSON path.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the corpus exporter from the command line."""

    args = parse_args()
    export_corpus(
        parsed_root=args.parsed_root,
        corpus_path=args.corpus_output,
        metadata_path=args.metadata_output,
    )


if __name__ == "__main__":
    main()
