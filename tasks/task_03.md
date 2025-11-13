# Task 03: Create CLI for Document Processing Pipeline

## 📌 Metadata

- **Epic**: Tooling & Automation
- **Priority**: Medium
- **Estimated Effort**: 1-2 days
- **Team**: Backend/Full-stack
- **Related Tasks**: Task 01: LlamaParse PDF Processing Pipeline
- **Blocking**: []
- **Blocked by**: []

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [x] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [x] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] ✅ [Component 1](#component-1) - Ready
    - [x] ✅ [Component 2](#component-2) - Ready
- [x] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation
- [x] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards with comprehensive documentation.
- **argparse Tutorial**: [Python Official Documentation](https://docs.python.org/3/library/argparse.html)

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- The newly implemented PDF processing pipeline can only be triggered via integration tests or direct code execution in a Python shell.
- There is no user-friendly, standardized way for developers to run the pipeline on a specific document or a batch of all available documents.

### Mục tiêu

Implement a command-line interface (CLI) tool, integrated with the project's `Makefile`, to provide a simple and consistent way to run the document processing pipeline.

### Success Metrics / Acceptance Criteria

- **Usability**: Developers can run the pipeline with a single `make` command.
- **Functionality**:
    - Running `make process-docs` processes all documents listed in `document_metadata.json`.
    - Running `make process-docs FILE="<filename.pdf>"` processes only the specified file.
    - The CLI provides clear feedback if a specified file is not found in the metadata.
- **Reliability**: The CLI correctly orchestrates the `PDFProcessor` and handles file paths as expected.

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Argparse-based CLI with Makefile Integration**: A lightweight Python CLI script using the built-in `argparse` library to handle execution modes, integrated into the existing `Makefile` for ease of use.

### Stack công nghệ

- **Python `argparse`**: Chosen for its inclusion in the standard library, avoiding the need for new external dependencies to create a robust CLI.
- **`Makefile`**: Leveraged to provide a simple, memorable, and consistent entry point for developers.

### Issues & Solutions

1. **Logical Script Location** → Create a new directory `src/cli/` to house all command-line tools, improving project organization.
2. **Handling Multiple Modes** → Use an optional `--file` argument in the CLI script. The script's logic will change based on whether this argument is present.
3. **Makefile Argument Passing** → Utilize a Makefile variable (`FILE`) and a conditional shell command within the make target to pass the optional filename to the Python script.

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: CLI Development & Integration**
1. **CLI Script Implementation**
   - Create a new directory `src/cli/`.
   - Create the main script file `src/cli/process_documents.py`.
   - Use `argparse` to set up the optional `--file` argument.
   - Implement the main `async` function to:
     - Load and parse `data/raw_documents/document_metadata.json`.
     - Determine the list of target documents based on the presence of the `--file` argument.
     - Instantiate and run the `PDFProcessor` for the target documents.
   - *Decision Point: Finalize argument names and CLI feedback messages.*

2. **Makefile Integration**
   - Add a new `process-docs` target to the `Makefile`.
   - Implement the conditional logic to check for the `FILE` variable and pass it to the Python script.

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards & Documentation Requirements**
> 
> All code implementations **MUST** follow **enterprise-level Python standards** as defined in previous tasks.

### Component 1

#### Requirement 1 - Document Processing CLI Script
- **Requirement**: Create a Python script at `src/cli/process_documents.py` that uses the `PDFProcessor` to parse documents. The script must support parsing all documents from metadata or a single specified document.
- **Implementation**:
  - `src/cli/process_documents.py`
  ```python
  import argparse
  import asyncio
  import json
  from pathlib import Path
  from typing import List, Dict, Any

  from loguru import logger

  from core.document_processing.pdf_processor import PDFProcessor


  async def main():
      """
      Main function to run the document processing CLI.
      
      Parses command-line arguments to determine which documents to process
      and then invokes the PDFProcessor pipeline.
      """
      parser = argparse.ArgumentParser(description="Run the document processing pipeline.")
      parser.add_argument(
          "--file",
          type=str,
          help="The specific filename of a document to process. Must be listed in document_metadata.json.",
          required=False,
      )
      args = parser.parse_args()

      # Load metadata
      metadata_path = Path("data/raw_documents/document_metadata.json")
      if not metadata_path.exists():
          logger.error(f"Metadata file not found: {metadata_path}")
          return

      with open(metadata_path, 'r', encoding='utf-8') as f:
          all_docs_metadata = json.load(f)

      target_docs: List[Dict[str, Any]] = []
      if args.file:
          # Single file mode
          found = False
          for doc in all_docs_metadata:
              if doc.get("document_name") == args.file:
                  target_docs.append(doc)
                  found = True
                  break
          if not found:
              logger.error(f"File '{args.file}' not found in metadata file. Aborting.")
              return
      else:
          # Batch mode for all documents
          target_docs = all_docs_metadata

      file_paths_to_process = [
          str(Path("data/raw_documents") / doc["document_name"]) for doc in target_docs
      ]
      
      if not file_paths_to_process:
            logger.warning("No documents to process.")
            return

      # Initialize and run the processor
      # Assuming API keys are in the environment, handled by SETTINGS
      processor = PDFProcessor(llama_config={})
      logger.info(f"Starting processing for {len(file_paths_to_process)} document(s)...")
      await processor.process_pdf_batch(file_paths_to_process)
      logger.info("All processing tasks completed.")


  if __name__ == "__main__":
      asyncio.run(main())

  ```
- **Acceptance Criteria**:
  - [x] Script is created at `src/cli/process_documents.py`.
  - [x] Script correctly parses the `--file` argument.
  - [x] Script processes all documents from metadata when no argument is given.
  - [x] Script processes only the specified file when the argument is provided.
  - [x] Script prints an error and exits if a specified file is not in the metadata.

### Component 2

#### Requirement 1 - Makefile Integration Target
- **Requirement**: Add a `process-docs` target to the `Makefile` for easy execution of the CLI script.
- **Implementation**:
  - `Makefile`
  ```makefile
  .PHONY: process-docs
  process-docs: ## Process documents via CLI. Usage: make process-docs [FILE=doc.pdf]
	@if [ -n "$(FILE)" ]; then \
		uv run python src/cli/process_documents.py --file $(FILE); \
	else \
		uv run python src/cli/process_documents.py; \
	fi
  ```
- **Acceptance Criteria**:
  - [x] `make process-docs` runs the script without the `--file` argument.
  - [x] `make process-docs FILE="<filename.pdf>"` runs the script with the `--file "<filename.pdf>"` argument.
  - [x] The command is placed logically within the Makefile, e.g., under a new "Processing" section.

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Batch Processing Mode
- **Purpose**: Verify that the CLI processes all documents from the metadata file.
- **Steps**:
  1. Ensure `data/raw_documents/document_metadata.json` lists at least one document.
  2. Run `make process-docs`.
- **Expected Result**: The pipeline runs for all documents listed in the metadata. Parsed files appear in `data/parsed_documents/`.
- **Status**: ✅ Passed

### Test Case 2: Single File Mode (Valid File)
- **Purpose**: Verify that the CLI processes only the specified, valid document.
- **Steps**:
  1. Get a valid document name from `document_metadata.json`.
  2. Run `make process-docs FILE="<valid_filename.pdf>"`.
- **Expected Result**: The pipeline runs for only the specified document. A new parsed folder is created for just that document.
- **Status**: ✅ Passed

### Test Case 3: Single File Mode (Invalid File)
- **Purpose**: Verify that the CLI handles requests for documents not in the metadata.
- **Steps**:
  1. Run `make process-docs FILE="non_existent_file.pdf"`.
- **Expected Result**: The script prints an error message stating the file was not found in the metadata and exits gracefully without processing anything.
- **Status**: ✅ Passed

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation to document what was actually accomplished.

### What Was Implemented

**Components Completed**:
- [x] Document Processing CLI Script: A Python script in `src/cli/` to orchestrate the pipeline.
- [x] Makefile Integration: A `process-docs` target for easy execution.

**Files Created/Modified**:
```
src/
    └── cli/
        └── process_documents.py      # CLI script for running the PDF processing pipeline
Makefile                          # Added 'process-docs' target
```

**Key Features Delivered**:
1. **Document Processing CLI**: A new command-line tool to run the PDF pipeline.
2. **Makefile Integration**: A simplified `make` command for easy execution.
3. **Flexible Processing Modes**: Support for both batch processing of all documents and single-file processing.

### Technical Highlights

**Architecture Decisions**:
- **`src/cli` Directory**: Established a dedicated directory for command-line tools to improve project structure.
- **`argparse`**: Used Python's standard library for argument parsing to avoid new dependencies.
- **Module Execution (`python -m`)**: Chose to execute the CLI as a module to ensure the project root is added to `sys.path`. This approach is compatible with the project's existing absolute import style (`from src...`) and avoids the `ModuleNotFoundError` encountered when using a standard `[project.scripts]` entry point, which expects a different package layout.

**Documentation Added**:
- [ ] Docstrings added to the main function of the CLI script.
- [ ] Help text added to the `process-docs` target in the Makefile.

### Validation Results

**Test Coverage**:
- [x] All manual test cases pass.

**Deployment Notes**:
- No special deployment considerations are needed for this CLI tool.
