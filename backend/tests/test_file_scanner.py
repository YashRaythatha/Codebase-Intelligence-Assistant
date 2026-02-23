"""Unit tests for file_scanner: FileRecord list and manifest."""

from pathlib import Path

import pytest

from ingest.file_scanner import FileRecord, scan, write_manifest


def test_scan_mini_repo():
    fixtures = Path(__file__).resolve().parent / "fixtures" / "mini_repo"
    if not fixtures.exists():
        pytest.skip("fixtures/mini_repo not found")
    records = scan(fixtures)
    assert len(records) >= 2
    paths = [str(r.rel_path).replace("\\", "/") for r in records]
    assert any("foo.py" in p for p in paths)
    assert any("bar.js" in p for p in paths)
    for r in records:
        assert isinstance(r, FileRecord)
        assert r.abs_path.exists()
        assert r.ext in {".py", ".js", ".ts", ".java", ".md", ".yml", ".json", ".toml", ".sql", ".txt"}
        assert r.sha256
        assert r.size_bytes >= 0
