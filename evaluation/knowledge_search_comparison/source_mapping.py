"""Source-ID mapping helpers for HippoRAG and BrandMind search diagnostics."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS_PATH = (
    PROJECT_ROOT
    / ".codex"
    / "benchmarks"
    / "hipporag"
    / "corpus"
    / "marketing_5books_corpus.json"
)
DEFAULT_METADATA_PATH = (
    PROJECT_ROOT
    / ".codex"
    / "benchmarks"
    / "hipporag"
    / "corpus"
    / "marketing_5books_metadata.json"
)
SOURCE_ID_PATTERN = re.compile(r"[a-z0-9_]+::[0-9A-Za-z][0-9A-Za-z_.:-]*")


class CorpusRecord(BaseModel):
    """One exported HippoRAG corpus passage."""

    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    idx: int = Field(ge=0)

    @property
    def source_id(self) -> str:
        """Return the source ID stored in the HippoRAG title field."""

        return self.title


class SourceMetadataRecord(BaseModel):
    """Traceability metadata for one BrandMind source chunk."""

    source_id: str = Field(min_length=1)
    book_slug: str = ""
    book_dir: str = ""
    chunk_id: str = ""
    pages: list[int] = Field(default_factory=list)
    source: str = ""
    original_document: str = ""
    author: str = ""
    section_summary: str = ""
    word_count: int | None = None

    @model_validator(mode="after")
    def infer_chunk_id(self) -> "SourceMetadataRecord":
        """Infer missing chunk ID from the stable ``book_slug::chunk_id`` ID."""

        if not self.chunk_id and "::" in self.source_id:
            self.chunk_id = self.source_id.split("::", maxsplit=1)[1]
        return self


class SourceMapping(BaseModel):
    """Lookup table from retrieved text, index, or chunk ID to source IDs."""

    records: list[CorpusRecord]
    metadata_by_source_id: dict[str, SourceMetadataRecord]
    duplicate_text_count: int = 0

    @model_validator(mode="after")
    def validate_sources(self) -> "SourceMapping":
        """Ensure every corpus record has metadata when metadata is available."""

        missing_metadata = [
            record.source_id
            for record in self.records
            if (
                self.metadata_by_source_id
                and record.source_id not in self.metadata_by_source_id
            )
        ]
        if missing_metadata:
            raise ValueError(
                "Corpus records missing metadata: "
                f"{missing_metadata[:5]} ({len(missing_metadata)} total)."
            )
        self.duplicate_text_count = count_duplicate_texts(self.records)
        return self

    @property
    def source_ids_by_exact_text(self) -> dict[str, list[str]]:
        """Map exact corpus text to all matching source IDs."""

        mapping: dict[str, list[str]] = {}
        for record in self.records:
            mapping.setdefault(record.text, []).append(record.source_id)
        return mapping

    @property
    def source_ids_by_normalized_text(self) -> dict[str, list[str]]:
        """Map whitespace-normalized corpus text to all matching source IDs."""

        mapping: dict[str, list[str]] = {}
        for record in self.records:
            normalized = normalize_text(record.text)
            mapping.setdefault(normalized, []).append(record.source_id)
        return mapping

    @property
    def source_ids_by_index(self) -> dict[int, str]:
        """Map HippoRAG corpus index to stable source ID."""

        return {record.idx: record.source_id for record in self.records}

    @property
    def source_ids_by_chunk_id(self) -> dict[str, list[str]]:
        """Map parser chunk IDs to stable source IDs."""

        mapping: dict[str, list[str]] = {}
        for metadata in self.metadata_by_source_id.values():
            if metadata.chunk_id:
                mapping.setdefault(metadata.chunk_id, []).append(metadata.source_id)
        return mapping

    def source_ids_for_text(self, text: str) -> list[str]:
        """Map raw retrieved text to source IDs using exact then normalized text."""

        if not text:
            return []
        exact_matches = self.source_ids_by_exact_text.get(text)
        if exact_matches:
            return unique_preserve_order(exact_matches)
        normalized_matches = self.source_ids_by_normalized_text.get(
            normalize_text(text)
        )
        return unique_preserve_order(normalized_matches or [])

    def source_ids_for_document(self, document: str | Mapping[str, Any]) -> list[str]:
        """Map a HippoRAG returned document object or string to source IDs."""

        if isinstance(document, str):
            return self.source_ids_for_text(document)

        explicit_source = document.get("source_id") or document.get("title")
        if isinstance(explicit_source, str) and explicit_source in (
            self.metadata_by_source_id
        ):
            return [explicit_source]

        raw_index = document.get("idx") or document.get("index")
        if isinstance(raw_index, int) and raw_index in self.source_ids_by_index:
            return [self.source_ids_by_index[raw_index]]

        raw_text = (
            document.get("text") or document.get("content") or document.get("doc")
        )
        if isinstance(raw_text, str):
            return self.source_ids_for_text(raw_text)
        return []

    def source_ids_for_chunk_id(self, chunk_id: str) -> list[str]:
        """Map a BrandMind chunk ID to stable source IDs."""

        return unique_preserve_order(self.source_ids_by_chunk_id.get(chunk_id, []))

    def source_ids_in_text(self, text: str) -> list[str]:
        """Extract stable source IDs already present in formatted tool output."""

        return unique_preserve_order(
            match.strip(".,;:)]}") for match in SOURCE_ID_PATTERN.findall(text)
        )


def load_source_mapping(
    corpus_path: Path = DEFAULT_CORPUS_PATH,
    metadata_path: Path = DEFAULT_METADATA_PATH,
) -> SourceMapping:
    """Load corpus and metadata sidecar into a source mapping object."""

    records = load_corpus_records(corpus_path)
    metadata = load_source_metadata(metadata_path)
    return SourceMapping(records=records, metadata_by_source_id=metadata)


def load_corpus_records(path: Path) -> list[CorpusRecord]:
    """Load exported HippoRAG corpus records."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected corpus list in {path}.")
    return [CorpusRecord(**record) for record in payload]


def load_source_metadata(path: Path) -> dict[str, SourceMetadataRecord]:
    """Load source metadata sidecar keyed by stable source ID."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected metadata object in {path}.")
    raw_sources = payload.get("sources")
    if not isinstance(raw_sources, dict):
        raise ValueError(f"Expected metadata 'sources' object in {path}.")
    return {
        source_id: SourceMetadataRecord(**metadata)
        for source_id, metadata in raw_sources.items()
        if isinstance(metadata, dict)
    }


def normalize_text(text: str) -> str:
    """Normalize whitespace for robust retrieved-passage joins."""

    return re.sub(r"\s+", " ", text).strip()


def unique_preserve_order(values: Iterable[str]) -> list[str]:
    """Return unique non-empty strings while preserving first-seen order."""

    seen: set[str] = set()
    unique_values: list[str] = []
    for raw_value in values:
        value = str(raw_value).strip()
        if value and value not in seen:
            seen.add(value)
            unique_values.append(value)
    return unique_values


def count_duplicate_texts(records: list[CorpusRecord]) -> int:
    """Count corpus text values that map to more than one source ID."""

    text_counts: dict[str, int] = {}
    for record in records:
        text_counts[normalize_text(record.text)] = (
            text_counts.get(normalize_text(record.text), 0) + 1
        )
    return sum(1 for count in text_counts.values() if count > 1)
