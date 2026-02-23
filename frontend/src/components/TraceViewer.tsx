'use client'

import { useEffect, useState } from 'react'
import { getTrace } from '@/lib/api'
import type { TraceData } from '@/lib/types'

interface TraceViewerProps {
  traceId: string | null
  onClose?: () => void
}

export default function TraceViewer({ traceId, onClose }: TraceViewerProps) {
  const [trace, setTrace] = useState<TraceData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!traceId) {
      setTrace(null)
      return
    }
    setLoading(true)
    setError('')
    getTrace(traceId)
      .then((data) => setTrace(data as TraceData))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load trace'))
      .finally(() => setLoading(false))
  }, [traceId])

  if (!traceId) return null
  if (loading) return <div className="trace-viewer">Loading trace…</div>
  if (error) return <div className="trace-viewer trace-viewer-error">{error}</div>
  if (!trace) return null

  return (
    <div className="trace-viewer card">
      {onClose && (
        <div className="trace-viewer-header">
          <strong>Trace: {trace.trace_id}</strong>
          <button type="button" className="secondary" onClick={onClose}>Close</button>
        </div>
      )}
      <dl className="trace-meta">
        <dt>Started</dt>
        <dd>{trace.started_at ?? '—'}</dd>
        <dt>Ended</dt>
        <dd>{trace.ended_at ?? '—'}</dd>
        <dt>Endpoint</dt>
        <dd>{trace.endpoint_name ?? '—'}</dd>
        {trace.usage && (
          <>
            <dt>Tokens</dt>
            <dd>{trace.usage.total_tokens ?? trace.usage.prompt_tokens != null ? `${trace.usage.prompt_tokens} prompt / ${trace.usage.completion_tokens ?? 0} completion` : '—'}</dd>
          </>
        )}
      </dl>
      <h4>Steps</h4>
      <ul className="trace-steps">
        {trace.steps?.map((step, i) => (
          <li key={i}>
            <span className="trace-step-type">{step.step_type}</span>
            {step.payload && Object.keys(step.payload).length > 0 && (
              <pre className="trace-step-payload">{JSON.stringify(step.payload, null, 2)}</pre>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
