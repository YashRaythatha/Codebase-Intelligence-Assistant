# Backend – Codebase Intelligence Assistant

FastAPI service: ingest repos, run agent-first with RAG fallback, return answers with evidence and trace_id.

## Structure

- **app/** – main, settings, logging (run_id/trace_id), tracing (JSON per request), api (routes, schemas)
- **ingest/** – repo_loader, file_scanner (FileRecord), chunker, indexer (Chroma per repo_id)
- **rag/** – prompts, retriever, rag_fallback
- **agent/** – tools, guardrails, memory_store, agent_runner (agent first, then RAG)
- **analysis/** – framework_detector, endpoint_mapper, auth_finder, dependency_mapper, flow_tracer

## Run

From repo root: `pip install -e .` then `python -m app.main`. See root README and SETUP.md.

## Data

- `data/repos/{repo_id}/` – manifest, memory, detected.json
- `data/indexes/` – Chroma per repo_id
- `data/logs/` – app.log and per-module logs
- `data/traces/{trace_id}.json` – request traces
