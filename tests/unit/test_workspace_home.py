"""Regression tests for BrandMind workspace root selection."""

from pathlib import Path

import shared.workspace as workspace_mod
from shared.workspace import _resolve_brandmind_home


def test_brandmind_home_defaults_to_user_directory(monkeypatch) -> None:
    """Production sessions keep using the user's durable BrandMind home."""
    monkeypatch.delenv("BRANDMIND_HOME", raising=False)

    assert _resolve_brandmind_home() == Path.home() / ".brandmind"


def test_brandmind_home_can_be_isolated_for_eval_runs(monkeypatch, tmp_path) -> None:
    """Eval harnesses can isolate profile and project state per run."""
    isolated_home = tmp_path / ".brandmind-eval"
    monkeypatch.setenv("BRANDMIND_HOME", str(isolated_home))

    assert _resolve_brandmind_home() == isolated_home


def test_project_workspace_bootstraps_editable_files(monkeypatch, tmp_path) -> None:
    """Session setup creates the files the agent later edits in place."""
    monkeypatch.setattr(workspace_mod, "BRANDMIND_HOME", tmp_path)

    workspace_dir, user_dir = workspace_mod.ensure_project_workspace(
        "abc123",
        "Cafe Saigon",
    )

    assert workspace_dir is not None
    assert user_dir is not None
    for filename in ("brand_brief.md", "working_notes.md", "quality_gates.md"):
        assert (workspace_dir / filename).is_file()
    assert (user_dir / "profile.md").is_file()
