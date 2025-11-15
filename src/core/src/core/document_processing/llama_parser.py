import datetime
import json
import os
import time
from pathlib import Path
from typing import List, Optional

from loguru import logger

from config.system_config import SETTINGS
from core.document_processing.models import PDFParseResult

PAGE_MARKDOWN_TEMPLATE = """# Page {page_number}

**Document**: {document_name}
**Author**: {author}
**Original File**: {original_file_path}
**Page Number**: {page_number}/{total_pages}
**Processing Time**: {processing_timestamp}

---

{page_text}"""


class LlamaPDFProcessor:
    """
    High-level PDF processing with LlamaParse.
    Uses local imports to handle optional dependencies gracefully.
    """

    def __init__(self, api_key: Optional[str] = None, **config):
        """
        Initializes the LlamaPDFProcessor.

        Args:
            api_key (Optional[str]): The API key for LlamaParse. If None, it defaults to
                SETTINGS.LLAMA_PARSE_API_KEY.
            **config: Additional configuration for LlamaParse.
        """
        self.api_key = api_key if api_key is not None else SETTINGS.LLAMA_PARSE_API_KEY
        self.config = config
        self._parser = None
        self.author_map = self._load_author_metadata()

    def _load_author_metadata(self):
        """Loads author metadata from the JSON file."""
        metadata_path = Path("data/raw_documents/document_metadata.json")
        if not metadata_path.exists():
            logger.warning(f"Author metadata file not found at {metadata_path}")
            return {}
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata_list = json.load(f)
            return {item["document_name"]: item["author"] for item in metadata_list}
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load or parse author metadata: {e}")
            return {}

    @property
    def parser(self):
        """
        Lazy initialization of the LlamaParse instance.
        This property ensures that the LlamaParse client is only created when it is
        first accessed, allowing for optional dependency management.

        Returns:
            The LlamaParse instance.
        """
        if self._parser is None:
            self._parser = self._create_parser()
        return self._parser

    def _create_parser(self):
        """
        Creates and configures the LlamaParse instance.
        This method handles the import and instantiation of the LlamaParse client,
        raising an ImportError if the required package is not installed.

        Returns:
            An instance of the LlamaParse client.

        Raises:
            ImportError: If the 'llama-cloud-services' package is not installed.
        """
        try:
            from llama_cloud_services import LlamaParse

            # Ensure api_key is not duplicated if already in config
            parser_config = self.config.copy()
            if "api_key" in parser_config:
                del parser_config["api_key"]

            return LlamaParse(
                api_key=self.api_key,
                parse_mode="parse_page_with_agent",
                model="openai-gpt-4-1-mini",
                high_res_ocr=True,
                adaptive_long_table=True,
                outlined_table_extraction=True,
                output_tables_as_HTML=True,
                result_type="markdown",
                **parser_config,
            )
        except ImportError as e:
            raise ImportError(
                "llama-cloud-services not installed. "
                "Install with: make add-indexer PKG=llama-cloud-services"
            ) from e

    async def parse_pdf(self, file_path: str, **options) -> PDFParseResult:
        """
        Parses a single PDF file and generates per-page markdown files.

        This method processes a PDF, extracts its content page by page, and saves each
        page as a separate markdown file in a structured output directory. It also
        gathers metadata about the parsing process.

        Args:
            file_path (str): The path to the PDF file to be parsed.
            **options: Additional parsing options to be passed to LlamaParse.

        Returns:
            PDFParseResult: An object containing the extracted content, metadata,
                            and paths to the generated page files.

        Raises:
            FileNotFoundError: If the specified PDF file does not exist.
        """
        logger.info(f"Starting PDF parsing: {file_path}")
        start_time = time.time()

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        doc_name = path.stem
        author = self.author_map.get(path.name, "Unknown")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("data/parsed_documents") / f"{doc_name}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            result = await self.parser.aparse(file_path, **options)
            markdown_documents = result.get_markdown_documents(split_by_page=True)

            page_files = []
            for i, doc in enumerate(markdown_documents, 1):
                page_file = output_dir / f"page_{i}.md"
                page_content = PAGE_MARKDOWN_TEMPLATE.format(
                    page_number=i,
                    document_name=doc_name,
                    author=author,
                    original_file_path=file_path,
                    total_pages=len(markdown_documents),
                    processing_timestamp=datetime.datetime.now().isoformat(),
                    page_text=doc.text,
                )
                with open(page_file, "w", encoding="utf-8") as f:
                    f.write(page_content)
                page_files.append(str(page_file))

            content = "\n\n---\n\n".join([doc.text for doc in markdown_documents])
            processing_time = time.time() - start_time

            return PDFParseResult(
                content=content,
                pages=len(markdown_documents),
                tables_extracted=content.count("<table"),
                processing_time=processing_time,
                file_path=file_path,
                file_size=path.stat().st_size,
                output_directory=str(output_dir),
                page_files=page_files,
                metadata={
                    "parser_version": "llama-parse",
                    "config": self.config,
                    "file_extension": path.suffix,
                    "timestamp": timestamp,
                    "author": author,
                },
            )

        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {e}")
            raise

    async def parse_pdf_batch(self, file_paths: List[str]) -> List[PDFParseResult]:
        """
        Parses multiple PDF files sequentially with progress tracking.

        This method iterates through a list of file paths, parsing each PDF
        individually. It uses tqdm to display a progress bar for the batch operation.

        Args:
            file_paths (List[str]): A list of paths to the PDF files to be processed.

        Returns:
            List[PDFParseResult]: A list of result objects, one for each successfully
                                 parsed PDF.
        """
        from tqdm import tqdm

        logger.info(f"Starting sequential PDF parsing: {len(file_paths)} files")
        results = []

        with tqdm(total=len(file_paths), desc="Processing PDFs") as pbar:
            for file_path in file_paths:
                try:
                    result = await self.parse_pdf(file_path)
                    results.append(result)
                    pbar.set_description(f"Processed: {os.path.basename(file_path)}")
                    pbar.update(1)
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
                    pbar.update(1)
                    continue

        logger.info(f"Completed batch parsing: {len(results)} successful")
        return results
