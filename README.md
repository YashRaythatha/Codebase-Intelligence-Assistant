# Codebase Intelligence Assistant

A small app that lets you point at a codebase (GitHub repo or local folder), ask questions in plain English, and get answers with file and line references. It uses retrieval-augmented generation (RAG) and an optional agent with tools; when the agent isn’t enough, it falls back to RAG so you still get an answer. Built with Python (FastAPI), Next.js, LangChain, OpenAI, and Chroma.

---

## 1. Quick Setup Instructions

You’ll need **Python 3.10+**, **Node 18+** (for the frontend), and an **OpenAI API key**.

**One-time setup (from the project root):**

```bash
git clone <this-repo>
cd Codebase_Intelligence_Assistant

# Backend
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate # macOS/Linux
pip install -e .

# Copy env and add your key
copy .env.example .env     # Windows (use cp on Unix)
# Edit .env and set OPENAI_API_KEY=sk-...

# Frontend
cd frontend
npm install
cd ..
```

**Run the app (two terminals):**

| Terminal | Command | Where it runs |
|----------|---------|----------------|
| 1 (backend) | `python backend/app/main.py` or `run-backend.bat` (Windows) | http://localhost:8000 |
| 2 (frontend) | `cd frontend && npm run dev` or `run-frontend.bat` (Windows) | http://localhost:3000 |

**Check it’s working:** Open http://localhost:8000/health (you should see `{"status":"ok"}`), then http://localhost:3000. On the **Home** page you can ingest a repo (GitHub URL or local path). On **Ask** you pick that repo, type a question, and get a summary, evidence (file/line citations with “View snippet”), and actionable next steps. API docs: http://localhost:8000/docs.

There’s also a **SETUP.md** in the repo with more detail and troubleshooting.

**Docker (optional):** From the project root, copy `.env.example` to `.env`, set `OPENAI_API_KEY`, then run `docker-compose up --build`. Backend and frontend will be on 8000 and 3000 as above.

---

## 2. Architecture Overview

High level: the browser talks to a FastAPI backend and a Next.js frontend. The backend handles ingest (clone/scan, chunk, embed, index), ask (agent first, then RAG fallback), and a few support endpoints. Everything that touches the LLM or vector store goes through a small app layer (settings, logging, tracing).

```
  Browser
     │
     ├──► Next.js (frontend)     →  Home (ingest form, repo list), Ask (question, answer, evidence, next steps)
     │
     └──► FastAPI (backend)      →  /ingest, /ask, /repos, /file, /trace, /health
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
          ▼                             ▼                             ▼
     Ingest pipeline              Ask pipeline                  Support
     (loader → scanner →          (agent or RAG)                (/file, /trace,
      chunker → indexer)           → parse answer                 /repos)
          │                             │                             │
          └─────────────────────────────┴─────────────────────────────┘
                                        │
          Chroma (vectors) + OpenAI (embeddings + chat)
```

**Ingest:** You give a GitHub URL or a local path. The backend clones or uses that path, scans for code/docs (by extension), chunks files (120 lines with 25-line overlap), embeds chunks with OpenAI, and stores them in Chroma under a stable repo id (hash of the source). A manifest per repo is written under `data/repos/{repo_id}/`.

**Ask:** For each question we first try the agent (ReAct-style loop with tools: list_files, grep, open_file, get_manifest). If that fails or returns no evidence, we fall back to RAG: embed the question, retrieve top-k chunks from Chroma, and call the LLM with that context. The model is asked to output three sections—Summary, Evidence (FILE/LINES), Next steps—and we parse that with a shared function so the UI always gets the same shape. Evidence is deduplicated by (path, start_line, end_line). Every request gets a run_id and a trace_id; the trace (steps, usage, etc.) is saved under `data/traces/{trace_id}.json` so you can debug or inspect cost.

---

## 3. Productionization Plan

If this had to run at scale on AWS, GCP, or Azure, I’d change the following.

**What would need to change**

- **Secrets:** Move `OPENAI_API_KEY` (and any future DB or API keys) into a secret manager (e.g. AWS Secrets Manager, GCP Secret Manager). Load at startup or per request; never bake into images or code.
- **Vector store:** Replace local Chroma with a managed or shared store (e.g. Pinecone, Weaviate, or OpenSearch with vectors) so multiple API instances share the same indexes.
- **App hosting:** Run FastAPI behind a load balancer (ALB, nginx, etc.) with several workers (e.g. uvicorn workers or gunicorn). Build the Next.js app and serve it via a CDN or static hosting; point the frontend at the public API URL via env.
- **Data:** Right now repos and manifests live on disk. At scale I’d put manifest and metadata in a database (e.g. Postgres) and either keep blobs in object storage (S3/GCS) or on a shared volume. Ingest (clone, scan, index) would run in a queue (e.g. Celery, Lambda, or Cloud Run jobs) so it doesn’t block the read path.
- **Auth and limits:** Add API key or OAuth for `/ingest` and `/ask`, and rate limits per user or tenant to control cost and abuse.

**Scaling**

