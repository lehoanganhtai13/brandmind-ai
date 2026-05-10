"""Subprocess worker for HippoRAG native retrieval in its conda environment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from evaluation.hipporag_comparison.hipporag_litellm import (
    HippoRagLiteLLMConfig,
    build_hipporag,
)
from evaluation.knowledge_search_comparison.source_mapping import (
    DEFAULT_CORPUS_PATH,
    DEFAULT_METADATA_PATH,
    load_corpus_records,
    load_source_mapping,
)

DEFAULT_SAVE_DIR = Path(".codex/benchmarks/hipporag/index/marketing_5books")


class HippoRagRetrievedPassage(BaseModel):
    """One passage returned by HippoRAG native retrieval."""

    rank: int = Field(ge=1)
    text: str
    score: float | None = None
    source_ids: list[str] = Field(default_factory=list)


class HippoRagWorkerResponse(BaseModel):
    """JSON response emitted by the HippoRAG worker process."""

    query: str
    top_k: int
    passages: list[HippoRagRetrievedPassage]


def retrieve_with_hipporag(
    *,
    query: str,
    top_k: int,
    save_dir: Path,
    corpus_path: Path,
    metadata_path: Path,
) -> HippoRagWorkerResponse:
    """Run HippoRAG ``retrieve`` and map native passages to source IDs."""

    hipporag = build_hipporag(HippoRagLiteLLMConfig(save_dir=str(save_dir)))
    query_solutions = hipporag.retrieve([query], num_to_retrieve=top_k)
    if not query_solutions:
        return HippoRagWorkerResponse(query=query, top_k=top_k, passages=[])

    mapping = load_source_mapping(corpus_path, metadata_path)
    solution = query_solutions[0]
    docs = _coerce_sequence(getattr(solution, "docs", None))
    scores = _coerce_sequence(getattr(solution, "doc_scores", None))
    passages = [
        HippoRagRetrievedPassage(
            rank=index + 1,
            text=str(document),
            score=float(scores[index]) if index < len(scores) else None,
            source_ids=mapping.source_ids_for_document(str(document)),
        )
        for index, document in enumerate(docs[:top_k])
    ]
    return HippoRagWorkerResponse(query=query, top_k=top_k, passages=passages)


def _coerce_sequence(value: Any) -> list[Any]:
    """Normalize HippoRAG list-like outputs without truth-value checks."""

    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)

    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        result = tolist()
        return result if isinstance(result, list) else [result]

    return list(value)


def index_with_hipporag(
    *,
    save_dir: Path,
    corpus_path: Path,
) -> dict[str, Any]:
    """Build or refresh a HippoRAG index over the exported five-book corpus."""

    records = load_corpus_records(corpus_path)
    hipporag = build_hipporag(HippoRagLiteLLMConfig(save_dir=str(save_dir)))
    hipporag.index(docs=[record.text for record in records])
    return {
        "indexed_records": len(records),
        "save_dir": str(save_dir),
        "corpus_path": str(corpus_path),
    }


def build_parser() -> argparse.ArgumentParser:
    """Build the worker CLI parser."""

    parser = argparse.ArgumentParser(
        description="Run HippoRAG native indexing or retrieval."
    )
    parser.add_argument(
        "mode",
        choices=("index", "retrieve"),
        help="Worker mode to run.",
    )
    parser.add_argument("--query", default="", help="Query for retrieve mode.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--save-dir", type=Path, default=DEFAULT_SAVE_DIR)
    parser.add_argument("--corpus-path", type=Path, default=DEFAULT_CORPUS_PATH)
    parser.add_argument("--metadata-path", type=Path, default=DEFAULT_METADATA_PATH)
    return parser


def main() -> None:
    """Run the HippoRAG worker CLI."""

    args = build_parser().parse_args()
    if args.mode == "index":
        payload: object = index_with_hipporag(
            save_dir=args.save_dir,
            corpus_path=args.corpus_path,
        )
    else:
        if not args.query:
            raise SystemExit("--query is required for retrieve mode.")
        payload = retrieve_with_hipporag(
            query=args.query,
            top_k=args.top_k,
            save_dir=args.save_dir,
            corpus_path=args.corpus_path,
            metadata_path=args.metadata_path,
        ).model_dump()
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
