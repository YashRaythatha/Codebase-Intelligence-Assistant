"""Plugin-style endpoint mapping: framework plugins + endpoint_generic. Return method, path, file, handler, confidence, evidence."""

from typing import Any


def map_endpoints(repo_id: str) -> list[dict[str, Any]]:
    """Return list of {method, path, file, handler, confidence, evidence} with file/line citations."""
    return []
