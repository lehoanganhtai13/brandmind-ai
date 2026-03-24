# Task 39: Document Generation Suite — PDF, DOCX, PPTX, XLSX, Markdown

## 📌 Metadata

- **Epic**: Brand Strategy — Tools
- **Priority**: High (P1 — generate_document; P2 — generate_presentation; P3 — export_to_markdown)
- **Estimated Effort**: 1.5 weeks
- **Team**: Backend
- **Related Tasks**: Task 38 (generate_image — images embedded in docs), Task 45 (Communication Skill — deliverable assembly)
- **Blocking**: Task 41 (Document Generator sub-agent), Task 45 (Communication & Planning Skill)
- **Blocked by**: None

### ✅ Progress Checklist

- [x] 🤖 [Agent Protocol](#-agent-protocol) — Read and confirm before starting
- [x] 🎯 [Context & Goals](#🎯-context--goals)
- [x] 🛠 [Solution Design](#🛠-solution-design)
- [x] 🔬 [Pre-Implementation Research](#-pre-implementation-research) — Findings logged before coding
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan)
- [x] 📋 [Implementation Detail](#📋-implementation-detail)
    - [x] ✅ [Component 1: Brand Strategy Document Templates](#component-1-brand-strategy-document-templates)
    - [x] ✅ [Component 2: generate_document Tool (PDF + DOCX)](#component-2-generate_document-tool)
    - [x] ✅ [Component 3: generate_presentation Tool (PPTX)](#component-3-generate_presentation-tool)
    - [x] ✅ [Component 4: export_to_markdown Tool](#component-4-export_to_markdown-tool)
    - [x] ✅ [Component 5: generate_spreadsheet Tool (XLSX)](#component-5-generate_spreadsheet-tool)
- [ ] 🧪 [Test Execution Log](#-test-execution-log) — All tests run and results recorded
- [ ] 📊 [Decision Log](#-decision-log) — Key decisions documented
- [ ] 📝 [Task Summary](#📝-task-summary)

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards (see Agent Protocol section)
- **Prompt Engineering Standards**: `tasks/prompt_engineering_standards.md`
- **Blueprint Reference**: `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — Section 5.3, Tools 11-12, 17
- **fpdf2 docs**: https://py-pdf.github.io/fpdf2/
- **python-docx docs**: https://python-docx.readthedocs.io/
- **python-pptx docs**: https://python-pptx.readthedocs.io/
- **openpyxl docs**: https://openpyxl.readthedocs.io/
- **XLSX Skill Reference**: `.claude/skills/xlsx/SKILL.md` — formula best practices
- **Blueprint Phase 5 Document Structure**: Section 4.5, Skill 4 — "Document Assembly" subsection
- **Output Directory Pattern**: Centralized via `BRANDMIND_OUTPUT_DIR` env var → `./brandmind-output/` default

------------------------------------------------------------------------

## 🤖 Agent Protocol

> **MANDATORY**: Read this section in full before starting any implementation work.

### Rule 1 — Research Before Coding

Before writing any code for a component:
1. Read all files referenced in "Reference Documentation" above
2. Read existing code in `src/shared/src/shared/agent_tools/` to understand tool function conventions
3. Fetch documentation for external libraries: fpdf2, python-docx, python-pptx, openpyxl
4. Read `.claude/skills/xlsx/SKILL.md` for Excel best practices (formula-driven, not hardcoded values)
5. Log your findings in [Pre-Implementation Research](#-pre-implementation-research) before proceeding
6. **Do NOT assume or invent** library API behavior — verify against actual documentation

### Rule 2 — Ask, Don't Guess

When encountering any of the following, **STOP and ask the user** before proceeding:

- Font rendering issues (especially Vietnamese diacritics in PDF)
- Library version conflicts or API changes
- Document layout decisions that significantly affect user experience
- Unclear mapping between phase_outputs structure and document sections

Format: State the issue clearly, present your options with pros/cons, and ask for a decision.

### Rule 3 — Update Progress As You Go

After completing each component or sub-task:
1. Check off the corresponding item in the Progress Checklist
2. Update the component status emoji: ⏳ Pending → 🚧 In Progress → ✅ Done
3. Fill in the Test Execution Log with actual results as tests run
4. Log any significant decisions in the Decision Log

### Rule 4 — Production-Grade Code Standards

All code MUST meet these standards (no exceptions):

| Standard | Requirement |
|----------|-------------|
| **Docstrings** | Every module, class, and function — purpose, args, returns, business context |
| **Comments** | Inline comments for complex logic, business rules, non-obvious decisions |
| **String quotes** | Double quotes `"` consistently throughout |
| **Type hints** | All function signatures — no `Any` unless truly unavoidable |
| **Naming** | PEP 8 — `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE` constants |
| **Line length** | Max 100 characters |
| **Language** | English only — all code, comments, docstrings |
| **Modularity** | Single responsibility — break large functions into focused, reusable units |

### Rule 5 — Excel-Specific Standards (Component 5)

From `.claude/skills/xlsx/SKILL.md` — apply when building generate_spreadsheet:

- **CRITICAL**: Use Excel **formulas** for all calculations — NEVER hardcode computed values in Python. The spreadsheet must be dynamic: edit an input cell and dependent cells recalculate automatically.
- **Color coding**: Blue (#4472C4) for user-editable input cells, Black for formula cells, Green (#548235) for cross-sheet references.
- **Number formatting**: Currency with `$#,##0`, percentages with `0.0%`, dates with `YYYY-MM-DD`.
- **Structure**: Freeze top row (headers), auto-fit column widths, named sheets with clear purpose.
- **Formulas**: Use `=SUM()`, `=AVERAGE()`, `=IF()`, `=VLOOKUP()` — build real financial models, not static tables.

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Phase 5 (Brand Strategy Plan & Deliverables) tạo 3 outputs chính: Brand Strategy Document (PDF/DOCX), Pitch Deck (PPTX), và structured Markdown export
- Document cần professional quality — kiểu consulting firm output (cover page, TOC, branded headers/footers, embedded images)
- Blueprint Section 4.5 định nghĩa rõ cấu trúc 10-section document:
  1. Cover Page → 2. Executive Summary → 3. Business Context → 4. Market Intelligence → 5. Brand Strategy Core → 6. Brand Identity → 7. Communication Framework → 8. Implementation Roadmap → 9. KPI & Measurement → 10. Appendices
- PPTX pitch deck: 10-15 slides summary cho stakeholder presentation
- Markdown export: cho dễ share/edit trong các tools khác (Notion, GitHub, etc.)
- Cần install 3 packages mới: `fpdf2`, `python-docx`, `python-pptx`

### Mục tiêu

1. generate_document tool tạo professional PDF/DOCX từ structured phase outputs
2. generate_presentation tool tạo brand strategy pitch deck PPTX
3. export_to_markdown tool xuất structured data thành well-formatted markdown
4. generate_spreadsheet tool tạo dynamic Excel workbooks (competitor analysis, KPI tracking, content calendar, budgets)
5. Brand Strategy document template cho F&B domain

### Success Metrics / Acceptance Criteria

- **Quality**: PDF output looks professional — branded, consistent, readable
- **Completeness**: Document covers all 10 sections defined in blueprint
- **Flexibility**: Accept structured dict input → produce formatted output
- **Embedding**: Images (mood boards, Brand Key) embedded trong document
- **Usability**: DOCX editable by user in Word/Google Docs without broken formatting

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Template-Based Architecture**: Định nghĩa brand strategy document template (section structures, styles, layouts) → populate từ structured phase output. Mỗi format (PDF, DOCX, PPTX) có builder riêng nhưng share chung template definition.

### New Dependencies

| Package | Purpose | License | Install |
|---------|---------|---------|---------|
| `fpdf2` | PDF generation | LGPL v3 | `uv add fpdf2` (shared package) |
| `python-docx` | DOCX generation | MIT | `uv add python-docx` (shared package) |
| `python-pptx` | PPTX generation | MIT | `uv add python-pptx` (shared package) |
| `openpyxl` | XLSX generation with formulas | MIT | `uv add openpyxl` (shared package) |

### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Document templates | `src/shared/src/shared/agent_tools/document/templates/` | Template definitions |
| PDF Builder | `src/shared/src/shared/agent_tools/document/pdf_builder.py` | fpdf2-based PDF generation |
| DOCX Builder | `src/shared/src/shared/agent_tools/document/docx_builder.py` | python-docx-based DOCX generation |
| PPTX Builder | `src/shared/src/shared/agent_tools/document/pptx_builder.py` | python-pptx-based PPTX generation |
| generate_document tool | `src/shared/src/shared/agent_tools/document/generate_document.py` | Tool function |
| generate_presentation tool | `src/shared/src/shared/agent_tools/document/generate_presentation.py` | Tool function |
| generate_spreadsheet tool | `src/shared/src/shared/agent_tools/document/generate_spreadsheet.py` | Excel tool function |
| export_to_markdown tool | `src/shared/src/shared/agent_tools/document/export_to_markdown.py` | Tool function |

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Dependencies & Templates**
1. Add fpdf2, python-docx, python-pptx to shared package
2. Define brand strategy document template (section structures, content mapping)

### **Phase 2: PDF & DOCX Builders**
1. PDF Builder: cover page, TOC, section rendering, table formatting, image embedding
2. DOCX Builder: same structure, Word-native formatting

### **Phase 3: PPTX Builder & Markdown Export**
1. PPTX Builder: slide layouts, brand strategy deck template
2. Markdown exporter: pure Python string formatting

### **Phase 4: Tool Layer**
1. Plain functions wrapping builders
2. Integration testing

------------------------------------------------------------------------

## 🔬 Pre-Implementation Research

> **Agent**: Complete this section BEFORE writing any implementation code.
> Log your findings here so the user can verify your understanding is correct.

### Codebase Audit

- **Files read**: [List existing files — agent_tools/ structure, config/system_config.py, existing tool function patterns]
- **Relevant patterns found**: [How other tools handle output paths, error handling, logging, config access]
- **Potential conflicts**: [Any existing document generation code, package conflicts]

### External Library / API Research

- **fpdf2**: [Version, key APIs — FPDF class, add_page(), cell(), multi_cell(), image(), set_font()]
- **python-docx**: [Version, key APIs — Document(), add_heading(), add_paragraph(), add_table(), styles]
- **python-pptx**: [Version, key APIs — Presentation(), add_slide(), placeholder manipulation, shapes]
- **openpyxl**: [Version, key APIs — Workbook(), ws.cell(), ws.append(), Formula strings, PatternFill, Font, Alignment]
- **Vietnamese font support**: [fpdf2 Unicode font handling for PDF Vietnamese text]

### Unknown / Risks Identified

- [ ] Verify fpdf2 handles Vietnamese diacritics with Unicode font (DejaVu Sans or NotoSans)
- [ ] Confirm python-docx styles survive Google Docs import
- [ ] Test openpyxl formula recalculation behavior (formulas saved but may need LibreOffice to recalculate)
- [ ] Determine optimal image DPI for PDF embedding (mood boards, Brand Key)

### Research Status

- [ ] All referenced documentation read
- [ ] Library APIs verified for all 4 formats
- [ ] Vietnamese text rendering tested in PDF
- [ ] No unresolved ambiguities remain → Ready to implement

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards Reminder**: Apply the standards from Agent Protocol Rule 4 to every file.
> Excel generation follows Rule 5. Test specifications are written BEFORE implementation.

### Component 1: Brand Strategy Document Templates

#### Requirement 1 - Document Structure Definition
- **Requirement**: Define the standard brand strategy document structure from Blueprint Section 4.5
- **Implementation**:
  - `src/shared/src/shared/agent_tools/document/templates/brand_strategy.py`
  ```python
  from pydantic import BaseModel, Field


  class DocumentSection(BaseModel):
      """A section in the brand strategy document."""
      id: str
      title: str
      subtitle: str = ""
      content_key: str  # Key in phase_outputs dict
      required: bool = True
      page_break_before: bool = True


  class BrandStrategyTemplate(BaseModel):
      """
      Template for the Brand Strategy Document.

      Defines the 10-section structure per Blueprint Section 4.5:
      1. Cover Page
      2. Executive Summary
      3. Business Context & Problem Statement (Phase 0)
      4. Market Intelligence Summary (Phase 1)
      5. Brand Strategy Core (Phase 2)
      6. Brand Identity & Expression (Phase 3)
      7. Communication Framework (Phase 4)
      8. Implementation Roadmap (Phase 5)
      9. KPI & Measurement Plan (Phase 5)
      10. Appendices
      """
      brand_name: str
      prepared_by: str = "BrandMind AI"
      date: str = ""  # auto-filled
      brand_colors: list[str] = Field(
          default_factory=lambda: ["#1B365D", "#F5F0E8", "#D4A84B"]
      )  # navy, cream, gold

      sections: list[DocumentSection] = Field(
          default_factory=lambda: [
              DocumentSection(
                  id="cover",
                  title="Brand Strategy",
                  subtitle="Professional Brand Strategy Document",
                  content_key="cover",
                  page_break_before=False,
              ),
              DocumentSection(
                  id="executive_summary",
                  title="Executive Summary",
                  content_key="executive_summary",
              ),
              DocumentSection(
                  id="business_context",
                  title="Business Context & Problem Statement",
                  content_key="phase_0_output",
              ),
              DocumentSection(
                  id="brand_equity_audit",
                  title="Brand Equity Audit",
                  content_key="phase_0_5_output",
                  required=False,  # Only for refresh/repositioning/rebrand
              ),
              DocumentSection(
                  id="market_intelligence",
                  title="Market Intelligence",
                  content_key="phase_1_output",
              ),
              DocumentSection(
                  id="brand_strategy_core",
                  title="Brand Strategy Core",
                  subtitle="Positioning, Value Architecture & Brand Essence",
                  content_key="phase_2_output",
              ),
              DocumentSection(
                  id="brand_identity",
                  title="Brand Identity & Expression",
                  subtitle="Personality, Voice, Visual Identity & Naming",
                  content_key="phase_3_output",
              ),
              DocumentSection(
                  id="communication",
                  title="Communication Framework",
                  content_key="phase_4_output",
              ),
              DocumentSection(
                  id="roadmap",
                  title="Implementation Roadmap",
                  content_key="implementation_roadmap",
              ),
              DocumentSection(
                  id="kpi",
                  title="KPI & Measurement Plan",
                  content_key="kpis",
              ),
              DocumentSection(
                  id="appendices",
                  title="Appendices",
                  content_key="appendices",
                  required=False,
              ),
          ]
      )


  class PresentationSlideTemplate(BaseModel):
      """A slide in the brand strategy pitch deck."""
      id: str
      layout: str  # "title", "content", "two_column", "image", "table"
      title: str
      content_key: str
      required: bool = True  # False for conditional slides (e.g., brand equity audit)
      notes: str = ""  # Speaker notes


  class BrandStrategyDeckTemplate(BaseModel):
      """Template for the PPTX brand strategy pitch deck (10-15 slides)."""
      brand_name: str
      brand_colors: list[str] = Field(
          default_factory=lambda: ["#1B365D", "#F5F0E8", "#D4A84B"]
      )
      slides: list[PresentationSlideTemplate] = Field(
          default_factory=lambda: [
              PresentationSlideTemplate(
                  id="title", layout="title",
                  title="Brand Strategy",
                  content_key="cover",
              ),
              PresentationSlideTemplate(
                  id="agenda", layout="content",
                  title="Agenda",
                  content_key="agenda",
              ),
              PresentationSlideTemplate(
                  id="business_context", layout="content",
                  title="Business Context",
                  content_key="phase_0_output",
              ),
              PresentationSlideTemplate(
                  id="brand_equity_audit", layout="content",
                  title="Brand Equity Audit",
                  content_key="phase_0_5_output",
                  required=False,
              ),
              PresentationSlideTemplate(
                  id="market_overview", layout="two_column",
                  title="Market Overview",
                  content_key="phase_1_output.market_overview",
              ),
              PresentationSlideTemplate(
                  id="competitive", layout="table",
                  title="Competitive Landscape",
                  content_key="phase_1_output.competitor_analysis",
              ),
              PresentationSlideTemplate(
                  id="target_audience", layout="content",
                  title="Target Audience",
                  content_key="phase_1_output.target_audience",
              ),
              PresentationSlideTemplate(
                  id="positioning", layout="content",
                  title="Brand Positioning",
                  content_key="phase_2_output",
              ),
              PresentationSlideTemplate(
                  id="identity", layout="image",
                  title="Brand Identity",
                  content_key="phase_3_output",
              ),
              PresentationSlideTemplate(
                  id="communication", layout="two_column",
                  title="Communication Framework",
                  content_key="phase_4_output",
              ),
              PresentationSlideTemplate(
                  id="roadmap", layout="table",
                  title="Implementation Roadmap",
                  content_key="implementation_roadmap",
              ),
              PresentationSlideTemplate(
                  id="kpis", layout="table",
                  title="KPIs & Measurement",
                  content_key="kpis",
              ),
              PresentationSlideTemplate(
                  id="next_steps", layout="content",
                  title="Next Steps",
                  content_key="next_steps",
              ),
          ]
      )
  ```
- **Acceptance Criteria**:
  - [ ] Template covers all 10 document sections from blueprint
  - [ ] Deck template covers 10-15 slides
  - [ ] Templates are configurable with brand colors

### Component 2: generate_document Tool

#### Requirement 1 - PDF Builder
- **Requirement**: Generate professional PDF using fpdf2
- **Implementation**:
  - `src/shared/src/shared/agent_tools/document/pdf_builder.py`
  ```python
  import os
  from datetime import date
  from pathlib import Path

  from fpdf import FPDF

  # Path to bundled Unicode font for Vietnamese diacritics
  _FONT_DIR = Path(__file__).parent / "fonts"
  _NOTO_SANS_REGULAR = str(_FONT_DIR / "NotoSans-Regular.ttf")
  _NOTO_SANS_BOLD = str(_FONT_DIR / "NotoSans-Bold.ttf")


  def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
      """Convert '#RRGGBB' hex string to (r, g, b) int tuple."""
      hex_color = hex_color.lstrip("#")
      return (
          int(hex_color[0:2], 16),
          int(hex_color[2:4], 16),
          int(hex_color[4:6], 16),
      )


  class BrandStrategyPDF(FPDF):
      """Extended FPDF with branded header/footer and page numbering."""

      def __init__(self, brand_name: str, brand_colors: list[str]):
          super().__init__()
          self.brand_name = brand_name
          self.primary_rgb = _hex_to_rgb(brand_colors[0])
          self.accent_rgb = _hex_to_rgb(brand_colors[2]) if len(brand_colors) > 2 else (180, 150, 60)

      def header(self):
          """Branded header on every page except page 1 (cover)."""
          if self.page_no() == 1:
              return
          self.set_font("NotoSans", "", 8)
          self.set_text_color(*self.primary_rgb)
          self.cell(0, 8, self.brand_name, align="L")
          self.cell(0, 8, "Brand Strategy Document", align="R", new_x="LMARGIN", new_y="NEXT")
          self.set_draw_color(*self.accent_rgb)
          self.line(10, self.get_y(), 200, self.get_y())
          self.ln(4)

      def footer(self):
          """Page number footer on every page except page 1."""
          if self.page_no() == 1:
              return
          self.set_y(-15)
          self.set_font("NotoSans", "", 8)
          self.set_text_color(128, 128, 128)
          self.cell(0, 10, f"Page {self.page_no()}", align="C")


  class BrandStrategyPDFBuilder:
      """
      Builds professional brand strategy PDF documents using fpdf2.

      Features:
          - Branded cover page with brand name and colors
          - Auto-generated Table of Contents
          - Section headers with brand color accent
          - Tables (competitor analysis, KPIs, roadmap)
          - Embedded images (mood boards, Brand Key)
          - Page numbers and branded footer
          - Unicode support for Vietnamese text
      """

      def __init__(self):
          self.pdf: BrandStrategyPDF | None = None
          self.section_pages: list[tuple[str, int]] = []

      def build(
          self,
          content: dict,
          template: "BrandStrategyTemplate",
          output_path: str,
          images: dict[str, str] | None = None,
      ) -> str:
          """
          Build the complete PDF document.

          Args:
              content: Dict with phase outputs keyed by content_key.
              template: Document template defining sections and branding.
              output_path: Output file path.
              images: Dict of section_id -> file_path for embedding.

          Returns:
              Absolute path to generated PDF.
          """
          images = images or {}

          # Use local date var instead of mutating template
          doc_date = template.date or date.today().strftime("%Y-%m-%d")

          self.pdf = BrandStrategyPDF(
              brand_name=template.brand_name,
              brand_colors=template.brand_colors,
          )

          # Register Unicode fonts for Vietnamese diacritics
          if os.path.isfile(_NOTO_SANS_REGULAR):
              self.pdf.add_font("NotoSans", "", _NOTO_SANS_REGULAR, uni=True)
          else:
              # Fallback — Helvetica has no Vietnamese support, but
              # NotoSans font files are required for proper diacritics.
              logger.warning(
                  f"NotoSans font not found at {_NOTO_SANS_REGULAR}. "
                  f"Vietnamese diacritics will not render correctly."
              )
              # Use Helvetica as fallback font alias
              self._font_family = "Helvetica"
          if os.path.isfile(_NOTO_SANS_BOLD):
              self.pdf.add_font("NotoSans", "B", _NOTO_SANS_BOLD, uni=True)

          self.pdf.set_auto_page_break(auto=True, margin=20)

          # 1. Cover page
          self._render_cover_page(template)

          # 2. Placeholder page for TOC (will be page 2)
          self.pdf.add_page()
          toc_page = self.pdf.page_no()

          # 3. Render each section
          self.section_pages = []
          for section in template.sections:
              if section.id == "cover":
                  continue  # Already rendered
              section_data = content.get(section.content_key)
              if section_data is None and section.required:
                  section_data = f"[No data provided for {section.title}]"
              elif section_data is None:
                  continue  # Skip optional empty sections

              if section.page_break_before:
                  self.pdf.add_page()

              self.section_pages.append((section.title, self.pdf.page_no()))
              self._render_section(section, section_data)

              # Embed image if available for this section
              if section.id in images and os.path.isfile(images[section.id]):
                  self._embed_image(images[section.id])

          # 4. Render TOC on the reserved page 2
          self._render_toc(toc_page)

          # 5. Save
          Path(output_path).parent.mkdir(parents=True, exist_ok=True)
          self.pdf.output(output_path)
          return str(Path(output_path).resolve())

      def _render_cover_page(self, template: "BrandStrategyTemplate"):
          """Render branded cover page with brand name, subtitle, date, and color bar."""
          pdf = self.pdf
          pdf.add_page()

          primary_rgb = _hex_to_rgb(template.brand_colors[0])
          accent_rgb = _hex_to_rgb(template.brand_colors[2]) if len(template.brand_colors) > 2 else (180, 150, 60)
          bg_rgb = _hex_to_rgb(template.brand_colors[1]) if len(template.brand_colors) > 1 else (245, 240, 232)

          # Full-page background tint
          pdf.set_fill_color(*bg_rgb)
          pdf.rect(0, 0, 210, 297, "F")

          # Top accent bar
          pdf.set_fill_color(*primary_rgb)
          pdf.rect(0, 0, 210, 12, "F")

          # Brand name — large centered title
          pdf.ln(60)
          pdf.set_font("NotoSans", "B", 36)
          pdf.set_text_color(*primary_rgb)
          pdf.cell(0, 20, template.brand_name, align="C", new_x="LMARGIN", new_y="NEXT")

          # Subtitle
          pdf.ln(4)
          pdf.set_font("NotoSans", "", 18)
          pdf.set_text_color(80, 80, 80)
          first_section = template.sections[0] if template.sections else None
          subtitle = first_section.subtitle if first_section and first_section.subtitle else "Brand Strategy Document"
          pdf.cell(0, 12, subtitle, align="C", new_x="LMARGIN", new_y="NEXT")

          # Horizontal accent line
          pdf.ln(8)
          pdf.set_draw_color(*accent_rgb)
          pdf.set_line_width(0.8)
          pdf.line(60, pdf.get_y(), 150, pdf.get_y())
          pdf.ln(12)

          # Prepared by + date
          pdf.set_font("NotoSans", "", 12)
          pdf.set_text_color(100, 100, 100)
          pdf.cell(0, 8, f"Prepared by: {template.prepared_by}", align="C", new_x="LMARGIN", new_y="NEXT")
          pdf.cell(0, 8, doc_date, align="C", new_x="LMARGIN", new_y="NEXT")

          # Bottom accent bar
          pdf.set_fill_color(*accent_rgb)
          pdf.rect(0, 285, 210, 12, "F")

      def _render_toc(self, toc_page: int):
          """
          Render table of contents on the reserved TOC page.

          Args:
              toc_page: Page number reserved for TOC.
          """
          pdf = self.pdf
          pdf.page = toc_page
          primary_rgb = pdf.primary_rgb

          pdf.set_y(25)
          pdf.set_font("NotoSans", "B", 20)
          pdf.set_text_color(*primary_rgb)
          pdf.cell(0, 12, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
          pdf.ln(6)

          pdf.set_font("NotoSans", "", 12)
          for title, page_num in self.section_pages:
              pdf.set_text_color(40, 40, 40)
              # Section title on the left, page number right-aligned
              title_width = pdf.get_string_width(title)
              page_str = str(page_num)
              page_width = pdf.get_string_width(page_str)
              available = 190 - title_width - page_width
              dots = " . " * max(1, int(available / pdf.get_string_width(" . ")))
              pdf.cell(0, 8, f"{title}{dots}{page_str}", new_x="LMARGIN", new_y="NEXT")

      def _render_section(self, section: "DocumentSection", content):
          """
          Render a document section with appropriate formatting based on content type.

          Args:
              section: DocumentSection template definition.
              content: Section data — str, dict, list[str], or list[dict].
          """
          pdf = self.pdf
          primary_rgb = pdf.primary_rgb

          # Section heading
          pdf.set_font("NotoSans", "B", 18)
          pdf.set_text_color(*primary_rgb)
          pdf.cell(0, 12, section.title, new_x="LMARGIN", new_y="NEXT")

          if section.subtitle:
              pdf.set_font("NotoSans", "", 11)
              pdf.set_text_color(120, 120, 120)
              pdf.cell(0, 8, section.subtitle, new_x="LMARGIN", new_y="NEXT")

          # Accent underline
          pdf.set_draw_color(*pdf.accent_rgb)
          pdf.set_line_width(0.5)
          pdf.line(10, pdf.get_y() + 1, 80, pdf.get_y() + 1)
          pdf.ln(8)

          # Render content based on type
          pdf.set_text_color(30, 30, 30)
          pdf.set_font("NotoSans", "", 11)

          if isinstance(content, str):
              pdf.multi_cell(0, 6, content)
              pdf.ln(4)

          elif isinstance(content, dict):
              self._render_dict_content(content)

          elif isinstance(content, list):
              if content and isinstance(content[0], dict):
                  # list[dict] -> table
                  headers = list(content[0].keys())
                  rows = [[str(row.get(h, "")) for h in headers] for row in content]
                  self._render_table(headers, rows)
              elif content and isinstance(content[0], str):
                  # list[str] -> bullet list
                  for item in content:
                      pdf.cell(6, 6, chr(8226))  # bullet character
                      pdf.multi_cell(0, 6, f"  {item}")
                      pdf.ln(2)
              pdf.ln(4)

      def _render_dict_content(self, data: dict, depth: int = 0):
          """
          Recursively render dict content as labeled paragraphs.

          Args:
              data: Dict of key-value pairs.
              depth: Nesting depth for indentation.
          """
          pdf = self.pdf
          indent = depth * 8

          for key, value in data.items():
              label = key.replace("_", " ").title()

              if isinstance(value, str):
                  pdf.set_x(10 + indent)
                  pdf.set_font("NotoSans", "B", 11)
                  pdf.cell(pdf.get_string_width(label + ": ") + 2, 6, f"{label}: ")
                  pdf.set_font("NotoSans", "", 11)
                  pdf.multi_cell(0, 6, value)
                  pdf.ln(2)

              elif isinstance(value, list):
                  pdf.set_x(10 + indent)
                  pdf.set_font("NotoSans", "B", 11)
                  pdf.cell(0, 6, f"{label}:", new_x="LMARGIN", new_y="NEXT")
                  pdf.set_font("NotoSans", "", 11)

                  if value and isinstance(value[0], dict):
                      headers = list(value[0].keys())
                      rows = [[str(r.get(h, "")) for h in headers] for r in value]
                      self._render_table(headers, rows)
                  else:
                      for item in value:
                          pdf.set_x(14 + indent)
                          pdf.multi_cell(0, 6, f"{chr(8226)}  {item}")
                          pdf.ln(1)
                  pdf.ln(3)

              elif isinstance(value, dict):
                  pdf.set_x(10 + indent)
                  pdf.set_font("NotoSans", "B", 12)
                  pdf.cell(0, 7, label, new_x="LMARGIN", new_y="NEXT")
                  self._render_dict_content(value, depth=depth + 1)

      def _render_table(self, headers: list[str], rows: list[list[str]]):
          """
          Render a formatted table with header row highlighting.

          Args:
              headers: Column header labels.
              rows: List of row data (each row is a list of cell strings).
          """
          pdf = self.pdf
          primary_rgb = pdf.primary_rgb

          # Calculate column widths proportionally
          num_cols = len(headers)
          usable_width = 190  # A4 width minus margins
          col_width = usable_width / num_cols

          # Header row
          pdf.set_font("NotoSans", "B", 9)
          pdf.set_fill_color(*primary_rgb)
          pdf.set_text_color(255, 255, 255)
          for header in headers:
              pdf.cell(col_width, 7, header[:20], border=1, fill=True, align="C")
          pdf.ln()

          # Data rows
          pdf.set_font("NotoSans", "", 9)
          pdf.set_text_color(30, 30, 30)
          fill_toggle = False
          for row in rows:
              if fill_toggle:
                  pdf.set_fill_color(245, 245, 245)
              else:
                  pdf.set_fill_color(255, 255, 255)

              max_h = 7
              for cell_text in row:
                  # Estimate row height for wrapped text
                  lines_needed = max(1, len(cell_text) // 25 + 1)
                  max_h = max(max_h, lines_needed * 5)

              for cell_text in row:
                  pdf.cell(col_width, max_h, str(cell_text)[:40], border=1, fill=True)
              pdf.ln()
              fill_toggle = not fill_toggle

          pdf.ln(4)

      def _embed_image(self, image_path: str, caption: str = ""):
          """
          Embed an image centered on the page with optional caption.

          Args:
              image_path: Absolute path to the image file.
              caption: Optional caption text below the image.
          """
          pdf = self.pdf

          # Check remaining page space — add page if less than 80mm available
          if pdf.get_y() > 210:
              pdf.add_page()

          # Center the image, max width 160mm
          pdf.image(image_path, x=25, w=160)
          pdf.ln(3)

          if caption:
              pdf.set_font("NotoSans", "", 9)
              pdf.set_text_color(100, 100, 100)
              pdf.cell(0, 6, caption, align="C", new_x="LMARGIN", new_y="NEXT")
              pdf.ln(4)
  ```

#### Requirement 2 - DOCX Builder
- **Requirement**: Generate editable DOCX using python-docx
- **Implementation**:
  - `src/shared/src/shared/agent_tools/document/docx_builder.py`
  ```python
  import os
  from datetime import date
  from pathlib import Path

  from docx import Document
  from docx.enum.section import WD_ORIENT
  from docx.enum.table import WD_TABLE_ALIGNMENT
  from docx.enum.text import WD_ALIGN_PARAGRAPH
  from docx.oxml.ns import qn
  from docx.oxml import OxmlElement
  from docx.shared import Inches, Pt, RGBColor


  def _hex_to_rgb_color(hex_color: str) -> RGBColor:
      """Convert '#RRGGBB' to docx RGBColor."""
      h = hex_color.lstrip("#")
      return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


  class BrandStrategyDOCXBuilder:
      """
      Builds brand strategy DOCX documents using python-docx.

      Produces editable Word documents with professional styling.
      Users can further customize in Word or Google Docs.

      Features:
          - Custom styles for headings, body text, lists
          - Brand color application to headings and accents
          - Tables with merged cells and formatting
          - Image embedding
          - Auto-generated TOC field (updates on open in Word)
      """

      def __init__(self):
          self.doc: Document | None = None
          self.primary_color: RGBColor | None = None
          self.accent_color: RGBColor | None = None

      def build(
          self,
          content: dict,
          template: "BrandStrategyTemplate",
          output_path: str,
          images: dict[str, str] | None = None,
      ) -> str:
          """
          Build DOCX document from structured phase outputs.

          Args:
              content: Dict with phase outputs keyed by content_key.
              template: Document template defining sections and branding.
              output_path: Output file path.
              images: Dict of section_id -> file_path for embedding.

          Returns:
              Absolute path to generated DOCX.
          """
          images = images or {}
          doc_date = template.date or date.today().strftime("%Y-%m-%d")

          self.doc = Document()
          self.primary_color = _hex_to_rgb_color(template.brand_colors[0])
          self.accent_color = (
              _hex_to_rgb_color(template.brand_colors[2])
              if len(template.brand_colors) > 2
              else RGBColor(180, 150, 60)
          )
          self._apply_base_styles()

          # Cover page
          self._render_cover(template)
          self.doc.add_page_break()

          # TOC field — Word updates it on open
          self._insert_toc_field()
          self.doc.add_page_break()

          # Sections
          for section in template.sections:
              if section.id == "cover":
                  continue
              section_data = content.get(section.content_key)
              if section_data is None and section.required:
                  section_data = f"[No data provided for {section.title}]"
              elif section_data is None:
                  continue

              if section.page_break_before:
                  self.doc.add_page_break()

              self._render_heading(section.title, level=1)
              if section.subtitle:
                  sub_para = self.doc.add_paragraph(section.subtitle)
                  sub_para.runs[0].font.color.rgb = RGBColor(120, 120, 120)
                  sub_para.runs[0].font.size = Pt(11)

              self._render_content(section_data)

              if section.id in images and os.path.isfile(images[section.id]):
                  self._embed_image(images[section.id])

          # Save
          Path(output_path).parent.mkdir(parents=True, exist_ok=True)
          self.doc.save(output_path)
          return str(Path(output_path).resolve())

      def _apply_base_styles(self):
          """Apply brand font and color defaults to built-in styles."""
          style = self.doc.styles["Normal"]
          style.font.name = "Calibri"
          style.font.size = Pt(11)

          for level in range(1, 4):
              heading_style = self.doc.styles[f"Heading {level}"]
              heading_style.font.color.rgb = self.primary_color
              heading_style.font.name = "Calibri"

      def _render_cover(self, template: "BrandStrategyTemplate"):
          """Render a cover page with brand name, subtitle, and date."""
          # Spacer
          for _ in range(6):
              self.doc.add_paragraph("")

          # Brand name
          title_para = self.doc.add_paragraph()
          title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
          run = title_para.add_run(template.brand_name)
          run.font.size = Pt(36)
          run.font.bold = True
          run.font.color.rgb = self.primary_color

          # Subtitle
          subtitle = template.sections[0].subtitle if template.sections else "Brand Strategy Document"
          sub_para = self.doc.add_paragraph()
          sub_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
          run = sub_para.add_run(subtitle or "Brand Strategy Document")
          run.font.size = Pt(18)
          run.font.color.rgb = RGBColor(80, 80, 80)

          # Date and author
          self.doc.add_paragraph("")
          meta_para = self.doc.add_paragraph()
          meta_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
          run = meta_para.add_run(f"Prepared by: {template.prepared_by}  |  {doc_date}")
          run.font.size = Pt(12)
          run.font.color.rgb = RGBColor(100, 100, 100)

      def _insert_toc_field(self):
          """Insert a Word TOC field that auto-updates when document is opened."""
          heading = self.doc.add_heading("Table of Contents", level=1)
          paragraph = self.doc.add_paragraph()
          run = paragraph.add_run()
          fld_char_begin = OxmlElement("w:fldChar")
          fld_char_begin.set(qn("w:fldCharType"), "begin")
          run._r.append(fld_char_begin)

          instr_text = OxmlElement("w:instrText")
          instr_text.set(qn("xml:space"), "preserve")
          instr_text.text = ' TOC \\o "1-3" \\h \\z \\u '
          run._r.append(instr_text)

          fld_char_end = OxmlElement("w:fldChar")
          fld_char_end.set(qn("w:fldCharType"), "end")
          run._r.append(fld_char_end)

      def _render_heading(self, text: str, level: int = 1):
          """
          Add a heading with brand color.

          Args:
              text: Heading text.
              level: Heading level (1-3).
          """
          heading = self.doc.add_heading(text, level=level)
          for run in heading.runs:
              run.font.color.rgb = self.primary_color

      def _render_content(self, content):
          """
          Render content based on its type (str, dict, list).

          Args:
              content: Section data in any supported format.
          """
          if isinstance(content, str):
              self._render_paragraph(content)

          elif isinstance(content, dict):
              for key, value in content.items():
                  label = key.replace("_", " ").title()
                  if isinstance(value, str):
                      para = self.doc.add_paragraph()
                      run_label = para.add_run(f"{label}: ")
                      run_label.bold = True
                      para.add_run(value)
                  elif isinstance(value, list) and value and isinstance(value[0], dict):
                      self._render_heading(label, level=2)
                      headers = list(value[0].keys())
                      rows = [[str(r.get(h, "")) for h in headers] for r in value]
                      self._render_table(headers, rows)
                  elif isinstance(value, list):
                      self._render_heading(label, level=2)
                      for item in value:
                          self.doc.add_paragraph(str(item), style="List Bullet")
                  elif isinstance(value, dict):
                      self._render_heading(label, level=2)
                      self._render_content(value)

          elif isinstance(content, list):
              if content and isinstance(content[0], dict):
                  headers = list(content[0].keys())
                  rows = [[str(r.get(h, "")) for h in headers] for r in content]
                  self._render_table(headers, rows)
              else:
                  for item in content:
                      self.doc.add_paragraph(str(item), style="List Bullet")

      def _render_paragraph(self, text: str):
          """
          Add a body paragraph.

          Args:
              text: Paragraph text content.
          """
          self.doc.add_paragraph(text)

      def _render_table(self, headers: list[str], rows: list[list[str]]):
          """
          Render a formatted table with branded header row.

          Args:
              headers: Column header labels.
              rows: List of row data (list of cell strings each).
          """
          table = self.doc.add_table(rows=1 + len(rows), cols=len(headers))
          table.style = "Light Grid Accent 1"
          table.alignment = WD_TABLE_ALIGNMENT.CENTER

          # Header row
          for col_idx, header_text in enumerate(headers):
              cell = table.rows[0].cells[col_idx]
              cell.text = header_text
              for para in cell.paragraphs:
                  for run in para.runs:
                      run.font.bold = True
                      run.font.size = Pt(10)

          # Data rows
          for row_idx, row_data in enumerate(rows):
              for col_idx, cell_text in enumerate(row_data):
                  table.rows[row_idx + 1].cells[col_idx].text = cell_text

          self.doc.add_paragraph("")  # Spacer after table

      def _embed_image(self, image_path: str, caption: str = ""):
          """
          Embed an image centered with optional caption.

          Args:
              image_path: Path to image file.
              caption: Optional caption text.
          """
          para = self.doc.add_paragraph()
          para.alignment = WD_ALIGN_PARAGRAPH.CENTER
          run = para.add_run()
          run.add_picture(image_path, width=Inches(5.5))

          if caption:
              cap_para = self.doc.add_paragraph()
              cap_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
              run = cap_para.add_run(caption)
              run.font.size = Pt(9)
              run.font.color.rgb = RGBColor(100, 100, 100)
  ```

#### Requirement 3 - Tool Function
- **Requirement**: generate_document plain function that routes to PDF or DOCX builder. Follows codebase convention (`search_web`, `scrape_web_content`).
- **Implementation**:
  - `src/shared/src/shared/agent_tools/document/generate_document.py`
  ```python
  import json
  import os

  from loguru import logger

  from shared.agent_tools.document.templates.brand_strategy import (
      BrandStrategyTemplate,
  )


  def generate_document(
      content: str,
      doc_format: str = "pdf",
      brand_name: str = "Brand",
      brand_colors: list[str] | None = None,
      images: str | None = None,
      output_path: str | None = None,
  ) -> str:
      """
      Generate a professional brand strategy document.

      Compiles all phase outputs into a complete strategy document.
      Use this tool at the end of Phase 5 to produce the final
      deliverable.

      Args:
          content: JSON string of structured content with phase outputs.
              Must include keys: phase_0_output through phase_5_output,
              executive_summary, implementation_roadmap, kpis
          doc_format: Output format — "pdf" (default) or "docx"
          brand_name: Brand name for cover page and headers
          brand_colors: List of hex color codes [primary, secondary, accent]
          images: Optional JSON string mapping section IDs to image file paths
              (e.g., '{"brand_key": "/path/to/brand_key.png"}')
          output_path: Custom output path. Default: resolved from
              BRANDMIND_OUTPUT_DIR env var → ./brandmind-output/documents/

      Returns:
          Path to generated document file + summary of contents
      """

      # ── Parse content ───────────────────────────────────────────
      try:
          data = json.loads(content)
      except json.JSONDecodeError as e:
          return f"Invalid content JSON: {e}"

      # ── Resolve output path ─────────────────────────────────────
      if not output_path:
          base = os.environ.get(
              "BRANDMIND_OUTPUT_DIR",
              os.path.join(os.getcwd(), "brandmind-output"),
          )
          output_dir = os.path.join(base, "documents")
          os.makedirs(output_dir, exist_ok=True)
          safe_name = brand_name.lower().replace(" ", "_")
          ext = "pdf" if doc_format == "pdf" else "docx"
          output_path = os.path.join(
              output_dir, f"{safe_name}_brand_strategy.{ext}"
          )

      # ── Build document ──────────────────────────────────────────
      template = BrandStrategyTemplate(
          brand_name=brand_name,
          brand_colors=brand_colors or ["#1B365D", "#F5F0E8", "#D4A84B"],
      )

      # Parse images if provided
      images_dict: dict[str, str] = {}
      if images:
          try:
              images_dict = json.loads(images)
          except json.JSONDecodeError:
              logger.warning("Invalid images JSON, ignoring")

      try:
          if doc_format == "pdf":
              from shared.agent_tools.document.pdf_builder import (
                  BrandStrategyPDFBuilder,
              )
              builder = BrandStrategyPDFBuilder()
          elif doc_format == "docx":
              from shared.agent_tools.document.docx_builder import (
                  BrandStrategyDOCXBuilder,
              )
              builder = BrandStrategyDOCXBuilder()
          else:
              return f"Unsupported format '{doc_format}'. Use 'pdf' or 'docx'."

          result_path = builder.build(
              content=data,
              template=template,
              output_path=output_path,
              images=images_dict,
          )

          section_count = len(template.sections)
          logger.info(
              f"Document generated: {result_path} "
              f"({section_count} sections)"
          )
          return (
              f"Document saved to: {result_path}\n"
              f"Format: {format.upper()}\n"
              f"Sections: {section_count}\n"
              f"Brand: {brand_name}"
          )

      except Exception as e:
          logger.error(f"Document generation failed: {e}")
          return f"Document generation failed: {e}"
  ```
- **Acceptance Criteria**:
  - [ ] PDF output is professionally formatted with branded elements
  - [ ] DOCX output is editable in Word/Google Docs
  - [ ] Tables render correctly for competitor analysis, KPIs
  - [ ] Images embed properly (mood boards, Brand Key)
  - [ ] Vietnamese text renders correctly (Unicode)
  - [ ] TOC auto-generated

### Component 3: generate_presentation Tool

#### Requirement 1 - PPTX Builder
- **Requirement**: Build brand strategy pitch deck
- **Implementation**:
  - `src/shared/src/shared/agent_tools/document/pptx_builder.py`
  ```python
  import os
  from pathlib import Path

  from pptx import Presentation
  from pptx.dml.color import RGBColor
  from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
  from pptx.util import Inches, Pt, Emu


  def _hex_to_pptx_rgb(hex_color: str) -> RGBColor:
      """Convert '#RRGGBB' to pptx RGBColor."""
      h = hex_color.lstrip("#")
      return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


  class BrandStrategyPPTXBuilder:
      """
      Builds brand strategy PPTX pitch decks using python-pptx.

      Creates a 10-15 slide deck summarizing the brand strategy
      for stakeholder presentation.

      Slide layouts:
          - title: Full-width title slide with brand colors
          - content: Title + bullet point content
          - two_column: Side-by-side comparison
          - image: Title + large image (mood board, Brand Key)
          - table: Title + data table (competitors, KPIs)
      """

      # Standard layout indices in the default pptx template
      LAYOUT_TITLE = 0        # Title Slide
      LAYOUT_CONTENT = 1      # Title and Content
      LAYOUT_TWO_CONTENT = 3  # Two Content
      LAYOUT_BLANK = 6        # Blank

      def __init__(self):
          self.prs = Presentation()
          # Set widescreen 16:9 aspect ratio
          self.prs.slide_width = Inches(13.333)
          self.prs.slide_height = Inches(7.5)
          self.primary_color = _hex_to_pptx_rgb("#1B365D")
          self.secondary_color = _hex_to_pptx_rgb("#F5F0E8")
          self.accent_color = _hex_to_pptx_rgb("#D4A84B")

      def build(
          self,
          content: dict,
          template: "BrandStrategyDeckTemplate",
          output_path: str,
          images: dict[str, str] | None = None,
      ) -> str:
          """
          Build PPTX presentation from structured content.

          Args:
              content: Dict with phase outputs keyed by content_key.
              template: Deck template defining slide sequence.
              output_path: Output file path.
              images: Dict of slide_id -> image file path.

          Returns:
              Absolute path to generated PPTX.
          """
          images = images or {}

          if template.brand_colors:
              self._apply_brand_theme(template.brand_colors)

          for slide_def in template.slides:
              # Resolve nested content keys like "phase_1_output.market_overview"
              slide_content = self._resolve_content_key(
                  content, slide_def.content_key
              )
              if slide_content is None:
                  slide_content = f"[Data pending: {slide_def.title}]"

              layout = slide_def.layout
              if layout == "title":
                  self._create_title_slide(slide_def, slide_content)
              elif layout == "content":
                  self._create_content_slide(slide_def, slide_content)
              elif layout == "two_column":
                  self._create_two_column_slide(slide_def, slide_content)
              elif layout == "image":
                  self._create_image_slide(
                      slide_def, slide_content, images
                  )
              elif layout == "table":
                  self._create_table_slide(slide_def, slide_content)
              else:
                  self._create_content_slide(slide_def, slide_content)

          Path(output_path).parent.mkdir(parents=True, exist_ok=True)
          self.prs.save(output_path)
          return str(Path(output_path).resolve())

      def _resolve_content_key(self, content: dict, key: str):
          """
          Resolve dotted content key like 'phase_1_output.market_overview'.

          Args:
              content: Root content dict.
              key: Dotted key path.

          Returns:
              Resolved value or None.
          """
          parts = key.split(".")
          current = content
          for part in parts:
              if isinstance(current, dict) and part in current:
                  current = current[part]
              else:
                  return None
          return current

      def _extract_bullets(self, content) -> list[str]:
          """
          Extract bullet-point strings from various content types.

          Args:
              content: str, list, or dict content.

          Returns:
              List of bullet-point strings.
          """
          if isinstance(content, str):
              return [line.strip() for line in content.split("\n") if line.strip()]
          elif isinstance(content, list):
              return [str(item) if not isinstance(item, dict) else str(item) for item in content]
          elif isinstance(content, dict):
              bullets = []
              for key, val in content.items():
                  label = key.replace("_", " ").title()
                  if isinstance(val, str):
                      bullets.append(f"{label}: {val}")
                  elif isinstance(val, list):
                      bullets.append(f"{label}: {', '.join(str(v) for v in val[:3])}")
                  else:
                      bullets.append(f"{label}: {str(val)[:80]}")
              return bullets
          return [str(content)]

      def _create_title_slide(self, slide_def, content):
          """
          Create title/cover slide with brand name and subtitle.

          Args:
              slide_def: PresentationSlideTemplate definition.
              content: Cover content (str or dict with 'brand_name', 'subtitle').
          """
          layout = self.prs.slide_layouts[self.LAYOUT_TITLE]
          slide = self.prs.slides.add_slide(layout)

          # Title
          title = slide.shapes.title
          title.text = slide_def.title
          for para in title.text_frame.paragraphs:
              for run in para.runs:
                  run.font.color.rgb = self.primary_color
                  run.font.size = Pt(44)
                  run.font.bold = True

          # Subtitle placeholder
          if len(slide.placeholders) > 1:
              subtitle_ph = slide.placeholders[1]
              if isinstance(content, dict):
                  subtitle_ph.text = content.get("subtitle", "Brand Strategy Presentation")
              elif isinstance(content, str):
                  subtitle_ph.text = content[:200]
              else:
                  subtitle_ph.text = "Brand Strategy Presentation"
              for para in subtitle_ph.text_frame.paragraphs:
                  for run in para.runs:
                      run.font.size = Pt(20)
                      run.font.color.rgb = _hex_to_pptx_rgb("#666666")

          # Speaker notes
          if slide_def.notes:
              slide.notes_slide.notes_text_frame.text = slide_def.notes

      def _create_content_slide(self, slide_def, content):
          """
          Create content slide with title and bullet points.

          Args:
              slide_def: PresentationSlideTemplate definition.
              content: Content to render as bullets.
          """
          layout = self.prs.slide_layouts[self.LAYOUT_CONTENT]
          slide = self.prs.slides.add_slide(layout)

          # Title
          slide.shapes.title.text = slide_def.title
          for run in slide.shapes.title.text_frame.paragraphs[0].runs:
              run.font.color.rgb = self.primary_color
              run.font.size = Pt(28)
              run.font.bold = True

          # Content body
          body = slide.placeholders[1]
          tf = body.text_frame
          tf.clear()

          bullets = self._extract_bullets(content)
          for i, bullet in enumerate(bullets[:10]):  # Max 10 bullets per slide
              if i == 0:
                  tf.paragraphs[0].text = bullet
                  tf.paragraphs[0].font.size = Pt(16)
              else:
                  para = tf.add_paragraph()
                  para.text = bullet
                  para.font.size = Pt(16)
                  para.space_before = Pt(6)

          if slide_def.notes:
              slide.notes_slide.notes_text_frame.text = slide_def.notes

      def _create_two_column_slide(self, slide_def, content):
          """
          Create two-column comparison slide.

          Splits content dict into left/right halves, or renders
          first-half/second-half of a list.

          Args:
              slide_def: PresentationSlideTemplate definition.
              content: Dict or list to split into two columns.
          """
          layout = self.prs.slide_layouts[self.LAYOUT_BLANK]
          slide = self.prs.slides.add_slide(layout)

          # Title text box
          txBox = slide.shapes.add_textbox(
              Inches(0.5), Inches(0.3), Inches(12), Inches(1)
          )
          tf = txBox.text_frame
          tf.text = slide_def.title
          tf.paragraphs[0].font.size = Pt(28)
          tf.paragraphs[0].font.bold = True
          tf.paragraphs[0].font.color.rgb = self.primary_color

          bullets = self._extract_bullets(content)
          mid = len(bullets) // 2

          # Left column
          left_box = slide.shapes.add_textbox(
              Inches(0.5), Inches(1.6), Inches(5.8), Inches(5.2)
          )
          left_tf = left_box.text_frame
          left_tf.word_wrap = True
          for i, bullet in enumerate(bullets[:mid] or bullets[:5]):
              if i == 0:
                  left_tf.paragraphs[0].text = bullet
                  left_tf.paragraphs[0].font.size = Pt(14)
              else:
                  para = left_tf.add_paragraph()
                  para.text = bullet
                  para.font.size = Pt(14)
                  para.space_before = Pt(4)

          # Right column
          right_box = slide.shapes.add_textbox(
              Inches(6.8), Inches(1.6), Inches(5.8), Inches(5.2)
          )
          right_tf = right_box.text_frame
          right_tf.word_wrap = True
          for i, bullet in enumerate(bullets[mid:mid + 5] or bullets[5:10]):
              if i == 0:
                  right_tf.paragraphs[0].text = bullet
                  right_tf.paragraphs[0].font.size = Pt(14)
              else:
                  para = right_tf.add_paragraph()
                  para.text = bullet
                  para.font.size = Pt(14)
                  para.space_before = Pt(4)

          if slide_def.notes:
              slide.notes_slide.notes_text_frame.text = slide_def.notes

      def _create_image_slide(self, slide_def, content, images: dict):
          """
          Create slide with a large image and optional caption text.

          Args:
              slide_def: PresentationSlideTemplate definition.
              content: Caption or descriptive content.
              images: Dict of slide_id -> image file path.
          """
          layout = self.prs.slide_layouts[self.LAYOUT_BLANK]
          slide = self.prs.slides.add_slide(layout)

          # Title
          txBox = slide.shapes.add_textbox(
              Inches(0.5), Inches(0.3), Inches(12), Inches(1)
          )
          tf = txBox.text_frame
          tf.text = slide_def.title
          tf.paragraphs[0].font.size = Pt(28)
          tf.paragraphs[0].font.bold = True
          tf.paragraphs[0].font.color.rgb = self.primary_color

          # Image
          image_path = images.get(slide_def.id)
          if image_path and os.path.isfile(image_path):
              slide.shapes.add_picture(
                  image_path,
                  Inches(1.5), Inches(1.6),
                  width=Inches(10), height=Inches(5.2),
              )
          else:
              # Placeholder text when image is missing
              placeholder_box = slide.shapes.add_textbox(
                  Inches(2), Inches(2.5), Inches(9), Inches(3)
              )
              ptf = placeholder_box.text_frame
              ptf.word_wrap = True
              bullets = self._extract_bullets(content)
              for i, bullet in enumerate(bullets[:6]):
                  if i == 0:
                      ptf.paragraphs[0].text = bullet
                      ptf.paragraphs[0].font.size = Pt(16)
                  else:
                      para = ptf.add_paragraph()
                      para.text = bullet
                      para.font.size = Pt(16)

          if slide_def.notes:
              slide.notes_slide.notes_text_frame.text = slide_def.notes

      def _create_table_slide(self, slide_def, content):
          """
          Create slide with a data table.

          Args:
              slide_def: PresentationSlideTemplate definition.
              content: list[dict] for table rows, or dict/str for fallback.
          """
          layout = self.prs.slide_layouts[self.LAYOUT_BLANK]
          slide = self.prs.slides.add_slide(layout)

          # Title
          txBox = slide.shapes.add_textbox(
              Inches(0.5), Inches(0.3), Inches(12), Inches(0.8)
          )
          tf = txBox.text_frame
          tf.text = slide_def.title
          tf.paragraphs[0].font.size = Pt(28)
          tf.paragraphs[0].font.bold = True
          tf.paragraphs[0].font.color.rgb = self.primary_color

          # Build table from list[dict]
          if isinstance(content, list) and content and isinstance(content[0], dict):
              headers = list(content[0].keys())
              num_rows = min(len(content), 8)  # Max 8 data rows on one slide
              num_cols = min(len(headers), 6)   # Max 6 columns

              table_shape = slide.shapes.add_table(
                  num_rows + 1, num_cols,
                  Inches(0.5), Inches(1.4),
                  Inches(12), Inches(5.5),
              )
              table = table_shape.table

              # Header row
              for col_idx in range(num_cols):
                  cell = table.cell(0, col_idx)
                  cell.text = headers[col_idx]
                  for para in cell.text_frame.paragraphs:
                      para.font.size = Pt(11)
                      para.font.bold = True
                      para.font.color.rgb = RGBColor(255, 255, 255)
                  cell.fill.solid()
                  cell.fill.fore_color.rgb = self.primary_color

              # Data rows
              for row_idx, row_data in enumerate(content[:num_rows]):
                  for col_idx in range(num_cols):
                      cell = table.cell(row_idx + 1, col_idx)
                      cell.text = str(row_data.get(headers[col_idx], ""))
                      for para in cell.text_frame.paragraphs:
                          para.font.size = Pt(10)
          else:
              # Fallback: render as bullet content
              bullets = self._extract_bullets(content)
              content_box = slide.shapes.add_textbox(
                  Inches(0.5), Inches(1.4), Inches(12), Inches(5.5)
              )
              ctf = content_box.text_frame
              ctf.word_wrap = True
              for i, bullet in enumerate(bullets[:10]):
                  if i == 0:
                      ctf.paragraphs[0].text = bullet
                      ctf.paragraphs[0].font.size = Pt(14)
                  else:
                      para = ctf.add_paragraph()
                      para.text = bullet
                      para.font.size = Pt(14)

          if slide_def.notes:
              slide.notes_slide.notes_text_frame.text = slide_def.notes

      def _apply_brand_theme(self, brand_colors: list[str]):
          """
          Apply brand colors to the builder's color palette.

          Args:
              brand_colors: [primary_hex, secondary_hex, accent_hex].
          """
          if len(brand_colors) >= 1:
              self.primary_color = _hex_to_pptx_rgb(brand_colors[0])
          if len(brand_colors) >= 2:
              self.secondary_color = _hex_to_pptx_rgb(brand_colors[1])
          if len(brand_colors) >= 3:
              self.accent_color = _hex_to_pptx_rgb(brand_colors[2])
  ```

#### Requirement 2 - Tool Function
- **Implementation**:
  - `src/shared/src/shared/agent_tools/document/generate_presentation.py`
  ```python
  import json
  import os

  from loguru import logger

  from shared.agent_tools.document.pptx_builder import (
      BrandStrategyPPTXBuilder,
  )
  from shared.agent_tools.document.templates.brand_strategy import (
      BrandStrategyDeckTemplate,
  )


  def generate_presentation(
      content: str,
      brand_name: str = "Brand",
      brand_colors: list[str] | None = None,
      images: dict[str, str] | None = None,
      output_path: str | None = None,
  ) -> str:
      """
      Generate a brand strategy pitch deck (PPTX).

      Creates a 10-15 slide summary presentation suitable for
      stakeholder meetings, investor pitches, or team alignment.

      Args:
          content: JSON string of structured content with phase outputs
          brand_name: Brand name for title slide
          brand_colors: [primary_hex, secondary_hex, accent_hex]
          images: Optional dict of image paths keyed by slide ID
              (e.g., {"identity": "/path/to/mood_board.png"}).
              Used by BrandStrategyPPTXBuilder for image slides.
          output_path: Custom output path. Default: resolved from
              BRANDMIND_OUTPUT_DIR env var → ./brandmind-output/presentations/

      Returns:
          Path to generated .pptx file + slide count summary
      """

      # ── Parse content ───────────────────────────────────────────
      try:
          data = json.loads(content)
      except json.JSONDecodeError as e:
          return f"Invalid content JSON: {e}"

      # ── Resolve output path ─────────────────────────────────────
      if not output_path:
          base = os.environ.get(
              "BRANDMIND_OUTPUT_DIR",
              os.path.join(os.getcwd(), "brandmind-output"),
          )
          output_dir = os.path.join(base, "presentations")
          os.makedirs(output_dir, exist_ok=True)
          safe_name = brand_name.lower().replace(" ", "_")
          output_path = os.path.join(
              output_dir, f"{safe_name}_strategy_deck.pptx"
          )

      # ── Build presentation ──────────────────────────────────────
      deck_template = BrandStrategyDeckTemplate(
          brand_name=brand_name,
          brand_colors=brand_colors or ["#1B365D", "#F5F0E8", "#D4A84B"],
      )

      try:
          builder = BrandStrategyPPTXBuilder()
          result_path = builder.build(
              content=data,
              template=deck_template,
              output_path=output_path,
              images=images,  # Pass images for image-type slides
          )

          slide_count = len(deck_template.slides)
          logger.info(
              f"Presentation generated: {result_path} "
              f"({slide_count} slides)"
          )
          return (
              f"Presentation saved to: {result_path}\n"
              f"Slides: {slide_count}\n"
              f"Brand: {brand_name}"
          )

      except Exception as e:
          logger.error(f"Presentation generation failed: {e}")
          return f"Presentation generation failed: {e}"
  ```
- **Acceptance Criteria**:
  - [ ] 10-15 slide deck generated
  - [ ] Brand colors applied to slide theme
  - [ ] Tables render for competitor analysis, KPIs
  - [ ] Speaker notes included
  - [ ] Editable in PowerPoint/Google Slides

### Component 4: export_to_markdown Tool

#### Requirement 1 - Markdown Export
- **Requirement**: Export structured phase outputs to well-formatted Markdown
- **Implementation**:
  - `src/shared/src/shared/agent_tools/document/export_to_markdown.py`
  ```python
  import json
  import os
  from pathlib import Path

  from loguru import logger


  def export_to_markdown(
      content: str,
      sections: list[str] | None = None,
      output_path: str | None = None,
  ) -> str:
      """
      Export brand strategy data to well-formatted Markdown.

      Creates a clean Markdown document suitable for sharing via
      Notion, GitHub, or any Markdown-compatible platform.

      Args:
          content: JSON string of structured content with phase outputs
          sections: Specific sections to export (None = all)
          output_path: Output file path. Default: resolved from
              BRANDMIND_OUTPUT_DIR env var → ./brandmind-output/documents/

      Returns:
          Path to generated .md file OR the markdown content if short
      """

      # ── Parse content ───────────────────────────────────────────
      try:
          data = json.loads(content)
      except json.JSONDecodeError as e:
          return f"Invalid content JSON: {e}"

      # ── Build markdown ──────────────────────────────────────────
      formatter = MarkdownFormatter()

      if sections:
          # Export selected sections only
          md_parts = []
          for section_key in sections:
              if section_key in data:
                  md_parts.append(
                      formatter.format_phase_output(section_key, data[section_key])
                  )
          markdown_text = "\n\n---\n\n".join(md_parts)
      else:
          markdown_text = formatter.format_full_document(data)

      # ── Short content → return directly ─────────────────────────
      if len(markdown_text) < 2000 and not output_path:
          return markdown_text

      # ── Write to file ───────────────────────────────────────────
      if not output_path:
          base = os.environ.get(
              "BRANDMIND_OUTPUT_DIR",
              os.path.join(os.getcwd(), "brandmind-output"),
          )
          output_dir = os.path.join(base, "documents")
          os.makedirs(output_dir, exist_ok=True)
          safe_name = data.get("brand_name", "brand").lower().replace(" ", "_")
          output_path = os.path.join(
              output_dir, f"{safe_name}_brand_strategy_export.md"
          )

      path = Path(output_path)
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(markdown_text, encoding="utf-8")

      logger.info(f"Markdown exported: {output_path}")
      return (
          f"Markdown exported to: {output_path}\n"
          f"Length: {len(markdown_text)} characters"
      )


  # Phase key display name mapping
  _PHASE_TITLES = {
      "cover": "Cover",
      "executive_summary": "Executive Summary",
      "phase_0_output": "Business Context & Problem Statement",
      "phase_0_5_output": "Brand Equity Audit",
      "phase_1_output": "Market Intelligence",
      "phase_2_output": "Brand Strategy Core",
      "phase_3_output": "Brand Identity & Expression",
      "phase_4_output": "Communication Framework",
      "implementation_roadmap": "Implementation Roadmap",
      "kpis": "KPI & Measurement Plan",
      "appendices": "Appendices",
      "next_steps": "Next Steps",
  }


  class MarkdownFormatter:
      """
      Formats structured brand strategy data into clean Markdown.

      Handles:
          - Nested dict -> headers + content
          - Lists -> bullet points
          - Tables -> Markdown tables
          - Images -> inline references
      """

      def format_phase_output(
          self, phase_key: str, data
      ) -> str:
          """
          Format a single phase output as a Markdown section.

          Args:
              phase_key: Key name (e.g. 'phase_1_output').
              data: Phase data — str, dict, or list.

          Returns:
              Formatted Markdown string for this section.
          """
          title = _PHASE_TITLES.get(
              phase_key, phase_key.replace("_", " ").title()
          )
          lines = [f"## {title}", ""]
          self._render_value(lines, data, depth=3)
          return "\n".join(lines)

      def _render_value(
          self, lines: list[str], value, depth: int = 3
      ):
          """
          Recursively render a value into Markdown lines.

          Args:
              lines: Accumulator list of Markdown lines.
              value: Data to render (str, dict, list).
              depth: Current heading depth (3 = ###).
          """
          if isinstance(value, str):
              lines.append(value)
              lines.append("")

          elif isinstance(value, dict):
              for key, val in value.items():
                  label = key.replace("_", " ").title()
                  if isinstance(val, str):
                      lines.append(f"**{label}**: {val}")
                      lines.append("")
                  elif isinstance(val, list) and val and isinstance(val[0], dict):
                      heading_prefix = "#" * min(depth, 6)
                      lines.append(f"{heading_prefix} {label}")
                      lines.append("")
                      headers = list(val[0].keys())
                      rows = [
                          [str(r.get(h, "")) for h in headers]
                          for r in val
                      ]
                      lines.append(self.format_table(headers, rows))
                      lines.append("")
                  elif isinstance(val, list):
                      heading_prefix = "#" * min(depth, 6)
                      lines.append(f"{heading_prefix} {label}")
                      lines.append("")
                      for item in val:
                          lines.append(f"- {item}")
                      lines.append("")
                  elif isinstance(val, dict):
                      heading_prefix = "#" * min(depth, 6)
                      lines.append(f"{heading_prefix} {label}")
                      lines.append("")
                      self._render_value(lines, val, depth=depth + 1)

          elif isinstance(value, list):
              if value and isinstance(value[0], dict):
                  headers = list(value[0].keys())
                  rows = [
                      [str(r.get(h, "")) for h in headers]
                      for r in value
                  ]
                  lines.append(self.format_table(headers, rows))
                  lines.append("")
              else:
                  for item in value:
                      lines.append(f"- {item}")
                  lines.append("")

      def format_table(
          self, headers: list[str], rows: list[list[str]]
      ) -> str:
          """
          Format data as a Markdown table.

          Args:
              headers: Column header labels.
              rows: List of row data (list of cell strings).

          Returns:
              Markdown table string with header, separator, and data rows.
          """
          # Calculate column widths for alignment
          col_widths = [len(h) for h in headers]
          for row in rows:
              for i, cell in enumerate(row):
                  if i < len(col_widths):
                      col_widths[i] = max(col_widths[i], len(cell))

          # Header row
          header_line = "| " + " | ".join(
              h.ljust(col_widths[i]) for i, h in enumerate(headers)
          ) + " |"

          # Separator row
          sep_line = "| " + " | ".join(
              "-" * col_widths[i] for i in range(len(headers))
          ) + " |"

          # Data rows
          data_lines = []
          for row in rows:
              padded = []
              for i in range(len(headers)):
                  cell = row[i] if i < len(row) else ""
                  padded.append(cell.ljust(col_widths[i]))
              data_lines.append("| " + " | ".join(padded) + " |")

          return "\n".join([header_line, sep_line] + data_lines)

      def format_full_document(self, all_phases: dict) -> str:
          """
          Format all phase outputs into a complete Markdown document.

          Args:
              all_phases: Dict of all phase outputs keyed by content_key.

          Returns:
              Complete Markdown document string with title, TOC, and sections.
          """
          brand_name = all_phases.get("brand_name", "Brand")
          parts = [
              f"# {brand_name} — Brand Strategy Document",
              "",
              f"*Generated by BrandMind AI*",
              "",
              "---",
              "",
              "## Table of Contents",
              "",
          ]

          # Build TOC from known phase order
          section_order = [
              "executive_summary", "phase_0_output", "phase_0_5_output",
              "phase_1_output", "phase_2_output", "phase_3_output",
              "phase_4_output", "implementation_roadmap", "kpis",
              "appendices",
          ]
          toc_idx = 1
          for key in section_order:
              if key in all_phases:
                  title = _PHASE_TITLES.get(
                      key, key.replace("_", " ").title()
                  )
                  anchor = title.lower().replace(" ", "-").replace("&", "")
                  parts.append(f"{toc_idx}. [{title}](#{anchor})")
                  toc_idx += 1

          parts.extend(["", "---", ""])

          # Render each section
          for key in section_order:
              if key in all_phases:
                  parts.append(self.format_phase_output(key, all_phases[key]))
                  parts.append("---")
                  parts.append("")

          # Include any extra keys not in the standard order
          rendered = set(section_order) | {"brand_name", "cover", "agenda"}
          for key, value in all_phases.items():
              if key not in rendered:
                  parts.append(self.format_phase_output(key, value))
                  parts.append("---")
                  parts.append("")

          return "\n".join(parts)
  ```
- **Acceptance Criteria**:
  - [ ] Clean, readable Markdown output
  - [ ] Tables formatted correctly
  - [ ] Exports all or selected sections
  - [ ] Compatible with Notion/GitHub rendering

### Component 5: generate_spreadsheet Tool (XLSX)

> Status: ⏳ Pending

#### Requirement 1 — Spreadsheet Templates Definition
- **Requirement**: Define reusable spreadsheet templates for common brand strategy deliverables. Each template specifies sheets, column structure, and formula patterns.

- **Implementation**:
  - `src/shared/src/shared/agent_tools/document/spreadsheet_templates.py`
  ```python
  """
  Spreadsheet template definitions for brand strategy deliverables.

  Each template defines the sheet structure, column layout, and
  formula patterns used by generate_spreadsheet. Templates produce
  dynamic, formula-driven Excel workbooks — not static data dumps.
  """


  SPREADSHEET_TEMPLATES = {
      "competitor_analysis": {
          "description": "Competitor analysis matrix with scoring, comparison charts, and SWOT",
          "sheets": [
              {
                  "name": "Overview",
                  "columns": [
                      "Competitor", "Category", "Market Position",
                      "Price Range", "Target Audience", "Key Strength",
                      "Key Weakness", "Overall Score",
                  ],
                  "formulas": {},
                  # NOTE: "Overall Score" is a user-input field (1-10 scale),
                  # NOT a formula. The overview columns are descriptive text,
                  # so AVERAGE would produce #DIV/0!. Agent fills this manually.
              },
              {
                  "name": "Detailed Comparison",
                  "columns": [
                      "Attribute", "Our Brand", "Competitor 1",
                      "Competitor 2", "Competitor 3", "Gap Analysis",
                  ],
                  "formulas": {
                      "Gap Analysis": '=IF(B{row}>MAX(C{row}:E{row}),"Leading",IF(B{row}<MIN(C{row}:E{row}),"Lagging","Competitive"))',
                  },
              },
              {
                  "name": "SWOT Matrix",
                  "columns": [
                      "Category", "Item", "Impact (1-5)",
                      "Likelihood (1-5)", "Priority Score",
                  ],
                  "formulas": {
                      "Priority Score": "=C{row}*D{row}",
                  },
              },
          ],
      },
      "brand_audit": {
          "description": "Brand audit scorecard with evaluation criteria, scoring, and gap analysis",
          "sheets": [
              {
                  "name": "Scorecard",
                  "columns": [
                      "Dimension", "Criteria", "Current Score (1-10)",
                      "Target Score (1-10)", "Gap", "Priority",
                  ],
                  "formulas": {
                      "Gap": "=D{row}-C{row}",
                      "Priority": '=IF(E{row}>5,"Critical",IF(E{row}>3,"High",IF(E{row}>1,"Medium","Low")))',
                  },
              },
              {
                  "name": "Detailed Assessment",
                  "columns": [
                      "Area", "Findings", "Evidence", "Recommendation",
                  ],
                  "formulas": {},
              },
          ],
      },
      "content_calendar": {
          "description": "Monthly content calendar with scheduling, channels, themes, and status tracking",
          "sheets": [
              {
                  "name": "Monthly Plan",
                  "columns": [
                      "Week", "Date", "Channel", "Content Type",
                      "Topic/Theme", "Copy Draft", "Visual Needed",
                      "Status", "Owner",
                  ],
                  "formulas": {},
              },
              {
                  "name": "Content Ideas",
                  "columns": [
                      "Idea", "Content Pillar", "Channel", "Format",
                      "Priority", "Estimated Effort", "Notes",
                  ],
                  "formulas": {},
              },
              {
                  "name": "Channel Mix",
                  "columns": [
                      "Channel", "Posts/Month", "Avg Engagement Rate",
                      "Est. Reach", "Monthly Cost", "Cost per Engagement",
                  ],
                  "formulas": {
                      "Cost per Engagement": "=IF(B{row}*C{row}*D{row}=0,0,E{row}/(B{row}*C{row}*D{row}))",
                  },
              },
          ],
      },
      "kpi_dashboard": {
          "description": "KPI tracking dashboard with targets, actuals, trend formulas, and RAG status",
          "sheets": [
              {
                  "name": "Dashboard",
                  "columns": [
                      "KPI", "Category", "Target", "Actual",
                      "% Achievement", "Trend", "RAG Status",
                  ],
                  "formulas": {
                      "% Achievement": "=IF(C{row}=0,0,D{row}/C{row})",
                      "RAG Status": '=IF(E{row}>=0.9,"Green",IF(E{row}>=0.7,"Amber","Red"))',
                  },
              },
              {
                  "name": "Monthly Tracking",
                  "columns": [
                      "KPI", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "YTD Average",
                  ],
                  "formulas": {
                      "YTD Average": "=AVERAGE(B{row}:M{row})",
                  },
              },
          ],
      },
      "budget_plan": {
          "description": "Marketing budget with channel allocation, ROI projections, and variance tracking",
          "sheets": [
              {
                  "name": "Budget Overview",
                  "columns": [
                      "Category", "Q1 Budget", "Q2 Budget",
                      "Q3 Budget", "Q4 Budget", "Annual Total",
                      "% of Total",
                  ],
                  "formulas": {
                      "Annual Total": "=SUM(B{row}:E{row})",
                      # Note: $TOTAL_ROW must be resolved at build time
                      # to the actual last data row + 1 (SUM row).
                      # Implementation: after populating data rows, compute
                      # total_row = first_data_row + num_data_rows (the SUM row)
                      # and replace {total_row} in the formula string.
                      "% of Total": "=F{row}/F{total_row}",
                  },
              },
              {
                  "name": "Channel Breakdown",
                  "columns": [
                      "Channel", "Monthly Budget", "Est. Impressions",
                      "Est. Clicks", "Est. Conversions", "CPM", "CPC", "CPA",
                  ],
                  "formulas": {
                      "CPM": "=IF(C{row}=0,0,(B{row}/C{row})*1000)",
                      "CPC": "=IF(D{row}=0,0,B{row}/D{row})",
                      "CPA": "=IF(E{row}=0,0,B{row}/E{row})",
                  },
              },
              {
                  "name": "ROI Projections",
                  "columns": [
                      "Initiative", "Investment", "Projected Revenue",
                      "Projected ROI", "Confidence Level",
                  ],
                  "formulas": {
                      "Projected ROI": "=IF(B{row}=0,0,(C{row}-B{row})/B{row})",
                  },
              },
          ],
      },
  }
  ```

- **Acceptance Criteria**:
  - [ ] All 5 templates defined with sheet structure and formula patterns
  - [ ] Formulas use Excel formula syntax, not Python calculations
  - [ ] Templates cover key brand strategy deliverables

#### Requirement 2 — XLSX Builder & Tool Function
- **Requirement**: Build Excel workbooks from templates, applying brand formatting, formulas, and data. The builder creates dynamic spreadsheets where editing inputs auto-recalculates derived fields.

- **Implementation**:
  - `src/shared/src/shared/agent_tools/document/xlsx_builder.py`
  ```python
  """
  Brand strategy XLSX builder using openpyxl.

  Generates formula-driven, professionally formatted Excel workbooks
  for brand strategy deliverables. Follows color-coding conventions:
  blue (#4472C4) for user inputs, black for formulas, green (#548235)
  for cross-sheet references.

  CRITICAL: All calculations MUST use Excel formulas, not hardcoded
  Python values. Spreadsheets must be dynamic.
  """
  from pathlib import Path
  from typing import Any

  from openpyxl import Workbook
  from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
  from openpyxl.utils import get_column_letter


  # =========================================================================
  # Color Constants (brand strategy color coding)
  # =========================================================================

  HEADER_FILL = PatternFill(
      start_color="1F4E79", end_color="1F4E79", fill_type="solid"
  )
  HEADER_FONT = Font(
      name="Calibri", size=11, bold=True, color="FFFFFF"
  )
  INPUT_FONT = Font(
      name="Calibri", size=11, color="4472C4"  # Blue = user input
  )
  FORMULA_FONT = Font(
      name="Calibri", size=11, color="000000"  # Black = formula
  )
  CROSSREF_FONT = Font(
      name="Calibri", size=11, color="548235"  # Green = cross-sheet ref
  )
  THIN_BORDER = Border(
      left=Side(style="thin"),
      right=Side(style="thin"),
      top=Side(style="thin"),
      bottom=Side(style="thin"),
  )


  class BrandStrategyXLSXBuilder:
      """
      Builds branded Excel workbooks from template definitions.

      Creates multi-sheet workbooks with:
          - Professional header formatting (dark navy, white text)
          - Color-coded cells (blue=inputs, black=formulas, green=cross-refs)
          - Auto-fitted column widths
          - Frozen header rows
          - Excel formulas for all calculations

      Args:
          brand_name: Brand name for title row.
          brand_colors: Optional [primary_hex, secondary_hex, accent_hex].
      """

      def __init__(
          self,
          brand_name: str = "Brand",
          brand_colors: list[str] | None = None,
      ):
          self.brand_name = brand_name
          self.brand_colors = brand_colors or []
          self.wb = Workbook()
          # Remove default sheet — we create named sheets from template
          self.wb.remove(self.wb.active)

      def build_from_template(
          self,
          template_def: dict,
          data: dict[str, list[dict[str, Any]]],
      ) -> Workbook:
          """
          Build workbook from a SPREADSHEET_TEMPLATES entry.

          Args:
              template_def: Template dict with "sheets" list.
              data: Dict mapping sheet name → list of row dicts.
                  Each row dict maps column name → value.

          Returns:
              Populated openpyxl Workbook ready to save.
          """
          for sheet_def in template_def["sheets"]:
              sheet_name = sheet_def["name"]
              columns = sheet_def["columns"]
              formulas = sheet_def.get("formulas", {})
              sheet_data = data.get(sheet_name, [])

              ws = self.wb.create_sheet(title=sheet_name)
              self._write_title_row(ws, sheet_name, len(columns))
              self._write_headers(ws, columns, row=2)
              self._write_data_rows(ws, columns, sheet_data, formulas, start_row=3)
              self._apply_formatting(ws, columns)

          return self.wb

      def _write_title_row(self, ws, title: str, col_span: int):
          """Write brand + sheet title as merged row 1."""
          ws.merge_cells(
              start_row=1, start_column=1,
              end_row=1, end_column=col_span,
          )
          cell = ws.cell(row=1, column=1)
          cell.value = f"{self.brand_name} — {title}"
          cell.font = Font(name="Calibri", size=14, bold=True)
          cell.alignment = Alignment(horizontal="center")

      def _write_headers(self, ws, columns: list[str], row: int = 2):
          """Write column headers with professional formatting."""
          for col_idx, col_name in enumerate(columns, 1):
              cell = ws.cell(row=row, column=col_idx)
              cell.value = col_name
              cell.fill = HEADER_FILL
              cell.font = HEADER_FONT
              cell.alignment = Alignment(horizontal="center", wrap_text=True)
              cell.border = THIN_BORDER

      def _write_data_rows(
          self,
          ws,
          columns: list[str],
          data: list[dict[str, Any]],
          formulas: dict[str, str],
          start_row: int = 3,
      ):
          """
          Write data rows with formulas where defined.

          For columns with formula patterns, inserts the Excel formula
          with {row} replaced by actual row number and {total_row}
          replaced by the SUM/total row (last data row + 1).

          Also appends:
          - {row_scores}: expands to the cell range for score columns
            in the same row (columns B through second-to-last).
          """
          # Compute total_row for budget_plan "% of Total" formulas.
          # total_row = one row after the last data row (the SUM row).
          total_row = start_row + len(data)

          for row_offset, row_data in enumerate(data):
              row_num = start_row + row_offset
              for col_idx, col_name in enumerate(columns, 1):
                  cell = ws.cell(row=row_num, column=col_idx)

                  if col_name in formulas:
                      # Insert Excel formula with placeholders resolved
                      formula = formulas[col_name]
                      formula = formula.replace("{row}", str(row_num))
                      formula = formula.replace(
                          "{total_row}", str(total_row)
                      )
                      # {row_scores} — expand to score column range
                      # (columns B through second-to-last column)
                      if "{row_scores}" in formula:
                          last_score_col = get_column_letter(
                              len(columns) - 1
                          )
                          formula = formula.replace(
                              "{row_scores}",
                              f"B{row_num}:{last_score_col}{row_num}",
                          )
                      cell.value = formula
                      cell.font = FORMULA_FONT
                  else:
                      cell.value = row_data.get(col_name, "")
                      cell.font = INPUT_FONT

                  cell.border = THIN_BORDER
                  cell.alignment = Alignment(wrap_text=True)

      def _apply_formatting(self, ws, columns: list[str]):
          """Apply auto-width, freeze panes, and number formatting."""
          # Auto-fit column widths (approximate)
          for col_idx, col_name in enumerate(columns, 1):
              col_letter = get_column_letter(col_idx)
              max_width = max(len(col_name), 12)
              ws.column_dimensions[col_letter].width = max_width + 2

          # Freeze header rows (rows 1-2 are title + headers)
          ws.freeze_panes = "A3"

      def save(self, output_path: str) -> str:
          """
          Save workbook to file.

          Args:
              output_path: Absolute or relative path for .xlsx file.

          Returns:
              Absolute path to saved file.
          """
          path = Path(output_path)
          path.parent.mkdir(parents=True, exist_ok=True)
          self.wb.save(str(path))
          return str(path.resolve())
  ```

  - `src/shared/src/shared/agent_tools/document/generate_spreadsheet.py`
  ```python
  """
  generate_spreadsheet tool — creates brand strategy Excel workbooks.

  Produces formula-driven, professionally formatted XLSX files for
  marketing deliverables: competitor analysis, KPI dashboards,
  content calendars, and budget planning.
  """
  import json
  import os
  from typing import Any

  from loguru import logger

  from shared.agent_tools.document.spreadsheet_templates import (
      SPREADSHEET_TEMPLATES,
  )
  from shared.agent_tools.document.xlsx_builder import (
      BrandStrategyXLSXBuilder,
  )


  def generate_spreadsheet(
      content: str,
      template: str = "competitor_analysis",
      brand_name: str = "Brand",
      brand_colors: list[str] | None = None,
      output_path: str | None = None,
  ) -> str:
      """
      Generate a brand strategy spreadsheet (XLSX).

      Creates formatted, formula-driven Excel workbooks for common
      brand strategy deliverables. Spreadsheets are dynamic — edit
      input cells and formula cells recalculate automatically.

      Available templates:
          - "competitor_analysis": Scoring matrix, comparison, SWOT
          - "brand_audit": Scorecard with gap analysis and prioritization
          - "content_calendar": Monthly plan, ideas backlog, channel mix
          - "kpi_dashboard": Targets vs actuals with RAG status and trends
          - "budget_plan": Channel budgets, ROI projections, variance

      Args:
          content: JSON string mapping sheet names to row data.
              Format: {"SheetName": [{"Column1": val, "Column2": val}, ...]}
          template: Spreadsheet type — see available templates above.
          brand_name: Brand name for title headers.
          brand_colors: [primary_hex, secondary_hex, accent_hex] for theming.
          output_path: Custom output path. Default: resolved from
              BRANDMIND_OUTPUT_DIR env var → ./brandmind-output/spreadsheets/

      Returns:
          Path to generated .xlsx file + sheet summary.
          Format: "Spreadsheet saved to: {path}\\nSheets: {list}\\nTemplate: {name}"
      """
      logger.info(
          f"Generating spreadsheet: template={template}, "
          f"brand={brand_name}"
      )

      # Validate template
      if template not in SPREADSHEET_TEMPLATES:
          available = ", ".join(SPREADSHEET_TEMPLATES.keys())
          return (
              f"Unknown template '{template}'. "
              f"Available templates: {available}"
          )

      template_def = SPREADSHEET_TEMPLATES[template]

      # Parse content JSON
      try:
          data: dict[str, list[dict[str, Any]]] = json.loads(content)
      except json.JSONDecodeError as e:
          return f"Invalid content JSON: {e}"

      # Resolve output path
      if not output_path:
          base = os.environ.get(
              "BRANDMIND_OUTPUT_DIR",
              os.path.join(os.getcwd(), "brandmind-output"),
          )
          output_dir = os.path.join(base, "spreadsheets")
          os.makedirs(output_dir, exist_ok=True)
          safe_name = brand_name.lower().replace(" ", "_")
          output_path = os.path.join(
              output_dir, f"{safe_name}_{template}.xlsx"
          )

      # Build and save workbook
      try:
          builder = BrandStrategyXLSXBuilder(
              brand_name=brand_name,
              brand_colors=brand_colors,
          )
          builder.build_from_template(template_def, data)
          saved_path = builder.save(output_path)

          sheet_names = [s["name"] for s in template_def["sheets"]]
          logger.info(f"Spreadsheet saved: {saved_path}")

          return (
              f"Spreadsheet saved to: {saved_path}\n"
              f"Sheets: {', '.join(sheet_names)}\n"
              f"Template: {template} — {template_def['description']}\n"
              f"Note: Formulas are embedded. Open in Excel/Google Sheets "
              f"for auto-calculation."
          )

      except Exception as e:
          logger.error(f"Spreadsheet generation failed: {e}")
          return f"Spreadsheet generation failed: {e}"
  ```

- **Acceptance Criteria**:
  - [ ] All 5 templates generate valid XLSX files
  - [ ] Excel formulas embedded (SUM, AVERAGE, IF, VLOOKUP patterns)
  - [ ] Color coding applied: blue inputs, black formulas
  - [ ] Header rows frozen, columns auto-sized
  - [ ] Opens correctly in Excel, Google Sheets, LibreOffice
  - [ ] Brand name appears in title row of each sheet
  - [ ] Output path follows BRANDMIND_OUTPUT_DIR convention

------------------------------------------------------------------------

## 🧪 Test Execution Log

> **Agent**: Record actual test results here as you run them.
> Do not mark a test as Passed until you have run it and seen the output.

### Test 1: PDF Generation
- **Purpose**: Verify full brand strategy PDF generation
- **Steps**:
  1. Prepare mock phase_outputs dict with all 6 phases
  2. Call `generate_document(content=json.dumps(mock_data), format="pdf", brand_name="Test Brand")`
  3. Open generated PDF
- **Expected Result**: Multi-page PDF with cover, TOC, all sections, tables, footer
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 2: DOCX Generation & Editability
- **Purpose**: Verify DOCX opens correctly in Word/Google Docs
- **Steps**:
  1. Generate DOCX with `format="docx"`
  2. Open in Word/Google Docs
  3. Verify formatting intact and editable
- **Expected Result**: Editable document with correct styles
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 3: PPTX Pitch Deck
- **Purpose**: Verify presentation generation
- **Steps**:
  1. Call `generate_presentation(content=json.dumps(mock_data))`
  2. Open in PowerPoint/Google Slides
  3. Verify 10-15 slides with correct content
- **Expected Result**: Professional pitch deck with brand colors
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 4: Vietnamese Text Rendering
- **Purpose**: Verify Unicode/Vietnamese text in PDF
- **Steps**:
  1. Include Vietnamese content in phase outputs
  2. Generate PDF
  3. Check diacritics render correctly
- **Expected Result**: Vietnamese text with all diacritics intact
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 5: XLSX Competitor Analysis
- **Purpose**: Verify competitor analysis spreadsheet with formulas
- **Steps**:
  1. Prepare mock competitor data
  2. Call `generate_spreadsheet(content=json.dumps(mock_data), template="competitor_analysis")`
  3. Open in Excel/Google Sheets
  4. Verify formulas calculate (change an input, check derived cells update)
- **Expected Result**: Multi-sheet workbook with working formulas, blue input cells, frozen headers
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 6: XLSX KPI Dashboard
- **Purpose**: Verify KPI dashboard with RAG status formulas
- **Steps**:
  1. Prepare mock KPI data
  2. Call `generate_spreadsheet(content=json.dumps(mock_data), template="kpi_dashboard")`
  3. Verify RAG status formula works (Green/Amber/Red based on % Achievement)
- **Expected Result**: Dashboard with correct RAG status, % calculated from formula
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 7: Output Directory Resolution
- **Purpose**: Verify all tools respect BRANDMIND_OUTPUT_DIR
- **Steps**:
  1. Set `BRANDMIND_OUTPUT_DIR=/tmp/test-brand-output`
  2. Call generate_document, generate_presentation, generate_spreadsheet
  3. Verify all outputs under `/tmp/test-brand-output/`
- **Expected Result**: All files in correct subdirectories (documents/, presentations/, spreadsheets/)
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📊 Decision Log

> **Agent**: Document every significant decision made during implementation.

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | PDF library | fpdf2 vs ReportLab vs WeasyPrint | fpdf2 | Lightweight, LGPL, good Unicode support, sufficient for strategy docs |
| 2 | Excel approach | openpyxl vs xlsxwriter vs pandas to_excel | openpyxl | Supports formulas + formatting + reading, MIT license, pandas uses openpyxl internally |
| 3 | Formula strategy | Hardcoded Python values vs Excel formulas | Excel formulas | Dynamic spreadsheets that recalculate on edit — essential for planning tools |
| 4 | Output directory | Hardcoded paths vs BRANDMIND_OUTPUT_DIR env var | Env var with CWD default | Consistent across all tools (images, docs, spreadsheets), CLI-friendly |
| 5 | Template vs freeform | Only template-based generation vs allow arbitrary content | Template-based with data injection | Consistent quality, formula patterns pre-defined, agent provides data not structure |

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation and all tests pass.

### What Was Implemented

**Components Completed**:
- [ ] [Component 1]: Brand Strategy Document Templates — 10-section doc + 12-slide deck structure
- [ ] [Component 2]: generate_document Tool (PDF + DOCX) — professional branded documents
- [ ] [Component 3]: generate_presentation Tool (PPTX) — pitch deck with brand theme
- [ ] [Component 4]: export_to_markdown Tool — clean Markdown for Notion/GitHub
- [ ] [Component 5]: generate_spreadsheet Tool (XLSX) — 5 formula-driven templates

**Files Created/Modified**:
```
src/shared/src/shared/agent_tools/document/
├── __init__.py                    # Package exports
├── templates/
│   ├── __init__.py
│   └── brand_strategy.py         # Document & deck templates
├── pdf_builder.py                 # fpdf2-based PDF generation
├── docx_builder.py                # python-docx DOCX generation
├── pptx_builder.py                # python-pptx PPTX generation
├── xlsx_builder.py                # openpyxl XLSX generation (formulas + formatting)
├── spreadsheet_templates.py       # XLSX template definitions (5 templates)
├── generate_document.py           # Tool function (PDF/DOCX)
├── generate_presentation.py       # Tool function (PPTX)
├── generate_spreadsheet.py        # Tool function (XLSX)
└── export_to_markdown.py          # Tool function (Markdown)
```

**Key Features Delivered**:
1. **4-format document generation**: PDF, DOCX, PPTX, XLSX from structured phase outputs
2. **5 Excel templates**: competitor analysis, brand audit, content calendar, KPI dashboard, budget plan — all formula-driven
3. **Consistent output directory**: All tools use BRANDMIND_OUTPUT_DIR → ./brandmind-output/ default

### Technical Highlights

**Architecture Decisions** (see Decision Log for details):
- Template-based generation for consistent quality
- Excel formulas (not hardcoded values) for dynamic spreadsheets
- fpdf2 for PDF (Unicode/Vietnamese support)

**Performance / Quality Results**:
- [PDF generation time]: [Observed result]
- [XLSX formula validation]: [Confirmed working in Excel/Sheets]

**Documentation Checklist**:
- [ ] All functions have comprehensive docstrings (purpose, args, returns)
- [ ] Template structures documented
- [ ] Type hints complete and accurate

### Validation Results

**Test Results**:
- [ ] All tests in Test Execution Log: ✅ Passed
- [ ] Vietnamese text renders correctly in PDF
- [ ] DOCX formatting survives Google Docs import
- [ ] XLSX formulas recalculate in Excel/Google Sheets

**Deployment Notes**:
- New dependencies: fpdf2, python-docx, python-pptx, openpyxl (add to `src/shared/pyproject.toml`)
- Optional: Set BRANDMIND_OUTPUT_DIR to customize output location
- Vietnamese PDF requires Unicode font — fpdf2 does NOT include Vietnamese-capable fonts by default. Implementation must:
  1. Bundle a Unicode font that covers Vietnamese diacritics (recommended: **NotoSans** or **DejaVuSans**)
  2. Register the font via `pdf.add_font("NotoSans", "", "path/to/NotoSans-Regular.ttf", uni=True)`
  3. Store font files in `src/shared/src/shared/agent_tools/document/fonts/` (committed to repo)
  4. Test with Vietnamese text: `"Cà phê đặc biệt Việt Nam"` — verify all diacritics render correctly
  - **Risk**: If font is missing at runtime, PDF generation will fall back to Helvetica and Vietnamese characters will render as `?` or boxes

------------------------------------------------------------------------
