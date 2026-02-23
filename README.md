# Codebase Intelligence Assistant

RAG + Agent assistant for codebase Q&A: ingest a repo (GitHub or local path), ask questions, get answers with **file and line citations**. The **agent** uses a ReAct-style loop with tools (`list_files`, `grep`, `open_file`, `get_manifest`); **RAG** fallback runs if the agent fails or returns no evidence. Uses LangChain, OpenAI embeddings, and Chroma. Answer format: Summary, Evidence (file/line citations), and **actionable Next steps** (recommendations, not follow-up questions).

---

## 1. Quick Setup Instructions

**Prerequisites:** Python 3.10+, Node 18+ (for frontend), OpenAI API key.

**Setup:** See **[SETUP.md](SETUP.md)** for step-by-step setup (venv, backend, frontend). Then edit `.env` and set `OPENAI_API_KEY`.

**Backend (manual):**

```bash
git clone <this-repo>
cd Codebase_Intelligence_Assistant
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Unix
pip install -e .
copy .env.example .env          # Windows; cp on Unix
# Edit .env and set OPENAI_API_KEY=sk-...
```

**Run locally (two terminals, from project root):**

| Terminal | Command | URL |
|----------|---------|-----|
| 1 | `make run-api` or `python backend/app/main.py` or `run-backend.bat` (Windows) | http://localhost:8000 |
| 2 | `make run-web` or `cd frontend && npm install && npm run dev` or `run-frontend.bat` (Windows) | http://localhost:3000 |

**Verify:** Open http://localhost:8000/health (expect `{"status":"ok"}`), then http://localhost:3000.

- **Home**: ingest a repo (GitHub URL or local path). **Ask**: select repo, type a question → get **Summary**, **Evidence** (file/line citations with **View snippet**), and **Next steps** (actionable recommendations). Optional trace viewer; 404 page and history in UI.
- **Useful URLs:** API docs http://localhost:8000/docs · Health http://localhost:8000/health

**Features:** ReAct agent with tools (list_files, grep, open_file, get_manifest); RAG fallback; evidence deduplication; actionable Next steps (recommendations, not "Try asking"); ingest validation (GitHub/GitLab/Bitbucket URLs, local path); path traversal guards; `/file` snippet cap (e.g. 50 lines for View snippet); trace viewer; 404 page; ask history (localStorage).

**Docker Compose:**

```bash
copy .env.example .env   # set OPENAI_API_KEY
docker-compose up --build
```

Backend: http://localhost:8000 · Frontend: http://localhost:3000

---

## 2. Architecture Overview

```
  User (browser)
         │
         ├──► FastAPI (backend/): /ingest, /ask, /repos, /file, /trace
         └──► Next.js (frontend/): Home (ingest, repo picker), Ask (Q&A, evidence, View snippet)
                              │
                              ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  app: settings, logging, tracing (run_id, steps, usage per run)  │
  └─────────────────────────────────────────────────────────────────┘
         │
         ├──► ingest: loader → scanner → chunker → indexer
         │              (manifest + detected.json under data/repos/{repo_id})
         │
         ├──► rag: retriever (Chroma, top-k=10) │ chains (answer_with_rag, parse_structured_answer) │ rag_fallback
         ├──► agent: ReAct loop (list_files, grep, open_file, get_manifest) │ agent_runner │ memory_store
         │         prompts (agent, RAG, tool extraction)
         │
         └──► analysis: framework_detector, endpoint_mapper, auth_finder,
                        dependency_mapper, flow_tracer
                              │
                              ▼
  Chroma (vectors) + OpenAI (embeddings + chat)
```

**Flow:** Ingest → clone/scan → chunk (120 lines, 25 overlap) → embed → index; framework detection writes `detected.json`. Ask → **agent first** (ReAct with tools + memory per conversation_id), **RAG fallback** on failure or no evidence → parse Summary / Evidence / Next steps (shared `parse_structured_answer`); evidence deduped by (path, start_line, end_line). Every request gets **run_id** and **trace_id**; trace saved as `data/traces/{trace_id}.json`. Frontend: **GET /trace?trace_id=** and trace viewer toggle; Next steps shown as actionable list (optional "Or ask:" for question-like lines).

