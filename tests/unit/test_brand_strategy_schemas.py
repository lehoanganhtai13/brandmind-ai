"""Unit tests for Brand Strategy Phase Output Schemas (Tasks 43-45).

Tests Phase1Output through Phase5Output Pydantic models.
"""

from __future__ import annotations

import pytest

from core.brand_strategy.schemas import (
    Phase1Output,
    Phase2Output,
    Phase3Output,
    Phase4Output,
    Phase5Output,
)


class TestPhase1Output:
    """Test Phase 1 Market Intelligence schema."""

    def test_empty_defaults(self):
        output = Phase1Output()
        assert output.market_overview is not None
        assert output.competitive_landscape is not None

    def test_serialization_roundtrip(self):
        output = Phase1Output()
        json_str = output.model_dump_json()
        loaded = Phase1Output.model_validate_json(json_str)
        assert loaded == output


class TestPhase2Output:
    """Test Phase 2 Brand Positioning schema."""

    def test_empty_defaults(self):
        output = Phase2Output()
        assert output.positioning is not None

    def test_serialization_roundtrip(self):
        output = Phase2Output()
        json_str = output.model_dump_json()
        loaded = Phase2Output.model_validate_json(json_str)
        assert loaded == output


class TestPhase3Output:
    """Test Phase 3 Brand Identity schema."""

    def test_empty_defaults(self):
        output = Phase3Output()
        assert output.brand_personality is not None
        assert output.brand_voice is not None

    def test_serialization_roundtrip(self):
        output = Phase3Output()
        json_str = output.model_dump_json()
        loaded = Phase3Output.model_validate_json(json_str)
        assert loaded == output


class TestPhase4Output:
    """Test Phase 4 Communication Framework schema."""

    def test_empty_defaults(self):
        output = Phase4Output()
        assert output.messaging_hierarchy is not None

    def test_serialization_roundtrip(self):
        output = Phase4Output()
        json_str = output.model_dump_json()
        loaded = Phase4Output.model_validate_json(json_str)
        assert loaded == output


class TestPhase5Output:
    """Test Phase 5 Strategy Plan schema."""

    def test_empty_defaults(self):
        output = Phase5Output()
        assert output.brand_strategy_document is not None

    def test_serialization_roundtrip(self):
        output = Phase5Output()
        json_str = output.model_dump_json()
        loaded = Phase5Output.model_validate_json(json_str)
        assert loaded == output
