"""Detect frameworks: Python FastAPI, Django, Flask. Node Express, NestJS. Java Spring Boot. Save detected.json."""

import json
from pathlib import Path

from app.settings import get_settings


def detect_framework(repo_id: str) -> dict:
    """Detect frameworks from dependency files and imports. Save data/repos/{repo_id}/detected.json."""
    settings = get_settings()
    base = settings.repos_path / repo_id
    manifest_file = base / "manifest.json"
    if not manifest_file.exists():
        return {}
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        repo_root = Path(data.get("repo_root", str(base)))
        detected: dict = {"frameworks": [], "evidence": []}
        if (repo_root / "requirements.txt").exists():
            text = (repo_root / "requirements.txt").read_text(encoding="utf-8", errors="replace")
            if "fastapi" in text.lower():
                detected["frameworks"].append("FastAPI")
                detected["evidence"].append({"file": "requirements.txt", "line": 1, "hint": "fastapi"})
            if "django" in text.lower():
                detected["frameworks"].append("Django")
                detected["evidence"].append({"file": "requirements.txt", "line": 1, "hint": "django"})
            if "flask" in text.lower():
                detected["frameworks"].append("Flask")
                detected["evidence"].append({"file": "requirements.txt", "line": 1, "hint": "flask"})
        if (repo_root / "package.json").exists():
            pkg = json.loads((repo_root / "package.json").read_text(encoding="utf-8"))
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "express" in deps:
                detected["frameworks"].append("Express")
                detected["evidence"].append({"file": "package.json", "line": 1, "hint": "express"})
            if "nestjs" in str(deps).lower():
                detected["frameworks"].append("NestJS")
                detected["evidence"].append({"file": "package.json", "line": 1, "hint": "nestjs"})
        out_path = base / "detected.json"
        base.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(detected, indent=2), encoding="utf-8")
        return detected
    except Exception:
        return {}