---

## 3. Productionization Plan

If this needed to run at scale on **AWS / GCP / Azure**:

**Changes required**

- **Secrets:** Move `OPENAI_API_KEY` (and any DB credentials) to a secret manager (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault). Inject via env or runtime fetch; never in code or image.
- **Vector store:** Replace local Chroma with a managed service (Pinecone, Weaviate Cloud, AWS OpenSearch with vector support) or self-host Chroma/Weaviate behind a load balancer so multiple app instances share the same index.
- **App runtime:** Run FastAPI behind a reverse proxy (ALB/nginx); multiple workers (uvicorn workers or gunicorn). Frontend: build Next.js (`npm run build`), serve static assets via S3 + CloudFront (or equivalent); set `NEXT_PUBLIC_API_BASE_URL` to the public API URL.
- **Persistence:** Today repos/manifests live on local disk. For scale: store manifest and metadata in a DB (e.g. PostgreSQL); keep file content in object storage (S3/GCS/Azure Blob) or still on attached volume if acceptable. Repo clone/scan could run in a worker (e.g. Celery, Lambda, Cloud Run job).
- **Auth:** Add API key or OAuth for `/ingest` and `/ask`; rate limit per user/tenant to protect cost and abuse.

**Scaling**

- **Horizontal:** Stateless API replicas behind a load balancer; shared vector DB and (if added) DB. Ingest jobs in a queue + worker pool.
- **Vertical:** Larger instances for embedding/indexing bursts; separate read path (ask) from write path (ingest) so heavy ingest doesn’t starve queries.

**Security**

- TLS everywhere; secrets from vault only. Path traversal already guarded (all file access under repo root). Input validation and rate limiting on `/ask` and `/ingest`. Optional: scan uploaded/cloned repos for secrets before indexing.

**Monitoring**

- Export metrics (request count, latency p50/p99, error rate, token usage) to Prometheus/CloudWatch/Stackdriver. Alerts on error rate and latency. Centralize logs (e.g. CloudWatch Logs, GCP Logging) and optionally trace (OpenTelemetry → X-Ray/Datadog).

**Cost**

- Dominated by OpenAI (embedding + LLM). Mitigate: cache embeddings per chunk hash; use smaller/cheaper model where acceptable; rate limit and quotas per user. Vector DB and compute are secondary.

**Reliability**

- Health check (`GET /health`) for load balancer. Retries with backoff for OpenAI and vector DB. Agent fallback to RAG on failure already in place. Idempotent ingest where possible (e.g. index by chunk hash).

---

## 4. RAG / LLM Approach & Design Decisions

**Chunking strategy**

- **Choice:** 120 lines per chunk, 25-line overlap. Chunks are built from contiguous lines with a `FILE:` / `LINES:` header and metadata (rel_path, start_line, end_line).
- **Reasoning:** Code is line-oriented; 120 lines keeps functions/modules in one or few chunks. Overlap reduces boundary effects. We did not tune per-language; a single strategy keeps the pipeline simple.

**Embedding model choice**

- **Choice:** OpenAI `text-embedding-3-small` (configurable via `OPENAI_EMBED_MODEL`).
- **Reasoning:** Good quality and stable API; same provider as the chat model simplifies keys and billing. Alternatives (e.g. Cohere, local models) would require another integration and possibly different dimensionality handling in Chroma.

**LLM selection**

- **Choice:** OpenAI chat model (default `gpt-4o`, configurable via `OPENAI_MODEL`).
- **Reasoning:** Strong instruction-following and tool use for the agent; consistent format for Summary / Evidence / Next steps. Temperature 0 for deterministic answers.

**Retrieval method**

- **Choice:** Semantic only: embed the user question, retrieve top-k (default 10) chunks by cosine similarity from Chroma. Overview-style questions prefer doc chunks first. No keyword/BM25, no reranker.
- **Tradeoff:** Simple and fast; may miss exact string matches. Acceptable for “conceptual” code Q&A; hybrid or reranker could be added later if needed.

**Prompt design**

