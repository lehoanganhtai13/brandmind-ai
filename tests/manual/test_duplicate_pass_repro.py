"""Manual end-to-end repro for the duplicate-pass bug (turn-1 advance flow).

This script is **manual** — it requires:

* A running ``brandmind serve`` server on the configured host/port
  (default 0.0.0.0:8000).
* A valid ``GEMINI_API_KEY`` in ``environments/.env``.
* The duplicate-pass-resurrection memo
  (``project_duplicate_pass_resurrection_2026_05_03.md``) for context
  on what is being measured.

What it does
------------

1. Opens a brand-strategy session via the CLI client.
2. Sends a single canonical message that mirrors the Linh Phase A iso
   trigger (premium F&B SME repositioning + skip-dispatch hint +
   "đẩy nhanh tới Phase 5").
3. Streams the first turn's text events and counts the number of
   distinct user-facing text passes by detecting paragraph-break
   boundaries that are followed by a Vietnamese-style greeting or a
   phase-heading prefix.
4. Prints PASS_COUNT alongside the raw text. Pass criterion:
   PASS_COUNT == 1 in the fixed variant, PASS_COUNT >= 2 in the
   control (current production).

Variants
--------

The script reads an ``EXPERIMENT`` environment variable selecting the
variant under test:

* ``EXPERIMENT=control`` — current production stack. Expect Pass 2 in
  ≥80 % of runs.
* ``EXPERIMENT=fix-content-check-silent`` — the operator must, before
  running this script, manually edit
  ``src/core/src/core/brand_strategy/content_check.py::_rejection``
  so the ToolMessage instructs the agent to update the workspace
  silently when the workspace already contains the deliverable, and
  to NOT re-emit user-facing text. Expect 0/N runs to surface Pass 2.

The script does not modify production code itself — variant selection
is the operator's responsibility, gated by manual diff review.

Usage
-----

    EXPERIMENT=control N_RUNS=5 python tests/manual/test_duplicate_pass_repro.py
    EXPERIMENT=fix-content-check-silent N_RUNS=5 \\
        python tests/manual/test_duplicate_pass_repro.py

The output is JSONL with one record per run, plus an aggregate summary
on stdout's last line.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import uuid
from dataclasses import dataclass
from typing import Iterable

# This import path matches the CLI client used in src/cli/inference.py.
# At scaffold time the import is intentionally not exercised — the
# next session's operator will adjust it to the live module path if
# the package layout has shifted.
try:
    from cli.client import BrandMindClient
except ImportError as exc:  # pragma: no cover - scaffold tolerance
    BrandMindClient = None  # type: ignore[assignment]
    _IMPORT_ERR: Exception | None = exc
else:
    _IMPORT_ERR = None


CANONICAL_MESSAGE = (
    "Xin chào, em là marketing executive Chuyện Ba Bữa Signature "
    "(premium spinoff từ Chuyện Ba Bữa, khai trương 6 tháng tại Quận 3 "
    "gần Lê Quý Đôn). Vấn đề: T2-T5 chỉ 40% công suất, cuối tuần đầy. "
    "Mục tiêu repositioning hướng business lunch + dinner cho doanh "
    "nhân Quận 3. Ngân sách Growth 50-80M/tháng. Em xin tự cung cấp "
    "thông tin nhanh, mong anh dùng KG có sẵn (skip dispatch "
    "market-research/social-analysis vì browser-use đang bị broken), "
    "đẩy nhanh tới Phase 5 production artifacts."
)


# Markers that begin a fresh user-facing pass. Tuned against the
# Phase A iso v2 turn-01 transcript: Pass 1 begins with "Chào bạn",
# Pass 2 begins with "Chào bạn" again after a tool-call gap.
_PASS_START_MARKERS = (
    re.compile(r"\bChào bạn\b", re.IGNORECASE),
    re.compile(r"\bXin chào\b", re.IGNORECASE),
    re.compile(r"^### Phase \d", re.MULTILINE),
)


@dataclass
class RunRecord:
    """One run of the canonical Linh trigger.

    Attributes:
        run_index: 0-based run number within the batch.
        experiment: The label of the variant under test.
        agent_text: Concatenated user-facing text from this turn.
        pass_count: Number of distinct passes detected by the marker
            heuristic. ``1`` indicates clean per-turn discipline;
            ``>=2`` indicates the duplicate-pass bug fired.
    """

    run_index: int
    experiment: str
    agent_text: str
    pass_count: int


def count_passes(text: str) -> int:
    """Return the number of distinct user-facing passes in ``text``.

    The heuristic counts how many marker phrases appear in the
    transcript. The first marker counts as the start of Pass 1; each
    subsequent marker counts as a new pass. The function is
    deliberately conservative: a single marker present once returns
    ``1`` so genuinely disciplined turns are not flagged.

    Args:
        text: Concatenated agent text from a single turn.

    Returns:
        The number of distinct passes detected. ``0`` only when the
        text is empty.
    """
    if not text.strip():
        return 0

    marker_hits = 0
    for marker in _PASS_START_MARKERS:
        marker_hits += len(marker.findall(text))

    return max(marker_hits, 1)


async def run_one(experiment: str, run_index: int) -> RunRecord:
    """Execute a single repro run.

    The function builds a fresh session, sends the canonical message,
    accumulates the streamed text, and returns a :class:`RunRecord`.
    Network and server failures bubble up so the caller can decide
    whether to retry.

    Args:
        experiment: The variant label (``"control"`` or
            ``"fix-content-check-silent"``).
        run_index: The 0-based index of this run within the batch.

    Returns:
        A :class:`RunRecord` describing what the agent produced.

    Raises:
        ImportError: When ``cli.client.BrandMindClient`` cannot be
            imported. The scaffold leaves this as a manual fixup point
            for the next session.
        RuntimeError: When the server is unreachable or returns a
            non-streaming response.
    """
    if BrandMindClient is None:
        raise ImportError(
            "BrandMindClient could not be imported at scaffold time. "
            f"Original error: {_IMPORT_ERR!r}. Adjust the import path "
            "in this manual repro before running the experiment."
        )

    client = BrandMindClient()  # type: ignore[call-arg]
    session_id = await client.create_session(  # type: ignore[attr-defined]
        mode="BRAND_STRATEGY",
        session_label=f"dup-pass-{experiment}-{uuid.uuid4().hex[:8]}",
    )

    accumulated: list[str] = []
    async for event in client.stream_message(  # type: ignore[attr-defined]
        session_id=session_id, content=CANONICAL_MESSAGE
    ):
        if getattr(event, "type", "") == "streaming_token":
            token = getattr(event, "token", "")
            if token:
                accumulated.append(token)

    text = "".join(accumulated)
    return RunRecord(
        run_index=run_index,
        experiment=experiment,
        agent_text=text,
        pass_count=count_passes(text),
    )


async def run_batch(experiment: str, n_runs: int) -> Iterable[RunRecord]:
    """Run ``n_runs`` repro runs and yield records as they finish.

    Runs are executed sequentially because the server holds a global
    ``_brand_strategy_lock`` (see ``server/services/session_manager``)
    that serializes brand-strategy sessions; parallel runs would queue
    behind the lock and not provide additional signal.

    Args:
        experiment: The variant label propagated to each
            :class:`RunRecord`.
        n_runs: Number of runs to execute.

    Yields:
        Run records in completion order.
    """
    for i in range(n_runs):
        yield await run_one(experiment, i)


def main() -> int:
    """Entry point for the manual repro.

    Reads ``EXPERIMENT`` and ``N_RUNS`` from the environment, runs
    the batch, and prints JSONL records to stdout followed by an
    aggregate summary line. Exit code is ``0`` on success and ``1``
    on import failure.

    Returns:
        Process exit code.
    """
    experiment = os.environ.get("EXPERIMENT", "control")
    n_runs = int(os.environ.get("N_RUNS", "5"))

    async def _drive() -> list[RunRecord]:
        records: list[RunRecord] = []
        async for rec in run_batch(experiment, n_runs):
            records.append(rec)
            print(
                json.dumps(
                    {
                        "run_index": rec.run_index,
                        "experiment": rec.experiment,
                        "pass_count": rec.pass_count,
                        "agent_chars": len(rec.agent_text),
                    }
                ),
                flush=True,
            )
        return records

    try:
        records = asyncio.run(_drive())
    except ImportError as exc:
        print(f"SETUP_ERROR: {exc}", file=sys.stderr)
        return 1

    duplicate_runs = [r for r in records if r.pass_count >= 2]
    summary = {
        "experiment": experiment,
        "n_runs": n_runs,
        "duplicate_pass_count": len(duplicate_runs),
        "duplicate_pass_rate": len(duplicate_runs) / max(n_runs, 1),
    }
    print(json.dumps({"summary": summary}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
