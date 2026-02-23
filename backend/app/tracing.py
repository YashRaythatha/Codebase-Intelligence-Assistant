"""JSON tracing per request: trace_id, steps, usage, save to backend/data/traces/{trace_id}.json."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.settings import get_settings


class Trace:
    """Trace object: start, add_step, set_usage, end, save to traces/{trace_id}.json."""

    def __init__(self) -> None:
        self.trace_id = str(uuid.uuid4())
        self.run_id: str | None = None
        self.repo_id: str | None = None
        self.conversation_id: str | None = None
        self.question: str | None = None
        self.endpoint_name: str | None = None
        self.steps: list[dict[str, Any]] = []
        self.usage: dict[str, Any] | None = None
        self.answer_summary: str | None = None
        self.started_at: str | None = None
        self.ended_at: str | None = None

    def start(
        self,
        run_id: str,
        repo_id: str | None = None,
        conversation_id: str | None = None,
        question: str | None = None,
        endpoint_name: str | None = None,
    ) -> None:
        self.run_id = run_id
        self.repo_id = repo_id
        self.conversation_id = conversation_id
        self.question = question
        self.endpoint_name = endpoint_name
        self.started_at = datetime.now(tz=timezone.utc).isoformat()

    def add_step(self, step_type: str, payload: dict[str, Any], latency_ms: float | None = None) -> None:
        step: dict[str, Any] = {"step_type": step_type, "payload": payload}
        if latency_ms is not None:
            step["latency_ms"] = latency_ms
        self.steps.append(step)

    def set_usage(
        self,
        model: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> None:
        self.usage = {
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

    def end(self, answer_summary: str | None = None) -> None:
        self.answer_summary = answer_summary
        self.ended_at = datetime.now(tz=timezone.utc).isoformat()

    def save(self) -> None:
        settings = get_settings()
        trace_path = settings.trace_path
        trace_path.mkdir(parents=True, exist_ok=True)
        path = trace_path / f"{self.trace_id}.json"
        obj = {
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "repo_id": self.repo_id,
            "conversation_id": self.conversation_id,
            "question": self.question,
            "endpoint_name": self.endpoint_name,
            "steps": self.steps,
            "usage": self.usage,
            "answer_summary": self.answer_summary,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }
        path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
