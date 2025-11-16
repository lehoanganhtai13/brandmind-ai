# Task 07: Enhance Document Metadata in Parsing Pipeline

## 📌 Metadata

- **Epic**: Document Processing
- **Priority**: Medium
- **Estimated Effort**: 0.5 days
- **Team**: Backend
- **Related Tasks**: -
- **Blocking**: []
- **Blocked by**: -

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [x] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [x] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] ✅ [Component 1](#component-1) - Update Metadata Loading
    - [x] ✅ [Component 2](#component-2) - Update PDF Parsing Logic
    - [x] ✅ [Component 3](#component-3) - Update Markdown Template
- [ ] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation
- [ ] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards with comprehensive documentation

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- The current document processing pipeline parses PDFs and generates per-page markdown files.
- The metadata embedded in these markdown files includes the author's name, which is retrieved from `data/raw_documents/document_metadata.json`.
- However, the markdown files currently only display the document's filename (e.g., `Kotler_and_Armstrong_Principles_of_Marketing_test`) rather than its true, human-readable title (e.g., "Principles of Marketing 17th Edition").
- This makes the generated content less user-friendly and harder to identify.

### Mục tiêu

Enhance the document parsing pipeline to include the document's true title (`document_title`) in the metadata of each generated markdown page. This will improve the clarity and usability of the parsed documents.

### Success Metrics / Acceptance Criteria

- **Metadata Enrichment**: The `document_metadata.json` file is correctly parsed to extract `document_title` in addition to `author`.
- **Template Update**: The markdown template used for generating page files includes the `document_title`.
- **Output Verification**: Newly generated `page_*.md` files correctly display the `document_title` in their header.
- **Data Integrity**: The `PDFParseResult` model correctly includes the `document_title` in its `metadata` field for downstream use.
- **No Regressions**: The document parsing process continues to function correctly without errors after the changes.

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Metadata-Driven Content Generation**: We will modify the `LlamaPDFProcessor` to load the complete metadata object (including `author` and `document_title`) for each document. This metadata will then be passed to the markdown generation step, where an updated template will render the `document_title` in the header of each page file.

### Stack công nghệ

- **Python**: Core programming language.
- **Pydantic**: For data modeling (`PDFParseResult`).
- **Loguru**: For logging.
- No new technologies are required.

### Issues & Solutions

1. **Challenge**: The current metadata loading function only extracts the `author`.
   → **Solution**: Refactor `_load_author_metadata` to `_load_document_metadata` and change its return structure to a dictionary containing both `author` and `document_title`.
2. **Challenge**: The markdown template and parsing logic do not account for the document title.
   → **Solution**: Update the `PAGE_MARKDOWN_TEMPLATE` constant and the logic in the `parse_pdf` method to correctly format and insert the `document_title`.

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Code Implementation**
1. **Refactor Metadata Loading**:
   - In `llama_parser.py`, rename `_load_author_metadata` to `_load_document_metadata`.
   - Update its logic to return a dictionary mapping the filename to an object containing both `author` and `document_title`.
2. **Update Parsing Logic**:
   - In `llama_parser.py`, modify the `parse_pdf` method to retrieve the full metadata object (author and title).
   - Implement fallback logic to handle cases where metadata might be missing.
3. **Update Markdown Template**:
   - In `llama_parser.py`, add a placeholder for `document_title` to the `PAGE_MARKDOWN_TEMPLATE`.
4. **Update Data Model**:
   - In `llama_parser.py`, ensure `document_title` is added to the `metadata` dictionary within the returned `PDFParseResult` object.

### **Phase 2: Verification**
1. **Run Manual Test**:
   - Delete the existing `data/parsed_documents` directory.
   - Run the `parse-docs` script (e.g., `make parse-docs`).
2. **Inspect Output**:
   - Check the content of the newly generated `page_*.md` files to confirm that the `document_title` is present and correct in the header.

------------------------------------------------------------------------

## 📋 Implementation Detail

### Component 1

#### Requirement 1 - Update Metadata Loading Logic
- **Requirement**: The system must load both `author` and `document_title` from `document_metadata.json`.
- **Implementation**:
  - `src/core/src/core/document_processing/llama_parser.py`
  ```python
  # Rename _load_author_metadata to _load_document_metadata
  # and adjust the logic.
  
  class LlamaPDFProcessor:
      def __init__(self, ...):
          # ...
          self.document_metadata = self._load_document_metadata() # Renamed attribute

      def _load_document_metadata(self):
          """Loads document metadata (author and title) from the JSON file."""
          metadata_path = Path("data/raw_documents/document_metadata.json")
          if not metadata_path.exists():
              logger.warning(f"Document metadata file not found at {metadata_path}")
              return {}
          try:
              with open(metadata_path, "r", encoding="utf-8") as f:
                  metadata_list = json.load(f)
              # New structure: map filename to a dict of metadata
              return {
                  item["document_name"]: {
                      "author": item.get("author", "Unknown"),
                      "document_title": item.get("original_name", Path(item["document_name"]).stem)
                  }
                  for item in metadata_list
              }
          except (json.JSONDecodeError, KeyError) as e:
              logger.error(f"Failed to load or parse document metadata: {e}")
              return {}
  ```
- **Acceptance Criteria**:
  - [ ] The `_load_document_metadata` method correctly parses the JSON and returns a dictionary with the new structure.
  - [ ] The `self.document_metadata` attribute holds the loaded data.

### Component 2

#### Requirement 1 - Update PDF Parsing Logic to Use New Metadata
- **Requirement**: The `parse_pdf` method must use the new metadata structure to retrieve `author` and `document_title`.
- **Implementation**:
  - `src/core/src/core/document_processing/llama_parser.py`
  ```python
  # In parse_pdf method
  async def parse_pdf(self, file_path: str, **options) -> PDFParseResult:
      # ...
      doc_name = path.stem
      
      # Retrieve metadata using the new structure
      metadata = self.document_metadata.get(path.name, {})
      author = metadata.get("author", "Unknown")
      document_title = metadata.get("document_title", doc_name.replace("_", " ").title())

      # ... (rest of the function)

      # Pass document_title to the template
      page_content = PAGE_MARKDOWN_TEMPLATE.format(
          # ...,
          document_title=document_title,
          author=author,
          # ...
      )

      # ...

      # Add to the result metadata
      return PDFParseResult(
          # ...,
          metadata={
              "parser_version": "llama-parse",
              "config": self.config,
              "file_extension": path.suffix,
              "timestamp": timestamp,
              "author": author,
              "document_title": document_title, # Add new field
          },
      )
  ```
- **Acceptance Criteria**:
  - [ ] `author` and `document_title` are correctly extracted from the loaded metadata.
  - [ ] Fallback values are used if a document's metadata is not found.
  - [ ] The `document_title` is passed to the markdown template.
  - [ ] The `PDFParseResult` includes `document_title` in its metadata dictionary.

### Component 3

#### Requirement 1 - Update Markdown Template
- **Requirement**: The markdown template must be updated to display the document title.
- **Implementation**:
  - `src/core/src/core/document_processing/llama_parser.py`
  ```python
  # Modify the PAGE_MARKDOWN_TEMPLATE constant
  
  PAGE_MARKDOWN_TEMPLATE = """# Page {page_number}

**Document Title**: {document_title}
**Author**: {author}
**Original File**: {original_file_path}
**Page Number**: {page_number}/{total_pages}
**Processing Time**: {processing_timestamp}

---

{page_text}"""
  ```
- **Acceptance Criteria**:
  - [ ] The `PAGE_MARKDOWN_TEMPLATE` constant is updated with the `document_title` field.
  - [ ] The `Document` field is renamed to `Document Title` for clarity.

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Verify Correct Metadata in Output Files
- **Purpose**: To ensure that the `document_title` and `author` are correctly written to the generated markdown page files.
- **Steps**:
  1. Delete the `data/parsed_documents` directory to ensure a clean run.
  2. Execute the command `make parse-docs`.
  3. Open one of the newly generated files (e.g., `data/parsed_documents/Kotler_and_Armstrong_Principles_of_Marketing_test_.../page_1.md`).
  4. Inspect the header of the markdown file.
- **Expected Result**:
  - The header should contain a line: `**Document Title**: Principles of Marketing 17th Edition`.
  - The header should contain a line: `**Author**: Philip Kotler, Gary Armstrong`.
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation to document what was actually accomplished.

### What Was Implemented

**Components Completed**:
- [x] **Component 1**: Updated metadata loading logic to retrieve both author and document_title.
- [x] **Component 2**: Modified PDF parsing logic to use the new metadata structure and pass document_title to the template and PDFParseResult.
- [x] **Component 3**: Updated the markdown template to display the document title.

### Files Created/Modified:
```
data/raw_documents/
├── document_metadata.json      # Renamed 'original_name' to 'document_title'
src/core/src/core/document_processing/
├── llama_parser.py             # Refactored metadata loading and updated parsing logic
tasks/
└── task_07.md                  # Updated task progress and summary
```

**Key Features Delivered**:
1. **Enriched Document Metadata**: Generated markdown files now include the human-readable document title, improving clarity and usability.
2. **Consistent Naming**: Standardized metadata field from 'original_name' to 'document_title' across JSON and code.

### Technical Highlights

**Architecture Decisions**:
- **Centralized Metadata**: Consolidated document metadata loading within LlamaPDFProcessor for consistent access.
- **Template-Driven Output**: Utilized a flexible markdown template for easy customization of output format.

**Documentation Added**:
- [x] All functions have comprehensive docstrings
- [x] Complex business logic is well-commented
- [x] Module-level documentation explains purpose
- [x] Type hints are complete and accurate

### Validation Results

**Test Coverage**:
- [ ] All test cases pass
- [ ] Edge cases handled
- [ ] Error scenarios tested
- [ ] Performance benchmarks met

**Deployment Notes**:
- No special deployment considerations.
- No configuration changes required.
- No database migrations needed.