- **RAG path:** Single prompt: “Answer using ONLY the provided context; cite FILE and LINES; output Summary / Evidence / Next Steps.” Context = concatenated retrieved chunks.
- **Agent path:** System prompt: rules (no invented paths, cite FILE/LINES, use tools when needed, output same three sections). Human message = user question + agent scratchpad.
- **Tool extraction (analysis):** Separate prompts for endpoint extraction and auth detection from code → strict JSON. Keeps parsing reliable for plugins.

**Prompts used (exact text)**

Defined in `backend/rag/prompts.py`. The RAG chain uses `RAG_SYSTEM` + `RAG_USER_TEMPLATE`; the agent uses `AGENT_SYSTEM` when the full agent is wired.

- **RAG system** (`RAG_SYSTEM`):  
  *You answer questions about a codebase using ONLY the provided context. Cite every claim with FILE and LINES (e.g. FILE: path/to/file.py LINES: 10-20). Output exactly three sections: Summary: (short answer), Evidence: (list of FILE/LINES with a brief note for each), Next steps: (actionable recommendations, e.g. bullet points). Do not invent paths; only cite paths that appear in the context.*

- **RAG user** (`RAG_USER_TEMPLATE`):  
  *Context from the codebase:*  
  *{context}*  
  *Question: {question}*  
  *Answer using only the context above. Cite FILE and LINES.*

- **Agent system** (`AGENT_SYSTEM`):  
  *You are a codebase assistant. Use the tools to explore the repo when needed. Rules: Only cite files that exist in the repo (use tools to list/read files). Cite with FILE and LINES (e.g. FILE: path/to/file.py LINES: 10-20). Output exactly three sections: Summary, Evidence, Next steps (actionable recommendations). Do not make up file paths or line numbers.*

**Context window management**

- Chunk size (120 lines) and top-k (10) keep total context within model limits. No explicit truncation of retrieved text; if we increased top-k, we’d need to cap total tokens or summarize chunks.

**Guardrails**

- **Path traversal:** All file access (tools, `/file` API) resolves under repo root; `..` and absolute paths rejected.
- **Manifest guardrail (agent):** If the agent’s final answer mentions a file path not in the repo manifest, we append a note (“File not found in manifest. Verify.”) and log it.
- **Citation parsing:** Only parsed FILE/LINES from the model output are shown as evidence; we don’t trust free-form paths in prose.
- **`/file` limit:** Max 200 lines per request to bound payload and abuse.

**Quality evaluation**

- **Eval harness:** 20 sample questions (`eval/sample_questions.json`); runner runs them against a repo_id, prints citation coverage (% of answers with ≥1 evidence) and latency, writes `eval/results.json`. No ground-truth labels yet; used for regression and tuning.

**Observability**

- **Logging:** Per-module loggers; logs under `LOG_DIR` (e.g. `data/logs/`) with RotatingFileHandler. `run_id` available for correlation.
- **Traces:** Every request gets a `run_id` and `trace_id` (uuid4). Steps (retrieval, LLM, agent tool calls), token usage, and final answer written to `TRACE_DIR/{trace_id}.json` for debugging and cost analysis.

---

## 5. Key Technical Decisions

| Decision | Why |
|----------|-----|
| **Chroma for vectors** | Local, no extra service for MVP; straightforward to replace with Pinecone/Weaviate for scale. |
| **OpenAI for embed + LLM** | Single provider, good quality, configurable via env. |
| **Agent by default for Ask** | ReAct agent with tools: list_files, grep, open_file, get_manifest; RAG fallback if agent fails or returns no evidence. |
| **Structured answer (Summary / Evidence / Next steps)** | Consistent UI and parsing; evidence is machine-parseable (file, lines, note); Next steps are actionable recommendations (bullet points), not follow-up questions. |
| **Regex parsing of LLM output** | No dependency on JSON/structured output API; works with any model that follows the prompt. Tradeoff: brittle if format drifts. |
| **Repo ID = hash of URL/path** | Stable ID without a DB; same repo always gets the same ID. |
| **Manifest + detected.json per repo** | Enables incremental index updates and framework-aware analysis (endpoint/auth plugins). |
| **Trace per request** | Debugging and eval; each run is a JSON file with steps and usage. |
| **Next.js in `frontend/`** | Clear separation from backend; can be deployed independently. |

Decision log and tradeoffs are documented in the sections above.

