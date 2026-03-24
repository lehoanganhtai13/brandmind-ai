"""Unit tests for Brand Strategy Session (Task 46).

Tests BrandStrategySession persistence, phase advancement,
and brief synchronization.
"""

from __future__ import annotations

import pytest

from core.brand_strategy.session import (
    BrandStrategySession,
    list_sessions,
    load_session,
    save_session,
)


class TestBrandStrategySession:
    """Test session model."""

    def test_default_session(self):
        session = BrandStrategySession()
        assert session.current_phase == "phase_0"
        assert session.scope is None
        assert session.brand_name is None
        assert session.completed_phases == []
        assert session.brief is not None
        assert len(session.session_id) == 8

    def test_advance_phase(self):
        session = BrandStrategySession()
        session.advance_phase("phase_1")
        assert session.current_phase == "phase_1"
        assert "phase_0" in session.completed_phases
        assert session.updated_at != ""

    def test_advance_multiple_phases(self):
        session = BrandStrategySession()
        session.advance_phase("phase_1")
        session.advance_phase("phase_2")
        session.advance_phase("phase_3")
        assert session.current_phase == "phase_3"
        assert session.completed_phases == [
            "phase_0",
            "phase_1",
            "phase_2",
        ]

    def test_save_phase_output(self):
        session = BrandStrategySession()
        session.save_phase_output(
            "phase_0",
            {
                "problem_statement": "Low foot traffic",
                "scope": "NEW_BRAND",
            },
        )
        assert session.brief.phase_0_output["problem_statement"] == "Low foot traffic"
        assert session.updated_at != ""

    def test_sync_metadata_to_brief(self):
        session = BrandStrategySession(
            brand_name="Café X",
            scope="REFRESH",
            budget_tier="growth",
        )
        session.sync_metadata_to_brief()
        assert session.brief.brand_name == "Café X"
        assert session.brief.scope == "REFRESH"
        assert session.brief.budget_tier == "growth"
        assert session.brief.session_id == session.session_id

    def test_sync_metadata_handles_none(self):
        session = BrandStrategySession()
        session.sync_metadata_to_brief()
        assert session.brief.brand_name == ""
        assert session.brief.scope == ""


class TestSessionPersistence:
    """Test save/load/list."""

    def test_save_and_load(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path)

        session = BrandStrategySession(
            brand_name="Test Café",
            scope="NEW_BRAND",
            current_phase="phase_1",
            budget_tier="starter",
        )
        filepath = save_session(session)
        assert filepath.exists()

        loaded = load_session(session.session_id)
        assert loaded is not None
        assert loaded.brand_name == "Test Café"
        assert loaded.current_phase == "phase_1"
        assert loaded.scope == "NEW_BRAND"
        assert loaded.budget_tier == "starter"
        assert loaded.session_id == session.session_id

    def test_load_nonexistent_returns_none(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path)

        result = load_session("nonexistent_id")
        assert result is None

    def test_save_creates_directory(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        nested = tmp_path / "nested" / "dir"
        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", nested)

        session = BrandStrategySession()
        filepath = save_session(session)
        assert filepath.exists()
        assert nested.exists()

    def test_list_sessions(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path)

        # Save 3 sessions
        for name in ["Brand A", "Brand B", "Brand C"]:
            s = BrandStrategySession(brand_name=name)
            save_session(s)

        sessions = list_sessions()
        assert len(sessions) == 3
        names = {s["brand_name"] for s in sessions}
        assert names == {"Brand A", "Brand B", "Brand C"}

    def test_list_sessions_empty_dir(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path)

        sessions = list_sessions()
        assert sessions == []

    def test_save_updates_timestamp(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path)

        session = BrandStrategySession()
        assert session.updated_at == ""
        save_session(session)
        assert session.updated_at != ""

    def test_roundtrip_with_brief_data(self, tmp_path, monkeypatch):
        import core.brand_strategy.session as sess_mod

        monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path)

        session = BrandStrategySession(brand_name="X")
        session.save_phase_output("phase_0", {"test_key": "test_value"})
        save_session(session)

        loaded = load_session(session.session_id)
        assert loaded is not None
        assert loaded.brief.phase_0_output["test_key"] == "test_value"
