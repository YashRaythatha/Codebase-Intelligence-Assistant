"""Scan repo for files; return FileRecord list. Exclude dirs and filter by extension."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone

EXTENSIONS = {".py", ".js", ".ts", ".java", ".md", ".yml", ".yaml", ".json", ".toml", ".sql", ".txt", ".tsx", ".jsx", ".go", ".rs", ".rb"}
SKIP_DIRS = {".git", "node_modules", "dist", "build", "target", "venv", ".venv", ".next", "coverage", "__pycache__"}


@dataclass
class FileRecord:
    abs_path: Path
    rel_path: Path
    ext: str
    size_bytes: int
    mtime_epoch: float
    sha256: str


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except Exception:
        pass
    return h.hexdigest()


def scan(repo_root: Path) -> list[FileRecord]:
    """Return list of FileRecord for allowed extensions under repo_root, excluding SKIP_DIRS."""
    out: list[FileRecord] = []
    repo_root = repo_root.resolve()
    for f in repo_root.rglob("*"):
        if not f.is_file():
            continue
        try:
            rel = f.relative_to(repo_root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if rel.suffix.lower() not in EXTENSIONS:
            continue
        try:
            stat = f.stat()
            sha = _file_sha256(f)
        except Exception:
            continue
        out.append(FileRecord(
            abs_path=f,
            rel_path=rel,
            ext=rel.suffix.lower(),
            size_bytes=stat.st_size,
            mtime_epoch=stat.st_mtime,
            sha256=sha,
        ))
    return sorted(out, key=lambda r: str(r.rel_path))


def write_manifest(repo_id: str, repo_root: Path, files: list[FileRecord], manifest_dir: Path) -> None:
    """Write manifest.json at manifest_dir/manifest.json."""
    manifest_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    files_payload = [
        {
            "rel_path": str(r.rel_path).replace("\\", "/"),
            "ext": r.ext,
            "size_bytes": r.size_bytes,
            "mtime_epoch": r.mtime_epoch,
            "sha256": r.sha256,
        }
        for r in files
    ]
    manifest = {
        "repo_id": repo_id,
        "repo_root": str(repo_root),
        "created_at": now,
        "files": files_payload,
    }
    (manifest_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
