"""Smoke test: ensure no duplicate handlers when get_logger/configure called multiple times."""

import logging

from app.logging_config import configure_root_logging, get_logger, set_log_dir
from pathlib import Path
import tempfile


def test_no_duplicate_handlers():
    with tempfile.TemporaryDirectory() as tmp:
        set_log_dir(Path(tmp))
        configure_root_logging("INFO")
        root = logging.getLogger()
        count_before = len(root.handlers)

        configure_root_logging("INFO")
        count_after = len(root.handlers)
        assert count_after == count_before, "Repeated configure_root_logging should not add duplicate handlers"

    logger = get_logger("test.module")
    assert logger is not None
