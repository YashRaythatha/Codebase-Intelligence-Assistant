"""Configure root logger and per-module loggers. get_logger(name, run_id, trace_id) for request context."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_log_dir: Path | None = None
_log_formatter: logging.Formatter | None = None
_module_logs_configured: set[str] = set()


def set_log_dir(path: Path) -> None:
    global _log_dir
    _log_dir = path


class _ContextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.run_id = getattr(record, "run_id", "")
        record.trace_id = getattr(record, "trace_id", "")
        return super().format(record)


def _ensure_module_log(name: str) -> None:
    """Add rotating file handler for this module to backend/data/logs/{sanitized_module}.log (no duplicates)."""
    global _log_formatter, _module_logs_configured
    if not _log_dir or not _log_formatter:
        return
    safe = name.replace(".", "_").replace("/", "_")[:64]
    if safe in _module_logs_configured:
        return
    _module_logs_configured.add(safe)
    log = logging.getLogger(name)
    for h in log.handlers:
        if getattr(h, "baseFilename", "").endswith(f"{safe}.log"):
            return
    _log_dir.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(_log_dir / f"{safe}.log", maxBytes=5 * 1024 * 1024, backupCount=3)
    fh.setFormatter(_log_formatter)
    log.addHandler(fh)


def get_logger(name: str, run_id: str | None = None, trace_id: str | None = None) -> logging.Logger:
    _ensure_module_log(name)
    logger = logging.getLogger(name)
    if run_id or trace_id:
        return logging.LoggerAdapter(logger, {"run_id": run_id or "", "trace_id": trace_id or ""})
    return logger


def configure_root_logging(level: str = "INFO") -> None:
    global _log_formatter
    level_map = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING, "ERROR": logging.ERROR}
    log_level = level_map.get(level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(log_level)
    for h in root.handlers[:]:
        root.removeHandler(h)

    _log_formatter = _ContextFormatter("%(asctime)s | %(levelname)s | run_id=%(run_id)s | trace_id=%(trace_id)s | %(name)s | %(message)s")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(_log_formatter)
    root.addHandler(sh)

    if _log_dir:
        _log_dir.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(_log_dir / "app.log", maxBytes=5 * 1024 * 1024, backupCount=3)
        fh.setFormatter(_log_formatter)
        root.addHandler(fh)
