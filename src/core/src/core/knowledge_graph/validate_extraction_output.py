"""Validation script for extraction output files.

This script validates the structure and format of:
1. triples.json - Extracted knowledge graph triples
2. extraction_progress.json - Extraction progress checkpoint

Usage:
    python -m core.knowledge_graph.validate_extraction_output --folder <folder_name>
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, cast

from loguru import logger
from pydantic import BaseModel, Field, ValidationError


class Entity(BaseModel):
    """Entity model for validation."""

    name: str
    type: str
    description: str


class Relationship(BaseModel):
    """Relationship model for validation."""

    source: str
    target: str
    type: str | None = None  # Optional - some relationships may not have type
    description: str


class Extraction(BaseModel):
    """Nested extraction object."""

    entities: List[Entity]
    relationships: List[Relationship]


class ExtractionResult(BaseModel):
    """Single chunk extraction result model."""

    chunk_id: str
    extraction: Extraction  # Nested object
    # Optional fields - not validated strictly
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_hierarchy: Any = None  # Can be dict or string
    validation: Dict[str, Any] = Field(default_factory=dict)


class TriplesOutput(BaseModel):
    """Complete triples.json structure."""

    total_chunks: int = Field(ge=0)
    total_entities: int = Field(ge=0)
    total_relations: int = Field(ge=0)
    extractions: List[ExtractionResult]


class ExtractionProgress(BaseModel):
    """Extraction progress checkpoint structure."""

    last_batch_idx: int = Field(ge=-1)
    completed_chunk_ids: List[str]
    failed_chunk_ids: List[str] = Field(default_factory=list)


def validate_triples_json(file_path: Path) -> Dict[str, Any]:
    """Validate triples.json structure and content.

    Args:
        file_path: Path to triples.json

    Returns:
        Validation results dictionary
    """
    results = {
        "file": str(file_path),
        "valid": False,
        "errors": [],
        "warnings": [],
        "stats": {},
    }

    try:
        # Check file exists
        if not file_path.exists():
            cast(List[str], results["errors"]).append(f"File not found: {file_path}")
            return results

        # Load JSON
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate structure with Pydantic
        try:
            triples = TriplesOutput(**data)
        except ValidationError as e:
            cast(List[str], results["errors"]).append(f"Schema validation failed: {e}")
            return results

        # Verify counts match
        actual_chunks = len(triples.extractions)
        actual_entities = sum(len(e.extraction.entities) for e in triples.extractions)
        actual_relations = sum(
            len(e.extraction.relationships) for e in triples.extractions
        )

        if triples.total_chunks != actual_chunks:
            cast(List[str], results["errors"]).append(
                f"total_chunks mismatch: declared={triples.total_chunks}, "
                f"actual={actual_chunks}"
            )

        if triples.total_entities != actual_entities:
            cast(List[str], results["errors"]).append(
                f"total_entities mismatch: declared={triples.total_entities}, "
                f"actual={actual_entities}"
            )

        if triples.total_relations != actual_relations:
            cast(List[str], results["errors"]).append(
                f"total_relations mismatch: declared={triples.total_relations}, "
                f"actual={actual_relations}"
            )

        # Check for duplicates
        chunk_ids = [e.chunk_id for e in triples.extractions]
        if len(chunk_ids) != len(set(chunk_ids)):
            duplicates = [cid for cid in chunk_ids if chunk_ids.count(cid) > 1]
            cast(List[str], results["errors"]).append(
                f"Duplicate chunk_ids found: {set(duplicates)}"
            )

        # Check for empty extractions
        empty_chunks = [
            e.chunk_id
            for e in triples.extractions
            if len(e.extraction.entities) == 0 and len(e.extraction.relationships) == 0
        ]
        if empty_chunks:
            cast(List[str], results["warnings"]).append(
                f"{len(empty_chunks)} chunks with no entities or relationships: "
                f"{empty_chunks}"
            )

        # Store stats
        results["stats"] = {
            "total_chunks": actual_chunks,
            "total_entities": actual_entities,
            "total_relations": actual_relations,
            "avg_entities_per_chunk": (
                actual_entities / actual_chunks if actual_chunks > 0 else 0
            ),
            "avg_relations_per_chunk": (
                actual_relations / actual_chunks if actual_chunks > 0 else 0
            ),
            "empty_chunks": len(empty_chunks),
        }

        # Mark as valid if no errors
        if not results["errors"]:
            results["valid"] = True

    except json.JSONDecodeError as e:
        cast(List[str], results["errors"]).append(f"Invalid JSON: {e}")
    except Exception as e:
        cast(List[str], results["errors"]).append(f"Unexpected error: {e}")

    return results


def validate_extraction_progress(file_path: Path) -> Dict[str, Any]:
    """Validate extraction_progress.json structure and content.

    Args:
        file_path: Path to extraction_progress.json

    Returns:
        Validation results dictionary
    """
    results = {
        "file": str(file_path),
        "valid": False,
        "errors": [],
        "warnings": [],
        "stats": {},
    }

    try:
        # Check file exists
        if not file_path.exists():
            cast(List[str], results["errors"]).append(f"File not found: {file_path}")
            return results

        # Load JSON
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate structure with Pydantic
        try:
            progress = ExtractionProgress(**data)
        except ValidationError as e:
            cast(List[str], results["errors"]).append(f"Schema validation failed: {e}")
            return results

        # Check for duplicate chunk IDs
        all_ids = progress.completed_chunk_ids + progress.failed_chunk_ids
        if len(all_ids) != len(set(all_ids)):
            cast(List[str], results["errors"]).append(
                "Duplicate chunk IDs found in progress file"
            )

        # Check for overlap between completed and failed
        completed_set = set(progress.completed_chunk_ids)
        failed_set = set(progress.failed_chunk_ids)
        overlap = completed_set & failed_set
        if overlap:
            cast(List[str], results["errors"]).append(
                f"Chunks appear in both completed and failed: {len(overlap)} chunks"
            )

        # Store stats
        results["stats"] = {
            "last_batch_idx": progress.last_batch_idx,
            "completed_chunks": len(progress.completed_chunk_ids),
            "failed_chunks": len(progress.failed_chunk_ids),
            "total_processed": len(all_ids),
        }

        # Mark as valid if no errors
        if not results["errors"]:
            results["valid"] = True

    except json.JSONDecodeError as e:
        cast(List[str], results["errors"]).append(f"Invalid JSON: {e}")
    except Exception as e:
        cast(List[str], results["errors"]).append(f"Unexpected error: {e}")

    return results


def cross_validate(
    triples_results: Dict[str, Any], progress_results: Dict[str, Any]
) -> List[str]:
    """Cross-validate triples.json and extraction_progress.json.

    Args:
        triples_results: Validation results for triples.json
        progress_results: Validation results for extraction_progress.json

    Returns:
        List of cross-validation warnings
    """
    warnings: List[str] = []

    if not triples_results["valid"] or not progress_results["valid"]:
        return warnings

    # Extract data from results
    triples_chunks = triples_results["stats"]["total_chunks"]
    progress_completed = progress_results["stats"]["completed_chunks"]
    progress_failed = progress_results["stats"]["failed_chunks"]

    # Check if triples count matches completed count
    if triples_chunks != progress_completed:
        warnings.append(
            f"Mismatch: triples.json has {triples_chunks} chunks, "
            f"but progress shows {progress_completed} completed"
        )

    # Warn about failed chunks
    if progress_failed > 0:
        warnings.append(f"{progress_failed} chunks failed and are not in triples.json")

    return warnings


def main():
    """Main validation entry point."""
    parser = argparse.ArgumentParser(description="Validate extraction output files")
    parser.add_argument(
        "--folder",
        type=str,
        required=True,
        help="Folder name in data/parsed_documents/",
    )

    args = parser.parse_args()

    base_dir = Path("data/parsed_documents")
    folder_path = base_dir / args.folder

    if not folder_path.exists():
        logger.error(f"Folder not found: {folder_path}")
        return

    logger.info("=" * 80)
    logger.info("EXTRACTION OUTPUT VALIDATION")
    logger.info("=" * 80)

    # Validate triples.json
    triples_file = folder_path / "triples.json"
    logger.info(f"\n📄 Validating {triples_file.name}...")
    triples_results = validate_triples_json(triples_file)

    if triples_results["valid"]:
        logger.success("✅ triples.json is valid!")
        logger.info(f"   Chunks: {triples_results['stats']['total_chunks']}")
        logger.info(f"   Entities: {triples_results['stats']['total_entities']}")
        logger.info(f"   Relations: {triples_results['stats']['total_relations']}")
        logger.info(
            f"   Avg entities/chunk: "
            f"{triples_results['stats']['avg_entities_per_chunk']:.1f}"
        )
        logger.info(
            f"   Avg relations/chunk: "
            f"{triples_results['stats']['avg_relations_per_chunk']:.1f}"
        )
    else:
        logger.error("❌ triples.json validation failed!")
        for error in triples_results["errors"]:
            logger.error(f"   - {error}")

    if triples_results["warnings"]:
        for warning in triples_results["warnings"]:
            logger.warning(f"   ⚠️  {warning}")

    # Validate extraction_progress.json
    progress_file = folder_path / "extraction_progress.json"
    logger.info(f"\n📄 Validating {progress_file.name}...")
    progress_results = validate_extraction_progress(progress_file)

    if progress_results["valid"]:
        logger.success("✅ extraction_progress.json is valid!")
        logger.info(f"   Last batch: {progress_results['stats']['last_batch_idx']}")
        logger.info(
            f"   Completed: {progress_results['stats']['completed_chunks']} chunks"
        )
        logger.info(f"   Failed: {progress_results['stats']['failed_chunks']} chunks")
    else:
        logger.error("❌ extraction_progress.json validation failed!")
        for error in progress_results["errors"]:
            logger.error(f"   - {error}")

    if progress_results["warnings"]:
        for warning in progress_results["warnings"]:
            logger.warning(f"   ⚠️  {warning}")

    # Cross-validation
    logger.info("\n🔍 Cross-validation...")
    cross_warnings = cross_validate(triples_results, progress_results)
    if cross_warnings:
        for warning in cross_warnings:
            logger.warning(f"   ⚠️  {warning}")
    else:
        logger.success("✅ Files are consistent with each other")

    # Final summary
    logger.info("\n" + "=" * 80)
    if triples_results["valid"] and progress_results["valid"]:
        logger.success("✅ ALL VALIDATIONS PASSED!")
    else:
        logger.error("❌ VALIDATION FAILED - Please review errors above")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
