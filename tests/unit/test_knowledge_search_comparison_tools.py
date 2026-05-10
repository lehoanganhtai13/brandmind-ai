"""Unit tests for external comparison tool adapters."""

from __future__ import annotations

import os

from evaluation.knowledge_search_comparison.tools import (
    PROJECT_ROOT,
    build_conda_subprocess_env,
)


def test_build_conda_subprocess_env_removes_uv_and_conda_activation() -> None:
    """Nested conda workers should not inherit uv or active conda state."""

    env = build_conda_subprocess_env(
        {
            "PATH": "/bin",
            "PYTHONPATH": "/existing",
            "VIRTUAL_ENV": "/project/.venv",
            "UV_RUN_RECURSION_DEPTH": "1",
            "CONDA_PREFIX": "/Users/example/miniconda3",
            "CONDA_DEFAULT_ENV": "base",
        }
    )

    assert env["PATH"] == "/bin"
    assert "VIRTUAL_ENV" not in env
    assert "UV_RUN_RECURSION_DEPTH" not in env
    assert "CONDA_PREFIX" not in env
    assert "CONDA_DEFAULT_ENV" not in env
    assert env["PYTHONPATH"].split(os.pathsep)[0] == str(PROJECT_ROOT)
    assert env["PYTHONPATH"].endswith("/existing")
