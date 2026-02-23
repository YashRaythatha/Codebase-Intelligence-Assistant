"""Best-effort flow tracer: given handler hint or endpoint, follow imports and calls. Return ordered steps with citations and limitations."""

from typing import Any


def trace_flow(repo_id: str, handler_hint: str | None = None) -> list[dict[str, Any]]:
    """Return ordered steps with file/line citations and limitations list."""
    return []
