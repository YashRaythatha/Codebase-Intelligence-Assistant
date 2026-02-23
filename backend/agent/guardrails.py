"""Path traversal protection; validate cited files exist in manifest; append note if unknown file cited."""

import json
from pathlib import Path

from app.settings import get_settings


def validate_path_traversal(rel_path: str) -> bool:
    """Return False if path attempts traversal or is invalid."""
    clean = rel_path.replace("\\", "/").lstrip("/")
    if ".." in clean or clean.startswith("/"):
        return False
    return True


def get_manifest_files(repo_id: str) -> set[str]:
    """Return set of relative file paths in manifest."""
    settings = get_settings()
    base = settings.repos_path / repo_id
    manifest_file = base / "manifest.json"
    if not manifest_file.exists():
        return set()
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        files = data.get("files", [])
        return set(f.replace("\\", "/") for f in files)
    except Exception:
        return set()


def validate_cited_file(repo_id: str, rel_path: str) -> bool:
    """Return True if rel_path exists in manifest."""
    allowed = get_manifest_files(repo_id)
    norm = rel_path.replace("\\", "/").lstrip("/")
    return norm in allowed or any(f.endswith(norm) for f in allowed)
