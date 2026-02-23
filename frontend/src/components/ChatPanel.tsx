'use client'

import type { AskResponse, Evidence } from '@/lib/api'

interface ChatPanelProps {
  question: string
  onQuestionChange: (v: string) => void
  onSubmit: (e: React.FormEvent) => void
  loading: boolean
  repoId: string
  result: AskResponse | null
  onViewSnippet: (ev: Evidence) => void
  error: string
}

export default function ChatPanel({
  question,
  onQuestionChange,
  onSubmit,
  loading,
  repoId,
  result,
  onViewSnippet,
  error,
}: ChatPanelProps) {
  return (
    <>
      <div className="card ask-form-card">
        <form onSubmit={onSubmit} className="ask-form">
          <label className="ask-label">Question</label>
          <textarea
            value={question}
            onChange={(e) => onQuestionChange(e.target.value)}
            placeholder="e.g. Where is auth handled?"
            disabled={loading}
            className="ask-question-input"
            rows={6}
          />
          <button type="submit" disabled={loading || !repoId} className="ask-submit">
            {loading ? 'Asking…' : 'Ask'}
          </button>
        </form>
        {error && <p className="ask-error">{error}</p>}
      </div>
      {result && (
        <div className="card ask-result">
          {result.source && <p className="ask-result-source">Answered with {result.source}</p>}
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
                      <button type="button" className="secondary btn-snippet" onClick={() => onViewSnippet(ev)}>
                        View snippet
                      </button>
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
                <ul className="next-steps-list">
                  {result.next_steps
                    .trim()
                    .replace(/^Next steps:\s*/i, '')
                    .split(/\n+/)
                    .map((s) => s.replace(/^[\s•\-*]+\s*/, '').trim())
                    .filter(Boolean)
                    .map((item, i) => (
                      <li key={i} className="next-step-item">{item}</li>
                    ))}
                </ul>
              ) : (
                <p>—</p>
              )}
            </div>
          </section>
        </div>
      )}
    </>
  )
}
