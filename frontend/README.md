# Frontend – Codebase Intelligence Assistant

Next.js TypeScript UI: ingest (repo URL or local path), repo selector, Ask page with chat, evidence modal, trace viewer.

## Structure

- **src/app/** – layout, page (Home), ask/page (Ask)
- **src/components/** – RepoSelect, IngestForm, ChatPanel, EvidenceModal, TraceViewer
- **src/lib/** – api.ts, types.ts, storage.ts (localStorage: repos, chat per repo_id, showTraces), uuid.ts

## Run

`npm install` then `npm run dev`. Set `NEXT_PUBLIC_API_BASE_URL` (default http://localhost:8000). See root README.
