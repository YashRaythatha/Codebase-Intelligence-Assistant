"""Plugin-style auth detection: plugins + auth_generic. Return type, file, symbol, description, confidence, evidence."""

from typing import Any


def find_auth(repo_id: str) -> list[dict[str, Any]]:
    """Return list of {type, file, symbol, description, confidence, evidence} with file/line."""
    return []
