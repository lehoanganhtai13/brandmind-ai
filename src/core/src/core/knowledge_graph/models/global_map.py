"""Pydantic models for global_map.json structure."""

import json
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field


class SectionNode(BaseModel):
    """Represents a section/chapter in the document hierarchy."""

    title: str = Field(description="Section title")
    level: int = Field(ge=1, le=5, description="Heading level (1-5)")
    start_page_id: str = Field(
        description="Page file where section starts (e.g., 'page_5.md')"
    )
    end_page_id: str = Field(description="Page file where section ends")
    start_line_index: int = Field(
        ge=0, description="0-indexed line number in start_page_id"
    )
    summary_context: str = Field(
        description="Brief summary of section content (2-3 sentences)"
    )
    children: List["SectionNode"] = Field(
        default_factory=list, description="Nested subsections"
    )


class GlobalMap(BaseModel):
    """Root model for global_map.json."""

    structure: List[SectionNode] = Field(description="Top-level sections/chapters")

    def to_json_file(self, filepath: str) -> None:
        """Save to JSON file with pretty formatting.

        Args:
            filepath: Path to save JSON file
        """
        Path(filepath).write_text(
            json.dumps(self.model_dump(), indent=2, ensure_ascii=False)
        )
