"""Eval session helper — captures full transcript during interactive eval.

Usage (from Claude Code or Python):
    from evaluation.eval_session import EvalSession

    session = EvalSession(persona="linh", run=2)
    session.start()  # creates server session

    # For each turn:
    response = session.send("user message here")
    print(response)  # full agent response

    session.save()  # saves transcript.json + metadata.json
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from httpx_sse import connect_sse


class EvalSession:
    """Interactive eval session with full transcript capture."""

    def __init__(
        self,
        persona: str,
        run: int,
        base_url: str = "http://localhost:8000/api/v1",
        output_dir: str | None = None,
        timeout: int = 600,
    ):
        self.persona = persona
        self.run = run
        self.base_url = base_url
        self.timeout = timeout
        self.session_id: str | None = None
        self.turns: list[dict[str, Any]] = []
        self.turn_count = 0
        self._start_time: float | None = None

        date = datetime.now().strftime("%Y%m%d")
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(
                f"brandmind-output/eval/brandmind_{persona}_r{run}_{date}"
            )

    def start(self) -> str:
        """Create a new brand-strategy session on the server."""
        resp = httpx.post(
            f"{self.base_url}/sessions",
            json={"mode": "brand-strategy"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self.session_id = data["session_id"]
        self._start_time = time.time()
        print(f"Session created: {self.session_id}")
        return self.session_id

    def send(self, user_message: str) -> str:
        """Send a message and capture the FULL agent response.

        Returns the complete agent response text.
        Also captures tools used and timing metadata.
        """
        if not self.session_id:
            raise RuntimeError("Call start() first")

        self.turn_count += 1
        turn_start = time.time()

        # Capture full response via SSE streaming
        agent_text = ""
        tools_used: list[str] = []

        with httpx.Client(timeout=self.timeout) as client:
            with connect_sse(
                client,
                "POST",
                f"{self.base_url}/sessions/{self.session_id}/message",
                params={"stream": "true"},
                json={"content": user_message},
            ) as sse:
                for event in sse.iter_sse():
                    if event.event == "streaming_token":
                        data = json.loads(event.data)
                        agent_text += data.get("token", "")
                    elif event.event == "tool_call":
                        data = json.loads(event.data)
                        tools_used.append(data.get("tool_name", ""))
                    elif event.event == "done":
                        break
                    elif event.event == "error":
                        err = event.data
                        print(f"  [ERROR] {err}")
                        break

        elapsed = time.time() - turn_start

        # Record turn
        turn_data = {
            "turn": self.turn_count,
            "user": user_message,
            "agent": agent_text,
            "user_chars": len(user_message),
            "agent_chars": len(agent_text),
            "tools_used": tools_used,
            "elapsed_seconds": round(elapsed, 1),
        }
        self.turns.append(turn_data)

        print(
            f"  Turn {self.turn_count}: "
            f"{len(agent_text)} chars, "
            f"{len(tools_used)} tools, "
            f"{elapsed:.1f}s"
        )

        return agent_text

    def get_session_state(self) -> dict[str, Any]:
        """Get current session state from server."""
        if not self.session_id:
            return {}
        resp = httpx.get(
            f"{self.base_url}/sessions/{self.session_id}",
            timeout=10,
        )
        return resp.json()

    def save(self) -> Path:
        """Save transcript and metadata to output directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Get final session state
        state = self.get_session_state()
        metadata = state.get("metadata", {})

        # Save transcript (r1-compatible format)
        transcript = {
            "persona": self.persona,
            "system": "brandmind",
            "run": self.run,
            "date": datetime.now().strftime("%Y%m%d"),
            "turns": [
                {
                    "turn": t["turn"],
                    "user": t["user"],
                    "agent": t["agent"],
                }
                for t in self.turns
            ],
        }
        transcript_path = self.output_dir / "transcript.json"
        transcript_path.write_text(
            json.dumps(transcript, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Save metadata
        meta = {
            "system": "brandmind",
            "persona": self.persona,
            "run": self.run,
            "date": datetime.now().strftime("%Y%m%d"),
            "total_turns": self.turn_count,
            "session_id": self.session_id,
            "session_metadata": metadata,
            "turn_stats": [
                {
                    "turn": t["turn"],
                    "user_chars": t["user_chars"],
                    "agent_chars": t["agent_chars"],
                    "tools_used": t["tools_used"],
                    "elapsed_seconds": t["elapsed_seconds"],
                }
                for t in self.turns
            ],
            "total_user_chars": sum(t["user_chars"] for t in self.turns),
            "total_agent_chars": sum(t["agent_chars"] for t in self.turns),
            "reproducibility": {
                "agent_model": "gemini-3-flash-preview (thinking=high)",
                "simulated_user": "claude-opus-4-6 (direct interaction)",
                "server_version": "brandmind-ai 0.1.0",
                "interaction_method": "HTTP API (streaming SSE) via localhost:8000",
            },
        }
        meta_path = self.output_dir / "metadata.json"
        meta_path.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        total_chars = meta["total_user_chars"] + meta["total_agent_chars"]
        print(
            f"\nSaved to {self.output_dir}/"
            f"\n  transcript.json: {self.turn_count} turns, "
            f"{total_chars} chars"
            f"\n  metadata.json"
        )
        return self.output_dir
