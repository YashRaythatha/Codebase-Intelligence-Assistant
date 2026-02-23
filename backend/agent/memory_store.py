"""In-memory store keyed by conversation_id; persist snapshots under data/repos/{repo_id}/memory/{conversation_id}.json."""

import json
from pathlib import Path
from typing import Any

from app.settings import get_settings

_store: dict[str, dict[str, Any]] = {}
MAX_MESSAGES = 10


def get_memory(repo_id: str, conversation_id: str) -> dict[str, Any]:
    key = f"{repo_id}:{conversation_id}"
    if key in _store:
        return _store[key].copy()
    settings = get_settings()
    mem_path = settings.repos_path / repo_id / "memory" / f"{conversation_id}.json"
    if mem_path.exists():
        try:
            data = json.loads(mem_path.read_text(encoding="utf-8"))
            _store[key] = data
            return data.copy()
        except Exception:
            pass
    return {"messages": [], "discovered": {}}


def save_memory(repo_id: str, conversation_id: str, data: dict[str, Any]) -> None:
    key = f"{repo_id}:{conversation_id}"
    messages = data.get("messages", [])[-MAX_MESSAGES:]
    data = {**data, "messages": messages}
    _store[key] = data
    settings = get_settings()
    mem_dir = settings.repos_path / repo_id / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    mem_path = mem_dir / f"{conversation_id}.json"
    try:
        mem_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def append_message(repo_id: str, conversation_id: str, role: str, content: str) -> None:
    mem = get_memory(repo_id, conversation_id)
    mem.setdefault("messages", []).append({"role": role, "content": content})
    save_memory(repo_id, conversation_id, mem)
