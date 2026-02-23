"""Tests for chunker."""
from pathlib import Path

import pytest

from ingest.chunker import chunk_file, CHUNK_LINES, OVERLAP_LINES


def test_chunk_file(tmp_path):
    (tmp_path / "foo.py").write_text("line\n" * 50)
    chunks = chunk_file(tmp_path, Path("foo.py"))
    assert len(chunks) >= 1
    assert all("path" in c and "start_line" in c and "end_line" in c and "text" in c for c in chunks)
    assert chunks[0]["path"] == "foo.py"
    assert chunks[0]["start_line"] == 1
    assert "FILE:" in chunks[0]["text"] and "LINES:" in chunks[0]["text"]
