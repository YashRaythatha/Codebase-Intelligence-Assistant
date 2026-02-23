'use client'

import { useEffect, useRef } from 'react'

interface EvidenceModalProps {
  path: string
  lines: string[]
  onClose: () => void
  error?: string
}

export default function EvidenceModal({ path, lines, onClose, error }: EvidenceModalProps) {
  const closeRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    closeRef.current?.focus()
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  return (
    <div className="snippet-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Evidence snippet">
      <div className="card snippet-panel" onClick={(e) => e.stopPropagation()}>
        <div className="snippet-panel-header">
          <h3 className="snippet-panel-title">{path}</h3>
          <button type="button" className="secondary snippet-close" onClick={onClose} ref={closeRef} aria-label="Close">
            Close
          </button>
        </div>
        {error ? (
          <p className="snippet-error">{error}</p>
        ) : lines.length === 0 ? (
          <p className="snippet-empty">No content for this range.</p>
        ) : (
          <pre className="snippet-pre">
            {lines.map((line, i) => (
              <span key={i}>
                {i + 1}  {line}
                {'\n'}
              </span>
            ))}
          </pre>
        )}
      </div>
    </div>
  )
}
