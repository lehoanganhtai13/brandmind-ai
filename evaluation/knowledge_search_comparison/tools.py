"""External tool clients for the knowledge-search comparison harness."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from pydantic import BaseModel, Field

from evaluation.knowledge_search_comparison.hipporag_worker import (
    DEFAULT_SAVE_DIR,
    HippoRagWorkerResponse,
)
from evaluation.knowledge_search_comparison.source_mapping import (
    DEFAULT_CORPUS_PATH,
    DEFAULT_METADATA_PATH,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class HippoRagSubprocessConfig(BaseModel):
    """Configuration for calling HippoRAG through its isolated conda env."""

    conda_env: str = "brandmind-hipporag"
    save_dir: Path = DEFAULT_SAVE_DIR
    corpus_path: Path = DEFAULT_CORPUS_PATH
    metadata_path: Path = DEFAULT_METADATA_PATH
    timeout_seconds: int = Field(default=180, gt=0)


class HippoRagSubprocessSearchTool:
    """Async search adapter that calls ``hipporag_worker`` via conda."""

    def __init__(self, config: HippoRagSubprocessConfig | None = None) -> None:
        """Initialize the subprocess-backed HippoRAG search tool."""

        self.config = config or HippoRagSubprocessConfig()

    async def __call__(self, *, query: str, top_k: int) -> str:
        """Return formatted HippoRAG native retriever output for an agent."""

        response = await self.search(query=query, top_k=top_k)
        return format_hipporag_response(response)

    async def search(self, *, query: str, top_k: int) -> HippoRagWorkerResponse:
        """Run HippoRAG retrieve in the configured conda environment."""

        command = [
            "conda",
            "run",
            "-n",
            self.config.conda_env,
            "python",
            "-m",
            "evaluation.knowledge_search_comparison.hipporag_worker",
            "retrieve",
            "--query",
            query,
            "--top-k",
            str(top_k),
            "--save-dir",
            str(self.config.save_dir),
            "--corpus-path",
            str(self.config.corpus_path),
            "--metadata-path",
            str(self.config.metadata_path),
        ]
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{PROJECT_ROOT}:{existing_pythonpath}"
            if existing_pythonpath
            else str(PROJECT_ROOT)
        )
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=PROJECT_ROOT,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout_seconds,
            )
        except TimeoutError as exc:
            process.kill()
            await process.wait()
            raise TimeoutError("HippoRAG retrieve timed out.") from exc

        if process.returncode != 0:
            stderr_text = stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"HippoRAG worker failed: {stderr_text}")

        return parse_hipporag_worker_stdout(stdout)


def parse_hipporag_worker_stdout(stdout: bytes) -> HippoRagWorkerResponse:
    """Parse the final JSON object emitted by the HippoRAG worker."""

    text = stdout.decode("utf-8", errors="replace").strip()
    if not text:
        raise ValueError("HippoRAG worker returned empty stdout.")

    json_line = text.splitlines()[-1]
    payload = json.loads(json_line)
    if not isinstance(payload, dict):
        raise ValueError("Expected HippoRAG worker response object.")
    return HippoRagWorkerResponse(**payload)


def format_hipporag_response(response: HippoRagWorkerResponse) -> str:
    """Format native HippoRAG passages for the answer-flow agent."""

    if not response.passages:
        return "No HippoRAG results found."

    lines: list[str] = []
    for passage in response.passages:
        source_ids = ", ".join(passage.source_ids) or "unmapped"
        score = "" if passage.score is None else f" | Score: {passage.score:.4f}"
        lines.append(f"[{passage.rank}] Source IDs: {source_ids}{score}")
        lines.append(passage.text)
        lines.append("")
    return "\n".join(lines).strip()


def script_entrypoint() -> int:
    """Small helper for manual smoke tests of the subprocess parser."""

    response = parse_hipporag_worker_stdout(sys.stdin.buffer.read())
    print(format_hipporag_response(response))
    return 0
