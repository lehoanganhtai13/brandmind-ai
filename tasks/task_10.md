# Task 10: CLI Control Flags for Pipeline Steps

## 📌 Metadata

- **Epic**: Document Processing Enhancement
- **Priority**: Medium
- **Estimated Effort**: 1 day
- **Team**: Backend/Full-stack
- **Related Tasks**: Task 01 (LlamaParse PDF Processing Pipeline), Task 08 (Table Fragmentation), Task 09 (Text Integrity)
- **Blocking**: []
- **Blocked by**: []

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [x] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [x] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] [Component 1](#component-1) - CLI Argument Updates
    - [x] [Component 2](#component-2) - PDFProcessor Logic Updates
- [x] 🧪 [Test Cases](#🧪-test-cases) - Manual verification steps
- [x] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **Current CLI**: `src/cli/parse_documents.py`
- **Processor**: `src/core/src/core/document_processing/pdf_processor.py`

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

Currently, the `parse-docs` CLI executes the full PDF processing pipeline. There is no way to selectively disable specific steps (e.g., for debugging, performance testing, or when specific features are not needed). The user wants to add CLI flags to control the execution of:
-   **Table Merging** (`--skip-table-merge`)
-   **Text Integrity Restoration** (`--skip-text-merge`)
-   **Table Summarization** (`--skip-table-summarization`)

### Mục tiêu

1.  Update `parse-docs` CLI to accept 3 new optional arguments.
2.  Update `PDFProcessor` to accept configuration options for enabling/disabling these steps.
3.  Conditionally execute pipeline steps based on the configuration.
4.  Ensure backward compatibility (default behavior remains running all steps).
5.  Renumber pipeline steps for consistency (Step 5.5 -> Step 6).

### Success Metrics / Acceptance Criteria

-   **CLI Usability**: User can pass `--skip-table-merge`, `--skip-text-merge`, `--skip-table-summarization` to `parse-docs`.
-   **Correct Execution**:
    -   If `--skip-table-merge` is passed, Steps 3, 4, 5 are skipped.
    -   If `--skip-text-merge` is passed, Step 6 (formerly 5.5) is skipped.
    -   If `--skip-table-summarization` is passed, Step 8 (formerly 7) is skipped.
-   **Default Behavior**: If no flags are passed, all steps run as usual.

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

1.  **CLI Layer**: Use `argparse` to add boolean flags with `action='store_true'`.
2.  **Processor Layer**: Update `process_pdf` and `process_pdf_batch` signatures to accept explicit boolean flags.
3.  **Logic Layer**: Wrap relevant code blocks in `if not skip_...:` checks and renumber steps.

### Stack công nghệ

-   **Python argparse**: Standard library for CLI parsing.
-   **Python AsyncIO**: For passing arguments through async pipeline.
-   **tqdm**: For progress bar visualization (restored in batch processing).

### Issues & Solutions

1.  **Argument Naming** → Changed from `--no-X` to `--skip-X` for clarity and consistency.
    -   `--skip-table-merge`
    -   `--skip-text-merge`
    -   `--skip-table-summarization`

2.  **Step Renumbering** →
    -   Step 5.5 (Text Integrity) -> Step 6
    -   Step 6 (Re-detect) -> Step 7
    -   Step 7 (Summarize) -> Step 8
    -   Step 8 (Update Files) -> Step 9
    -   Step 9 (Reports) -> Step 10

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: CLI Updates**
1.  Modify `src/cli/parse_documents.py`.
2.  Add arguments `--skip-table-merge`, `--skip-text-merge`, `--skip-table-summarization`.
3.  Pass values to `processor.process_pdf_batch`.

### **Phase 2: Processor Updates**
1.  Modify `src/core/src/core/document_processing/pdf_processor.py`.
2.  Update `process_pdf_batch` to accept explicit arguments and pass to `process_pdf`.
3.  Restore `tqdm` progress bar in `process_pdf_batch`.
4.  Update `process_pdf` to accept new args.
5.  Add conditional logic and renumber steps 6-10.

### **Phase 3: Verification**
1.  Run `parse-docs --file ... --skip-table-merge` and verify logs.
2.  Run `parse-docs --file ... --skip-text-merge` and verify logs.
3.  Run `parse-docs --file ... --skip-table-summarization` and verify logs.

------------------------------------------------------------------------

## 📋 Implementation Detail

### Component 1: CLI Argument Updates

#### Requirement 1 - Update `parse_documents.py`
-   **File**: `src/cli/parse_documents.py`
-   **Changes**:
    ```python
    parser.add_argument(
        "--skip-table-merge",
        action="store_true",
        help="Skip table fragmentation merging step",
    )
    parser.add_argument(
        "--skip-text-merge",
        action="store_true",
        help="Skip cross-page text integrity restoration step",
    )
    parser.add_argument(
        "--skip-table-summarization",
        action="store_true",
        help="Skip table summarization step",
    )
    
    # ... inside async_main ...
    await processor.process_pdf_batch(
        file_paths_to_process,
        skip_table_merge=args.skip_table_merge,
        skip_text_merge=args.skip_text_merge,
        skip_table_summarization=args.skip_table_summarization,
    )
    ```

### Component 2: PDFProcessor Logic Updates

#### Requirement 1 - Update `process_pdf_batch`
-   **File**: `src/core/src/core/document_processing/pdf_processor.py`
-   **Changes**: Explicit arguments and restored progress bar.
    ```python
    async def process_pdf_batch(
        self,
        file_paths: List[str],
        skip_table_merge: bool = False,
        skip_text_merge: bool = False,
        skip_table_summarization: bool = False,
    ) -> List[PDFParseResult]:
        # ...
        from tqdm import tqdm
        with tqdm(total=len(file_paths), desc="Processing PDFs") as pbar:
            for file_path in file_paths:
                # ... call process_pdf with explicit args ...
                pbar.update(1)
    ```

#### Requirement 2 - Update `process_pdf`
-   **File**: `src/core/src/core/document_processing/pdf_processor.py`
-   **Changes**:
    ```python
    async def process_pdf(
        self, 
        file_path: str, 
        skip_table_merge: bool = False,
        skip_text_merge: bool = False,
        skip_table_summarization: bool = False
    ) -> PDFParseResult:
        # ...
        
        # Step 3, 4, 5: Table Merging
        if not skip_table_merge:
            # ... existing logic ...
        else:
            logger.info("Skipping table merging (Steps 3-5) as requested")
            
        # Step 6: Text Integrity (Renumbered from 5.5)
        if not skip_text_merge:
            logger.info("Step 6: Restoring cross-page text integrity")
            # ...
        else:
            logger.info("Skipping text integrity restoration (Step 6) as requested")
            
        # Step 7: Re-detect tables (Renumbered from 6)
        
        # Step 8: Summarization (Renumbered from 7)
        if not skip_table_summarization:
            # ...
        else:
            logger.info("Skipping table summarization (Step 8) as requested")

        # Step 9: Update Files (Renumbered from 8)

        # Step 10: Reports (Renumbered from 9)
    ```

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Default Execution
-   **Command**: `parse-docs --file test.pdf`
-   **Expected**: All steps (1-10) execute.

### Test Case 2: Skip Table Merge
-   **Command**: `parse-docs --file test.pdf --skip-table-merge`
-   **Expected**: Steps 3, 4, 5 skipped. Logs show "Skipping table merging...". Steps 6-10 execute.

### Test Case 3: Skip Text Merge
-   **Command**: `parse-docs --file test.pdf --skip-text-merge`
-   **Expected**: Step 6 skipped. Logs show "Skipping text integrity...". Steps 3-5 and 7-10 execute.

### Test Case 4: Skip Summarization
-   **Command**: `parse-docs --file test.pdf --skip-table-summarization`
-   **Expected**: Step 8 skipped. Logs show "Skipping table summarization...". Steps 3-7 and 9-10 execute.

------------------------------------------------------------------------

## 📝 Task Summary

### What Was Implemented

1.  **CLI Updates**:
    -   Renamed flags to `--skip-table-merge`, `--skip-text-merge`, `--skip-table-summarization`.
    -   Updated `src/cli/parse_documents.py` to pass these flags explicitly.

2.  **Processor Updates**:
    -   Updated `PDFProcessor.process_pdf` to accept explicit skip flags.
    -   Renumbered pipeline steps:
        -   Step 5.5 -> Step 6 (Text Integrity)
        -   Step 6 -> Step 7 (Re-detect)
        -   Step 7 -> Step 8 (Summarize)
        -   Step 8 -> Step 9 (Update Files)
        -   Step 9 -> Step 10 (Reports)
    -   Updated `PDFProcessor.process_pdf_batch` to accept explicit arguments and restored `tqdm` progress bar.
    -   Restored detailed report generation logic in Step 10.

### Verification Results

-   **Test 1: `--skip-table-merge`**: Verified that Steps 3, 4, 5 are skipped.
-   **Test 2: `--skip-text-merge`**: Verified that Step 6 is skipped.
-   **Test 3: `--skip-table-summarization`**: Verified that Step 8 is skipped.
-   **Default Behavior**: Verified that all steps run when no flags are provided.

**Test Output**:
```bash
# --skip-table-merge
INFO | Skipping table merging (Steps 3-5) as requested

# --skip-text-merge
INFO | Skipping text integrity restoration (Step 6) as requested

# --skip-table-summarization
INFO | Skipping table summarization (Step 8) as requested
```
