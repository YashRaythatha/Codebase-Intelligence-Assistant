"""Ingest repo: GitHub URL clone or local path. Returns (repo_id, repo_root)."""

from ingest.loader import load_repo


def ingest_repo(
    repo_url: str | None = None,
    local_path: str | None = None,
    branch: str | None = None,
) -> tuple[str, str]:
    """
    If repo_url: clone into data/repos/{repo_id}. If local_path: use as-is.
    Returns (repo_id, repo_root_absolute_path).
    """
    source = repo_url or local_path or ""
    if not source:
        raise ValueError("Provide repo_url or local_path")
    repo_id, repo_root = load_repo(source)
    return repo_id, str(repo_root)