---

## 6. Engineering Standards

**Practices followed**

- **Type hints and docstrings** on public functions.
- **Modular layout:** `backend/` (app, ingest, rag, analysis, eval), `frontend/` with clear boundaries.
- **Single responsibility:** Small functions; trace hooks at request boundaries.
- **Secrets:** Only in `.env`; never hardcoded.
- **Logging:** One logger per module via `get_logger(__name__)`; structured enough to grep by component.
- **Testing:** Pytest for backend (ingest, chunker, indexer, retriever, chains, tools, analysis, API); eval runner for citation coverage and latency. No frontend test suite.
- **Linting:** Ruff and Black (see Makefile `lint`).
- **Containerization:** Dockerfile for backend; `frontend/Dockerfile` for frontend; `docker-compose.yml` for both.

**Consciously skipped (and why)**

- **Go support:** Scope is Python, Node, Java; keeps plugin surface and tests manageable.
- **Reranker / hybrid search:** Not implemented to keep v1 simple; add if quality requires it.
- **Structured output (JSON) for RAG answer:** Regex parsing works with current models; JSON would need schema and validation.
- **Auth in MVP:** Shipped without API keys or login; add for multi-tenant or public deployment.
- **Database for repo metadata:** File-based manifest and `memory.json`; no DB to keep the stack minimal.
- **Streaming for `/ask`:** Single response; streaming could be added later.
- **Frontend automated tests:** Backend and eval covered; frontend tested manually. Jest/Playwright could be added.
- **Persistent agent chat across sessions:** Agent appends user/assistant messages to disk per `conversation_id` under `data/repos/{repo_id}/memory/`; no cross-session chat UI.

See the “Consciously skipped” list.

---

## 7. What You'd Improve with More Time

- **RAG:** Add a reranker for retrieved chunks; try hybrid search (keyword + vector); tune chunk size/overlap per language.
- **Agent:** Add tools (e.g. “run tests”); optional “RAG only” toggle in the UI for faster, cheaper answers.
- **Eval:** Ground-truth labels (expected files/snippets per question); regression tests on citation coverage; latency SLOs.
- **Frontend:** Skeleton loaders, keyboard shortcuts, optional dark theme, shareable question URLs.
- **Auth:** API key or OAuth for production.
- **Docs:** OpenAPI examples; short “Quick start” video or GIF.
- **Observability:** Export metrics (Prometheus/CloudWatch); distributed tracing for agent tool calls.

---

## Project layout

```
backend/          # Python API and RAG pipeline
  app/            # Settings, logging, tracing, FastAPI routes
  ingest/         # loader, scanner, chunker, indexer (manifest under data/repos/{repo_id})
  rag/            # Prompts, retriever (Chroma top-k=10), chains (answer_with_rag, parse_structured_answer), rag_fallback
  agent/          # agent_runner (ReAct + tools), langchain_tools, tools, memory_store, guardrails
  analysis/       # Framework detector, endpoint mapper, auth finder, dependency mapper, flow tracer
  eval/           # sample_questions.json, runner.py, results.json
  tests/          # Pytest tests

frontend/         # Next.js UI
  src/app/        # layout, page (Home), ask/page, not-found
  src/components/ # RepoSelect, IngestForm, EvidenceModal, TraceViewer, ChatPanel
  src/lib/        # api, storage, types, uuid
  ...

docker/           # Backend Dockerfile
data/             # Repos, manifests, indexes, logs, traces (gitignored)
```

**Commands:** `make setup` | `make lint` | `make test` | `make run-api` | `make run-web`. Windows: `run-backend.bat`, `run-frontend.bat`. Eval (from repo root, after `pip install -e .`): `python -m eval.runner <repo_id>`.

**Environment:** `.env` from `.env.example`; require `OPENAI_API_KEY`. Optional: `OPENAI_MODEL`, `OPENAI_EMBED_MODEL`, `REPOS_BASE`, `CHROMA_DIR`, `LOG_DIR`, `TRACE_DIR`, `ALLOWED_ORIGINS`. Frontend: `frontend/.env` from `frontend/.env.example` → `NEXT_PUBLIC_API_BASE_URL`.

See the architecture and technical decisions sections above for details.
