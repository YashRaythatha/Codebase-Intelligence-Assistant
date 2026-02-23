"""Chunk files into fixed-size blocks with overlap."""

from pathlib import Path

CHUNK_LINES = 120
OVERLAP_LINES = 25


def chunk_file(repo_root: Path, rel_path: Path) -> list[dict]:
    """Chunk one file. Each chunk: {path, start_line, end_line, text}."""
    full = repo_root / rel_path
    if not full.exists():
        return []
    try:
        text = full.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    lines = text.splitlines()
    chunks: list[dict] = []
    start = 0
    while start < len(lines):
        end = min(start + CHUNK_LINES, len(lines))
        block = "\n".join(lines[start:end])
        chunks.append({
            "path": str(rel_path).replace("\\", "/"),
            "start_line": start + 1,
            "end_line": end,
            "text": f"FILE: {rel_path}\nLINES: {start + 1}-{end}\n\n{block}",
        })
        start = end - OVERLAP_LINES if end < len(lines) else len(lines)
    return chunks
