# Setup Guide – Codebase Intelligence Assistant

Use this once to install everything so the project runs smoothly.

---

## Prerequisites (install if you don't have them)

| Requirement | Where to get it |
|-------------|------------------|
| **Python 3.10–3.13** | [python.org/downloads](https://www.python.org/downloads/) – use 3.12 or 3.13 (not 3.14); check **"Add Python to PATH"** |
| **Node.js 18+** | [nodejs.org](https://nodejs.org/) (LTS) |
| **OpenAI API key** | [platform.openai.com](https://platform.openai.com/api-keys) – needed for ingest and ask |

---

## Setup

1. **Python venv and backend** (run from project root)
   ```bat
   cd path\to\Codebase_Intelligence_Assistant
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e .
   ```
   If `python` is not found, try `py -m venv .venv` then `.venv\Scripts\activate`.

2. **Environment file** (in project root)
   ```bat
   copy .env.example .env
   ```
   Edit `.env` and set `OPENAI_API_KEY=sk-...`. Optional: `OPENAI_MODEL`, `OPENAI_EMBED_MODEL`, `CHROMA_DIR`, `LOG_DIR`, `TRACE_DIR`, `ALLOWED_ORIGINS` (see `.env.example` comments).

3. **Frontend**
   ```bat
   cd frontend
   copy .env.example .env
   npm install
   cd ..
   ```

4. **Run** (two terminals, from project root)
   - Terminal 1: `run-backend.bat` (or with venv activated: `python backend\app\main.py`)
   - Terminal 2: `run-frontend.bat` (or `cd frontend && npm run dev`)
   - Backend: http://localhost:8000 · Frontend: http://localhost:3000

5. **Verify** – Open http://localhost:8000/health (should show `{"status":"ok"}`) and http://localhost:3000 (app home).

---

## Troubleshooting

| Problem | What to do |
|--------|-------------|
| "Python is not recognized" | Install Python from python.org and tick "Add to PATH", or use **Anaconda Prompt** and run the manual steps. |
| "Unable to create process" when using `py` | The launcher points to an old Python. Create the project venv manually: `python -m venv .venv` then `.venv\Scripts\activate`. |
| **ChromaDB / Pydantic error on startup** (e.g. `unable to infer type for attribute "chroma_server_nofile"`) | You're on **Python 3.14**. This project needs **Python 3.10–3.13**. Install [Python 3.12](https://www.python.org/downloads/release/python-3120/) or 3.13, remove the old `.venv` folder, then run the setup steps again. |
| "node/npm is not recognized" | Install Node.js from nodejs.org; then run `cd frontend && npm install`. |
| Backend starts but ingest/ask fail | Make sure `.env` has a valid `OPENAI_API_KEY`. |

---

## Summary

- **First time:** Follow the setup steps above, set `OPENAI_API_KEY` in `.env`, then run `run-backend.bat` and `run-frontend.bat` (in two terminals).
- **Later:** Just run `run-backend.bat` and `run-frontend.bat`. No need to run setup again unless you add dependencies or delete `.venv`.
