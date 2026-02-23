"""Scan repo directory for code and documentation files."""

from pathlib import Path

EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".rb"}
DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".txt"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build", ".next"}


def is_doc_path(rel_path: Path) -> bool:
    """True if path is likely documentation (README, CONTRIBUTING, docs/, *.md)."""
    s = rel_path.as_posix().lower()
    return (
        "readme" in s
        or "contributing" in s
        or s.startswith("docs/")
        or rel_path.suffix.lower() in {".md", ".mdx", ".rst"}
    )


def scan_files(repo_root: Path) -> list[Path]:
    """Return list of relative paths for code and doc files under repo_root."""
    out: list[Path] = []
    for f in repo_root.rglob("*"):
        if not f.is_file():
            continue
        if any(part in SKIP_DIRS for part in f.relative_to(repo_root).parts):
            continue
        rel = f.relative_to(repo_root)
        if f.suffix.lower() in EXTENSIONS or f.suffix.lower() in DOC_EXTENSIONS:
            out.append(rel)
    return sorted(out)
