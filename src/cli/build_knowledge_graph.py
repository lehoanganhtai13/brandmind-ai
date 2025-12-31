"""CLI for building knowledge graph from parsed documents."""

import argparse
import asyncio
from pathlib import Path

from loguru import logger


async def run_document_library(folder_path: Path, resume: bool = False) -> None:
    """
    Run Stream A: Document Library indexing.

    Processes chunks.json to embed document chunks and store them in Milvus
    DocumentChunks collection. Uses Gemini embedder in RETRIEVAL mode for
    optimized document search.

    Args:
        folder_path: Path to folder containing chunks.json
        resume: Whether to resume from previous checkpoint
    """
    from config.system_config import SETTINGS
    from core.knowledge_graph.curator.collection_init import ensure_collection_exists
    from core.knowledge_graph.curator.document_library import (
        DOCUMENT_CHUNKS_BM25_CONFIG,
        DOCUMENT_CHUNKS_SCHEMA,
        build_document_library,
    )
    from shared.database_clients.vector_database.milvus.config import MilvusConfig
    from shared.database_clients.vector_database.milvus.database import (
        MilvusVectorDatabase,
    )
    from shared.model_clients.embedder.gemini import GeminiEmbedder
    from shared.model_clients.embedder.gemini.config import (
        EmbeddingMode,
        GeminiEmbedderConfig,
    )

    chunks_file = folder_path / "chunks.json"
    if not chunks_file.exists():
        logger.error("chunks.json not found. Run Stage 2 (chunking) first.")
        return

    # Initialize clients
    milvus = MilvusVectorDatabase(
        config=MilvusConfig(
            host=SETTINGS.MILVUS_HOST,
            port=SETTINGS.MILVUS_PORT,
            user="root",
            password=SETTINGS.MILVUS_ROOT_PASSWORD,
            run_async=True,
        )
    )

    embedder = GeminiEmbedder(
        config=GeminiEmbedderConfig(
            api_key=SETTINGS.GEMINI_API_KEY,
            model="gemini-embedding-001",
            task_type=EmbeddingMode.RETRIEVAL,
            output_dimensionality=SETTINGS.EMBEDDING_DIM,
        )
    )

    # Get collection name from SETTINGS
    collection_name = SETTINGS.COLLECTION_DOCUMENT_CHUNKS

    # Ensure collection exists
    await ensure_collection_exists(
        milvus, collection_name, DOCUMENT_CHUNKS_SCHEMA, DOCUMENT_CHUNKS_BM25_CONFIG
    )

    # Run builder
    progress_path = folder_path / "document_library_progress.json"
    stats = await build_document_library(
        chunks_path=chunks_file,
        vector_db=milvus,
        embedder=embedder,
        collection_name=collection_name,
        progress_path=progress_path,
    )

    logger.success(f"✅ Document Library: Indexed {stats['upserted']} chunks")


