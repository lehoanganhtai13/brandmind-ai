"""Unit tests for document generation tools (Task 39).

Tests export_to_markdown helpers and spreadsheet templates.
Pure function tests only — no external API calls.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from shared.agent_tools.document._output_path import (
    _manifest_path,
    _slugify_brand,
    append_manifest,
    resolve_output_path,
)
from shared.agent_tools.document.export_to_markdown import (
    _PHASE_TITLES,
    _render_value,
    _format_table,
    _format_full_document,
    export_to_markdown,
)
from shared.agent_tools.document.generate_document import generate_document
from shared.agent_tools.document.generate_spreadsheet import generate_spreadsheet
from shared.agent_tools.document.list_artifacts import list_artifacts
from shared.agent_tools.document.spreadsheet_templates import SPREADSHEET_TEMPLATES


# ===== _PHASE_TITLES =====


class TestPhaseTitles:
    """Verify _PHASE_TITLES mapping has the expected entries."""

    EXPECTED_KEYS = {
        "cover",
        "executive_summary",
        "phase_0_output",
        "phase_0_5_output",
        "phase_1_output",
        "phase_2_output",
        "phase_3_output",
        "phase_4_output",
        "phase_5_output",
        "appendices",
    }

    def test_has_exactly_10_entries(self):
        assert len(_PHASE_TITLES) == 10

    def test_contains_all_expected_keys(self):
        assert set(_PHASE_TITLES.keys()) == self.EXPECTED_KEYS

    def test_all_values_are_non_empty_strings(self):
        for key, title in _PHASE_TITLES.items():
            assert isinstance(title, str), f"Title for '{key}' is not a string"
            assert len(title) > 0, f"Title for '{key}' is empty"

    def test_cover_title(self):
        assert _PHASE_TITLES["cover"] == "Cover"

    def test_executive_summary_title(self):
        assert _PHASE_TITLES["executive_summary"] == "Executive Summary"

    def test_phase_0_5_title(self):
        assert _PHASE_TITLES["phase_0_5_output"] == "Brand Equity Audit"

    def test_appendices_title(self):
        assert _PHASE_TITLES["appendices"] == "Appendices"


# ===== _render_value =====


class TestRenderValue:
    """Test recursive Markdown rendering of values."""

    def test_string_returned_as_is(self):
        assert _render_value("hello world", level=3) == "hello world"

    def test_empty_string(self):
        assert _render_value("", level=3) == ""

    def test_dict_renders_keys_as_headings(self):
        data = {"brand_name": "Acme", "tagline": "Quality First"}
        result = _render_value(data, level=3)
        assert "### Brand Name" in result
        assert "Acme" in result
        assert "### Tagline" in result
        assert "Quality First" in result

    def test_dict_heading_level_increments(self):
        data = {"outer": {"inner": "deep"}}
        result = _render_value(data, level=2)
        assert "## Outer" in result
        assert "### Inner" in result
        assert "deep" in result

    def test_dict_heading_level_caps_at_6(self):
        data = {"key": "value"}
        result = _render_value(data, level=7)
        # min(7, 6) = 6, so should use ######
        assert "###### Key" in result

    def test_list_of_dicts_renders_as_table(self):
        data = [
            {"name": "Alpha", "score": 9},
            {"name": "Beta", "score": 7},
        ]
        result = _render_value(data, level=3)
        # Table should have header row with pipe characters
        assert "| Name | Score |" in result
        assert "| Alpha | 9 |" in result
        assert "| Beta | 7 |" in result

    def test_list_of_strings_renders_as_bullets(self):
        data = ["item one", "item two", "item three"]
        result = _render_value(data, level=3)
        assert "- item one" in result
        assert "- item two" in result
        assert "- item three" in result

    def test_integer_converted_to_string(self):
        assert _render_value(42, level=3) == "42"

    def test_float_converted_to_string(self):
        assert _render_value(3.14, level=3) == "3.14"

    def test_boolean_converted_to_string(self):
        assert _render_value(True, level=3) == "True"

    def test_none_converted_to_string(self):
        assert _render_value(None, level=3) == "None"

    def test_empty_list(self):
        # Empty list — no dicts, joins empty list of strings
        result = _render_value([], level=3)
        assert result == ""

    def test_empty_dict(self):
        result = _render_value({}, level=3)
        assert result == ""


# ===== _format_table =====


class TestFormatTable:
    """Test Markdown table generation from list of dicts."""

    def test_basic_table(self):
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        result = _format_table(data)
        lines = result.split("\n")
        assert len(lines) == 4  # header + separator + 2 data rows
        assert lines[0] == "| Name | Age |"
        assert lines[1] == "| --- | --- |"
        assert lines[2] == "| Alice | 30 |"
        assert lines[3] == "| Bob | 25 |"

    def test_empty_list_returns_empty_string(self):
        assert _format_table([]) == ""

    def test_single_row(self):
        data = [{"metric": "Revenue", "value": "100k"}]
        result = _format_table(data)
        lines = result.split("\n")
        assert len(lines) == 3  # header + separator + 1 data row
        assert "| Revenue | 100k |" in result

    def test_pipe_characters_escaped(self):
        data = [{"content": "A | B", "status": "ok"}]
        result = _format_table(data)
        # Pipe in value should be escaped
        assert "A \\| B" in result

    def test_missing_key_uses_empty_string(self):
        data = [
            {"a": 1, "b": 2},
            {"a": 3},  # missing "b"
        ]
        result = _format_table(data)
        lines = result.split("\n")
        # Last row should have empty cell for missing "b"
        assert lines[3] == "| 3 |  |"

    def test_headers_from_first_dict_keys(self):
        data = [{"first_name": "X", "last_name": "Y"}]
        result = _format_table(data)
        assert "| First Name | Last Name |" in result

    def test_non_string_values_converted(self):
        data = [{"count": 42, "active": True}]
        result = _format_table(data)
        assert "| 42 | True |" in result


# ===== _format_full_document =====


class TestFormatFullDocument:
    """Test full document rendering with TOC and sections."""

    def test_document_starts_with_title(self):
        content = {"cover": "Brand X"}
        result = _format_full_document(content)
        assert result.startswith("# Brand Strategy\n")

    def test_toc_present(self):
        content = {"cover": "Brand X", "executive_summary": "Summary here"}
        result = _format_full_document(content)
        assert "## Table of Contents" in result

    def test_toc_links_generated(self):
        content = {"cover": "Brand X"}
        result = _format_full_document(content)
        assert "- [Cover](#cover)" in result

    def test_toc_link_for_phase_with_ampersand(self):
        content = {"phase_0_output": "data"}
        result = _format_full_document(content)
        title = _PHASE_TITLES["phase_0_output"]
        # Anchor: "business context & problem statement" → "business-context--problem-statement"
        anchor = title.lower().replace(" ", "-").replace("&", "")
        assert f"- [{title}](#{anchor})" in result

    def test_sections_rendered_with_h2(self):
        content = {"cover": "Brand X", "appendices": "References"}
        result = _format_full_document(content)
        assert "## Cover" in result
        assert "## Appendices" in result

    def test_section_values_rendered(self):
        content = {"executive_summary": "This is the summary."}
        result = _format_full_document(content)
        assert "This is the summary." in result

    def test_unknown_key_gets_title_cased(self):
        content = {"custom_section": "Custom content"}
        result = _format_full_document(content)
        assert "## Custom Section" in result
        assert "- [Custom Section]" in result

    def test_multiple_sections_ordering(self):
        content = {
            "cover": "First",
            "executive_summary": "Second",
            "appendices": "Third",
        }
        result = _format_full_document(content)
        cover_pos = result.index("## Cover")
        summary_pos = result.index("## Executive Summary")
        appendices_pos = result.index("## Appendices")
        assert cover_pos < summary_pos < appendices_pos

    def test_nested_dict_in_section(self):
        content = {
            "phase_1_output": {
                "market_size": "Large",
                "competitors": ["A", "B"],
            }
        }
        result = _format_full_document(content)
        assert "### Market Size" in result
        assert "Large" in result
        assert "- A" in result
        assert "- B" in result

    def test_empty_content_produces_minimal_document(self):
        result = _format_full_document({})
        assert "# Brand Strategy" in result
        assert "## Table of Contents" in result


# ===== export_to_markdown =====


class TestExportToMarkdown:
    """Test the top-level export_to_markdown function."""

    def test_invalid_json_returns_error(self):
        result = export_to_markdown("not valid json")
        assert "Invalid content JSON" in result

    def test_none_content_returns_error(self):
        result = export_to_markdown(None)
        assert "Invalid content JSON" in result

    def test_short_content_returned_directly(self):
        content = json.dumps({"cover": "Brand X"})
        result = export_to_markdown(content)
        # Short content should be the markdown itself
        assert "# Brand Strategy" in result
        assert "Brand X" in result

    def test_section_filtering(self):
        content = json.dumps({
            "cover": "Brand X",
            "executive_summary": "Summary",
            "appendices": "Refs",
        })
        result = export_to_markdown(content, sections=["cover"])
        assert "Brand X" in result
        # Filtered sections should not appear
        assert "Summary" not in result
        assert "Refs" not in result

    def test_section_filtering_with_multiple_keys(self):
        content = json.dumps({
            "cover": "Brand X",
            "executive_summary": "Summary",
            "appendices": "Refs",
        })
        result = export_to_markdown(content, sections=["cover", "appendices"])
        assert "Brand X" in result
        assert "Refs" in result
        assert "Summary" not in result

    def test_long_content_writes_to_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Long content is written to disk under the configured output dir.

        The sandbox in :mod:`_output_path` anchors writes under
        ``$BRANDMIND_OUTPUT_DIR``. Pinning the env var to ``tmp_path``
        makes ``tmp_path`` the configured base, so a path supplied
        under it is honoured by the sandbox as-is. The result message
        reports the absolute filesystem path the user can open.
        """
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        # Build content large enough to exceed _SHORT_CONTENT_THRESHOLD (2000)
        large_text = "A" * 2500
        content = json.dumps({"cover": large_text})
        output_file = tmp_path / "export.md"

        result = export_to_markdown(content, output_path=str(output_file))

        assert "Markdown exported to:" in result
        assert str(output_file) in result
        assert output_file.exists()
        file_content = output_file.read_text(encoding="utf-8")
        assert "# Brand Strategy" in file_content
        assert large_text in file_content

    def test_long_content_creates_parent_dirs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sandbox creates the category subdirectory when it does not exist."""
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        content = json.dumps({"cover": "X" * 2500})
        # Provide a nested path under the configured base; the sandbox
        # only redirects when the path escapes the base, so a nested
        # sub-path under tmp_path is honoured.
        output_file = tmp_path / "nested" / "deep" / "export.md"

        result = export_to_markdown(content, output_path=str(output_file))

        assert output_file.exists()
        assert "Markdown exported to:" in result

    def test_long_content_reports_char_count(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Result message reports the character count regardless of write location."""
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        content = json.dumps({"cover": "B" * 2500})
        output_file = tmp_path / "export.md"

        result = export_to_markdown(content, output_path=str(output_file))

        assert "characters" in result

    def test_long_content_default_path_uses_brand_subdir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without output_path, file lands in <base>/documents/<brand-slug>/<timestamp>_*.md."""
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        content = json.dumps({"cover": "C" * 2500})

        result = export_to_markdown(
            content,
            brand_name="Chuyện Ba Bữa Signature",
        )

        documents_dir = tmp_path / "documents"
        # Per-brand subdir uses slugified form (Vietnamese diacritics → hyphens)
        assert documents_dir.exists()
        brand_subdirs = list(documents_dir.iterdir())
        assert len(brand_subdirs) == 1
        # Slugifier collapses diacritics + spaces into hyphens
        assert "-" in brand_subdirs[0].name
        # Filename has timestamp prefix
        produced_files = list(brand_subdirs[0].iterdir())
        assert len(produced_files) == 1
        assert produced_files[0].name.endswith("brand_strategy_export.md")
        # Result message contains the absolute path the user can open
        assert str(produced_files[0]) in result

    def test_empty_sections_filter_returns_full_doc(self):
        content = json.dumps({"cover": "Brand X", "appendices": "Refs"})
        result = export_to_markdown(content, sections=[])
        # Empty list is falsy, so no filtering should happen
        assert "Brand X" in result
        assert "Refs" in result

    def test_nonexistent_section_filter_returns_minimal(self):
        content = json.dumps({"cover": "Brand X"})
        result = export_to_markdown(content, sections=["nonexistent"])
        # Nothing matches, so content dict is empty after filtering
        assert "# Brand Strategy" in result
        assert "Brand X" not in result


# ===== generate_document =====


class TestGenerateDocument:
    """Test the report builder tool contract."""

    def test_accepts_structured_content_object(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        content = {
            "cover": "Modern Heritage Bistro",
            "executive_summary": ["Clarify Signature positioning."],
            "phase_0_output": {"Problem": "Weekday bookings are weak."},
            "phase_1_output": {"Target": "Executive lunch guests."},
            "phase_2_output": {"Positioning": "Vietnamese heritage bistro."},
            "phase_3_output": {"Visual": "Peacock blue and bronze."},
            "phase_4_output": {"Messaging": "Vị di sản quen, trải nghiệm mới."},
            "phase_5_output": {
                "roadmap": [{"Horizon": "0-3 months", "Items": "Launch assets"}],
                "measurement": [
                    {
                        "KPI": "Weekday bookings",
                        "Method": "Reservation log",
                        "Baseline": "measure weeks 1-2",
                        "Target": "20% monthly growth",
                        "Cadence": "weekly",
                    }
                ],
            },
        }

        result = generate_document(
            content,
            brand_name="Chuyện Ba Bữa Signature",
        )

        assert "Document FILE saved to disk" in result
        assert "Format: DOCX" in result
        path_line = next(
            line for line in result.splitlines() if line.startswith("Path: ")
        )
        artifact_path = Path(path_line.removeprefix("Path: "))
        assert artifact_path.is_file()
        assert tmp_path in artifact_path.parents


# ===== generate_spreadsheet =====


class TestGenerateSpreadsheet:
    """Test spreadsheet generation guardrails for KPI dashboards."""

    def test_kpi_targets_get_default_horizon_when_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from openpyxl import load_workbook

        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        content = {
            "Dashboard": [
                {
                    "KPI": "CPA (Cost per Booking)",
                    "Method": "Ads Manager + Booking Log",
                    "Baseline": "no data — measure pre-launch",
                    "Target": "< 150,000 VND",
                    "Cadence": "monthly",
                    "Owner": "Marketing Exec",
                    "Current": "no data — measure pre-launch",
                    "Notes": "Track paid acquisition efficiency",
                }
            ]
        }

        result = generate_spreadsheet(
            json.dumps(content, ensure_ascii=False),
            template="kpi_dashboard",
            brand_name="Chuyện Ba Bữa Signature",
        )

        path_line = next(
            line for line in result.splitlines() if line.startswith("Path: ")
        )
        workbook = load_workbook(Path(path_line.removeprefix("Path: ")))
        dashboard = workbook["Dashboard"]
        monthly = workbook["Monthly Tracking"]

        assert dashboard["D3"].value == "< 150,000 VND by Month 3"
        assert monthly["A3"].value == "CPA (Cost per Booking)"


# ===== SPREADSHEET_TEMPLATES =====


class TestSpreadsheetTemplates:
    """Verify spreadsheet template structure and completeness."""

    EXPECTED_TEMPLATE_KEYS = {
        "competitor_analysis",
        "brand_audit",
        "content_calendar",
        "kpi_dashboard",
        "budget_plan",
    }

    def test_has_exactly_5_templates(self):
        assert len(SPREADSHEET_TEMPLATES) == 5

    def test_contains_all_expected_keys(self):
        assert set(SPREADSHEET_TEMPLATES.keys()) == self.EXPECTED_TEMPLATE_KEYS

    @pytest.mark.parametrize("key", EXPECTED_TEMPLATE_KEYS)
    def test_template_has_description(self, key: str):
        template = SPREADSHEET_TEMPLATES[key]
        assert "description" in template
        assert isinstance(template["description"], str)
        assert len(template["description"]) > 0

    @pytest.mark.parametrize("key", EXPECTED_TEMPLATE_KEYS)
    def test_template_has_sheets(self, key: str):
        template = SPREADSHEET_TEMPLATES[key]
        assert "sheets" in template
        assert isinstance(template["sheets"], list)
        assert len(template["sheets"]) > 0

    @pytest.mark.parametrize("key", EXPECTED_TEMPLATE_KEYS)
    def test_each_sheet_has_required_fields(self, key: str):
        for sheet in SPREADSHEET_TEMPLATES[key]["sheets"]:
            assert "name" in sheet, f"Sheet in '{key}' missing 'name'"
            assert "headers" in sheet, f"Sheet in '{key}' missing 'headers'"
            assert "formulas" in sheet, f"Sheet in '{key}' missing 'formulas'"
            assert isinstance(sheet["name"], str)
            assert isinstance(sheet["headers"], list)
            assert isinstance(sheet["formulas"], dict)

    @pytest.mark.parametrize("key", EXPECTED_TEMPLATE_KEYS)
    def test_sheet_headers_are_non_empty_strings(self, key: str):
        for sheet in SPREADSHEET_TEMPLATES[key]["sheets"]:
            assert len(sheet["headers"]) > 0, (
                f"Sheet '{sheet['name']}' in '{key}' has no headers"
            )
            for header in sheet["headers"]:
                assert isinstance(header, str)
                assert len(header) > 0

    def test_competitor_analysis_sheets(self):
        sheets = SPREADSHEET_TEMPLATES["competitor_analysis"]["sheets"]
        sheet_names = [s["name"] for s in sheets]
        assert "Overview" in sheet_names
        assert "Detailed Comparison" in sheet_names

    def test_kpi_dashboard_sheets(self):
        sheets = SPREADSHEET_TEMPLATES["kpi_dashboard"]["sheets"]
        sheet_names = [s["name"] for s in sheets]
        assert "Dashboard" in sheet_names
        assert "Monthly Tracking" in sheet_names

    def test_budget_plan_has_total_row_formula(self):
        """Budget plan uses {total_row} placeholder in formulas."""
        sheets = SPREADSHEET_TEMPLATES["budget_plan"]["sheets"]
        overview = next(s for s in sheets if s["name"] == "Budget Overview")
        pct_formula = overview["formulas"]["% of Total"]
        assert "{total_row}" in pct_formula

    def test_formulas_use_row_placeholder(self):
        """All formulas should use {row} placeholder."""
        for key, template in SPREADSHEET_TEMPLATES.items():
            for sheet in template["sheets"]:
                for col, formula in sheet["formulas"].items():
                    assert "{row}" in formula, (
                        f"Formula for '{col}' in sheet '{sheet['name']}' "
                        f"of template '{key}' missing {{row}} placeholder"
                    )

    def test_brand_audit_gap_formula(self):
        sheets = SPREADSHEET_TEMPLATES["brand_audit"]["sheets"]
        scorecard = next(s for s in sheets if s["name"] == "Scorecard")
        assert "Gap" in scorecard["formulas"]
        assert scorecard["formulas"]["Gap"] == "=D{row}-C{row}"

    def test_kpi_dashboard_rag_formula(self):
        sheets = SPREADSHEET_TEMPLATES["kpi_dashboard"]["sheets"]
        dashboard = next(s for s in sheets if s["name"] == "Dashboard")
        assert "RAG Status" in dashboard["formulas"]
        assert "Green" in dashboard["formulas"]["RAG Status"]
        assert "Amber" in dashboard["formulas"]["RAG Status"]
        assert "Red" in dashboard["formulas"]["RAG Status"]

    def test_kpi_dashboard_has_actionable_tracker_columns(self) -> None:
        sheets = SPREADSHEET_TEMPLATES["kpi_dashboard"]["sheets"]
        dashboard = next(s for s in sheets if s["name"] == "Dashboard")
        for header in ("Method", "Baseline", "Cadence", "Owner", "Notes"):
            assert header in dashboard["headers"]


# ===== resolve_output_path =====


class TestSlugifyBrand:
    """Brand slug normalisation for per-brand subdirectory naming."""

    def test_lowercases_and_replaces_spaces(self) -> None:
        assert _slugify_brand("Brand Name") == "brand-name"

    def test_collapses_runs_of_special_chars(self) -> None:
        assert _slugify_brand("Brand   ---   Name!!!") == "brand-name"

    def test_strips_leading_trailing_hyphens(self) -> None:
        assert _slugify_brand("---Brand---") == "brand"

    def test_diacritics_collapse_to_hyphen(self) -> None:
        # Vietnamese diacritics are not ASCII alphanumerics — collapse
        # to hyphens to keep the directory name filesystem-safe.
        result = _slugify_brand("Chuyện Ba Bữa")
        assert result.startswith("chuy")
        assert "-" in result

    def test_empty_falls_back_to_brand(self) -> None:
        assert _slugify_brand("") == "brand"
        assert _slugify_brand("   ") == "brand"

    def test_pure_alphanumeric_passes_through(self) -> None:
        assert _slugify_brand("Acme123") == "acme123"


class TestResolveOutputPath:
    """Sandbox places artifacts under <base>/<category>/<brand-slug>/<timestamp>_*."""

    def test_none_provided_creates_per_brand_timestamp_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        path = resolve_output_path(
            None,
            category="documents",
            brand_name="Acme Corp",
            default_filename="brand_strategy.docx",
        )
        # <tmp>/documents/acme-corp/<timestamp>_brand_strategy.docx
        assert (tmp_path / "documents" / "acme-corp").exists()
        parts = Path(path).parts
        assert "documents" in parts
        assert "acme-corp" in parts
        assert Path(path).name.endswith("brand_strategy.docx")
        # Timestamp prefix YYYYMMDD_HHMMSS
        prefix = Path(path).name.split("_brand_strategy")[0]
        assert len(prefix) == 15  # 8 date digits + "_" + 6 time digits

    def test_path_under_base_is_honoured_as_is(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        provided = tmp_path / "custom" / "explicit.docx"
        path = resolve_output_path(
            str(provided),
            category="documents",
            brand_name="Acme",
            default_filename="brand_strategy.docx",
        )
        assert Path(path) == provided
        # Parent directory was created
        assert provided.parent.exists()

    def test_path_outside_base_redirected_with_timestamp(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        path = resolve_output_path(
            "/etc/evil.docx",
            category="documents",
            brand_name="Acme",
            default_filename="brand_strategy.docx",
        )
        # Redirected under per-brand subdir; basename preserved with
        # timestamp prefix.
        assert str(tmp_path) in path
        assert "documents" in Path(path).parts
        assert "acme" in Path(path).parts
        assert Path(path).name.endswith("evil.docx")

    def test_relative_path_redirected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        path = resolve_output_path(
            "stray.docx",
            category="documents",
            brand_name="Acme",
            default_filename="brand_strategy.docx",
        )
        # `os.path.abspath("stray.docx")` resolves under cwd, which is
        # outside tmp_path, so the sandbox redirects.
        assert str(tmp_path) in path
        assert Path(path).name.endswith("stray.docx")

    def test_different_brands_get_different_subdirs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        p1 = resolve_output_path(
            None, category="documents", brand_name="Brand A",
            default_filename="x.docx",
        )
        p2 = resolve_output_path(
            None, category="documents", brand_name="Brand B",
            default_filename="x.docx",
        )
        assert Path(p1).parent != Path(p2).parent
        assert "brand-a" in Path(p1).parts
        assert "brand-b" in Path(p2).parts


# ===== append_manifest =====


class TestAppendManifest:
    """JSONL manifest writer used by the artifact tools."""

    def test_appends_single_jsonl_line(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        artifact_path = tmp_path / "documents" / "acme" / "20260501_x.docx"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_bytes(b"hello world")

        append_manifest(
            brand_name="Acme",
            category="documents",
            tool="generate_document",
            path=str(artifact_path),
        )

        manifest = Path(_manifest_path())
        assert manifest.exists()
        lines = manifest.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["brand_name"] == "Acme"
        assert record["category"] == "documents"
        assert record["tool"] == "generate_document"
        assert record["filename"] == "20260501_x.docx"
        assert record["path"] == str(artifact_path)
        assert record["size_bytes"] == 11
        # No active session in unit tests → "unbound" sentinel
        assert record["session_id"] == "unbound"
        assert "generated_at" in record

    def test_multiple_appends_preserve_order(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        for i in range(3):
            f = tmp_path / f"f{i}.docx"
            f.write_text("x")
            append_manifest(
                brand_name="Acme",
                category="documents",
                tool="generate_document",
                path=str(f),
            )
        lines = Path(_manifest_path()).read_text(encoding="utf-8").splitlines()
        assert len(lines) == 3
        for i, line in enumerate(lines):
            record = json.loads(line)
            assert record["filename"] == f"f{i}.docx"

    def test_missing_file_records_zero_size(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        append_manifest(
            brand_name="Acme",
            category="documents",
            tool="generate_document",
            path=str(tmp_path / "does_not_exist.docx"),
        )
        record = json.loads(
            Path(_manifest_path()).read_text(encoding="utf-8").splitlines()[0]
        )
        assert record["size_bytes"] == 0


# ===== list_artifacts =====


class TestListArtifacts:
    """Manifest-backed query tool used by the orchestrator."""

    def _seed_manifest(self, base: Path, records: list[dict[str, Any]]) -> None:
        """Write a minimal manifest by hand so tests don't depend on
        append_manifest under specific session contexts."""
        base.mkdir(parents=True, exist_ok=True)
        manifest = base / ".manifest.jsonl"
        with manifest.open("a", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

    def test_no_manifest_returns_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        result = list_artifacts(scope="all")
        assert "No artifacts found" in result

    def test_all_scope_returns_every_record(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        self._seed_manifest(tmp_path, [
            {
                "session_id": "s1", "brand_name": "Brand A",
                "category": "documents", "tool": "generate_document",
                "filename": "a.docx", "path": "/x/a.docx",
                "size_bytes": 100, "generated_at": "2026-05-01T10:00:00+07:00",
            },
            {
                "session_id": "s2", "brand_name": "Brand B",
                "category": "spreadsheets", "tool": "generate_spreadsheet",
                "filename": "b.xlsx", "path": "/x/b.xlsx",
                "size_bytes": 200, "generated_at": "2026-05-01T11:00:00+07:00",
            },
        ])
        result = list_artifacts(scope="all")
        assert "a.docx" in result
        assert "b.xlsx" in result
        assert "Found 2 artifact(s)" in result

    def test_category_filter(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        self._seed_manifest(tmp_path, [
            {
                "session_id": "s1", "brand_name": "A",
                "category": "documents", "tool": "generate_document",
                "filename": "a.docx", "path": "/x/a.docx",
                "size_bytes": 100, "generated_at": "2026-05-01T10:00:00+07:00",
            },
            {
                "session_id": "s1", "brand_name": "A",
                "category": "spreadsheets", "tool": "generate_spreadsheet",
                "filename": "b.xlsx", "path": "/x/b.xlsx",
                "size_bytes": 200, "generated_at": "2026-05-01T11:00:00+07:00",
            },
        ])
        result = list_artifacts(scope="all", category="documents")
        assert "a.docx" in result
        assert "b.xlsx" not in result

    def test_current_session_without_session_returns_helpful_message(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        # Seed a manifest so the tool reaches the scope check rather
        # than the empty-manifest early return.
        self._seed_manifest(tmp_path, [
            {
                "session_id": "s1", "brand_name": "A",
                "category": "documents", "tool": "generate_document",
                "filename": "a.docx", "path": "/x/a.docx",
                "size_bytes": 100, "generated_at": "2026-05-01T10:00:00+07:00",
            },
        ])
        result = list_artifacts(scope="current_session")
        # No active session in unit tests → tool tells caller to switch
        # scope rather than silently returning empty.
        assert "No active brand strategy session" in result

    def test_invalid_scope_returns_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        result = list_artifacts(scope="bogus")  # type: ignore[arg-type]
        assert "Invalid scope" in result

    def test_invalid_category_returns_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        result = list_artifacts(scope="all", category="bogus")  # type: ignore[arg-type]
        assert "Invalid category" in result

    def test_current_session_reports_missing_required_categories(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        self._seed_manifest(tmp_path, [
            {
                "session_id": "s1", "brand_name": "A",
                "category": "images", "tool": "generate_image",
                "filename": "a.jpeg", "path": "/x/a.jpeg",
                "size_bytes": 100, "generated_at": "2026-05-01T10:00:00+07:00",
            },
            {
                "session_id": "s1", "brand_name": "A",
                "category": "presentations", "tool": "generate_presentation",
                "filename": "a.pptx", "path": "/x/a.pptx",
                "size_bytes": 200, "generated_at": "2026-05-01T10:01:00+07:00",
            },
        ])
        session = MagicMock(session_id="s1", brand_name="A")

        with patch("core.brand_strategy.session.get_active_session", return_value=session):
            result = list_artifacts(scope="current_session")

        assert "Missing required categories: documents, spreadsheets" in result
        assert "CLOSURE_STATUS: INCOMPLETE" in result

    def test_current_session_reports_complete_required_categories(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRANDMIND_OUTPUT_DIR", str(tmp_path))
        self._seed_manifest(tmp_path, [
            {
                "session_id": "s1", "brand_name": "A",
                "category": category, "tool": "tool",
                "filename": f"{category}.out", "path": f"/x/{category}.out",
                "size_bytes": 100, "generated_at": "2026-05-01T10:00:00+07:00",
            }
            for category in ("images", "documents", "presentations", "spreadsheets")
        ])
        session = MagicMock(session_id="s1", brand_name="A")

        with patch("core.brand_strategy.session.get_active_session", return_value=session):
            result = list_artifacts(scope="current_session")

        assert "Missing required categories: none" in result
        assert "CLOSURE_STATUS: COMPLETE" in result
