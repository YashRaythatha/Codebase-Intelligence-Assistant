"""Load or clone a repo and return repo_id and manifest path."""

import hashlib
from pathlib import Path

from app.logging_config import get_logger
from app.settings import get_settings

logger = get_logger(__name__)


def _repo_id_from_input(source: str) -> str:
    """Stable repo ID from GitHub URL or local path."""
    normalized = source.strip().lower().replace("\\", "/")
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def load_repo(source: str) -> tuple[str, Path]:
    """
    Load repo from GitHub URL or local path.
    Returns (repo_id, path_to_repo_root).
    For local path, path must exist; we don't copy.
    """
    settings = get_settings()
    repo_id = _repo_id_from_input(source)
    repos_base = settings.repos_path

    if source.startswith("http://") or source.startswith("https://"):
        dest = repos_base / repo_id
        dest.mkdir(parents=True, exist_ok=True)
        import subprocess
        if (dest / ".git").exists():
            subprocess.run(["git", "pull"], cwd=dest, capture_output=True)
        else:
            subprocess.run(["git", "clone", "--depth", "1", source, str(dest)], check=True, capture_output=True)
        return repo_id, dest

    # Local path
    p = Path(source).resolve()
    if not p.is_dir():
        raise FileNotFoundError(f"Local path not found: {source}")
    return repo_id, p
