"""CLI for building knowledge graph from parsed documents."""

import argparse
import asyncio
from pathlib import Path

from loguru import logger


async def async_main() -> None:
    """Main CLI entry point for knowledge graph building."""
    parser = argparse.ArgumentParser(
        description="Build knowledge graph from parsed documents."
    )
    parser.add_argument(
        "--folder",
        type=str,
        required=True,
        help="Folder name in data/parsed_documents/ to process",
    )
    parser.add_argument(
        "--stage",
        type=str,
        choices=["mapping", "chunking", "extraction", "validate", "all"],
        default="all",
        help="Which stage to run (default: all)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume extraction from last checkpoint (Stage 3 only)",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry only previously failed chunks (Stage 3 only)",
    )

    args = parser.parse_args()

    base_dir = Path("data/parsed_documents")
    folder_path = base_dir / args.folder

    if not folder_path.exists():
        logger.error(f"Folder not found: {folder_path}")
        logger.info(f"Available folders in {base_dir}:")
        for f in sorted(base_dir.iterdir()):
            if f.is_dir():
                logger.info(f"  - {f.name}")
        return

    # Stage 1: Mapping
    if args.stage in ["mapping", "all"]:
        logger.info("=" * 80)
        logger.info("STAGE 1: DOCUMENT MAPPING")
        logger.info("=" * 80)

        from core.knowledge_graph.cartographer import DocumentCartographer

        cartographer = DocumentCartographer(document_folder=str(folder_path))

        # Run analysis
        global_map, messages = await cartographer.analyze()

        # Save outputs
        output_file = folder_path / "global_map.json"
        global_map.to_json_file(str(output_file))
        logger.info(f"✅ Saved global_map.json to {output_file}")

        # Save message log
        log_file = cartographer.save_message_log(messages)
        logger.info(f"✅ Saved message log to {log_file}")
        logger.info(f"📊 Mapped {len(global_map.structure)} top-level sections")

    # Stage 2: Chunking
    if args.stage in ["chunking", "all"]:
        logger.info("=" * 80)
        logger.info("STAGE 2: SEMANTIC CHUNKING")
        logger.info("=" * 80)

        from core.knowledge_graph.chunker.document_chunker import DocumentChunker

        # Check if global_map.json exists
        global_map_file = folder_path / "global_map.json"
        if not global_map_file.exists():
            logger.error("global_map.json not found. Run Stage 1 (mapping) first.")
            return

        chunker = DocumentChunker(
            document_folder=str(folder_path), global_map_path=str(global_map_file)
        )

        # Run chunking
        result = chunker.chunk_document()

        # Save output
        output_file = folder_path / "chunks.json"
        result.to_json_file(str(output_file))
        logger.info(f"✅ Saved chunks.json to {output_file}")
        logger.info(
            f"📊 Generated {result.total_chunks} chunks "
            f"(avg {result.avg_chunk_size:.0f} words/chunk)"
        )

    # Stage 3: Knowledge Extraction
    if args.stage in ["extraction", "all"]:
        logger.info("=" * 80)
        logger.info("STAGE 3: KNOWLEDGE EXTRACTION")
        logger.info("=" * 80)

        from core.knowledge_graph.miner import BatchProcessor

        # Check if chunks.json exists
        chunks_file = folder_path / "chunks.json"
        if not chunks_file.exists():
            logger.error("chunks.json not found. Run Stage 2 (chunking) first.")
            return

        processor = BatchProcessor(document_folder=str(folder_path))

        # Validate mutually exclusive flags
        if args.resume and args.retry_failed:
            logger.error(
                "Cannot use --resume and --retry-failed together. "
                "Use --resume to continue processing remaining chunks, "
                "or --retry-failed to retry only failed chunks."
            )
            return

        # Run extraction (with resume or retry-failed support)
        if args.retry_failed:
            logger.info("🔄 Retrying previously failed chunks...")
            results = await processor.process_all_chunks(
                resume=False, retry_failed=True
            )
        else:
            results = await processor.process_all_chunks(resume=args.resume)

        # Output is saved incrementally by batch processor
        # Just log final statistics
        output_file = folder_path / "triples.json"
        total_entities = sum(len(r.extraction.entities) for r in results)
        total_relations = sum(len(r.extraction.relationships) for r in results)

        logger.info(f"✅ Extraction complete! Results saved to {output_file}")
        logger.info(
            f"📊 Extracted {total_entities} entities, "
            f"{total_relations} relations from "
            f"{len(results)} chunks"
        )

    # Stage 4: Validation
    if args.stage in ["validate", "all"]:
        logger.info("=" * 80)
        logger.info("STAGE 4: VALIDATION")
        logger.info("=" * 80)

        from core.knowledge_graph.validate_extraction_output import (
            cross_validate,
            validate_extraction_progress,
            validate_triples_json,
        )

        # Validate triples.json
        triples_file = folder_path / "triples.json"
        if not triples_file.exists():
            logger.warning("triples.json not found. Run Stage 3 (extraction) first.")
        else:
            logger.info(f"📄 Validating {triples_file.name}...")
            triples_results = validate_triples_json(triples_file)

            if triples_results["valid"]:
                logger.success("✅ triples.json is valid!")
                stats = triples_results["stats"]
                logger.info(f"   Chunks: {stats['total_chunks']}")
                logger.info(f"   Entities: {stats['total_entities']}")
                logger.info(f"   Relations: {stats['total_relations']}")
                logger.info(
                    f"   Avg entities/chunk: {stats['avg_entities_per_chunk']:.1f}"
                )
                logger.info(
                    f"   Avg relations/chunk: {stats['avg_relations_per_chunk']:.1f}"
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
        if not progress_file.exists():
            logger.warning(
                "extraction_progress.json not found. Run Stage 3 (extraction) first."
            )
        else:
            logger.info(f"📄 Validating {progress_file.name}...")
            progress_results = validate_extraction_progress(progress_file)

            if progress_results["valid"]:
                logger.success("✅ extraction_progress.json is valid!")
                stats = progress_results["stats"]
                logger.info(f"   Last batch: {stats['last_batch_idx']}")
                logger.info(f"   Completed: {stats['completed_chunks']} chunks")
                logger.info(f"   Failed: {stats['failed_chunks']} chunks")
            else:
                logger.error("❌ extraction_progress.json validation failed!")
                for error in progress_results["errors"]:
                    logger.error(f"   - {error}")

            if progress_results["warnings"]:
                for warning in progress_results["warnings"]:
                    logger.warning(f"   ⚠️  {warning}")

        # Cross-validation
        if triples_file.exists() and progress_file.exists():
            logger.info("🔍 Cross-validation...")
            cross_warnings = cross_validate(triples_results, progress_results)
            if cross_warnings:
                for warning in cross_warnings:
                    logger.warning(f"   ⚠️  {warning}")
            else:
                logger.success("✅ Files are consistent with each other")

    logger.info("=" * 80)
    logger.info("✅ Processing complete!")
    logger.info("=" * 80)


def main() -> None:
    """Synchronous entry point."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