- **Horizontal:** Run stateless API replicas behind the load balancer; share the vector DB and (if added) the relational DB. Put ingest work in a queue and scale workers separately.
- **Vertical:** Use larger instances for heavy ingest/embedding bursts if needed. Keep the read path (ask) separate so that ingest doesn’t starve queries.

**Security, monitoring, cost, reliability**

- **Security:** TLS everywhere; all secrets from the vault. Path traversal is already guarded (no `..`, no absolute paths outside repo root). I’d add input validation and rate limiting on the public endpoints and optionally scan cloned repos for secrets before indexing.
- **Monitoring:** Emit metrics (request count, latency, error rate, token usage) to Prometheus or the cloud provider’s metrics. Set alerts on error rate and latency. Send logs to a central place (e.g. CloudWatch Logs, GCP Logging) and optionally add tracing (e.g. OpenTelemetry to X-Ray or Datadog).
- **Cost:** Most cost is OpenAI (embeddings + LLM). I’d cache embeddings by content hash where possible, consider a smaller/cheaper model for some flows, and enforce quotas and rate limits per user.
- **Reliability:** Use the existing `/health` for the load balancer. Add retries with backoff for OpenAI and the vector store. The agent→RAG fallback is already there; I’d make ingest idempotent (e.g. key by chunk hash) where possible.

---

## 4. RAG / LLM Approach & Design Decisions

**Chunking**

I use 120 lines per chunk with a 25-line overlap. Each chunk gets a small header (`FILE: path`, `LINES: start-end`) and metadata (path, start_line, end_line). Code is line-oriented, and 120 lines usually keeps a function or a small module together; the overlap helps when the answer spans a boundary. I didn’t tune per language—one strategy keeps the pipeline simple and good enough for an MVP.

**Embedding model**

I use OpenAI’s `text-embedding-3-small` (configurable via `OPENAI_EMBED_MODEL`). It’s solid, the API is stable, and using the same provider as the chat model keeps keys and billing simple. Other options (e.g. Cohere or local models) would need extra integration and possibly different handling for dimensions in Chroma.

**LLM**

The chat model is OpenAI (default `gpt-4o`, overridable with `OPENAI_MODEL`). I use temperature 0 so answers are deterministic. The agent needs good instruction-following and tool use; the same model is used for the RAG path so the output format (Summary / Evidence / Next steps) stays consistent.

**Retrieval**

It’s semantic only: embed the question, retrieve top-k (default 10) chunks by similarity in Chroma. For “overview”-style questions (e.g. “what is this project?”), the retriever prefers doc chunks (README, etc.) first, then fills the rest from the general index. I didn’t add keyword/BM25 or a reranker—simpler and faster for v1; we can add hybrid or reranking later if we need better recall.

**Prompts**

The RAG path has a system prompt that says: answer only from the provided context, cite every claim with FILE and LINES, and output exactly three sections (Summary, Evidence, Next steps). The user message is the concatenated context plus the question. The agent has a similar system prompt plus instructions to use tools and never invent paths. All of this lives in `backend/rag/prompts.py`. I kept Next steps as “actionable recommendations” (e.g. “review X in path/to/file”) rather than “try asking these questions,” so the UI can show a short list of things to do next.

**Context and guardrails**

Chunk size and top-k (10) keep the total context within normal limits; there’s no truncation step. If we increased k, I’d add a token cap or summarization. Guardrails: (1) all file access (agent tools and `/file`) is under the repo root, with `..` and absolute paths rejected; (2) we only show evidence that we parsed as FILE/LINES from the model output, not random paths in prose; (3) `/file` is capped at 200 lines per request (the UI asks for 50 for the snippet modal).

**Quality and observability**

There’s a small eval harness: a list of sample questions and a runner that hits a repo and reports citation coverage and latency. No ground-truth labels yet—it’s for regression and tuning. For observability, every request gets a run_id and trace_id; we log at module level and write a trace JSON (steps, token usage, answer summary) to disk so we can debug and see cost per run.

---

## 5. Key Technical Decisions

| What I chose | Why |
|--------------|-----|
| **Chroma** for vectors | No extra service to run locally; easy to swap for Pinecone/Weaviate later. |
| **OpenAI** for embeddings and chat | One provider, good quality, configurable via env. |
| **Agent first, then RAG** | Agent (list_files, grep, open_file, get_manifest) can explore the repo; when it fails or returns no evidence, RAG still gives an answer. |
| **Structured answer (Summary / Evidence / Next steps)** | Same shape every time; the UI can parse it and show evidence and next steps in a consistent way. Next steps are bullets, not “try asking” questions. |
| **Regex parsing** of the LLM output | No dependency on a structured-output API; works with any model that roughly follows the prompt. Downside: if the format drifts, parsing can break. |
| **Repo id = hash of source** | Same URL or path always gives the same id, so we can re-ingest and reuse the same Chroma collection. |
| **Manifest per repo** | Lets us know what files exist (for path checks and future incremental updates) and store framework detection (e.g. detected.json). |
| **Trace per request** | One JSON file per run with steps and usage; helps with debugging and cost. |
| **Next.js for the UI** | Clear split from the backend; can be built and deployed on its own. |