async def run_knowledge_graph(folder_path: Path, resume: bool = False) -> None:
    """
    Run Stream B: Knowledge Graph indexing.

    Processes triples.json to build knowledge graph with entity resolution,
    storing entities/relations in FalkorDB and their descriptions in Milvus.
    Uses Gemini embedder in SEMANTIC mode for entity matching.

    Args:
        folder_path: Path to folder containing triples.json
        resume: Whether to resume from previous checkpoint
    """
    from config.system_config import SETTINGS
    from core.knowledge_graph.curator.collection_init import ensure_collection_exists
    from core.knowledge_graph.curator.collection_schemas import (
        ENTITY_BM25_CONFIG,
        ENTITY_DESCRIPTIONS_SCHEMA,
        RELATION_BM25_CONFIG,
        RELATION_DESCRIPTIONS_SCHEMA,
    )
    from core.knowledge_graph.curator.knowledge_graph_builder import (
        build_knowledge_graph,
    )
    from shared.database_clients.graph_database.falkordb import (
        FalkorDBClient,
        FalkorDBConfig,
    )
    from shared.database_clients.vector_database.milvus.config import MilvusConfig
    from shared.database_clients.vector_database.milvus.database import (
        MilvusVectorDatabase,
    )
    from shared.model_clients.embedder.gemini import GeminiEmbedder
    from shared.model_clients.embedder.gemini.config import (
        EmbeddingMode,
        GeminiEmbedderConfig,
    )

    triples_file = folder_path / "triples.json"
    if not triples_file.exists():
        logger.error("triples.json not found. Run Stage 3 (extraction) first.")
        return

    # Initialize clients
    milvus = MilvusVectorDatabase(
        config=MilvusConfig(
            host=SETTINGS.MILVUS_HOST,
            port=SETTINGS.MILVUS_PORT,
            user="root",
            password=SETTINGS.MILVUS_ROOT_PASSWORD,
            run_async=True,
        )
    )

    falkor = FalkorDBClient(
        config=FalkorDBConfig(
            host=SETTINGS.FALKORDB_HOST,
            port=SETTINGS.FALKORDB_PORT,
            username=SETTINGS.FALKORDB_USERNAME,
            password=SETTINGS.FALKORDB_PASSWORD,
            graph_name=SETTINGS.FALKORDB_GRAPH_NAME,
        )
    )

    embedder = GeminiEmbedder(
        config=GeminiEmbedderConfig(
            api_key=SETTINGS.GEMINI_API_KEY,
            model="gemini-embedding-001",
            task_type=EmbeddingMode.SEMANTIC,
            output_dimensionality=SETTINGS.EMBEDDING_DIM,
        )
    )

    # Get collection names from SETTINGS
    entity_collection = SETTINGS.COLLECTION_ENTITY_DESCRIPTIONS
    relation_collection = SETTINGS.COLLECTION_RELATION_DESCRIPTIONS

    # Ensure collections exist
    await ensure_collection_exists(
        milvus, entity_collection, ENTITY_DESCRIPTIONS_SCHEMA, ENTITY_BM25_CONFIG
    )
    await ensure_collection_exists(
        milvus, relation_collection, RELATION_DESCRIPTIONS_SCHEMA, RELATION_BM25_CONFIG
    )

    # Run builder
    progress_path = folder_path / "kg_build_progress.json"
    stats = await build_knowledge_graph(
        triples_path=triples_file,
        graph_db=falkor,
        vector_db=milvus,
        embedder=embedder,
        entity_collection_name=entity_collection,
        relation_collection_name=relation_collection,
        progress_path=progress_path,
    )

    logger.success(
        f"✅ Knowledge Graph: {stats['entities_created']} entities, "
        f"{stats['entities_merged']} merged, {stats['relations_created']} relations"
    )


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
        choices=[
            "mapping",
            "chunking",
            "extraction",
            "validate",
            "indexing",
            "post-process",
            "all",
        ],
        default="all",
        help="Which stage to run (default: all)",
    )
    parser.add_argument(
        "--stream",
        type=str,
        choices=["document-library", "knowledge-graph", "all"],
        default="all",
        help="Which indexing stream to run (Stage 5 only)",
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="For post-process stage: only report issues without fixing",
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

    # Stage 5: Indexing
    if args.stage in ["indexing", "all"]:
        logger.info("=" * 80)
        logger.info("STAGE 5: INDEXING (Document Library + Knowledge Graph)")
        logger.info("=" * 80)

        # Validate prerequisites
        chunks_file = folder_path / "chunks.json"
        triples_file = folder_path / "triples.json"

        if not chunks_file.exists() and not triples_file.exists():
            logger.error(
                "Neither chunks.json nor triples.json found. "
                "Run Stage 2 (chunking) and/or Stage 3 (extraction) first."
            )
            return

        # Run selected streams based on --stream argument
        stream = args.stream

        # Stream A: Document Library
        if stream in ["document-library", "all"]:
            if chunks_file.exists():
                logger.info("-" * 40)
                logger.info("Stream A: Document Library Builder")
                logger.info("-" * 40)
                try:
                    await run_document_library(folder_path, resume=args.resume)
                except Exception:
                    logger.exception("Stream A failed")
                    if stream == "document-library":
                        raise
            else:
                logger.warning("Skipping Stream A: chunks.json not found")

        # Stream B: Knowledge Graph
        if stream in ["knowledge-graph", "all"]:
            if triples_file.exists():
                logger.info("-" * 40)
                logger.info("Stream B: Knowledge Graph Builder")
                logger.info("-" * 40)
                try:
                    await run_knowledge_graph(folder_path, resume=args.resume)
                except Exception:
                    logger.exception("Stream B failed")
                    if stream == "knowledge-graph":
                        raise
            else:
                logger.warning("Skipping Stream B: triples.json not found")

        logger.info("=" * 80)
        logger.info("✅ Stage 5 Indexing complete!")
        logger.info("=" * 80)

    # Stage 6: Post-Processing (optional cleanup)
    if args.stage == "post-process":
        logger.info("=" * 80)
        logger.info("STAGE 6: POST-PROCESSING (Data Cleanup)")
        logger.info("=" * 80)

        from config.system_config import SETTINGS
        from core.knowledge_graph.curator.post_processing import run_post_processing
        from shared.database_clients.graph_database.falkordb import (
            FalkorDBClient,
            FalkorDBConfig,
        )
        from shared.database_clients.vector_database.milvus.config import MilvusConfig
        from shared.database_clients.vector_database.milvus.database import (
            MilvusVectorDatabase,
        )

        # Initialize clients
        milvus = MilvusVectorDatabase(
            config=MilvusConfig(
                host=SETTINGS.MILVUS_HOST,
                port=SETTINGS.MILVUS_PORT,
                user="root",
                password=SETTINGS.MILVUS_ROOT_PASSWORD,
                run_async=True,
            )
        )

        falkor = FalkorDBClient(
            config=FalkorDBConfig(
                host=SETTINGS.FALKORDB_HOST,
                port=SETTINGS.FALKORDB_PORT,
                username=SETTINGS.FALKORDB_USERNAME,
                password=SETTINGS.FALKORDB_PASSWORD,
                graph_name=SETTINGS.FALKORDB_GRAPH_NAME,
            )
        )

        # Initialize embedder for description re-embedding
        from shared.model_clients.embedder.gemini import GeminiEmbedder
        from shared.model_clients.embedder.gemini.config import (
            EmbeddingMode,
            GeminiEmbedderConfig,
        )

        embedder = GeminiEmbedder(
            config=GeminiEmbedderConfig(
                api_key=SETTINGS.GEMINI_API_KEY,
                model="gemini-embedding-001",
                task_type=EmbeddingMode.SEMANTIC,
                output_dimensionality=SETTINGS.EMBEDDING_DIM,
            )
        )

        # Run post-processing
        stats = await run_post_processing(
            graph_db=falkor,
            vector_db=milvus,
            embedder=embedder,
            entity_collection_name=SETTINGS.COLLECTION_ENTITY_DESCRIPTIONS,
            relation_collection_name=SETTINGS.COLLECTION_RELATION_DESCRIPTIONS,
            dry_run=args.dry_run,
        )

        if args.dry_run:
            logger.info("✅ Post-processing dry run complete (no changes made)")
            logger.info(
                "   Re-run with --stage post-process (without --dry-run) to apply fixes"
            )
        else:
            logger.info("✅ Post-processing complete!")

    logger.info("=" * 80)
    logger.info("✅ Processing complete!")
    logger.info("=" * 80)


def main() -> None:
    """Synchronous entry point."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
