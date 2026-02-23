/**
 * API client for Codebase Intelligence Assistant backend.
 * Base URL is read from NEXT_PUBLIC_API_BASE_URL (default http://localhost:8000).
 */

const getBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
}

async function fetchApi<T>(
  path: string,
  options?: RequestInit & { params?: Record<string, string> }
): Promise<T> {
  const { params, ...init } = options || {}
  const url = new URL(path, getBaseUrl())
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v))
  }
  const res = await fetch(url.toString(), {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init.headers },
  })
  if (!res.ok) {
    const text = await res.text()
    let detail: string = text
    try {
      const j = JSON.parse(text) as { detail?: string }
      detail = typeof j.detail === 'string' ? j.detail : text
    } catch {
      // use text as-is
    }
    const err = new Error(detail) as Error & { detail?: string; status?: number }
    err.detail = detail
    err.status = res.status
    throw err
  }
  return res.json() as Promise<T>
}

/** Get a user-friendly message from an API error (from fetchApi). */
export function getApiErrorMessage(err: unknown): string {
  if (err instanceof Error && 'detail' in err && typeof (err as { detail?: string }).detail === 'string') {
    return (err as { detail: string }).detail
  }
  if (err instanceof Error) return err.message
  return 'Something went wrong'
}

// --- Types (aligned with backend schemas) ---

export interface Evidence {
  path: string
  start_line: number
  end_line: number
  note?: string
}

export interface AskResponse {
  answer?: { summary: string; evidence: Evidence[]; next_steps?: string[] }
  trace_id: string
  run_id?: string
  summary: string
  evidence: Evidence[]
  next_steps: string
  source?: string
}

export interface AskHistoryEntry {
  id: string
  repoId: string
  question: string
  response: AskResponse
  createdAt: number
}

// --- Repos ---

export async function getRepos(): Promise<{ repos: { repo_id: string; root_path: string }[] }> {
  return fetchApi<{ repos: { repo_id: string; root_path: string }[] }>('/repos')
}

// --- Ingest ---

export interface IngestParams {
  repo_url?: string
  local_path?: string
  branch?: string
}

export interface IngestResult {
  repo_id: string
  index_stats?: Record<string, unknown>
  detected?: Record<string, unknown>
}

export async function ingestRepoFull(params: IngestParams): Promise<IngestResult> {
  const body: Record<string, string | undefined> = {
    repo_url: params.repo_url,
    local_path: params.local_path,
    branch: params.branch,
  }
  return fetchApi<IngestResult>('/ingest', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

// --- Ask ---

export async function ask(
  repoId: string,
  question: string,
  useAgent: boolean = true,
  conversationId?: string
): Promise<AskResponse> {
  return fetchApi<AskResponse>('/ask', {
    method: 'POST',
    body: JSON.stringify({
      repo_id: repoId,
      conversation_id: conversationId ?? null,
      question,
      use_agent: useAgent,
    }),
  })
}

// --- File (snippet) ---

export interface FileSnippet {
  file?: string
  path: string
  start?: number
  end?: number
  lines: string[]
  lines_numbered?: { no: number; text: string }[]
}

export async function getFile(
  repoId: string,
  path: string,
  start?: number,
  end?: number,
  maxLines?: number
): Promise<FileSnippet> {
  const params: Record<string, string> = { repo_id: repoId, path }
  if (start != null) params.start = String(start)
  if (end != null) params.end = String(end)
  if (maxLines != null) params.max_lines = String(maxLines)
  return fetchApi<FileSnippet>('/file', { params })
}

// --- Trace ---

export async function getTrace(traceId: string): Promise<Record<string, unknown>> {
  return fetchApi<Record<string, unknown>>('/trace', { params: { trace_id: traceId } })
}

// --- Ask history (localStorage) ---

const ASK_HISTORY_KEY = 'codebase-intel-ask-history'
const MAX_HISTORY = 50

export function getAskHistory(): AskHistoryEntry[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(ASK_HISTORY_KEY)
    if (!raw) return []
    const arr = JSON.parse(raw) as AskHistoryEntry[]
    return Array.isArray(arr) ? arr.slice(-MAX_HISTORY) : []
  } catch {
    return []
  }
}

export function appendAskHistory(entry: Omit<AskHistoryEntry, 'id' | 'createdAt'>): void {
  if (typeof window === 'undefined') return
  const full: AskHistoryEntry = {
    ...entry,
    id: crypto.randomUUID?.() ?? `h-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    createdAt: Date.now(),
  }
  const history = getAskHistory()
  history.push(full)
  const trimmed = history.slice(-MAX_HISTORY)
  localStorage.setItem(ASK_HISTORY_KEY, JSON.stringify(trimmed))
}

export function clearAskHistory(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem(ASK_HISTORY_KEY)
}