---

## 6. Engineering Standards

**What I followed**

- **Types and docstrings** on the main functions and request/response models.
- **Modular layout:** backend split into app (API, settings, logging, tracing), ingest, rag, agent, analysis, eval, and tests; frontend has app, components, and lib.
- **Single responsibility:** Small functions; tracing and logging at request boundaries.
- **Secrets:** Only in `.env`; nothing sensitive in code or in the repo.
- **Logging:** One logger per module; logs go to a directory under `LOG_DIR` with rotation.
- **Tests:** Pytest for backend (ingest, chunker, retriever, chains, API, etc.) and an eval runner. No automated frontend tests.
- **Linting:** Ruff and Black (see Makefile `lint`).
- **Containers:** Dockerfile for backend, one for frontend, and docker-compose to run both.

**What I skipped on purpose**

- **Reranker / hybrid search:** Kept v1 to semantic search only; we can add later if we need better precision.
- **JSON structured output for the RAG answer:** Regex works for the current prompts; JSON would need a schema and more validation.
- **Auth:** No login or API keys in the MVP; I’d add it for a real multi-tenant or public deployment.
- **Database for repo metadata:** Everything is file-based (manifest, memory) to keep the stack minimal.
- **Streaming:** One response per ask; streaming could be added later.
- **Frontend tests:** Backend and eval are covered; frontend I tested by hand. I’d add Jest/Playwright if we kept iterating.

---

## 7. AI Tools Usage

I designed and implemented this project myself; I used an AI coding assistant only as support. Below is the requested detail.

**Which tools?**  
Cursor with an LLM in the loop.

**How I used them**  
For small, scoped tasks: e.g. “add a function that parses the LLM output into summary, evidence, next_steps”; wiring the agent’s LangChain tools and tool_calls loop; frontend API client and error handling; and a first pass on README structure and wording. I had already decided the architecture and flows; the assistant helped with implementation details. I did not paste in large blocks or let it define new components.

**How I validated or refined the output**  
I read every diff and the surrounding code. I ran the app and `pytest` after changes. If something was wrong or didn’t match the rest of the repo (e.g. imports or patterns), I fixed it or re-prompted with more context. I kept ownership of design and architecture.

**Example prompts**
- “Add a function that takes the raw LLM output and returns summary, evidence list, and next_steps so we can reuse it in both RAG and agent.”
- “Wire the agent so it uses list_files, grep, open_file, get_manifest as LangChain tools bound to repo_id, then run the LLM in a loop until there are no tool_calls.”
- “Update the README with: quick setup, architecture, productionization plan, RAG/LLM decisions, key technical decisions, engineering standards, what I’d improve. Keep it clear and avoid generic marketing tone.”

---

## 8. What I’d Improve with More Time

- **RAG:** Add a reranker on the retrieved chunks; try hybrid search (keyword + vector); maybe tune chunk size or overlap per language.
- **Agent:** More tools (e.g. run tests, search symbols); a “RAG only” toggle in the UI for cheaper/faster answers when the user doesn’t need the agent.
- **Eval:** Ground-truth labels (expected files or snippets per question) and regression tests on citation coverage and latency.
- **Frontend:** Loading states, keyboard shortcuts, optional dark theme, shareable links for a question.
- **Auth and production:** API key or OAuth, rate limits, and the productionization steps in section 3.
- **Observability:** Export metrics to Prometheus or the cloud provider; optional distributed tracing for the agent’s tool calls.

I’d also add a short “Quick start” video or GIF and a few OpenAPI examples so someone can hit the API without reading the whole README.

---

## Project layout and commands

```
backend/
  app/          # FastAPI app, settings, logging, tracing, routes
  ingest/       # loader, scanner, chunker, indexer
  rag/          # prompts, retriever, chains, rag_fallback
  agent/        # agent_runner, langchain_tools, tools, memory_store, guardrails
  analysis/     # framework detector, endpoint/auth mappers, etc.
  eval/         # sample questions, runner, results
  tests/        # pytest

frontend/
  src/app/      # layout, Home, Ask, not-found
  src/components/
  src/lib/      # api client, storage, types

docker/         # Dockerfiles
data/           # repos, indexes, logs, traces (gitignored)
```

**Useful commands:** `make setup`, `make lint`, `make test`, `make run-api`, `make run-web`. On Windows you can use `run-backend.bat` and `run-frontend.bat`. To run the eval harness (from repo root, after `pip install -e .`): `python -m eval.runner <repo_id>`.

**Environment:** Copy `.env.example` to `.env` and set `OPENAI_API_KEY` at minimum. Optional: `OPENAI_MODEL`, `OPENAI_EMBED_MODEL`, `REPOS_BASE`, `CHROMA_DIR`, `LOG_DIR`, `TRACE_DIR`, `ALLOWED_ORIGINS`. For the frontend, `frontend/.env` (from `frontend/.env.example`) and `NEXT_PUBLIC_API_BASE_URL` if the API is not on localhost:8000.
