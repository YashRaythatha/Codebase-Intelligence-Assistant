'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import {
  getRepos,
  ask,
  getFile,
  getAskHistory,
  appendAskHistory,
  clearAskHistory,
  getApiErrorMessage,
  type AskResponse,
  type Evidence,
  type AskHistoryEntry,
} from '@/lib/api'
import { getShowTraces, setShowTraces } from '@/lib/storage'
import { uuid } from '@/lib/uuid'
import TraceViewer from '@/components/TraceViewer'
import RepoSelect from '@/components/RepoSelect'
import EvidenceModal from '@/components/EvidenceModal'

function formatTime(ms: number) {
  const d = new Date(ms)
  const now = new Date()
  const sameDay = d.toDateString() === now.toDateString()
  if (sameDay) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function AskPage() {
  const [repos, setRepos] = useState<{ repo_id: string; root_path: string }[]>([])
  const [repoId, setRepoId] = useState('')
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<AskResponse | null>(null)
  const [snippet, setSnippet] = useState<{ path: string; lines: string[]; error?: string } | null>(null)
  const [history, setHistory] = useState<AskHistoryEntry[]>([])
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null)
  const [showTraces, setShowTracesState] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [conversationId] = useState(() => uuid())
  const resultRef = useRef<HTMLDivElement>(null)
  const [reposLoading, setReposLoading] = useState(true)
  const [reposError, setReposError] = useState('')

  useEffect(() => {
    setShowTracesState(getShowTraces())
  }, [])

  useEffect(() => {
    setReposLoading(true)
    setReposError('')
    getRepos()
      .then((data) => {
        setRepos(data.repos || [])
        if (data.repos?.length && !repoId) setRepoId(data.repos[0].repo_id)
      })
      .catch(() => {
        setRepos([])
        setReposError('Could not load repos. Check that the backend is running.')
      })
      .finally(() => setReposLoading(false))
  }, [])

  useEffect(() => {
    setHistory(getAskHistory())
  }, [])

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setResult(null)
    setSelectedHistoryId(null)
    if (!repoId || !question.trim()) return
    setLoading(true)
    try {
      const data = await ask(repoId, question.trim(), true, conversationId)
      setResult(data)
      appendAskHistory({ repoId, question: question.trim(), response: data })
      setHistory(getAskHistory())
      setTimeout(() => resultRef.current?.focus({ preventScroll: true }), 100)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  function loadHistoryEntry(entry: AskHistoryEntry) {
    setResult(entry.response)
    setRepoId(entry.repoId)
    setQuestion(entry.question)
    setSnippet(null)
    setSelectedHistoryId(entry.id)
  }

  function clearHistory() {
    clearAskHistory()
    setHistory([])
    setResult(null)
    setSelectedHistoryId(null)
  }

  async function viewSnippet(ev: Evidence) {
    try {
      const data = await getFile(repoId, ev.path, ev.start_line, ev.end_line, 50)
      setSnippet({ path: data.path, lines: data.lines, error: undefined })
    } catch (e) {
      setSnippet({ path: ev.path, lines: [], error: getApiErrorMessage(e) })
    }
  }

  function startNewChat() {
    setResult(null)
    setQuestion('')
    setSnippet(null)
    setError('')
    setSelectedHistoryId(null)
  }

  /** Split next steps into lines/bullets for display. Optional: detect question-like lines for "Ask" button. */
  function parseNextSteps(nextSteps: string): { items: string[]; questions: string[] } {
    if (!nextSteps?.trim()) return { items: [], questions: [] }
    const text = nextSteps.trim()
    const normalized = text.replace(/^Next steps:\s*/i, '').trim()
    const lines = normalized
      .split(/\n+/)
      .map((s) => s.replace(/^[\s•\-*]+\s*/, '').trim())
      .filter((s) => s.length > 0)
    const questions = lines.filter((s) => s.endsWith('?') && s.length > 10)
    return { items: lines, questions }
  }

  return (
    <div className="ask-page">
      <nav className="ask-nav">
        <span className="ask-nav-brand">Codebase Intelligence</span>
        <div className="ask-nav-links">
          <Link href="/">Home</Link>
          <Link href="/ask" className="active">Ask</Link>
        </div>
      </nav>

      <div className="ask-body">
      <aside className={`ask-sidebar ${historyOpen ? 'ask-sidebar-open' : ''}`}>
        <button
          type="button"
          className="ask-sidebar-toggle"
          onClick={() => setHistoryOpen((o) => !o)}
          title={historyOpen ? 'Collapse history' : 'Expand history'}
        >
          <span className="ask-sidebar-toggle-icon" aria-hidden>{historyOpen ? '◀' : '▶'}</span>
          <span className="ask-sidebar-toggle-label">History</span>
          {history.length > 0 && <span className="ask-sidebar-toggle-count">{history.length}</span>}
        </button>
        <div className="ask-sidebar-content">
          <div className="ask-sidebar-header">
            <h2>Past questions</h2>
            {history.length > 0 && (
              <button type="button" className="secondary small" onClick={clearHistory}>Clear</button>
            )}
          </div>
          {history.length === 0 ? (
            <p className="ask-sidebar-empty">No previous chats yet.</p>
          ) : (
            <ul className="ask-history-list">
              {[...history].reverse().map((entry) => (
                <li key={entry.id}>
                  <button
                    type="button"
                    className={`ask-history-item ${selectedHistoryId === entry.id ? 'active' : ''}`}
                    onClick={() => loadHistoryEntry(entry)}
                  >
                    <span className="ask-history-question">{entry.question}</span>
                    <span className="ask-history-meta">{formatTime(entry.createdAt)}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      <main className="ask-main-content" id="main">
        <h1>Ask</h1>
        {reposLoading ? (
          <div className="card ask-empty-repos">
            <p>Loading repos…</p>
          </div>
        ) : reposError ? (
          <div className="card ask-empty-repos">
            <p className="ask-error">{reposError}</p>
            <Link href="/">Go to Home</Link>
          </div>
        ) : repos.length === 0 ? (
          <div className="ask-empty-repos card">
            <p>No repos indexed yet. Ingest a repo on the Home page first.</p>
            <Link href="/" className="ask-empty-repos-link">Go to Home</Link>
          </div>
        ) : (
          <>
        <RepoSelect repos={repos} value={repoId} onChange={setRepoId} disabled={loading} />
        <div className="card ask-form-card">
          <div className="ask-form-header">
            <button type="button" className="secondary ask-new-chat" onClick={startNewChat} title="Start a new question">
              New chat
            </button>
          </div>
          <form onSubmit={handleAsk} className="ask-form" aria-busy={loading}>
            <label className="ask-label" htmlFor="ask-question">Question</label>
            <textarea
              id="ask-question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. Where is auth handled? How does the request flow?"
              disabled={loading}
              className="ask-question-input"
              rows={6}
              aria-describedby={error ? 'ask-error' : undefined}
            />
            <button type="submit" disabled={loading || !repoId} className="ask-submit">
              {loading ? (
                <span className="ask-submit-loading"><span className="ask-spinner" aria-hidden /> Asking…</span>
              ) : (
                'Ask'
              )}
            </button>
          </form>
          {error && <p id="ask-error" className="ask-error" role="alert">{error}</p>}
        </div>

        {result && (
          <div className="card ask-result" ref={resultRef} tabIndex={-1} aria-label="Answer result">
            <div className="ask-result-header">
              {result.source && <p className="ask-result-source">Answered with {result.source}</p>}
              {result.trace_id && (
                <label className="trace-toggle">
                  <input
                    type="checkbox"
                    checked={showTraces}
                    onChange={(e) => {
                      const v = e.target.checked
                      setShowTracesState(v)
                      setShowTraces(v)
                    }}
                  />
                  Show trace
                </label>
              )}
            </div>

            <section className="result-section result-section-summary">
              <h2 className="result-section-title">Summary</h2>
              <div className="result-section-body">
                <p>{result.summary || '—'}</p>
              </div>
            </section>

            <section className="result-section result-section-evidence">
              <h2 className="result-section-title">Evidence</h2>
              <div className="result-section-body">
                {result.evidence?.length ? (
                  <ul className="ask-evidence-list">
                    {result.evidence.map((ev, i) => (
                      <li key={i} className="evidence-item">
                        <span className="evidence-file">{ev.path}</span>
                        <span className="evidence-lines">L{ev.start_line}–{ev.end_line}</span>
                        <button type="button" className="secondary btn-snippet" onClick={() => viewSnippet(ev)}>View snippet</button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="result-muted">No citations.</p>
                )}
              </div>
            </section>

            <section className="result-section result-section-nextsteps">
              <h2 className="result-section-title">Next steps</h2>
              <div className="result-section-body">
                {result.next_steps ? (
                  <>
                    <ul className="next-steps-list">
                      {parseNextSteps(result.next_steps).items.map((item, i) => (
                        <li key={i} className="next-step-item">{item}</li>
                      ))}
                    </ul>
                    {parseNextSteps(result.next_steps).questions.length > 0 && (
                      <div className="next-steps-actions">
                        <span className="next-steps-label">Or ask:</span>
                        {parseNextSteps(result.next_steps).questions.map((q, i) => (
                          <button
                            key={i}
                            type="button"
                            className="next-step-btn"
                            onClick={() => setQuestion(q)}
                          >
                            {q}
                          </button>
                        ))}
                      </div>
                    )}
                  </>
                ) : (
                  <p>—</p>
                )}
              </div>
            </section>
            {showTraces && result.trace_id && (
              <TraceViewer traceId={result.trace_id} />
            )}
          </div>
        )}

        {snippet && (
          <EvidenceModal
            path={snippet.path}
            lines={snippet.lines}
            error={snippet.error}
            onClose={() => setSnippet(null)}
          />
        )}
          </>
        )}
      </main>
      </div>
    </div>
  )
}
