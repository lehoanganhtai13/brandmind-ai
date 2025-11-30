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
        choices=["mapping", "chunking", "building", "all"],
        default="all",
        help="Which stage to run (default: all)",
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

    # TODO: Stage 3 (Building) - Future task

    logger.info("=" * 80)
    logger.info("✅ Processing complete!")
    logger.info("=" * 80)


def main() -> None:
    """Synchronous entry point for CLI."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
