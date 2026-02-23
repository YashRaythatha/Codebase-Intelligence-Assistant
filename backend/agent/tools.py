"""Agent tools: list_files, grep, open_file, get_manifest, detect_framework, map_endpoints, find_auth, map_dependencies, trace_flow."""

import json
import re
from pathlib import Path
from typing import Any

from app.settings import get_settings
from agent.guardrails import validate_path_traversal, get_manifest_files


def list_files(repo_id: str, pattern: str = "*") -> list[str]:
    """Return up to 200 rel_paths matching pattern."""
    settings = get_settings()
    base = settings.repos_path / repo_id
    manifest_file = base / "manifest.json"
    if not manifest_file.exists():
        return []
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        repo_root = Path(data.get("repo_root", str(base)))
        files = data.get("files", [])
        out = []
        for f in files[:200]:
            rel = f.replace("\\", "/")
            if pattern and pattern != "*" and pattern not in rel:
                continue
            out.append(rel)
        return out
    except Exception:
        return []


def grep(repo_id: str, pattern: str, glob: str = "**/*") -> list[dict[str, Any]]:
    """Return up to 50 matches with file and line_no."""
    settings = get_settings()
    base = settings.repos_path / repo_id
    manifest_file = base / "manifest.json"
    if not manifest_file.exists():
        return []
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        repo_root = Path(data.get("repo_root", str(base)))
        files = data.get("files", [])[:100]
        out = []
        try:
            rx = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return []
        for rel in files:
            if len(out) >= 50:
                break
            full = repo_root / rel
            if not full.is_file():
                continue
            try:
                text = full.read_text(encoding="utf-8", errors="replace")
                for i, line in enumerate(text.splitlines(), 1):
                    if rx.search(line):
                        out.append({"file": rel.replace("\\", "/"), "line_no": i, "text": line[:200]})
                    if len(out) >= 50:
                        break
            except Exception:
                continue
        return out
    except Exception:
        return []


def open_file(repo_id: str, rel_path: str, start: int | None = None, end: int | None = None, max_lines: int = 200) -> list[dict[str, Any]]:
    """Return numbered lines; path traversal protected."""
    if not validate_path_traversal(rel_path):
        return []
    settings = get_settings()
    base = settings.repos_path / repo_id
    manifest_file = base / "manifest.json"
    if not manifest_file.exists():
        return []
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        repo_root = Path(data.get("repo_root", str(base)))
        full = repo_root / rel_path.replace("\\", "/")
        if not full.is_file():
            return []
        lines = full.read_text(encoding="utf-8", errors="replace").splitlines()
        if start is not None and end is not None:
            start1 = max(0, start - 1)
            end1 = min(len(lines), end)
            slice_lines = lines[start1:end1]
            return [{"no": start1 + i + 1, "text": line} for i, line in enumerate(slice_lines)]
        slice_lines = lines[:max_lines]
        return [{"no": i + 1, "text": line} for i, line in enumerate(slice_lines)]
    except Exception:
        return []


def get_manifest(repo_id: str) -> dict[str, Any]:
    """Return manifest summary."""
    settings = get_settings()
    base = settings.repos_path / repo_id
    manifest_file = base / "manifest.json"
    if not manifest_file.exists():
        return {}
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        return {"repo_id": data.get("repo_id"), "repo_root": data.get("repo_root"), "file_count": len(data.get("files", []))}
    except Exception:
        return {}


def detect_framework(repo_id: str) -> dict[str, Any]:
    """Return detected.json content if present."""
    settings = get_settings()
    path = settings.repos_path / repo_id / "detected.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def map_endpoints(repo_id: str) -> list[dict[str, Any]]:
    """Return endpoint list (placeholder)."""
    return []


def find_auth(repo_id: str) -> list[dict[str, Any]]:
    """Return auth list (placeholder)."""
    return []


def map_dependencies(repo_id: str) -> dict[str, Any]:
    """Return dependency map (placeholder)."""
    return {}


def trace_flow(repo_id: str, handler_hint: str | None = None) -> list[dict[str, Any]]:
    """Best-effort flow steps (placeholder)."""
    return []
