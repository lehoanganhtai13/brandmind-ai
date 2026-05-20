"""Unit tests for BrandMind server lifecycle CLI routing."""

from __future__ import annotations

import pytest

from cli import inference as cli_inference


def test_serve_health_url_uses_loopback_for_wildcard_bind() -> None:
    url = cli_inference._serve_health_url("0.0.0.0", 8000)

    assert url == "http://127.0.0.1:8000/api/v1/health"


def test_run_serve_command_defaults_to_foreground(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        cli_inference, "_run_uvicorn_server", lambda: calls.append("run")
    )

    cli_inference._run_serve_command([])

    assert calls == ["run"]


def test_run_serve_command_can_start_detached(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        cli_inference,
        "_start_detached_server",
        lambda: calls.append("detach"),
    )

    cli_inference._run_serve_command(["--detach"])

    assert calls == ["detach"]


def test_run_serve_command_can_stop_detached(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        cli_inference,
        "_stop_detached_server",
        lambda: calls.append("stop"),
    )

    cli_inference._run_serve_command(["--stop"])

    assert calls == ["stop"]


def test_run_serve_command_can_print_status(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        cli_inference,
        "_print_detached_status",
        lambda: calls.append("status"),
    )

    cli_inference._run_serve_command(["--status"])

    assert calls == ["status"]


def test_run_serve_command_can_print_logs(monkeypatch) -> None:
    calls: list[tuple[bool, int]] = []

    def fake_print_logs(*, follow: bool, tail_lines: int) -> None:
        calls.append((follow, tail_lines))

    monkeypatch.setattr(cli_inference, "_print_server_logs", fake_print_logs)

    cli_inference._run_serve_command(["--logs", "--tail", "25"])

    assert calls == [(False, 25)]


def test_run_serve_command_can_follow_logs(monkeypatch) -> None:
    calls: list[tuple[bool, int]] = []

    def fake_print_logs(*, follow: bool, tail_lines: int) -> None:
        calls.append((follow, tail_lines))

    monkeypatch.setattr(cli_inference, "_print_server_logs", fake_print_logs)

    cli_inference._run_serve_command(["--logs", "--follow", "--tail", "5"])

    assert calls == [(True, 5)]


def test_run_serve_command_rejects_follow_without_logs() -> None:
    with pytest.raises(SystemExit):
        cli_inference._run_serve_command(["--follow"])


def test_run_serve_command_rejects_negative_tail() -> None:
    with pytest.raises(SystemExit):
        cli_inference._run_serve_command(["--logs", "--tail", "-1"])


def test_read_log_tail_returns_requested_lines(tmp_path) -> None:
    log_path = tmp_path / "brandmind-serve.log"
    log_path.write_text("a\nb\nc\n", encoding="utf-8")

    assert cli_inference._read_log_tail(log_path, 2) == ["b\n", "c\n"]


def test_run_serve_command_rejects_multiple_lifecycle_actions() -> None:
    with pytest.raises(SystemExit):
        cli_inference._run_serve_command(["--detach", "--status"])
