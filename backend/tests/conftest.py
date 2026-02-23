"""Pytest fixtures."""
import os
from pathlib import Path

import pytest

os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent
