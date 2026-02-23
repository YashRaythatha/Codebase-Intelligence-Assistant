"""FastAPI routes: /ingest, /ask, /repos, /health, /file, /trace. run_id and trace_id per request."""

import json
import uuid
from pathlib import Path

from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.schemas import (
    IngestRequest,
    IngestResponse,
    AskRequest,
    AnswerBody,
    EvidenceItem,
    FileLine,
)
from app.logging_config import get_logger
from app.settings import get_settings
from app.tracing import Trace
from ingest.indexer import index_repo
from rag.chains import answer_with_rag
from rag.rag_fallback import run_rag
from agent.agent_runner import run_agent as run_agent_runner
from analysis.framework_detector import detect_framework as detect_framework_analysis

logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
    if not origins:
        origins = ["http://localhost:3000"]

    app = FastAPI(
        title="Codebase Intelligence Assistant",
        version="0.1.0",
        description="Ingest repositories (GitHub or local path), ask questions, get answers with file and line citations.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    def unhandled_exception_handler(request, exc):
        """Return consistent JSON 500 without leaking stack traces. HTTPException is re-raised."""
        if isinstance(exc, HTTPException):
            raise exc
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred. Please try again."},
        )

    @app.get("/health", tags=["Health"])
    def health():
        """Liveness check. Returns 200 when the service is up."""
        return {"status": "ok"}

    def _validate_ingest_source(source: str) -> None:
        """Validate source (URL or local path). Raises HTTPException 400 if invalid."""
        s = source.strip()
        if not s:
            raise HTTPException(status_code=400, detail="Provide repo_url, local_path, or source")
        if s.startswith("http://") or s.startswith("https://"):
            if "github.com" not in s and "gitlab.com" not in s and "bitbucket" not in s:
                raise HTTPException(
                    status_code=400,
                    detail="Supported URLs: GitHub, GitLab, or Bitbucket (e.g. https://github.com/user/repo)",
                )
            return
        # Local path
        p = Path(s).resolve()
        if not p.exists():
            raise HTTPException(status_code=400, detail=f"Local path does not exist: {s}")
        if not p.is_dir():
            raise HTTPException(status_code=400, detail="Local path must be a directory")

    def _validate_repo_id(repo_id: str) -> None:
        """Reject path traversal or invalid repo_id."""
        if not repo_id or ".." in repo_id or "/" in repo_id or "\\" in repo_id:
            raise HTTPException(status_code=400, detail="Invalid repo_id")

    @app.post("/ingest", response_model=IngestResponse, tags=["Ingest"])
    def ingest(body: IngestRequest):
        """Index a repository from a GitHub URL or local path. Returns repo_id and optional framework detection."""
        run_id = str(uuid.uuid4())
        trace = Trace()
        trace.start(run_id=run_id, endpoint_name="ingest")
        source = body.source or body.repo_url or body.local_path or ""
        logger.info("ingest start run_id=%s source_preview=%s", run_id, (source[:80] + "..." if len(source) > 80 else source))
        try:
            _validate_ingest_source(source)
            repo_id = index_repo(source)
            trace.add_step("index", {"repo_id": repo_id})
            detected = detect_framework_analysis(repo_id)
            trace.end(answer_summary=repo_id)
            trace.save()
            return IngestResponse(repo_id=repo_id, index_stats=None, detected=detected or None)
        except HTTPException:
            raise
        except ValueError as e:
            trace.add_step("error", {"detail": str(e)})
            trace.end()
            trace.save()
            raise HTTPException(status_code=400, detail=str(e))
        except FileNotFoundError as e:
            trace.add_step("error", {"detail": str(e)})
            trace.end()
            trace.save()
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.exception("Ingest failed")
            trace.add_step("error", {"detail": str(e)})
            trace.end()
            trace.save()
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/ask", tags=["Ask"])
    def ask(body: AskRequest):
        """Ask a question about an indexed repo. Returns summary, evidence (file/line citations), and actionable next steps."""
        run_id = str(uuid.uuid4())
        trace = Trace()
        logger.info("ask start run_id=%s repo_id=%s question_preview=%s", run_id, body.repo_id, (body.question[:80] + "..." if len(body.question) > 80 else body.question))
        trace.start(
            run_id=run_id,
            repo_id=body.repo_id,
            conversation_id=body.conversation_id,
            question=body.question,
            endpoint_name="ask",
        )
        try:
            _validate_repo_id(body.repo_id)
            repo_manifest = settings.repos_path / body.repo_id / "manifest.json"
            if not repo_manifest.exists():
                raise HTTPException(status_code=404, detail="Repo not found. Ingest the repo first.")
            if body.use_agent:
                try:
                    out = run_agent_runner(
                        body.repo_id,
                        body.conversation_id,
                        body.question,
                        trace,
                        run_id,
                    )
                except Exception:
                    out = run_rag(body.repo_id, body.question, trace, run_id)
            else:
                out = run_rag(body.repo_id, body.question, trace, run_id)
            # Deduplicate evidence by (path, start_line, end_line)
            raw_evidence = out.get("evidence", [])
            seen = set()
            unique_evidence = []
            for e in raw_evidence:
                key = (e.get("path"), e.get("start_line"), e.get("end_line"))
                if key in seen:
                    continue
                seen.add(key)
                unique_evidence.append(e)
            evidence = [
                EvidenceItem(path=e["path"], start_line=e["start_line"], end_line=e["end_line"], note=e.get("note"))
                for e in unique_evidence
            ]
            next_steps_list = [out.get("next_steps", "")] if out.get("next_steps") else []
            answer = AnswerBody(summary=out.get("summary", ""), evidence=evidence, next_steps=next_steps_list)
            trace.add_step("answer", {"summary_preview": (out.get("summary") or "")[:200]})
            trace.end(answer_summary=out.get("summary", "")[:500])
            trace.save()
            # New shape (prompt) + legacy top-level (frontend compat)
            return {
                "answer": answer.model_dump(),
                "trace_id": trace.trace_id,
                "run_id": run_id,
                "summary": out.get("summary", ""),
                "evidence": [{"path": e.path, "start_line": e.start_line, "end_line": e.end_line, "note": e.note} for e in evidence],
                "next_steps": out.get("next_steps", ""),
                "source": out.get("source", "rag"),
            }
        except Exception as e:
            logger.exception("Ask failed")
            trace.add_step("error", {"detail": str(e)})
            trace.end()
            trace.save()
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/repos", tags=["Repos"])
    def repos():
        """List indexed repositories (repo_id and root_path from each manifest)."""
        settings = get_settings()
        base = settings.repos_path
        if not base.exists():
            return {"repos": []}
        result = []
        for d in base.iterdir():
            if d.is_dir():
                manifest_file = d / "manifest.json"
                if manifest_file.exists():
                    try:
                        data = json.loads(manifest_file.read_text(encoding="utf-8"))
                        result.append({"repo_id": data.get("repo_id", d.name), "root_path": data.get("repo_root", "")})
                    except Exception as e:
                        logger.warning("repos: could not parse manifest %s: %s", manifest_file, e)
                        result.append({"repo_id": d.name, "root_path": ""})
        return {"repos": result}

    @app.get("/file", tags=["File"])
    def get_file(repo_id: str, path: str, start: int | None = None, end: int | None = None, max_lines: int | None = None):
        """Return file content or a line range (for evidence snippets). Path is relative to repo root."""
        _validate_repo_id(repo_id)
        settings = get_settings()
        base = settings.repos_path / repo_id
        manifest_file = base / "manifest.json"
        if not manifest_file.exists():
            raise HTTPException(status_code=404, detail="Repo not found")
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        repo_root = Path(manifest.get("repo_root", str(base)))
        path_clean = path.replace("\\", "/").lstrip("/").rstrip(".,;")
        if ".." in path_clean or path_clean.startswith("/") or not path_clean:
            raise HTTPException(status_code=400, detail="Invalid path")
        # Try canonical repo copy first (data/repos/repo_id), then manifest repo_root
        full = base / path_clean
        if not full.exists() or not full.is_file():
            full = repo_root / path_clean
        if not full.exists() or not full.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        try:
            all_lines = full.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            raise HTTPException(status_code=500, detail="Could not read file")
        cap = min(200, max(1, max_lines)) if max_lines is not None else 200
        if start is not None and end is not None:
            start1 = max(0, start - 1)
            end1 = min(len(all_lines), max(end, start1 + 1))
            if start1 >= len(all_lines) and len(all_lines) > 0:
                start1 = len(all_lines) - 1
                end1 = len(all_lines)
            # Cap snippet size for "View snippet" (e.g. max_lines=50)
            span = end1 - start1
            if span > cap:
                end1 = start1 + cap
            lines = all_lines[start1:end1]
            line_objs = [FileLine(no=start1 + i + 1, text=line) for i, line in enumerate(lines)]
        else:
            lines = all_lines[:cap]
            line_objs = [FileLine(no=i + 1, text=line) for i, line in enumerate(lines)]
        lines_flat = [ln.text for ln in line_objs]
        return {"file": path_clean, "path": path_clean, "start": start, "end": end, "lines": lines_flat, "lines_numbered": [{"no": ln.no, "text": ln.text} for ln in line_objs]}

    @app.get("/trace", tags=["Trace"])
    def get_trace(trace_id: str):
        """Fetch a request trace by trace_id (steps, token usage, etc.)."""
        if not trace_id or ".." in trace_id or "/" in trace_id or "\\" in trace_id:
            raise HTTPException(status_code=400, detail="Invalid trace_id")
        settings = get_settings()
        trace_path = settings.trace_path / f"{trace_id}.json"
        if not trace_path.is_file():
            raise HTTPException(status_code=404, detail="Trace not found")
        try:
            data = json.loads(trace_path.read_text(encoding="utf-8"))
            return data
        except Exception:
            raise HTTPException(status_code=500, detail="Could not read trace")

    return app
