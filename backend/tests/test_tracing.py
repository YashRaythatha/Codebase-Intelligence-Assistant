"""Confirm a trace file is created when Trace.save() is called."""

from pathlib import Path

import pytest

from app.settings import get_settings
from app.tracing import Trace


def test_trace_save_creates_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.tracing.get_settings", lambda: type("S", (), {"trace_path": tmp_path})())
    trace = Trace()
    trace.start(run_id="run-1", repo_id="repo-1", question="q?", endpoint_name="ask")
    trace.add_step("test", {"foo": "bar"}, latency_ms=10.0)
    trace.end(answer_summary="ok")
    trace.save()
    path = tmp_path / f"{trace.trace_id}.json"
    assert path.exists()
    data = path.read_text(encoding="utf-8")
    assert "run-1" in data
    assert "run_id" in data
    assert "steps" in data
